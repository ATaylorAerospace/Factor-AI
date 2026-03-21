"""Knowledge base — synthetic legal dataset loading, embedding, and retrieval."""

from factor.knowledge.loader import load_synthetic_dataset
from factor.knowledge.vectorstore import get_vectorstore

__all__ = ["load_synthetic_dataset", "get_vectorstore"]
