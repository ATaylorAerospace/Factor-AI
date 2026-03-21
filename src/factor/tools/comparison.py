"""Cross-document comparison tools."""

from __future__ import annotations

import logging
from collections import defaultdict

from strands import tool

logger = logging.getLogger(__name__)


@tool
def compare_across_documents(provisions_by_doc: dict[str, list[dict]]) -> dict:
    """Cross-document comparison for inconsistencies and conflicts.

    Compares provisions of the same type across multiple documents to find
    inconsistencies in terms, jurisdictions, and risk levels.

    Args:
        provisions_by_doc: Mapping of document_id to list of provision dicts.
            Each provision dict must have 'provision_type' and 'text' keys.

    Returns:
        Dictionary with comparison results grouped by provision type.
    """
    by_type: dict[str, list[dict]] = defaultdict(list)

    for doc_id, provisions in provisions_by_doc.items():
        for prov in provisions:
            ptype = prov.get("provision_type", "other")
            by_type[ptype].append({
                "document_id": doc_id,
                "text": prov.get("text", ""),
                "provision_type": ptype,
            })

    results = []

    for ptype, provs in by_type.items():
        if len(provs) < 2:
            continue

        inconsistencies = []
        doc_ids = [p["document_id"] for p in provs]

        if ptype == "governing_law":
            jurisdictions = set()
            for p in provs:
                text_lower = p["text"].lower()
                for state in [
                    "new york", "delaware", "california", "texas", "illinois",
                    "florida", "massachusetts", "washington", "virginia",
                    "england", "singapore", "hong kong",
                ]:
                    if state in text_lower:
                        jurisdictions.add(state)
            if len(jurisdictions) > 1:
                inconsistencies.append(
                    f"Multiple governing law jurisdictions detected: {', '.join(jurisdictions)}"
                )

        if ptype in ("indemnification", "limitation_of_liability"):
            has_cap = []
            no_cap = []
            for p in provs:
                text_lower = p["text"].lower()
                if any(w in text_lower for w in ["cap", "limit", "aggregate", "maximum"]):
                    has_cap.append(p["document_id"])
                else:
                    no_cap.append(p["document_id"])
            if has_cap and no_cap:
                inconsistencies.append(
                    f"Liability cap inconsistency: capped in [{', '.join(has_cap)}], "
                    f"uncapped in [{', '.join(no_cap)}]"
                )

        if ptype == "termination":
            cure_period = []
            no_cure = []
            for p in provs:
                text_lower = p["text"].lower()
                if any(w in text_lower for w in ["cure", "remedy period", "days to cure"]):
                    cure_period.append(p["document_id"])
                else:
                    no_cure.append(p["document_id"])
            if cure_period and no_cure:
                inconsistencies.append(
                    f"Cure period inconsistency: present in [{', '.join(cure_period)}], "
                    f"absent in [{', '.join(no_cure)}]"
                )

        texts = [p["text"].strip() for p in provs]
        unique_texts = set(texts)
        if len(unique_texts) > 1:
            inconsistencies.append(
                f"Language varies across {len(unique_texts)} documents for '{ptype}'"
            )

        risk_level = "low"
        if len(inconsistencies) >= 3:
            risk_level = "high"
        elif len(inconsistencies) >= 1:
            risk_level = "medium"

        results.append({
            "provision_type": ptype,
            "documents_compared": doc_ids,
            "inconsistencies": inconsistencies,
            "risk_level": risk_level,
            "count": len(provs),
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
