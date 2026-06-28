"""
Generates synthetic sample documents into sample_data/ — fully invented text, no
real person's data, used by tests and the live demo.

Run:  python scripts/generate_sample_data.py
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent.parent / "sample_data"

RECEIPT_LINES = [
    "SUNRISE GENERAL STORE",
    "123 MG Road, Springfield",
    "Date: 15/03/2026",
    "",
    "Rice 5kg            450.00",
    "Cooking Oil 1L       180.00",
    "Soap x3               90.00",
    "",
    "Subtotal:            720.00",
    "Tax:                  36.00",
    "Total:               756.00",
    "",
    "Thank you for shopping!",
]

RESUME_TEXT = """Asha Verma
asha.verma@example.invalid
+91 98765 43210

Skills: Python, SQL, Data Analysis, Project Management

Experience:
Data Analyst, Northwind Analytics, 2022-2024
Junior Developer, Contoso Software, 2020-2022

Education:
B.Tech Computer Science, Springfield Institute of Technology, 2020
"""


def make_receipt_image(path: Path) -> None:
    img = Image.new("RGB", (500, 420), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    y = 10
    for line in RECEIPT_LINES:
        draw.text((20, y), line, fill="black", font=font)
        y += 26
    img.save(path)


def make_receipt_scanned_pdf(receipt_image_path: Path, out_path: Path) -> None:
    """An image-only PDF (no text layer) — exercises the pdf_ocr branch of ocr.py."""
    doc = fitz.open()
    img = Image.open(receipt_image_path)
    page = doc.new_page(width=img.width, height=img.height)
    page.insert_image(page.rect, filename=str(receipt_image_path))
    doc.save(out_path)


def make_resume_text_pdf(out_path: Path) -> None:
    """A normal text-layer PDF — exercises the pdf_text branch of ocr.py (no OCR needed)."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), RESUME_TEXT, fontsize=11)
    doc.save(out_path)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    receipt_png = OUT_DIR / "receipt.png"
    make_receipt_image(receipt_png)
    make_receipt_scanned_pdf(receipt_png, OUT_DIR / "receipt_scanned.pdf")
    make_resume_text_pdf(OUT_DIR / "resume.pdf")
    print(f"Generated sample data in {OUT_DIR}")


if __name__ == "__main__":
    main()
