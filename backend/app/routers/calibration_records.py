import os
import uuid
from datetime import date
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.calibration_record import CalibrationRecord, CalibrationResult
from app.models.equipment import Equipment
from app.models.user import User

router = APIRouter(prefix="/calibration-records", tags=["Calibration Records"])

UPLOAD_BASE = Path(os.environ.get("UPLOAD_DIR", str(Path(__file__).parent.parent.parent / "uploads")))
CERT_DIR = UPLOAD_BASE / "calibration_certs"


def ensure_cert_dir():
    CERT_DIR.mkdir(parents=True, exist_ok=True)


# ─── Pydantic output schema ───────────────────────────────────────────────────

class CalibrationRecordOut(BaseModel):
    id: int
    equipment_id: int
    calibration_date: date
    next_due_date: date
    performed_by: Optional[str] = None
    certificate_ref: Optional[str] = None
    result: Optional[CalibrationResult] = None
    notes: Optional[str] = None
    has_certificate: bool
    created_by: Optional[int] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj: CalibrationRecord):
        return cls(
            id=obj.id,
            equipment_id=obj.equipment_id,
            calibration_date=obj.calibration_date,
            next_due_date=obj.next_due_date,
            performed_by=obj.performed_by,
            certificate_ref=obj.certificate_ref,
            result=obj.result,
            notes=obj.notes,
            has_certificate=bool(obj.certificate_filename),
            created_by=obj.created_by,
            created_at=obj.created_at.isoformat() if obj.created_at else "",
            updated_at=obj.updated_at.isoformat() if obj.updated_at else "",
        )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=List[CalibrationRecordOut])
def list_records(
    equipment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    records = (
        db.query(CalibrationRecord)
        .filter(CalibrationRecord.equipment_id == equipment_id)
        .order_by(CalibrationRecord.calibration_date.desc())
        .all()
    )
    return [CalibrationRecordOut.from_orm(r) for r in records]


@router.post("", response_model=CalibrationRecordOut, status_code=status.HTTP_201_CREATED)
async def create_record(
    equipment_id: int = Form(...),
    calibration_date: date = Form(...),
    next_due_date: date = Form(...),
    performed_by: Optional[str] = Form(None),
    certificate_ref: Optional[str] = Form(None),
    result: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    certificate: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    equip = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equip:
        raise HTTPException(status_code=404, detail="Equipment not found")

    cert_result = CalibrationResult(result) if result else None

    cert_filename = None
    if certificate and certificate.filename:
        if not certificate.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted for calibration certificates")
        ensure_cert_dir()
        safe_name = "".join(c for c in Path(certificate.filename).stem if c.isalnum() or c in "-_")[:50]
        cert_filename = f"{uuid.uuid4().hex}_{safe_name}.pdf"
        dest = CERT_DIR / cert_filename
        content = await certificate.read()
        dest.write_bytes(content)

    record = CalibrationRecord(
        equipment_id=equipment_id,
        calibration_date=calibration_date,
        next_due_date=next_due_date,
        performed_by=performed_by or None,
        certificate_ref=certificate_ref or None,
        result=cert_result,
        notes=notes or None,
        certificate_filename=cert_filename,
        created_by=current_user.id,
    )
    db.add(record)

    equip.last_calibration_date = calibration_date
    equip.calibration_due_date = next_due_date
    if certificate_ref:
        equip.calibration_certificate_ref = certificate_ref

    db.commit()
    db.refresh(record)
    return CalibrationRecordOut.from_orm(record)


@router.get("/{record_id}/certificate")
def download_certificate(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    record = db.query(CalibrationRecord).filter(CalibrationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if not record.certificate_filename:
        raise HTTPException(status_code=404, detail="No certificate attached to this record")
    path = CERT_DIR / record.certificate_filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Certificate file not found on server")
    display_name = f"calibration_cert_{record_id}.pdf"
    return FileResponse(str(path), media_type="application/pdf", filename=display_name)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    record = db.query(CalibrationRecord).filter(CalibrationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.certificate_filename:
        path = CERT_DIR / record.certificate_filename
        if path.exists():
            path.unlink()
    db.delete(record)
    db.commit()
