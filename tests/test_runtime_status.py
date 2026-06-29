from pathlib import Path

from docstruct.runtime_status import check_llm, check_mock


def test_check_mock_always_connected():
    status = check_mock()
    assert status["connected"] is True
    assert status["level"] == "info"


def test_check_llm_missing_path():
    status = check_llm(None)
    assert status["connected"] is False
    assert status["level"] == "error"


def test_check_llm_nonexistent_file():
    status = check_llm("/definitely/not/a/real/model.gguf")
    assert status["connected"] is False


def test_check_llm_existing_file(tmp_path: Path):
    fake_model = tmp_path / "fake.gguf"
    fake_model.write_bytes(b"not a real model, just testing the file-exists check")
    status = check_llm(str(fake_model))
    assert status["connected"] is True
    assert "fake.gguf" in status["label"]
