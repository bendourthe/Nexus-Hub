### Step 1: Understand Prompt Anatomy

Every LLM interaction consists of roles. How you use each role determines output quality.

**Role Responsibilities**:

| Role | Purpose | Best Practices |
|------|---------|---------------|
| **System** | Define persona, rules, constraints, output format | Stable across conversations; set once |
| **User** | Provide task input, context, specific instructions | Dynamic per request |
| **Assistant** | Prefill to guide response format or continue generation | Use sparingly for format steering |

**System Prompt Structure Template**:

```
You are [ROLE] that [PRIMARY_FUNCTION].

## Rules
- [Rule 1: constraint or behavior requirement]
- [Rule 2: constraint or behavior requirement]
- [Rule 3: what to do when uncertain]

## Output Format
[Describe the exact structure of expected output]

## Examples
[Optional: include 1-2 examples in the system prompt for consistent behavior]
```

**Example: Classification System Prompt**:

```python
CLASSIFICATION_SYSTEM = """You are a customer support ticket classifier.

## Rules
- Classify each ticket into exactly ONE category
- If a ticket spans multiple categories, choose the PRIMARY intent
- If uncertain, classify as "general" rather than guessing
- Never explain your reasoning in the output; return only the classification

## Categories
- billing: Payment issues, invoices, refunds, subscription changes
- technical: Bugs, errors, performance issues, feature not working
- account: Login problems, password reset, profile changes, permissions
- feature_request: New feature suggestions, enhancement requests
- general: Anything that does not fit the above categories

## Output Format
Respond with ONLY a JSON object:
{"category": "<category>", "confidence": <0.0-1.0>}
"""
```

**Assistant Prefill for Format Steering**:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    system=CLASSIFICATION_SYSTEM,
    messages=[
        {"role": "user", "content": "I can't log into my account since yesterday"},
        # Prefill forces the model to continue from this point
        {"role": "assistant", "content": "{"},
    ],
)
# Response will continue the JSON object: "category": "account", "confidence": 0.95}
```
