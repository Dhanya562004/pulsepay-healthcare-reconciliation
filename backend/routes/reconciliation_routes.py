from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.schemas.reconciliation_schema import ReconciliationReport
from backend.services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/reconcile", tags=["Reconciliation Engine"])

@router.get("", response_model=ReconciliationReport)
def run_reconciliation(db: Session = Depends(get_db)):
    """
    Scans system database to detect billing vs payment mismatches.
    Detects 5 major mismatch categories:
    1. Invoice = PAID but no SUCCESS payment
    2. Payment = SUCCESS but Invoice still PENDING/FAILED
    3. Multiple SUCCESS payments for single invoice (Double charge / Overpayment)
    4. Failed payments not retried
    5. Amount discrepancies / Partial payments
    """
    return ReconciliationService.run_reconciliation(db)

@router.post("/resolve")
def resolve_mismatch(invoice_id: str, mismatch_type: str, db: Session = Depends(get_db)):
    """
    Executes automated fix for detected reconciliation mismatch.
    """
    try:
        return ReconciliationService.resolve_mismatch(db, invoice_id=invoice_id, mismatch_type=mismatch_type)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))
