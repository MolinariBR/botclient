from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram import Update, User as TelegramUser, Message

from src.handlers.user_handlers import UserHandlers
from src.models.user import User
from src.services.pixgo_service import PixGoService
from src.services.usdt_service import USDTService


class TestStatusIntegration:
    """Integration tests for status display functionality"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing"""
        engine = create_engine("sqlite:///:memory:")

        # Import all models to ensure they use the same Base
        from src.models.base import Base
        from src.models import user, admin, group, payment  # Import all model modules

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
            "id": "pix_123",
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
        """User handlers instance with real database and mock services"""
        return UserHandlers(db_session, mock_pixgo_service, mock_usdt_service)

    def create_test_user(self, db_session, **kwargs):
        """Create a test user in the database"""
        defaults = {
            "telegram_id": "12345",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "status_assinatura": "ativo",
            "data_expiracao": datetime.utcnow() + timedelta(days=30),
            "is_banned": False,
            "is_muted": False
        }
        defaults.update(kwargs)

        user = User(**defaults)
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_status_display_active_user(self, user_handlers, db_session):
        """Test status display for active user with all fields"""
        # Create test user
        test_user = self.create_test_user(db_session)

        # Mock Telegram update
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int("12345")  # Use the test user ID directly

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message

        context = Mock()

        # Execute status handler
        await user_handlers.status_handler(update, context)

        # Verify response
        message.reply_text.assert_called_once()
        response = message.reply_text.call_args[0][0]

        assert "📊 **Status da Assinatura**" in response
        assert "Status: ativo" in response
        assert "Expiração:" in response
        # Should not show ban/mute status for basic status display

    @pytest.mark.asyncio
    async def test_status_display_expired_user(self, user_handlers, db_session):
        """Test status display for user with expired subscription"""
        # Create test user with expired subscription
        test_user = self.create_test_user(
            db_session,
            status_assinatura="expirado",
            data_expiracao=datetime.utcnow() - timedelta(days=1)
        )

        # Mock Telegram update
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int("12345")  # Use the test user ID directly

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message

        context = Mock()

        # Execute status handler
        await user_handlers.status_handler(update, context)

        # Verify response
        message.reply_text.assert_called_once()
        response = message.reply_text.call_args[0][0]

        assert "📊 **Status da Assinatura**" in response
        assert "Status: expirado" in response
        assert "Expiração:" in response

    @pytest.mark.asyncio
    async def test_status_display_user_not_found(self, user_handlers, db_session):
        """Test status display when user is not found in database"""
        # Mock Telegram update for non-existent user
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 99999  # Non-existent user

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message

        context = Mock()

        # Execute status handler
        await user_handlers.status_handler(update, context)

        # Verify error response
        message.reply_text.assert_called_once()
        response = message.reply_text.call_args[0][0]

        assert "Usuário não encontrado. Certifique-se de ter iniciado uma conversa com o bot." == response

    @pytest.mark.asyncio
    async def test_status_display_english_status(self, user_handlers, db_session):
        """Test status display with English status that gets title-cased"""
        # Create test user with English status
        test_user = self.create_test_user(
            db_session,
            status_assinatura="active"
        )

        # Mock Telegram update
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int("12345")  # Use the test user ID directly

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message

        context = Mock()

        # Execute status handler
        await user_handlers.status_handler(update, context)

        # Verify response shows title-cased status
        message.reply_text.assert_called_once()
        response = message.reply_text.call_args[0][0]

        assert "Status: Active" in response