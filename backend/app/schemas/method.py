from datetime import datetime, date
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.models.method import MethodStatus


class MethodBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    standard_reference: Optional[str] = None
    version: str = "1.0"
    performance_characteristics: Optional[Dict[str, Any]] = {}
    measurement_uncertainty_info: Optional[Dict[str, Any]] = {}


class MethodCreate(MethodBase):
    pass


class MethodUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    standard_reference: Optional[str] = None
    version: Optional[str] = None
    status: Optional[MethodStatus] = None
    validation_date: Optional[date] = None
    performance_characteristics: Optional[Dict[str, Any]] = None
    measurement_uncertainty_info: Optional[Dict[str, Any]] = None


class MethodOut(MethodBase):
    id: int
    status: MethodStatus
    validation_date: Optional[date] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MethodRevisionOut(BaseModel):
    id: int
    method_id: int
    version: str
    changes_description: Optional[str] = None
    revised_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
