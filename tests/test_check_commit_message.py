from scripts.check_commit_message import check


def test_accepts_simple_conventional_commit():
    assert check("feat: add invoice schema")


def test_accepts_commit_with_scope():
    assert check("fix(ocr): handle plain text files")


def test_accepts_multiline_commit_checking_first_line_only():
    assert check("docs: update README\n\nlonger body text here")


def test_rejects_non_conventional_commit():
    assert not check("updated some stuff")


def test_rejects_empty_message():
    assert not check("")


def test_rejects_unknown_type():
    assert not check("yolo: did a thing")
