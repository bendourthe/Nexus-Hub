---
name: rag-implementation
description: Retrieval-Augmented Generation implementation including document processing, chunking strategies, embedding, vector stores, retrieval optimization, and retrieval-quality measurement. Use when building RAG pipelines, optimizing retrieval quality, or evaluating RAG systems. Make sure to use this skill whenever the user says "evaluate RAG", "measure retrieval quality", "compare chunking strategies", "why is my RAG returning the wrong passages", "Recall@k", "NDCG", "tune my retriever", or asks whether a bad answer came from retrieval or from the model. SKIP, do NOT use for, general model-output scoring, rubric design, or LLM-as-judge calibration that is not about retrieval (use ai-output-evaluation).
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
- Measuring retrieval quality on its own terms (Recall@k, Precision@k, MRR, NDCG@k, multi-hop recall)
- Diagnosing whether a weak answer came from retrieval or from generation
- Comparing chunking or retrieval configurations against a fixed evaluation set
- Scaling RAG systems for production (caching, batching, cost control)

**Trigger phrases**: "RAG pipeline", "retrieval augmented generation", "vector database", "document chunking", "embedding", "semantic search", "retrieval quality", "vector store", "document ingestion", "reranking", "hybrid search", "evaluate RAG", "measure retrieval quality", "compare chunking strategies", "Recall@k", "NDCG"

**When NOT to use this skill**: general AI-output scoring, rubric design, LLM-as-judge calibration, or evaluator validation that is not about retrieval belongs to `[[ai-output-evaluation]]`. This skill owns the retrieval half of the measurement; that skill owns the generation half and the evaluator itself.

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

Full walkthrough: [step-1-design-the-document-ingestion-pipeline.md](references/step-1-design-the-document-ingestion-pipeline.md) (load this step when you reach it).

### Step 2: Choose and Implement a Chunking Strategy

Full walkthrough: [step-2-choose-and-implement-a-chunking-strategy.md](references/step-2-choose-and-implement-a-chunking-strategy.md) (load this step when you reach it).

### Step 3: Select and Configure Embeddings

Full walkthrough: [step-3-select-and-configure-embeddings.md](references/step-3-select-and-configure-embeddings.md) (load this step when you reach it).

### Step 4: Set Up the Vector Store

Full walkthrough: [step-4-set-up-the-vector-store.md](references/step-4-set-up-the-vector-store.md) (load this step when you reach it).

### Step 5: Implement Retrieval Strategies

Full walkthrough: [step-5-implement-retrieval-strategies.md](references/step-5-implement-retrieval-strategies.md) (load this step when you reach it).

### Step 6: Construct Prompts with Retrieved Context

Full walkthrough: [step-6-construct-prompts-with-retrieved-context.md](references/step-6-construct-prompts-with-retrieved-context.md) (load this step when you reach it).

### Step 7: Evaluate RAG Quality

Measure retrieval before generation. Compute Recall@k / Precision@k / NDCG on the retrieved set first; only then interpret generation metrics such as faithfulness. A low faithfulness score is not a generation failure until retrieval has been shown to have returned the relevant passage.

Full walkthrough: [step-7-evaluate-rag-quality.md](references/step-7-evaluate-rag-quality.md) (load this step when you reach it).

### Step 8: Optimize for Production

Full walkthrough: [step-8-optimize-for-production.md](references/step-8-optimize-for-production.md) (load this step when you reach it).

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

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Default fixed-size chunking is good enough" | Splitting mid-sentence or mid-table strands the context the answer needs across two chunks, so retrieval returns half the fact and the LLM hallucinates the rest; chunking must respect the document's structure. |
| "I'll skip the eval suite, the answers look right" | "Looks right" on a handful of demo queries hides low recall on the long tail; without a faithfulness/relevance/recall suite a retrieval regression ships undetected. |
| "I do not need source attribution in the prompt" | Without injected sources the system cannot show provenance and you cannot distinguish a grounded answer from a hallucination, which is the entire point of RAG. |
| "Full re-indexing on every update is simpler" | Re-embedding the whole corpus on each document change is slow and expensive at scale and creates a stale window; incremental indexing keeps the store current without the full cost. |
| "The answer was wrong, so I'll rewrite the prompt" | If the relevant passage never entered the top k, no prompt rewrite can recover it; measuring Recall@k first is what separates a retrieval failure from a generation failure, and skipping it sends you tuning the half that was already working. |
| "One eval run showed a 5-point recall gain, so the new chunk size wins" | On 50 queries a 5-point difference sits well inside the confidence interval; without an interval and a one-variable-at-a-time change, a grid search records noise as progress. |

## Verification

- [ ] Document loaders handle target formats (PDF, HTML, code, etc.)
- [ ] Chunking strategy chosen and tuned for document type and query patterns
- [ ] Embedding model selected with cost/quality trade-off justified
- [ ] Vector store configured with appropriate index type and distance metric
- [ ] Retrieval strategy tested (similarity, MMR, hybrid, reranking)
- [ ] Prompt template injects context with source attribution
- [ ] Evaluation suite measures faithfulness, relevance, and recall
- [ ] Retrieval metrics were computed and interpreted before any generation metric (see `references/evaluation.md`)
- [ ] Every reported retrieval metric states its k and its query count
- [ ] Caching in place for embeddings and frequent queries
- [ ] Incremental indexing handles document updates without full re-index
- [ ] Production monitoring tracks retrieval latency, cost, and quality drift

## Related Skills

- [[ai-agent-development]] -- building agents that use RAG as a tool
- [[prompt-engineering]] -- designing prompts for RAG answer generation
- [[sql-expert]] -- using pgvector with existing Postgres databases
- [[performance-testing]] -- load testing RAG retrieval endpoints
- [[ai-output-evaluation]] -- owns the generation half of RAG evaluation: rubrics, LLM-as-judge, and validating the evaluator itself
- [[egress-redaction]] -- governs any authorized export of queries, passages, or relevance labels produced by an evaluation run

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
