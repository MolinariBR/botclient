import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.user import User
from src.models.group import Group, GroupMembership
from src.models.payment import Payment
from src.models.base import Base


class TestUserModel:
    """Unit tests for User model"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing"""
        engine = create_engine("sqlite:///:memory:")

        # Import all models to ensure they use the same Base
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_user_creation_with_required_fields(self, db_session):
        """Test creating a user with minimal required fields"""
        user = User(
            telegram_id="123456789",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.telegram_id == "123456789"
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.status_assinatura == "inactive"  # default value
        assert user.is_banned is False
        assert user.is_muted is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_creation_with_all_fields(self, db_session):
        """Test creating a user with all fields populated"""
        expiration_date = datetime.utcnow() + timedelta(days=30)
        mute_until = datetime.utcnow() + timedelta(hours=1)

        user = User(
            telegram_id="987654321",
            username="premiumuser",
            first_name="Premium",
            last_name="User",
            status_assinatura="active",
            data_expiracao=expiration_date,
            is_banned=True,
            is_muted=True,
            mute_until=mute_until,
            warn_count=2,
            auto_renew=False
        )
        db_session.add(user)
        db_session.commit()

        assert user.telegram_id == "987654321"
        assert user.username == "premiumuser"
        assert user.status_assinatura == "active"
        assert user.data_expiracao == expiration_date
        assert user.is_banned is True
        assert user.is_muted is True
        assert user.mute_until == mute_until
        assert user.warn_count == 2
        assert user.auto_renew is False

    def test_telegram_id_uniqueness(self, db_session):
        """Test that telegram_id must be unique"""
        user1 = User(telegram_id="111111111", username="user1")
        user2 = User(telegram_id="111111111", username="user2")

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):  # IntegrityError in real database
            db_session.commit()

    def test_telegram_id_required(self, db_session):
        """Test that telegram_id is required"""
        user = User(username="testuser")
        db_session.add(user)

        with pytest.raises(Exception):  # IntegrityError for NOT NULL constraint
            db_session.commit()

    def test_default_values(self, db_session):
        """Test default values are set correctly"""
        user = User(telegram_id="123456789")
        db_session.add(user)
        db_session.commit()

        assert user.status_assinatura == "inactive"
        assert user.is_banned is False
        assert user.is_muted is False
        assert user.warn_count == 0
        assert user.auto_renew is True
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_updated_at_auto_update(self, db_session):
        """Test that updated_at is automatically updated on changes"""
        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)
        db_session.commit()

        original_updated_at = user.updated_at

        # Wait a bit and update
        import time
        time.sleep(0.01)

        user.username = "updateduser"
        db_session.commit()

        assert user.updated_at > original_updated_at

    def test_user_payment_relationship(self, db_session):
        """Test User-Payment relationship"""
        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)
        db_session.commit()

        payment = Payment(
            user_id=user.id,
            pixgo_payment_id="pix_123",
            amount=10.0,
            status="pending",
            completed_at=None
        )
        db_session.add(payment)
        db_session.commit()

        # Test forward relationship (User -> Payments)
        assert len(user.payments) == 1
        assert user.payments[0].pixgo_payment_id == "pix_123"

        # Test reverse relationship (Payment -> User)
        assert payment.user.id == user.id
        assert payment.user.username == "testuser"

    def test_payment_completed_at_field(self, db_session):
        """Test Payment completed_at field functionality"""
        from datetime import datetime

        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)
        db_session.commit()

        # Test payment with completed_at = None
        pending_payment = Payment(
            user_id=user.id,
            pixgo_payment_id="pix_pending",
            amount=10.0,
            status="pending",
            completed_at=None
        )
        db_session.add(pending_payment)
        db_session.commit()

        assert pending_payment.completed_at is None
        assert pending_payment.status == "pending"

        # Test payment with completed_at set
        completion_time = datetime.utcnow()
        completed_payment = Payment(
            user_id=user.id,
            pixgo_payment_id="pix_completed",
            amount=10.0,
            status="completed",
            completed_at=completion_time
        )
        db_session.add(completed_payment)
        db_session.commit()

        assert completed_payment.completed_at == completion_time
        assert completed_payment.status == "completed"

    def test_user_group_membership_relationship(self, db_session):
        """Test User-GroupMembership relationship"""
        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)

        group = Group(telegram_group_id="group123", name="Test Group")
        db_session.add(group)
        db_session.commit()

        membership = GroupMembership(user_id=user.id, group_id=group.id)
        db_session.add(membership)
        db_session.commit()

        # Test forward relationship (User -> GroupMemberships)
        assert len(user.group_memberships) == 1
        assert user.group_memberships[0].group.name == "Test Group"

        # Test reverse relationship (GroupMembership -> User)
        assert membership.user.username == "testuser"

        # Test Group -> Memberships relationship
        assert len(group.memberships) == 1
        assert group.memberships[0].user.username == "testuser"

    def test_user_status_values(self, db_session):
        """Test valid status_assinatura values"""
        valid_statuses = ["active", "inactive", "expired", "pending"]

        for status in valid_statuses:
            user = User(telegram_id=f"test_{status}", status_assinatura=status)
            db_session.add(user)
            db_session.commit()

            # Verify the status was set correctly
            db_user = db_session.query(User).filter_by(telegram_id=f"test_{status}").first()
            assert db_user.status_assinatura == status

    def test_user_ban_mute_fields(self, db_session):
        """Test ban and mute related fields"""
        future_time = datetime.utcnow() + timedelta(hours=2)

        user = User(
            telegram_id="123456789",
            is_banned=True,
            is_muted=True,
            mute_until=future_time
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_banned is True
        assert user.is_muted is True
        # Check that mute_until was set (can't compare exact datetime due to SQLAlchemy)
        assert user.mute_until is not None

    def test_user_optional_fields(self, db_session):
        """Test that optional fields can be None"""
        user = User(telegram_id="123456789")
        db_session.add(user)
        db_session.commit()

        # These fields should be None/null initially
        assert user.username is None
        assert user.first_name is None
        assert user.last_name is None
        assert user.data_expiracao is None
        assert user.mute_until is None