"""
certificate_generator.py
Generates a simple PDF completion certificate using reportlab.
"""

import os
from datetime import date
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "certificates")


def generate_certificate(username, course_title="Coding Fundamentals"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"certificate_{username.replace(' ', '_')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    page_size = landscape(A4)
    c = canvas.Canvas(filepath, pagesize=page_size)
    width, height = page_size

    # Border
    c.setStrokeColor(HexColor("#2c3e50"))
    c.setLineWidth(4)
    c.rect(1 * cm, 1 * cm, width - 2 * cm, height - 2 * cm)

    # Title
    c.setFont("Helvetica-Bold", 34)
    c.setFillColor(HexColor("#2c3e50"))
    c.drawCentredString(width / 2, height - 4 * cm, "Certificate of Completion")

    # Subtitle
    c.setFont("Helvetica", 16)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(width / 2, height - 5.5 * cm, "This certifies that")

    # Name
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(HexColor("#e67e22"))
    c.drawCentredString(width / 2, height - 7 * cm, username)

    # Course info
    c.setFont("Helvetica", 16)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(
        width / 2, height - 8.5 * cm,
        f"has successfully completed the course \"{course_title}\""
    )

    # Date
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 10 * cm, f"Issued on: {date.today().isoformat()}")

    c.save()
    return filepath
