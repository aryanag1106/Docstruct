# DocStruct — Constitution

## Non-negotiable principles

1. **CPU-first, always.** No code path requires a GPU/CUDA runtime. Default build, config, and demo run on CPU only.

2. **Offline-first, provably.** The core pipeline (file → structured JSON) makes zero outbound network calls. This is a passing automated test (`tests/test_no_network.py`), not just a README claim.

3. **Declare every model and runtime.** Every model used anywhere in the pipeline is named (model + size + quantization) and its runtime declared (llama.cpp via Ollama, Tesseract, PyMuPDF, etc.) in the README.

4. **Never fabricate a field.** When OCR confidence is low, when a field fails schema validation, or when the model is uncertain, the system marks that field `needs_review` with a reason — never silently inventing a plausible value.

5. **Privacy by construction.** No real person's PII is ever committed to this repository — not in fixtures, not in screenshots, not in demo recordings. All sample/test documents use fully synthetic data.

6. **Strong copyleft, deliberately.** Licensed AGPL-3.0. A network-deployed, modified version of this project must release its source.

7. **No fake green checkmarks.** Every CI/pre-commit check defined does real work. A stub job that always exits 0 is a disqualifying violation per the hackathon rules, and bad engineering regardless.

8. **Small, reviewable, attributed work.** Every issue has exactly one assignee, one estimate, one due date. Commits follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`).
