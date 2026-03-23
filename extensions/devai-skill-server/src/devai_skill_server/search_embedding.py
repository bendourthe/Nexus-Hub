"""Optional embedding-based search providers (v0.2 placeholder).

This module defines the interface for embedding providers. Implementations
will be added in a future version. The search engine falls back to BM25
keyword search when no embedding provider is available.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of embedding vectors."""
        ...

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Embed a single query. Returns embedding vector."""
        ...


class EmbeddingSearch:
    """Semantic search using embeddings with cosine similarity (v0.2 placeholder)."""

    def __init__(self, provider: EmbeddingProvider) -> None:
        self._provider = provider

    def build(self, skills: list[dict], catalog_version: str) -> None:
        raise NotImplementedError("Embedding search will be implemented in v0.2")

    def search(self, query: str, max_results: int = 5) -> list[tuple[str, float]]:
        raise NotImplementedError("Embedding search will be implemented in v0.2")
