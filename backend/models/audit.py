import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from backend.database.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True) # INVOICE_CREATED, PAYMENT_INITIATED, WEBHOOK_PROCESSED, WEBHOOK_DUPLICATE, RECONCILIATION_RUN, RETRY_ATTEMPT
    entity_type = Column(String(50), nullable=False) # INVOICE, PAYMENT, WEBHOOK, SYSTEM
    entity_id = Column(String(100), nullable=True, index=True)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True) # JSON or descriptive string
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
