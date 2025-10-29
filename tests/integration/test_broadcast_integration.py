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


class TestBroadcastIntegration:
    """Integration tests for broadcast functionality"""

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
    async def test_broadcast_to_all_members_integration(self, admin_handlers, db_session):
        """Integration test for broadcasting message to all group members"""
        # Create test data
        admin = self.create_test_admin(db_session)

        # Create multiple users and groups
        user1 = self.create_test_user(db_session, telegram_id="11111", username="user1")
        user2 = self.create_test_user(db_session, telegram_id="22222", username="user2")
        user3 = self.create_test_user(db_session, telegram_id="33333", username="user3")

        group1 = self.create_test_group(db_session, telegram_group_id="-100111", name="Group 1")
        group2 = self.create_test_group(db_session, telegram_group_id="-100222", name="Group 2")

        # Add users to groups
        self.create_test_membership(db_session, user1, group1)
        self.create_test_membership(db_session, user2, group1)
        self.create_test_membership(db_session, user3, group2)

        # Mock telegram service send_message
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Execute broadcast
        broadcast_message = "Test broadcast message"
        await admin_handlers._broadcast_to_all_members(broadcast_message)

        # Verify send_message was called for each user
        assert admin_handlers.telegram.send_message.call_count == 3

        # Check the calls
        calls = admin_handlers.telegram.send_message.call_args_list

        # Should send to user1
        assert any(call[0][0] == int(user1.telegram_id) for call in calls)
        # Should send to user2
        assert any(call[0][0] == int(user2.telegram_id) for call in calls)
        # Should send to user3
        assert any(call[0][0] == int(user3.telegram_id) for call in calls)

        # Check message content
        for call in calls:
            message_content = call[0][1]
            assert "📢 **Mensagem do Administrador**" in message_content
            assert broadcast_message in message_content

    @pytest.mark.asyncio
    async def test_broadcast_with_send_failures_integration(self, admin_handlers, db_session):
        """Integration test for broadcast with some send failures"""
        # Create test data
        user1 = self.create_test_user(db_session, telegram_id="11111", username="user1")
        user2 = self.create_test_user(db_session, telegram_id="22222", username="user2")

        group = self.create_test_group(db_session)

        self.create_test_membership(db_session, user1, group)
        self.create_test_membership(db_session, user2, group)

        # Mock telegram service to fail for user2
        async def mock_send_message(telegram_id, message):
            if telegram_id == int(user2.telegram_id):
                raise Exception("Send failed")
            return True

        admin_handlers.telegram.send_message = AsyncMock(side_effect=mock_send_message)

        # Execute broadcast
        await admin_handlers._broadcast_to_all_members("Test message")

        # Verify send_message was called for both users
        assert admin_handlers.telegram.send_message.call_count == 2

        # Check calls were made to both users
        calls = admin_handlers.telegram.send_message.call_args_list
        user_ids_called = [call[0][0] for call in calls]
        assert int(user1.telegram_id) in user_ids_called
        assert int(user2.telegram_id) in user_ids_called

    @pytest.mark.asyncio
    async def test_broadcast_empty_groups_integration(self, admin_handlers, db_session):
        """Integration test for broadcast when there are no groups/members"""
        # No test data created - empty database

        # Mock telegram service
        admin_handlers.telegram.send_message = AsyncMock()

        # Execute broadcast
        await admin_handlers._broadcast_to_all_members("Test message")

        # Verify no messages were sent
        admin_handlers.telegram.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_multiple_groups_integration(self, admin_handlers, db_session):
        """Integration test for broadcast across multiple groups"""
        # Create multiple groups with members
        group1 = self.create_test_group(db_session, telegram_group_id="-100111", name="Group 1")
        group2 = self.create_test_group(db_session, telegram_group_id="-100222", name="Group 2")

        # Group 1 has 2 members
        user1 = self.create_test_user(db_session, telegram_id="11111", username="user1")
        user2 = self.create_test_user(db_session, telegram_id="22222", username="user2")
        self.create_test_membership(db_session, user1, group1)
        self.create_test_membership(db_session, user2, group1)

        # Group 2 has 1 member
        user3 = self.create_test_user(db_session, telegram_id="33333", username="user3")
        self.create_test_membership(db_session, user3, group2)

        # Mock telegram service
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Execute broadcast
        await admin_handlers._broadcast_to_all_members("Multi-group broadcast")

        # Verify all 3 users received the message
        assert admin_handlers.telegram.send_message.call_count == 3

        # Check all users were contacted
        calls = admin_handlers.telegram.send_message.call_args_list
        user_ids_called = [call[0][0] for call in calls]
        assert int(user1.telegram_id) in user_ids_called
        assert int(user2.telegram_id) in user_ids_called
        assert int(user3.telegram_id) in user_ids_called