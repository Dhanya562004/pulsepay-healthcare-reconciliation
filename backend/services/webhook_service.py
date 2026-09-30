import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from backend.models.webhook import WebhookEvent
from backend.models.payment import Payment
from backend.models.invoice import Invoice
from backend.services.audit_service import AuditService
from backend.schemas.webhook_schema import WebhookPayload, WebhookResponse
from backend.utils.logger import logger

class WebhookService:
    @staticmethod
    def process_payment_webhook(db: Session, payload: WebhookPayload) -> WebhookResponse:
        """
        Production-grade webhook processor with strict idempotency, safe unknown payment handling,
        out-of-order event protection, and double-update prevention.
        """
        start_time = time.time()
        logger.info(f"[WEBHOOK INGEST] Event ID: {payload.event_id} | Payment ID: {payload.payment_id} | Status: {payload.status}")

        # -------------------------------------------------------------------
        # 1. IDEMPOTENCY CHECK
        # -------------------------------------------------------------------
        existing_event = db.query(WebhookEvent).filter(WebhookEvent.event_id == payload.event_id).first()
        if existing_event:
            logger.warning(f"[IDEMPOTENCY BLOCK] Duplicate event_id received: '{payload.event_id}'")
            
            AuditService.log_event(
                db=db,
                event_type="WEBHOOK_DUPLICATE_IGNORED",
                entity_type="WEBHOOK",
                entity_id=payload.event_id,
                message=f"Idempotency block: Duplicate webhook event_id '{payload.event_id}' ignored.",
                details={"payment_id": payload.payment_id, "status": payload.status}
            )

            execution_time = (time.time() - start_time) * 1000
            return WebhookResponse(
                status="ignored",
                message=f"Duplicate event_id '{payload.event_id}' ignored for idempotency.",
                event_id=payload.event_id,
                payment_id=payload.payment_id,
                execution_time_ms=round(execution_time, 2)
            )

        # Create record of incoming webhook event
        webhook_event = WebhookEvent(
            id=str(uuid.uuid4()),
            event_id=payload.event_id,
            payment_id=payload.payment_id,
            status=payload.status.upper(),
            processing_status="PROCESSED",
            payload=json.dumps(payload.model_dump(), default=str),
            processed_at=datetime.utcnow()
        )
        db.add(webhook_event)

        # -------------------------------------------------------------------
        # 2. UNKNOWN PAYMENT HANDLING
        # -------------------------------------------------------------------
        payment = db.query(Payment).filter(Payment.id == payload.payment_id).first()
        if not payment:
            logger.error(f"[UNKNOWN PAYMENT] Webhook received for non-existent payment_id: '{payload.payment_id}'")
            webhook_event.processing_status = "PAYMENT_NOT_FOUND"
            db.commit()

            AuditService.log_event(
                db=db,
                event_type="WEBHOOK_UNKNOWN_PAYMENT",
                entity_type="WEBHOOK",
                entity_id=payload.event_id,
                message=f"Safely handled unknown payment_id '{payload.payment_id}' in webhook event.",
                details=payload.model_dump()
            )

            execution_time = (time.time() - start_time) * 1000
            return WebhookResponse(
                status="payment_not_found",
                message=f"Payment ID '{payload.payment_id}' does not exist in backend database.",
                event_id=payload.event_id,
                payment_id=payload.payment_id,
                execution_time_ms=round(execution_time, 2)
            )

        invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()

        # -------------------------------------------------------------------
        # 3. OUT-OF-ORDER & DELAYED EVENT HANDLING
        # -------------------------------------------------------------------
        # Rule: If payment is ALREADY SUCCESS, do not allow an incoming FAILED webhook event to overwrite status to FAILED.
        if payment.status == "SUCCESS" and payload.status.upper() == "FAILED":
            logger.warning(
                f"[DELAYED/OUT-OF-ORDER EVENT] Payment '{payment.id}' is already SUCCESS. "
                f"Ignoring delayed FAILED event '{payload.event_id}'."
            )
            webhook_event.processing_status = "DELAYED_IGNORED"
            db.commit()

            AuditService.log_event(
                db=db,
                event_type="WEBHOOK_DELAYED_IGNORED",
                entity_type="WEBHOOK",
                entity_id=payload.event_id,
                message=f"Out-of-order FAILED event ignored because payment {payment.id} is already SUCCESS.",
                details={"payment_id": payment.id, "invoice_id": payment.invoice_id}
            )

            execution_time = (time.time() - start_time) * 1000
            return WebhookResponse(
                status="delayed_ignored",
                message="Out-of-order FAILED event ignored to preserve successful payment state.",
                event_id=payload.event_id,
                payment_id=payment.id,
                invoice_id=payment.invoice_id,
                invoice_status=invoice.status if invoice else None,
                execution_time_ms=round(execution_time, 2)
            )

        # -------------------------------------------------------------------
        # 4. PREVENT DOUBLE UPDATES & APPLY STATE TRANSITIONS
        # -------------------------------------------------------------------
        event_status = payload.status.upper()
        previous_payment_status = payment.status
        previous_invoice_status = invoice.status if invoice else None

        # Update payment status
        payment.status = event_status
        if event_status == "FAILED" and payload.failure_reason:
            payment.failure_reason = payload.failure_reason
        payment.updated_at = datetime.utcnow()

        # Update invoice status
        if invoice:
            if event_status == "SUCCESS":
                invoice.status = "PAID"
                invoice.updated_at = datetime.utcnow()
            elif event_status == "FAILED":
                # Only mark invoice FAILED if no other successful payments exist for this invoice
                other_success_payment = db.query(Payment).filter(
                    Payment.invoice_id == invoice.id,
                    Payment.status == "SUCCESS",
                    Payment.id != payment.id
                ).first()
                if not other_success_payment:
                    invoice.status = "FAILED"
                    invoice.updated_at = datetime.utcnow()

        db.commit()

        AuditService.log_event(
            db=db,
            event_type="WEBHOOK_PROCESSED",
            entity_type="WEBHOOK",
            entity_id=payload.event_id,
            message=(
                f"Successfully processed webhook '{payload.event_id}'. "
                f"Payment {payment.id}: {previous_payment_status} -> {payment.status}. "
                f"Invoice {invoice.id if invoice else 'N/A'}: {previous_invoice_status} -> {invoice.status if invoice else 'N/A'}."
            ),
            details={
                "event_id": payload.event_id,
                "payment_id": payment.id,
                "new_payment_status": payment.status,
                "new_invoice_status": invoice.status if invoice else None
            }
        )

        execution_time = (time.time() - start_time) * 1000
        return WebhookResponse(
            status="processed",
            message=f"Webhook processed successfully. Invoice status updated to '{invoice.status if invoice else 'N/A'}'.",
            event_id=payload.event_id,
            payment_id=payment.id,
            invoice_id=invoice.id if invoice else None,
            invoice_status=invoice.status if invoice else None,
            execution_time_ms=round(execution_time, 2)
        )

    @staticmethod
    def get_webhook_history(db: Session, limit: int = 50) -> List[WebhookEvent]:
        """Fetch list of recent webhook events for UI/Audit display."""
        return db.query(WebhookEvent).order_by(WebhookEvent.processed_at.desc()).limit(limit).all()
