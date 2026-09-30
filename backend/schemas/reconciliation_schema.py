from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class MismatchItem(BaseModel):
    mismatch_type: str # PAID_WITHOUT_SUCCESS_PAYMENT, SUCCESS_PAYMENT_INVOICE_PENDING, MULTIPLE_SUCCESS_PAYMENTS, UNRETRIED_FAILED_PAYMENT, AMOUNT_DISCREPANCY
    severity: str # HIGH, MEDIUM, LOW
    invoice_id: str
    patient_id: str
    patient_name: str
    invoice_amount: float
    invoice_status: str
    description: str
    suggested_action: str
    details: Dict[str, Any]

class ReconciliationReport(BaseModel):
    timestamp: str
    total_invoices_scanned: int
    total_payments_scanned: int
    clean_invoices: int
    total_mismatches_found: int
    mismatches_by_type: Dict[str, int]
    mismatches: List[MismatchItem]
