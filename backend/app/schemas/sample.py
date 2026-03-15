from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel
from app.models.sample import SampleStatus


class SampleBase(BaseModel):
    contract_id: int
    description: Optional[str] = None
    sample_type: Optional[str] = None
    collection_date: Optional[date] = None
    collection_location: Optional[str] = None
    gps_coordinates: Optional[str] = None
    storage_condition: Optional[str] = None


class SampleCreate(SampleBase):
    pass


class SampleUpdate(BaseModel):
    description: Optional[str] = None
    sample_type: Optional[str] = None
    collection_date: Optional[date] = None
    collection_location: Optional[str] = None
    gps_coordinates: Optional[str] = None
    storage_condition: Optional[str] = None
    status: Optional[SampleStatus] = None
    disposal_date: Optional[date] = None
    disposal_method: Optional[str] = None


class CustodyEntry(BaseModel):
    action: str


class SampleOut(SampleBase):
    id: int
    sample_code: str
    received_by: Optional[int] = None
    received_at: datetime
    status: SampleStatus
    barcode_data: Optional[str] = None
    disposal_date: Optional[date] = None
    disposal_method: Optional[str] = None
    chain_of_custody: Optional[List[Any]] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
