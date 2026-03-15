import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class NonconformityStatus(str, enum.Enum):
    identified = "identified"
    suspended = "suspended"
    under_review = "under_review"
    corrective_action = "corrective_action"
    closed = "closed"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Nonconformity(Base):
    __tablename__ = "nonconformities"

    id = Column(Integer, primary_key=True, index=True)
    nc_number = Column(String, unique=True, index=True, nullable=False)
    related_sample_id = Column(Integer, ForeignKey("samples.id"), nullable=True)
    related_test_id = Column(Integer, ForeignKey("test_results.id"), nullable=True)
    description = Column(Text, nullable=False)
    risk_level = Column(SAEnum(RiskLevel), default=RiskLevel.low, nullable=False)
    identified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    identified_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(SAEnum(NonconformityStatus), default=NonconformityStatus.identified, nullable=False)
    work_suspended = Column(Boolean, default=False, nullable=False)
    investigation = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    customer_notified = Column(Boolean, default=False, nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    related_sample = relationship("Sample", back_populates="nonconformities")
    related_test = relationship("TestResult", back_populates="nonconformities")
    identifier = relationship("User", foreign_keys=[identified_by])
    closer = relationship("User", foreign_keys=[closed_by])
