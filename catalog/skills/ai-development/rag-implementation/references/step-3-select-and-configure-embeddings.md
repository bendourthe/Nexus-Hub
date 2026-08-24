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
