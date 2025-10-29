from unittest.mock import Mock, patch

import pytest
import requests

from src.services.pixgo_service import (
    PixGoService,
    PixGoAPIError,
    PixGoTimeoutError,
    PixGoCircuitBreakerError,
    PixGoRateLimitError,
    PixGoValidationError,
    CircuitBreaker,
    CircuitBreakerState
)


class TestPixGoService:
    """Unit tests for PixGo service"""

    @patch.object(PixGoService, '_make_request')
    def test_create_payment_success(self, mock_make_request):
        """Test successful payment creation"""
        service = PixGoService("test_key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "payment_id": "pix_123",
                "qr_code": "qr_code_data",
                "qr_image_url": "http://example.com/qr.png",
                "expires_at": "2025-10-28T10:00:00Z"
            }
        }
        mock_make_request.return_value = mock_response

        result = service.create_payment(10.0, "Test payment")

        assert result is not None
        assert result["payment_id"] == "pix_123"
        assert result["qr_code"] == "qr_code_data"
        mock_make_request.assert_called_once()

    @patch.object(PixGoService, '_make_request')
    def test_create_payment_failure(self, mock_make_request):
        """Test payment creation failure"""
        service = PixGoService("test_key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "success": False,
            "error": "Invalid amount"
        }
        mock_make_request.return_value = mock_response

        result = service.create_payment(10.0, "Test payment")

        assert result is None
        mock_make_request.assert_called_once()

    @patch.object(PixGoService, '_make_request')
    def test_get_qr_code(self, mock_make_request):
        """Test QR code retrieval"""
        service = PixGoService("test_key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "qr_code": "qr_code_data"
        }
        mock_make_request.return_value = mock_response

        qr_code = service.get_qr_code("pix_123")
        assert qr_code == "qr_code_data"
        mock_make_request.assert_called_once()

    @patch.object(PixGoService, '_make_request')
    def test_get_payment_status_success(self, mock_make_request):
        """Test successful payment status retrieval"""
        service = PixGoService("test_key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "completed"
        }
        mock_make_request.return_value = mock_response

        status = service.get_payment_status("pix_123")
        assert status == "completed"
        mock_make_request.assert_called_once_with("GET", "https://pixgo.org/api/v1/payment/pix_123/status")

    @patch.object(PixGoService, '_make_request')
    def test_get_payment_status_failure(self, mock_make_request):
        """Test payment status retrieval failure"""
        service = PixGoService("test_key")

        mock_make_request.side_effect = requests.RequestException("API Error")

        status = service.get_payment_status("pix_123")
        assert status is None

    @patch.object(PixGoService, '_make_request')
    def test_create_payment_with_payer_info(self, mock_make_request):
        """Test payment creation with payer information"""
        service = PixGoService("test_key")

        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "payment_id": "pix_123",
                "qr_code": "qr_code_data",
                "qr_image_url": "http://example.com/qr.png",
                "expires_at": "2025-10-28T10:00:00Z"
            }
        }
        mock_make_request.return_value = mock_response

        payer_info = {"customer_name": "John Doe", "customer_email": "john@example.com"}
        result = service.create_payment(10.0, "Test payment", payer_info)

        assert result is not None
        assert result["payment_id"] == "pix_123"
        mock_make_request.assert_called_once()

        # Verify payer info was included in payload
        call_args = mock_make_request.call_args
        assert call_args[0][0] == "POST"  # method
        assert call_args[0][1] == "https://pixgo.org/api/v1/payment/create"  # url
        payload = call_args[1]["json"]
        assert payload["customer_name"] == "John Doe"
        assert payload["customer_email"] == "john@example.com"
        assert payload["currency"] == "BRL"

    @patch.object(PixGoService, '_make_request')
    def test_timeout_error_handling(self, mock_make_request):
        """Test timeout error handling"""
        service = PixGoService("test_key")

        mock_make_request.side_effect = requests.Timeout("Request timeout")

        result = service.create_payment(10.0, "Test payment")
        assert result is None

    # Note: Retry mechanism is tested indirectly through integration tests
    # The @retry_on_failure decorator on _make_request handles retries at HTTP level

    @patch.object(PixGoService, '_make_request')
    def test_circuit_breaker_open(self, mock_make_request):
        """Test circuit breaker opens after failures"""
        service = PixGoService("test_key")

        # Simulate 5 failures to open circuit breaker
        mock_make_request.side_effect = requests.RequestException("API Error")

        # Make 5 failed calls
        for _ in range(5):
            service.create_payment(10.0, "Test payment")

        # Circuit breaker should now be open
        assert service.circuit_breaker.state == CircuitBreakerState.OPEN

        # Next call should raise circuit breaker error
        with pytest.raises(PixGoCircuitBreakerError):
            service.create_payment(10.0, "Test payment")

    @patch.object(PixGoService, '_make_request')
    @patch('src.services.pixgo_service.time.time')
    @patch('src.utils.performance.performance_monitor.measure')  # Disable performance monitoring for this test
    def test_circuit_breaker_recovery(self, mock_measure, mock_time, mock_make_request):
        """Test circuit breaker recovery after timeout"""
        # Disable performance monitoring for this test
        mock_measure.return_value.__enter__ = Mock()
        mock_measure.return_value.__exit__ = Mock()

        service = PixGoService("test_key")

        # Set up time progression
        mock_time.side_effect = [100, 100, 100, 100, 100, 200]  # Last call after recovery timeout

        # Simulate 5 failures to open circuit breaker
        mock_make_request.side_effect = requests.RequestException("API Error")

        # Make 5 failed calls
        for _ in range(5):
            service.create_payment(10.0, "Test payment")

        assert service.circuit_breaker.state == CircuitBreakerState.OPEN

        # Mock successful response for recovery attempt
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": {"payment_id": "pix_123"}}
        mock_make_request.side_effect = None
        mock_make_request.return_value = mock_response

        # Next call should attempt recovery (half-open state)
        result = service.create_payment(10.0, "Test payment")

        assert result is not None
        assert result["payment_id"] == "pix_123"
        assert service.circuit_breaker.state == CircuitBreakerState.CLOSED

    @patch('src.services.pixgo_service.time.time')
    def test_fallback_to_usdt(self, mock_time):
        """Test fallback to USDT when PixGo fails"""
        service = PixGoService("test_key")

        # Mock time for consistent payment ID
        mock_time.return_value = 1234567890

        # Mock USDT service
        mock_usdt_service = Mock()
        mock_usdt_service.get_payment_address.return_value = "0x1234567890abcdef"
        mock_usdt_service.get_payment_instructions.return_value = "Pay 10.0 USDT to 0x1234567890abcdef"

        # Simulate PixGo failure
        with patch.object(service, '_create_payment_internal') as mock_internal:
            mock_internal.side_effect = PixGoAPIError("PixGo API unavailable")

            result = service.create_payment(10.0, "Test payment", fallback_service=mock_usdt_service)

        assert result is not None
        assert result["payment_method"] == "USDT"
        assert result["amount"] == 10.0
        assert result["usdt_address"] == "0x1234567890abcdef"
        assert result["fallback"] is True
        assert "usdt_1234567890" in result["payment_id"]

    @patch.object(PixGoService, '_make_request')
    def test_custom_exceptions(self, mock_make_request):
        """Test custom exception handling"""
        service = PixGoService("test_key")

        # Test timeout exception
        mock_make_request.side_effect = requests.Timeout("Timeout")
        result = service.create_payment(10.0, "Test payment")
        assert result is None

        # Test API error exception
        mock_make_request.side_effect = requests.HTTPError("500 Server Error")
        result = service.create_payment(10.0, "Test payment")
        assert result is None

    def test_service_initialization(self):
        """Test service initialization with custom parameters"""
        service = PixGoService("test_key", timeout=60)

        assert service.api_key == "test_key"
        assert service.timeout == 60
        assert service.base_url == "https://pixgo.org/api/v1"
        assert hasattr(service, 'circuit_breaker')
        assert service.circuit_breaker.failure_threshold == 5
        assert service.circuit_breaker.recovery_timeout == 60


