"""Professional two-page PDF reports from stored resume analysis (ReportLab)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.resume_analysis import ResumeAnalysisOutput

COMPANY_NAME = "MyCareer AI"
SUPPORT_EMAIL = "habin936@gmail.com"
CONFIDENTIAL_TAGLINE = "Confidential candidate summary"

# Brand palette
BRAND_PRIMARY = colors.HexColor("#0369a1")
BRAND_ACCENT = colors.HexColor("#0ea5e9")
BRAND_DARK = colors.HexColor("#0f172a")
BRAND_MUTED = colors.HexColor("#64748b")
BRAND_PANEL = colors.HexColor("#f0f9ff")

# Tight content budgets to keep layout within ~2 pages (Letter).
_SUMMARY_MAX = 720
_SKILLS_TECH_MAX = 12
_PROF_MAX = 320
_ATS_NOTES_MAX = 260
_ATS_BULLETS = 4
_CAREER_ROLES = 6
_OUTLOOK_MAX = 360
_IMPROVE_BULLETS = 4
_GAP_ITEMS = 5
_INDUSTRY_CTX_MAX = 280
_COURSES = 5
_SW_QUICK = 3


def _safe_findings_dict(raw: Any) -> dict[str, Any] | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


def _parse_analysis_output(findings: dict[str, Any] | None) -> ResumeAnalysisOutput | None:
    if not findings:
        return None
    data = {k: v for k, v in findings.items() if k != "_meta"}
    try:
        return ResumeAnalysisOutput.model_validate(data)
    except Exception:
        return None


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text or ""), style)


def _bullets(items: list[str], style: ParagraphStyle, max_items: int) -> list:
    out: list = []
    slice_ = items[:max_items]
    for it in slice_:
        t = str(it).strip()
        if t:
            out.append(Paragraph(f"• {escape(t)}", style))
            out.append(Spacer(1, 2))
    if len(items) > max_items:
        out.append(
            Paragraph(
                f"<i>{escape(f'…and {len(items) - max_items} more in the app')}</i>",
                style,
            )
        )
    return out


def _skill_gap_flowables(
    nlp: ResumeAnalysisOutput | None,
    bullet_style: ParagraphStyle,
    body_style: ParagraphStyle,
) -> list:
    """Skill gap section: structured gaps, or synthesized plain text when gaps are empty."""
    out: list = []
    if nlp and nlp.skill_gap_analysis.gaps:
        for g in nlp.skill_gap_analysis.gaps[:_GAP_ITEMS]:
            line = (
                f"<b>{escape(g.skill)}</b> ({escape(g.importance)}): "
                f"{escape(g.gap_description[:220])}"
            )
            out.append(Paragraph(line, bullet_style))
            out.append(Spacer(1, 2))
        if nlp.skill_gap_analysis.industry_context.strip():
            out.append(
                _p(nlp.skill_gap_analysis.industry_context[:_INDUSTRY_CTX_MAX], body_style)
            )
        return out

    # Populate when empty: synthesize from other NLP signals (no fabrication of new facts).
    if not nlp:
        out.append(
            _p(
                "Structured skill gap data was not available for this export. "
                "Re-run resume analysis in MyCareer AI for a detailed gap map.",
                body_style,
            )
        )
        return out

    parts: list[str] = []
    if nlp.weaknesses:
        parts.append(
            "Focus areas (from your analysis): "
            + "; ".join(escape(w) for w in nlp.weaknesses[:6])
        )
    if nlp.improvement_suggestions:
        parts.append(
            "Resume improvements to close common gaps: "
            + "; ".join(escape(s) for s in nlp.improvement_suggestions[:5])
        )
    if nlp.skills_assessment.proficiency_notes.strip():
        parts.append(escape(nlp.skills_assessment.proficiency_notes[:400]))
    if nlp.recommended_roles:
        parts.append(
            "Skills implied by target roles ("
            + ", ".join(escape(r) for r in nlp.recommended_roles[:5])
            + "): prioritize depth in the stack you use most, plus measurable outcomes."
        )
    if nlp.ats_compatibility.suggestions:
        parts.append(
            "ATS-oriented improvements that often correlate with clearer skill signaling: "
            + "; ".join(escape(s) for s in nlp.ats_compatibility.suggestions[:4])
        )

    if parts:
        out.append(_p(" ".join(parts)[:1600], body_style))
    else:
        out.append(
            _p(
                "No dedicated skill-gap rows were stored. Use the in-app analysis to "
                "prioritize skills against your target roles and refresh this report.",
                body_style,
            )
        )
    return out


def _qr_block(url: str | None, caption_style: ParagraphStyle) -> list:
    if not url or not str(url).strip():
        return []
    try:
        buf = BytesIO()
        qr = qrcode.QRCode(version=None, box_size=2, border=1)
        qr.add_data(url.strip())
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(buf, format="PNG")
        buf.seek(0)
        im = Image(ImageReader(buf), width=0.72 * inch, height=0.72 * inch)
        return [
            im,
            Spacer(1, 3),
            _p("Scan to open this analysis in the app", caption_style),
        ]
    except Exception:
        return []


def _candidate_table(
    display_name: str | None,
    email: str | None,
    linkedin: str | None,
    github: str | None,
    label_style: ParagraphStyle,
    value_style: ParagraphStyle,
) -> Table:
    def cell_val(v: str | None) -> Paragraph:
        t = (v or "").strip() or "—"
        return Paragraph(escape(t), value_style)

    data = [
        [
            Paragraph("<b>Name</b>", label_style),
            cell_val(display_name),
            Paragraph("<b>Email</b>", label_style),
            cell_val(email),
        ],
        [
            Paragraph("<b>LinkedIn</b>", label_style),
            cell_val(linkedin),
            Paragraph("<b>GitHub</b>", label_style),
            cell_val(github),
        ],
    ]
    tbl = Table(data, colWidths=[0.95 * inch, 2.35 * inch, 0.95 * inch, 2.35 * inch])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, BRAND_ACCENT),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return tbl


def _on_page(canvas: Any, doc: SimpleDocTemplate) -> None:
    canvas.saveState()
    w, h = letter
    canvas.setStrokeColor(BRAND_ACCENT)
    canvas.setLineWidth(1.1)
    y_rule = h - 0.4 * inch
    canvas.line(0.55 * inch, y_rule, w - 0.55 * inch, y_rule)
    canvas.setFillColor(BRAND_PRIMARY)
    canvas.setFont("Helvetica-Bold", 9.5)
    canvas.drawString(0.55 * inch, h - 0.34 * inch, COMPANY_NAME)
    canvas.setFillColor(BRAND_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 0.55 * inch, h - 0.34 * inch, "Career Intelligence Report")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(BRAND_MUTED)
    pg = canvas.getPageNumber()
    foot = (
        f"{COMPANY_NAME} · {SUPPORT_EMAIL} · Page {pg} · "
        f"{datetime.now(UTC).strftime('%Y-%m-%d UTC')}"
    )
    canvas.drawCentredString(w / 2, 0.36 * inch, foot)
    canvas.restoreState()


def build_analysis_pdf_bytes(
    *,
    analysis_id: str,
    summary_column: str,
    findings_raw: Any,
    scores_raw: Any,
    analysis_version: int,
    model_name: str | None = None,
    candidate_display_name: str | None = None,
    candidate_email: str | None = None,
    candidate_linkedin_url: str | None = None,
    candidate_github_url: str | None = None,
    online_report_url: str | None = None,
) -> bytes:
    findings = _safe_findings_dict(findings_raw)
    scores = _safe_findings_dict(scores_raw) or {}
    nlp = _parse_analysis_output(findings)

    resume_score = int(scores.get("resume_score", 0) or 0)
    if nlp is not None:
        resume_score = nlp.resume_score

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.92 * inch,
        bottomMargin=0.62 * inch,
        title=f"{COMPANY_NAME} — Career Report",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="MC_Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=BRAND_DARK,
        spaceAfter=2,
        leading=22,
    )
    tag_style = ParagraphStyle(
        name="MC_Tag",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        textColor=BRAND_MUTED,
        spaceAfter=10,
        leading=11,
    )
    h2_style = ParagraphStyle(
        name="MC_H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        textColor=BRAND_PRIMARY,
        spaceBefore=8,
        spaceAfter=4,
        leading=13,
    )
    body_style = ParagraphStyle(
        name="MC_Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        textColor=BRAND_DARK,
        alignment=TA_JUSTIFY,
        leading=11.5,
        spaceAfter=4,
    )
    bullet_wrap = ParagraphStyle(
        name="MC_Bullet",
        parent=body_style,
        leftIndent=10,
        bulletIndent=4,
        alignment=TA_LEFT,
        fontSize=8.5,
        leading=11,
    )
    label_cell = ParagraphStyle(
        name="MC_LabelCell",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=BRAND_DARK,
    )
    value_cell = ParagraphStyle(
        name="MC_ValueCell",
        parent=body_style,
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
    )
    caption_small = ParagraphStyle(
        name="MC_Caption",
        parent=tag_style,
        fontSize=7.5,
        textColor=BRAND_MUTED,
        alignment=TA_CENTER,
    )

    story: list = []

    story.append(_p(COMPANY_NAME, title_style))
    story.append(_p("Career Intelligence Report", tag_style))
    story.append(
        _p(
            f"{escape(COMPANY_NAME)} · {escape(SUPPORT_EMAIL)} · {escape(CONFIDENTIAL_TAGLINE)}",
            tag_style,
        )
    )
    story.append(Spacer(1, 0.08 * inch))

    story.append(
        _candidate_table(
            candidate_display_name,
            candidate_email,
            candidate_linkedin_url,
            candidate_github_url,
            label_cell,
            value_cell,
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    # Score row + optional QR (same row to save vertical space)
    ats_score = 0
    if nlp:
        ats_score = nlp.ats_compatibility.score
    else:
        ats_score = int(scores.get("ats_score", 0) or 0)

    score_cell_left = _p(
        f"<b>Resume score</b><br/><font size='20' color='#0369a1'><b>{resume_score}</b></font>"
        "<font size='9'>/100</font>",
        body_style,
    )
    score_cell_right = _p(
        f"<b>ATS compatibility</b><br/><font size='20' color='#0369a1'><b>{ats_score}</b></font>"
        "<font size='9'>/100</font>",
        body_style,
    )
    qr_bits = _qr_block(online_report_url, caption_small)
    if qr_bits:
        qr_cell = KeepTogether(qr_bits)
        qr_tbl = Table(
            [[score_cell_left, score_cell_right, qr_cell]],
            colWidths=[2.35 * inch, 2.35 * inch, 1.55 * inch],
        )
        qr_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (1, -1), BRAND_PANEL),
                    ("BOX", (0, 0), (1, -1), 0.5, BRAND_ACCENT),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (1, -1), 12),
                    ("TOPPADDING", (0, 0), (1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (1, -1), 10),
                    ("ALIGN", (2, 0), (2, -1), "CENTER"),
                    ("VALIGN", (2, 0), (2, -1), "MIDDLE"),
                ]
            )
        )
        story.append(qr_tbl)
    else:
        score_table = Table([[score_cell_left, score_cell_right]], colWidths=[3.05 * inch, 3.05 * inch])
        score_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), BRAND_PANEL),
                    ("BOX", (0, 0), (-1, -1), 0.5, BRAND_ACCENT),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.append(score_table)

    story.append(Spacer(1, 0.1 * inch))

    meta_line = (
        f"Analysis ID: {analysis_id[:8]}… · Version {analysis_version}"
        + (f" · Model {escape(model_name)}" if model_name else "")
    )
    story.append(_p(meta_line, tag_style))

    # Summary
    story.append(_p("Summary", h2_style))
    summary_text = (
        nlp.professional_summary.strip()
        if nlp
        else (summary_column or "").strip()
    )
    if summary_text:
        story.append(_p(summary_text[:_SUMMARY_MAX], body_style))
    else:
        story.append(_p("No summary available for this analysis record.", body_style))

    # Skills
    story.append(_p("Skills analysis", h2_style))
    if nlp:
        sa = nlp.skills_assessment
        tech = ", ".join(sa.technical_skills[:_SKILLS_TECH_MAX]) or "—"
        soft = ", ".join(sa.soft_skills[:14]) or "—"
        story.append(_p(f"<b>Technical:</b> {escape(tech)}", body_style))
        story.append(_p(f"<b>Soft skills:</b> {escape(soft)}", body_style))
        if sa.proficiency_notes:
            story.append(_p(sa.proficiency_notes[:_PROF_MAX], body_style))
    else:
        story.append(
            _p("Structured skills assessment not available; re-run resume analysis.", body_style)
        )

    # ATS
    story.append(_p("ATS compatibility", h2_style))
    if nlp:
        ac = nlp.ats_compatibility
        if ac.formatting_notes:
            story.append(_p(ac.formatting_notes[:_ATS_NOTES_MAX], body_style))
        story.extend(_bullets(ac.suggestions, bullet_wrap, _ATS_BULLETS))
    else:
        story.append(_p("—", body_style))

    # Career
    story.append(_p("Career recommendations", h2_style))
    if nlp:
        story.extend(_bullets(nlp.recommended_roles, bullet_wrap, _CAREER_ROLES))
        if nlp.career_outlook:
            story.append(_p("<b>Outlook (5–10 years)</b>", body_style))
            story.append(_p(nlp.career_outlook[:_OUTLOOK_MAX], body_style))
        if nlp.improvement_suggestions:
            story.append(_p("<b>Resume improvements</b>", body_style))
            story.extend(_bullets(nlp.improvement_suggestions, bullet_wrap, _IMPROVE_BULLETS))
    else:
        story.append(_p("—", body_style))

    # Skill gaps (never left as a bare dash when NLP exists)
    story.append(_p("Skill gap analysis", h2_style))
    story.extend(_skill_gap_flowables(nlp, bullet_wrap, body_style))

    # Learning roadmap
    story.append(_p("Learning roadmap", h2_style))
    if nlp and nlp.course_recommendations:
        for c in nlp.course_recommendations[:_COURSES]:
            prov = f" — {c.provider}" if c.provider else ""
            line = (
                f"<b>{escape(c.title)}</b>{escape(prov)}<br/>"
                f"<i>{escape(c.rationale[:200])}</i>"
            )
            story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 3))
    else:
        story.append(_p("—", body_style))

    if nlp and (nlp.strengths or nlp.weaknesses):
        story.append(_p("Strengths & focus areas", h2_style))
        if nlp.strengths:
            story.append(_p("<b>Strengths</b>", body_style))
            story.extend(_bullets(nlp.strengths, bullet_wrap, _SW_QUICK))
        if nlp.weaknesses:
            story.append(_p("<b>Areas to strengthen</b>", body_style))
            story.extend(_bullets(nlp.weaknesses, bullet_wrap, _SW_QUICK))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    pdf = buf.getvalue()
    buf.close()
    return pdf
