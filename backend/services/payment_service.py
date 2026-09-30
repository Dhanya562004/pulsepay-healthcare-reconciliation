import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.schemas.payment_schema import PaymentCreate
from backend.services.audit_service import AuditService
from backend.utils.logger import logger

class PaymentService:
    @staticmethod
    def create_payment(db: Session, data: PaymentCreate) -> Dict[str, Any]:
        """
        Initiates payment for an invoice with simulated payment gateway processing.
        """
        invoice = db.query(Invoice).filter(Invoice.id == data.invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice with ID '{data.invoice_id}' not found.")

        # Determine payment amount (defaults to invoice amount if omitted)
        payment_amount = data.amount if data.amount is not None else invoice.amount

        # Generate provider transaction reference
        prefix = "pay_rzp_" if data.provider.lower() == "razorpay" else "tx_str_"
        ext_ref = f"{prefix}{uuid.uuid4().hex[:12]}"

        payment = Payment(
            id=str(uuid.uuid4()),
            invoice_id=invoice.id,
            amount=payment_amount,
            status="INITIATED",
            provider=data.provider.lower(),
            external_reference_id=ext_ref,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        AuditService.log_event(
            db=db,
            event_type="PAYMENT_INITIATED",
            entity_type="PAYMENT",
            entity_id=payment.id,
            message=f"Initiated {payment.provider} payment for Invoice {invoice.id} amount ${payment.amount:.2f}",
            details={"invoice_id": invoice.id, "ext_ref": ext_ref, "provider": payment.provider}
        )

        # Handle simulation forced failure scenario
        if data.simulate_failure:
            payment.status = "FAILED"
            payment.failure_reason = "Simulated Gateway Network Timeout / Insufficient Funds"
            payment.updated_at = datetime.utcnow()
            db.commit()

            AuditService.log_event(
                db=db,
                event_type="PAYMENT_FAILED",
                entity_type="PAYMENT",
                entity_id=payment.id,
                message=f"Payment {payment.id} failed gateway validation: {payment.failure_reason}",
                details={"reason": payment.failure_reason}
            )

        return payment.to_dict()

    @staticmethod
    def get_payment_by_id(db: Session, payment_id: str) -> Optional[Payment]:
        """Fetch payment record by UUID."""
        return db.query(Payment).filter(Payment.id == payment_id).first()

    @staticmethod
    def retry_payment(db: Session, payment_id: str, force_success: bool = True) -> Dict[str, Any]:
        """
        Retries a failed payment attempt.
        """
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError(f"Payment with ID '{payment_id}' not found.")

        if payment.status == "SUCCESS":
            return {"status": "already_successful", "payment": payment.to_dict()}

        invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()

        # Update payment status
        previous_status = payment.status
        payment.status = "SUCCESS" if force_success else "FAILED"
        payment.failure_reason = None if force_success else "Retry failed: Gateway timeout"
        payment.updated_at = datetime.utcnow()

        if force_success and invoice:
            invoice.status = "PAID"
            invoice.updated_at = datetime.utcnow()

        db.commit()

        AuditService.log_event(
            db=db,
            event_type="PAYMENT_RETRY",
            entity_type="PAYMENT",
            entity_id=payment.id,
            message=f"Retried payment {payment.id}. Result: {payment.status} (Previous: {previous_status})",
            details={"invoice_id": payment.invoice_id, "new_status": payment.status}
        )

        return {
            "status": "retry_completed",
            "payment_status": payment.status,
            "invoice_status": invoice.status if invoice else "N/A",
            "payment": payment.to_dict()
        }

    @staticmethod
    def retry_all_failed_payments(db: Session) -> Dict[str, Any]:
        """
        Bulk retries all failed payments in the system.
        """
        failed_payments = db.query(Payment).filter(Payment.status == "FAILED").all()
        retried_count = 0
        succeeded_count = 0

        for pay in failed_payments:
            res = PaymentService.retry_payment(db, pay.id, force_success=True)
            retried_count += 1
            if res.get("payment_status") == "SUCCESS":
                succeeded_count += 1

        AuditService.log_event(
            db=db,
            event_type="BULK_PAYMENT_RETRY",
            entity_type="SYSTEM",
            entity_id=None,
            message=f"Bulk retried {retried_count} failed payments. Succeeded: {succeeded_count}",
            details={"total_retried": retried_count, "succeeded": succeeded_count}
        )

        return {
            "total_retried": retried_count,
            "succeeded": succeeded_count
        }
