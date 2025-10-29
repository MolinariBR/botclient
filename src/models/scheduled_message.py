import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text, Time
from sqlalchemy.orm import relationship

from .base import Base


class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=False)
    schedule_time = Column(Time, nullable=False)  # HH:MM format
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("admins.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    admin = relationship("Admin", back_populates="scheduled_messages")
