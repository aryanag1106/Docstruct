# Contributing to DocStruct

## Principles

CPU-only, offline-first for the core pipeline, never fabricate a field, no real PII ever, no stub CI/pre-commit jobs. See `spec-kit/plan.md` for the full list.

## Local dev setup

```bash
sudo apt-get install -y tesseract-ocr
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,web]"
pre-commit install
pre-commit install --hook-type commit-msg   # for the commitizen commit-message check
python scripts/generate_sample_data.py
```

### gitleaks (one extra step — no Go toolchain needed)

The pre-commit gitleaks hook calls a local `gitleaks` binary rather than building from source (that build needs a Go toolchain, which most machines don't have). Install it once:

- **Windows**: download the `windows_x64` zip from <https://github.com/gitleaks/gitleaks/releases/latest>, extract `gitleaks.exe` somewhere on your `PATH` (e.g. `C:\Tools`), then add that folder to PATH.
- **macOS**: `brew install gitleaks`
- **Linux**: download the matching `linux_x64` tarball from the releases page above, extract `gitleaks`, and move it to `/usr/local/bin`.

Verify with `gitleaks version`. CI doesn't need this step — `.gitlab-ci.yml`'s `gitleaks` job runs in its own Docker container, completely independent of your local machine.

## Commit style

Conventional commits, enforced by `commitizen` at commit time: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`. One logical change per commit.

## Before opening an MR/PR

- [ ] `pre-commit run --all-files` passes locally
- [ ] `pytest tests/` passes, including `tests/test_no_network.py`
- [ ] No new dependency pulls in a GPU/CUDA build by default
- [ ] If you touched `pipeline.process_document`'s signature, update `docs/work-division.md`'s frozen interface section — the other person's code depends on it staying accurate

## Running the full pipeline locally

```bash
docstruct sample_data/receipt.png --doc-type receipt           # mock backend
docstruct sample_data/resume.pdf  --doc-type resume --backend llm   # needs DOCSTRUCT_MODEL_PATH
streamlit run src/docstruct/app_streamlit.py
```
