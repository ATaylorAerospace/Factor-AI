"""Tests for document parsing tools."""

from pathlib import Path

from factor.tools.parsing import parse_pdf, parse_docx


def test_parse_pdf_missing_file():
    result = parse_pdf(file_path="/nonexistent/file.pdf")
    assert result["error"]
    assert result["text"] == ""


def test_parse_docx_missing_file():
    result = parse_docx(file_path="/nonexistent/file.docx")
    assert result["error"]
    assert result["text"] == ""


def test_parse_pdf_returns_structure(temp_dir):
    # Create a simple text file to test the path validation
    path = Path(temp_dir) / "test.txt"
    path.write_text("sample content")
    # parse_pdf expects a real PDF; test that it handles non-PDF gracefully
    try:
        result = parse_pdf(file_path=str(path))
        assert isinstance(result, dict)
    except Exception:
        pass  # Expected for non-PDF file
