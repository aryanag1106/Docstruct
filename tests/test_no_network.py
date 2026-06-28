"""
Automated version of "demo must show it running with the network off."

Patches socket.socket.connect to raise, then runs the full pipeline. If anything in
ocr.py / preprocess.py / llm_extract.py (mock backend) / validate.py ever tries to
open a network connection, this test fails loudly instead of the team finding out
live during the Wi-Fi-off demo.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from docstruct.pipeline import process_document

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"


class NetworkBlockedError(RuntimeError):
    pass


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def guard(*args, **kwargs):
        raise NetworkBlockedError("Network access attempted during an offline-required code path.")

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket.socket, "connect_ex", guard)
    yield


def test_pipeline_completes_with_network_blocked():
    result = process_document(SAMPLE_DIR / "receipt.png", doc_type="receipt", backend="mock")
    assert result["status"] == "ok"


def test_pdf_text_pipeline_completes_with_network_blocked():
    result = process_document(SAMPLE_DIR / "resume.pdf", doc_type="resume", backend="mock")
    assert result["data"]["full_name"] == "Asha Verma"
