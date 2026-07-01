# Agents — DocStruct

This file describes the AI agents and automated inference components in DocStruct.

## Pipeline agents

DocStruct's pipeline is a chain of CPU-based agents, each with a clearly declared scope:

### 1. OCR Agent

**Model:** Tesseract OCR 5.x
**Runtime:** `pytesseract` (CPU)
**Input:** PDF page or image
**Output:** Raw text + per-word confidence scores
**Languages supported:** English (`eng`), Telugu (`tel`), Hindi (`hin`)

Responsible for converting scanned documents and photographed images into machine-readable text. For text-layer PDFs, OCR is skipped entirely — PyMuPDF reads the embedded text directly.

### 2. Auto-Classify Agent

**Model:** Keyword heuristic (no neural network)
**Runtime:** Pure Python
**Input:** Raw text
**Output:** `receipt | invoice | resume | generic_form`

A lightweight, instant classifier that scores the text against keyword lists for each document type. Deliberately not a neural model — this keeps the `auto` option free (zero extra latency or model cost) on top of the extraction step.

### 3. Extraction Agent

**Model:** Qwen2.5-instruct (0.5B–3B), GGUF Q4_K_M quantization
**Runtime:** Ollama (llama.cpp-based) or llama-cpp-python directly
**Hardware:** CPU only
**Input:** Raw text + target JSON schema
**Output:** Structured JSON matching the document-type schema

The core AI agent. Takes noisy OCR text and uses an instruction-tuned LLM to fill the fields defined by the chosen document type's Pydantic schema. Grammar-constrained decoding (GBNF) guarantees syntactically valid JSON output.

### 4. Validation Agent

**Model:** None (deterministic rule engine)
**Runtime:** Pydantic v2 + custom business rules
**Input:** Raw extracted dict
**Output:** Validated record with per-field `status: ok | needs_review`

Cross-checks the extraction agent's output against the schema and business rules. Any field that fails type checks, format checks, or falls below OCR confidence thresholds is flagged `needs_review` with a human-readable reason — never silently accepted.

## What these agents do NOT do

- No agent sends data to an external server — all inference is local
- No agent makes decisions for the user — flagged fields are for human review
- No agent auto-corrects uncertain fields — `needs_review` is honest, not a guess
