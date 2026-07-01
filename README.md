# DocStruct

**Offline Document → JSON Extractor.** Turns PDFs, scanned documents, receipts, forms, and resumes into clean, structured JSON — entirely on a CPU, entirely offline.

Built for the CPU-First Hackathon: GPUs are scarce and online; most computing isn't. This project proves a CPU is enough, and that it keeps working when the network doesn't.

## 1. Problem statement

Receipts, resumes, and scanned forms are everywhere, and almost none of them start out as structured data. Cloud OCR/LLM APIs can turn them into JSON, but that means sending documents off-device and depending on a network connection that may simply not be there (a field office, a low-bandwidth region, a deliberately air-gapped environment). DocStruct does the same job — document in, structured JSON out — with the entire pipeline running locally on ordinary CPU hardware, no API keys, no outbound calls.

## 2. Features

- Accepts **PDFs** (text-layer or scanned), **images** (JPEG/PNG/TIFF/BMP), and **plain text** (`.txt`) files.
- Four built-in document-type schemas: **receipt**, **invoice**, **resume**, **generic_form** (a key:value catch-all for anything else) — plus an **auto-detect** mode (`doc_type="auto"`) that heuristically classifies the document before extracting, at no extra inference cost.
- Smart input handling: a text-layer PDF or `.txt` file is read directly (fast, no OCR, no hallucination risk); a scanned PDF or photo is OCR'd via Tesseract, with OpenCV preprocessing (deskew/denoise) for camera-quality input.
- Structured extraction via a local LLM, two ways: **llama.cpp** (grammar-constrained decoding) or a local **Ollama** server (`format: "json"` mode) — pick whichever installs cleanly on your machine; Ollama needs no C++ compiler, which matters a lot on Windows.
- Every output record carries a `status: ok | needs_review` plus a `field_flags` dict explaining exactly which fields are uncertain and why — **never** a silently fabricated field.
- Three interfaces, same underlying pipeline: a Typer **CLI**, a multi-page **Streamlit** web app (Dashboard / Upload & Process / History / Settings / About, with per-document View/Edit tabs so a flagged field can be corrected and re-validated in place), and the library itself (`docstruct.pipeline.process_document`).
- A dependency-free **mock** extraction backend (regex/heuristics) for development, CI, and demoing the architecture before model weights are downloaded — the real backends are `llm` and `ollama`; mock is explicitly not a substitute for either in the final demo.

## 3. Architecture

```text
 file.pdf / file.jpg
        │
        ▼
 ┌──────────────────┐   text-layer PDF? ──► read directly (PyMuPDF), no OCR
 │   ocr.py          │
 │  (+ preprocess.py │   scanned PDF / image? ──► OpenCV deskew/denoise ──► Tesseract OCR
 │   for camera input)                                                    (+ per-word confidence)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  llm_extract.py    │  raw text ──► grammar-constrained JSON (llama.cpp + GBNF)
 │  (mock | llm)      │  matching the target schema (schemas.py)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐
 │  validate.py        │  Pydantic schema check + business rules + OCR-confidence
 └────────┬─────────┘    flagging → status: ok | needs_review, with reasons
          ▼
   structured JSON  ──►  CLI stdout / file  or  Streamlit download button
```

## 4. Tech stack (CPU-first declaration, per hackathon rules)

| Stage | Tool / Model | Runtime | Hardware |
|---|---|---|---|
| Text-layer PDF extraction | PyMuPDF (`fitz`) | Python | CPU |
| Image/scanned-PDF preprocessing | OpenCV (deskew, denoise, adaptive threshold) | `opencv-python-headless` | CPU |
| OCR | **Tesseract OCR** | `pytesseract` | CPU |
| Structured extraction | **Qwen2.5-0.5B/1.5B-Instruct** (or similar small instruct model), GGUF, Q4_K_M quantization | **llama.cpp** (`llama-cpp-python`, grammar-constrained decoding) **or** **Ollama** (local server, `format: "json"` mode) — Ollama needs no C++ compiler | CPU |
| Validation | Pydantic v2 | Python | CPU |
| Interfaces | Typer (CLI), Streamlit (web) | Python | CPU |

No GPU, no CUDA, anywhere in this stack. The `mock` backend (heuristic, no model) exists for dev/CI speed; the `llm` backend above is what the live demo runs.

