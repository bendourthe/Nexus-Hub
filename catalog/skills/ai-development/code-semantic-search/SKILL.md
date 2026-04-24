---
name: code-semantic-search
description: Semantic search over source-code corpora using code-specialized embeddings, AST-aware chunking, and hybrid BM25+dense retrieval with incremental re-indexing
summary_l0: "Retrieve relevant code from large repositories using hybrid semantic search and AST-aware chunking"
overview_l1: "This skill covers semantic search specifically for source-code corpora, which differs from general RAG in three ways: code-specialized embedding models outperform generic text embeddings on identifier-heavy queries; AST-aware chunking preserves function and class boundaries that character-based splitters shred; and incremental re-indexing via content-hash or Merkle trees avoids re-embedding unchanged subtrees on each commit. Use this skill when the agent must answer questions about a codebase larger than the model's context window, when grep or ripgrep produces too many false positives for natural-language queries, or when a team wants to eliminate 'where do we handle X?' spelunking. Under the MCP Registry Policy the reference implementation is DevAI-Hub's internal devai-code-search MCP - keyword-only in v1.0.0, hybrid retrieval planned for v1.1.0 with local ONNX embeddings and a sqlite-vec vector store. Third-party semantic-code-search services are drop-class under the policy because their default flow ships source code to an external embedding endpoint."
version: 1.0.0
author: Benjamin Dourthe
category: ai-development
language: Multi-language
tags: [rag, retrieval, embeddings, code-search, mcp, ast-chunking, incremental-indexing]
tools_required: [Read, Glob, Grep, Bash]
---

# Code Semantic Search

Semantic search over source-code corpora. This skill is the specialized sibling of the general-purpose `rag-implementation` skill: same RAG mental model, but adapted for the three properties that make code corpora different from prose corpora.

DevAI-Hub's reference implementation is the internal [`devai-code-search`](../../../../extensions/devai-code-search/) MCP. v1.0.0 ships keyword-only search (inverted index + rapidfuzz, zero API keys, zero model downloads, zero outbound calls). v1.1.0 adds dense retrieval with local ONNX embeddings and a sqlite-vec vector store. Under the MCP Registry Policy in `AGENTS.md`, third-party semantic-code-search services are drop-class because their default flow ships source code to an external embedding endpoint.

## When to Use This Skill

Use this skill when:

- The agent must answer questions about a codebase that exceeds the model's context window. Loading the full tree is not an option; retrieval is.
- Natural-language queries about the code ("where do we handle rate limiting for the billing endpoint?") are the dominant access pattern, and grep would return too many false positives.
- The team wants to eliminate "spelunking through the repo" as a recurring task before code reviews, onboarding, or incident response.
- A new feature needs to cite existing implementations of similar patterns in the codebase.
- You are planning a refactor that needs to find every caller of a function whose exact name you do not remember.

**When NOT to use**:

- The codebase fits in the model's context window. Direct reads are faster and higher-fidelity than any retrieval - indexing overhead is not free.
- The query is about a single identifier whose exact spelling is known. `grep` / `Grep` is faster and cheaper.
- The query is about the user's runtime state (a specific error, a specific failing test, a specific database row). Use the relevant debugging or observability skills instead.
- The project ships no more than a handful of files. The overhead of indexing and maintaining an index exceeds the benefit.

## Instructions

### Step 1: Choose the embedding strategy

Under the MCP Registry Policy decision tree in [`AGENTS.md`](../../../../AGENTS.md), the preference order for embedding backends is:

