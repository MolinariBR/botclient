from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.user import User
from src.services.pixgo_service import PixGoService


class TestPaymentIntegration:
    """Integration tests for payment creation and QR generation flow"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing"""
        engine = create_engine("sqlite:///:memory:")

        # Import all models to ensure they use the same Base
        from src.models.base import Base

        # Create all tables using the shared Base
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def pixgo_service(self):
        """Real PixGo service instance"""
        return PixGoService("test_api_key")

    def create_test_user(self, db_session):
        """Create a test user in the database"""
        user = User(
            telegram_id="12345",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @patch("src.services.pixgo_service.requests.Session.post")
    @patch("src.services.pixgo_service.requests.Session.get")
    def test_payment_creation_and_qr_generation_flow(self, mock_get, mock_post, pixgo_service, db_session):
        """Test complete payment creation and QR generation flow"""
        # Setup mocks for successful API calls
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "payment_id": "pix_123456",
                "qr_code": "test_qr_code_data",
                "qr_image_url": "http://example.com/qr.png",
                "expires_at": "2025-10-28T10:00:00Z"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mock_qr_response = Mock()
        mock_qr_response.json.return_value = {
            "qr_code": "actual_qr_code_data"
        }
        mock_qr_response.raise_for_status.return_value = None
        mock_get.return_value = mock_qr_response

        # Create test user
        user = self.create_test_user(db_session)

        # Test payment creation
        payment_data = pixgo_service.create_payment(
            amount=10.0,
            description="Test payment",
            payer_info={"customer_name": "Test User"}
        )

        assert payment_data is not None
        assert payment_data["payment_id"] == "pix_123456"
        assert payment_data["qr_code"] == "test_qr_code_data"

        # Test QR code retrieval
        qr_code = pixgo_service.get_qr_code("pix_123456")
        assert qr_code == "actual_qr_code_data"

        # Verify API calls
        mock_post.assert_called_once()
        post_call_args = mock_post.call_args
        payload = post_call_args[1]["json"]
        assert payload["amount"] == 10.0
        assert payload["description"] == "Test payment"
        assert payload["currency"] == "BRL"
        assert payload["customer_name"] == "Test User"

        mock_get.assert_called_once_with("https://api.pixgo.com/payment/pix_123456/qr")

    @patch("src.services.pixgo_service.requests.Session.post")
    def test_payment_creation_failure_handling(self, mock_post, pixgo_service):
        """Test payment creation failure handling"""
        # Setup mock for failed API call
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": False,
            "error": "Invalid API key"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test payment creation failure
        payment_data = pixgo_service.create_payment(
            amount=10.0,
            description="Test payment"
        )

        assert payment_data is None
        mock_post.assert_called_once()

    @patch("src.services.pixgo_service.requests.Session.post")
    @patch("src.services.pixgo_service.requests.Session.get")
    def test_payment_status_checking_flow(self, mock_get, mock_post, pixgo_service):
        """Test payment status checking flow"""
        # Setup mock for status check
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "completed"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test status checking
        status = pixgo_service.get_payment_status("pix_123456")
        assert status == "completed"

        mock_get.assert_called_once_with("https://api.pixgo.com/payment/pix_123456/status")

    def test_service_initialization(self, pixgo_service):
        """Test PixGo service initialization"""
        assert pixgo_service.api_key == "test_api_key"
        assert pixgo_service.base_url == "https://api.pixgo.com"
        assert pixgo_service.session is not None

    @patch("src.services.pixgo_service.requests.Session.post")
    def test_payment_creation_with_custom_base_url(self, mock_post):
        """Test payment creation with custom base URL"""
        custom_service = PixGoService("test_key", "https://custom.pixgo.com")

        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"payment_id": "pix_123"}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        payment_data = custom_service.create_payment(5.0, "Custom payment")

        assert payment_data is not None
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://custom.pixgo.com/payment/create"
