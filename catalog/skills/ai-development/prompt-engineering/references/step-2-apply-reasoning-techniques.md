### Step 2: Apply Reasoning Techniques

Choose a reasoning technique based on task complexity and latency budget.

**Technique Selection Guide**:

| Technique | Task Complexity | Latency | Token Cost | When to Use |
|-----------|----------------|---------|------------|-------------|
| **Zero-shot** | Simple | Low | Low | Clear, well-defined tasks |
| **Few-shot** | Medium | Medium | Medium | Pattern-following tasks |
| **Chain-of-thought** | High | High | High | Multi-step reasoning |
| **Tree-of-thought** | Very High | Very High | Very High | Problems with multiple valid paths |
| **Self-consistency** | High | Very High | Very High | When correctness is critical |

**Zero-Shot (Direct Instruction)**:

```python
def zero_shot_extract(text: str) -> dict:
    """Extract structured data with zero-shot prompting."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                "Extract the following fields from the text below. "
                "If a field is not present, use null.\n\n"
                "Fields: name, email, phone, company, role\n\n"
                f"Text: {text}\n\n"
                "Respond with ONLY a JSON object containing these fields."
            ),
        }],
    )
    import json
    return json.loads(extract_text(response.content))
```

**Few-Shot (Learning from Examples)**:

```python
FEW_SHOT_EXAMPLES = [
    {
        "input": "The server is returning 500 errors on the /api/users endpoint",
        "output": '{"category": "technical", "priority": "high", "component": "api"}'
    },
    {
        "input": "Can you add dark mode to the dashboard?",
        "output": '{"category": "feature_request", "priority": "low", "component": "ui"}'
    },
    {
        "input": "I was charged twice for my subscription this month",
        "output": '{"category": "billing", "priority": "high", "component": "payments"}'
    },
]


def few_shot_classify(ticket: str) -> dict:
    """Classify a support ticket using few-shot examples."""
    examples_block = "\n\n".join(
        f"Input: {ex['input']}\nOutput: {ex['output']}"
        for ex in FEW_SHOT_EXAMPLES
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                "Classify the support ticket. Follow the exact format shown in the examples.\n\n"
                f"Examples:\n{examples_block}\n\n"
                f"Input: {ticket}\nOutput:"
            ),
        }],
    )
    import json
    return json.loads(extract_text(response.content))
```

**Chain-of-Thought (Step-by-Step Reasoning)**:

```python
def chain_of_thought_analyze(code: str, question: str) -> dict:
    """Analyze code with explicit reasoning steps."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": (
                "Analyze the following code and answer the question.\n\n"
                "Think through this step-by-step:\n"
                "1. First, identify what the code does at a high level\n"
                "2. Trace the execution flow for typical inputs\n"
                "3. Identify any edge cases or potential issues\n"
                "4. Answer the specific question\n\n"
                f"Code:\n```\n{code}\n```\n\n"
                f"Question: {question}\n\n"
                "Structure your response as:\n"
                "<thinking>\n[Your step-by-step analysis]\n</thinking>\n\n"
                "<answer>\n[Your final answer]\n</answer>"
            ),
        }],
    )
    text = extract_text(response.content)
    thinking = extract_between_tags(text, "thinking")
    answer = extract_between_tags(text, "answer")
    return {"thinking": thinking, "answer": answer}
```

**Self-Consistency (Multiple Reasoning Paths)**:

```python
def self_consistency(question: str, num_samples: int = 5) -> str:
    """Generate multiple reasoning paths and pick the most common answer."""
    answers = []

    for _ in range(num_samples):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.7,  # Higher temperature for diverse paths
            messages=[{
                "role": "user",
                "content": (
                    f"{question}\n\n"
                    "Think step-by-step, then provide your final answer "
                    "on the last line after 'ANSWER: '"
                ),
            }],
        )
        text = extract_text(response.content)
        # Extract the final answer line
        for line in reversed(text.split("\n")):
            if line.strip().startswith("ANSWER:"):
                answers.append(line.split("ANSWER:")[1].strip())
                break

    # Return the most common answer
    from collections import Counter
    if not answers:
        return "No consistent answer found."
    most_common = Counter(answers).most_common(1)[0]
    return most_common[0]
```
