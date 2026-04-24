"""Keyword search over a chunk corpus.

Approach: build an inverted index from tokens -> chunk IDs. On query,
tokenize, compute a score per candidate chunk from (a) token overlap
(intersection size) and (b) a rapidfuzz fuzzy ratio between the full
query text and each candidate's text, and return top-K.

No network. No ML. No model download.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from devai_code_search.types import Chunk, SearchResult

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}")
_SUBTOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")


def _tokenize(text: str) -> list[str]:
    """Lowercase tokens.

    For each identifier-like token, emit both the full lowercased form AND
    its underscore-split subparts (length >= 2). This lets a query for
    `user` match `user_id`, `find_user`, etc. - standard for code search.
    """
    tokens: list[str] = []
    for m in _TOKEN_RE.finditer(text):
        full = m.group(0).lower()
        tokens.append(full)
        if "_" in full:
            for part in _SUBTOKEN_RE.findall(full):
                if len(part) >= 2:
                    tokens.append(part)
    return tokens


@dataclass
class KeywordIndex:
    """In-memory inverted index over a chunk corpus."""

    chunks: list[Chunk]
    tokens_per_chunk: list[set[str]] = field(default_factory=list)
    postings: dict[str, set[int]] = field(default_factory=dict)

    @classmethod
    def build(cls, chunks: list[Chunk]) -> KeywordIndex:
        idx = cls(chunks=chunks, tokens_per_chunk=[], postings={})
        for cid, chunk in enumerate(chunks):
            toks = set(_tokenize(chunk.text))
            idx.tokens_per_chunk.append(toks)
            for tok in toks:
                idx.postings.setdefault(tok, set()).add(cid)
        return idx

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not query.strip() or not self.chunks:
            return []
        if limit <= 0:
            return []

        qtokens = set(_tokenize(query))
        candidates: set[int] = set()
        for tok in qtokens:
            candidates.update(self.postings.get(tok, set()))

        # If no exact token match, fall back to scanning all chunks with fuzzy ratio only.
        if not candidates:
            candidates = set(range(len(self.chunks)))

        scored: list[tuple[int, float]] = []
        for cid in candidates:
            overlap = len(qtokens & self.tokens_per_chunk[cid])
            fuzz_score = fuzz.token_set_ratio(query, self.chunks[cid].text) / 100.0
            # Weight overlap heavily; fuzzy as a tiebreaker.
            score = overlap * 1.0 + fuzz_score * 0.5
            if score > 0:
                scored.append((cid, score))

        scored.sort(key=lambda pair: pair[1], reverse=True)
        top = scored[:limit]
        return [
            SearchResult(chunk=self.chunks[cid], score=round(score, 4), rank=rank + 1)
            for rank, (cid, score) in enumerate(top)
        ]
