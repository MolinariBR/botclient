from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram import Chat, Message, Update
from telegram import User as TelegramUser

from src.handlers.user_handlers import UserHandlers
from src.models.payment import Payment
from src.models.user import User
from src.services.pixgo_service import PixGoService
from src.services.usdt_service import USDTService
from src.utils.config import Config


class TestRenewIntegration:
    """Integration tests for subscription renewal flow"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing"""
        engine = create_engine("sqlite:///:memory:")

        # Import all models to ensure they use the same Base and relationships are resolved
        from src.models.base import Base
        from src.models.user import User
        from src.models.payment import Payment
        from src.models.group import Group, GroupMembership
        from src.models.admin import Admin

        # Create all tables using the shared Base
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def mock_pixgo_service(self):
        """Mock PixGo service"""
        service = Mock(spec=PixGoService)
        service.create_payment = Mock(return_value={
            "id": "pix_renew_123",
            "qr_code": "qr_code_data"
        })
        service.get_qr_code = Mock(return_value="QR_CODE_DATA")
        return service

    @pytest.fixture
    def mock_usdt_service(self):
        """Mock USDT service"""
        service = Mock(spec=USDTService)
        service.get_payment_instructions = Mock(return_value="USDT payment instructions")
        return service

    @pytest.fixture
    def user_handlers(self, db_session, mock_pixgo_service, mock_usdt_service):
        """User handlers instance with real database"""
        return UserHandlers(db_session, mock_pixgo_service, mock_usdt_service)

    def create_test_user(self, db_session, telegram_id="12345", username="testuser", status="active"):
        """Create a test user in the database"""
        import datetime
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name="Test",
            last_name="User",
            status_assinatura=status,
            data_expiracao=datetime.datetime.utcnow() + datetime.timedelta(days=30) if status == "active" else None
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_renew_handler_successful_pix_payment_integration(self, user_handlers, db_session, mock_pixgo_service):
        """Integration test for successful subscription renewal with PIX payment"""
        # Create test user with active subscription
        user = self.create_test_user(db_session, telegram_id="12345", username="testuser", status="active")

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345
        telegram_user.username = "testuser"

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        context = Mock()

        # Execute renew handler
        await user_handlers.renew_handler(update, context)

        # Verify payment was created in database
        payment = db_session.query(Payment).filter_by(user_id=user.id).first()
        assert payment is not None
        assert payment.pixgo_payment_id == "pix_renew_123"
        assert payment.amount == Config.SUBSCRIPTION_PRICE
        assert payment.payment_method == "pix"
        assert payment.status == "pending"

        # Verify PIX service was called correctly
        mock_pixgo_service.create_payment.assert_called_once_with(
            amount=Config.SUBSCRIPTION_PRICE,
            description="Renovação de Assinatura VIP - testuser",
            payer_info={"telegram_id": "12345"}
        )
        mock_pixgo_service.get_qr_code.assert_called_once_with("pix_renew_123")

        # Verify response message
        message.reply_text.assert_called_once()
        response = message.reply_text.call_args[0][0]
        assert "🔄 **Renovação de Assinatura**" in response
        assert f"R$ {Config.SUBSCRIPTION_PRICE:.2f}" in response
        assert "QR_CODE_DATA" in response
        assert f"mais {Config.SUBSCRIPTION_DAYS} dias" in response

    @pytest.mark.asyncio
    async def test_renew_handler_pix_fails_fallback_to_usdt_integration(self, user_handlers, db_session, mock_pixgo_service, mock_usdt_service):
        """Integration test for renewal with PIX failure and USDT fallback"""
        # Create test user with active subscription
        user = self.create_test_user(db_session, telegram_id="12345", username="testuser", status="active")

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345
        telegram_user.username = "testuser"

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        context = Mock()

        # Mock PIX payment failure
        mock_pixgo_service.create_payment.return_value = None

        # Execute renew handler
        await user_handlers.renew_handler(update, context)

        # Verify no payment was created in database (PIX failed)
        payment = db_session.query(Payment).filter_by(user_id=user.id).first()
        assert payment is None

        # Verify USDT service was called
        mock_usdt_service.get_payment_instructions.assert_called_once_with(Config.SUBSCRIPTION_PRICE)

        # Verify USDT response message
        message.reply_text.assert_called_once_with(
            f"PIX indisponível. Use USDT para renovação:\nUSDT payment instructions"
        )

        # Verify PIX service was attempted
        mock_pixgo_service.create_payment.assert_called_once_with(
            amount=Config.SUBSCRIPTION_PRICE,
            description="Renovação de Assinatura VIP - testuser",
            payer_info={"telegram_id": "12345"}
        )

    @pytest.mark.asyncio
    async def test_renew_handler_expired_subscription_integration(self, user_handlers, db_session):
        """Integration test for renewal attempt with expired subscription"""
        # Create test user with expired subscription
        import datetime
        user = User(
            telegram_id="12345",
            username="testuser",
            first_name="Test",
            last_name="User",
            status_assinatura="active",
            data_expiracao=datetime.datetime.utcnow() - datetime.timedelta(days=1)  # Expired
        )
        db_session.add(user)
        db_session.commit()

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        context = Mock()

        # Execute renew handler
        await user_handlers.renew_handler(update, context)

        # Verify no payment was created
        payment = db_session.query(Payment).filter_by(user_id=user.id).first()
        assert payment is None

        # Verify correct error message
        message.reply_text.assert_called_once_with("Sua assinatura expirou. Use /pay para renovar.")

    @pytest.mark.asyncio
    async def test_renew_handler_no_active_subscription_integration(self, user_handlers, db_session):
        """Integration test for renewal attempt with no active subscription"""
        # Create test user with inactive subscription
        user = self.create_test_user(db_session, telegram_id="12345", username="testuser", status="inactive")

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        context = Mock()

        # Execute renew handler
        await user_handlers.renew_handler(update, context)

        # Verify no payment was created
        payment = db_session.query(Payment).filter_by(user_id=user.id).first()
        assert payment is None

        # Verify correct error message
        message.reply_text.assert_called_once_with("Você não possui uma assinatura ativa. Use /pay para assinar.")