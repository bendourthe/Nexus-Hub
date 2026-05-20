---
name: rag-implementation
description: Retrieval-Augmented Generation implementation including document processing, chunking strategies, embedding, vector stores, and retrieval optimization. Use when building RAG pipelines, optimizing retrieval quality, or evaluating RAG systems.
summary_l0: "Implement RAG pipelines with chunking, embeddings, vector stores, and retrieval optimization"
overview_l1: "This skill provides end-to-end patterns for building Retrieval-Augmented Generation systems, from document ingestion through retrieval optimization to production deployment. Use it when building RAG pipelines from scratch, choosing and configuring vector databases, designing document chunking strategies, selecting embedding models, implementing hybrid retrieval (keyword plus semantic), optimizing retrieval quality with reranking, or evaluating RAG system performance. Key capabilities include document processing (PDF, HTML, code), chunking strategies (fixed-size, semantic, recursive), embedding model selection, vector store configuration, hybrid search implementation, reranking pipelines, and evaluation frameworks measuring faithfulness, relevance, and recall. The expected output is a production-ready RAG pipeline with optimized retrieval, caching, and cost controls. Trigger phrases: RAG pipeline, retrieval augmented generation, vector database, document chunking, embedding, semantic search, retrieval quality, vector store, document ingestion, reranking, hybrid search."
---

# RAG Implementation

End-to-end patterns for building Retrieval-Augmented Generation systems, from document ingestion through retrieval optimization to production deployment. Covers chunking strategies, embedding selection, vector store configuration, retrieval techniques, and evaluation frameworks.

## When to Use This Skill

Use this skill for:

- Building RAG pipelines from scratch
- Choosing and configuring vector databases
- Designing document chunking strategies
- Selecting and fine-tuning embedding models
- Implementing hybrid retrieval (keyword + semantic)
- Optimizing retrieval quality with reranking
- Evaluating RAG system performance (faithfulness, relevance, recall)
- Scaling RAG systems for production (caching, batching, cost control)

**Trigger phrases**: "RAG pipeline", "retrieval augmented generation", "vector database", "document chunking", "embedding", "semantic search", "retrieval quality", "vector store", "document ingestion", "reranking", "hybrid search"

## What This Skill Does

Provides RAG implementation expertise including:

- **Document Processing**: PDF, HTML, code, and structured data ingestion
- **Chunking Strategies**: Fixed-size, semantic, recursive, and document-aware splitting
- **Embedding Models**: OpenAI, Cohere, open-source model selection and tuning
- **Vector Databases**: Pinecone, Chroma, pgvector, Qdrant setup and optimization
- **Retrieval Strategies**: Similarity search, MMR, hybrid search, reranking
- **Prompt Construction**: Context injection, source attribution, citation patterns
- **Evaluation**: Faithfulness, answer relevance, context recall metrics
- **Production Considerations**: Caching, batching, incremental updates, cost management

## Instructions

### Step 1: Design the Document Ingestion Pipeline

Before building retrieval, you need clean, structured documents. The quality of ingested data determines the ceiling for retrieval quality.

**Document Loader Architecture**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """A single document with content and metadata."""
    content: str
    metadata: dict = field(default_factory=dict)
    source: str = ""
    doc_type: str = ""


class DocumentLoader(ABC):
    """Base class for document loaders."""

    @abstractmethod
    def load(self, source: str) -> list[Document]:
        ...


class PDFLoader(DocumentLoader):
    """Load and extract text from PDF files."""

    def load(self, source: str) -> list[Document]:
        import pymupdf  # PyMuPDF

        docs = []
        pdf = pymupdf.open(source)
        for page_num, page in enumerate(pdf):
            text = page.get_text("text")
            if text.strip():
                docs.append(Document(
                    content=text,
                    metadata={
                        "page": page_num + 1,
                        "total_pages": len(pdf),
                    },
                    source=source,
                    doc_type="pdf",
                ))
        pdf.close()
        return docs


class HTMLLoader(DocumentLoader):
    """Load and extract text from HTML, stripping boilerplate."""

    def load(self, source: str) -> list[Document]:
        from bs4 import BeautifulSoup
        import requests

        if source.startswith("http"):
            html = requests.get(source, timeout=30).text
        else:
            html = Path(source).read_text(encoding="utf-8")

        soup = BeautifulSoup(html, "html.parser")

        # Remove navigation, headers, footers, scripts
        for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        return [Document(
            content=text,
            metadata={"title": soup.title.string if soup.title else ""},
            source=source,
            doc_type="html",
        )]


