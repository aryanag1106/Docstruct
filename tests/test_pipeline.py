from pathlib import Path

import pytest

from docstruct.pipeline import process_document

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"


@pytest.fixture(scope="module", autouse=True)
def ensure_sample_data():
    if not (SAMPLE_DIR / "receipt.png").exists():
        from scripts.generate_sample_data import main  # noqa: E402

        main()


def test_receipt_image_ocr_extracts_total_and_merchant():
    result = process_document(SAMPLE_DIR / "receipt.png", doc_type="receipt", backend="mock")
    assert result["data"]["merchant_name"] == "SUNRISE GENERAL STORE"
    assert result["data"]["total_amount"] == 756.0
    assert result["status"] == "ok"
    assert result["ocr_source"] == "image_ocr"


def test_scanned_pdf_uses_ocr_branch():
    result = process_document(SAMPLE_DIR / "receipt_scanned.pdf", doc_type="receipt", backend="mock")
    assert result["ocr_source"] == "pdf_ocr"
    assert result["data"]["total_amount"] == 756.0


def test_text_pdf_skips_ocr_entirely():
    result = process_document(SAMPLE_DIR / "resume.pdf", doc_type="resume", backend="mock")
    assert result["ocr_source"] == "pdf_text"
    assert result["ocr_confidence"] is None  # no OCR ran, so no OCR confidence to report
    assert result["data"]["full_name"] == "Asha Verma"
    assert "skills" in result["data"] and len(result["data"]["skills"]) > 0


def test_invoice_text_file_skips_ocr_and_extracts_fields():
    result = process_document(SAMPLE_DIR / "invoice.txt", doc_type="invoice", backend="mock")
    assert result["ocr_source"] == "plain_text"
    assert result["data"]["invoice_number"] == "INV-2049"
    assert result["data"]["total_amount"] == 2341.5
    assert result["status"] == "ok"


def test_auto_detect_classifies_invoice_correctly():
    result = process_document(SAMPLE_DIR / "invoice.txt", doc_type="auto", backend="mock")
    assert result["doc_type"] == "invoice"
    assert result["doc_type_auto_detected"] is True


def test_auto_detect_classifies_resume_correctly():
    result = process_document(SAMPLE_DIR / "resume.pdf", doc_type="auto", backend="mock")
    assert result["doc_type"] == "resume"


def test_processing_seconds_is_reported():
    result = process_document(SAMPLE_DIR / "receipt.png", doc_type="receipt", backend="mock")
    assert isinstance(result["processing_seconds"], float)
    assert result["processing_seconds"] >= 0


def test_wrong_doc_type_is_flagged_needs_review_not_fabricated():
    """A resume run through the receipt schema should never produce a plausible-looking
    total — it should come back flagged, which is the whole point of validate.py."""
    result = process_document(SAMPLE_DIR / "resume.pdf", doc_type="receipt", backend="mock")
    assert result["status"] == "needs_review"
    assert "total_amount" in result["field_flags"]
    assert result["data"]["total_amount"] is None
