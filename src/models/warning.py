import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from .base import Base


class Warning(Base):
    __tablename__ = "warnings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="warnings")
    admin = relationship("Admin", back_populates="warnings")
