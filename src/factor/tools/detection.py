"""Provision type detection tools."""

from __future__ import annotations

import re
import logging

from strands import tool

logger = logging.getLogger(__name__)

PROVISION_PATTERNS: dict[str, list[str]] = {
    "indemnification": [
        r"(?i)indemnif",
        r"(?i)hold\s+harmless",
        r"(?i)defend\s+and\s+indemnif",
    ],
    "limitation_of_liability": [
        r"(?i)limitation\s+of\s+liability",
        r"(?i)limit.{0,15}liab",
        r"(?i)in\s+no\s+event\s+shall.{0,30}(liable|liability)",
        r"(?i)aggregate\s+liability",
    ],
    "non_assignment": [
        r"(?i)non-?assignment",
        r"(?i)shall\s+not\s+assign",
        r"(?i)may\s+not\s+assign",
        r"(?i)assignment.{0,20}(prohibited|restricted)",
    ],
    "confidentiality": [
        r"(?i)confidential\s+information",
        r"(?i)non-?disclosure",
        r"(?i)proprietary\s+information",
        r"(?i)trade\s+secret",
    ],
    "non_compete": [
        r"(?i)non-?compete",
        r"(?i)restrictive\s+covenant",
        r"(?i)non-?solicitation",
        r"(?i)covenant\s+not\s+to\s+compete",
    ],
    "termination": [
        r"(?i)terminat",
        r"(?i)expir",
        r"(?i)cancellat",
        r"(?i)right\s+to\s+terminate",
    ],
    "governing_law": [
        r"(?i)governing\s+law",
        r"(?i)governed\s+by",
        r"(?i)jurisdiction",
        r"(?i)choice\s+of\s+law",
        r"(?i)venue",
    ],
    "force_majeure": [
        r"(?i)force\s+majeure",
        r"(?i)act\s+of\s+god",
        r"(?i)beyond.{0,20}(reasonable\s+)?control",
    ],
    "change_of_control": [
        r"(?i)change\s+of\s+control",
        r"(?i)merger\s+(or\s+)?acquisition",
        r"(?i)change\s+in\s+ownership",
    ],
    "representations_warranties": [
        r"(?i)represent.{0,10}warrant",
        r"(?i)hereby\s+represents",
        r"(?i)covenants\s+and\s+represents",
    ],
    "entire_agreement": [
        r"(?i)entire\s+agreement",
        r"(?i)integration\s+clause",
        r"(?i)supersedes\s+all\s+prior",
    ],
    "severability": [
        r"(?i)severab",
        r"(?i)savings\s+clause",
        r"(?i)if\s+any\s+provision.{0,30}invalid",
    ],
    "waiver": [
        r"(?i)waiver",
        r"(?i)amendment",
        r"(?i)modification.{0,20}writing",
    ],
    "notice": [
        r"(?i)notice.{0,10}(shall|must|will)\s+be",
        r"(?i)notification",
        r"(?i)written\s+notice",
    ],
}


@tool
def detect_provision_type(provision_text: str) -> dict:
    """Classify a provision into a standard category.

    Uses pattern matching to identify the provision type from the text.

    Args:
        provision_text: The text of the provision to classify.

    Returns:
        Dictionary with detected type, confidence, and matched patterns.
    """
    if not provision_text.strip():
        return {
            "provision_type": "other",
            "confidence": 0.0,
            "matched_patterns": [],
        }

    scores: dict[str, int] = {}
    matches_detail: dict[str, list[str]] = {}

    for ptype, patterns in PROVISION_PATTERNS.items():
        match_count = 0
        matched = []
        for pattern in patterns:
            found = re.findall(pattern, provision_text)
            if found:
                match_count += len(found)
                matched.extend(found)
        if match_count > 0:
            scores[ptype] = match_count
            matches_detail[ptype] = matched

    if not scores:
        return {
            "provision_type": "other",
            "confidence": 0.0,
            "matched_patterns": [],
        }

    best_type = max(scores, key=scores.get)  # type: ignore[arg-type]
    total_matches = sum(scores.values())
    confidence = min(scores[best_type] / max(total_matches, 1), 1.0)

    logger.info("Detected provision type: %s (confidence=%.2f)", best_type, confidence)

    return {
        "provision_type": best_type,
        "confidence": round(confidence, 3),
        "matched_patterns": matches_detail.get(best_type, []),
        "all_detected": list(scores.keys()),
    }
