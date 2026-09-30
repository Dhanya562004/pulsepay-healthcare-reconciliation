from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime

class InvoiceCreate(BaseModel):
    patient_id: str = Field(..., example="PAT-90210", description="Unique identifier for the patient")
    patient_name: str = Field(default="John Doe", example="Sarah Connor", description="Full name of the patient")
    service_description: str = Field(default="General Healthcare Service", example="MRI Scan & Radiology", description="Medical service provided")
    amount: float = Field(..., gt=0, example=450.00, description="Invoice amount in USD/INR")

class InvoiceResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    service_description: str
    amount: float
    status: str
    created_at: Union[datetime, str]
    updated_at: Union[datetime, str]

    class Config:
        from_attributes = True

class InvoiceDetailResponse(InvoiceResponse):
    payments: List[dict] = []
