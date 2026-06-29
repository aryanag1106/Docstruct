"""
The single entry point both `cli.py` and `app_streamlit.py` call. Keeping this one
function as the only public surface means the interfaces never need to know about
Tesseract, PyMuPDF, or llama.cpp directly — matching the frozen-interfaces approach
in docs/work-division.md.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from . import llm_extract, ocr, validate
from .schemas import DocType

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


def process_document(
    path: str | Path,
    doc_type: DocType | str = "generic_form",
    backend: str = "mock",
    lang: str = "eng",
    preprocess_images: bool = True,
    **backend_kwargs: Any,
) -> dict[str, Any]:
    """
    Run the full pipeline on one file. Returns a JSON-serializable dict:
    {doc_type, doc_type_auto_detected, data, status, field_flags, ocr_source,
    ocr_confidence, processing_seconds}.

    Pass doc_type="auto" to heuristically detect the type instead of choosing one
    (see llm_extract.classify_doc_type — keyword-based, not a model call, so it's
    free on top of whatever the real extraction backend costs).

    Set `backend="llm"` (pass model_path=... or rely on $DOCSTRUCT_MODEL_PATH) once a
    model is downloaded, or `backend="ollama"` (pass model=..., ollama_url=... or rely
    on the matching env vars) for a local Ollama server; `backend="mock"` (default)
    needs no model and is what CI/tests run against. Extra `backend_kwargs` are
    forwarded straight to `llm_extract.extract()`.
    """
    start = time.monotonic()
    path = Path(path)
    input_path = path

    if preprocess_images and path.suffix.lower() in IMAGE_SUFFIXES:
        from . import preprocess as preprocess_mod

        input_path = preprocess_mod.preprocess(path)

    ocr_result = ocr.extract_text(input_path, lang=lang)

    auto_detected = doc_type == "auto"
    resolved_doc_type: DocType = llm_extract.classify_doc_type(ocr_result.text) if auto_detected else doc_type  # type: ignore[assignment]

    raw = llm_extract.extract(resolved_doc_type, ocr_result.text, backend=backend, **backend_kwargs)
    validated = validate.validate(resolved_doc_type, raw, ocr_result=ocr_result)
    result = validated.to_json_dict()
    result["doc_type_auto_detected"] = auto_detected
    result["processing_seconds"] = round(time.monotonic() - start, 1)
    return result
