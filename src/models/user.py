import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    status_assinatura = Column(String, default="inactive")  # active, inactive, expired
    data_expiracao = Column(DateTime)
    is_banned = Column(Boolean, default=False)
    is_muted = Column(Boolean, default=False)
    mute_until = Column(DateTime)
    warn_count = Column(Integer, default=0)
    auto_renew = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Relationships
    payments = relationship("Payment", back_populates="user")
    group_memberships = relationship("GroupMembership", back_populates="user")
    warnings = relationship("Warning", back_populates="user")
