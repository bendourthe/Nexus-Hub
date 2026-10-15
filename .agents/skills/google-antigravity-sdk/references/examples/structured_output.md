# Example: Structured Output

Constrain a turn's output to a Pydantic schema so you get a parsed, validated object instead of free text. This is output *constraint*, distinct from output *evaluation* (scoring quality).

## Code

```python
import asyncio
from pydantic import BaseModel
from google.antigravity import Agent, LocalAgentConfig


class Finding(BaseModel):
    severity: str
    file: str
    line: int
    summary: str


class ReviewResult(BaseModel):
    findings: list[Finding]
    overall: str


async def main() -> None:
    config = LocalAgentConfig(model="gemini-3.5-flash")
    async with Agent(config) as agent:
        result = await agent.chat(
            "Review src/auth.py for security issues.",
            response_format=ReviewResult,
        )
        # result is a parsed ReviewResult, not a string.
        for f in result.findings:
            print(f"{f.severity}: {f.file}:{f.line} -- {f.summary}")


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- Declaring a Pydantic model as the `response_format` makes it the response contract: the agent's output is parsed and validated against it automatically.
- Failure modes: invalid JSON, missing required fields, type mismatch. The standard recovery is to route the parse error back to the model with a corrective instruction and retry once, then fail closed if it still does not conform (see [../error_handling.md](../error_handling.md)).
- Keep schemas tight. Optional fields and loose types give the model room to return something unhelpful that still validates.

## Constraint vs. evaluation

- **Constraint (this example)**: force the output into a known shape.
- **Evaluation**: judge whether the output is *good*. That is the `developer-experience/ai-output-evaluation` skill.

## Related

- [../error_handling.md](../error_handling.md) -- handling parse failures.
- The `ai-agent-development` skill's `sdk-structured-output.md` reference -- the pattern in general terms.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
