import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ContractStatus(str, enum.Enum):
    draft = "draft"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String, nullable=False)
    scope_of_work = Column(Text, nullable=True)
    requested_tests = Column(JSON, default=list)
    decision_rules = Column(Text, nullable=True)
    status = Column(SAEnum(ContractStatus), default=ContractStatus.draft, nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    customer = relationship("Customer", back_populates="contracts")
    samples = relationship("Sample", back_populates="contract")
    reports = relationship("Report", back_populates="contract")
    complaints = relationship("Complaint", back_populates="contract")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    approver = relationship("User", foreign_keys=[approved_by])