1. **Local ONNX / self-hosted Ollama** - zero outbound calls, zero API keys. DevAI-Hub's `devai-code-search` will ship an ONNX embedding backend in v1.1.0. In regulated environments this is the only acceptable option.
2. **Commercial code-specialized embedding provider via your-own-account** - acceptable only if the vendor passes all three conditions of the decision tree (intrinsic destination, non-RE'able, extremely worth it). Most projects do not meet the third condition; skip this tier unless you have explicitly justified it in writing.
3. **Anything else** - drop.

Code-specialized embedding families outperform generic prose embeddings on identifier-heavy queries because they have been trained on code tokens (snake_case, camelCase, language keywords). When using a local model, prefer one trained on a corpus that includes code (standard ONNX embedding models like `bge-small-en` work acceptably; code-fine-tuned variants work better at the cost of larger model files).

### Step 2: Choose the chunking strategy

| Strategy | When to use |
|---|---|
| **AST-aware** | Any language with a tree-sitter grammar (Python, TypeScript, JavaScript, Go, Rust, Java, C++, C#, Scala, and more). Walk the parse tree; emit one chunk per function, method, or class. Preserves semantic units the embedder expects to vectorize. |
| **Recursive character splitter with language separators** | Long-tail languages without a tree-sitter grammar, or configurations where a tree-sitter runtime is not available (e.g. restricted wheels-only install on Windows). Prefer separators: `\n\nclass `, `\n\ndef `, `\nfunction `, `\npublic `, `\n\n`, `\n`. 600-char target window, 80-char overlap works well for most code. |
| **Fixed-size with overlap** | Emergency fallback only. Do not ship this in production. |

DevAI-Hub's `devai-code-search` ships the recursive character splitter with language separators in v1.0.0 to keep the install path wheels-only on Windows; v1.1.0 adds tree-sitter starting with Python.

### Step 3: Choose the vector store

Under the policy, the store must be local and self-hostable. Acceptable options:

- **In-process**: sqlite-vec (SQLite + vector extension, single-file), FAISS (library, numpy-backed), Chroma (embedded mode).
- **Self-hosted daemon**: Milvus (open-source, heavier), Qdrant (open-source), pgvector (if the team already runs Postgres).
- **Not acceptable under the policy**: any managed vector-DB service (Pinecone and similar hosted offerings from the Milvus / Qdrant / other-open-source ecosystems).

For a v1.0.0-style MVP, prefer in-process. DevAI-Hub's `devai-code-search` uses sqlite-vec in v1.1.0 because it ships prebuilt Windows wheels and needs no daemon.

### Step 4: Wire up hybrid retrieval

Hybrid BM25 + dense retrieval consistently outperforms either alone:

- BM25 catches identifier-exact matches that dense vectors smear (e.g. `compute_total` matches `compute_total` but a dense vector may rank a semantically-similar `calculate_sum` above it).
- Dense retrieval catches natural-language intent that BM25 misses (e.g. "how is rate limiting implemented" matches a `RateLimiter` class body that does not contain the phrase "rate limiting").

Combine the two rankings with **reciprocal rank fusion (RRF)**:

```
rrf_score(doc) = sum over each ranker of 1 / (k + rank_of_doc_in_ranker)
```

Typical `k = 60`. Sort by `rrf_score` descending, take the top K. Optionally rerank the top-K with a cross-encoder for higher precision at the cost of latency.

### Step 5: Incremental re-indexing

Re-embedding the entire corpus on every commit is wasteful - most files do not change. Maintain a **content-hash manifest** per file:

- SHA-256 each file on first index; store in the manifest.
- On re-index, hash each file again; skip unchanged ones; re-chunk modified ones; drop entries for deleted files.

For very large repos, upgrade the flat manifest to a directory-keyed Merkle tree so entire subtrees can be skipped when no descendant changed. DevAI-Hub's `devai-code-search` ships the flat manifest in v1.0.0 and upgrades in v1.1.0.

### Step 6: Rerank strategies

After RRF, the top 20-50 candidates can be reranked for higher precision:

- **Cross-encoder rerank**: a smaller transformer that scores (query, chunk) pairs directly. Slower than bi-encoder retrieval but more precise. Use `bge-reranker-base` or similar ONNX-compatible model locally.
- **Rule-based rerank**: boost chunks whose file path matches the query intent (e.g. query mentions "auth" and the chunk lives in `src/auth/`), or chunks with more comment density (well-documented code tends to be more canonical).
- **LLM-assisted rerank**: ask the agent to score each candidate on relevance. Costs more per query; use only for small top-K.

### Step 7: Common pitfalls

- **Stale indexes after merges or rebases** - incremental indexing must run on the post-merge tree, not the pre-merge working copy.
- **Chunk-size misconfiguration causing token-limit overruns** - 600-char chunks with 80-char overlap fit well within any model's context; 4000-char chunks can overflow when stacked.
- **Embedding cost at first index** - one-time, but can be significant. For a 10k-file repo with local models, budget 5-15 minutes on CPU.
- **Language-coverage gaps in AST splitters** - tree-sitter does not cover every language. Always ship a recursive character splitter fallback.
- **Query drift over time** - what was semantic six months ago may be noise now. Periodic eval on a fixed query set catches degradation.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "grep is fast enough" | grep returns 200 lines for "payment processing"; the agent still has to read each to filter. Semantic search returns 5 chunks ranked by relevance. The cost difference compounds per query. |
| "We do not need AST chunking; the recursive splitter is fine" | Character splitters shred function bodies across chunk boundaries. The dense vector for the fragment stops representing the function and retrieval quality collapses on identifier-heavy queries. Use recursive AS A FALLBACK, not as the default for languages with AST support. |
| "We will re-index on every commit" | Re-embedding 50 MB of TypeScript with a commercial embedding endpoint costs roughly $2 per run and takes 3-10 minutes. Content-hash or Merkle diffing cuts the cost to the delta. |
| "A managed vector-DB service is easier" | It is, right until the day your source code starts going to a third party at index time. The MCP Registry Policy classifies that as drop-class. Local stores (sqlite-vec, FAISS, Chroma in-process) are not significantly harder to operate. |

## Verification

- [ ] The chosen embedding strategy is documented, and either the backend is local (ONNX, Ollama) or the vendor-intrinsic justification is written.
- [ ] The chosen chunking strategy is AST-aware for every language with tree-sitter support, with a recursive character splitter configured as fallback.
- [ ] The vector store is local (in-process or self-hosted daemon); no managed vendor service is used.
- [ ] Hybrid retrieval (BM25 + dense, RRF-combined) is in place.
- [ ] Incremental re-indexing is enabled; SHA-256 content-hashes or a Merkle tree are persisted.
- [ ] Rerank strategy is documented (cross-encoder, rule-based, or LLM-assisted).
- [ ] Spot-check: three natural-language queries ("where do we handle authentication", "what is the retry policy for failed webhooks", "find the pagination helper") each return the file(s) the team expects within the top 5 results.
- [ ] No source code, query text, or identifier names leave the local machine except to vendor-intrinsic destinations (if any, per the decision tree).

## Related Skills

- [`rag-implementation`](../rag-implementation/SKILL.md) - general-purpose RAG over non-code corpora. This skill is the code-corpus specialization.
- [`context-manager`](../../orchestration/context-manager/SKILL.md) - for session-level context budgeting. Use `code-semantic-search` as the escape valve when the repo exceeds the context window.
- [`context-engineering`](../context-engineering/SKILL.md) - deliberate context shaping. Semantic search is one of the primary retrieval-based context sources.
- [`local-docs-lookup`](../../research/local-docs-lookup/SKILL.md) - for library-docs grounding. This skill is for the user's own code.
- DevAI-Hub's internal [`devai-code-search`](../../../../extensions/devai-code-search/) MCP - the reference implementation referenced throughout. Install via `pip install -e extensions/devai-code-search` or the DevAI-Hub installer.
