"""Tests for cross-document comparison tools."""

from factor.tools.comparison import compare_across_documents


def test_compare_detects_jurisdiction_inconsistency(sample_provisions_by_doc):
    """Verify governing law inconsistencies are detected across documents."""
    result = compare_across_documents(provisions_by_doc=sample_provisions_by_doc)
    assert result["total_documents"] == 2
    assert result["is_synthetic"] is True
    gov_law = [c for c in result["comparisons"] if c["provision_type"] == "governing_law"]
    assert len(gov_law) == 1
    assert len(gov_law[0]["inconsistencies"]) > 0


def test_compare_detects_liability_cap_inconsistency(sample_provisions_by_doc):
    """Verify liability cap inconsistencies are flagged."""
    result = compare_across_documents(provisions_by_doc=sample_provisions_by_doc)
    indem = [c for c in result["comparisons"] if c["provision_type"] == "indemnification"]
    assert len(indem) == 1
    assert len(indem[0]["inconsistencies"]) > 0


def test_compare_single_document():
    """No comparisons should be produced with only one document."""
    result = compare_across_documents(provisions_by_doc={
        "doc-1": [{"provision_type": "termination", "text": "30 days notice required."}],
    })
    assert result["comparisons"] == []
    assert result["total_documents"] == 1


def test_compare_empty_input():
    """Empty input should return empty comparisons."""
    result = compare_across_documents(provisions_by_doc={})
    assert result["total_documents"] == 0
    assert result["comparisons"] == []


def test_compare_identical_provisions():
    """Identical provisions across docs should not flag language variations."""
    same_text = "This Agreement shall be governed by the laws of Delaware."
    result = compare_across_documents(provisions_by_doc={
        "doc-1": [{"provision_type": "governing_law", "text": same_text}],
        "doc-2": [{"provision_type": "governing_law", "text": same_text}],
    })
    gov_law = [c for c in result["comparisons"] if c["provision_type"] == "governing_law"]
    assert len(gov_law) == 1
    text_variations = [
        i for i in gov_law[0]["inconsistencies"] if "Language varies" in i
    ]
    assert len(text_variations) == 0


def test_compare_termination_cure_period_inconsistency():
    """Cure period present in one doc but absent in another should be flagged."""
    result = compare_across_documents(provisions_by_doc={
        "doc-1": [{"provision_type": "termination", "text": "Either party may terminate with 30 days cure period."}],
        "doc-2": [{"provision_type": "termination", "text": "Either party may terminate immediately."}],
    })
    term = [c for c in result["comparisons"] if c["provision_type"] == "termination"]
    assert len(term) == 1
    assert any("Cure period" in i for i in term[0]["inconsistencies"])
