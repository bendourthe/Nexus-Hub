### Step 5: Implement Retrieval Strategies

**Basic Similarity Search vs. Advanced Strategies**:

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| **Similarity** | Nearest-neighbor by embedding distance | Default starting point |
| **MMR** | Maximal Marginal Relevance (relevance + diversity) | When results are too similar |
| **Hybrid** | Combine keyword (BM25) + semantic search | When exact terms matter |
| **Reranking** | Two-stage: retrieve broadly, rerank precisely | Quality-critical applications |

**Maximal Marginal Relevance (MMR)**:

```python
def mmr_search(
    query_embedding: list[float],
    candidate_embeddings: list[list[float]],
    candidate_docs: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """Select diverse results balancing relevance and novelty."""
    selected = []
    remaining = list(range(len(candidate_docs)))

    for _ in range(min(top_k, len(candidate_docs))):
        best_score = -float("inf")
        best_idx = -1

        for idx in remaining:
            # Relevance to query
            relevance = cosine_similarity(query_embedding, candidate_embeddings[idx])

            # Maximum similarity to already-selected documents
            if selected:
                max_sim = max(
                    cosine_similarity(candidate_embeddings[idx], candidate_embeddings[s])
                    for s in selected
                )
            else:
                max_sim = 0.0

            # MMR score: balance relevance against redundancy
            score = lambda_param * relevance - (1 - lambda_param) * max_sim

            if score > best_score:
                best_score = score
                best_idx = idx

        selected.append(best_idx)
        remaining.remove(best_idx)

    return [candidate_docs[i] for i in selected]
```

**Hybrid Search (Keyword + Semantic)**:

```python
def hybrid_search(
    query: str,
    vector_results: list[dict],
    keyword_results: list[dict],
    alpha: float = 0.6,
    top_k: int = 5,
) -> list[dict]:
    """Combine vector similarity and keyword (BM25) scores using RRF."""
    # Reciprocal Rank Fusion
    rrf_scores: dict[str, float] = {}
    k = 60  # RRF constant

    for rank, doc in enumerate(vector_results):
        doc_id = doc["metadata"].get("source", "") + str(doc.get("chunk_index", rank))
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + alpha / (k + rank + 1)
        doc["_id"] = doc_id

    for rank, doc in enumerate(keyword_results):
        doc_id = doc["metadata"].get("source", "") + str(doc.get("chunk_index", rank))
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + (1 - alpha) / (k + rank + 1)
        doc["_id"] = doc_id

    # Merge and sort by combined score
    all_docs = {d["_id"]: d for d in vector_results + keyword_results}
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    return [all_docs[doc_id] for doc_id, _ in ranked[:top_k] if doc_id in all_docs]
```

**Hybrid Retrieval in Practice**:

Hybrid BM25 + dense retrieval with a reranking stage is the production pattern for agent-grade code retrieval: keyword matches catch identifier-exact queries that dense vectors smear, while dense retrieval catches natural-language intent that BM25 misses. The standard stack is a BM25 inverted index, dense embeddings over AST-aware or recursive chunks, reciprocal-rank fusion to combine the two rankings, and an optional cross-encoder rerank on the top-K survivors. On real agent workloads this stack consistently outperforms grep baselines on both token consumption and tool-call counts, because the ranked chunk set the agent reads is an order of magnitude smaller than a broad grep response while still containing the relevant code. Nexus-Hub's reverse-engineered local equivalent is the `nexus-code-search` MCP under [`extensions/nexus-code-search/`](../../../../extensions/nexus-code-search/) - v1.0.0 ships the BM25 / keyword tier, and v1.1.0 adds the dense and hybrid tiers with a fully local embedding backend.

**Two-Stage Reranking**:

```python
def rerank_results(
    query: str,
    results: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Rerank initial retrieval results using a cross-encoder model."""
    import cohere

    co = cohere.ClientV2()

    documents = [r["content"] for r in results]
    response = co.rerank(
        query=query,
        documents=documents,
        model="rerank-english-v3.0",
        top_n=top_k,
    )

    reranked = []
    for hit in response.results:
        result = results[hit.index].copy()
        result["rerank_score"] = hit.relevance_score
        reranked.append(result)

    return reranked
```
