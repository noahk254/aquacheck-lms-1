import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, JSON, Text, Float
from sqlalchemy.orm import relationship
from app.database import Base


class TestStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    validated = "validated"
    failed = "failed"


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), nullable=False)
    method_id = Column(Integer, ForeignKey("methods.id"), nullable=True)
    catalog_item_id = Column(Integer, ForeignKey("test_catalog.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    equipment_ids = Column(JSON, default=list)
    raw_observations = Column(JSON, default=dict)
    result_value = Column(String, nullable=True)
    result_unit = Column(String, nullable=True)
    uncertainty_value = Column(Float, nullable=True)
    uncertainty_unit = Column(String, nullable=True)
    status = Column(SAEnum(TestStatus), default=TestStatus.pending, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    validated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    amendments = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    sample = relationship("Sample", back_populates="test_results")
    method = relationship("Method", back_populates="test_results")
    assignee = relationship("User", foreign_keys=[assigned_to])
    validator = relationship("User", foreign_keys=[validated_by])
    nonconformities = relationship("Nonconformity", back_populates="related_test")
