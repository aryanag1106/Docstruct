# Specification — DocStruct

## Problem statement
Convert PDFs, scanned documents, receipts, forms, and resumes into clean structured JSON, fully offline, on CPU-only hardware, without any cloud OCR/LLM API calls.

## Users
- **Person 1 (OCR/preprocessing/file handling)** — owns getting clean text out of whatever file comes in.
- **Person 2 (LLM parsing/structuring/UI)** — owns turning that text into a validated structured record and exposing it to a user.
- **End user** — anyone with a pile of receipts/resumes/forms and no interest in typing them in by hand.

## Input formats
- PDF (`.pdf`) — text-layer (native) or scanned (image-only); both handled, see `ocr.py`.
- Image (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`).
- Document type selector: `receipt` | `resume` | `generic_form` (chosen by the user; this is not auto-detected in the MVP — see Out of scope).

## Output format
A single JSON object:
```json
{
  "doc_type": "receipt",
  "data": { "...": "fields matching that doc_type's schema (schemas.py)" },
  "status": "ok | needs_review",
  "field_flags": { "field_name": "human-readable reason" },
  "ocr_source": "pdf_text | pdf_ocr | image_ocr",
  "ocr_confidence": "float 0-100, or null when no OCR ran (pdf_text path)"
}
```

## Functional requirements
- FR1: Given a text-layer PDF, extract its text directly, with `ocr_source: "pdf_text"` and `ocr_confidence: null` (no OCR ran, so there is no OCR confidence to report).
- FR2: Given a scanned PDF or image, OCR it via Tesseract and report `ocr_source` (`pdf_ocr`/`image_ocr`) and per-document mean confidence.
- FR3: Given OCR/PDF text and a `doc_type`, produce a dict matching that type's Pydantic schema.
- FR4: Validate the result; any missing/invalid required field, any disagreement, or low OCR confidence sets `status: needs_review` with a `field_flags` reason — never a silent guess.
- FR5: Both the CLI and the Streamlit UI call the same `pipeline.process_document()` function — no logic duplicated between interfaces.
- FR6: The pipeline makes zero network calls during processing with the `mock` backend (and with the `llm` backend, given a local model file) — this is enforced by an automated test, not just documented.

## Non-functional requirements
- NFR1 (Performance): a single-page document processes in a few seconds with the `mock` backend; the `llm` backend's latency depends on the chosen model size/quantization but stays CPU-only and avoids anything requiring more than a few GB of RAM.
- NFR2 (Privacy): no real person's data anywhere in the repo, fixtures, or demo recordings — `scripts/generate_sample_data.py` produces entirely synthetic documents.
- NFR3 (Resilience): a corrupt/unreadable file fails with a clear exception surfaced to the user (CLI exit code / Streamlit error banner), not a crash or a silently empty result.
- NFR4 (Portability): pure CPU wheels throughout; `llama-cpp-python`'s default build is CPU-only — never pin a CUDA build.

## Edge cases (explicitly handled or explicitly out of scope)
| Case | Behavior |
|---|---|
| Scanned PDF with very low scan quality | OCR confidence drops, `_ocr_quality` flag set, `status: needs_review` |
| Wrong `doc_type` selected for the file (e.g. a resume run as `receipt`) | Required receipt fields (total, merchant) come back null and flagged — proven by `tests/test_pipeline.py::test_wrong_doc_type_is_flagged_needs_review_not_fabricated` |
| Multi-page PDF | All pages' text concatenated; per-page OCR confidence averaged. Multi-page *table* extraction (e.g. a 5-page bank statement) is **out of scope** for the MVP |
| Handwritten forms | Tesseract's accuracy on cursive handwriting is a known, declared limitation — not solved in this MVP, only printed/typed text is targeted |
| Multiple documents batched in one run | **Out of scope** for MVP — one file per invocation; batching is a natural Phase-2.5 extension, not required for the hackathon submission |
| Auto-detecting `doc_type` instead of the user choosing it | **Out of scope** — a real classifier-then-route step is a stretch goal, not required |

## Performance constraints (CPU-only)
- No GPU/CUDA dependency anywhere, enforced by review (Constitution Article 1 in `spec-kit/plan.md`'s linked principles) and by `requirements`/`pyproject.toml` never specifying a CUDA build.
- Model size budget: ≤ ~2 GB for the chosen GGUF LLM at Q4_K_M, so it runs comfortably on an 8 GB RAM laptop alongside Tesseract and the rest of the stack.

## Acceptance criteria for the MVP demo
- [x] `pytest tests/` passes, including the network-blocked test (`test_no_network.py`).
- [x] A text-layer PDF, a scanned PDF, and a photographed-style image all process correctly (proven in `tests/test_pipeline.py`, run against real generated fixtures, not mocked file I/O).
- [x] A deliberately mismatched `doc_type` comes back `needs_review`, not a fabricated record.
- [ ] The real `llm` backend produces schema-valid JSON on the same sample set (needs a downloaded model — see README §5).
- [ ] Full run demoed with Wi-Fi off.
