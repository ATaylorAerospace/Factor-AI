"""Tests for ChromaDB vector store."""

import pytest

from factor.knowledge.vectorstore import (
    get_vectorstore,
    add_documents,
    query,
    reset_collection,
    COLLECTION_NAME,
    _collection,
)


def test_get_vectorstore_creates_collection(chroma_temp_dir):
    import factor.knowledge.vectorstore as vs
    vs._collection = None  # reset global

    collection = get_vectorstore(persist_dir=chroma_temp_dir)
    assert collection is not None
    assert collection.name == COLLECTION_NAME

    vs._collection = None  # clean up


def test_add_and_query_documents(chroma_temp_dir):
    import factor.knowledge.vectorstore as vs
    vs._collection = None

    docs = [
        "Indemnification clause with unlimited liability and no cap.",
        "Standard confidentiality agreement with mutual obligations.",
        "Force majeure clause covering pandemic and natural disasters.",
    ]
    metas = [
        {"legal_domain": "Contract Law & UCC Analysis"},
        {"legal_domain": "Contract Law & UCC Analysis"},
        {"legal_domain": "Corporate/Commercial Law"},
    ]
    ids = ["doc-1", "doc-2", "doc-3"]

    count = add_documents(
        documents=docs,
        metadatas=metas,
        ids=ids,
        persist_dir=chroma_temp_dir,
    )
    assert count == 3

    results = query(
        query_text="indemnification liability",
        n_results=2,
        persist_dir=chroma_temp_dir,
    )
    assert len(results) > 0
    assert results[0]["is_synthetic"] is True

    vs._collection = None


def test_add_documents_includes_synthetic_metadata(chroma_temp_dir):
    import factor.knowledge.vectorstore as vs
    vs._collection = None

    add_documents(
        documents=["Test document"],
        metadatas=[{"legal_domain": "Tax Law"}],
        ids=["test-1"],
        persist_dir=chroma_temp_dir,
    )

    collection = get_vectorstore(persist_dir=chroma_temp_dir)
    result = collection.get(ids=["test-1"], include=["metadatas"])
    meta = result["metadatas"][0]
    assert meta["source"] == "Taylor658/synthetic-legal"
    assert meta["is_synthetic"] == "true"

    vs._collection = None


def test_reset_collection(chroma_temp_dir):
    import factor.knowledge.vectorstore as vs
    vs._collection = None

    get_vectorstore(persist_dir=chroma_temp_dir)
    reset_collection(persist_dir=chroma_temp_dir)
    assert vs._collection is None
