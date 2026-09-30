import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.base import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(100), unique=True, nullable=False, index=True) # Unique webhook identifier for Idempotency
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), nullable=False) # SUCCESS, FAILED
    processing_status = Column(String(50), nullable=False, default="PROCESSED") # PROCESSED, DUPLICATE_IGNORED, DELAYED_IGNORED, PAYMENT_NOT_FOUND, FAILED
    payload = Column(Text, nullable=True) # JSON payload string
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    payment = relationship("Payment", back_populates="webhook_events")

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "payment_id": self.payment_id,
            "status": self.status,
            "processing_status": self.processing_status,
            "payload": self.payload,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
