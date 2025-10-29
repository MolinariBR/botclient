import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("admins.id"), nullable=False)

    # Relationships
    admin = relationship("Admin", back_populates="system_configs")
