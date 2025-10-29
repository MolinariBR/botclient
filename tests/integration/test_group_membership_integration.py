from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram import Chat, Message
from telegram import User as TelegramUser
from telegram.ext import ContextTypes

from src.handlers.admin_handlers import AdminHandlers
from src.models.admin import Admin
from src.models.group import Group, GroupMembership
from src.models.user import User
from src.services.telegram_service import TelegramService


class TestGroupMembershipIntegration:
    """Integration tests for group membership management flow"""

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
    def telegram_service(self):
        """Mock telegram service for testing"""
        return Mock(spec=TelegramService)

    @pytest.fixture
    def mock_logging_service(self):
        """Mock logging service"""
        return Mock()

    @pytest.fixture
    def admin_handlers(self, db_session, telegram_service, mock_logging_service):
        """Admin handlers instance with real database"""
        return AdminHandlers(db_session, telegram_service, mock_logging_service)

    def create_test_admin(self, db_session, telegram_id="12345", username="admin"):
        """Create a test admin in the database"""
        admin = Admin(
            telegram_id=telegram_id,
            username=username
        )
        db_session.add(admin)
        db_session.commit()
        return admin

    def create_test_user(self, db_session, telegram_id="67890", username="testuser"):
        """Create a test user in the database"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name="Test",
            last_name="User"
        )
        db_session.add(user)
        db_session.commit()
        return user

    def test_complete_add_user_to_group_flow(self, admin_handlers, db_session):
        """Test complete flow of admin adding user to group"""
        # Setup test data
        admin = self.create_test_admin(db_session)
        user = self.create_test_user(db_session)

        # Mock Telegram service responses
        admin_handlers.telegram.create_chat_invite_link = AsyncMock(return_value="https://t.me/joinchat/abc123")
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Create mock Telegram objects
        mock_admin_user = Mock(spec=TelegramUser)
        mock_admin_user.id = 12345

        mock_message = Mock(spec=Message)

        mock_chat = Mock(spec=Chat)
        mock_chat.id = -1001234567890
        mock_chat.title = "Test VIP Group"

        # Create update and context
        update = Mock()
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat

        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = [user.username]

        # Execute the add handler
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Verify database state
        # Check that group was created
        group = db_session.query(Group).filter_by(telegram_group_id=str(mock_chat.id)).first()
        assert group is not None
        assert group.name == mock_chat.title

        # Check that membership was created
        membership = db_session.query(GroupMembership).filter_by(
            user_id=user.id, group_id=group.id
        ).first()
        assert membership is not None
        assert membership.user_id == user.id
        assert membership.group_id == group.id
        assert membership.joined_at is not None

        # Verify Telegram service calls
        admin_handlers.telegram.create_chat_invite_link.assert_called_once_with(
            int(group.telegram_group_id),
            name=f"Convite para {user.username}"
        )

        expected_message = (
            f"Você foi adicionado ao grupo VIP: {group.name}\n\n"
            f"Link de convite: https://t.me/joinchat/abc123"
        )
        admin_handlers.telegram.send_message.assert_called_once_with(
            67890,  # user.telegram_id as int
            expected_message
        )

        # Verify admin notification
        mock_message.reply_text.assert_called_once_with("Usuário @testuser adicionado com sucesso ao grupo.")

    def test_add_user_not_found_flow(self, admin_handlers, db_session):
        """Test add user flow when target user doesn't exist"""
        # Setup test data
        admin = self.create_test_admin(db_session)

        # Create mock Telegram objects
        mock_admin_user = Mock(spec=TelegramUser)
        mock_admin_user.id = 12345

        mock_message = Mock(spec=Message)

        mock_chat = Mock(spec=Chat)
        mock_chat.id = -1001234567890
        mock_chat.title = "Test VIP Group"

        # Create update and context
        update = Mock()
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat

        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ["nonexistentuser"]

        # Execute the add handler
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Verify user not found message
        mock_message.reply_text.assert_called_once_with(
            "Usuário @nonexistentuser não encontrado. Certifique-se de que o usuário iniciou uma conversa com o bot."
        )

        # Verify no database changes
        groups = db_session.query(Group).all()
        assert len(groups) == 0

        memberships = db_session.query(GroupMembership).all()
        assert len(memberships) == 0

    def test_add_user_access_denied_flow(self, admin_handlers, db_session):
        """Test add user flow when user is not admin"""
        # Setup test data - no admin created
        user = self.create_test_user(db_session)

        # Create mock Telegram objects for non-admin user
        mock_regular_user = Mock(spec=TelegramUser)
        mock_regular_user.id = 99999  # Different ID from admin

        mock_message = Mock(spec=Message)

        mock_chat = Mock(spec=Chat)
        mock_chat.id = -1001234567890
        mock_chat.title = "Test VIP Group"

        # Create update and context
        update = Mock()
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat

        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = [user.username]

        # Execute the add handler
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Verify access denied
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

        # Verify no database changes
        groups = db_session.query(Group).all()
        assert len(groups) == 0

        memberships = db_session.query(GroupMembership).all()
        assert len(memberships) == 0