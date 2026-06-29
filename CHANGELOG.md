# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `invoice` document type (distinct schema from `receipt`: invoice number, due date, vendor/customer).
- Plain-text (`.txt`) ingestion — no OCR needed, same as the existing text-layer-PDF fast path.
- Heuristic doc-type auto-detection (`doc_type="auto"`) — keyword-based, not a model call, so it's free.
- **Ollama backend** (`backend="ollama"`) as a no-C++-compiler alternative to llama-cpp-python — added after a Windows build failure (missing MSVC/CMake toolchain) made clear that llama-cpp-python's source build isn't reliable to assume on a hackathon laptop.
- `runtime_status.py` — honest connectivity checks (file-exists for `llm`, a quick `/api/tags` ping for `ollama`) backing the UI's status indicator; never reports "connected" without actually checking.
- Full Streamlit UI rewrite: Dashboard / Upload & Process / History / Settings / About pages, dark+amber theme, multi-file upload, per-result View/Edit tabs (corrections re-validate against the schema, never just trusted blindly), session-based history (explicitly not persisted — no database in this MVP).
- `scripts/download_model.py` — tries a few small GGUF models in order, prints the working `export` command.
- `packages.txt` + `.streamlit/config.toml` for Streamlit Community Cloud deployment.
- 9 new tests (invoice extraction, auto-detect, processing-time reporting, runtime-status checks) — 19 total, all passing.

### Fixed

- `generate_sample_data.py`'s receipt image used a hardcoded Linux font path with a silent fallback to PIL's tiny unscaled default bitmap font on any other OS — this OCR'd badly on Windows and caused 2 of 10 tests to fail there. Now tries several cross-platform font paths, falling back to a *scaled* default font, not the tiny one.
- `MONEY_RE` in the mock extractor capped the integer part of an amount at 3 digits unless comma-grouped, so an ungrouped 4-digit amount like `2341.50` silently matched only `341.50`. Caught by the new invoice test, fixed to allow any number of leading digits.

## [Unreleased — earlier]

- Phase 1: README, spec-kit (spec.md, plan.md), work-division plan, GitLab issues source-of-truth + bulk-creation script, GPL-3.0 license.
- Phase 2 (core pipeline, implemented and tested):
  - `schemas.py` — Pydantic models for `receipt`, `resume`, `generic_form`.
  - `ocr.py` — text-layer PDF extraction (PyMuPDF) and Tesseract OCR for scanned PDFs/images, with per-line reconstruction and per-word confidence.
  - `preprocess.py` — OpenCV deskew/denoise/adaptive-threshold for camera-quality input.
  - `gbnf.py` — generic JSON grammar for llama.cpp grammar-constrained decoding.
  - `llm_extract.py` — heuristic `mock` backend + `llm` backend wiring for llama.cpp.
  - `validate.py` — Pydantic + business-rule + OCR-confidence-aware `ok`/`needs_review` flagging.
  - `pipeline.py`, `cli.py` (Typer), `app_streamlit.py` (Streamlit) — end-to-end glue and two interfaces over one pipeline function.
  - `scripts/generate_sample_data.py` — synthetic (no real PII) receipt/resume fixtures.
- Phase 3 tooling: `.pre-commit-config.yaml`, `.gitlab-ci.yml` (10 real checks), `.github/workflows/ci.yml`, `pyproject.toml` (ruff/black/mypy/commitizen config).

### Known gaps (tracked in `docs/issues.yaml`)

- `llm` and `ollama` backends not yet validated end-to-end against a real downloaded/pulled model on the team's own machine (mock backend is what's tested in CI; real-model validation happens locally where model weights actually live).
- Schema-aware (per-field) GBNF grammar is a stretch goal; current grammar guarantees valid JSON syntax only, not per-field types — semantic correctness is `validate.py`'s job.
- History/Dashboard are session-only (no persistent database) — by design for this MVP, noted as a known limitation rather than hidden.
