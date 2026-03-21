"""Citation extraction and labeling tools."""

from __future__ import annotations

import re
import logging

from strands import tool

logger = logging.getLogger(__name__)

CASE_CITATION_PATTERN = re.compile(
    r"([A-Z][a-zA-Z\s&,.']+)\s+v\.\s+([A-Z][a-zA-Z\s&,.']+),?\s*"
    r"(\d+\s+[A-Z][a-zA-Z.\s]+\d+)?"
)
STATUTE_PATTERN = re.compile(
    r"(\d+)\s+(U\.?S\.?C\.?|C\.?F\.?R\.?|Stat\.?)\s*§?\s*(\d+[a-z]?(?:\([a-z0-9]+\))?)"
)
REGULATION_PATTERN = re.compile(
    r"(\d+)\s+(?:Fed\.\s*Reg\.|FR)\s+(\d+)"
)


@tool
def extract_citations(text: str) -> list[dict]:
    """Extract and label citations from text.

    All citations extracted from the synthetic dataset are synthetic
    and NOT real legal references.

    Args:
        text: Text to extract citations from.

    Returns:
        List of citation dictionaries, each marked as synthetic.
    """
    citations = []

    for match in CASE_CITATION_PATTERN.finditer(text):
        citations.append({
            "type": "case",
            "plaintiff": match.group(1).strip(),
            "defendant": match.group(2).strip(),
            "reporter": match.group(3).strip() if match.group(3) else "",
            "full_citation": match.group(0).strip(),
            "is_synthetic": True,
            "warning": "This citation is synthetically generated and NOT a real case.",
        })

    for match in STATUTE_PATTERN.finditer(text):
        citations.append({
            "type": "statute",
            "title": match.group(1),
            "code": match.group(2),
            "section": match.group(3),
            "full_citation": match.group(0).strip(),
            "is_synthetic": True,
            "warning": "This citation is synthetically generated and NOT a real statute.",
        })

    for match in REGULATION_PATTERN.finditer(text):
        citations.append({
            "type": "regulation",
            "volume": match.group(1),
            "page": match.group(2),
            "full_citation": match.group(0).strip(),
            "is_synthetic": True,
            "warning": "This citation is synthetically generated and NOT a real regulation.",
        })

    logger.info("Extracted %d citations (all synthetic)", len(citations))
    return citations
