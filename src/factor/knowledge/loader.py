"""Load the Taylor658/synthetic-legal dataset from HuggingFace."""

from __future__ import annotations

import logging
from typing import Iterator

logger = logging.getLogger(__name__)

DATASET_NAME = "Taylor658/synthetic-legal"
DATASET_DISCLAIMER = (
    "ALL content in this dataset is synthetically generated and IS NOT legally accurate. "
    "All citations, statutes, case references, legal problems, verified solutions, and "
    "pairings are synthetic constructs. No citations, statutes, or case references are real."
)

DD_DOMAINS = [
    "Contract Law & UCC Analysis",
    "Corporate/Commercial Law",
    "Intellectual Property",
    "Tax Law",
    "Environmental Law",
    "Administrative Law",
]

ALL_DOMAINS = [
    "Contract Law & UCC Analysis",
    "Corporate/Commercial Law",
    "Tort Law",
    "Constitutional Law",
    "Criminal Law & Procedure",
    "Administrative Law",
    "Intellectual Property",
    "International Law",
    "Tax Law",
    "Civil Procedure",
    "Environmental Law",
    "Immigration Law",
    "Family Law",
]


def load_synthetic_dataset(
    split: str = "train",
    domains: list[str] | None = None,
    max_rows: int | None = None,
) -> list[dict]:
    """Load the synthetic-legal dataset from HuggingFace.

    Args:
        split: Dataset split to load.
        domains: Optional list of legal domains to filter by.
            Defaults to DD_DOMAINS for due diligence use.
        max_rows: Maximum number of rows to load.

    Returns:
        List of row dictionaries with synthetic legal content.
    """
    from datasets import load_dataset

    logger.info("Loading dataset %s (split=%s)", DATASET_NAME, split)

    ds = load_dataset(DATASET_NAME, split=split)

    if domains is None:
        domains = DD_DOMAINS

    rows = []
    for row in ds:
        if domains and row.get("legal_domain") not in domains:
            continue

        rows.append({
            "id": row.get("id"),
            "legal_domain": row.get("legal_domain", ""),
            "legal_problem": row.get("legal_problem", ""),
            "verified_solution": row.get("verified_solution", ""),
            "verification_method": row.get("verification_method", ""),
            "is_synthetic": True,
            "disclaimer": DATASET_DISCLAIMER,
        })

        if max_rows and len(rows) >= max_rows:
            break

    logger.info("Loaded %d rows from %s (filtered to %d domains)", len(rows), DATASET_NAME, len(domains))
    return rows


def iter_synthetic_dataset(
    split: str = "train",
    domains: list[str] | None = None,
    batch_size: int = 100,
) -> Iterator[list[dict]]:
    """Iterate over the dataset in batches for memory efficiency.

    Args:
        split: Dataset split to load.
        domains: Optional domain filter.
        batch_size: Number of rows per batch.

    Yields:
        Batches of row dictionaries.
    """
    from datasets import load_dataset

    ds = load_dataset(DATASET_NAME, split=split, streaming=True)

    if domains is None:
        domains = DD_DOMAINS

    batch: list[dict] = []
    for row in ds:
        if domains and row.get("legal_domain") not in domains:
            continue

        batch.append({
            "id": row.get("id"),
            "legal_domain": row.get("legal_domain", ""),
            "legal_problem": row.get("legal_problem", ""),
            "verified_solution": row.get("verified_solution", ""),
            "verification_method": row.get("verification_method", ""),
            "is_synthetic": True,
            "disclaimer": DATASET_DISCLAIMER,
        })

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch
