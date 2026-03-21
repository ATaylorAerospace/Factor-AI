"""Gap analysis tools — identify missing provisions."""

from __future__ import annotations

import logging

from strands import tool

logger = logging.getLogger(__name__)

STANDARD_CHECKLISTS: dict[str, list[str]] = {
    "nda": [
        "confidentiality",
        "non_compete",
        "non_assignment",
        "termination",
        "governing_law",
        "entire_agreement",
        "severability",
        "notice",
        "indemnification",
    ],
    "lease": [
        "termination",
        "governing_law",
        "indemnification",
        "limitation_of_liability",
        "force_majeure",
        "notice",
        "entire_agreement",
        "severability",
        "waiver",
        "representations_warranties",
    ],
    "loan": [
        "representations_warranties",
        "indemnification",
        "limitation_of_liability",
        "termination",
        "governing_law",
        "change_of_control",
        "notice",
        "entire_agreement",
        "severability",
        "waiver",
        "force_majeure",
    ],
    "merger": [
        "representations_warranties",
        "indemnification",
        "limitation_of_liability",
        "termination",
        "governing_law",
        "change_of_control",
        "non_compete",
        "confidentiality",
        "notice",
        "entire_agreement",
        "severability",
        "force_majeure",
    ],
    "employment": [
        "termination",
        "non_compete",
        "confidentiality",
        "indemnification",
        "governing_law",
        "severability",
        "notice",
        "entire_agreement",
    ],
    "unknown": [
        "termination",
        "governing_law",
        "indemnification",
        "entire_agreement",
        "severability",
        "notice",
    ],
}

SEVERITY_MAP: dict[str, str] = {
    "indemnification": "high",
    "limitation_of_liability": "high",
    "change_of_control": "high",
    "representations_warranties": "high",
    "confidentiality": "medium",
    "non_compete": "medium",
    "termination": "medium",
    "governing_law": "medium",
    "force_majeure": "medium",
    "non_assignment": "low",
    "entire_agreement": "low",
    "severability": "low",
    "waiver": "low",
    "notice": "low",
}


@tool
def find_gaps(
    detected_provisions: list[str],
    doc_type: str = "unknown",
    checklist: dict | None = None,
) -> list[dict]:
    """Identify missing provisions against a standard checklist.

    Args:
        detected_provisions: List of detected provision type strings.
        doc_type: Document type to select the appropriate checklist.
        checklist: Optional custom checklist. Uses built-in if not provided.

    Returns:
        List of gap dictionaries with missing provision details.
    """
    if checklist:
        required = checklist.get("required", [])
    else:
        dt = doc_type.lower().replace(" ", "_")
        required = STANDARD_CHECKLISTS.get(dt, STANDARD_CHECKLISTS["unknown"])

    detected_set = {p.lower().replace(" ", "_") for p in detected_provisions}
    gaps = []

    for provision in required:
        if provision not in detected_set:
            severity = SEVERITY_MAP.get(provision, "medium")
            gaps.append({
                "missing_provision": provision,
                "severity": severity,
                "doc_type": doc_type,
                "recommendation": (
                    f"Consider adding a '{provision.replace('_', ' ')}' clause. "
                    f"This is standard for {doc_type} agreements."
                ),
                "reference_standard": f"Standard {doc_type} checklist",
                "is_synthetic": True,
            })

    logger.info(
        "Gap analysis for %s: %d required, %d detected, %d gaps",
        doc_type,
        len(required),
        len(detected_set),
        len(gaps),
    )

    return gaps
