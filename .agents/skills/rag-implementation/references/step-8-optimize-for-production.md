### Step 8: Optimize for Production

**Caching Strategy**:

```python
import hashlib
import json
from datetime import datetime, timedelta


class EmbeddingCache:
    """Cache embeddings to avoid recomputing for identical text."""

    def __init__(self, store: dict | None = None, ttl_hours: int = 168):
        self.store = store or {}
        self.ttl = timedelta(hours=ttl_hours)

    def _key(self, text: str, model: str) -> str:
        return hashlib.sha256(f"{model}:{text}".encode()).hexdigest()

    def get(self, text: str, model: str) -> list[float] | None:
        key = self._key(text, model)
        entry = self.store.get(key)
        if entry and datetime.utcnow() - entry["ts"] < self.ttl:
            return entry["embedding"]
        return None

    def put(self, text: str, model: str, embedding: list[float]):
        key = self._key(text, model)
        self.store[key] = {"embedding": embedding, "ts": datetime.utcnow()}


class CachedEmbedding(EmbeddingModel):
    """Wrapper that caches embeddings from any EmbeddingModel."""

    def __init__(self, inner: EmbeddingModel, cache: EmbeddingCache):
        self.inner = inner
        self.cache = cache
        self.model_name = getattr(inner, "model", "default")

    def embed(self, texts: list[str]) -> list[list[float]]:
        results = [None] * len(texts)
        uncached_indices = []

        for i, text in enumerate(texts):
            cached = self.cache.get(text, self.model_name)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)

        if uncached_indices:
            uncached_texts = [texts[i] for i in uncached_indices]
            new_embeddings = self.inner.embed(uncached_texts)
            for idx, emb in zip(uncached_indices, new_embeddings):
                results[idx] = emb
                self.cache.put(texts[idx], self.model_name, emb)

        return results

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]
```

**Incremental Indexing**:

```python
class IncrementalIndexer:
    """Track which documents have been indexed and only process new or changed ones."""

    def __init__(self, state_file: str = ".rag_index_state.json"):
        self.state_file = Path(state_file)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"indexed": {}}

    def _save_state(self):
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def needs_indexing(self, source: str) -> bool:
        """Check if a source needs (re-)indexing based on modification time."""
        import os
        mtime = os.path.getmtime(source)
        prev = self.state["indexed"].get(source)
        return prev is None or prev < mtime

    def mark_indexed(self, source: str):
        import os
        self.state["indexed"][source] = os.path.getmtime(source)
        self._save_state()
```
