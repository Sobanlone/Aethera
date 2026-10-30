from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Dict, List

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


REPORT_FIELDS = [
    ("Report ID", "report_id"),
    ("Category", "category"),
    ("Summary", "summary"),
    ("Description", "description"),
    ("Approximate location", "location"),
    ("Date and time", "incident_time"),
    ("Evidence notes", "evidence"),
    ("Potential impact", "impact"),
    ("Missing information", "missing_info"),
    ("Observed facts", "observed_facts"),
    ("Unverified information", "unverified_info"),
    ("Suggested next steps", "suggested_next_steps"),
]


def report_json(report: Dict[str, Any]) -> bytes:
    return json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")


def report_pdf(report: Dict[str, Any]) -> bytes:
    output = BytesIO()
    document = canvas.Canvas(output, pagesize=letter)
    page_width, page_height = letter
    left_margin = 48
    y = page_height - 54

    document.setTitle(report.get("summary") or "Aethera environmental report")
    document.setFont("Helvetica-Bold", 16)
    document.drawString(left_margin, y, "Aethera Environmental Incident Report")
    y -= 30
    document.setFont("Helvetica", 10)

    for label, key in REPORT_FIELDS:
        value = str(report.get(key) or "Not provided")
        lines = simpleSplit(f"{label}: {value}", "Helvetica", 10, page_width - 2 * left_margin)
        for line in lines:
            if y < 54:
                document.showPage()
                y = page_height - 54
                document.setFont("Helvetica", 10)
            document.drawString(left_margin, y, line)
            y -= 15
        y -= 5

    checklist = report.get("checklist") or []
    if checklist:
        if y < 80:
            document.showPage()
            y = page_height - 54
        document.setFont("Helvetica-Bold", 11)
        document.drawString(left_margin, y, "Documentation checklist")
        y -= 18
        document.setFont("Helvetica", 10)
        for item in checklist:
            if y < 54:
                document.showPage()
                y = page_height - 54
                document.setFont("Helvetica", 10)
            document.drawString(left_margin, y, f"[x] {item}")
            y -= 15

    document.save()
    return output.getvalue()


def report_png(report: Dict[str, Any]) -> bytes:
    width = 1200
    margin = 56
    font = ImageFont.load_default(size=22)
    title_font = ImageFont.load_default(size=32)
    lines: List[tuple[str, Any]] = [
        ("Aethera Environmental Incident Report", title_font),
    ]

    for label, key in REPORT_FIELDS:
        value = str(report.get(key) or "Not provided").replace("\n", " ")
        lines.append((f"{label}: {value}", font))

    checklist = report.get("checklist") or []
    if checklist:
        lines.append(("Documentation checklist: " + ", ".join(checklist), font))

    draw_measure = ImageDraw.Draw(Image.new("RGB", (width, 1), "white"))
    wrapped: List[tuple[str, Any]] = []
    for text, text_font in lines:
        words = text.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and draw_measure.textlength(candidate, font=text_font) > width - 2 * margin:
                wrapped.append((current, text_font))
                current = word
            else:
                current = candidate
        wrapped.append((current, text_font))
        wrapped.append(("", font))

    line_height = 38
    height = max(360, margin * 2 + len(wrapped) * line_height)
    image = Image.new("RGB", (width, height), "#f5f8f5")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, width - 24, height - 24), radius=24, fill="white", outline="#1f6b4f", width=3)
    y = margin
    for text, text_font in wrapped:
        draw.text((margin, y), text, fill="#173b2e", font=text_font)
        y += line_height

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
