"""
Downloads a small instruct GGUF model for the `llm` backend, trying a few known-good
candidates in order (smallest/fastest first) so one stale filename doesn't block you.

Usage:
    pip install huggingface_hub
    python scripts/download_model.py
    export DOCSTRUCT_MODEL_PATH="$(pwd)/models/<whatever it printed>"

If every candidate below 404s (HF sometimes renames a quant file), open the repo
URL it prints in a browser, check the "Files" tab for the real filename, and run:
    huggingface-cli download <repo_id> <filename> --local-dir models
"""

from __future__ import annotations

from pathlib import Path

CANDIDATES = [
    # (repo_id, filename) — ordered smallest/fastest first
    ("Qwen/Qwen2.5-0.5B-Instruct-GGUF", "qwen2.5-0.5b-instruct-q4_k_m.gguf"),
    ("Qwen/Qwen2.5-1.5B-Instruct-GGUF", "qwen2.5-1.5b-instruct-q4_k_m.gguf"),
    ("TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"),
]

OUT_DIR = Path(__file__).resolve().parent.parent / "models"


def main() -> None:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise SystemExit("Run `pip install huggingface_hub` first.") from None

    OUT_DIR.mkdir(exist_ok=True)
    for repo_id, filename in CANDIDATES:
        print(f"Trying {repo_id} / {filename} ...")
        try:
            path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=OUT_DIR)
            print(f"\n✅ Downloaded: {path}")
            print(f'Run: export DOCSTRUCT_MODEL_PATH="{path}"')
            return
        except Exception as exc:  # noqa: BLE001 - we deliberately fall through to the next candidate
            print(f"  ✗ failed ({exc.__class__.__name__}): trying next candidate...")

    print(
        "\nAll candidates failed. Open https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/tree/main "
        "in a browser, copy the exact .gguf filename you see there, then run:\n"
        "  huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct-GGUF <filename> --local-dir models"
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
