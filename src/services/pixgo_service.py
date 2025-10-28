import logging
import time
from enum import Enum
from typing import Any, Type

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Import performance monitoring
try:
    from src.utils.performance import measure_performance
except ImportError:
    # Fallback if performance monitoring is not available
    def measure_performance(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class PixGoError(Exception):
    """Base exception for PixGo service errors"""
    pass


class PixGoAPIError(PixGoError):
    """Exception raised for PixGo API errors"""
    pass


class PixGoTimeoutError(PixGoError):
    """Exception raised for PixGo timeout errors"""
    pass


class PixGoCircuitBreakerError(PixGoError):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Simple circuit breaker implementation"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: Type[Exception] | tuple[Type[Exception], ...] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitBreakerState.CLOSED

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time and time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise PixGoCircuitBreakerError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


def retry_on_failure(max_retries: int = 3, backoff_factor: float = 0.3, exceptions: tuple[Type[Exception], ...] = (requests.RequestException,)):
    """Decorator to retry function calls on failure with exponential backoff"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {wait_time:.2f}s: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected error in retry logic")
        return wrapper
    return decorator


class PixGoService:
    def __init__(self, api_key: str, base_url: str = "https://pixgo.org/api/v1", timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=0.3
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update(
            {"X-API-Key": api_key, "Content-Type": "application/json"}
        )

        # Circuit breaker for API calls
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=(requests.RequestException, PixGoAPIError)
        )

    @retry_on_failure(max_retries=2, exceptions=(requests.Timeout, requests.ConnectionError))
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with timeout and error handling"""
        try:
            kwargs.setdefault('timeout', self.timeout)
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.Timeout as e:
            logger.error(f"Request timeout for {url}: {e}")
            raise PixGoTimeoutError(f"Request timeout: {e}") from e
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise PixGoAPIError(f"API request failed: {e}") from e

    @measure_performance("pixgo_service.create_payment")
    def create_payment(
        self,
        amount: float,
        description: str,
        payer_info: dict[str, Any] | None = None,
        fallback_service: Any = None,
    ) -> dict[str, Any] | None:
        """Create a PIX payment with fallback support"""
        try:
            return self.circuit_breaker.call(self._create_payment_internal, amount, description, payer_info)
        except PixGoCircuitBreakerError:
            # Circuit breaker is open, try fallback immediately
            if fallback_service:
                return self._fallback_to_usdt(amount, description, fallback_service)
            raise
        except (PixGoError, requests.RequestException) as e:
            logger.error(f"PixGo payment creation failed, attempting fallback: {e}")
            if fallback_service:
                return self._fallback_to_usdt(amount, description, fallback_service)
            return None

    def _create_payment_internal(
        self,
        amount: float,
        description: str,
        payer_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Internal payment creation logic"""
        payload = {"amount": amount, "description": description, "currency": "BRL"}
        if payer_info:
            payload.update(payer_info)

        response = self._make_request("POST", f"{self.base_url}/payment/create", json=payload)
        data = response.json()

        if data.get("success"):
            logger.info(f"Created PIX payment: {data.get('data', {}).get('payment_id')}")
            return data.get("data")

        error_msg = data.get("error", "Unknown error")
        logger.error(f"Failed to create PIX payment: {error_msg}")
        raise PixGoAPIError(f"Payment creation failed: {error_msg}")

    def _fallback_to_usdt(self, amount: float, description: str, usdt_service: Any) -> dict[str, Any] | None:
        """Fallback to USDT payment when PixGo fails"""
        logger.info(f"Falling back to USDT payment for amount {amount}")
        try:
            usdt_address = usdt_service.get_payment_address()
            instructions = usdt_service.get_payment_instructions(amount)

            return {
                "payment_id": f"usdt_{int(time.time())}",
                "payment_method": "USDT",
                "amount": amount,
                "description": description,
                "usdt_address": usdt_address,
                "instructions": instructions,
                "fallback": True
            }
        except Exception as e:
            logger.error(f"USDT fallback also failed: {e}")
            return None

    @measure_performance("pixgo_service.get_payment_status")
    def get_payment_status(self, payment_id: str) -> str | None:
        """Get payment status with error handling"""
        try:
            return self.circuit_breaker.call(self._get_payment_status_internal, payment_id)
        except (PixGoError, requests.RequestException) as e:
            logger.error(f"Failed to get payment status for {payment_id}: {e}")
            return None

    def _get_payment_status_internal(self, payment_id: str) -> str | None:
        """Internal payment status retrieval"""
        response = self._make_request("GET", f"{self.base_url}/payment/{payment_id}/status")
        data = response.json()
        return data.get("status")

    @measure_performance("pixgo_service.get_qr_code")
    def get_qr_code(self, payment_id: str) -> str | None:
        """Get QR code for payment with error handling"""
        try:
            return self.circuit_breaker.call(self._get_qr_code_internal, payment_id)
        except (PixGoError, requests.RequestException) as e:
            logger.error(f"Failed to get QR code for {payment_id}: {e}")
            return None

    def _get_qr_code_internal(self, payment_id: str) -> str | None:
        """Internal QR code retrieval"""
        response = self._make_request("GET", f"{self.base_url}/payment/{payment_id}/qr")
        data = response.json()
        return data.get("qr_code")
