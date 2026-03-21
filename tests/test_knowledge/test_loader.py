"""Tests for the synthetic dataset loader."""

from factor.knowledge.loader import (
    DATASET_NAME,
    DATASET_DISCLAIMER,
    DD_DOMAINS,
    ALL_DOMAINS,
)


def test_dataset_name():
    assert DATASET_NAME == "Taylor658/synthetic-legal"


def test_dataset_disclaimer_content():
    assert "synthetically generated" in DATASET_DISCLAIMER
    assert "NOT legally accurate" in DATASET_DISCLAIMER


def test_dd_domains_subset():
    for domain in DD_DOMAINS:
        assert domain in ALL_DOMAINS


def test_all_domains_count():
    assert len(ALL_DOMAINS) == 13


def test_dd_domains_count():
    assert len(DD_DOMAINS) == 6


def test_dd_domains_include_contract_law():
    assert "Contract Law & UCC Analysis" in DD_DOMAINS


def test_dd_domains_include_corporate():
    assert "Corporate/Commercial Law" in DD_DOMAINS
