from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.handlers.admin_handlers import AdminHandlers
from src.models.admin import Admin
from src.models.group import Group, GroupMembership
from src.models.user import User
from src.services.telegram_service import TelegramService


class TestKickIntegration:
    """Integration tests for /kick command"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing"""
        engine = create_engine("sqlite:///:memory:")

        # Import all models to ensure they use the same Base
        from src.models.admin import Base

        # Create all tables using the shared Base
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def telegram_service(self):
        """Mock telegram service"""
        service = Mock(spec=TelegramService)
        service.kick_chat_member = AsyncMock(return_value=True)
        return service

    @pytest.fixture
    def mock_logging_service(self):
        """Mock logging service"""
        return Mock()

    @pytest.fixture
    def admin_handlers(self, db_session, telegram_service, mock_logging_service):
        """Admin handlers instance with real database"""
        return AdminHandlers(db_session, telegram_service, mock_logging_service)

    def create_test_data(self, db_session):
        """Create test data in database"""
        # Create admin
        admin = Admin(telegram_id="12345", username="admin")
        db_session.add(admin)
        db_session.commit()  # Commit to get ID

        # Create regular user
        user = User(
            telegram_id="67890",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        db_session.add(user)
        db_session.commit()  # Commit to get ID

        # Create group
        group = Group(
            telegram_group_id="-1001234567890",
            name="Test VIP Group"
        )
        db_session.add(group)
        db_session.commit()  # Commit to get ID

        # Create membership
        membership = GroupMembership(user_id=user.id, group_id=group.id)
        db_session.add(membership)
        db_session.commit()  # Commit to get ID

        return admin, user, group, membership

    @pytest.mark.asyncio
    async def test_kick_integration_success(self, admin_handlers, db_session, telegram_service):
        """Test complete kick integration flow"""
        # Setup test data
        admin, user, group, membership = self.create_test_data(db_session)

        # Create mock update
        from telegram import Chat, Message, Update
        from telegram import User as TelegramUser

        mock_admin_user = Mock(spec=TelegramUser)
        mock_admin_user.id = 12345

        mock_message = Mock(spec=Message)
        mock_message.reply_text = AsyncMock()

        mock_chat = Mock(spec=Chat)
        mock_chat.id = -1001234567890

        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat

        context = Mock()
        context.args = ["testuser"]

        # Execute kick
        await admin_handlers.kick_handler(update, context)

        # Verify membership was removed from database
        db_membership = db_session.query(GroupMembership).filter_by(
            user_id=user.id, group_id=group.id
        ).first()
        assert db_membership is None

        # Verify telegram kick was called
        telegram_service.kick_chat_member.assert_called_once_with(
            -1001234567890, 67890
        )

        # Verify success message
        mock_message.reply_text.assert_called_once_with(
            "Usuário @testuser removido do grupo com sucesso."
        )

    @pytest.mark.asyncio
    async def test_kick_integration_telegram_failure(self, admin_handlers, db_session, telegram_service):
        """Test kick integration when Telegram API fails"""
        # Setup test data
        admin, user, group, membership = self.create_test_data(db_session)

        # Make telegram kick fail
        telegram_service.kick_chat_member = AsyncMock(return_value=False)

        # Create mock update
        from telegram import Chat, Message, Update
        from telegram import User as TelegramUser

        mock_admin_user = Mock(spec=TelegramUser)
        mock_admin_user.id = 12345

        mock_message = Mock(spec=Message)
        mock_message.reply_text = AsyncMock()

        mock_chat = Mock(spec=Chat)
        mock_chat.id = -1001234567890

        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat

        context = Mock()
        context.args = ["testuser"]

        # Execute kick
        await admin_handlers.kick_handler(update, context)

        # Verify membership was still removed from database
        db_membership = db_session.query(GroupMembership).filter_by(
            user_id=user.id, group_id=group.id
        ).first()
        assert db_membership is None

        # Verify telegram kick was attempted
        telegram_service.kick_chat_member.assert_called_once_with(
            -1001234567890, 67890
        )

        # Verify error message
        mock_message.reply_text.assert_called_once_with(
            "Usuário @testuser removido do banco de dados, mas falha ao remover do grupo Telegram."
        )

    @pytest.mark.asyncio
    async def test_kick_integration_user_not_in_group(self, admin_handlers, db_session, telegram_service):
        """Test kick integration when user is not in the group"""
        # Setup test data but remove membership
        admin, user, group, membership = self.create_test_data(db_session)
        db_session.delete(membership)
        db_session.commit()

        # Create mock update
        from telegram import Chat, Message, Update
        from telegram import User as TelegramUser

        mock_admin_user = Mock(spec=TelegramUser)
        mock_admin_user.id = 12345

        mock_message = Mock(spec=Message)
        mock_message.reply_text = AsyncMock()

        mock_chat = Mock(spec=Chat)
        mock_chat.id = -1001234567890

        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat

        context = Mock()
        context.args = ["testuser"]

        # Execute kick
        await admin_handlers.kick_handler(update, context)

        # Verify telegram kick was not called
        telegram_service.kick_chat_member.assert_not_called()

        # Verify error message
        mock_message.reply_text.assert_called_once_with(
            "Usuário @testuser não é membro deste grupo."
        )
