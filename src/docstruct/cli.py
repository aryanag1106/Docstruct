"""
CLI entry point.

    docstruct sample_data/receipt.png --doc-type receipt
    docstruct sample_data/resume.pdf  --doc-type resume --backend llm

(Typer collapses a single-command app to a flat CLI — no subcommand name needed.)
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .pipeline import process_document

app = typer.Typer(add_completion=False, help="Offline, CPU-only document -> structured JSON extractor.")


@app.command()
def extract(
    path: Path = typer.Argument(..., exists=True, help="Path to a PDF or image file."),
    doc_type: str = typer.Option(..., "--doc-type", "-t", help="receipt | resume | generic_form"),
    backend: str = typer.Option("mock", "--backend", "-b", help="mock | llm"),
    lang: str = typer.Option("eng", help="Tesseract language code, e.g. eng, eng+tel, eng+hin"),
    out: Path | None = typer.Option(None, "--out", "-o", help="Write JSON to this path instead of stdout."),
) -> None:
    """Extract structured JSON from a single document."""
    result = process_document(path, doc_type=doc_type, backend=backend, lang=lang)  # type: ignore[arg-type]
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if out:
        out.write_text(text)
        typer.echo(f"Wrote {out}")
    else:
        typer.echo(text)

    if result["status"] == "needs_review":
        typer.secho(f"⚠ needs_review: {result['field_flags']}", fg=typer.colors.YELLOW, err=True)


if __name__ == "__main__":
    app()
