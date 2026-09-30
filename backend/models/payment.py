import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="INITIATED", index=True) # INITIATED, SUCCESS, FAILED
    provider = Column(String(50), nullable=False, default="razorpay") # razorpay, stripe, mock_gateway
    external_reference_id = Column(String(100), unique=True, nullable=False, index=True)
    failure_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    webhook_events = relationship("WebhookEvent", back_populates="payment", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "status": self.status,
            "provider": self.provider,
            "external_reference_id": self.external_reference_id,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
