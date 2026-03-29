"""ChromaDB vector store for the synthetic legal knowledge base."""

from __future__ import annotations

import logging
from pathlib import Path

import chromadb

from factor.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "synthetic_legal"


class VectorStoreManager:
    """Manages ChromaDB collection lifecycle.

    Replaces module-level global state with an explicit manager for
    better testability and isolation.
    """

    def __init__(self):
        self._collection = None
        self._persist_dir: str | None = None

    def get_collection(self, persist_dir: str | None = None) -> chromadb.Collection:
        """Get or create the ChromaDB collection for synthetic legal data.

        Args:
            persist_dir: Directory for ChromaDB persistence.
                Defaults to settings.factor_knowledge_path.

        Returns:
            ChromaDB Collection instance.
        """
        target_dir = persist_dir or settings.factor_knowledge_path

        if self._collection is not None and self._persist_dir == target_dir:
            return self._collection

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(path=target_dir)

        self._collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "source": "Taylor658/synthetic-legal",
                "is_synthetic": "true",
                "disclaimer": "ALL content including citations is synthetically generated",
            },
        )
        self._persist_dir = target_dir

        logger.info(
            "ChromaDB collection '%s' ready at %s (%d documents)",
            COLLECTION_NAME,
            target_dir,
            self._collection.count(),
        )

        return self._collection

    def reset(self, persist_dir: str | None = None) -> None:
        """Delete and recreate the collection."""
        persist_path = persist_dir or self._persist_dir or settings.factor_knowledge_path
        client = chromadb.PersistentClient(path=persist_path)

        try:
            client.delete_collection(COLLECTION_NAME)
        except ValueError:
            pass

        self._collection = None
        self._persist_dir = None
        logger.info("Reset collection '%s'", COLLECTION_NAME)


# Module-level default manager instance
_manager = VectorStoreManager()


def get_vectorstore(persist_dir: str | None = None) -> chromadb.Collection:
    """Get or create the ChromaDB collection (module-level convenience).

    Args:
        persist_dir: Directory for ChromaDB persistence.

    Returns:
        ChromaDB Collection instance.
    """
    return _manager.get_collection(persist_dir)


def add_documents(
    documents: list[str],
    metadatas: list[dict],
    ids: list[str],
    persist_dir: str | None = None,
) -> int:
    """Add documents to the vector store.

    Args:
        documents: List of document texts to embed and store.
        metadatas: List of metadata dicts for each document.
        ids: List of unique IDs for each document.
        persist_dir: Optional override for persistence directory.

    Returns:
        Number of documents added.
    """
    collection = get_vectorstore(persist_dir)

    for meta in metadatas:
        meta["source"] = "Taylor658/synthetic-legal"
        meta["is_synthetic"] = "true"
        meta["disclaimer"] = "ALL content including citations is synthetically generated"

    batch_size = 500
    total_added = 0

    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i : i + batch_size]
        batch_metas = metadatas[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]

        collection.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids,
        )
        total_added += len(batch_docs)
        logger.info("Added batch %d-%d (%d documents)", i, i + len(batch_docs), total_added)

    return total_added


def query(
    query_text: str,
    n_results: int = 5,
    domain_filter: str | None = None,
    persist_dir: str | None = None,
) -> list[dict]:
    """Query the vector store for similar documents.

    Args:
        query_text: Text to search for.
        n_results: Number of results to return.
        domain_filter: Optional legal domain filter.
        persist_dir: Optional override for persistence directory.

    Returns:
        List of result dictionaries with content and metadata.
    """
    collection = get_vectorstore(persist_dir)

    where_filter = None
    if domain_filter:
        where_filter = {"legal_domain": domain_filter}

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=where_filter,
    )

    hits = []
    if results and results.get("documents"):
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            hits.append({
                "content": doc,
                "metadata": meta,
                "id": results["ids"][0][i] if results.get("ids") else str(i),
                "distance": results["distances"][0][i] if results.get("distances") else None,
                "is_synthetic": True,
            })

    return hits


def reset_collection(persist_dir: str | None = None) -> None:
    """Delete and recreate the collection."""
    _manager.reset(persist_dir)
