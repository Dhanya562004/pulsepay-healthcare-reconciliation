from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database.session import get_db
from backend.schemas.invoice_schema import InvoiceCreate, InvoiceResponse, InvoiceDetailResponse
from backend.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])

@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new healthcare billing invoice."""
    return InvoiceService.create_invoice(db, payload)

@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, PAID, FAILED)"),
    patient_id: Optional[str] = Query(None, description="Filter by Patient ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieve list of invoices with optional filtering and pagination."""
    return InvoiceService.get_invoices(db, status=status, patient_id=patient_id, limit=limit, offset=offset)

@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice_detail(invoice_id: str, db: Session = Depends(get_db)):
    """Retrieve full details for an invoice, including all payment records."""
    detail = InvoiceService.get_invoice_detail(db, invoice_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found.")
    return detail
