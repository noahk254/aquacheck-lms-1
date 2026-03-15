from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.nonconformity import Nonconformity, NonconformityStatus
from app.schemas.nonconformity import NonconformityCreate, NonconformityUpdate, NonconformityOut
from app.services.audit import log_action

router = APIRouter(prefix="/nonconformities", tags=["Nonconformities"])


def _next_nc_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(Nonconformity).filter(Nonconformity.nc_number.like(f"NC-{year}-%")).count()
    return f"NC-{year}-{str(count + 1).zfill(5)}"


@router.get("", response_model=List[NonconformityOut])
def list_ncs(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Nonconformity).order_by(Nonconformity.created_at.desc()).all()


@router.post("", response_model=NonconformityOut, status_code=status.HTTP_201_CREATED)
def create_nc(
    payload: NonconformityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    nc = Nonconformity(
        **payload.model_dump(),
        nc_number=_next_nc_number(db),
        identified_by=current_user.id,
    )
    db.add(nc)
    db.commit()
    db.refresh(nc)
    log_action(db, current_user.id, "CREATE_NC", "nonconformity", str(nc.id))
    return nc


@router.get("/{nc_id}", response_model=NonconformityOut)
def get_nc(nc_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    nc = db.query(Nonconformity).filter(Nonconformity.id == nc_id).first()
    if not nc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nonconformity not found")
    return nc


@router.put("/{nc_id}", response_model=NonconformityOut)
def update_nc(
    nc_id: int,
    payload: NonconformityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    nc = db.query(Nonconformity).filter(Nonconformity.id == nc_id).first()
    if not nc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nonconformity not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(nc, k, v)
    db.commit()
    db.refresh(nc)
    log_action(db, current_user.id, "UPDATE_NC", "nonconformity", str(nc_id))
    return nc


@router.post("/{nc_id}/suspend", response_model=NonconformityOut)
def suspend_work(
    nc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    nc = db.query(Nonconformity).filter(Nonconformity.id == nc_id).first()
    if not nc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nonconformity not found")
    nc.work_suspended = True
    nc.status = NonconformityStatus.suspended
    db.commit()
    db.refresh(nc)
    log_action(db, current_user.id, "SUSPEND_WORK_NC", "nonconformity", str(nc_id))
    return nc


@router.post("/{nc_id}/close", response_model=NonconformityOut)
def close_nc(
    nc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    nc = db.query(Nonconformity).filter(Nonconformity.id == nc_id).first()
    if not nc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nonconformity not found")
    nc.status = NonconformityStatus.closed
    nc.closed_at = datetime.now(timezone.utc)
    nc.closed_by = current_user.id
    db.commit()
    db.refresh(nc)
    log_action(db, current_user.id, "CLOSE_NC", "nonconformity", str(nc_id))
    return nc
