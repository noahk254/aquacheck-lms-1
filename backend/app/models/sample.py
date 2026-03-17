import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, JSON, Text, Date
from sqlalchemy.orm import relationship
from app.database import Base


class SampleStatus(str, enum.Enum):
    received = "received"
    registered = "registered"
    assigned = "assigned"
    in_testing = "in_testing"
    completed = "completed"
    archived = "archived"
    disposed = "disposed"


class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    sample_code = Column(String, unique=True, index=True, nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    description = Column(Text, nullable=True)
    sample_type = Column(String, nullable=True)
    collection_date = Column(Date, nullable=True)
    collection_location = Column(String, nullable=True)
    gps_coordinates = Column(String, nullable=True)
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    storage_condition = Column(String, nullable=True)
    status = Column(SAEnum(SampleStatus), default=SampleStatus.received, nullable=False)
    barcode_data = Column(Text, nullable=True)
    disposal_date = Column(Date, nullable=True)
    disposal_method = Column(String, nullable=True)
    chain_of_custody = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    requested_test_ids = Column(JSON, default=list)

    contract = relationship("Contract", back_populates="samples")
    receiver = relationship("User", foreign_keys=[received_by])
    test_results = relationship("TestResult", back_populates="sample")
    nonconformities = relationship("Nonconformity", back_populates="related_sample")
