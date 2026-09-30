from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.database.session import get_db
from backend.schemas.webhook_schema import WebhookPayload, WebhookResponse
from backend.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhook", tags=["Webhook Processing"])

@router.post("/payment", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
def handle_payment_webhook(payload: WebhookPayload, db: Session = Depends(get_db)):
    """
    CRITICAL: Production Webhook Endpoint for Payment Gateways.
    Enforces idempotency (rejects duplicate event_id), handles out-of-order events,
    safely handles unknown payments, and updates payment & invoice state.
    """
    return WebhookService.process_payment_webhook(db, payload)

@router.get("/history")
def get_webhook_history(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve history of received webhook events and idempotency decisions."""
    events = WebhookService.get_webhook_history(db, limit=limit)
    return [e.to_dict() for e in events]
