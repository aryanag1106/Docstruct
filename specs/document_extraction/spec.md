# Feature Spec: Offline Document to Structured JSON Extraction

## Overview
DocStruct converts PDFs, scanned documents, receipts, invoices, resumes, and plain text files into clean, validated structured JSON — entirely offline, on CPU.

## Supported input formats
- PDF (text-layer or scanned)
- Images (JPEG, PNG, BMP, TIFF)
- Plain text (`.txt`)

## Supported document types
- `receipt` — retail receipts with merchant, total, line items
- `invoice` — B2B invoices with invoice number, vendor, customer, due date
- `resume` — CVs with name, contact, skills, experience, education
- `generic_form` — key:value catch-all for any other structured document

## Pipeline
```
Input file
    ↓
OCR (Tesseract) or direct text extraction (PyMuPDF) — CPU only
    ↓
LLM field extraction (Ollama/llama.cpp, CPU) — grammar-constrained JSON
    ↓
Pydantic schema validation + business rules
    ↓
Structured JSON with per-field status (ok | needs_review)
```

## Model and runtime declaration
| Stage | Model | Runtime | Hardware |
|---|---|---|---|
| OCR | Tesseract 5.x (eng/tel/hin) | pytesseract | CPU |
| Text extraction | PyMuPDF | fitz | CPU |
| Field extraction | Qwen2.5 (0.5B–3B instruct), GGUF Q4_K_M | Ollama (llama.cpp-based) | CPU |
| Validation | Pydantic v2 | Python | CPU |

## Acceptance criteria
- [x] Processing completes with zero network calls (verified by `tests/test_no_network.py`)
- [x] All supported input formats and document types produce schema-valid JSON output
- [x] Every field carries a `status: ok | needs_review` — never a silent fabrication
- [x] CLI and web UI both call the same `pipeline.process_document()` function
- [x] Full pipeline runs on a CPU-only laptop with Wi-Fi off
