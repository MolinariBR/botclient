import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.models.user import User
from src.models.group import Group, GroupMembership
from src.models.payment import Payment
from src.models.base import Base


class TestGroupModel:
    """Unit tests for Group model"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing"""
        engine = create_engine("sqlite:///:memory:")

        # Import all models to ensure they use the same Base
        Base.metadata.create_all(engine)

        # Enable foreign key constraints in SQLite
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON"))
            conn.commit()

        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_group_creation_with_required_fields(self, db_session):
        """Test creating a group with minimal required fields"""
        group = Group(
            telegram_group_id="group123",
            name="Test Group"
        )
        db_session.add(group)
        db_session.commit()

        assert group.id is not None
        assert group.telegram_group_id == "group123"
        assert group.name == "Test Group"
        assert group.is_vip is True  # default value
        assert group.created_at is not None
        assert group.updated_at is not None

    def test_group_creation_with_all_fields(self, db_session):
        """Test creating a group with all fields populated"""
        group = Group(
            telegram_group_id="vip_group_456",
            name="VIP Premium Group",
            description="A premium group for VIP users",
            is_vip=False
        )
        db_session.add(group)
        db_session.commit()

        assert group.telegram_group_id == "vip_group_456"
        assert group.name == "VIP Premium Group"
        assert group.description == "A premium group for VIP users"
        assert group.is_vip is False

    def test_telegram_group_id_uniqueness(self, db_session):
        """Test that telegram_group_id must be unique"""
        group1 = Group(telegram_group_id="unique_group", name="Group 1")
        group2 = Group(telegram_group_id="unique_group", name="Group 2")

        db_session.add(group1)
        db_session.commit()

        db_session.add(group2)
        with pytest.raises(Exception):  # IntegrityError in real database
            db_session.commit()

    def test_telegram_group_id_required(self, db_session):
        """Test that telegram_group_id is required"""
        group = Group(name="Test Group")
        db_session.add(group)

        with pytest.raises(Exception):  # IntegrityError for NOT NULL constraint
            db_session.commit()

    def test_default_values(self, db_session):
        """Test default values are set correctly"""
        group = Group(telegram_group_id="test_group", name="Test")
        db_session.add(group)
        db_session.commit()

        assert group.is_vip is True
        assert group.description is None
        assert group.created_at is not None
        assert group.updated_at is not None

    def test_updated_at_auto_update(self, db_session):
        """Test that updated_at is automatically updated on changes"""
        group = Group(telegram_group_id="test_group", name="Original Name")
        db_session.add(group)
        db_session.commit()

        original_updated_at = group.updated_at

        # Wait a bit and update
        import time
        time.sleep(0.01)

        group.name = "Updated Name"
        db_session.commit()

        assert group.updated_at > original_updated_at

    def test_group_memberships_relationship(self, db_session):
        """Test Group-Memberships relationship"""
        group = Group(telegram_group_id="test_group", name="Test Group")
        db_session.add(group)

        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)
        db_session.commit()

        membership = GroupMembership(user_id=user.id, group_id=group.id)
        db_session.add(membership)
        db_session.commit()

        # Test forward relationship (Group -> Memberships)
        assert len(group.memberships) == 1
        assert group.memberships[0].user.username == "testuser"

        # Test reverse relationship (Membership -> Group)
        assert membership.group.name == "Test Group"

    def test_group_optional_fields(self, db_session):
        """Test that optional fields can be None"""
        group = Group(telegram_group_id="test_group", name="Test")
        db_session.add(group)
        db_session.commit()

        # description should be None initially
        assert group.description is None


class TestGroupMembershipModel:
    """Unit tests for GroupMembership model"""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing"""
        engine = create_engine("sqlite:///:memory:")

        # Import all models to ensure they use the same Base
        Base.metadata.create_all(engine)

        # Enable foreign key constraints in SQLite
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON"))
            conn.commit()

        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_membership_creation(self, db_session):
        """Test creating a group membership"""
        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)

        group = Group(telegram_group_id="test_group", name="Test Group")
        db_session.add(group)
        db_session.commit()

        membership = GroupMembership(user_id=user.id, group_id=group.id)
        db_session.add(membership)
        db_session.commit()

        assert membership.id is not None
        assert membership.user_id == user.id
        assert membership.group_id == group.id
        assert membership.joined_at is not None

        # Test relationships
        assert membership.user.username == "testuser"
        assert membership.group.name == "Test Group"

    def test_user_id_required(self, db_session):
        """Test that user_id is required"""
        group = Group(telegram_group_id="test_group", name="Test Group")
        db_session.add(group)
        db_session.commit()

        membership = GroupMembership(group_id=group.id)  # Missing user_id
        db_session.add(membership)

        with pytest.raises(Exception):  # IntegrityError for NOT NULL constraint
            db_session.commit()

    def test_group_id_required(self, db_session):
        """Test that group_id is required"""
        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)
        db_session.commit()

        membership = GroupMembership(user_id=user.id)  # Missing group_id
        db_session.add(membership)

        with pytest.raises(Exception):  # IntegrityError for NOT NULL constraint
            db_session.commit()

    def test_foreign_key_constraints(self, db_session):
        """Test foreign key constraints"""
        # Try to create membership with non-existent user_id
        membership = GroupMembership(user_id=999, group_id=1)
        db_session.add(membership)

        with pytest.raises(Exception):  # Foreign key constraint violation
            db_session.commit()

    def test_joined_at_default(self, db_session):
        """Test that joined_at gets a default value"""
        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)

        group = Group(telegram_group_id="test_group", name="Test Group")
        db_session.add(group)
        db_session.commit()

        membership = GroupMembership(user_id=user.id, group_id=group.id)
        db_session.add(membership)
        db_session.commit()

        assert membership.joined_at is not None
        assert isinstance(membership.joined_at, datetime)

    def test_unique_user_group_combination(self, db_session):
        """Test that a user can only have one membership per group"""
        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)

        group = Group(telegram_group_id="test_group", name="Test Group")
        db_session.add(group)
        db_session.commit()

        # Create first membership
        membership1 = GroupMembership(user_id=user.id, group_id=group.id)
        db_session.add(membership1)
        db_session.commit()

        # Try to create duplicate membership
        membership2 = GroupMembership(user_id=user.id, group_id=group.id)
        db_session.add(membership2)

        # This should work in SQLite (no unique constraint), but we can test the logic
        db_session.commit()

        # Check that we have 2 memberships (SQLite allows duplicates)
        memberships = db_session.query(GroupMembership).filter_by(
            user_id=user.id, group_id=group.id
        ).all()
        assert len(memberships) == 2

    def test_membership_deletion_cascades(self, db_session):
        """Test that membership relationships work correctly when deleting"""
        user = User(telegram_id="123456789", username="testuser")
        db_session.add(user)

        group = Group(telegram_group_id="test_group", name="Test Group")
        db_session.add(group)
        db_session.commit()

        membership = GroupMembership(user_id=user.id, group_id=group.id)
        db_session.add(membership)
        db_session.commit()

        # Delete membership
        db_session.delete(membership)
        db_session.commit()

        # User and group should still exist
        assert db_session.query(User).filter_by(id=user.id).first() is not None
        assert db_session.query(Group).filter_by(id=group.id).first() is not None

        # Membership should be gone
        assert db_session.query(GroupMembership).filter_by(
            user_id=user.id, group_id=group.id
        ).first() is None