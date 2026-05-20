from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

# BM25 parameters
K1 = 1.5
B = 0.75

# Field weights for ranking
FIELD_WEIGHTS: dict[str, float] = {
    "name": 3.0,
    "title": 2.5,
    "tags": 2.0,
    "summary_l0": 1.5,
    "category": 1.5,
    "overview_l1": 1.0,
}

# Priority boost (additive after score normalization)
PRIORITY_BOOST: dict[str, float] = {
    "CRITICAL": 0.3,
    "HIGH": 0.15,
    "MEDIUM": 0.0,
}

STOP_WORDS = frozenset({
    "the", "a", "an", "is", "in", "for", "and", "or", "to", "of",
    "with", "on", "at", "by", "it", "its", "this", "that", "be",
    "are", "was", "were", "do", "does", "has", "have", "had",
})


@dataclass
class IndexedDocument:
    name: str
    fields: dict[str, list[str]]
    priority: str


@dataclass
class BM25Index:
    """BM25 search index over skill metadata fields."""

    _documents: list[IndexedDocument] = field(default_factory=list)
    _avg_lengths: dict[str, float] = field(default_factory=dict)
    _doc_freqs: dict[str, dict[str, int]] = field(default_factory=dict)
    _n_docs: int = 0

    def build(self, skills: list[dict]) -> None:
        """Build the BM25 index from skill metadata."""
        self._documents = []
        field_lengths: dict[str, list[int]] = {f: [] for f in FIELD_WEIGHTS}
        self._doc_freqs = {f: {} for f in FIELD_WEIGHTS}

        for skill in skills:
            doc_fields: dict[str, list[str]] = {}

            doc_fields["name"] = self.tokenize(skill.get("name", ""))
            doc_fields["title"] = self.tokenize(skill.get("title", ""))
            tags_str = " ".join(skill.get("tags", []))
            doc_fields["tags"] = self.tokenize(tags_str)
            doc_fields["summary_l0"] = self.tokenize(skill.get("summary_l0", skill.get("description", "")))
            doc_fields["category"] = self.tokenize(skill.get("category", ""))
            doc_fields["overview_l1"] = self.tokenize(skill.get("overview_l1", skill.get("long_description", "")))

            doc = IndexedDocument(
                name=skill["name"],
                fields=doc_fields,
                priority=skill.get("priority", "MEDIUM"),
            )
            self._documents.append(doc)

            for f_name in FIELD_WEIGHTS:
                tokens = doc_fields.get(f_name, [])
                field_lengths[f_name].append(len(tokens))
                seen = set(tokens)
                for token in seen:
                    self._doc_freqs[f_name][token] = self._doc_freqs[f_name].get(token, 0) + 1

        self._n_docs = len(self._documents)
        for f_name in FIELD_WEIGHTS:
            lengths = field_lengths[f_name]
            self._avg_lengths[f_name] = sum(lengths) / max(len(lengths), 1)

    def search(self, query: str, max_results: int = 5) -> list[tuple[str, float]]:
        """Search and return list of (skill_name, score) tuples."""
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores: dict[str, float] = {}

        for doc in self._documents:
            total_score = 0.0

            for f_name, weight in FIELD_WEIGHTS.items():
                doc_tokens = doc.fields.get(f_name, [])
                if not doc_tokens:
                    continue

                tf_map = Counter(doc_tokens)
                doc_len = len(doc_tokens)
                avg_len = self._avg_lengths.get(f_name, 1.0)

                field_score = 0.0
                for qt in query_tokens:
                    tf = tf_map.get(qt, 0)
                    if tf == 0:
                        continue

                    df = self._doc_freqs.get(f_name, {}).get(qt, 0)
                    idf = math.log((self._n_docs - df + 0.5) / (df + 0.5) + 1.0)

                    numerator = tf * (K1 + 1)
                    denominator = tf + K1 * (1 - B + B * doc_len / max(avg_len, 1e-6))
                    field_score += idf * (numerator / denominator)

                total_score += field_score * weight

            # Priority boost only applies when at least one query token matched.
            # Otherwise an unrelated query (e.g. "xyzzyplugh") would return every
            # high-priority doc with priority_boost as its score.
            if total_score > 0:
                total_score += PRIORITY_BOOST.get(doc.priority, 0.0)
                scores[doc.name] = total_score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:max_results]

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Lowercase, split on non-alphanumeric, remove stop words."""
        tokens = re.split(r"[^a-z0-9]+", text.lower())
        return [t for t in tokens if t and t not in STOP_WORDS]
