"""Tests for legal domain classification tools."""

from factor.tools.classification import classify_domain


def test_classify_contract_law():
    """Contract-related text should classify to Contract Law."""
    result = classify_domain(
        provision_text="This contract involves a breach of warranty under the UCC."
    )
    assert "Contract" in result


def test_classify_corporate():
    """Corporate text should classify to Corporate/Commercial Law."""
    result = classify_domain(
        provision_text="The board of directors approved the merger and acquisition of securities."
    )
    assert "Corporate" in result


def test_classify_ip():
    """IP-related text should classify to Intellectual Property."""
    result = classify_domain(
        provision_text="Patent infringement and trademark licensing rights are at issue."
    )
    assert "Intellectual Property" in result


def test_classify_environmental():
    """Environmental text should classify to Environmental Law."""
    result = classify_domain(
        provision_text="EPA hazardous waste remediation and clean water compliance."
    )
    assert "Environmental" in result


def test_classify_criminal():
    """Criminal text should classify to Criminal Law."""
    result = classify_domain(
        provision_text="The defendant faces felony prosecution and sentencing."
    )
    assert "Criminal" in result


def test_classify_tax():
    """Tax-related text should classify to Tax Law."""
    result = classify_domain(
        provision_text="The IRS assessment of capital gains tax and withholding requirements."
    )
    assert "Tax" in result


def test_classify_empty_defaults_to_contract():
    """Empty text should default to Contract Law & UCC Analysis."""
    result = classify_domain(provision_text="")
    assert result == "Contract Law & UCC Analysis"


def test_classify_no_keywords_defaults_to_contract():
    """Text with no matching keywords defaults to Contract Law."""
    result = classify_domain(
        provision_text="The quick brown fox jumps over the lazy dog."
    )
    assert result == "Contract Law & UCC Analysis"
