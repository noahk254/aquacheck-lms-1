from datetime import datetime, timezone, date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.models.method import Method, MethodStatus, MethodRevision
from app.schemas.method import MethodCreate, MethodUpdate, MethodOut, MethodRevisionOut
from app.services.audit import log_action

router = APIRouter(prefix="/methods", tags=["Methods"])


@router.get("", response_model=List[MethodOut])
def list_methods(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Method).order_by(Method.created_at.desc()).all()


@router.post("", response_model=MethodOut, status_code=status.HTTP_201_CREATED)
def create_method(
    payload: MethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.quality_manager)),
):
    existing = db.query(Method).filter(Method.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Method code already exists")
    method = Method(**payload.model_dump(), created_by=current_user.id)
    db.add(method)
    db.commit()
    db.refresh(method)
    log_action(db, current_user.id, "CREATE_METHOD", "method", str(method.id))
    return method


@router.get("/{method_id}", response_model=MethodOut)
def get_method(method_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    method = db.query(Method).filter(Method.id == method_id).first()
    if not method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Method not found")
    return method


@router.put("/{method_id}", response_model=MethodOut)
def update_method(
    method_id: int,
    payload: MethodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.quality_manager)),
):
    method = db.query(Method).filter(Method.id == method_id).first()
    if not method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Method not found")
    old_version = method.version
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(method, k, v)
    # Record revision if version changed
    if payload.version and payload.version != old_version:
        revision = MethodRevision(
            method_id=method_id,
            version=payload.version,
            changes_description=f"Updated from version {old_version} to {payload.version}",
            revised_by=current_user.id,
        )
        db.add(revision)
    db.commit()
    db.refresh(method)
    log_action(db, current_user.id, "UPDATE_METHOD", "method", str(method_id))
    return method


@router.post("/{method_id}/validate", response_model=MethodOut)
def validate_method(
    method_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.quality_manager)),
):
    method = db.query(Method).filter(Method.id == method_id).first()
    if not method:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Method not found")
    method.status = MethodStatus.validated
    method.validation_date = date.today()
    db.commit()
    db.refresh(method)
    log_action(db, current_user.id, "VALIDATE_METHOD", "method", str(method_id))
    return method


@router.get("/{method_id}/revisions", response_model=List[MethodRevisionOut])
def get_revisions(method_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(MethodRevision).filter(MethodRevision.method_id == method_id).all()
