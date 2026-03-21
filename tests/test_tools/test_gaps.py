"""Tests for gap analysis tools."""

from factor.tools.gaps import find_gaps


def test_find_gaps_nda(sample_provisions):
    gaps = find_gaps(detected_provisions=sample_provisions, doc_type="nda")
    assert isinstance(gaps, list)
    # NDA checklist includes non_assignment which is not in sample_provisions
    missing_types = [g["missing_provision"] for g in gaps]
    assert "non_assignment" in missing_types
    for gap in gaps:
        assert gap["is_synthetic"] is True
        assert gap["severity"] in ("low", "medium", "high", "critical")
        assert gap["recommendation"]


def test_find_gaps_no_missing():
    all_nda = [
        "confidentiality", "non_compete", "non_assignment",
        "termination", "governing_law", "entire_agreement",
        "severability", "notice", "indemnification",
    ]
    gaps = find_gaps(detected_provisions=all_nda, doc_type="nda")
    assert len(gaps) == 0


def test_find_gaps_empty_provisions():
    gaps = find_gaps(detected_provisions=[], doc_type="nda")
    assert len(gaps) > 0  # All provisions are missing


def test_find_gaps_unknown_doc_type():
    gaps = find_gaps(detected_provisions=["termination"], doc_type="unknown")
    assert isinstance(gaps, list)
    # unknown has a shorter checklist
    for gap in gaps:
        assert gap["doc_type"] == "unknown"


def test_find_gaps_custom_checklist():
    checklist = {"required": ["confidentiality", "termination", "custom_clause"]}
    gaps = find_gaps(
        detected_provisions=["confidentiality"],
        doc_type="nda",
        checklist=checklist,
    )
    missing = [g["missing_provision"] for g in gaps]
    assert "termination" in missing
    assert "custom_clause" in missing
    assert "confidentiality" not in missing
