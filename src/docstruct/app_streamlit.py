"""
Streamlit UI for DocStruct — Dashboard / Upload & Process / History / Settings / About,
all calling the same `docstruct.pipeline.process_document()` function the CLI uses.

Run:  streamlit run src/docstruct/app_streamlit.py

No CDN calls, no browser storage. All state lives in `st.session_state` for the life
of the running process — there is deliberately no database in this MVP (see "History"
below); that keeps the offline story simple and honest about what persists.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from docstruct.pipeline import process_document
from docstruct.runtime_status import check_backend
from docstruct.validate import validate as validate_record

st.set_page_config(page_title="DocStruct", page_icon="📄", layout="wide")

# ---------------------------------------------------------------------------
# Styling — dark + amber, matching the project's reference design. Streamlit's own
# theme (.streamlit/config.toml) sets the base colors; this layer adds the pieces
# Streamlit has no native widget for: brand lockup, status pills, result cards.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { font-family: -apple-system, "Segoe UI", Inter, sans-serif; }
    .mono { font-family: ui-monospace, "Cascadia Code", "SF Mono", Consolas, monospace; }

    .brand-row { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 1.2rem; }
    .brand-logo {
        width: 38px; height: 38px; border-radius: 8px; background: #F0A93B; color: #1A1304;
        display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem;
    }
    .brand-name { font-weight: 700; font-size: 1.05rem; color: #E7E8EA; line-height: 1.1; }
    .brand-tag { font-size: 0.65rem; letter-spacing: 0.06em; color: #8B8D98; text-transform: uppercase; }

    .runtime-label, .section-label {
        font-size: 0.7rem; letter-spacing: 0.06em; color: #8B8D98; text-transform: uppercase; margin-bottom: 0.35rem;
    }
    .runtime-box {
        border: 1px solid #262830; border-radius: 8px; padding: 0.55rem 0.7rem; font-size: 0.82rem;
        background: #15171C; color: #C9CAD1; line-height: 1.35;
    }
    .dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 0.4rem; }
    .dot-ok { background: #3ECF8E; } .dot-warn { background: #E8B339; }
    .dot-error { background: #F36B6B; } .dot-info { background: #8B8D98; }
    .runtime-ok { border-color: #1E4A38; } .runtime-warn { border-color: #4A3D1E; } .runtime-error { border-color: #4A2224; }

    .mode-badges { display: flex; gap: 0.4rem; flex-wrap: wrap; }
    .mode-badge {
        font-family: ui-monospace, "Cascadia Code", "SF Mono", Consolas, monospace;
        font-size: 0.72rem; padding: 0.25rem 0.55rem; border-radius: 999px;
        background: #15171C; border: 1px solid #262830; color: #C9CAD1;
    }

    .badge { padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; white-space: nowrap; }
    .badge-ok { background: #102B20; color: #3ECF8E; }
    .badge-warn { background: #2B2210; color: #E8B339; }
    .badge-error { background: #2B1416; color: #F36B6B; }
    .badge-info { background: #1B1C22; color: #9A9CA6; }
    .doc-type-chip { background: #2A2014; color: #E0A857; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }

    .result-card { border: 1px solid #262830; border-radius: 10px; padding: 1rem 1.1rem; margin-bottom: 0.9rem; background: #121317; }
    .result-card-row { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; margin-top: 0.4rem; }
    .result-filename { font-weight: 600; font-size: 0.95rem; color: #E7E8EA; }
    .result-meta { font-size: 0.78rem; color: #8B8D98; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "settings" not in st.session_state:
    st.session_state.settings = {
        "backend": "mock",
        "model_path": os.environ.get("DOCSTRUCT_MODEL_PATH", ""),
        "ollama_url": os.environ.get("DOCSTRUCT_OLLAMA_URL", "http://localhost:11434"),
        "ollama_model": os.environ.get("DOCSTRUCT_OLLAMA_MODEL", "qwen2.5:0.5b"),
        "lang": "eng",
    }

settings = st.session_state.settings

DOC_TYPE_LABELS = {
    "auto": "Auto-detect",
    "receipt": "Receipt",
    "invoice": "Invoice",
    "resume": "Resume",
    "generic_form": "Generic form",
}


def backend_kwargs_for(s: dict[str, str]) -> dict[str, Any]:
    """Only forward the kwargs the chosen backend actually understands."""
    if s["backend"] == "llm":
        return {"model_path": s["model_path"]}
    if s["backend"] == "ollama":
        return {"model": s["ollama_model"], "ollama_url": s["ollama_url"]}
    return {}


def badge_html(label: str, level: str) -> str:
    return f'<span class="badge badge-{level}">{label}</span>'


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
          <div class="brand-logo">DS</div>
          <div>
            <div class="brand-name">DocStruct</div>
            <div class="brand-tag">Offline document intelligence</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "📤 Upload & Process", "🕐 History", "⚙️ Settings", "ℹ️ About"],
        label_visibility="collapsed",
    )

    status = check_backend(settings["backend"], **backend_kwargs_for(settings))
    st.markdown('<div class="runtime-label">Local runtime</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="runtime-box runtime-{status["level"]}">'
        f'<span class="dot dot-{status["level"]}"></span>{status["label"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="runtime-label" style="margin-top:1rem;">Mode</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mode-badges"><span class="mode-badge">⚡ CPU only</span>'
        '<span class="mode-badge">📡 Offline-first</span></div>',
        unsafe_allow_html=True,
    )

page_key = page.split(" ", 1)[1]


# ---------------------------------------------------------------------------
# Shared: result card (View / Edit)
# ---------------------------------------------------------------------------
def render_result_card(item: dict[str, Any], idx: int) -> None:
    result = item["result"]
    if "error" in result:
        st.markdown(
            f'<div class="result-card"><div class="result-filename">{item["filename"]}</div>'
            f'<div class="result-meta">Failed: {result["error"]}</div></div>',
            unsafe_allow_html=True,
        )
        return

    status_level = "ok" if result["status"] == "ok" else "warn"
    status_label = "✓ ok" if result["status"] == "ok" else f"⚠ needs review ({len(result['field_flags'])})"
    conf = result.get("ocr_confidence")
    conf_text = f"{conf:.0f}% OCR confidence" if conf is not None else "no OCR needed"
    auto_tag = " · auto-detected" if result.get("doc_type_auto_detected") else ""

    st.markdown(
        f"""
        <div class="result-card">
          <div class="result-filename">{item["filename"]}</div>
          <div class="result-card-row">
            <span class="doc-type-chip">{DOC_TYPE_LABELS.get(result["doc_type"], result["doc_type"])}{auto_tag}</span>
            {badge_html(status_label, status_level)}
            <span class="result-meta">{conf_text} · {result.get("processing_seconds", "?")}s · {result["ocr_source"]}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    view_tab, edit_tab = st.tabs(["🔍 View", "✏️ Edit"])
    with view_tab:
        if result["field_flags"]:
            st.caption(
                "Flagged fields: " + ", ".join(f"`{k}` — {v}" for k, v in result["field_flags"].items())
            )
        st.json(result["data"])
        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name=f"{Path(item['filename']).stem}_structured.json",
            mime="application/json",
            key=f"dl_{idx}",
        )

    with edit_tab:
        st.caption("Correct any field below, then save — corrections are re-validated against the schema.")
        data = result["data"]
        edited: dict[str, str] = {}
        with st.form(key=f"edit_form_{idx}"):
            for field_name, value in data.items():
                if isinstance(value, (dict, list)):
                    edited[field_name] = st.text_area(
                        field_name,
                        value=json.dumps(value, indent=2),
                        key=f"edit_{idx}_{field_name}",
                        height=100,
                    )
                else:
                    edited[field_name] = st.text_input(
                        field_name, value="" if value is None else str(value), key=f"edit_{idx}_{field_name}"
                    )
            submitted = st.form_submit_button("💾 Save corrections")

        if submitted:
            new_raw: dict[str, Any] = {}
            for field_name, text_value in edited.items():
                original = data[field_name]
                if isinstance(original, (dict, list)):
                    try:
                        new_raw[field_name] = json.loads(text_value) if text_value.strip() else original
                    except json.JSONDecodeError:
                        st.error(f"'{field_name}' isn't valid JSON — that field's edit was discarded.")
                        new_raw[field_name] = original
                elif text_value.strip() == "":
                    new_raw[field_name] = None
                elif isinstance(original, float):
                    try:
                        new_raw[field_name] = float(text_value)
                    except ValueError:
                        new_raw[field_name] = text_value
                else:
                    new_raw[field_name] = text_value

            revalidated = validate_record(result["doc_type"], new_raw, ocr_result=None)
            result["data"] = revalidated.data
            result["status"] = revalidated.status
            result["field_flags"] = revalidated.field_flags
            st.success("Saved and re-validated.")
            st.rerun()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def render_dashboard() -> None:
    st.markdown("## Dashboard")
    history = st.session_state.history
    if not history:
        st.info("Nothing processed yet this session. Go to **Upload & Process** to run your first document.")
        return

    total = len(history)
    ok_count = sum(1 for h in history if h["result"].get("status") == "ok")
    avg_time = sum(h["result"].get("processing_seconds", 0) for h in history) / total
    type_counts: dict[str, int] = {}
    for h in history:
        t = h["result"].get("doc_type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documents processed", total)
    c2.metric("Clean extractions", f"{ok_count}/{total}")
    c3.metric("Avg. processing time", f"{avg_time:.1f}s")
    c4.metric("Most common type", DOC_TYPE_LABELS.get(max(type_counts, key=lambda k: type_counts[k]), "—"))

    st.markdown("##### Documents by type")
    st.bar_chart({DOC_TYPE_LABELS.get(k, k): v for k, v in type_counts.items()})


