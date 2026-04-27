import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from app.database import Base


class CalibrationResult(str, enum.Enum):
    pass_ = "pass"
    fail = "fail"
    conditional = "conditional"


class CalibrationRecord(Base):
    __tablename__ = "calibration_records"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False, index=True)
    calibration_date = Column(Date, nullable=False)
    next_due_date = Column(Date, nullable=False)
    performed_by = Column(String, nullable=True)
    certificate_ref = Column(String, nullable=True)
    result = Column(SAEnum(CalibrationResult), nullable=True)
    notes = Column(Text, nullable=True)
    certificate_filename = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    equipment = relationship("Equipment", back_populates="calibration_records")
    creator = relationship("User", foreign_keys=[created_by])
