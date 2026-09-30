from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: Optional[str]
    message: str
    details: Optional[str]
    timestamp: str

    class Config:
        from_attributes = True

class SystemMetricsResponse(BaseModel):
    total_invoices: int
    total_invoiced_amount: float
    total_collected_amount: float
    total_pending_amount: float
    invoice_status_counts: Dict[str, int]
    total_payments: int
    payment_status_counts: Dict[str, int]
    total_webhooks: int
    duplicate_webhooks_blocked: int
    delayed_webhooks_handled: int
    total_mismatches_detected: int
