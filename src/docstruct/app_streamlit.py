"""
Streamlit UI for DocStruct.

Run:  streamlit run src/docstruct/app_streamlit.py

This file imports only from the `docstruct` package + Streamlit — no network calls,
no CDN-hosted JS/CSS, so it keeps working with Wi-Fi off exactly like the CLI.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from docstruct.pipeline import process_document

st.set_page_config(page_title="DocStruct — offline document → JSON", page_icon="📄")
st.title("📄 DocStruct")
st.caption("Offline, CPU-only document → structured JSON extractor. Works with Wi-Fi off.")

doc_type = st.selectbox("Document type", ["receipt", "resume", "generic_form"])
backend = st.radio(
    "Extraction backend",
    ["mock", "llm"],
    horizontal=True,
    help="'mock' is a fast heuristic extractor that needs no model download. "
    "'llm' uses the real llama.cpp pipeline — set DOCSTRUCT_MODEL_PATH first.",
)
uploaded = st.file_uploader("Upload a PDF or image", type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp"])

if uploaded is not None:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    result: dict | None
    with st.spinner("Running the offline pipeline..."):
        try:
            result = process_document(tmp_path, doc_type=doc_type, backend=backend)  # type: ignore[arg-type]
        except Exception as exc:  # surfaced to the user, not swallowed
            st.error(f"Extraction failed: {exc}")
            result = None

    if result is not None:
        if result["status"] == "ok":
            st.success("Extracted cleanly — no fields flagged.")
        else:
            st.warning(f"Needs review: {result['field_flags']}")

        st.json(result["data"])

        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name=f"{Path(uploaded.name).stem}_structured.json",
            mime="application/json",
        )

        with st.expander("Full result (incl. OCR diagnostics)"):
            st.json(result)
