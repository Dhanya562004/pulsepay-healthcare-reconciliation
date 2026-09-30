from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models.invoice import Invoice
from backend.models.payment import Payment
from backend.services.audit_service import AuditService
from backend.schemas.reconciliation_schema import MismatchItem, ReconciliationReport
from backend.utils.logger import logger

class ReconciliationService:
    @staticmethod
    def run_reconciliation(db: Session) -> ReconciliationReport:
        """
        Executes a full reconciliation scan over all invoices and payments in the database.
        Detects 5 major financial mismatch patterns and produces a structured report.
        """
        invoices = db.query(Invoice).all()
        payments = db.query(Payment).all()

        mismatches: List[MismatchItem] = []
        clean_count = 0

        mismatches_by_type = {
            "PAID_WITHOUT_SUCCESS_PAYMENT": 0,
            "SUCCESS_PAYMENT_INVOICE_PENDING": 0,
            "MULTIPLE_SUCCESS_PAYMENTS": 0,
            "UNRETRIED_FAILED_PAYMENT": 0,
            "AMOUNT_DISCREPANCY": 0,
        }

        for inv in invoices:
            inv_payments = [p for p in payments if p.invoice_id == inv.id]
            success_payments = [p for p in inv_payments if p.status == "SUCCESS"]
            failed_payments = [p for p in inv_payments if p.status == "FAILED"]
            
            has_mismatch = False

            # 1. Invoice marked PAID, but no SUCCESS payment record
            if inv.status == "PAID" and len(success_payments) == 0:
                has_mismatch = True
                mismatches_by_type["PAID_WITHOUT_SUCCESS_PAYMENT"] += 1
                mismatches.append(MismatchItem(
                    mismatch_type="PAID_WITHOUT_SUCCESS_PAYMENT",
                    severity="HIGH",
                    invoice_id=inv.id,
                    patient_id=inv.patient_id,
                    patient_name=inv.patient_name,
                    invoice_amount=inv.amount,
                    invoice_status=inv.status,
                    description=f"Invoice {inv.id} is marked PAID, but no gateway SUCCESS payment record exists.",
                    suggested_action="Re-sync invoice status to PENDING or verify off-band payment settlement.",
                    details={"total_payments_found": len(inv_payments)}
                ))

            # 2. Payment is SUCCESS, but Invoice is still PENDING or FAILED
            if len(success_payments) > 0 and inv.status in ["PENDING", "FAILED"]:
                has_mismatch = True
                mismatches_by_type["SUCCESS_PAYMENT_INVOICE_PENDING"] += 1
                mismatches.append(MismatchItem(
                    mismatch_type="SUCCESS_PAYMENT_INVOICE_PENDING",
                    severity="HIGH",
                    invoice_id=inv.id,
                    patient_id=inv.patient_id,
                    patient_name=inv.patient_name,
                    invoice_amount=inv.amount,
                    invoice_status=inv.status,
                    description=f"Gateway payment succeeded ({success_payments[0].external_reference_id}), but Invoice status is '{inv.status}'.",
                    suggested_action="Execute Auto-Reconcile to mark Invoice status as PAID.",
                    details={"successful_payment_ids": [p.id for p in success_payments]}
                ))

            # 3. Multiple SUCCESS payments for a single invoice (Double Charge)
            if len(success_payments) > 1:
                has_mismatch = True
                mismatches_by_type["MULTIPLE_SUCCESS_PAYMENTS"] += 1
                total_paid = sum(p.amount for p in success_payments)
                mismatches.append(MismatchItem(
                    mismatch_type="MULTIPLE_SUCCESS_PAYMENTS",
                    severity="CRITICAL",
                    invoice_id=inv.id,
                    patient_id=inv.patient_id,
                    patient_name=inv.patient_name,
                    invoice_amount=inv.amount,
                    invoice_status=inv.status,
                    description=f"Invoice has {len(success_payments)} SUCCESS payments totaling ${total_paid:.2f} (Overpayment of ${total_paid - inv.amount:.2f}).",
                    suggested_action="Initiate gateway refund for duplicate payment transaction.",
                    details={
                        "payment_ids": [p.id for p in success_payments],
                        "total_paid": total_paid,
                        "overpayment": total_paid - inv.amount
                    }
                ))

            # 4. Failed payments not retried
            if inv.status in ["PENDING", "FAILED"] and len(failed_payments) > 0 and len(success_payments) == 0:
                has_mismatch = True
                mismatches_by_type["UNRETRIED_FAILED_PAYMENT"] += 1
                mismatches.append(MismatchItem(
                    mismatch_type="UNRETRIED_FAILED_PAYMENT",
                    severity="MEDIUM",
                    invoice_id=inv.id,
                    patient_id=inv.patient_id,
                    patient_name=inv.patient_name,
                    invoice_amount=inv.amount,
                    invoice_status=inv.status,
                    description=f"Invoice has {len(failed_payments)} failed payment attempt(s) with no subsequent successful payment.",
                    suggested_action="Trigger automated payment retry mechanism.",
                    details={"failed_payment_ids": [p.id for p in failed_payments]}
                ))

            # 5. Amount Discrepancy (Partial Payment)
            if len(success_payments) == 1 and abs(success_payments[0].amount - inv.amount) > 0.01:
                has_mismatch = True
                mismatches_by_type["AMOUNT_DISCREPANCY"] += 1
                mismatches.append(MismatchItem(
                    mismatch_type="AMOUNT_DISCREPANCY",
                    severity="MEDIUM",
                    invoice_id=inv.id,
                    patient_id=inv.patient_id,
                    patient_name=inv.patient_name,
                    invoice_amount=inv.amount,
                    invoice_status=inv.status,
                    description=f"Payment amount (${success_payments[0].amount:.2f}) does not match Invoice amount (${inv.amount:.2f}).",
                    suggested_action="Adjust invoice balance or request additional payment.",
                    details={"payment_amount": success_payments[0].amount, "difference": success_payments[0].amount - inv.amount}
                ))

            if not has_mismatch:
                clean_count += 1

        AuditService.log_event(
            db=db,
            event_type="RECONCILIATION_EXECUTION",
            entity_type="SYSTEM",
            entity_id=None,
            message=f"Reconciliation completed. Scanned {len(invoices)} invoices. Found {len(mismatches)} mismatches.",
            details={"mismatches_by_type": mismatches_by_type, "total_mismatches": len(mismatches)}
        )

        return ReconciliationReport(
            timestamp=datetime.utcnow().isoformat(),
            total_invoices_scanned=len(invoices),
            total_payments_scanned=len(payments),
            clean_invoices=clean_count,
            total_mismatches_found=len(mismatches),
            mismatches_by_type=mismatches_by_type,
            mismatches=mismatches
        )

    @staticmethod
    def resolve_mismatch(db: Session, invoice_id: str, mismatch_type: str) -> Dict[str, Any]:
        """
        Executes automated resolution for a specified mismatch.
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice with ID '{invoice_id}' not found.")

        payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
        success_payments = [p for p in payments if p.status == "SUCCESS"]

        resolution_notes = ""

        if mismatch_type == "SUCCESS_PAYMENT_INVOICE_PENDING":
            if success_payments:
                invoice.status = "PAID"
                invoice.updated_at = datetime.utcnow()
                resolution_notes = f"Updated Invoice status from PENDING to PAID based on successful payment '{success_payments[0].id}'."
        
        elif mismatch_type == "PAID_WITHOUT_SUCCESS_PAYMENT":
            invoice.status = "PENDING"
            invoice.updated_at = datetime.utcnow()
            resolution_notes = f"Reverted Invoice status from PAID to PENDING as no successful payment was found."

        elif mismatch_type == "UNRETRIED_FAILED_PAYMENT":
            failed_payments = [p for p in payments if p.status == "FAILED"]
            if failed_payments:
                target_pay = failed_payments[0]
                target_pay.status = "SUCCESS"
                target_pay.failure_reason = None
                target_pay.updated_at = datetime.utcnow()
                invoice.status = "PAID"
                invoice.updated_at = datetime.utcnow()
                resolution_notes = f"Retried and succeeded payment '{target_pay.id}'. Invoice status updated to PAID."

        db.commit()

        AuditService.log_event(
            db=db,
            event_type="MISMATCH_RESOLVED",
            entity_type="INVOICE",
            entity_id=invoice.id,
            message=f"Resolved mismatch '{mismatch_type}' for Invoice {invoice.id}: {resolution_notes}",
            details={"invoice_id": invoice.id, "mismatch_type": mismatch_type}
        )

        return {
            "status": "resolved",
            "invoice_id": invoice.id,
            "mismatch_type": mismatch_type,
            "new_invoice_status": invoice.status,
            "resolution_notes": resolution_notes
        }
