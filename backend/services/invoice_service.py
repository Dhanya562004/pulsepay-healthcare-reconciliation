import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.schemas.invoice_schema import InvoiceCreate
from backend.services.audit_service import AuditService
from backend.utils.logger import logger

class InvoiceService:
    @staticmethod
    def create_invoice(db: Session, data: InvoiceCreate) -> Invoice:
        """Create a new healthcare invoice."""
        invoice = Invoice(
            id=str(uuid.uuid4()),
            patient_id=data.patient_id,
            patient_name=data.patient_name,
            service_description=data.service_description,
            amount=data.amount,
            status="PENDING",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        AuditService.log_event(
            db=db,
            event_type="INVOICE_CREATED",
            entity_type="INVOICE",
            entity_id=invoice.id,
            message=f"Created invoice for patient {invoice.patient_id} ({invoice.patient_name}) amount ${invoice.amount:.2f}",
            details=invoice.to_dict()
        )
        return invoice

    @staticmethod
    def get_invoices(
        db: Session,
        status: Optional[str] = None,
        patient_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Fetch list of invoices with optional filters."""
        query = db.query(Invoice)
        if status:
            query = query.filter(Invoice.status == status.upper())
        if patient_id:
            query = query.filter(Invoice.patient_id == patient_id)
        
        return query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_invoice_by_id(db: Session, invoice_id: str) -> Optional[Invoice]:
        """Fetch a single invoice by UUID."""
        return db.query(Invoice).filter(Invoice.id == invoice_id).first()

    @staticmethod
    def get_invoice_detail(db: Session, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Fetch invoice along with all associated payment records."""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return None

        payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
        result = invoice.to_dict()
        result["payments"] = [p.to_dict() for p in payments]
        return result
