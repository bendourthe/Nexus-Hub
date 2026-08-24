### Step 1: Choose an Agent Architecture

Select an architecture based on task complexity, latency requirements, and reliability needs.

**Architecture Comparison**:

| Architecture | Best For | Latency | Reliability | Complexity |
|-------------|----------|---------|-------------|------------|
| **ReAct** | Simple tool-use tasks | Low | Medium | Low |
| **Plan-and-Execute** | Multi-step workflows | Medium | High | Medium |
| **Reflection** | Quality-critical outputs | High | High | Medium |
| **Multi-Agent** | Complex domain tasks | High | Variable | High |

**ReAct (Reason + Act) Pattern**:

The agent interleaves reasoning and action in a loop: think about what to do, execute a tool, observe the result, repeat.

```python
import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "search_codebase",
        "description": (
            "Search the codebase for files matching a regex pattern. "
            "Returns file paths and matching line contents. "
            "Use when looking for function definitions, imports, or string patterns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for."
                },
                "file_glob": {
                    "type": "string",
                    "description": "Optional glob to filter files (e.g., '*.py').",
                    "default": "*"
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "read_file",
        "description": (
            "Read the full contents of a file by path. "
            "Use when you need to examine a specific file found via search."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or workspace-relative file path."
                }
            },
            "required": ["path"]
        }
    }
]


def run_react_agent(user_query: str, max_turns: int = 10) -> str:
    """Run a ReAct agent loop with Claude."""
    messages = [{"role": "user", "content": user_query}]

    for turn in range(max_turns):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=(
                "You are a code analysis agent. Think step-by-step about what "
                "information you need, use tools to gather it, then provide "
                "your analysis. Always explain your reasoning before acting."
            ),
            tools=tools,
            messages=messages,
        )

        # If the model wants to use tools, execute them
        if response.stop_reason == "tool_use":
            # Append the assistant's response (contains tool_use blocks)
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            # Model produced a final text response
            return extract_text(response.content)

    return "Agent reached maximum turn limit without completing."
```

**Plan-and-Execute Pattern**:

Separate planning from execution. The planner decomposes the goal into steps; the executor handles each step independently.

```python
from dataclasses import dataclass, field


@dataclass
class Plan:
    goal: str
    steps: list[str] = field(default_factory=list)
    completed: list[int] = field(default_factory=list)
    results: dict[int, str] = field(default_factory=dict)


def create_plan(goal: str) -> Plan:
    """Use the LLM to decompose a goal into executable steps."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=(
            "You are a planning agent. Decompose the user's goal into "
            "a numbered list of concrete, independent steps. Each step "
            "should be actionable with available tools. Output ONLY the "
            "numbered list, nothing else."
        ),
        messages=[{"role": "user", "content": goal}],
    )
    steps = parse_numbered_list(extract_text(response.content))
    return Plan(goal=goal, steps=steps)


def execute_plan(plan: Plan) -> str:
    """Execute each step, replanning if a step fails."""
    for i, step in enumerate(plan.steps):
        if i in plan.completed:
            continue

        result = run_react_agent(
            f"Execute this step: {step}\n\n"
            f"Context from previous steps:\n{format_results(plan.results)}"
        )

        if is_failure(result):
            # Replan from this point forward
            revised = replan(plan, i, result)
            plan.steps = plan.steps[:i] + revised
            continue

        plan.results[i] = result
        plan.completed.append(i)

    return synthesize_results(plan)
```
