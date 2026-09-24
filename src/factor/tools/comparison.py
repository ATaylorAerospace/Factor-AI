"""Cross-document comparison tools."""

from __future__ import annotations

import logging
import re
from collections import defaultdict

from strands import tool

logger = logging.getLogger(__name__)

JURISDICTIONS = [
    "new york", "delaware", "california", "texas", "illinois",
    "florida", "massachusetts", "washington", "virginia",
    "england", "singapore", "hong kong",
]
CAP_PATTERN = re.compile(r"\b(?:cap|caps|capped|limit|limited|limitation|aggregate|maximum)\b", re.IGNORECASE)
CURE_PATTERN = re.compile(r"\b(?:cure|cured|remedy period)\b", re.IGNORECASE)


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
                doc_id: {j for j in JURISDICTIONS if j in text}
                for doc_id, text in doc_text.items()
            }
            jurisdictions = set().union(*per_doc.values())
            if len(jurisdictions) > 1:
                inconsistencies.append(
                    f"Multiple governing law jurisdictions detected: {', '.join(sorted(jurisdictions))}"
                )

        if ptype in ("indemnification", "limitation_of_liability"):
            has_cap = [d for d in doc_ids if CAP_PATTERN.search(doc_text[d])]
            no_cap = [d for d in doc_ids if d not in has_cap]
            if has_cap and no_cap:
                inconsistencies.append(
                    f"Liability cap inconsistency: capped in [{names(has_cap)}], "
                    f"uncapped in [{names(no_cap)}]"
                )

        if ptype == "termination":
            cure = [d for d in doc_ids if CURE_PATTERN.search(doc_text[d])]
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
