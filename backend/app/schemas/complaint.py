from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.complaint import ComplaintStatus


class ComplaintBase(BaseModel):
    customer_id: int
    contract_id: Optional[int] = None
    description: str
    reported_by: Optional[str] = None


class ComplaintCreate(ComplaintBase):
    pass


class ComplaintUpdate(BaseModel):
    description: Optional[str] = None
    investigation_notes: Optional[str] = None
    corrective_action: Optional[str] = None
    status: Optional[ComplaintStatus] = None


class ComplaintOut(ComplaintBase):
    id: int
    complaint_number: str
    status: ComplaintStatus
    received_at: datetime
    investigation_notes: Optional[str] = None
    corrective_action: Optional[str] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
