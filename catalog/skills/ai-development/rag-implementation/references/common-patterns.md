## Common Patterns

### Pattern 1: Parent-Child Chunking

Store small chunks for precise retrieval but return the surrounding parent chunk (or full section) for richer context.

```python
def parent_child_chunk(doc: Document, child_size: int = 256, parent_size: int = 1024):
    """Create small retrieval chunks linked to larger context chunks."""
    parents = fixed_size_chunk(doc, chunk_size=parent_size, overlap=0)
    children = []

    for parent_idx, parent in enumerate(parents):
        parent_doc = Document(content=parent.content, metadata=parent.metadata)
        kids = fixed_size_chunk(parent_doc, chunk_size=child_size, overlap=32)
        for kid in kids:
            kid.metadata["parent_index"] = parent_idx
        children.extend(kids)

    return parents, children
```

### Pattern 2: Query Expansion

Rephrase the user query multiple ways to improve recall.

```python
def expand_query(query: str, num_variants: int = 3) -> list[str]:
    """Generate query variants for broader retrieval."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                f"Generate {num_variants} alternative phrasings of this search query. "
                "Each should capture the same intent but use different words.\n\n"
                f"Query: {query}\n\n"
                "Output one variant per line, no numbering."
            ),
        }],
    )
    variants = extract_text(response.content).strip().split("\n")
    return [query] + [v.strip() for v in variants if v.strip()]
```

### Pattern 3: Metadata-Enriched Retrieval

Add generated metadata (summaries, keywords, questions) to chunks for richer retrieval signals.

```python
def enrich_chunk_metadata(chunk: Chunk) -> Chunk:
    """Add LLM-generated metadata to a chunk for improved retrieval."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                "For the following text, generate:\n"
                "1. A one-sentence summary\n"
                "2. 3-5 keywords\n"
                "3. 2 questions this text could answer\n\n"
                f"Text: {chunk.content[:1000]}\n\n"
                'Output as JSON: {"summary": "...", "keywords": [...], "questions": [...]}'
            ),
        }],
    )
    import json
    enrichment = json.loads(extract_text(response.content))
    chunk.metadata.update(enrichment)
    return chunk
```
