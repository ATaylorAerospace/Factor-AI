"""Tests for provision chunking tools."""

from factor.tools.chunking import chunk_provisions, _detect_anchor


def test_chunk_provisions_basic(sample_nda_text):
    provisions = chunk_provisions(text=sample_nda_text, doc_type="nda")
    assert isinstance(provisions, list)
    assert len(provisions) > 0
    for prov in provisions:
        assert "id" in prov
        assert "text" in prov
        assert "provision_type" in prov
        assert "chunk_index" in prov


def test_chunk_provisions_empty():
    provisions = chunk_provisions(text="", doc_type="unknown")
    assert provisions == []


def test_chunk_provisions_single_paragraph():
    text = "This is a simple paragraph with no sections."
    provisions = chunk_provisions(text=text, doc_type="unknown")
    assert len(provisions) >= 1
    assert provisions[0]["text"].strip() == text


def test_detect_anchor_indemnification():
    result = _detect_anchor("The party shall indemnify and hold harmless")
    assert result == "indemnification"


def test_detect_anchor_termination():
    result = _detect_anchor("Either party may terminate this agreement")
    assert result == "termination"


def test_detect_anchor_none():
    result = _detect_anchor("The quick brown fox jumps over the lazy dog")
    assert result is None


def test_chunk_provisions_preserves_doc_type():
    text = "1. CONFIDENTIALITY\nAll information shall be kept confidential."
    provisions = chunk_provisions(text=text, doc_type="nda")
    for prov in provisions:
        assert prov["doc_type"] == "nda"
