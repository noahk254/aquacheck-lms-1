from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.models.contract import Contract
from app.models.sample import Sample, SampleStatus
from app.models.test_result import TestResult, TestStatus
from app.models.test_catalog import TestCatalogItem
from app.schemas.test_result import TestResultCreate, TestResultUpdate, TestResultOut, UncertaintyResult, BulkResultCreate
from app.services.audit import log_action
from app.services.uncertainty import calculate_uncertainty

router = APIRouter(prefix="/test-results", tags=["Test Results"])


@router.get("", response_model=List[TestResultOut])
def list_test_results(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(TestResult).order_by(TestResult.created_at.desc()).all()


@router.post("", response_model=TestResultOut, status_code=status.HTTP_201_CREATED)
def create_test_result(
    payload: TestResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sample = db.query(Sample).filter(Sample.id == payload.sample_id).first()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    if not sample.contract_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sample must be linked to a contract before testing")

    contract = db.query(Contract).filter(Contract.id == sample.contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sample contract not found")

    tr = TestResult(**payload.model_dump(), started_at=datetime.now(timezone.utc))
    if tr.status == TestStatus.pending:
        tr.status = TestStatus.in_progress

    if sample.status in {SampleStatus.received, SampleStatus.registered, SampleStatus.assigned}:
        sample.status = SampleStatus.in_testing

    db.add(tr)
    db.commit()
    db.refresh(tr)
    log_action(db, current_user.id, "CREATE_TEST_RESULT", "test_result", str(tr.id))
    return tr


@router.get("/{result_id}", response_model=TestResultOut)
def get_test_result(result_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    tr = db.query(TestResult).filter(TestResult.id == result_id).first()
    if not tr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found")
    return tr


@router.put("/{result_id}", response_model=TestResultOut)
def update_test_result(
    result_id: int,
    payload: TestResultUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tr = db.query(TestResult).filter(TestResult.id == result_id).first()
    if not tr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found")
    update_data = payload.model_dump(exclude_unset=True)
    # If result_value is set, mark completed
    if "result_value" in update_data and update_data["result_value"] and tr.status == TestStatus.in_progress:
        tr.status = TestStatus.completed
        tr.completed_at = datetime.now(timezone.utc)
    for k, v in update_data.items():
        setattr(tr, k, v)
    db.commit()
    db.refresh(tr)
    log_action(db, current_user.id, "UPDATE_TEST_RESULT", "test_result", str(result_id))
    return tr


@router.post("/{result_id}/validate", response_model=TestResultOut)
def validate_test_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.quality_manager)),
):
    tr = db.query(TestResult).filter(TestResult.id == result_id).first()
    if not tr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found")
    if tr.status not in [TestStatus.completed, TestStatus.in_progress]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Test must be completed before validation")
    tr.status = TestStatus.validated
    tr.validated_by = current_user.id
    tr.validated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tr)
    log_action(db, current_user.id, "VALIDATE_TEST_RESULT", "test_result", str(result_id))
    return tr


@router.post("/{result_id}/calculate-uncertainty", response_model=UncertaintyResult)
def calc_uncertainty(
    result_id: int,
    values: List[float] = Body(..., embed=True),
    coverage_factor: float = Body(2.0, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tr = db.query(TestResult).filter(TestResult.id == result_id).first()
    if not tr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found")
    result = calculate_uncertainty(values, coverage_factor)
    # Store in the test result
    tr.uncertainty_value = result["expanded_uncertainty"]
    tr.uncertainty_unit = tr.result_unit or ""
    db.commit()
    return UncertaintyResult(**result)
