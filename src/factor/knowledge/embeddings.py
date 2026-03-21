"""Embedding generation for the knowledge base."""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class EmbeddingFunction(Protocol):
    """Protocol for embedding functions compatible with ChromaDB."""

    def __call__(self, input: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbeddings:
    """Embeddings using sentence-transformers library."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        logger.info("Loaded embedding model: %s", model_name)

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(input, show_progress_bar=False)
        return embeddings.tolist()


class BedrockEmbeddings:
    """Embeddings using Amazon Bedrock Titan."""

    def __init__(
        self,
        model_id: str = "amazon.titan-embed-text-v2:0",
        region_name: str = "us-west-2",
    ):
        import boto3

        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.model_id = model_id
        logger.info("Initialized Bedrock embeddings: %s", model_id)

    def __call__(self, input: list[str]) -> list[list[float]]:
        import json

        embeddings = []
        for text in input:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({"inputText": text[:8000]}),
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            embeddings.append(result["embedding"])
        return embeddings


def get_embedding_function(backend: str = "sentence-transformers") -> EmbeddingFunction:
    """Get the configured embedding function.

    Args:
        backend: Either 'sentence-transformers' or 'bedrock'.

    Returns:
        An embedding function compatible with ChromaDB.
    """
    if backend == "bedrock":
        return BedrockEmbeddings()
    return SentenceTransformerEmbeddings()
