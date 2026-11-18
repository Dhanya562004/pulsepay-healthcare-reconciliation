from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from backend.database.session import get_db
from backend.schemas.payment_schema import (
    PaymentCreate,
    PaymentResponse,
    PaymentRetryRequest,
    PaginatedPaymentResponse,
    PaymentDetailResponse,
)
from backend.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payment Processing"])

@router.get("", response_model=PaginatedPaymentResponse)
def list_payments(
    limit: int = Query(20, ge=1, le=100, description="Page size (1-100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(None, description="Filter by payment status (e.g. INITIATED, SUCCESS, FAILED)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve paginated list of payments with optional status filtering.
    """
    return PaymentService.get_payments(db, limit=limit, offset=offset, status=status)

@router.get("/{payment_id}", response_model=PaymentDetailResponse)
def get_payment_detail(payment_id: str, db: Session = Depends(get_db)):
    """
    Retrieve detailed payment information including related webhook event statuses.
    """
    detail = PaymentService.get_payment_detail(db, payment_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found.")
    return detail

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
