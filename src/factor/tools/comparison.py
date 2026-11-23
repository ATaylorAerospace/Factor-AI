"""Cross-document comparison tools."""

from __future__ import annotations

import logging
import re
from collections import defaultdict

from strands import tool

logger = logging.getLogger(__name__)

JURISDICTIONS = [
    # US states and DC
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "district of columbia", "florida", "georgia",
    "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky",
    "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire",
    "new jersey", "new mexico", "new york", "north carolina", "north dakota",
    "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island",
    "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming",
    # Common non-US choices of law
    "england", "wales", "scotland", "ireland", "ontario", "quebec",
    "british columbia", "singapore", "hong kong", "germany", "france",
    "switzerland", "netherlands", "japan", "australia", "india",
]
# Longest names first so "west virginia" is not read as "virginia"; word
# boundaries so "kansas" is not found inside "arkansas".
JURISDICTION_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(j) for j in sorted(JURISDICTIONS, key=len, reverse=True)) + r")\b"
)

# An explicit cap. "limit"/"limited"/"limitation" are weaker evidence: they
# appear in the heading "LIMITATION OF LIABILITY" even when the clause goes on
# to say liability is unlimited.
STRONG_CAP_PATTERN = re.compile(
    r"\b(?:cap|caps|capped|aggregate|maximum|(?:shall|will|may) not exceed)\b", re.IGNORECASE
)
WEAK_CAP_PATTERN = re.compile(r"\b(?:limit|limits|limited|limitation)\b", re.IGNORECASE)
UNCAPPED_PATTERN = re.compile(
    r"\b(?:unlimited|uncapped|no cap|no limit|without limit(?:ation)?|not (?:be )?limited)\b",
    re.IGNORECASE,
)
CURE_PATTERN = re.compile(r"\b(?:cure|cured|remedy period)\b", re.IGNORECASE)
NO_CURE_PATTERN = re.compile(
    r"\b(?:no|without(?: any)?)\s+(?:cure|remedy) period\b|\bno (?:right|opportunity) to cure\b",
    re.IGNORECASE,
)


def _has_liability_cap(text: str) -> bool:
    if STRONG_CAP_PATTERN.search(text):
        return True
    return bool(WEAK_CAP_PATTERN.search(text)) and not UNCAPPED_PATTERN.search(text)


def _has_cure_period(text: str) -> bool:
    return bool(CURE_PATTERN.search(text)) and not NO_CURE_PATTERN.search(text)


@tool
def compare_across_documents(
    provisions_by_doc: dict[str, list[dict]],
    doc_labels: dict[str, str] | None = None,
) -> dict:
    """Cross-document comparison for inconsistencies and conflicts.

    Compares provisions of the same type across multiple documents to find
    inconsistencies in terms, jurisdictions, and risk levels. Provisions are
    grouped per document first, so differences between clauses of a single
    document are never reported as cross-document inconsistencies.

    Args:
        provisions_by_doc: Mapping of document_id to list of provision dicts.
            Each provision dict must have 'provision_type' and 'text' keys.
        doc_labels: Optional mapping of document_id to a display name
            (e.g. the original filename) used in inconsistency messages.

    Returns:
        Dictionary with comparison results grouped by provision type.
    """
    labels = doc_labels or {}

    # provision type -> document id -> texts of that type in the document
    by_type: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for doc_id, provisions in provisions_by_doc.items():
        for prov in provisions:
            ptype = prov.get("provision_type", "other")
            by_type[ptype][doc_id].append(prov.get("text", ""))

    results = []

    for ptype, docs in by_type.items():
        if len(docs) < 2:
            continue

        doc_ids = list(docs)
        doc_text = {doc_id: "\n".join(texts).lower() for doc_id, texts in docs.items()}

        def names(ids: list[str]) -> str:
            return ", ".join(labels.get(i, i) for i in ids)

        inconsistencies = []

        if ptype == "governing_law":
            per_doc = {
                doc_id: frozenset(JURISDICTION_PATTERN.findall(text))
                for doc_id, text in doc_text.items()
            }
            # Compare document to document: two contracts that both name
            # Delaware law and New York courts agree with each other.
            named = {j for j in per_doc.values() if j}
            jurisdictions = set().union(*named) if named else set()
            if len(named) > 1:
                inconsistencies.append(
                    f"Multiple governing law jurisdictions detected: {', '.join(sorted(jurisdictions))}"
                )

        if ptype in ("indemnification", "limitation_of_liability"):
            has_cap = [d for d in doc_ids if _has_liability_cap(doc_text[d])]
            no_cap = [d for d in doc_ids if d not in has_cap]
            if has_cap and no_cap:
                inconsistencies.append(
                    f"Liability cap inconsistency: capped in [{names(has_cap)}], "
                    f"uncapped in [{names(no_cap)}]"
                )

        if ptype == "termination":
            cure = [d for d in doc_ids if _has_cure_period(doc_text[d])]
            no_cure = [d for d in doc_ids if d not in cure]
            if cure and no_cure:
                inconsistencies.append(
                    f"Cure period inconsistency: present in [{names(cure)}], "
                    f"absent in [{names(no_cure)}]"
                )

        normalized = {" ".join(text.split()) for text in doc_text.values()}
        if len(normalized) > 1:
            inconsistencies.append(
                f"Language varies across {len(normalized)} of {len(doc_ids)} documents for '{ptype}'"
            )

        risk_level = "low"
        if len(inconsistencies) >= 3:
            risk_level = "high"
        elif len(inconsistencies) >= 1:
            risk_level = "medium"

        results.append({
            "provision_type": ptype,
            "documents_compared": doc_ids,
            "document_names": [labels.get(d, d) for d in doc_ids],
            "inconsistencies": inconsistencies,
            "risk_level": risk_level,
            "count": sum(len(texts) for texts in docs.values()),
        })

    logger.info(
        "Compared provisions across %d documents: %d provision types analyzed",
        len(provisions_by_doc),
        len(results),
    )

    return {
        "comparisons": results,
        "total_documents": len(provisions_by_doc),
        "total_provision_types": len(by_type),
        "is_synthetic": True,
    }
