import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String)
    value_type = Column(String, default="string")  # string, int, float, bool
    description = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    @classmethod
    def get_value(cls, session, key: str, default=None):
        """Get configuration value by key"""
        config = session.query(cls).filter_by(key=key, is_active=True).first()
        if not config:
            return default

        if config.value_type == "int":
            return int(config.value)
        elif config.value_type == "float":
            return float(config.value)
        elif config.value_type == "bool":
            return config.value.lower() in ("true", "1", "yes")
        else:
            return config.value

    @classmethod
    def set_value(cls, session, key: str, value, value_type: str = "string", description: str = ""):
        """Set configuration value"""
        config = session.query(cls).filter_by(key=key).first()
        if not config:
            config = cls(key=key, description=description)

        config.value = str(value)
        config.value_type = value_type
        config.is_active = True
        session.add(config)
        session.commit()
        return config