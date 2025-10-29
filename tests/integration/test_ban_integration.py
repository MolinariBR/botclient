from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram import Chat, Message, Update
from telegram import User as TelegramUser

from src.handlers.admin_handlers import AdminHandlers
from src.models.admin import Admin
from src.models.group import Group, GroupMembership
from src.models.user import User
from src.services.telegram_service import TelegramService


class TestBanIntegration:
    """Integration tests for ban functionality"""

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
    def mock_telegram_service(self):
        """Mock telegram service"""
        return Mock(spec=TelegramService)

    @pytest.fixture
    def mock_logging_service(self):
        """Mock logging service"""
        return Mock()

    @pytest.fixture
    def admin_handlers(self, db_session, mock_telegram_service, mock_logging_service):
        """Admin handlers instance with real database"""
        return AdminHandlers(db_session, mock_telegram_service, mock_logging_service)

    def create_test_admin(self, db_session, telegram_id="12345", username="admin"):
        """Create a test admin in the database"""
        admin = Admin(
            telegram_id=telegram_id,
            username=username
        )
        db_session.add(admin)
        db_session.commit()
        return admin

    def create_test_user(self, db_session, telegram_id="67890", username="testuser", is_banned=False):
        """Create a test user in the database"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name="Test",
            last_name="User",
            is_banned=is_banned
        )
        db_session.add(user)
        db_session.commit()
        return user

    def create_test_group(self, db_session, telegram_group_id="-1001234567890", name="Test Group"):
        """Create a test group in the database"""
        group = Group(
            telegram_group_id=telegram_group_id,
            name=name
        )
        db_session.add(group)
        db_session.commit()
        return group

    def create_test_membership(self, db_session, user, group):
        """Create a test group membership"""
        membership = GroupMembership(
            user_id=user.id,
            group_id=group.id
        )
        db_session.add(membership)
        db_session.commit()
        return membership

    @pytest.mark.asyncio
    async def test_ban_handler_successful_ban_integration(self, admin_handlers, db_session):
        """Integration test for successful user ban"""
        # Create test data
        admin = self.create_test_admin(db_session)
        user = self.create_test_user(db_session, is_banned=False)
        group = self.create_test_group(db_session)
        membership = self.create_test_membership(db_session, user, group)

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int(admin.telegram_id)

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        context = Mock()
        context.args = [user.username]

        # Mock telegram service for kicking user
        admin_handlers.telegram.kick_chat_member = AsyncMock(return_value=True)

        # Execute ban handler
        await admin_handlers.ban_handler(update, context)

        # Refresh user from database
        db_session.refresh(user)

        # Assert user was banned
        assert user.is_banned == True

        # Assert membership was removed
        membership_count = db_session.query(GroupMembership).filter_by(user_id=user.id).count()
        assert membership_count == 0

        # Assert telegram kick was called
        admin_handlers.telegram.kick_chat_member.assert_called_once_with(
            int(group.telegram_group_id), int(user.telegram_id)
        )

        # Assert admin notification
        message.reply_text.assert_called_once_with(f"Usuário @{user.username} banido permanentemente.")

    @pytest.mark.asyncio
    async def test_ban_handler_user_already_banned_integration(self, admin_handlers, db_session):
        """Integration test for attempting to ban already banned user"""
        # Create test data
        admin = self.create_test_admin(db_session)
        user = self.create_test_user(db_session, is_banned=True)  # Already banned

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int(admin.telegram_id)

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        context = Mock()
        context.args = [user.username]

        # Execute ban handler
        await admin_handlers.ban_handler(update, context)

        # Refresh user from database
        db_session.refresh(user)

        # Assert user is still banned (no change)
        assert user.is_banned == True

        # Assert no telegram operations were called
        admin_handlers.telegram.kick_chat_member.assert_not_called()

        # Assert appropriate message
        message.reply_text.assert_called_once_with(f"Usuário @{user.username} já está banido.")

    @pytest.mark.asyncio
    async def test_ban_handler_remove_from_multiple_groups_integration(self, admin_handlers, db_session):
        """Integration test for banning user from multiple groups"""
        # Create test data
        admin = self.create_test_admin(db_session)
        user = self.create_test_user(db_session, is_banned=False)

        # Create multiple groups and memberships
        group1 = self.create_test_group(db_session, "-1001111111111", "Group 1")
        group2 = self.create_test_group(db_session, "-1002222222222", "Group 2")

        membership1 = self.create_test_membership(db_session, user, group1)
        membership2 = self.create_test_membership(db_session, user, group2)

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int(admin.telegram_id)

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        context = Mock()
        context.args = [user.username]

        # Mock telegram service for kicking user from multiple groups
        admin_handlers.telegram.kick_chat_member = AsyncMock(return_value=True)

        # Execute ban handler
        await admin_handlers.ban_handler(update, context)

        # Refresh user from database
        db_session.refresh(user)

        # Assert user was banned
        assert user.is_banned == True

        # Assert all memberships were removed
        membership_count = db_session.query(GroupMembership).filter_by(user_id=user.id).count()
        assert membership_count == 0

        # Assert telegram kick was called for each group
        expected_calls = [
            ((int(group1.telegram_group_id), int(user.telegram_id)),),
            ((int(group2.telegram_group_id), int(user.telegram_id)),)
        ]
        admin_handlers.telegram.kick_chat_member.assert_has_calls(expected_calls, any_order=True)
        assert admin_handlers.telegram.kick_chat_member.call_count == 2

        # Assert admin notification
        message.reply_text.assert_called_once_with(f"Usuário @{user.username} banido permanentemente.")

    @pytest.mark.asyncio
    async def test_ban_handler_telegram_kick_fails_integration(self, admin_handlers, db_session):
        """Integration test for ban when telegram kick fails"""
        # Create test data
        admin = self.create_test_admin(db_session)
        user = self.create_test_user(db_session, is_banned=False)
        group = self.create_test_group(db_session)
        membership = self.create_test_membership(db_session, user, group)

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int(admin.telegram_id)

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        context = Mock()
        context.args = [user.username]

        # Mock telegram service to fail kicking
        admin_handlers.telegram.kick_chat_member = AsyncMock(return_value=False)

        # Execute ban handler
        await admin_handlers.ban_handler(update, context)

        # Refresh user from database
        db_session.refresh(user)

        # Assert user was still banned (ban logic succeeded)
        assert user.is_banned == True

        # Assert membership was still removed
        membership_count = db_session.query(GroupMembership).filter_by(user_id=user.id).count()
        assert membership_count == 0

        # Assert telegram kick was attempted
        admin_handlers.telegram.kick_chat_member.assert_called_once_with(
            int(group.telegram_group_id), int(user.telegram_id)
        )

        # Assert admin notification (ban still succeeded despite kick failure)
        message.reply_text.assert_called_once_with(f"Usuário @{user.username} banido permanentemente.")

    @pytest.mark.asyncio
    async def test_ban_handler_prevents_reentry_integration(self, admin_handlers, db_session):
        """Integration test to verify banned user cannot re-enter groups"""
        # This test verifies the ban flag prevents re-entry logic
        # (The actual re-entry prevention would be implemented in group join handlers)

        # Create test data
        admin = self.create_test_admin(db_session)
        user = self.create_test_user(db_session, is_banned=False)

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int(admin.telegram_id)

        message = Mock(spec=Message)
        message.reply_text = AsyncMock()

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        context = Mock()
        context.args = [user.username]

        # Execute ban handler
        await admin_handlers.ban_handler(update, context)

        # Refresh user from database
        db_session.refresh(user)

        # Assert the ban flag is set (this would be checked by join handlers)
        assert user.is_banned == True

        # In a real scenario, join handlers would check this flag
        # and prevent the user from joining groups
        message.reply_text.assert_called_once_with(f"Usuário @{user.username} banido permanentemente.")