def render_upload() -> None:
    st.markdown("## Upload & Process")
    st.caption(
        "PDF, scanned PDF, image, or plain text. Receipts, invoices, resumes, and generic "
        "forms — processed entirely on this machine. Nothing leaves it."
    )

    backend_note = f"Backend: **{settings['backend']}**"
    if settings["backend"] == "llm" and settings["model_path"]:
        backend_note += f" ({Path(settings['model_path']).name})"
    elif settings["backend"] == "ollama":
        backend_note += f" ({settings['ollama_model']})"
    st.caption(backend_note + " — change this on the Settings page.")

    doc_type_choice = st.selectbox(
        "Document type", list(DOC_TYPE_LABELS.keys()), format_func=lambda k: DOC_TYPE_LABELS[k], index=0
    )

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "png", "jpg", "jpeg", "bmp", "tiff", "tif", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if st.button("🚀 Process documents", type="primary", disabled=not uploaded_files):
        for f in uploaded_files:
            suffix = Path(f.name).suffix
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(f.read())
                    tmp_path = tmp.name
                with st.spinner(f"Processing {f.name}..."):
                    result = process_document(
                        tmp_path,
                        doc_type=doc_type_choice,
                        backend=settings["backend"],
                        lang=settings["lang"],
                        **backend_kwargs_for(settings),
                    )
            except Exception as exc:  # surfaced in the card, never swallowed
                result = {"error": str(exc)}
            finally:
                if tmp_path:
                    Path(tmp_path).unlink(missing_ok=True)

            st.session_state.history.insert(
                0,
                {
                    "filename": f.name,
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "result": result,
                },
            )
        st.rerun()

    st.markdown(f"### Results ({len(st.session_state.history)})")
    if not st.session_state.history:
        st.info("No documents processed yet. Upload one above and click **Process documents**.")
    for idx, item in enumerate(st.session_state.history):
        render_result_card(item, idx)


