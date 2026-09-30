from pydantic import BaseModel, Field
from typing import Optional

class WebhookPayload(BaseModel):
    event_id: str = Field(..., example="evt_998877665544", description="Unique gateway event ID for idempotency")
    payment_id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440001", description="Target payment UUID")
    status: str = Field(..., example="SUCCESS", description="Gateway status: SUCCESS or FAILED")
    failure_reason: Optional[str] = Field(None, example="Insufficient funds / Invalid Card", description="Reason if status is FAILED")
    timestamp: Optional[str] = Field(None, description="Event creation ISO timestamp for out-of-order handling")

class WebhookResponse(BaseModel):
    status: str = Field(..., example="processed", description="Result: processed, duplicate_ignored, delayed_ignored, payment_not_found, error")
    message: str
    event_id: str
    payment_id: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_status: Optional[str] = None
    execution_time_ms: Optional[float] = None
