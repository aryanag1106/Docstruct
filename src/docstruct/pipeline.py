"""
The single entry point both `cli.py` and `app_streamlit.py` call. Keeping this one
function as the only public surface means the interfaces never need to know about
Tesseract, PyMuPDF, or llama.cpp directly — matching the frozen-interfaces approach
in docs/work-division.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import llm_extract, ocr, validate
from .schemas import DocType

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


def process_document(
    path: str | Path,
    doc_type: DocType,
    backend: str = "mock",
    lang: str = "eng",
    preprocess_images: bool = True,
) -> dict[str, Any]:
    """
    Run the full pipeline on one file. Returns a JSON-serializable dict:
    {doc_type, data, status, field_flags, ocr_source, ocr_confidence}.

    Set `backend="llm"` once a model is downloaded and DOCSTRUCT_MODEL_PATH is set;
    `backend="mock"` (default) needs no model and is what CI/tests run against.
    """
    path = Path(path)
    input_path = path

    if preprocess_images and path.suffix.lower() in IMAGE_SUFFIXES:
        from . import preprocess as preprocess_mod

        input_path = preprocess_mod.preprocess(path)

    ocr_result = ocr.extract_text(input_path, lang=lang)
    raw = llm_extract.extract(doc_type, ocr_result.text, backend=backend)
    validated = validate.validate(doc_type, raw, ocr_result=ocr_result)
    return validated.to_json_dict()
