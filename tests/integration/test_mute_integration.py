from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch
import asyncio

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram import Chat, Message, Update
from telegram import User as TelegramUser

from src.handlers.admin_handlers import AdminHandlers
from src.models.admin import Admin
from src.models.user import User
from src.services.mute_service import MuteService
from src.services.telegram_service import TelegramService


class TestMuteIntegration:
    """Integration tests for mute functionality"""

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
    def admin_handlers(self, db_session, mock_telegram_service):
        """Admin handlers instance with real database"""
        return AdminHandlers(db_session, mock_telegram_service)

    @pytest.fixture
    def mute_service(self, db_session):
        """Mute service instance with real database"""
        return MuteService(db_session, check_interval=1)  # Fast check interval for testing

    def create_test_admin(self, db_session, telegram_id="12345", username="admin"):
        """Create a test admin in the database"""
        admin = Admin(
            telegram_id=telegram_id,
            username=username
        )
        db_session.add(admin)
        db_session.commit()
        return admin

    def create_test_user(self, db_session, telegram_id="67890", username="testuser",
                        is_muted=False, mute_until=None):
        """Create a test user in the database"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name="Test",
            last_name="User",
            is_muted=is_muted,
            mute_until=mute_until
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_mute_handler_successful_mute_integration(self, admin_handlers, db_session):
        """Integration test for successful user mute"""
        # Create test data
        admin = self.create_test_admin(db_session)
        user = self.create_test_user(db_session, is_muted=False)

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int(admin.telegram_id)

        message = Mock(spec=Message)
        chat = Mock(spec=Chat)

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        update.effective_chat = chat

        # Mock telegram service methods
        admin_handlers.telegram.send_message = AsyncMock()

        # Execute mute command
        await admin_handlers.mute_handler(update, Mock(args=["testuser", "10"]))

        # Verify user was muted in database
        db_session.refresh(user)
        assert user.is_muted == True
        assert user.mute_until is not None

        # Verify mute duration is approximately correct (within 1 second)
        # Get the current time after the mute operation (naive for comparison with DB)
        now_after = datetime.now(timezone.utc).replace(tzinfo=None)
        expected_min = now_after + timedelta(minutes=9, seconds=59)  # Allow 1 second tolerance
        expected_max = now_after + timedelta(minutes=10, seconds=1)

        assert expected_min <= user.mute_until.replace(tzinfo=None) <= expected_max

    @pytest.mark.asyncio
    async def test_mute_handler_unmute_integration(self, admin_handlers, db_session):
        """Integration test for unmuting a user"""
        # Create test data
        admin = self.create_test_admin(db_session)
        user = self.create_test_user(db_session, is_muted=True,
                                   mute_until=datetime.now(timezone.utc) + timedelta(hours=1))

        # Setup Telegram mocks
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = int(admin.telegram_id)

        message = Mock(spec=Message)
        chat = Mock(spec=Chat)

        update = Mock(spec=Update)
        update.effective_user = telegram_user
        update.message = message
        update.effective_chat = chat

        # Execute unmute command (duration = 0)
        await admin_handlers.mute_handler(update, Mock(args=["testuser", "0"]))

        # Verify user was unmuted in database
        db_session.refresh(user)
        assert user.is_muted == False
        assert user.mute_until is None

    @pytest.mark.asyncio
    async def test_mute_service_automatic_unmute_integration(self, mute_service, db_session):
        """Integration test for automatic unmute when timer expires"""
        # Create a muted user with expired mute
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        user = self.create_test_user(db_session, is_muted=True, mute_until=past_time)

        # Start the mute service
        await mute_service.start()

        # Wait for the service to check (it checks every 1 second)
        await asyncio.sleep(2)

        # Stop the service
        await mute_service.stop()

        # Verify user was automatically unmuted
        db_session.refresh(user)
        assert user.is_muted == False
        assert user.mute_until is None

    @pytest.mark.asyncio
    async def test_mute_service_no_action_for_active_mutes_integration(self, mute_service, db_session):
        """Integration test that active mutes are not touched by the service"""
        # Create a muted user with future mute expiration
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        user = self.create_test_user(db_session, is_muted=True, mute_until=future_time)

        # Start the mute service
        await mute_service.start()

        # Wait for the service to check
        await asyncio.sleep(2)

        # Stop the service
        await mute_service.stop()

        # Verify user is still muted
        db_session.refresh(user)
        assert user.is_muted == True
        assert user.mute_until.replace(tzinfo=None) == future_time.replace(tzinfo=None)

    @pytest.mark.asyncio
    async def test_mute_service_multiple_expired_mutes_integration(self, mute_service, db_session):
        """Integration test for handling multiple expired mutes"""
        # Create multiple muted users with expired mutes
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)

        user1 = self.create_test_user(db_session, telegram_id="11111", username="user1",
                                    is_muted=True, mute_until=past_time)
        user2 = self.create_test_user(db_session, telegram_id="22222", username="user2",
                                    is_muted=True, mute_until=past_time)
        user3 = self.create_test_user(db_session, telegram_id="33333", username="user3",
                                    is_muted=True, mute_until=past_time)

        # Start the mute service
        await mute_service.start()

        # Wait for the service to check
        await asyncio.sleep(2)

        # Stop the service
        await mute_service.stop()

        # Verify all users were unmuted
        for user in [user1, user2, user3]:
            db_session.refresh(user)
            assert user.is_muted == False
            assert user.mute_until is None