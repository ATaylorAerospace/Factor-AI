"""Tests for provision type detection tools."""

from factor.tools.detection import detect_provision_type


def test_detect_indemnification():
    result = detect_provision_type(
        provision_text="Party A shall indemnify and hold harmless Party B from all losses."
    )
    assert result["provision_type"] == "indemnification"
    assert result["confidence"] > 0


def test_detect_limitation_of_liability():
    result = detect_provision_type(
        provision_text="The limitation of liability shall not exceed the aggregate fees paid."
    )
    assert result["provision_type"] == "limitation_of_liability"


def test_detect_confidentiality():
    result = detect_provision_type(
        provision_text="All confidential information shall be kept secret under this non-disclosure."
    )
    assert result["provision_type"] == "confidentiality"


def test_detect_governing_law():
    result = detect_provision_type(
        provision_text="This agreement shall be governed by and construed under the laws of Delaware."
    )
    assert result["provision_type"] == "governing_law"


def test_detect_termination():
    result = detect_provision_type(
        provision_text="Either party may terminate this agreement upon 30 days written notice."
    )
    assert result["provision_type"] == "termination"


def test_detect_force_majeure():
    result = detect_provision_type(
        provision_text="In the event of force majeure or act of God, performance is excused."
    )
    assert result["provision_type"] == "force_majeure"


def test_detect_empty_text():
    result = detect_provision_type(provision_text="")
    assert result["provision_type"] == "other"
    assert result["confidence"] == 0.0


def test_detect_unknown_text():
    result = detect_provision_type(
        provision_text="The quick brown fox jumps over the lazy dog."
    )
    assert result["provision_type"] == "other"


def test_detect_returns_all_detected():
    result = detect_provision_type(
        provision_text="The indemnification clause also limits liability under governing law."
    )
    assert "all_detected" in result
    assert len(result["all_detected"]) >= 1
