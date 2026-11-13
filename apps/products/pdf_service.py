import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from apps.products.ai_service import MarketIntelligenceAIService


class ProductReportPDFService:
    """
    Topic 48: Automated Executive PDF Report Generator
    Combines Product Metadata, Historical Price Drop Tables,
    and Google Gemini AI Market Intelligence into a professional PDF.
    """

    @classmethod
    def generate_pdf(cls, product) -> io.BytesIO:
        # ১. ফাইলের জন্য মেমোরি বাফার (RAM) তৈরি
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        elements = []

        # ২. কাস্টম টাইপোগ্রাফি স্টাইলস
        header_title_style = ParagraphStyle(
            "HeaderTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "SubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748B"),
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1E3A8A"),
            fontName="Helvetica-Bold",
            spaceAfter=6,
        )
        body_text = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )
        verdict_style = ParagraphStyle(
            "Verdict",
            parent=styles["Normal"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#065F46"),
            fontName="Helvetica-Bold",
        )

        # ৩. হেডার ও ব্র্যান্ডিং সেকশন
        elements.append(Paragraph("MarketPulse AI", header_title_style))
        elements.append(Paragraph("Executive Market Intelligence & Price History Report", subtitle_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B, %Y at %I:%M %p')}", subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=15))

        # ৪. প্রোডাক্ট বিবরণী টেবিল
        product_info_data = [
            [Paragraph("<b>Product Title:</b>", body_text), Paragraph(product.title, body_text)],
            [Paragraph("<b>Marketplace / Store:</b>", body_text), Paragraph(product.store_name, body_text)],
            [Paragraph("<b>Current Live Price:</b>", body_text), Paragraph(f"<b>{product.current_price} {product.currency}</b>", body_text)],
            [Paragraph("<b>Target Price:</b>", body_text), Paragraph(f"{product.target_price or 'None'} {product.currency}", body_text)],
            [Paragraph("<b>Stock Status:</b>", body_text), Paragraph(product.stock_status, body_text)],
        ]
        info_table = Table(product_info_data, colWidths=[130, 410])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 15))

        # ৫. ঐতিহাসিক দামের রেকর্ড টেবিল
        elements.append(Paragraph("Historical Price Fluctuation Log", section_heading))
        history_qs = product.price_history.all().order_by("-recorded_at")[:6]
        
        if history_qs.exists():
            history_data = [["Recorded Date", "Recorded Price", "Currency"]]
            for h in history_qs:
                history_data.append([
                    h.recorded_at.strftime("%Y-%m-%d %H:%M"),
                    f"{h.price:.2f}",
                    h.currency,
                ])
            history_table = Table(history_data, colWidths=[200, 200, 140])
            history_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(history_table)
        else:
            elements.append(Paragraph("<i>No historical price drop logs available yet.</i>", body_text))

        elements.append(Spacer(1, 15))

        # ৬. Google Gemini AI Market Intelligence সেকশন
        elements.append(Paragraph("Google Gemini AI Market Intelligence & Verdict", section_heading))
        ai_res = MarketIntelligenceAIService.generate_product_insights(product)

        if ai_res.get("success"):
            ai_data = ai_res.get("data", {})
            verdict = ai_data.get("price_verdict", "FAIR_PRICE")
            sentiment = ai_data.get("sentiment_score", "N/A")
            summary = ai_data.get("summary", "")
            reason = ai_data.get("verdict_reason", "")
            pros = ai_data.get("pros", [])
            cons = ai_data.get("cons", [])

            ai_summary_data = [
                [Paragraph(f"<b>Smart AI Verdict:</b> <font color='#059669'>{verdict}</font> | <b>Market Sentiment:</b> {sentiment}/100", verdict_style)],
                [Paragraph(f"<b>Executive Summary:</b> {summary}", body_text)],
                [Paragraph(f"<b>Verdict Rationale:</b> {reason}", body_text)],
            ]
            if pros:
                ai_summary_data.append([Paragraph(f"<b>Key Pros:</b> {', '.join(pros)}", body_text)])
            if cons:
                ai_summary_data.append([Paragraph(f"<b>Key Cons:</b> {', '.join(cons)}", body_text)])

            ai_table = Table(ai_summary_data, colWidths=[540])
            ai_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ECFDF5")),
                ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#10B981")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#A7F3D0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(ai_table)
        else:
            elements.append(Paragraph("<i>AI Market Intelligence currently offline.</i>", body_text))

        # ৭. ফুটার
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=5))
        elements.append(Paragraph("Confidential — Generated automatically by MarketPulse AI Competitor Intelligence Engine", subtitle_style))

        # ৮. মেমোরিতে বিল্ড করে বাফার রিটার্ন
        doc.build(elements)
        buffer.seek(0)
        return buffer