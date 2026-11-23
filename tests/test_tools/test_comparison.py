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


def test_compare_ignores_differences_within_one_document():
    """Two termination clauses in the same document are not a cross-document issue."""
    result = compare_across_documents(provisions_by_doc={
        "doc-1": [
            {"provision_type": "termination", "text": "Terminate for cause on 30 days notice and cure."},
            {"provision_type": "termination", "text": "Terminate for convenience immediately."},
        ],
    })
    assert result["comparisons"] == []


def test_compare_counts_documents_and_uses_labels():
    result = compare_across_documents(
        provisions_by_doc={
            "doc-1": [
                {"provision_type": "termination", "text": "Terminate with a 30 day cure period."},
                {"provision_type": "termination", "text": "Terminate for convenience."},
            ],
            "doc-2": [{"provision_type": "termination", "text": "Terminate immediately."}],
        },
        doc_labels={"doc-1": "msa.pdf", "doc-2": "nda.pdf"},
    )
    term = result["comparisons"][0]
    assert term["documents_compared"] == ["doc-1", "doc-2"]
    assert term["document_names"] == ["msa.pdf", "nda.pdf"]
    assert any("present in [msa.pdf], absent in [nda.pdf]" in i for i in term["inconsistencies"])
    assert any("across 2 of 2 documents" in i for i in term["inconsistencies"])


def test_compare_cap_detection_uses_whole_words():
    """'capital' and 'escape' must not count as a liability cap."""
    result = compare_across_documents(provisions_by_doc={
        "doc-1": [{"provision_type": "indemnification", "text": "Indemnify for losses to capital."}],
        "doc-2": [{"provision_type": "indemnification", "text": "Indemnify; no escape from duty."}],
    })
    indem = result["comparisons"][0]
    assert not any("cap inconsistency" in i for i in indem["inconsistencies"])


def _compare(ptype, a, b):
    result = compare_across_documents(provisions_by_doc={
        "a": [{"provision_type": ptype, "text": a}],
        "b": [{"provision_type": ptype, "text": b}],
    })
    return " | ".join(result["comparisons"][0]["inconsistencies"])


def test_unlimited_liability_under_limitation_heading_is_uncapped():
    findings = _compare(
        "limitation_of_liability",
        "LIMITATION OF LIABILITY. Liability under this agreement is unlimited.",
        "Liability is capped at the fees paid.",
    )
    assert "Liability cap inconsistency" in findings


def test_cap_with_carve_out_still_counts_as_capped():
    findings = _compare(
        "limitation_of_liability",
        "Aggregate liability shall not exceed $1M, but is not limited for fraud.",
        "Liability is capped at the fees paid.",
    )
    assert "Liability cap inconsistency" not in findings


def test_jurisdictions_beyond_the_original_twelve_are_compared():
    findings = _compare("governing_law", "governed by the laws of Ohio", "governed by the laws of Nevada")
    assert "nevada" in findings and "ohio" in findings


def test_west_virginia_differs_from_virginia_and_kansas_from_arkansas():
    assert "governing law jurisdictions" in _compare(
        "governing_law", "laws of West Virginia", "laws of Virginia"
    )
    assert "governing law jurisdictions" in _compare(
        "governing_law", "laws of Arkansas", "laws of Kansas"
    )


def test_identical_law_and_venue_pairs_are_consistent():
    clause = "governed by the laws of Delaware; venue lies in New York"
    assert "governing law jurisdictions" not in _compare("governing_law", clause, clause)


def test_explicit_no_cure_period_is_not_a_cure_period():
    findings = _compare(
        "termination",
        "Termination is effective at once with no cure period.",
        "The breaching party has a 30 day cure period.",
    )
    assert "Cure period inconsistency" in findings
