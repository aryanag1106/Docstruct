"""
Validates an extracted dict against its Pydantic schema, layers on a few business
rules, and folds in OCR confidence — producing one `status: ok|needs_review` decision
per record plus a `field_flags` dict explaining *why*, never a silent pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ValidationError

from .ocr import OcrResult
from .schemas import SCHEMA_BY_DOC_TYPE, DocType

OCR_CONFIDENCE_FLAG_THRESHOLD = 60.0  # tesseract confidence is 0-100


@dataclass
class ValidatedRecord:
    doc_type: DocType
    data: dict[str, Any]
    status: str  # "ok" | "needs_review"
    field_flags: dict[str, str] = field(default_factory=dict)
    ocr_source: str | None = None
    ocr_confidence: float | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "doc_type": self.doc_type,
            "data": self.data,
            "status": self.status,
            "field_flags": self.field_flags,
            "ocr_source": self.ocr_source,
            "ocr_confidence": self.ocr_confidence,
        }


def _business_rule_flags(doc_type: DocType, model: BaseModel) -> dict[str, str]:
    flags: dict[str, str] = {}
    if doc_type == "receipt":
        if getattr(model, "total_amount", None) is None:
            flags["total_amount"] = "no total amount found in the text"
        if not getattr(model, "merchant_name", None):
            flags["merchant_name"] = "no merchant name identified"
    elif doc_type == "resume":
        if not getattr(model, "full_name", None):
            flags["full_name"] = "no name identified"
        if not getattr(model, "email", None) and not getattr(model, "phone", None):
            flags["contact"] = "no email or phone number found"
    elif doc_type == "generic_form":
        if not model.fields:  # type: ignore[attr-defined]
            flags["fields"] = "no key:value pairs were extracted"
    return flags


def validate(doc_type: DocType, raw: dict[str, Any], ocr_result: OcrResult | None = None) -> ValidatedRecord:
    schema_cls = SCHEMA_BY_DOC_TYPE[doc_type]
    field_flags: dict[str, str] = {}

    try:
        model = schema_cls.model_validate(raw)
        data = model.model_dump()
    except ValidationError as exc:
        # Schema-level failure: surface every offending field explicitly instead of
        # discarding the record or guessing a "close enough" value.
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "<root>"
            field_flags[loc] = err["msg"]
        data = raw  # keep what we have, flagged, rather than dropping it
        model = None  # type: ignore[assignment]

    if model is not None:
        field_flags.update(_business_rule_flags(doc_type, model))

    ocr_source = ocr_result.source if ocr_result else None
    ocr_confidence = ocr_result.mean_confidence if ocr_result else None
    if ocr_confidence is not None and ocr_confidence < OCR_CONFIDENCE_FLAG_THRESHOLD:
        field_flags["_ocr_quality"] = (
            f"mean OCR confidence {ocr_confidence:.1f} is below threshold; verify by eye"
        )

    status = "ok" if not field_flags else "needs_review"
    return ValidatedRecord(
        doc_type=doc_type,
        data=data,
        status=status,
        field_flags=field_flags,
        ocr_source=ocr_source,
        ocr_confidence=ocr_confidence,
    )
