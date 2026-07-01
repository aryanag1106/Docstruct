# Plan: Document Extraction Pipeline

## Architecture

```
Input (PDF / image / .txt)
    ↓
OCR Agent (Tesseract) or direct text (PyMuPDF)
    ↓
Auto-Classify Agent (keyword heuristic)
    ↓
Extraction Agent (Ollama / llama.cpp, CPU, GGUF)
    ↓
Validation Agent (Pydantic + business rules)
    ↓
Structured JSON {status: ok | needs_review}
```

## Tech stack decisions
| Decision | Choice | Reason |
|---|---|---|
| OCR engine | Tesseract | Mature, CPU-only, multilingual |
| PDF text extraction | PyMuPDF | Fast, no OCR needed for text-layer PDFs |
| LLM runtime | Ollama (llama.cpp) | No C++ compiler required on Windows |
| Model | Qwen2.5-instruct GGUF Q4_K_M | Small, fast, good instruction-following |
| Validation | Pydantic v2 | Schema-first, clear error messages |

## Phased delivery
### Phase 1 — Core pipeline
- [x] OCR + text extraction
- [x] Schema definitions (receipt, invoice, resume, generic_form)
- [x] LLM extraction (mock + ollama + llm backends)
- [x] Validation with needs_review flagging

### Phase 2 — Interfaces
- [x] CLI (Typer)
- [x] Web UI (Streamlit, multi-page)
- [x] Auto-detect doc type

## Risks and mitigations
| Risk | Mitigation |
|---|---|
| LLM hallucination | Grammar-constrained decoding + Pydantic validation |
| OCR quality on photos | OpenCV preprocessing (deskew, denoise) |
| Windows C++ build failures | Ollama backend as alternative |

## Definition of done
All acceptance criteria in spec.md pass on a machine other than the one it was built on, with Wi-Fi off.
