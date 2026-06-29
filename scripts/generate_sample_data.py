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


FONT_CANDIDATES = [
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    # Windows
    "C:\\Windows\\Fonts\\consola.ttf",
    "C:\\Windows\\Fonts\\arial.ttf",
    # macOS
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _load_font(size: int = 16) -> ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    # No system font found at any candidate path. PIL's classic load_default() is a
    # tiny, low-res bitmap font that Tesseract OCRs unreliably — Pillow >=10.1 lets
    # you request it at a larger, scalable size instead, which OCRs far better.


INVOICE_TEXT = """INVOICE

Invoice Number: INV-2049
Invoice Date: 10/06/2026
Due Date: 24/06/2026

Vendor: Bluewave Office Supplies
Customer: Riya Sharma

Items:
Printer paper (5 reams)      1250.00
Ink cartridges (2)            980.00

Subtotal:                    2230.00
Tax:                          111.50
Total:                        2341.50

Payment due within 14 days.
"""


def make_invoice_text_file(out_path: Path) -> None:
    """A plain .txt invoice — exercises the no-OCR-needed plain_text path in ocr.py."""
    out_path.write_text(INVOICE_TEXT, encoding="utf-8")


def make_receipt_image(path: Path) -> None:
    img = Image.new("RGB", (1000, 840), color="white")
    draw = ImageDraw.Draw(img)
    font = _load_font(32)
    y = 20
    for line in RECEIPT_LINES:
        draw.text((40, y), line, fill="black", font=font)
        y += 52
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
    make_invoice_text_file(OUT_DIR / "invoice.txt")
    print(f"Generated sample data in {OUT_DIR}")


if __name__ == "__main__":
    main()
