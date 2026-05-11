from collections import OrderedDict
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
from app.models.user import User, UserRole
from app.models.report import Report, ReportStatus
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.sample import Sample
from app.models.test_result import TestResult
from app.schemas.report import ReportCreate, ReportUpdate, ReportOut
from app.services.audit import log_action

router = APIRouter(prefix="/reports", tags=["Reports"])


def _next_report_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(Report).filter(Report.report_number.like(f"RPT-{year}-%")).count()
    return f"RPT-{year}-{str(count + 1).zfill(5)}"


def _content_value(content: dict, key: str, default=None):
    value = (content or {}).get(key, default)
    return default if value in (None, "") else value


def _format_date(value):
    if not value:
        return "N/A"
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    return str(value)


_SCHEDULE_SPEC_HEADERS = {
    3: "NEMA STANDARD FOR EFFLUENT WATER; THIRD SCHEDULE.\nMaximum levels Permissible.",
    4: "NEMA MONITORING GUIDE;\nFOURTH SCHEDULE.",
    5: "NEMA STANDARD FOR EFFLUENT;\nFIFTH SCHEDULE.\n(Public Sewer Discharge)",
    6: "NEMA MONITORING STANDARD;\nSIXTH SCHEDULE.",
}

_SCHEDULE_CONTEXT = {
    3: "discharge into the environment",
    5: "discharge into public sewers",
    6: "discharge of treated effluent into the environment",
}


def _schedule_ns_note(waste_schedule):
    base = "NS: No Set Standard, ND: Not Detectable, TNTC: Too numerous to count, USEPA: United States Environmental Protection Agency, APHA: American Public Health Association."
    if waste_schedule:
        return base + " NEMA: National Environmental Management Authority."
    return base + " KS: Kenya Standard, EAS: East African Standard."


def _remarks_para(remarks, style):
    text = str(remarks) if remarks and remarks != "—" else "—"
    upper = text.upper()
    if "NON-COMPLIANT" in upper:
        return Paragraph(f'<font color="#dc2626"><b>{text}</b></font>', style)
    if "COMPLIANT" in upper:
        return Paragraph(f'<font color="#16a34a">{text}</font>', style)
    return text


def _auto_comment(sample, result_sections):
    if not sample or not sample.waste_schedule:
        return None
    non_compliant = [
        row.get("parameter", "")
        for section in result_sections
        for row in section.get("rows", [])
        if "NON-COMPLIANT" in str(row.get("remarks", "")).upper()
    ]
    if not non_compliant:
        return f"All tested parameters comply with the applicable NEMA schedule {sample.waste_schedule} standards."
    context = _SCHEDULE_CONTEXT.get(sample.waste_schedule, "the applicable standards")
    param_list = ", ".join(p for p in non_compliant if p)
    return (
        f"The parameters; {param_list} do not meet the set specifications for {context} "
        "based on the legal notice No.120 of EMCA, 2006. Treatment is therefore recommended."
    )


def _result_sections(test_results, content: dict, sample=None):
    manual_sections = content.get("result_sections")
    if isinstance(manual_sections, list) and manual_sections:
        return manual_sections

    waste_schedule = getattr(sample, "waste_schedule", None) if sample else None
    default_spec_header = _SCHEDULE_SPEC_HEADERS.get(waste_schedule, "SPECIFICATION")

    sections = OrderedDict()
    for result in test_results:
        raw = result.raw_observations or {}
        section_name = raw.get("section") or "TEST"
        sections.setdefault(section_name, []).append(
            {
                "parameter": raw.get("parameter_name") or (result.method.name if result.method else f"Method #{result.method_id}"),
                "method": raw.get("method_name") or (
                    result.method.standard_reference
                    if result.method and result.method.standard_reference
                    else result.method.code if result.method else "N/A"
                ),
                "result": result.result_value or "Pending",
                "specification": raw.get("specification") or raw.get("standard_limit") or raw.get("limit") or "—",
                "remarks": raw.get("remarks") or raw.get("compliance") or result.notes or "—",
            }
        )

    return [
        {
            "title": title,
            "specification_header": _content_value(content, "specification_title", default_spec_header),
            "rows": rows,
        }
        for title, rows in sections.items()
    ]


