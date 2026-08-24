### Step 7: Evaluate RAG Quality

**Measure retrieval before generation.** These are two separate measurements, and running them in the wrong order is the most common RAG debugging error. A model cannot ground an answer in a passage it never received, so a low faithfulness score on top of low recall is not a generation problem. Compute retrieval metrics first; only interpret the generation metrics once the relevant passage is confirmed to have reached the prompt.

| Family | Metrics | Answers | Fails when |
|--------|---------|---------|------------|
| **Retrieval** | Recall@k, Precision@k, MRR, NDCG@k, multi-hop recall | Did the retriever find the passages containing the answer? | Chunking, embeddings, index, query formulation, or k are wrong |
| **Generation** | Faithfulness, Answer Relevance | Did the model use those passages correctly? | Prompt construction, context ordering, or model capability are wrong |

For the retrieval half -- formulas, worked examples, edge cases, relevance-label conventions, confidence intervals, and the one-variable-at-a-time chunking grid search -- see `references/evaluation.md`. It is cold-readable and carries the full method; the summary table below covers the generation half and the two context metrics that bridge them.

**Evaluation Metrics**:

| Metric | Family | Measures | Range | Good Score |
|--------|--------|----------|-------|------------|
| **Faithfulness** | generation | Is the answer grounded in retrieved context? | 0-1 | > 0.85 |
| **Answer Relevance** | generation | Does the answer address the question? | 0-1 | > 0.80 |
| **Context Recall** | retrieval | Did retrieval find the relevant passages? | 0-1 | > 0.75 |
| **Context Precision** | retrieval | Are retrieved passages relevant (low noise)? | 0-1 | > 0.70 |

Read the first two only after the last two clear their bar. A system reporting Recall of 0.42 with Faithfulness of 0.91 is faithfully answering from the wrong passages most of the time.

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
