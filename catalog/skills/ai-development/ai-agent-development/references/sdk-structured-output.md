# Structured Output via Pydantic Schema

Constraining an agent's output to a schema is a different concern from evaluating that output. This reference covers output **constraint** (forcing the response into a known shape); output **evaluation** (scoring whether the response is good) is covered by `developer-experience/ai-output-evaluation`. The two layer: constrain first so the result is parseable, then evaluate the parsed result.

## The Pydantic-schema-as-response-contract pattern

The pattern is to declare a Pydantic model and pass it as the response contract (a `response_format` parameter, or the SDK's equivalent), so the agent's output is parsed and validated against the model automatically. Instead of receiving free text and parsing it by hand, you receive a typed object whose fields are guaranteed to exist and to have the declared types, or you receive a validation error.

```python
from pydantic import BaseModel

class ReviewResult(BaseModel):
    findings: list[str]
    severity: str
    overall: str

# The agent returns a parsed ReviewResult, not a string.
result = await agent.chat("Review src/auth.py.", response_format=ReviewResult)
```

The model becomes the single source of truth for the output shape: the schema documents it, the runtime enforces it, and downstream code consumes a typed object.

## Failure modes and recovery

Even with a schema, the model can produce output that does not conform. The three failure modes:

- **Invalid JSON** -- the output is not parseable at all.
- **Missing required fields** -- the JSON parses but omits a required field.
- **Type mismatch** -- a field is present but the wrong type (a string where an integer was declared).

The standard recovery is to route the parse or validation error back to the model with a corrective instruction ("your last response was missing the `severity` field; return valid JSON matching the schema") and retry once. If it still does not conform, fail closed: return the parse error to the caller rather than passing along malformed data. Keep schemas tight; optional fields and loose types give the model room to return something unhelpful that still validates.

## Related

- [google-antigravity-sdk structured_output example](../../google-antigravity-sdk/references/examples/structured_output.md) -- the concrete reference implementation of the response-contract pattern and its recovery loop.
- [ai-output-evaluation SKILL.md](../../../developer-experience/ai-output-evaluation/SKILL.md) -- the evaluation layer that sits above this constraint layer (scoring quality, not enforcing shape).
- [ai-agent-development SKILL.md](../SKILL.md) -- the parent skill.
