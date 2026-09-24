"""Document type inference — shared by the API pipeline and the Coordinator Agent."""

from __future__ import annotations

import re

# Whole-word patterns: a bare substring check made "standard" or "calendar"
# look like "nda" and misclassified most contracts as NDAs.
DOC_TYPE_SIGNALS: dict[str, list[str]] = {
    "nda": [r"non-?disclosure", r"\bnda\b", r"confidentiality agreement"],
    "lease": [r"lease agreement", r"\btenant\b", r"\blandlord\b", r"\bpremises\b"],
    "loan": [r"loan agreement", r"\bborrower\b", r"\blender\b", r"principal amount"],
    "merger": [r"\bmerger\b", r"\bacquisition\b", r"purchase agreement", r"target company"],
    "employment": [r"employment agreement", r"\bemployee\b", r"\bemployer\b", r"\bcompensation\b"],
    "license": [r"license agreement", r"\blicensor\b", r"\blicensee\b", r"\broyalt(?:y|ies)\b"],
    "supply": [r"supply agreement", r"\bsupplier\b", r"purchase order"],
}

_COMPILED = {
    doc_type: [re.compile(p, re.IGNORECASE) for p in patterns]
    for doc_type, patterns in DOC_TYPE_SIGNALS.items()
}


def infer_doc_type(text: str, filename: str = "") -> str:
    """Infer the contract type from its opening text and filename.

    Args:
        text: Full document text (only the first 2,000 characters are used).
        filename: Original filename, which often names the agreement type.

    Returns:
        One of the gap-analysis checklist keys, or "unknown".
    """
    name = re.sub(r"[_\-.]+", " ", filename)
    combined = f"{text[:2000]} {name}"
    for doc_type, patterns in _COMPILED.items():
        if any(p.search(combined) for p in patterns):
            return doc_type
    return "unknown"
