### Step 8: Optimize Cost and Latency

**Token Reduction Techniques**:

| Technique | Token Savings | Impact on Quality | When to Use |
|-----------|--------------|-------------------|-------------|
| **Concise instructions** | 20-40% | None if well-written | Always |
| **Remove redundancy** | 10-30% | None | Always |
| **Abbreviate examples** | 15-25% | Minor | Large few-shot sets |
| **Prompt caching** | 0% (cost savings) | None | Repeated system prompts |
| **Model routing** | N/A | Variable | Mixed-complexity workloads |

**Prompt Caching with Anthropic**:

```python
def cached_system_prompt_call(
    system_prompt: str,
    user_message: str,
    model: str = "claude-sonnet-4-20250514",
) -> str:
    """Use Anthropic's prompt caching for repeated system prompts."""
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    # Log cache performance
    usage = response.usage
    cached_input = getattr(usage, "cache_read_input_tokens", 0)
    total_input = usage.input_tokens
    if cached_input > 0:
        savings_pct = (cached_input / total_input) * 100 if total_input else 0
        print(f"Cache hit: {cached_input}/{total_input} tokens ({savings_pct:.0f}% cached)")

    return extract_text(response.content)
```

**Model Routing by Complexity**:

```python
def route_to_model(task_description: str, input_length: int) -> str:
    """Select the appropriate model based on task complexity."""
    # Simple heuristics for model routing
    complex_indicators = [
        "analyze", "compare", "evaluate", "design", "architect",
        "debug", "optimize", "refactor",
    ]

    is_complex = any(ind in task_description.lower() for ind in complex_indicators)
    is_long = input_length > 5000

    if is_complex or is_long:
        return "claude-sonnet-4-20250514"   # Higher capability
    else:
        return "claude-haiku-4-20250514"    # Lower cost, faster
```
