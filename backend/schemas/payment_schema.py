from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import datetime

class PaymentCreate(BaseModel):
    invoice_id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000", description="Target invoice UUID")
    amount: Optional[float] = Field(None, gt=0, example=450.00, description="Amount to pay (defaults to full invoice amount)")
    provider: str = Field(default="razorpay", example="razorpay", description="Payment gateway (razorpay, stripe, mock_gateway)")
    simulate_failure: bool = Field(default=False, description="Optionally force payment gateway initiation failure for testing")

class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    amount: float
    status: str
    provider: str
    external_reference_id: str
    failure_reason: Optional[str] = None
    created_at: Union[datetime, str]
    updated_at: Union[datetime, str]

    class Config:
        from_attributes = True

class PaymentRetryRequest(BaseModel):
    payment_id: str = Field(..., description="UUID of the failed payment to retry")
    force_success: bool = Field(default=True, description="Force gateway retry success")
