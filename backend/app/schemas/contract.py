from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel
from app.models.contract import ContractStatus


class ContractBase(BaseModel):
    title: str
    customer_id: int
    scope_of_work: Optional[str] = None
    requested_tests: Optional[List[Any]] = []
    decision_rules: Optional[str] = None


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    scope_of_work: Optional[str] = None
    requested_tests: Optional[List[Any]] = None
    decision_rules: Optional[str] = None
    status: Optional[ContractStatus] = None


class ContractOut(ContractBase):
    id: int
    contract_number: str
    status: ContractStatus
    reviewed_by: Optional[int] = None
    approved_by: Optional[int] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
