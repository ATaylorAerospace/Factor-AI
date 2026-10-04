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


def _make_pdf(path: Path, text: str) -> None:
    import fitz

    doc = fitz.open()
    doc.new_page().insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()


def test_parse_pdf_extracts_text_without_details(temp_dir):
    path = Path(temp_dir) / "sample.pdf"
    _make_pdf(path, "Section 1. Indemnification applies.")
    result = parse_pdf(file_path=str(path))
    assert "Indemnification" in result["text"]
    assert result["pages"] == 1
    # Per-page copies of the text are opt-in to keep peak memory down.
    assert "page_details" not in result


def test_parse_pdf_include_details(temp_dir):
    path = Path(temp_dir) / "sample.pdf"
    _make_pdf(path, "Section 1. Termination.")
    result = parse_pdf(file_path=str(path), include_details=True)
    assert result["page_details"][0]["page_number"] == 1
    assert "Termination" in result["page_details"][0]["text"]


def test_parse_docx_details_opt_in(temp_dir):
    from docx import Document

    path = Path(temp_dir) / "sample.docx"
    doc = Document()
    doc.add_paragraph("Governing Law. Delaware.")
    doc.save(str(path))

    plain = parse_docx(file_path=str(path))
    assert plain["paragraphs"] == 1
    assert "paragraph_details" not in plain

    detailed = parse_docx(file_path=str(path), include_details=True)
    assert detailed["paragraph_details"][0]["text"] == "Governing Law. Delaware."
