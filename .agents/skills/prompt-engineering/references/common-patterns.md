## Common Patterns

### Pattern 1: Classification with Confidence Gating

Route low-confidence classifications to human review.

```python
def classify_with_gating(text: str, confidence_threshold: float = 0.8) -> dict:
    """Classify text and flag low-confidence results for human review."""
    result = few_shot_classify(text)

    if result["confidence"] < confidence_threshold:
        result["needs_review"] = True
        result["review_reason"] = f"Confidence {result['confidence']:.2f} below threshold {confidence_threshold}"
    else:
        result["needs_review"] = False

    return result
```

### Pattern 2: Iterative Refinement Prompt

Ask the model to improve its own output through targeted self-critique.

```python
def iterative_refine(task: str, criteria: list[str], max_rounds: int = 3) -> str:
    """Generate and refine output against specific quality criteria."""
    criteria_block = "\n".join(f"- {c}" for c in criteria)

    draft = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": task}],
    )
    current = extract_text(draft.content)

    for round_num in range(max_rounds):
        review = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": (
                    f"Review this output against the following criteria:\n{criteria_block}\n\n"
                    f"Output:\n{current}\n\n"
                    "For each criterion, score 1 (met) or 0 (not met). "
                    "If all criteria are met, respond with ONLY 'ALL_MET'.\n"
                    "Otherwise, list the unmet criteria with specific improvement instructions."
                ),
            }],
        )
        feedback = extract_text(review.content)

        if "ALL_MET" in feedback:
            break

        revision = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": (
                    f"Original task: {task}\n\n"
                    f"Current output:\n{current}\n\n"
                    f"Improvement feedback:\n{feedback}\n\n"
                    "Revise the output to address all feedback. Output the complete revised version."
                ),
            }],
        )
        current = extract_text(revision.content)

    return current
```

### Pattern 3: Dynamic Few-Shot Selection

Select the most relevant examples for each input rather than using a fixed set.

```python
def dynamic_few_shot(
    query: str,
    example_pool: list[dict],
    embed_model,
    num_examples: int = 3,
) -> list[dict]:
    """Select the most relevant few-shot examples for a given query."""
    query_embedding = embed_model.embed_query(query)
    example_embeddings = embed_model.embed([ex["input"] for ex in example_pool])

    # Score each example by similarity to the query
    scored = []
    for i, ex in enumerate(example_pool):
        sim = cosine_similarity(query_embedding, example_embeddings[i])
        scored.append((sim, ex))

    # Return top-N most similar examples
    scored.sort(key=lambda x: x[0], reverse=True)
    return [ex for _, ex in scored[:num_examples]]
```
