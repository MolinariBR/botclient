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
    from utils.performance import measure_performance
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
    def __init__(self, message: str, status_code: int | None = None, response_data: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class PixGoTimeoutError(PixGoError):
    """Exception raised for PixGo timeout errors"""
    pass


class PixGoRateLimitError(PixGoError):
    """Exception raised for PixGo rate limit errors"""
    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class PixGoCircuitBreakerError(PixGoError):
    """Exception raised when circuit breaker is open"""
    pass


class PixGoValidationError(PixGoError):
    """Exception raised for validation errors"""
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
        """Make HTTP request with timeout and comprehensive error handling"""
        try:
            kwargs.setdefault('timeout', self.timeout)
            response = self.session.request(method, url, **kwargs)

            # Handle specific HTTP status codes
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                retry_seconds = int(retry_after) if retry_after and retry_after.isdigit() else 60
                logger.warning(f"Rate limited by PixGo API, retry after {retry_seconds}s")
                raise PixGoRateLimitError(f"Rate limit exceeded", retry_after=retry_seconds)

            response.raise_for_status()

            # Validate response content
            try:
                response_data = response.json()
                self._validate_api_response(response_data)
            except ValueError as e:
                logger.error(f"Invalid JSON response from PixGo API: {e}")
                raise PixGoAPIError(f"Invalid JSON response: {e}") from e

            return response

        except requests.Timeout as e:
            logger.error(f"Request timeout for {url}: {e}")
            raise PixGoTimeoutError(f"Request timeout: {e}") from e
        except requests.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise PixGoAPIError(f"Connection failed: {e}") from e
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            logger.error(f"HTTP error for {url} (status {status_code}): {e}")

            # Try to extract error details from response
            error_details = "Unknown error"
            if e.response and e.response.content:
                try:
                    error_data = e.response.json()
                    error_details = error_data.get('error', error_data.get('message', str(error_data)))
                except ValueError:
                    error_details = e.response.text[:200]  # Truncate long error messages

            raise PixGoAPIError(f"HTTP {status_code}: {error_details}", status_code=status_code) from e
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise PixGoAPIError(f"Request failed: {e}") from e

    def _validate_api_response(self, response_data: dict) -> None:
        """Validate API response structure and content"""
        if not isinstance(response_data, dict):
            raise PixGoValidationError("API response must be a JSON object")

        # Check for common API error patterns
        if response_data.get('success') is False:
            error_msg = response_data.get('error', response_data.get('message', 'API returned success=false'))
            raise PixGoAPIError(f"API error: {error_msg}", response_data=response_data)

        # Validate required fields for successful responses
        if 'data' in response_data and response_data.get('success') is True:
            if not isinstance(response_data['data'], dict):
                raise PixGoValidationError("API response data must be an object")

    @measure_performance("pixgo_service.create_payment")
    def create_payment(
        self,
        amount: float,
        description: str,
        payer_info: dict[str, Any] | None = None,
        fallback_service: Any = None,
    ) -> dict[str, Any] | None:
        """Create a PIX payment with comprehensive error handling and fallback support"""
        # Input validation
        if amount <= 0:
            logger.error(f"Invalid payment amount: {amount}")
            return None
        if not description or len(description.strip()) == 0:
            logger.error("Payment description cannot be empty")
            return None

        try:
            return self.circuit_breaker.call(self._create_payment_internal, amount, description, payer_info)
        except PixGoCircuitBreakerError as e:
            logger.warning(f"Circuit breaker open for PixGo, attempting fallback: {e}")
            if fallback_service:
                return self._fallback_to_usdt(amount, description, fallback_service)
            raise
        except PixGoRateLimitError as e:
            logger.warning(f"PixGo rate limited (retry after {e.retry_after}s), attempting fallback")
            if fallback_service:
                return self._fallback_to_usdt(amount, description, fallback_service)
            raise
        except PixGoValidationError as e:
            logger.error(f"Payment validation error: {e}")
            return None
        except PixGoTimeoutError as e:
            logger.warning(f"PixGo timeout, attempting fallback: {e}")
            if fallback_service:
                return self._fallback_to_usdt(amount, description, fallback_service)
            return None
        except PixGoAPIError as e:
            logger.error(f"PixGo API error, attempting fallback: {e}")
            if fallback_service:
                return self._fallback_to_usdt(amount, description, fallback_service)
            return None
        except Exception as e:
            logger.error(f"Unexpected error in PixGo payment creation: {e}")
            # Don't attempt fallback for unexpected errors
            return None

    def _create_payment_internal(
        self,
        amount: float,
        description: str,
        payer_info: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Internal payment creation logic with enhanced error handling"""
        # Validate input parameters
        if amount <= 0:
            raise PixGoValidationError("Payment amount must be positive")
        if not description or len(description.strip()) == 0:
            raise PixGoValidationError("Payment description cannot be empty")

        payload = {"amount": amount, "description": description.strip(), "currency": "BRL"}
        if payer_info:
            # Validate payer_info structure
            if not isinstance(payer_info, dict):
                raise PixGoValidationError("Payer info must be a dictionary")
            payload.update(payer_info)

        try:
            response = self._make_request("POST", f"{self.base_url}/payment/create", json=payload)
            data = response.json()

            if data.get("success") and "data" in data:
                payment_data = data["data"]
                payment_id = payment_data.get('payment_id', payment_data.get('id', 'unknown'))
                logger.info(f"Created PIX payment: {payment_id}")
                return payment_data

            # Handle API-level errors
            error_msg = data.get("error", data.get("message", "Unknown API error"))
            logger.error(f"Failed to create PIX payment: {error_msg}")
            raise PixGoAPIError(f"Payment creation failed: {error_msg}", response_data=data)

        except PixGoRateLimitError:
            # Re-raise rate limit errors as they need special handling
            raise
        except PixGoAPIError:
            # Re-raise API errors as-is
            raise
        except PixGoTimeoutError:
            # Re-raise timeout errors as they need special handling
            raise
        except PixGoValidationError:
            # Re-raise validation errors as they need special handling
            raise
        except Exception as e:
            logger.error(f"Unexpected error in payment creation: {e}")
            raise PixGoAPIError(f"Unexpected error: {e}") from e

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
