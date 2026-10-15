### Step 2: Choose and Implement a Chunking Strategy

Chunking determines what units of text the retriever can find. The right strategy depends on document structure and query patterns.

**Chunking Strategy Comparison**:

| Strategy | Best For | Pros | Cons |
|----------|----------|------|------|
| **Fixed-size** | Uniform documents | Simple, predictable | Splits mid-sentence |
| **Recursive** | Prose documents | Respects hierarchy | Needs separator tuning |
| **Semantic** | Mixed-format docs | Meaning-preserving | Slower, needs embeddings |
| **Document-aware** | Structured docs (code, markdown) | Preserves structure | Format-specific logic |
| **AST-aware** | Source code corpora | Preserves function/class boundaries | Needs per-language grammar; falls back to recursive for unsupported languages |

**AST-Aware Chunking for Source Code**:

Character-based splitters shred function and class bodies across chunk boundaries, which degrades retrieval quality on code-specific queries because the dense vector for the fragment stops representing the original unit. An AST-aware splitter walks the parse tree and emits one chunk per function, method, or class, preserving the semantic unit the embedder is supposed to vectorize. `tree-sitter` supports AST-based chunking across common languages including Python, TypeScript, JavaScript, Go, Rust, Java, C++, C#, and Scala; for file types without an AST grammar, fall back to a recursive character splitter with language-aware separators. Adopt this layered approach whenever the corpus is code: AST for supported languages, recursive for the long tail.

**Incremental Re-Indexing with Content-Hash Merkle Trees**:

Re-embedding an entire corpus on every commit is wasteful - most files do not change between commits, and embedding costs (both dollars and latency) compound quickly. The standard pattern is a **content-hash Merkle tree** over the file set: each leaf is a file-hash, interior nodes aggregate children, and the root fingerprints the whole corpus. On change, diff the old and new trees to identify the leaves that actually changed, and re-embed only the chunks under those leaves. Implemented correctly, this cuts re-index cost to the delta on every commit regardless of repo size. For non-code corpora the same pattern works with document-level hashes; the only requirement is that the chunk-to-source mapping is stable so you can invalidate precisely the chunks whose source changed. The Nexus-Hub internal `nexus-code-search` MCP ships a flat content-hash manifest in v1.0.0 and upgrades to a directory-keyed Merkle tree in v1.1.0 for larger repositories.

**Fixed-Size Chunking with Overlap**:

```python
@dataclass
class Chunk:
    """A chunk of text with provenance metadata."""
    content: str
    metadata: dict = field(default_factory=dict)
    chunk_index: int = 0


def fixed_size_chunk(
    doc: Document,
    chunk_size: int = 512,
    overlap: int = 64,
) -> list[Chunk]:
    """Split document into fixed-size token chunks with overlap."""
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(doc.content)
    chunks = []

    start = 0
    idx = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)

        chunks.append(Chunk(
            content=chunk_text,
            metadata={**doc.metadata, "source": doc.source, "chunk_method": "fixed"},
            chunk_index=idx,
        ))
        idx += 1
        start += chunk_size - overlap

    return chunks
```

**Recursive Character Splitting**:

```python
def recursive_chunk(
    doc: Document,
    chunk_size: int = 1000,
    overlap: int = 200,
    separators: list[str] | None = None,
) -> list[Chunk]:
    """Split text recursively using a hierarchy of separators."""
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]

    def _split(text: str, seps: list[str]) -> list[str]:
        if not seps:
            return [text]

        sep = seps[0]
        remaining_seps = seps[1:]

        if sep == "":
            # Character-level split as last resort
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

        parts = text.split(sep)
        chunks_out = []
        current = ""

        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks_out.append(current)
                if len(part) > chunk_size:
                    # Recurse with finer separators
                    chunks_out.extend(_split(part, remaining_seps))
                else:
                    current = part

        if current:
            chunks_out.append(current)

        return chunks_out

    raw_chunks = _split(doc.content, separators)

    return [
        Chunk(
            content=text,
            metadata={**doc.metadata, "source": doc.source, "chunk_method": "recursive"},
            chunk_index=i,
        )
        for i, text in enumerate(raw_chunks)
        if text.strip()
    ]
```

**Semantic Chunking (Embedding-Based Boundary Detection)**:

```python
import numpy as np


def semantic_chunk(
    doc: Document,
    embed_fn,
    similarity_threshold: float = 0.75,
    min_chunk_size: int = 100,
) -> list[Chunk]:
    """Split text at semantic boundaries detected by embedding similarity."""
    sentences = split_into_sentences(doc.content)
    if len(sentences) <= 1:
        return [Chunk(content=doc.content, metadata=doc.metadata, chunk_index=0)]

    # Embed each sentence
    embeddings = embed_fn([s for s in sentences])

    # Find breakpoints where consecutive sentence similarity drops
    breakpoints = []
    for i in range(len(embeddings) - 1):
        sim = cosine_similarity(embeddings[i], embeddings[i + 1])
        if sim < similarity_threshold:
            breakpoints.append(i + 1)

    # Build chunks from breakpoints
    chunks = []
    start = 0
    for bp in breakpoints:
        chunk_text = " ".join(sentences[start:bp])
        if len(chunk_text) >= min_chunk_size:
            chunks.append(chunk_text)
            start = bp

    # Add remaining text
    remaining = " ".join(sentences[start:])
    if remaining.strip():
        chunks.append(remaining)

    return [
        Chunk(
            content=text,
            metadata={**doc.metadata, "source": doc.source, "chunk_method": "semantic"},
            chunk_index=i,
        )
        for i, text in enumerate(chunks)
    ]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))
```
