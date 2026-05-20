from __future__ import annotations

import logging

from nexus_skill_server.config import ServerConfig
from nexus_skill_server.search_keyword import BM25Index

logger = logging.getLogger("nexus-skill-server")


class SearchEngine:
    """Unified search interface. Uses BM25 keyword search by default."""

    def __init__(self, config: ServerConfig) -> None:
        self._config = config
        self._keyword_index = BM25Index()
        self._embedding_search = None

    def build_index(self, skills: list[dict], catalog_version: str) -> None:
        """Build the keyword index (always) and embedding index (if configured)."""
        self._keyword_index.build(skills)
        logger.info("BM25 keyword index built with %d documents", len(skills))

        if self._config.embedding_provider != "none":
            self._try_init_embeddings(skills, catalog_version)

    def search(self, query: str, max_results: int = 5) -> list[tuple[str, float]]:
        """Dispatch to the active search backend."""
        if self._embedding_search is not None:
            try:
                return self._embedding_search.search(query, max_results)
            except Exception:
                logger.warning("Embedding search failed, falling back to keyword", exc_info=True)

        return self._keyword_index.search(query, max_results)

    def _try_init_embeddings(self, skills: list[dict], catalog_version: str) -> None:
        """Attempt to initialize embedding search. Fails silently to keyword fallback."""
        provider = self._config.embedding_provider
        logger.info("Embedding provider configured: %s (not yet implemented, using keyword search)", provider)
        # Embedding search will be implemented in v0.2.
        # When ready, import search_embedding and initialize here.
