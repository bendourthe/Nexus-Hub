## Common Patterns

### Pattern 1: Retry with Backoff

When a tool call fails due to transient errors, retry with exponential backoff rather than immediately asking the user.

```python
import time


def retry_tool_call(name: str, arguments: dict, max_retries: int = 3) -> str:
    """Retry a tool call with exponential backoff."""
    for attempt in range(max_retries):
        result = execute_tool(name, arguments)
        parsed = json.loads(result) if result.startswith("{") else {"output": result}

        if "error" not in parsed or not parsed.get("recoverable", True):
            return result

        wait = 2 ** attempt
        logger.warning(f"Tool {name} failed (attempt {attempt+1}), retrying in {wait}s")
        time.sleep(wait)

    return result  # Return last result even if failed
```

### Pattern 2: Human-in-the-Loop Escalation

For high-stakes actions, pause and request confirmation before executing.

```python
def human_in_the_loop(action_description: str, risk_level: str) -> bool:
    """Request human confirmation for risky actions."""
    if risk_level == "low":
        return True  # Auto-approve low-risk actions

    print(f"\n--- Agent requests approval ---")
    print(f"Action: {action_description}")
    print(f"Risk level: {risk_level}")
    response = input("Approve? [y/N]: ").strip().lower()
    return response == "y"
```

### Pattern 3: Agent-as-Tool (Nested Agents)

Use one agent as a tool for another, creating hierarchical agent systems.

```python
research_tool = {
    "name": "deep_research",
    "description": (
        "Perform in-depth research on a technical topic. "
        "Returns a detailed analysis with sources. "
        "Use for questions requiring multiple search steps."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The research question to investigate."
            }
        },
        "required": ["question"]
    }
}


def execute_research_agent(question: str) -> str:
    """Dedicated research sub-agent with web search tools."""
    return run_react_agent(
        f"Research this thoroughly and provide a detailed answer: {question}",
    )
```
