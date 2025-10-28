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


class TestInviteIntegration:
    """Integration tests for invite link generation functionality"""

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
    async def test_invite_link_generation_active_user(self, user_handlers, db_session):
        """Test invite link generation for active user"""
        # Create test user with active subscription
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

        # Execute invite handler
        await user_handlers.invite_handler(update, context)

        # Verify response
        message.reply_text.assert_called_once()
        response = message.reply_text.call_args[0][0]

        assert "🎫 **Link de Convite**" in response
        assert "Seu link de convite exclusivo:" in response
        assert "https://t.me/" in response
        assert "?start=invite_" in response
        assert "Rastreamento será implementado em breve" in response

    @pytest.mark.asyncio
    async def test_invite_link_generation_expired_user(self, user_handlers, db_session):
        """Test invite link generation is denied for user with expired subscription"""
        # Create test user with expired subscription
        test_user = self.create_test_user(
            db_session,
            status_assinatura="expirado",
            data_expiracao=datetime.utcnow() - timedelta(days=1)
        )

        # Mock Telegram update
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int("12345")

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message

        context = Mock()

        # Execute invite handler
        await user_handlers.invite_handler(update, context)

        # Verify error response
        message.reply_text.assert_called_once()
        response = message.reply_text.call_args[0][0]

        assert "Você precisa ter uma assinatura ativa para gerar links de convite." == response

    @pytest.mark.asyncio
    async def test_invite_link_generation_user_not_found(self, user_handlers, db_session):
        """Test invite link generation when user is not found in database"""
        # Don't create any user in database

        # Mock Telegram update for non-existent user
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 99999  # Non-existent user

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message

        context = Mock()

        # Execute invite handler
        await user_handlers.invite_handler(update, context)

        # Verify error response
        message.reply_text.assert_called_once()
        response = message.reply_text.call_args[0][0]

        assert "Usuário não encontrado. Use /pay para assinar primeiro." == response

    @pytest.mark.asyncio
    async def test_invite_link_uniqueness(self, user_handlers, db_session):
        """Test that generated invite links are unique"""
        # Create test user
        test_user = self.create_test_user(db_session)

        # Mock Telegram update
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int("12345")

        message1 = Mock(spec=Message)
        message1.reply_text = AsyncMock()

        message2 = Mock(spec=Message)
        message2.reply_text = AsyncMock()

        update1 = Mock(spec=Update)
        update1.effective_user = telegram_user
        update1.message = message1

        update2 = Mock(spec=Update)
        update2.effective_user = telegram_user
        update2.message = message2

        context = Mock()

        # Execute invite handler twice
        await user_handlers.invite_handler(update1, context)
        await user_handlers.invite_handler(update2, context)

        # Verify both responses contain invite links
        response1 = message1.reply_text.call_args[0][0]
        response2 = message2.reply_text.call_args[0][0]

        # Extract invite links from responses
        link1_start = response1.find("https://t.me/")
        link1_end = response1.find("\n", link1_start)
        link1 = response1[link1_start:link1_end].strip()

        link2_start = response2.find("https://t.me/")
        link2_end = response2.find("\n", link2_start)
        link2 = response2[link2_start:link2_end].strip()

        # Links should be different (unique invite codes)
        assert link1 != link2
        assert "start=invite_" in link1
        assert "start=invite_" in link2