class CodeLoader(DocumentLoader):
    """Load source code files with language-aware metadata."""

    LANGUAGE_MAP = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".go": "go", ".rs": "rust", ".java": "java", ".cs": "csharp",
    }

    def load(self, source: str) -> list[Document]:
        path = Path(source)
        content = path.read_text(encoding="utf-8")
        language = self.LANGUAGE_MAP.get(path.suffix, "unknown")

        return [Document(
            content=content,
            metadata={
                "language": language,
                "filename": path.name,
                "extension": path.suffix,
                "line_count": content.count("\n") + 1,
            },
            source=source,
            doc_type="code",
        )]
```

**Unified Ingestion Pipeline**:

```python
class IngestionPipeline:
    """Orchestrate document loading, cleaning, and chunking."""

    def __init__(self):
        self.loaders: dict[str, DocumentLoader] = {
            ".pdf": PDFLoader(),
            ".html": HTMLLoader(),
            ".htm": HTMLLoader(),
            ".py": CodeLoader(),
            ".js": CodeLoader(),
            ".ts": CodeLoader(),
        }

    def ingest(self, sources: list[str]) -> list[Document]:
        """Load and clean documents from multiple sources."""
        documents = []
        for source in sources:
            ext = Path(source).suffix.lower() if not source.startswith("http") else ".html"
            loader = self.loaders.get(ext)
            if loader is None:
                print(f"Skipping unsupported format: {ext}")
                continue

            docs = loader.load(source)
            for doc in docs:
                doc.content = self._clean(doc.content)
            documents.extend(docs)

        return documents

    def _clean(self, text: str) -> str:
        """Normalize whitespace and remove artifacts."""
        import re
        text = re.sub(r"\n{3,}", "\n\n", text)     # Collapse excess newlines
        text = re.sub(r"[ \t]{2,}", " ", text)      # Collapse excess spaces
        text = text.strip()
        return text
```

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

### Step 3: Select and Configure Embeddings

**Embedding Model Comparison**:

| Model | Dimensions | Speed | Quality | Cost |
|-------|-----------|-------|---------|------|
| `text-embedding-3-small` (OpenAI) | 1536 | Fast | Good | $0.02/1M tokens |
| `text-embedding-3-large` (OpenAI) | 3072 | Medium | Excellent | $0.13/1M tokens |
| `embed-english-v3.0` (Cohere) | 1024 | Fast | Excellent | $0.10/1M tokens |
| Code-specialized commercial families (VoyageAI, Google, and similar) | Typically 1024-3072 (some Matryoshka) | Fast | Excellent on code corpora | Metered |
| Ollama (`nomic-embed-text`, `mxbai-embed-large`, ...) | Typical 768 | Self-hosted | Good | Free (compute) |
| `BAAI/bge-large-en-v1.5` (open-source) | 1024 | Self-hosted | Very Good | Free (compute) |
| `nomic-embed-text-v1.5` (open-source) | 768 | Self-hosted | Good | Free (compute) |

**Code-Specialized Embeddings**:

When the corpus is source code rather than prose, prefer a code-specialized embedding model over a generic one: natural-language embeddings struggle with identifier tokens, operator sequences, and language-specific syntax that dominate code chunks. Code-specialized embedding families are available from commercial providers; local alternatives exist via Ollama and ONNX runtimes for environments where data cannot leave the network. In regulated environments the policy ordering is: (1) local ONNX / Ollama first, (2) commercial code-specialized families only if the vendor passes the MCP Registry Policy decision tree (see [AGENTS.md](../../../../AGENTS.md)).

**Embedding Client Implementation**:

```python
from abc import ABC, abstractmethod


class EmbeddingModel(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        ...


class OpenAIEmbedding(EmbeddingModel):
    def __init__(self, model: str = "text-embedding-3-small"):
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Batch in groups of 2048 (API limit)
        all_embeddings = []
        for i in range(0, len(texts), 2048):
            batch = texts[i:i + 2048]
            response = self.client.embeddings.create(input=batch, model=self.model)
            all_embeddings.extend([d.embedding for d in response.data])
        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]


