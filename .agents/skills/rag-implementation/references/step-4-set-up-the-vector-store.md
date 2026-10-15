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
