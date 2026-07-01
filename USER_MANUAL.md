# DocStruct — User Manual

## What is DocStruct?

DocStruct converts PDFs, scanned documents, receipts, invoices, resumes, and plain text files into clean, structured JSON — entirely offline, on CPU. Nothing leaves your machine.

## Quick start

### 1. Install

```bash
# System dependency (Linux)
sudo apt-get install -y tesseract-ocr

# Python package
pip install -e ".[dev,web]"

# Generate sample test files
python scripts/generate_sample_data.py
```

### 2. Run the web app

```bash
streamlit run src/docstruct/app_streamlit.py
```

Open `http://localhost:8501` in your browser.

### 3. Run the CLI

```bash
# Auto-detect document type
docstruct sample_data/invoice.txt

# Specify document type and backend
docstruct sample_data/resume.pdf --doc-type resume --backend ollama
```

## Supported document types

| Type | What it extracts |
|---|---|
| `receipt` | Merchant name, date, total amount, line items |
| `invoice` | Invoice number, vendor, customer, due date, total |
| `resume` | Name, email, phone, skills, experience, education |
| `generic_form` | Any key:value pairs found in the document |
| `auto` | Auto-detects the type (default) |

## Extraction backends

| Backend | What it needs | When to use |
|---|---|---|
| `mock` | Nothing | Development, CI, quick testing |
| `ollama` | Ollama app running locally | Best for Windows — real AI, no compiler needed |
| `llm` | `llama-cpp-python` + a GGUF model file | Linux/macOS with a downloaded GGUF model |

## Setting up the Ollama backend (recommended)

1. Install Ollama from `https://ollama.com/download`
2. Pull a model: `ollama pull qwen2.5:0.5b`
3. In Settings → pick **ollama** → set model tag to `qwen2.5:0.5b`

## Setting up the llm backend

```bash
pip install -e ".[llm]"
pip install huggingface_hub
python scripts/download_model.py
export DOCSTRUCT_MODEL_PATH="models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
```

## Offline demo

This is the whole point of DocStruct. Turn off Wi-Fi, then:

```bash
# Prove the pipeline makes zero network calls
pytest tests/test_no_network.py -v

# Run real AI extraction with no internet
docstruct sample_data/resume.pdf --doc-type resume --backend ollama
```

## Understanding the output

Every output record includes:

- `status: ok` — all fields extracted cleanly
- `status: needs_review` — one or more fields were uncertain or missing, with `field_flags` explaining why

DocStruct **never silently fabricates a field** — if it's uncertain, it says so.
