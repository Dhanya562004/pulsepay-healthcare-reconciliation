import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import relationship
from backend.database.base import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(100), nullable=False, index=True)
    patient_name = Column(String(200), nullable=False, default="Anonymous Patient")
    service_description = Column(String(255), nullable=False, default="General Healthcare Service")
    amount = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="PENDING", index=True) # PENDING, PAID, FAILED, PARTIALLY_PAID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "service_description": self.service_description,
            "amount": self.amount,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
