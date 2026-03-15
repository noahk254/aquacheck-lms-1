import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, JSON, Text, Date
from sqlalchemy.orm import relationship
from app.database import Base


class MethodStatus(str, enum.Enum):
    draft = "draft"
    validated = "validated"
    deprecated = "deprecated"


class Method(Base):
    __tablename__ = "methods"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    standard_reference = Column(String, nullable=True)
    version = Column(String, default="1.0", nullable=False)
    status = Column(SAEnum(MethodStatus), default=MethodStatus.draft, nullable=False)
    validation_date = Column(Date, nullable=True)
    performance_characteristics = Column(JSON, default=dict)
    measurement_uncertainty_info = Column(JSON, default=dict)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    creator = relationship("User", foreign_keys=[created_by])
    revisions = relationship("MethodRevision", back_populates="method", cascade="all, delete-orphan")
    test_results = relationship("TestResult", back_populates="method")


class MethodRevision(Base):
    __tablename__ = "method_revisions"

    id = Column(Integer, primary_key=True, index=True)
    method_id = Column(Integer, ForeignKey("methods.id"), nullable=False)
    version = Column(String, nullable=False)
    changes_description = Column(Text, nullable=True)
    revised_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    method = relationship("Method", back_populates="revisions")
    revisor = relationship("User", foreign_keys=[revised_by])