@router.get("", response_model=List[ReportOut])
def list_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Report)
    if current_user.role == UserRole.customer and current_user.customer_id:
        q = (
            q.join(Contract, Report.contract_id == Contract.id)
             .filter(Contract.customer_id == current_user.customer_id)
        )
    return q.order_by(Report.created_at.desc()).all()


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not permitted to create reports.",
        )
    contract = db.query(Contract).filter(Contract.id == payload.contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    content = payload.content or {}
    sample_id = content.get("sample_id")
    if sample_id:
        sample = db.query(Sample).filter(Sample.id == sample_id).first()
        if not sample:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
        if sample.contract_id != payload.contract_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected sample does not belong to this contract")

    report = Report(**payload.model_dump(), report_number=_next_report_number(db))
    db.add(report)
    db.commit()
    db.refresh(report)
    log_action(db, current_user.id, "CREATE_REPORT", "report", str(report.id))
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    # Customers may only view reports belonging to their own customer account
    if current_user.role == UserRole.customer and current_user.customer_id:
        contract = db.query(Contract).filter(Contract.id == report.contract_id).first()
        if not contract or contract.customer_id != current_user.customer_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return report


@router.post("/{report_id}/issue", response_model=ReportOut)
def issue_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not permitted to issue reports.",
        )
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
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    customer = db.query(Customer).filter(Customer.id == contract.customer_id).first()
    issuer = db.query(User).filter(User.id == report.issued_by).first() if report.issued_by else None
    content = report.content or {}
    sample_id = content.get("sample_id")
    sample = db.query(Sample).filter(Sample.id == sample_id).first() if sample_id else None
    test_results = []
    if sample:
        test_results = (
            db.query(TestResult)
            .filter(TestResult.sample_id == sample.id)
            .order_by(TestResult.created_at.asc())
            .all()
        )

    waste_schedule = getattr(sample, "waste_schedule", None) if sample else None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("title", parent=styles["Heading1"], textColor=colors.HexColor("#1A1A2E"), fontSize=16, alignment=1, spaceAfter=6)
    company_style = ParagraphStyle("company", parent=styles["Normal"], fontSize=8, leading=10, alignment=2)
    small_style = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=10)
    cell_style = ParagraphStyle("cell", parent=styles["Normal"], fontSize=8, leading=9)
    header_cell_style = ParagraphStyle("header_cell", parent=styles["Normal"], fontSize=8, leading=9, fontName="Helvetica-Bold", alignment=1)

    header_table = Table(
        [[
            Paragraph("<b>AQUACHECK</b><br/>Trusted Quality Check Partner", styles["Title"]),
            Paragraph(
                "AQUACHECK LABORATORIES LIMITED<br/>P.O. Box 216 - 00300, NAIROBI<br/>Westlands Commercial Centre<br/>Off Ring Road, Parklands Rd<br/>Email: aquachecklab@gmail.com<br/>Website: www.aquachecklab.com<br/>Tel: 0755596064/0734933819",
                company_style,
            ),
        ]],
        colWidths=[8.2 * cm, 8.8 * cm],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#60a5fa")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(_content_value(content, "report_title", "TEST REPORT"), title_style))
    story.append(Spacer(1, 0.15 * cm))

    def _contact_person_value():
        override = _content_value(content, "client_contact", None)
        if override:
            return override
        if not customer:
            return "N/A"
        parts = [p for p in [customer.contact_person, customer.phone] if p]
        return ", ".join(parts) if parts else "N/A"

    info_data = [
        ["SAMPLE DESCRIPTION:", sample.description if sample and sample.description else _content_value(content, "sample_description", "N/A"), "SAMPLING DATE:", _format_date(_content_value(content, "sampling_date", sample.collection_date if sample else None))],
        ["SUBMITTED BY:", _content_value(content, "submitted_by", customer.name if customer else "N/A"), "RECEIVED ON:", _format_date(_content_value(content, "received_on", sample.received_at if sample else None))],
        ["CONTACT PERSON:", _contact_person_value(), "ANALYSIS DATE:", _format_date(_content_value(content, "analysis_date", report.created_at))],
        ["SAMPLED BY:", _content_value(content, "sampled_by", "AQUACHECK LABORATORIES LTD"), "REPORT ISSUED ON:", _format_date(report.issued_at or _content_value(content, "report_issued_on", None))],
        ["SAMPLING LOCATION:", _content_value(content, "sampling_location", sample.collection_location if sample else "N/A"), "SAMPLE LAB ID:", _content_value(content, "sample_lab_id", sample.sample_code if sample else report.report_number)],
    ]
    info_table = Table(info_data, colWidths=[3.2 * cm, 5.3 * cm, 3.2 * cm, 5.3 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.2 * cm))

    result_sections = _result_sections(test_results, content, sample)
    if result_sections:
        for section in result_sections:
            spec_header = section.get("specification_header", "SPECIFICATION")
            result_rows = [[
                Paragraph(section.get("title", "TEST"), header_cell_style),
                Paragraph("METHOD", header_cell_style),
                Paragraph("RESULTS", header_cell_style),
                Paragraph(spec_header.replace("\n", "<br/>"), header_cell_style),
                Paragraph("REMARKS", header_cell_style),
            ]]
            for row in section.get("rows", []):
                result_rows.append([
                    row.get("parameter", "—"),
                    row.get("method", "—"),
                    row.get("result", "—"),
                    row.get("specification", "—"),
                    _remarks_para(row.get("remarks", "—"), cell_style),
                ])

            results_table = Table(result_rows, colWidths=[5.5 * cm, 4.1 * cm, 1.5 * cm, 3.2 * cm, 2.7 * cm])
            results_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9ca3af")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(results_table)
            story.append(Spacer(1, 0.12 * cm))
    else:
        story.append(Paragraph("No analytical results are linked to this report yet.", styles["Normal"]))

    ns_note = _content_value(content, "ns_definition", None) or _schedule_ns_note(waste_schedule)
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(f"<b>NS:</b> {ns_note}", small_style))
    story.append(Paragraph("<b>DISCLAIMER</b>", small_style))
    story.append(Paragraph(
        _content_value(
            content,
            "disclaimer",
            "These results only apply to the sample submitted and the recommendations/comments are only based on the tested parameters. "
            "The laboratory will not be held responsible for any sampling errors, which may include improper collection techniques, "
            "contamination during the sampling process, or inadequate sample representation. "
            "The test report shall not be reproduced without the written approval of Aquacheck Laboratories Ltd.",
        ),
        small_style,
    ))
    story.append(Paragraph("<b>COMMENTS.</b>", small_style))
    auto_comment = _auto_comment(sample, result_sections)
    story.append(Paragraph(
        _content_value(
            content,
            "final_comment",
            auto_comment or "Results reflect the items tested and should be interpreted together with the reported method, sample details, and decision rules.",
        ),
        styles["Normal"],
    ))

    story.append(Spacer(1, 0.8 * cm))
    signatory_table = Table([
        [
            Paragraph(f"<b>{_content_value(content, 'authorizer_name', 'Victor Mutai')}</b><br/>{_content_value(content, 'authorizer_title', 'Water Chemist')}", styles["Normal"]),
            Paragraph(f"<b>{_content_value(content, 'analyst_name', issuer.full_name if issuer else 'Lab Analyst')}</b><br/>{_content_value(content, 'analyst_title', 'Lab analyst')}", styles["Normal"]),
        ]
    ], colWidths=[8.5 * cm, 8.5 * cm])
    signatory_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (0, 0), 1, colors.black),
        ("LINEABOVE", (1, 0), (1, 0), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(signatory_table)

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={report.report_number}.pdf"},
    )