def render_history() -> None:
    st.markdown("## History")
    st.caption(
        "This session only — there's no database in this MVP, so history clears when the app restarts."
    )
    history = st.session_state.history
    if not history:
        st.info("Nothing processed yet this session.")
        return

    rows = [
        {
            "Time": h["timestamp"],
            "File": h["filename"],
            "Type": DOC_TYPE_LABELS.get(h["result"].get("doc_type", "—"), "—"),
            "Status": h["result"].get("status", "error"),
            "Seconds": h["result"].get("processing_seconds", "—"),
        }
        for h in history
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    if st.button("🗑️ Clear history"):
        st.session_state.history = []
        st.rerun()


def render_settings() -> None:
    st.markdown("## Settings")

    backend = st.radio(
        "Extraction backend",
        ["mock", "llm", "ollama"],
        index=["mock", "llm", "ollama"].index(settings["backend"]),
        horizontal=True,
        help="'mock' needs no model. 'llm' uses llama-cpp-python + a downloaded GGUF file. "
        "'ollama' uses a local Ollama server — no C++ compiler needed.",
    )

    model_path = settings["model_path"]
    ollama_url = settings["ollama_url"]
    ollama_model = settings["ollama_model"]

    if backend == "llm":
        model_path = st.text_input(
            "GGUF model path", value=model_path, help="e.g. models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
        )
    elif backend == "ollama":
        ollama_url = st.text_input("Ollama server URL", value=ollama_url)
        ollama_model = st.text_input(
            "Ollama model tag", value=ollama_model, help="must already be pulled: `ollama pull <tag>`"
        )

    lang = st.selectbox(
        "Tesseract OCR language(s)",
        ["eng", "eng+tel", "eng+hin", "eng+tel+hin"],
        index=["eng", "eng+tel", "eng+hin", "eng+tel+hin"].index(settings["lang"]),
    )

    if st.button("Save settings", type="primary"):
        st.session_state.settings = {
            "backend": backend,
            "model_path": model_path,
            "ollama_url": ollama_url,
            "ollama_model": ollama_model,
            "lang": lang,
        }
        st.success("Saved.")
        st.rerun()


def render_about() -> None:
    st.markdown("## About DocStruct")
    st.markdown("""
DocStruct turns PDFs, scanned documents, receipts, invoices, resumes, and generic
forms into clean structured JSON — entirely offline, on CPU.

**Pipeline:** text-layer PDFs are read directly (PyMuPDF); scanned PDFs, images, and
photos go through OpenCV preprocessing and Tesseract OCR; a small instruction model
(llama.cpp or Ollama) extracts fields into JSON; every field is validated against a
Pydantic schema and flagged `needs_review` rather than guessed when uncertain.

**Why offline matters:** the core pipeline makes zero network calls — proven by an
automated test (`tests/test_no_network.py`), not just claimed.

**License:** GNU GPL-3.0 — strong copyleft, source must stay open for any
distributed modified version.

See `README.md` and `spec-kit/` in the repository for the full architecture, model
declarations, and specification.
        """)


PAGES = {
    "Dashboard": render_dashboard,
    "Upload & Process": render_upload,
    "History": render_history,
    "Settings": render_settings,
    "About": render_about,
}
PAGES[page_key]()
