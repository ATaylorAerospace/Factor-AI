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
        from factor.knowledge.vectorstore import get_vectorstore

        store = get_vectorstore()
        where_filter = None
        if domain:
            where_filter = {"legal_domain": domain}

        results = store.query(
            query_texts=[query],
            n_results=min(top_k, 20),
            where=where_filter,
        )

        hits = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                meta = {}
                if results.get("metadatas") and results["metadatas"][0]:
                    meta = results["metadatas"][0][i]

                hits.append({
                    "content": doc,
                    "legal_domain": meta.get("legal_domain", "unknown"),
                    "source": "Taylor658/synthetic-legal",
                    "is_synthetic": True,
                    "disclaimer": (
                        "ALL content including citations is synthetically generated "
                        "and NOT legally accurate."
                    ),
                    "score": (
                        results["distances"][0][i]
                        if results.get("distances")
                        else None
                    ),
                    "id": (
                        results["ids"][0][i]
                        if results.get("ids")
                        else str(i)
                    ),
                })

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
