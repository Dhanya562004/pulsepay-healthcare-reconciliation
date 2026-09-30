from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.schemas.payment_schema import PaymentCreate, PaymentResponse, PaymentRetryRequest
from backend.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payment Processing"])

@router.post("/create", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    """
    Initiates payment for an invoice via simulated payment gateway (Razorpay / Stripe).
    """
    try:
        return PaymentService.create_payment(db, payload)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.post("/retry/{payment_id}")
def retry_failed_payment(payment_id: str, force_success: bool = True, db: Session = Depends(get_db)):
    """
    Manual API endpoint to retry a failed payment transaction.
    """
    try:
        return PaymentService.retry_payment(db, payment_id, force_success=force_success)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.post("/retry-all")
def retry_all_failed_payments(db: Session = Depends(get_db)):
    """
    Bulk retry endpoint / background job trigger for failed payments.
    """
    return PaymentService.retry_all_failed_payments(db)
