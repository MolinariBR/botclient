import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pixgo_payment_id = Column(String, unique=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="BRL")
    status = Column(String, default="pending")  # pending, completed, failed, expired
    payment_method = Column(String, default="pix")  # pix, usdt
    qr_code = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="payments")
