import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def _add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))
    page_num = canvas.getPageNumber()
    canvas.drawRightString(letter[0] - 36, 20, f"TaxPilot AI Statutory Audit Dossier — Page {page_num}")
    canvas.restoreState()


class PDFReportService:
    """Enterprise PDF Report Generation Service for GST Investigation Packages."""

    @staticmethod
    def generate_investigation_pdf(
        investigation_title: str,
        client_name: str,
        client_gstin: str,
        tax_period: str,
        mismatch_amount: float,
        notice_data: Dict[str, Any],
        verified_findings: List[Dict[str, Any]],
        response_draft: Dict[str, Any],
        suspect_invoices: Optional[List[Dict[str, Any]]] = None,
        verification_verdict: str = "VERIFIED",
        approver_name: str = "Statutory GST Auditor",
        approval_notes: str = "",
        approved_at: Optional[str] = None,
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#173B67")
        secondary_color = colors.HexColor("#2563A6")

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=primary_color,
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=10
        )
        heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=15,
            textColor=secondary_color,
            spaceBefore=10,
            spaceAfter=5
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#172B4D")
        )

        elements = []
        date_str = approved_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        notice_no = notice_data.get("notice_number") or "N/A"
        notice_type = notice_data.get("notice_type") or "DRC-01A"
        itc_claimed = float(notice_data.get("itc_claimed") or 0.0)
        itc_available = float(notice_data.get("itc_available") or 0.0)
        deadline = str(notice_data.get("response_deadline") or "N/A")

        # Header
        elements.append(Paragraph("TAXPILOT AI — FINAL GST AUDIT INVESTIGATION REPORT", title_style))
        elements.append(Paragraph(f"Case: {investigation_title}", subtitle_style))
        elements.append(Paragraph(f"Client: {client_name} ({client_gstin}) | Tax Period: {tax_period} | Approved: {date_str}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=10))

        # 1. Notice Summary Table
        elements.append(Paragraph("1. GST Notice & Discrepancy Overview", heading_style))
        summary_data = [
            ["Notice Number:", str(notice_no), "Notice Form:", str(notice_type)],
            ["Taxpayer GSTIN:", str(client_gstin), "Tax Period:", str(tax_period)],
            ["ITC Claimed (3B):", f"INR {itc_claimed:,.2f}", "ITC Available (2B):", f"INR {itc_available:,.2f}"],
            ["Alleged Excess ITC:", f"INR {mismatch_amount:,.2f}", "Response Deadline:", deadline]
        ]
        t1 = Table(summary_data, colWidths=[115, 155, 115, 155])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F5F7FA")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#172B4D")),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 10))

        # 2. Financial & Invoice Reconciliation
        elements.append(Paragraph("2. Invoice-Level Financial Reconciliation", heading_style))
        invoices = suspect_invoices or response_draft.get("annexure_invoices") or []
        if invoices:
            inv_rows = [["Invoice No.", "Supplier", "Supplier GSTIN", "Tax Amount", "Status"]]
            for inv in invoices:
                inv_rows.append([
                    str(inv.get("invoice_number", "N/A")),
                    str(inv.get("supplier_name", "N/A"))[:28],
                    str(inv.get("supplier_gstin", "N/A")),
                    f"INR {float(inv.get('tax_amount') or inv.get('total_tax') or 0.0):,.2f}",
                    str(inv.get("reconciliation_status", "RECONCILED"))
                ])
            t_inv = Table(inv_rows, colWidths=[95, 145, 115, 95, 90])
            t_inv.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]))
            elements.append(t_inv)
        else:
            elements.append(Paragraph(f"Reconciliation Summary: {response_draft.get('reconciliation_table', 'No invoice-level records available.')}", body_style))
        elements.append(Spacer(1, 10))

        # 3. Verified Findings & Verification Gate
        elements.append(Paragraph(f"3. Root-Cause Findings & Verification Gate ({verification_verdict})", heading_style))
        if verified_findings:
            findings_data = [["Root Cause", "Finding Title", "Evidence References", "Status"]]
            for f in verified_findings:
                findings_data.append([
                    str(f.get("finding_type", "FINDING")),
                    str(f.get("title", "Verified Finding"))[:42],
                    ", ".join(str(e) for e in f.get("evidence_ids", [])) or "N/A",
                    "SUPPORTED"
                ])
            t2 = Table(findings_data, colWidths=[110, 190, 160, 80])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]))
            elements.append(t2)
        else:
            elements.append(Paragraph("No independently verified findings recorded; see Auditor-approved submission below.", body_style))
        elements.append(Spacer(1, 10))

        # 4. Auditor-Approved Response Submission
        elements.append(Paragraph("4. Auditor-Approved Response Submission", heading_style))
        draft_title = response_draft.get("title") or "FORMAL REPLY TO GST NOTICE"
        exec_sum = (response_draft.get("executive_summary") or "").replace("\n", "<br/>")
        legal_text = (response_draft.get("legal_grounds") or response_draft.get("legal_submissions") or "").replace("\n", "<br/>")
        prayer_text = (response_draft.get("prayer") or "").replace("\n", "<br/>")

        elements.append(Paragraph(f"<b>Document Title:</b> {draft_title}", body_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"<b>Executive Summary:</b> {exec_sum}", body_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<b>Statutory Legal Grounds:</b><br/>{legal_text}", body_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<b>Prayer:</b> {prayer_text}", body_style))
        elements.append(Spacer(1, 12))

        # 5. Sign-off box
        elements.append(Paragraph("5. Auditor Sign-Off & Attestation", heading_style))
        sign_data = [
            ["Prepared by:", "TaxPilot AI Multi-Agent System", "Approved by:", str(approver_name)],
            ["Approval Date:", str(date_str), "Final Status:", "APPROVED FOR SUBMISSION"],
            ["Auditor Notes:", str(approval_notes or "Verified and approved by Auditor.")[:95], "", ""]
        ]
        t3 = Table(sign_data, colWidths=[100, 170, 100, 170])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F5F7FA")),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('SPAN', (1, 2), (3, 2)),
        ]))
        elements.append(t3)

        doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
        buffer.seek(0)
        return buffer.getvalue()


pdf_service = PDFReportService()
