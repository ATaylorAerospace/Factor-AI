"""RAG tools — search the synthetic legal knowledge base."""

from __future__ import annotations

import logging

from strands import tool

logger = logging.getLogger(__name__)


@tool
def search_synthetic_knowledge(query: str, domain: str | None = None, top_k: int = 5) -> list[dict]:
    """Search the SYNTHETIC legal knowledge base.

    WARNING: ALL results including citations are synthetically generated
    and NOT legally accurate. This dataset exists for research purposes only.

    Args:
        query: Search query string.
        domain: Optional legal domain filter (one of 13 domains).
        top_k: Number of results to return.

    Returns:
        List of result dictionaries with synthetic content and metadata.
    """
    try:
        from factor.knowledge.vectorstore import query as vector_query

        hits = [
            {
                "content": hit["content"],
                "legal_domain": (hit["metadata"] or {}).get("legal_domain", "unknown"),
                "source": "Taylor658/synthetic-legal",
                "is_synthetic": True,
                "disclaimer": (
                    "ALL content including citations is synthetically generated "
                    "and NOT legally accurate."
                ),
                "score": hit["distance"],
                "id": hit["id"],
            }
            for hit in vector_query(query, n_results=min(top_k, 20), domain_filter=domain)
        ]

        logger.info(
            "Knowledge search: query=%r, domain=%s, results=%d",
            query[:50], domain, len(hits),
        )
        return hits

    except Exception as e:
        logger.warning("Knowledge base not available: %s", e)
        return [{
            "content": "Knowledge base not initialized. Run scripts/seed_knowledge_base.py first.",
            "is_synthetic": True,
            "error": str(e),
        }]
