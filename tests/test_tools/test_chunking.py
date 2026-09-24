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


def test_chunk_keeps_all_caps_headings_with_their_clause():
    text = (
        "GOVERNING LAW. This Agreement shall be construed under the laws of Delaware.\n"
        "INDEMNITY: Supplier shall hold the Customer free from all losses arising from breach."
    )
    provisions = chunk_provisions(text=text, doc_type="unknown")
    assert [p["text"].split()[0] for p in provisions] == ["GOVERNING", "INDEMNITY:"]
    assert provisions[0]["provision_type"] == "governing_law"
    assert provisions[1]["provision_type"] == "indemnification"


def test_chunk_splits_mixed_case_section_headings():
    text = (
        "Section 1. Governing Law. This Agreement is governed by the laws of Delaware.\n"
        "Section 2. Indemnification. Supplier shall indemnify Customer against claims.\n"
        "Section 3. Termination. Either party may terminate upon thirty days notice."
    )
    provisions = chunk_provisions(text=text, doc_type="unknown")
    assert len(provisions) == 3
    assert [p["provision_type"] for p in provisions] == [
        "governing_law", "indemnification", "termination",
    ]


def test_chunk_attaches_bare_article_line_to_next_clause():
    text = (
        "ARTICLE VII\n"
        "INDEMNIFICATION. Each party shall indemnify the other against third-party claims."
    )
    provisions = chunk_provisions(text=text, doc_type="unknown")
    assert len(provisions) == 1
    assert provisions[0]["text"].startswith("ARTICLE VII")