class CohereEmbedding(EmbeddingModel):
    def __init__(self, model: str = "embed-english-v3.0"):
        import cohere
        self.client = cohere.ClientV2()
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embed(
            texts=texts,
            model=self.model,
            input_type="search_document",
            embedding_types=["float"],
        )
        return [list(e) for e in response.embeddings.float_]

    def embed_query(self, query: str) -> list[float]:
        response = self.client.embed(
            texts=[query],
            model=self.model,
            input_type="search_query",
            embedding_types=["float"],
        )
        return list(response.embeddings.float_[0])
```

### Step 4: Set Up the Vector Store

**Vector Store Comparison**:

| Store | Type | Scaling | Filtering | Best For |
|-------|------|---------|-----------|----------|
| **Chroma** | Embedded | Single node | Basic | Prototyping, small datasets |
| **Pinecone** | Managed cloud | Serverless | Rich | Production SaaS |
| **pgvector** | Postgres extension | Postgres scaling | SQL | Existing Postgres stacks |
| **Qdrant** | Self-hosted / cloud | Horizontal | Rich | High-performance production |
| **Milvus** | Self-hosted (gRPC + REST clients) | Horizontal | Rich | Open-source production vector DB; self-hostable in regulated environments |
| **FAISS** | In-process (library) | Single node | Basic | Local experimentation, embedded deployments where a daemon is undesirable |

**Chroma (Local Prototyping)**:

```python
import chromadb


def setup_chroma(collection_name: str = "documents"):
    """Initialize a local Chroma vector store."""
    client = chromadb.PersistentClient(path="./chroma_data")
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def index_chunks_chroma(collection, chunks: list[Chunk], embed_model: EmbeddingModel):
    """Index chunks into Chroma."""
    texts = [c.content for c in chunks]
    embeddings = embed_model.embed(texts)
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [c.metadata for c in chunks]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    print(f"Indexed {len(chunks)} chunks into Chroma.")


def search_chroma(
    collection,
    query: str,
    embed_model: EmbeddingModel,
    top_k: int = 5,
    where: dict | None = None,
) -> list[dict]:
    """Search Chroma for relevant chunks."""
    query_embedding = embed_model.embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    return [
        {
            "content": doc,
            "metadata": meta,
            "score": 1 - dist,  # Chroma returns distances; convert to similarity
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
```

**pgvector (Production with Postgres)**:

```python
import psycopg2
from pgvector.psycopg2 import register_vector


def setup_pgvector(conn_string: str, table: str = "documents", dimensions: int = 1536):
    """Initialize pgvector table and index."""
    conn = psycopg2.connect(conn_string)
    register_vector(conn)
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{{}}',
            embedding vector({dimensions})
        );
    """)
    cur.execute(f"""
        CREATE INDEX IF NOT EXISTS {table}_embedding_idx
        ON {table} USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    conn.commit()
    return conn


def index_chunks_pgvector(conn, chunks: list[Chunk], embed_model: EmbeddingModel):
    """Index chunks into pgvector."""
    import json
    texts = [c.content for c in chunks]
    embeddings = embed_model.embed(texts)
    cur = conn.cursor()

    for chunk, embedding in zip(chunks, embeddings):
        cur.execute(
            "INSERT INTO documents (content, metadata, embedding) VALUES (%s, %s, %s)",
            (chunk.content, json.dumps(chunk.metadata), embedding),
        )
    conn.commit()


def search_pgvector(
    conn, query: str, embed_model: EmbeddingModel, top_k: int = 5
) -> list[dict]:
    """Search pgvector for relevant chunks."""
    query_embedding = embed_model.embed_query(query)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT content, metadata, 1 - (embedding <=> %s::vector) AS score
        FROM documents
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (query_embedding, query_embedding, top_k),
    )
    return [
        {"content": row[0], "metadata": row[1], "score": row[2]}
        for row in cur.fetchall()
    ]
```

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

### Step 7: Evaluate RAG Quality

**Evaluation Metrics**:

| Metric | Measures | Range | Good Score |
|--------|----------|-------|------------|
| **Faithfulness** | Is the answer grounded in retrieved context? | 0-1 | > 0.85 |
| **Answer Relevance** | Does the answer address the question? | 0-1 | > 0.80 |
| **Context Recall** | Did retrieval find the relevant passages? | 0-1 | > 0.75 |
| **Context Precision** | Are retrieved passages relevant (low noise)? | 0-1 | > 0.70 |

**LLM-as-Judge Evaluation**:

```python
@dataclass
class RAGEvalResult:
    query: str
    faithfulness: float
    relevance: float
    context_recall: float
    overall: float


