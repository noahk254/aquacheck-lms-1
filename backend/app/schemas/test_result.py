from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from app.models.test_result import TestStatus


class TestResultBase(BaseModel):
    sample_id: int
    method_id: int
    assigned_to: Optional[int] = None
    equipment_ids: Optional[List[int]] = []
    raw_observations: Optional[Dict[str, Any]] = {}
    result_value: Optional[str] = None
    result_unit: Optional[str] = None
    uncertainty_value: Optional[float] = None
    uncertainty_unit: Optional[str] = None
    notes: Optional[str] = None


class TestResultCreate(TestResultBase):
    pass


class TestResultUpdate(BaseModel):
    assigned_to: Optional[int] = None
    equipment_ids: Optional[List[int]] = None
    raw_observations: Optional[Dict[str, Any]] = None
    result_value: Optional[str] = None
    result_unit: Optional[str] = None
    uncertainty_value: Optional[float] = None
    uncertainty_unit: Optional[str] = None
    status: Optional[TestStatus] = None
    notes: Optional[str] = None
    amendments: Optional[List[Any]] = None


class TestResultOut(TestResultBase):
    id: int
    status: TestStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    validated_by: Optional[int] = None
    validated_at: Optional[datetime] = None
    amendments: Optional[List[Any]] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UncertaintyResult(BaseModel):
    standard_uncertainty: float
    expanded_uncertainty: float
    coverage_factor: float
    confidence_level: str
