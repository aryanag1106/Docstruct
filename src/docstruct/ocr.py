"""
Text extraction for PDFs and images.

Strategy:
- Text-layer PDF (already has selectable text)   -> read it directly via PyMuPDF (fitz). No OCR needed,
  no LLM hallucination risk introduced by an unnecessary OCR pass.
- Scanned/image-only PDF, or a plain image file   -> rasterize/open the page(s) and run Tesseract OCR,
  returning per-word confidence so downstream validation can flag low-confidence text.

This is the one module in the pipeline that talks to Tesseract/PyMuPDF directly — everything else
consumes its `OcrResult` output, never raw bytes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# If Tesseract isn't on PATH (a common Windows headache), set TESSERACT_CMD to its
# full .exe path instead of fighting PATH/environment-variable propagation:
#   $env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
_tesseract_cmd = os.environ.get("TESSERACT_CMD")
if _tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd

MIN_EMBEDDED_TEXT_CHARS = 20  # below this, a "text" PDF page is treated as scanned


@dataclass
class OcrResult:
    text: str
    source: str  # "pdf_text" | "pdf_ocr" | "image_ocr"
    mean_confidence: float | None  # None when source == "pdf_text" (no OCR confidence to report)
    per_word_confidence: list[float] = field(default_factory=list)


def _ocr_image(img: Image.Image, lang: str = "eng") -> OcrResult:
    data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

    # Reconstruct line breaks from Tesseract's (block, paragraph, line) grouping instead
    # of joining every detected word with a single space — without this, the page's
    # actual layout is lost and every downstream heuristic that reasons about "lines"
    # (mock extraction, merchant-name-as-first-line, etc.) silently breaks.
    lines: dict[tuple[int, int, int], list[str]] = {}
    confidences: list[float] = []
    n = len(data["text"])
    for i in range(n):
        word = data["text"][i].strip()
        if not word:
            continue
        conf = float(data["conf"][i])
        if conf >= 0:
            confidences.append(conf)
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(word)

    text = "\n".join(" ".join(words) for words in lines.values())
    mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return OcrResult(
        text=text, source="image_ocr", mean_confidence=mean_conf, per_word_confidence=confidences
    )


def extract_text(path: str | Path, lang: str = "eng") -> OcrResult:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return OcrResult(
            text=path.read_text(encoding="utf-8", errors="replace"), source="plain_text", mean_confidence=None
        )

    if suffix == ".pdf":
        doc = fitz.open(path)
        embedded_text = "\n".join(page.get_text() for page in doc)  # type: ignore[attr-defined]
        if len(embedded_text.strip()) >= MIN_EMBEDDED_TEXT_CHARS:
            return OcrResult(text=embedded_text.strip(), source="pdf_text", mean_confidence=None)

        # Scanned PDF: rasterize each page and OCR it.
        all_text: list[str] = []
        all_conf: list[float] = []
        for page in doc:  # type: ignore[attr-defined]
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            result = _ocr_image(img, lang=lang)
            all_text.append(result.text)
            all_conf.extend(result.per_word_confidence)
        mean_conf = sum(all_conf) / len(all_conf) if all_conf else 0.0
        return OcrResult(
            text="\n".join(all_text),
            source="pdf_ocr",
            mean_confidence=mean_conf,
            per_word_confidence=all_conf,
        )

    # Plain image (jpg/png/etc.)
    img = Image.open(path)
    return _ocr_image(img, lang=lang)
