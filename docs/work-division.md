# Work Division Plan — DocStruct

> Replace the placeholder names/usernames below with your real team before Phase 1 submission. Keep this file and `docs/issues.yaml` in sync.

## Roles

| Role | Placeholder | Real name | GitLab username | GitHub username | Owns |
|---|---|---|---|---|---|
| Person 1 — OCR / preprocessing / file handling | Person1 | Aryan Agarwal | `AryanAg` | `AryanAg` | `ocr.py`, `preprocess.py`, `cli.py`, README/spec docs, CI/pre-commit setup |
| Person 2 — LLM parsing / structuring / UI | Person2 | Sejal | `sejal_521` | `sejal_521` | `schemas.py`, `gbnf.py`, `llm_extract.py`, `validate.py`, `pipeline.py`, `app_streamlit.py` |

## Why this split
Tesseract/PyMuPDF/OpenCV work (Person 1) and Pydantic-schema/llama.cpp work (Person 2) touch almost entirely different files and different dependency stacks — they can be developed in parallel from the first hour, as long as the interface between them is frozen early.

## Frozen interface (defined once, used by everyone)
- `ocr.extract_text(path, lang="eng") -> OcrResult` (`OcrResult` = text + source + mean_confidence + per_word_confidence). **Person 1 owns this, frozen early.**
- `llm_extract.extract(doc_type, text, backend="mock"|"llm", **kwargs) -> dict`. **Person 2 owns this, frozen early.**
- `validate.validate(doc_type, raw_dict, ocr_result=None) -> ValidatedRecord`. **Person 2 owns this.**
- `pipeline.process_document(path, doc_type, backend="mock", lang="eng") -> dict`. The one function `cli.py` and `app_streamlit.py` call — neither interface needs to know about Tesseract, PyMuPDF, or llama.cpp directly.

This interface is **already implemented and tested** in this repo (see `tests/`) — both people can build directly against it rather than negotiating it from scratch.

## Hand-off checkpoints
- **Early** — confirm the frozen interface above still matches what's actually in `pipeline.py` (it does, as of this commit); any change to a function signature gets flagged to the other person immediately, not discovered at integration time.
- **Mid-Phase-2** — Person 2 swaps `llm_extract`'s mock calls for the real `llm` backend with a downloaded model; Person 1 in parallel improves OCR robustness (language packs, preprocessing tuning) and starts the CI/pre-commit setup for Phase 3.
- **Before MVP deadline** — both backends (`mock` and `llm`) produce valid output on the same sample set; record the offline demo.
- **Phase 3** — Person 1 finishes CI/pre-commit/audit; Person 2 finishes CONTRIBUTING/CHANGELOG/repo metadata. Both do a final joint pass confirming zero stub checks.

## Communication
Whoever's blocked says so immediately rather than waiting for a checkpoint — with a 2-person team there's no slack to absorb silent blockers.
