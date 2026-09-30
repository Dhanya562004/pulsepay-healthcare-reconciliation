import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.audit import AuditLog
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.models.webhook import WebhookEvent
from backend.utils.logger import logger

class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        entity_type: str,
        message: str,
        entity_id: Optional[str] = None,
        details: Optional[Any] = None
    ) -> AuditLog:
        """Record a structured audit log entry in the database."""
        details_str = None
        if details is not None:
            if isinstance(details, (dict, list)):
                details_str = json.dumps(details, default=str)
            else:
                details_str = str(details)

        audit_entry = AuditLog(
            id=str(uuid.uuid4()),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            details=details_str,
            timestamp=datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)

        logger.info(f"[AUDIT] [{event_type}] [{entity_type}:{entity_id or 'N/A'}] - {message}")
        return audit_entry

    @staticmethod
    def get_recent_logs(db: Session, limit: int = 50) -> List[AuditLog]:
        """Fetch recent system audit logs ordered by timestamp descending."""
        return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_system_metrics(db: Session) -> Dict[str, Any]:
        """Compute key financial, operational, and observability metrics."""
        total_invoices = db.query(Invoice).count()
        total_invoiced_amount = db.query(func.coalesce(func.sum(Invoice.amount), 0.0)).scalar()

        # Status breakdowns for invoices
        inv_status_rows = db.query(Invoice.status, func.count(Invoice.id)).group_by(Invoice.status).all()
        invoice_status_counts = {status: count for status, count in inv_status_rows}

        # Collected amount (Paid invoices or success payments)
        total_collected_amount = db.query(func.coalesce(func.sum(Invoice.amount), 0.0)).filter(Invoice.status == "PAID").scalar()
        total_pending_amount = db.query(func.coalesce(func.sum(Invoice.amount), 0.0)).filter(Invoice.status == "PENDING").scalar()

        # Payments
        total_payments = db.query(Payment).count()
        pay_status_rows = db.query(Payment.status, func.count(Payment.id)).group_by(Payment.status).all()
        payment_status_counts = {status: count for status, count in pay_status_rows}

        # Webhook Telemetry
        total_webhooks = db.query(WebhookEvent).count()
        duplicate_webhooks = db.query(WebhookEvent).filter(WebhookEvent.processing_status == "DUPLICATE_IGNORED").count()
        delayed_webhooks = db.query(WebhookEvent).filter(WebhookEvent.processing_status == "DELAYED_IGNORED").count()

        return {
            "total_invoices": total_invoices,
            "total_invoiced_amount": float(total_invoiced_amount),
            "total_collected_amount": float(total_collected_amount),
            "total_pending_amount": float(total_pending_amount),
            "invoice_status_counts": invoice_status_counts,
            "total_payments": total_payments,
            "payment_status_counts": payment_status_counts,
            "total_webhooks": total_webhooks,
            "duplicate_webhooks_blocked": duplicate_webhooks,
            "delayed_webhooks_handled": delayed_webhooks,
        }
