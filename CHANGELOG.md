# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]
### Added
- Phase 1: README, spec-kit (spec.md, plan.md), work-division plan, GitLab issues source-of-truth + bulk-creation script, GPL-3.0 license.
- Phase 2 (core pipeline, implemented and tested in this commit):
  - `schemas.py` — Pydantic models for `receipt`, `resume`, `generic_form`.
  - `ocr.py` — text-layer PDF extraction (PyMuPDF) and Tesseract OCR for scanned PDFs/images, with per-line reconstruction and per-word confidence.
  - `preprocess.py` — OpenCV deskew/denoise/adaptive-threshold for camera-quality input.
  - `gbnf.py` — generic JSON grammar for llama.cpp grammar-constrained decoding.
  - `llm_extract.py` — heuristic `mock` backend (no model required) + `llm` backend wiring for llama.cpp (pending a downloaded model for end-to-end real-model validation).
  - `validate.py` — Pydantic + business-rule + OCR-confidence-aware `ok`/`needs_review` flagging.
  - `pipeline.py`, `cli.py` (Typer), `app_streamlit.py` (Streamlit) — end-to-end glue and two interfaces over one pipeline function.
  - `scripts/generate_sample_data.py` — synthetic (no real PII) receipt/resume fixtures.
  - 10 passing pytest tests, including an automated network-blocked proof (`test_no_network.py`).
- Phase 3 tooling: `.pre-commit-config.yaml`, `.gitlab-ci.yml` (10 real checks), `.github/workflows/ci.yml`, `pyproject.toml` (ruff/black/mypy/commitizen config). `ruff`, `black --check`, `mypy`, `bandit` all verified clean against the current codebase.

### Known gaps (tracked in `docs/issues.yaml`)
- `llm` backend not yet validated against a real downloaded GGUF model (mock backend is the only one tested end-to-end so far).
- Streamlit UI is functional but not visually polished.
- Schema-aware (per-field) GBNF grammar is a stretch goal; current grammar guarantees valid JSON syntax only, not per-field types — semantic correctness is `validate.py`'s job.