## 5. Setup (do this once, while online)

```bash
# System dependency
sudo apt-get install -y tesseract-ocr   # add tesseract-ocr-tel / -hin for other languages

# Python package, editable install with dev tools
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,web]"

# Generate the synthetic sample documents tests/demo use (no real PII anywhere in this repo)
python scripts/generate_sample_data.py
```

Then pick **one** real backend:

**Option A — Ollama (recommended on Windows, no C++ compiler needed):**

```bash
# Install from https://ollama.com/download, then:
ollama pull qwen2.5:0.5b
```

**Option B — llama-cpp-python:**

```bash
pip install -e ".[llm]"
pip install huggingface_hub
python scripts/download_model.py   # tries a few small models, prints the export command
export DOCSTRUCT_MODEL_PATH=/path/to/the/downloaded.gguf
```

## 6. Running it

```bash
# CLI (mock backend — no model needed, useful for a quick check; doc type auto-detected)
docstruct sample_data/receipt.png

# CLI, real backend
docstruct sample_data/invoice.txt --backend ollama
docstruct sample_data/resume.pdf --doc-type resume --backend llm

# Web UI (Dashboard / Upload & Process / History / Settings / About)
streamlit run src/docstruct/app_streamlit.py
```

## 7. Demo instructions (Wi-Fi OFF)

1. Turn off Wi-Fi/Ethernet at the OS level (the model weights and all Python packages must already be installed — see Setup above).
2. Run `python scripts/generate_sample_data.py` (pure local file generation, no network).
3. Run the CLI or Streamlit commands above against the generated samples.
4. Show at least one `status: needs_review` result (e.g. run a resume through `--doc-type receipt` deliberately, or feed a deliberately blurry image) to prove the system flags uncertainty instead of guessing.
5. `tests/test_no_network.py` is the automated version of this proof — it patches `socket.socket.connect` to raise and asserts the pipeline still completes. Run `pytest tests/test_no_network.py -v` to show it passing live.

## 8. License

**GNU AGPL-3.0.** See [`LICENSE`](./LICENSE) — a strong copyleft license: any distributed or network-deployed modified version of this project must also be released under AGPL-3.0 with source available. AGPL-3.0 is stricter than plain GPL-3.0 because it closes the "hosted service" loophole — even running a modified version as a web service requires releasing the source.

## 9. Repo map

```text
docstruct/
├── README.md, LICENSE, CONTRIBUTING.md, CHANGELOG.md
├── pyproject.toml              ← packaging + ruff/black/mypy/commitizen config
├── packages.txt                 ← apt deps for Streamlit Community Cloud (tesseract-ocr)
├── .streamlit/config.toml       ← dark + amber theme
├── .pre-commit-config.yaml
├── .gitlab-ci.yml               ← required CI, runs on the local GitLab Runner
├── .github/workflows/ci.yml     ← mirror for the GitHub remote
├── spec-kit/
│   ├── spec.md                  ← functional/non-functional requirements
│   └── plan.md                  ← architecture, phased delivery, risks
├── docs/
│   ├── work-division.md         ← 2-person role split
│   └── issues.yaml               ← source of truth for GitLab issues (assignee/estimate/due date)
├── scripts/
│   ├── create_gitlab_issues.py
│   ├── generate_sample_data.py
│   └── download_model.py        ← tries a few small GGUF models, smallest first
├── src/docstruct/                ← the actual implementation (see below)
├── tests/                         ← real pytest suite, including the offline proof
└── sample_data/                   ← synthetic fixtures generated by the script above
```

`src/docstruct/`: `schemas.py` (Pydantic models: receipt/invoice/resume/generic_form), `ocr.py`, `preprocess.py`, `gbnf.py`, `llm_extract.py` (mock + llama.cpp + Ollama backends, plus the auto-detect classifier), `validate.py`, `runtime_status.py` (sidebar connectivity checks), `pipeline.py` (the single function every interface calls), `cli.py`, `app_streamlit.py`.

## 10. Team

2-person team. Person 1: OCR + preprocessing + file handling. Person 2: LLM parsing + structuring + UI. See `docs/work-division.md` for the full split and frozen interfaces between the two halves.
