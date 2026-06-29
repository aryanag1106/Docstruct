"""
Lightweight, fast checks used only by the sidebar's "LOCAL LLM RUNTIME" status
indicator — never the core pipeline. These never raise; they return a status dict so
the UI can render something honest instead of either crashing or showing a fake green
light.

Note on `check_ollama`: it does open a socket, but only to localhost (loopback) —
that's local IPC to a server already running on the same machine, not an outbound
network/cloud call, and it has no bearing on `tests/test_no_network.py`'s guarantee
(which covers the document-processing pipeline, not this optional UI status check).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

StatusLevel = Literal["ok", "warn", "error", "info"]


def check_mock() -> dict[str, Any]:
    return {"connected": True, "label": "Mock heuristics — no model loaded", "level": "info"}


def check_llm(model_path: str | None) -> dict[str, Any]:
    if not model_path:
        return {"connected": False, "label": "No model path set", "level": "error"}
    if not Path(model_path).exists():
        return {"connected": False, "label": f"Model file not found: {model_path}", "level": "error"}
    return {"connected": True, "label": f"Ready — {Path(model_path).name}", "level": "ok"}


def check_ollama(url: str, model: str, timeout: float = 1.5) -> dict[str, Any]:
    try:
        import requests

        resp = requests.get(f"{url.rstrip('/')}/api/tags", timeout=timeout)
        resp.raise_for_status()
        tags = [m.get("name", "") for m in resp.json().get("models", [])]
        if any(model == t or t.startswith(model) for t in tags):
            return {"connected": True, "label": f"Connected — {model}", "level": "ok"}
        return {
            "connected": False,
            "label": f"Ollama running, but '{model}' isn't pulled yet",
            "level": "warn",
        }
    except Exception:
        return {"connected": False, "label": f"Ollama not reachable at {url}", "level": "error"}


def check_backend(backend: str, **kwargs: Any) -> dict[str, Any]:
    if backend == "mock":
        return check_mock()
    if backend == "llm":
        return check_llm(kwargs.get("model_path"))
    if backend == "ollama":
        return check_ollama(
            kwargs.get("ollama_url", "http://localhost:11434"), kwargs.get("ollama_model", "")
        )
    return {"connected": False, "label": f"Unknown backend: {backend}", "level": "error"}
