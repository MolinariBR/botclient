import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    permissions = Column(String, default="basic")  # basic, advanced, super
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Relationships
    warnings = relationship("Warning", back_populates="admin")
    system_configs = relationship("SystemConfig", back_populates="admin")
    scheduled_messages = relationship("ScheduledMessage", back_populates="admin")
