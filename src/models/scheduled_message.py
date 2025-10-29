import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from .base import Base


class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    id = Column(Integer, primary_key=True)
    message_type = Column(String, default="daily")  # daily, weekly, custom
    content = Column(Text, nullable=False)
    scheduled_time = Column(Time, nullable=False)  # Time of day to send
    day_of_week = Column(Integer)  # 0-6 for weekly messages (Monday=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("admins.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_sent = Column(DateTime)

    # Relationships
    creator = relationship("Admin")

    def should_send_today(self) -> bool:
        """Check if message should be sent today"""
        if not self.is_active:
            return False

        now = datetime.datetime.now()

        if self.message_type == "daily":
            return True
        elif self.message_type == "weekly":
            return now.weekday() == self.day_of_week
        else:
            return False

    def can_send_now(self) -> bool:
        """Check if message can be sent at current time"""
        if not self.should_send_today():
            return False

        now = datetime.datetime.now().time()
        # Allow sending within 5 minutes of scheduled time
        scheduled = datetime.datetime.combine(datetime.date.today(), self.scheduled_time)
        window_start = scheduled - datetime.timedelta(minutes=5)
        window_end = scheduled + datetime.timedelta(minutes=5)

        return window_start.time() <= now <= window_end.time()