class TestPixGoServiceErrorHandling:
    """Test enhanced error handling in PixGo service"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = PixGoService("test_key")
        self.service.api_key = "test_key"
        self.service.base_url = "https://api.pixgo.com"

    @patch.object(PixGoService, '_make_request')
    def test_create_payment_internal_success(self, mock_make_request):
        """Test successful payment creation in internal method"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "payment_id": "pix_123",
                "qr_code": "qr_code_data",
                "status": "pending"
            }
        }
        mock_make_request.return_value = mock_response

        result = self.service._create_payment_internal(100.0, "Test payment")

        assert result is not None
        assert result["payment_id"] == "pix_123"
        assert result["qr_code"] == "qr_code_data"

    @patch.object(PixGoService, '_make_request')
    def test_create_payment_internal_validation_error(self, mock_make_request):
        """Test validation error handling in internal method"""
        mock_make_request.side_effect = PixGoValidationError("Invalid amount")

        with pytest.raises(PixGoValidationError):
            self.service._create_payment_internal(100.0, "Test payment")

    @patch.object(PixGoService, '_make_request')
    def test_create_payment_internal_rate_limit_error(self, mock_make_request):
        """Test rate limit error handling in internal method"""
        mock_make_request.side_effect = PixGoRateLimitError("Rate limit exceeded", retry_after=60)

        with pytest.raises(PixGoRateLimitError) as exc_info:
            self.service._create_payment_internal(100.0, "Test payment")

        assert exc_info.value.retry_after == 60

    @patch.object(PixGoService, '_make_request')
    def test_create_payment_internal_timeout_error(self, mock_make_request):
        """Test timeout error handling in internal method"""
        mock_make_request.side_effect = PixGoTimeoutError("Connection timeout")

        with pytest.raises(PixGoTimeoutError):
            self.service._create_payment_internal(100.0, "Test payment")

    @patch.object(PixGoService, '_make_request')
    def test_create_payment_internal_server_error(self, mock_make_request):
        """Test server error handling in internal method"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_make_request.return_value = mock_response

        with pytest.raises(PixGoAPIError):
            self.service._create_payment_internal(100.0, "Test payment")

    def test_create_payment_invalid_amount(self):
        """Test invalid amount validation"""
        result = self.service.create_payment(-100.0, "Test payment")
        assert result is None

    def test_create_payment_empty_description(self):
        """Test empty description validation"""
        result = self.service.create_payment(100.0, "")
        assert result is None

    @patch.object(PixGoService, '_create_payment_internal')
    def test_create_payment_circuit_breaker_fallback(self, mock_internal):
        """Test circuit breaker fallback to USDT"""
        # Simulate circuit breaker open
        mock_internal.side_effect = PixGoCircuitBreakerError("Circuit breaker open")

        mock_usdt_service = Mock()
        mock_usdt_service.create_payment.return_value = {
            "payment_id": "usdt_123",
            "qr_code": "usdt_qr_code"
        }

        result = self.service.create_payment(100.0, "Test payment", fallback_service=mock_usdt_service)

        assert result is not None
        assert result["fallback"] is True
        assert result["payment_method"] == "USDT"
        assert result["usdt_address"] is not None

    @patch.object(PixGoService, '_create_payment_internal')
    def test_create_payment_rate_limit_fallback(self, mock_internal):
        """Test rate limit fallback to USDT"""
        mock_internal.side_effect = PixGoRateLimitError("Rate limited", retry_after=60)

        mock_usdt_service = Mock()
        mock_usdt_service.create_payment.return_value = {
            "payment_id": "usdt_123",
            "qr_code": "usdt_qr_code"
        }

        result = self.service.create_payment(100.0, "Test payment", fallback_service=mock_usdt_service)

        assert result is not None
        assert result["fallback"] is True

    @patch.object(PixGoService, '_create_payment_internal')
    def test_create_payment_timeout_fallback(self, mock_internal):
        """Test timeout fallback to USDT"""
        mock_internal.side_effect = PixGoTimeoutError("Timeout")

        mock_usdt_service = Mock()
        mock_usdt_service.create_payment.return_value = {
            "payment_id": "usdt_123",
            "qr_code": "usdt_qr_code"
        }

        result = self.service.create_payment(100.0, "Test payment", fallback_service=mock_usdt_service)

        assert result is not None
        assert result["fallback"] is True

    @patch.object(PixGoService, '_create_payment_internal')
    def test_create_payment_api_error_fallback(self, mock_internal):
        """Test API error fallback to USDT"""
        mock_usdt_service = Mock()
        mock_usdt_service.create_payment.return_value = {
            "payment_id": "usdt_123",
            "qr_code": "usdt_qr_code"
        }

        mock_internal.side_effect = PixGoAPIError("API Error")

        result = self.service.create_payment(100.0, "Test payment", fallback_service=mock_usdt_service)

        assert result is not None
        assert result["fallback"] is True

    @patch.object(PixGoService, '_create_payment_internal')
    def test_create_payment_validation_error_no_fallback(self, mock_internal):
        """Test validation error doesn't trigger fallback"""
        mock_internal.side_effect = PixGoValidationError("Validation error")

        result = self.service.create_payment(100.0, "Test payment", fallback_service=Mock())

        assert result is None

    @patch.object(PixGoService, '_create_payment_internal')
    def test_create_payment_unexpected_error_no_fallback(self, mock_internal):
        """Test unexpected error doesn't trigger fallback"""
        mock_internal.side_effect = Exception("Unexpected error")

        result = self.service.create_payment(100.0, "Test payment", fallback_service=Mock())

        assert result is None

    def test_fallback_to_usdt_success(self):
        """Test successful USDT fallback"""
        mock_usdt_service = Mock()
        mock_usdt_service.get_payment_address.return_value = "0x1234567890abcdef"
        mock_usdt_service.get_payment_instructions.return_value = "Pay 10.0 USDT to 0x1234567890abcdef"

        result = self.service._fallback_to_usdt(100.0, "Test payment", mock_usdt_service)

        assert result is not None
        assert result["payment_method"] == "USDT"
        assert result["amount"] == 100.0
        assert result["usdt_address"] == "0x1234567890abcdef"
        assert result["fallback"] is True

    def test_fallback_to_usdt_failure(self):
        """Test failed USDT fallback"""
        mock_usdt_service = Mock()
        mock_usdt_service.get_payment_address.side_effect = Exception("USDT service unavailable")

        result = self.service._fallback_to_usdt(100.0, "Test payment", mock_usdt_service)

        assert result is None

    def test_fallback_to_usdt_exception(self):
        """Test USDT fallback with exception"""
        mock_usdt_service = Mock()
        mock_usdt_service.get_payment_address.side_effect = Exception("USDT error")

        result = self.service._fallback_to_usdt(100.0, "Test payment", mock_usdt_service)

        assert result is None
