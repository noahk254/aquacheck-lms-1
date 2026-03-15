from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.nonconformity import NonconformityStatus, RiskLevel


class NonconformityBase(BaseModel):
    description: str
    risk_level: RiskLevel = RiskLevel.low
    related_sample_id: Optional[int] = None
    related_test_id: Optional[int] = None


class NonconformityCreate(NonconformityBase):
    pass


class NonconformityUpdate(BaseModel):
    description: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    status: Optional[NonconformityStatus] = None
    investigation: Optional[str] = None
    corrective_action: Optional[str] = None
    customer_notified: Optional[bool] = None
    work_suspended: Optional[bool] = None


class NonconformityOut(NonconformityBase):
    id: int
    nc_number: str
    identified_by: Optional[int] = None
    identified_at: datetime
    status: NonconformityStatus
    work_suspended: bool
    investigation: Optional[str] = None
    corrective_action: Optional[str] = None
    customer_notified: bool
    closed_at: Optional[datetime] = None
    closed_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
