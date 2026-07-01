# Tasks: Document Extraction Pipeline

## Phase 1 — Core pipeline
- [x] #1 schemas.py — Pydantic models for receipt/invoice/resume/generic_form — Person2 — 1h
- [x] #2 ocr.py — Tesseract + PyMuPDF text extraction with per-word confidence — Person1 — 1.5h
- [x] #3 preprocess.py — OpenCV deskew/denoise for photographed documents — Person1 — 1h
- [x] #4 gbnf.py — JSON grammar for llama.cpp constrained decoding — Person2 — 1h
- [x] #5 llm_extract.py — mock + llm + ollama backends + auto-classify — Person2 — 2h
- [x] #6 validate.py — schema + business rules + OCR confidence flagging — Person2 — 1h
- [x] #7 pipeline.py — glue function called by all interfaces — Person1 — 0.5h

## Phase 2 — Interfaces
- [x] #8 cli.py — Typer CLI with auto-detect — Person1 — 1h
- [x] #9 app_streamlit.py — multi-page Streamlit UI — Person2 — 3h
- [x] #10 test suite — 25 tests incl. network-blocked proof — Person1 — 2h
