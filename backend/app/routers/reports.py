from datetime import datetime, timezone
from typing import List
import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.deps import get_db, get_current_user
from app.models.user import User
from app.models.report import Report, ReportStatus
from app.models.contract import Contract
from app.schemas.report import ReportCreate, ReportUpdate, ReportOut
from app.services.audit import log_action

router = APIRouter(prefix="/reports", tags=["Reports"])


def _next_report_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(Report).filter(Report.report_number.like(f"RPT-{year}-%")).count()
    return f"RPT-{year}-{str(count + 1).zfill(5)}"


@router.get("", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Report).order_by(Report.created_at.desc()).all()


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = Report(**payload.model_dump(), report_number=_next_report_number(db))
    db.add(report)
    db.commit()
    db.refresh(report)
    log_action(db, current_user.id, "CREATE_REPORT", "report", str(report.id))
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.post("/{report_id}/issue", response_model=ReportOut)
def issue_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    report.status = ReportStatus.issued
    report.issued_by = current_user.id
    report.issued_at = datetime.now(timezone.utc)
    revision = list(report.revision_history or [])
    revision.append({"action": "issued", "user_id": current_user.id, "timestamp": datetime.now(timezone.utc).isoformat()})
    report.revision_history = revision
    db.commit()
    db.refresh(report)
    log_action(db, current_user.id, "ISSUE_REPORT", "report", str(report_id))
    return report


@router.get("/{report_id}/pdf")
def generate_pdf(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    contract = db.query(Contract).filter(Contract.id == report.contract_id).first()
    issuer = db.query(User).filter(User.id == report.issued_by).first() if report.issued_by else None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("title", parent=styles["Heading1"], textColor=colors.HexColor("#1A1A2E"), fontSize=18)
    subtitle_style = ParagraphStyle("subtitle", parent=styles["Normal"], textColor=colors.HexColor("#0ea5e9"), fontSize=11)

    story.append(Paragraph("AQUACHECK LABORATORIES LTD.", title_style))
    story.append(Paragraph("ISO/IEC 17025 Accredited Testing Laboratory", subtitle_style))
    story.append(Spacer(1, 0.5 * cm))

    header_data = [
        ["Report Number:", report.report_number],
        ["Report Type:", report.report_type.replace("_", " ").title()],
        ["Contract:", contract.contract_number if contract else "N/A"],
        ["Status:", report.status.value.upper()],
        ["Issued By:", issuer.full_name if issuer else "N/A"],
        ["Issued At:", report.issued_at.strftime("%Y-%m-%d %H:%M UTC") if report.issued_at else "Not issued"],
    ]
    t = Table(header_data, colWidths=[5 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0f2fe")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Report Content", styles["Heading2"]))
    content = report.content or {}
    if content:
        content_data = [[str(k), str(v)] for k, v in content.items()]
        ct = Table(content_data, colWidths=[6 * cm, 11 * cm])
        ct.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(ct)
    else:
        story.append(Paragraph("No content recorded.", styles["Normal"]))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "This report is issued in accordance with ISO/IEC 17025:2017 requirements. "
        "Results relate only to items tested.",
        styles["Normal"],
    ))

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={report.report_number}.pdf"},
    )
