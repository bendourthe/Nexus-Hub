### Step 6: Construct Prompts with Retrieved Context

**Context Injection Pattern**:

```python
def build_rag_prompt(
    query: str,
    retrieved_chunks: list[dict],
    system_instructions: str = "",
) -> list[dict]:
    """Build a prompt with retrieved context for the LLM."""
    context_block = "\n\n---\n\n".join(
        f"Source: {chunk['metadata'].get('source', 'unknown')}\n"
        f"{chunk['content']}"
        for chunk in retrieved_chunks
    )

    system = (
        f"{system_instructions}\n\n"
        "Answer the user's question using ONLY the provided context. "
        "If the context does not contain enough information to answer, "
        "say so explicitly rather than guessing.\n\n"
        "When citing information, reference the source document.\n\n"
        f"Context:\n{context_block}"
    )

    return {
        "system": system,
        "messages": [{"role": "user", "content": query}],
    }
```

**Full RAG Query Pipeline**:

```python
import anthropic


def rag_query(
    query: str,
    collection,
    embed_model: EmbeddingModel,
    top_k: int = 5,
    rerank: bool = True,
) -> str:
    """Execute a complete RAG query: retrieve, rerank, generate."""
    # Stage 1: Retrieve
    results = search_chroma(collection, query, embed_model, top_k=top_k * 3)

    # Stage 2: Rerank (optional)
    if rerank and len(results) > top_k:
        results = rerank_results(query, results, top_k=top_k)
    else:
        results = results[:top_k]

    # Stage 3: Generate
    prompt = build_rag_prompt(query, results)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=prompt["system"],
        messages=prompt["messages"],
    )

    return extract_text(response.content)
```
