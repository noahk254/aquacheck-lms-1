from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.models.document import DocumentCategory, DocumentStatus


class DocumentSection(BaseModel):
    heading: str = ""
    body: str = ""


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    version: Optional[str] = None
    status: Optional[DocumentStatus] = None
    effective_date: Optional[date] = None
    description: Optional[str] = None
    content: Optional[List[DocumentSection]] = None


class DocumentOut(BaseModel):
    id: int
    code: str
    title: str
    category: DocumentCategory
    version: str
    status: DocumentStatus
    effective_date: Optional[date] = None
    description: Optional[str] = None
    content: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