def evaluate_faithfulness(answer: str, context: str) -> float:
    """Score whether the answer is grounded in the provided context."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                "You are evaluating the faithfulness of an AI-generated answer.\n\n"
                f"Context:\n{context}\n\n"
                f"Answer:\n{answer}\n\n"
                "Score the answer on faithfulness (0.0 to 1.0):\n"
                "- 1.0: Every claim is supported by the context\n"
                "- 0.5: Some claims are supported, some are not\n"
                "- 0.0: The answer contradicts or fabricates beyond the context\n\n"
                "Respond with ONLY a JSON object: {\"score\": 0.X, \"reason\": \"...\"}"
            ),
        }],
    )
    import json
    result = json.loads(extract_text(response.content))
    return result["score"]


def evaluate_rag_system(
    test_cases: list[dict],
    rag_fn,
) -> list[RAGEvalResult]:
    """Run evaluation across a set of test queries."""
    results = []
    for case in test_cases:
        answer = rag_fn(case["query"])
        faithfulness = evaluate_faithfulness(answer, case.get("expected_context", ""))
        relevance = evaluate_relevance(answer, case["query"])
        context_recall = evaluate_context_recall(
            case.get("expected_passages", []),
            case.get("retrieved_passages", []),
        )

        results.append(RAGEvalResult(
            query=case["query"],
            faithfulness=faithfulness,
            relevance=relevance,
            context_recall=context_recall,
            overall=(faithfulness + relevance + context_recall) / 3,
        ))

    avg = lambda field: sum(getattr(r, field) for r in results) / len(results)
    print(f"\nRAG Evaluation Summary ({len(results)} cases):")
    print(f"  Faithfulness:    {avg('faithfulness'):.2f}")
    print(f"  Relevance:       {avg('relevance'):.2f}")
    print(f"  Context Recall:  {avg('context_recall'):.2f}")
    print(f"  Overall:         {avg('overall'):.2f}")

    return results
```

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

## Best Practices

- **Chunk size matters**: Start with 512 tokens, tune based on evaluation results; smaller chunks improve precision, larger chunks preserve context
- **Overlap prevents boundary loss**: Use 10-20% overlap to avoid splitting critical information across chunks
- **Embed queries differently**: Some models (Cohere) distinguish document vs. query embeddings; use the correct input type
- **Reranking is high ROI**: A reranker on top of basic retrieval often delivers more improvement than switching embedding models
- **Filter before searching**: Use metadata filters (date, source, document type) to narrow the search space
- **Measure before optimizing**: Establish baseline metrics with evaluation before tuning chunking, embeddings, or retrieval
- **Cache embeddings**: Embedding the same document twice is wasted compute; cache aggressively
- **Monitor retrieval drift**: Document collections change over time; re-evaluate periodically
- **Keep context concise**: More retrieved chunks does not always mean better answers; 3-5 high-quality chunks often outperform 10+ noisy ones
- **Attribute sources**: Always pass source metadata through to the final answer for traceability

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

## Quality Checklist

- [ ] Document loaders handle target formats (PDF, HTML, code, etc.)
- [ ] Chunking strategy chosen and tuned for document type and query patterns
- [ ] Embedding model selected with cost/quality trade-off justified
- [ ] Vector store configured with appropriate index type and distance metric
- [ ] Retrieval strategy tested (similarity, MMR, hybrid, reranking)
- [ ] Prompt template injects context with source attribution
- [ ] Evaluation suite measures faithfulness, relevance, and recall
- [ ] Caching in place for embeddings and frequent queries
- [ ] Incremental indexing handles document updates without full re-index
- [ ] Production monitoring tracks retrieval latency, cost, and quality drift

## Related Skills

- `ai-agent-development` - Building agents that use RAG as a tool
- `prompt-engineering` - Designing prompts for RAG answer generation
- `sql-expert` - Using pgvector with existing Postgres databases
- `performance-testing` - Load testing RAG retrieval endpoints

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
