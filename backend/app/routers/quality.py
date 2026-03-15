from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.models.nonconformity import Nonconformity, NonconformityStatus, RiskLevel
from app.models.complaint import Complaint, ComplaintStatus
from app.models.sample import Sample, SampleStatus
from app.models.equipment import Equipment
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/quality", tags=["Quality"])


@router.get("/dashboard")
def quality_dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    open_ncs = db.query(Nonconformity).filter(
        Nonconformity.status.notin_([NonconformityStatus.closed])
    ).count()
    open_ncs_high = db.query(Nonconformity).filter(
        Nonconformity.status.notin_([NonconformityStatus.closed]),
        Nonconformity.risk_level == RiskLevel.high,
    ).count()
    open_ncs_medium = db.query(Nonconformity).filter(
        Nonconformity.status.notin_([NonconformityStatus.closed]),
        Nonconformity.risk_level == RiskLevel.medium,
    ).count()
    open_ncs_low = db.query(Nonconformity).filter(
        Nonconformity.status.notin_([NonconformityStatus.closed]),
        Nonconformity.risk_level == RiskLevel.low,
    ).count()
    open_complaints = db.query(Complaint).filter(
        Complaint.status != ComplaintStatus.closed
    ).count()
    samples_in_testing = db.query(Sample).filter(
        Sample.status == SampleStatus.in_testing
    ).count()
    threshold = date.today() + timedelta(days=30)
    calibration_due = db.query(Equipment).filter(
        Equipment.calibration_due_date <= threshold,
        Equipment.calibration_due_date != None,  # noqa: E711
    ).count()

    return {
        "open_nonconformities": open_ncs,
        "open_ncs_by_risk": {"high": open_ncs_high, "medium": open_ncs_medium, "low": open_ncs_low},
        "open_complaints": open_complaints,
        "samples_in_testing": samples_in_testing,
        "equipment_calibration_due": calibration_due,
    }


@router.get("/audit-logs")
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    resource_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin, UserRole.manager, UserRole.quality_manager, UserRole.auditor)),
):
    query = db.query(AuditLog)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
