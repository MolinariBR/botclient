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
    status = Column(String, default="pending")  # pending, completed, failed, expired, waiting_proof
    payment_method = Column(String, default="pix")  # pix, usdt
    qr_code = Column(String)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # USDT proof fields
    proof_image_url = Column(String)  # URL da imagem do comprovante
    transaction_hash = Column(String)  # Hash da transação blockchain
    proof_submitted_at = Column(DateTime)  # Quando o comprovante foi enviado

    # Relationships
    user = relationship("User", back_populates="payments")
