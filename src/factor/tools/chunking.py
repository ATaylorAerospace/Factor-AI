"""Provision chunking tools — segment documents into legal provisions."""

from __future__ import annotations

import re
import uuid
import logging

from strands import tool

logger = logging.getLogger(__name__)

PROVISION_ANCHORS = [
    r"(?i)\b(indemnif|hold harmless)",
    r"(?i)\b(limitation of liability|limit.{0,10}liab)",
    r"(?i)\b(non-?assignment|assign.{0,10}clause)",
    r"(?i)\b(confidential|non-?disclosure)",
    r"(?i)\b(non-?compete|restrictive covenant)",
    r"(?i)\b(terminat|expir)",
    r"(?i)\b(governing law|jurisdiction|venue)",
    r"(?i)\b(force majeure|act of god)",
    r"(?i)\b(change of control|merger|acquisition)",
    r"(?i)\b(represent.{0,10}warrant)",
    r"(?i)\b(entire agreement|integration clause)",
    r"(?i)\b(severab|savings clause)",
    r"(?i)\b(waiver|amendment)",
    r"(?i)\b(notice|notification)",
]

SECTION_PATTERN = re.compile(
    r"^(?:\d+[\.\)]\s|[A-Z][A-Z\s]{2,}[:\.]|ARTICLE\s+\w+|SECTION\s+\d+)",
    re.MULTILINE,
)


def _detect_anchor(text: str) -> str | None:
    """Return the first matching provision anchor label, or None."""
    anchor_labels = [
        "indemnification", "limitation_of_liability", "non_assignment",
        "confidentiality", "non_compete", "termination", "governing_law",
        "force_majeure", "change_of_control", "representations_warranties",
        "entire_agreement", "severability", "waiver", "notice",
    ]
    for pattern, label in zip(PROVISION_ANCHORS, anchor_labels):
        if re.search(pattern, text):
            return label
    return None


@tool
def chunk_provisions(text: str, doc_type: str = "unknown") -> list[dict]:
    """Segment document text into individual legal provisions.

    Splits on section headers and then classifies each chunk using
    provision anchor patterns.

    Args:
        text: Full document text.
        doc_type: Type of document (nda, lease, loan, etc.).

    Returns:
        List of provision chunk dictionaries.
    """
    if not text.strip():
        return []

    splits = SECTION_PATTERN.split(text)
    raw_chunks: list[str] = []

    for part in splits:
        stripped = part.strip()
        if not stripped:
            continue
        if len(stripped) < 30:
            if raw_chunks:
                raw_chunks[-1] += "\n" + stripped
            else:
                raw_chunks.append(stripped)
        else:
            raw_chunks.append(stripped)

    if not raw_chunks and text.strip():
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        raw_chunks = paragraphs if paragraphs else [text.strip()]

    provisions = []
    for i, chunk_text in enumerate(raw_chunks):
        anchor = _detect_anchor(chunk_text)
        provisions.append({
            "id": str(uuid.uuid4()),
            "chunk_index": i,
            "text": chunk_text,
            "provision_type": anchor or "other",
            "doc_type": doc_type,
            "char_count": len(chunk_text),
        })

    logger.info("Chunked document into %d provisions (doc_type=%s)", len(provisions), doc_type)
    return provisions
