"""
Pydantic models for the document types DocStruct supports.

These serve two purposes:
1. Runtime validation (`validate.py` imports these directly).
2. JSON-Schema generation (`.model_json_schema()`) — used to document the expected
   output shape and to build prompts for the LLM extraction step.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

DocType = Literal["receipt", "resume", "generic_form"]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[\d\-\+\(\)\s]{7,20}$")


class LineItem(BaseModel):
    name: str
    quantity: float | None = None
    unit_price: float | None = None
    line_total: float | None = None


class ReceiptFields(BaseModel):
    merchant_name: str | None = None
    date: str | None = None  # left as free text; validate.py checks plausibility, doesn't coerce
    currency: str | None = "INR"
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None


class ExperienceEntry(BaseModel):
    title: str | None = None
    company: str | None = None
    duration: str | None = None


class EducationEntry(BaseModel):
    degree: str | None = None
    institution: str | None = None
    year: str | None = None


class ResumeFields(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def _email_shape(cls, v: str | None) -> str | None:
        # Intentionally permissive here: validate.py decides ok/needs_review.
        # This validator only normalizes whitespace, it never rejects.
        return v.strip() if v else v


class GenericFormFields(BaseModel):
    """Catch-all for a form type we don't have a dedicated schema for yet."""

    fields: dict[str, str] = Field(default_factory=dict)


SCHEMA_BY_DOC_TYPE: dict[DocType, type[BaseModel]] = {
    "receipt": ReceiptFields,
    "resume": ResumeFields,
    "generic_form": GenericFormFields,
}


def json_schema_for(doc_type: DocType) -> dict:
    return SCHEMA_BY_DOC_TYPE[doc_type].model_json_schema()
