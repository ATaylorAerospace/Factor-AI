"""Document parsing tools for PDF and DOCX extraction."""

from __future__ import annotations

import logging
from pathlib import Path

from strands import tool

logger = logging.getLogger(__name__)


@tool
def parse_pdf(file_path: str, include_details: bool = False) -> dict:
    """Extract text from a PDF document, preserving structure.

    Args:
        file_path: Path to the PDF file.
        include_details: Also return per-page text and dimensions under
            ``page_details``. This duplicates the whole document text in
            memory, so callers that only need ``text`` should leave it off.

    Returns:
        Dictionary with extracted text, page count, and metadata.
    """
    import fitz  # PyMuPDF

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}", "text": "", "pages": 0}

    pages = []
    full_text_parts = []

    with fitz.open(str(path)) as doc:
        page_count = len(doc)
        for page_num, page in enumerate(doc, 1):
            text = page.get_text("text")
            full_text_parts.append(text)
            if include_details:
                pages.append({
                    "page_number": page_num,
                    "text": text,
                    "width": page.rect.width,
                    "height": page.rect.height,
                })

    full_text = "\n\n".join(full_text_parts)
    logger.info("Parsed PDF %s: %d pages, %d characters", path.name, page_count, len(full_text))

    result = {
        "filename": path.name,
        "text": full_text,
        "pages": page_count,
        "file_size_bytes": path.stat().st_size,
    }
    if include_details:
        result["page_details"] = pages
    return result


@tool
def parse_docx(file_path: str, include_details: bool = False) -> dict:
    """Extract text from a Word document, preserving structure.

    Args:
        file_path: Path to the DOCX file.
        include_details: Also return per-paragraph text and style under
            ``paragraph_details``; off by default to avoid holding the
            document text twice.

    Returns:
        Dictionary with extracted text, paragraph count, and metadata.
    """
    from docx import Document

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}", "text": "", "paragraphs": 0}

    doc = Document(str(path))
    paragraphs = []
    full_text_parts = []
    paragraph_count = 0

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            paragraph_count += 1
            full_text_parts.append(text)
            if include_details:
                paragraphs.append({
                    "index": i,
                    "text": text,
                    "style": para.style.name if para.style else "Normal",
                })

    tables_text = []
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells)
            if row_text.strip(" |"):
                tables_text.append(row_text)

    full_text = "\n\n".join(full_text_parts)
    if tables_text:
        full_text += "\n\n[TABLES]\n" + "\n".join(tables_text)

    logger.info("Parsed DOCX %s: %d paragraphs", path.name, paragraph_count)

    result = {
        "filename": path.name,
        "text": full_text,
        "paragraphs": paragraph_count,
        "table_count": len(doc.tables),
        "file_size_bytes": path.stat().st_size,
    }
    if include_details:
        result["paragraph_details"] = paragraphs
    return result
