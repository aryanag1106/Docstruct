"""
Turns raw OCR/PDF text into a structured dict matching one of `schemas.py`'s models.

Two backends:
  - "mock"  — fast, dependency-free regex/heuristic extraction. Useful for development,
              CI, and demoing the pipeline architecture before the team has downloaded
              model weights. NOT a substitute for the real thing in the final demo.
  - "llm"   — Qwen2.5-1.5B-Instruct (or similar) via llama.cpp, grammar-constrained to
              valid JSON (see gbnf.py), prompted with the target schema.

Select via DocStruct's `--backend` CLI flag or the `backend=` argument here directly.
llama_cpp is imported lazily so the rest of the package works even before it's installed.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from .gbnf import generic_json_grammar
from .schemas import DocType, json_schema_for

DEFAULT_MODEL_ENV = "DOCSTRUCT_MODEL_PATH"

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{8,14}\d)")
MONEY_RE = re.compile(r"(?:rs\.?|inr|₹|\$)?\s?([0-9]{1,3}(?:,[0-9]{3})*\.[0-9]{2})", re.IGNORECASE)
DATE_RE = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")


# ---------------------------------------------------------------------------
# Mock backend — heuristic, offline, no model required
# ---------------------------------------------------------------------------
def _mock_extract_receipt(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    merchant = lines[0] if lines else None
    date_match = DATE_RE.search(text)
    totals = []
    for line in lines:
        if re.search(r"\btotal\b", line, re.IGNORECASE):
            m = MONEY_RE.search(line)
            if m:
                totals.append(float(m.group(1).replace(",", "")))
    return {
        "merchant_name": merchant,
        "date": date_match.group(0) if date_match else None,
        "currency": "INR",
        "line_items": [],
        "subtotal": None,
        "tax_amount": None,
        "total_amount": max(totals) if totals else None,
    }


def _mock_extract_resume(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines else None
    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)

    skills: list[str] = []
    skills_match = re.search(r"skills?\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    if skills_match:
        skills = [s.strip() for s in re.split(r"[,;]", skills_match.group(1)) if s.strip()]

    return {
        "full_name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "skills": skills,
        "experience": [],
        "education": [],
    }


def _mock_extract_generic(text: str) -> dict[str, Any]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if key and val:
                fields[key] = val
    return {"fields": fields}


_MOCK_DISPATCH = {
    "receipt": _mock_extract_receipt,
    "resume": _mock_extract_resume,
    "generic_form": _mock_extract_generic,
}


def mock_extract(doc_type: DocType, text: str) -> dict[str, Any]:
    return _MOCK_DISPATCH[doc_type](text)


# ---------------------------------------------------------------------------
# Real backend — llama.cpp, grammar-constrained
# ---------------------------------------------------------------------------
_PROMPT_TEMPLATE = """You extract structured data from noisy OCR text. Output ONLY a JSON object \
matching this JSON Schema, no prose, no markdown fences:

SCHEMA:
{schema}

OCR TEXT:
\"\"\"
{text}
\"\"\"

JSON:"""


def llm_extract(
    doc_type: DocType, text: str, model_path: str | None = None, max_tokens: int = 512
) -> dict[str, Any]:
    """
    Real extraction via llama.cpp. Requires `pip install llama-cpp-python` and a
    downloaded GGUF model (set DOCSTRUCT_MODEL_PATH or pass model_path explicitly).
    Raises a clear error rather than silently falling back to mock — falling back
    silently would hide exactly the kind of failure this project promises not to hide.
    """
    try:
        from llama_cpp import Llama, LlamaGrammar
    except ImportError as exc:  # pragma: no cover - exercised only without the optional dep
        raise RuntimeError(
            "llama-cpp-python is not installed. Run `pip install llama-cpp-python`, "
            "download a GGUF model (see README setup section), and set DOCSTRUCT_MODEL_PATH, "
            "or pass --backend mock to use the heuristic extractor instead."
        ) from exc

    resolved_model_path = model_path or os.environ.get(DEFAULT_MODEL_ENV)
    if not resolved_model_path:
        raise RuntimeError(f"No model path given. Set ${DEFAULT_MODEL_ENV} or pass model_path=.")

    llm = Llama(model_path=resolved_model_path, n_ctx=4096, verbose=False)
    grammar = LlamaGrammar.from_string(generic_json_grammar())

    schema = json_schema_for(doc_type)
    prompt = _PROMPT_TEMPLATE.format(schema=json.dumps(schema), text=text[:6000])

    output = llm(prompt, max_tokens=max_tokens, grammar=grammar, temperature=0.1)
    raw = output["choices"][0]["text"]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        # The grammar guarantees *some* valid JSON came out; this branch should be
        # unreachable in practice. If it ever triggers, that's a real bug to fix,
        # not something to paper over with a mock fallback.
        raise RuntimeError(f"Model produced grammar-valid-looking but unparseable output: {raw!r}") from exc


def extract(doc_type: DocType, text: str, backend: str = "mock", **kwargs: Any) -> dict[str, Any]:
    if backend == "mock":
        return mock_extract(doc_type, text)
    if backend == "llm":
        return llm_extract(doc_type, text, **kwargs)
    raise ValueError(f"Unknown backend: {backend!r} (expected 'mock' or 'llm')")
