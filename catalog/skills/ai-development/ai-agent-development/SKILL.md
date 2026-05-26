---
name: ai-agent-development
description: AI agent architecture and development patterns including tool use, memory systems, planning loops, and multi-agent orchestration. Use when building AI agents, designing tool interfaces, or implementing agent evaluation.
summary_l0: "Build AI agents with tool use, memory, planning loops, and multi-agent orchestration"
overview_l1: "This skill provides comprehensive architecture and implementation guidance for building AI agents that reason, plan, use tools, and collaborate. Use it when designing agent architectures (ReAct, plan-and-execute, reflection), implementing tool-use patterns with function calling or MCP, building memory systems (short-term, long-term, episodic, semantic), creating planning and reasoning loops, orchestrating multi-agent systems, or adding guardrails and evaluation. Key capabilities include architecture pattern selection, tool integration schemas, memory system design, planning loop implementation, multi-agent topologies (supervisor, peer-to-peer, pipeline), guardrail enforcement, trajectory-based evaluation, and observability instrumentation. The expected output is production-grade agent code with structured logging, error handling, and cost tracking. Trigger phrases: build an agent, agent architecture, tool use, function calling, agent memory, planning loop, multi-agent, agent orchestration, agent evaluation, agent guardrails, ReAct pattern, MCP server."
---

# AI Agent Development

Comprehensive patterns and implementation guidance for building AI agents that reason, plan, use tools, and collaborate. Covers the full spectrum from single-agent architectures to multi-agent orchestration, with production-grade error handling, observability, and evaluation.

> **Effort-level note**: when agents run inside loops or parallel fan-out, default the `effortLevel` to `high`, not `max`. Iterative and concurrent runs compound effort-level cost without matching quality gains. See the **Effort-Level Strategy** section of [prompt-engineering/SKILL.md](../prompt-engineering/SKILL.md) for the decision table. A full Opus 4.7 Anti-Patterns table for agent workloads is maintained alongside this skill.

## When to Use This Skill

Use this skill for:

- Designing agent architectures (ReAct, plan-and-execute, reflection)
- Implementing tool-use patterns with function calling or MCP
- Building memory systems (short-term, long-term, episodic, semantic)
- Creating planning and reasoning loops
- Orchestrating multi-agent systems
- Adding guardrails and safety layers to agents
- Evaluating and testing agent behavior
- Instrumenting agents for observability

**Trigger phrases**: "build an agent", "agent architecture", "tool use", "function calling", "agent memory", "planning loop", "multi-agent", "agent orchestration", "agent evaluation", "agent guardrails", "ReAct pattern", "MCP server"

## What This Skill Does

Provides agent development expertise including:

- **Architecture Patterns**: ReAct, plan-and-execute, reflection, and hybrid approaches
- **Tool Integration**: Function calling schemas, MCP servers, tool selection logic
- **Memory Systems**: Working memory, long-term stores, episodic recall, semantic search
- **Planning Loops**: Goal decomposition, step execution, replanning on failure
- **Multi-Agent Orchestration**: Supervisor, peer-to-peer, and pipeline topologies
- **Guardrails**: Input validation, output filtering, budget limits, human-in-the-loop
- **Evaluation**: Task completion metrics, trajectory analysis, regression testing
- **Observability**: Structured logging, trace propagation, cost tracking

## Instructions

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

### Step 2: Implement Tool Integration

Tools are the agent's interface to the external world. Design them for LLM consumption (see the `tool-design` skill for detailed guidance).

**Function Calling Schema Best Practices**:

```python
# Good: Specific, documented, constrained
file_edit_tool = {
    "name": "edit_file",
    "description": (
        "Replace a specific string in a file with new content. "
        "The old_string must appear exactly once in the file. "
        "Use when you need to modify existing code. "
        "Do NOT use for creating new files (use write_file instead)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to edit."
            },
            "old_string": {
                "type": "string",
                "description": "The exact text to find and replace. Must be unique in the file."
            },
            "new_string": {
                "type": "string",
                "description": "The replacement text. Must differ from old_string."
            }
        },
        "required": ["file_path", "old_string", "new_string"]
    }
}
```

**MCP Server Integration**:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def connect_mcp_server(command: str, args: list[str]) -> ClientSession:
    """Connect to an MCP server and return a session."""
    server_params = StdioServerParameters(command=command, args=args)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                print(f"  {tool.name}: {tool.description}")

            return session


async def call_mcp_tool(session: ClientSession, name: str, arguments: dict):
    """Call a tool on the MCP server and return the result."""
    result = await session.call_tool(name, arguments=arguments)
    return result.content
```

**Tool Execution with Error Handling**:

```python
import json
import traceback


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool call with structured error handling."""
    try:
        if name == "search_codebase":
            return search_codebase(**arguments)
        elif name == "read_file":
            return read_file(**arguments)
        elif name == "edit_file":
            return edit_file(**arguments)
        else:
            return json.dumps({
                "error": f"Unknown tool: {name}",
                "available_tools": ["search_codebase", "read_file", "edit_file"],
                "suggestion": "Check the tool name and try again."
            })
    except FileNotFoundError as e:
        return json.dumps({
            "error": f"File not found: {e}",
            "suggestion": "Use search_codebase to find the correct file path."
        })
    except PermissionError as e:
        return json.dumps({
            "error": f"Permission denied: {e}",
            "recoverable": False,
            "suggestion": "This file cannot be modified. Ask the user for guidance."
        })
    except Exception as e:
        return json.dumps({
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
            "suggestion": "An unexpected error occurred. Try a different approach."
        })
```

### Step 3: Build Memory Systems

Agents need memory to maintain context across turns, learn from past interactions, and recall relevant information.

**Memory Type Overview**:

| Type | Scope | Storage | Use Case |
|------|-------|---------|----------|
| **Working** | Current conversation | Message history | Immediate context |
| **Episodic** | Past interactions | Database | Recall similar tasks |
| **Semantic** | Domain knowledge | Vector store | Fact retrieval |
| **Procedural** | Learned workflows | Key-value store | Skill reuse |

**Working Memory (Conversation Buffer with Summarization)**:

```python
from dataclasses import dataclass


@dataclass
class WorkingMemory:
    messages: list[dict]
    max_tokens: int = 100_000
    summary: str = ""

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if self.estimate_tokens() > self.max_tokens * 0.8:
            self.compact()

    def compact(self):
        """Summarize older messages to free context space."""
        # Keep the most recent messages intact
        keep_recent = 6
        old_messages = self.messages[:-keep_recent]
        recent_messages = self.messages[-keep_recent:]

        summary_prompt = (
            f"Previous summary: {self.summary}\n\n"
            f"New messages to summarize:\n"
            f"{format_messages(old_messages)}\n\n"
            "Produce a concise summary preserving key decisions, "
            "findings, and action items."
        )
        self.summary = call_llm_for_summary(summary_prompt)
        self.messages = recent_messages

    def get_context(self) -> list[dict]:
        """Return messages with summary prepended if available."""
        if self.summary:
            summary_msg = {
                "role": "user",
                "content": f"[Context from earlier in this conversation]\n{self.summary}"
            }
            return [summary_msg] + self.messages
        return self.messages

    def estimate_tokens(self) -> int:
        return sum(len(m["content"]) // 4 for m in self.messages)
```

**Long-Term Episodic Memory**:

```python
import hashlib
from datetime import datetime


class EpisodicMemory:
    """Store and recall past agent interactions by similarity."""

    def __init__(self, vector_store, embedding_model):
        self.store = vector_store
        self.embedder = embedding_model

    def record_episode(self, task: str, trajectory: list[dict], outcome: str):
        """Save a completed task episode for future recall."""
        episode = {
            "task": task,
            "trajectory_summary": summarize_trajectory(trajectory),
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat(),
            "id": hashlib.sha256(f"{task}{datetime.utcnow()}".encode()).hexdigest()[:16],
        }
        embedding = self.embedder.embed(f"{task} {outcome}")
        self.store.upsert(id=episode["id"], vector=embedding, metadata=episode)

    def recall(self, current_task: str, top_k: int = 3) -> list[dict]:
        """Recall past episodes similar to the current task."""
        query_embedding = self.embedder.embed(current_task)
        results = self.store.query(vector=query_embedding, top_k=top_k)
        return [
            {
                "task": r.metadata["task"],
                "approach": r.metadata["trajectory_summary"],
                "outcome": r.metadata["outcome"],
                "similarity": r.score,
            }
            for r in results
        ]
```

### Step 4: Implement Planning and Reasoning Loops

**Reflection Pattern (Self-Critique Loop)**:

```python
def reflect_and_improve(task: str, max_iterations: int = 3) -> str:
    """Generate output, critique it, and iterate until quality threshold is met."""
    draft = generate_initial_response(task)

    for iteration in range(max_iterations):
        critique = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Task: {task}\n\n"
                        f"Current output:\n{draft}\n\n"
                        "Critique this output. Identify specific problems with:\n"
                        "1. Correctness: Are there factual or logical errors?\n"
                        "2. Completeness: Is anything missing?\n"
                        "3. Quality: Could the structure or clarity improve?\n\n"
                        "If the output is satisfactory, respond with ONLY 'APPROVED'.\n"
                        "Otherwise, list specific improvements needed."
                    ),
                }
            ],
        )

        critique_text = extract_text(critique.content)

        if "APPROVED" in critique_text:
            return draft

        # Revise based on critique
        revision = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Task: {task}\n\n"
                        f"Previous output:\n{draft}\n\n"
                        f"Critique:\n{critique_text}\n\n"
                        "Revise the output to address every critique point. "
                        "Produce the complete revised version."
                    ),
                }
            ],
        )
        draft = extract_text(revision.content)

    return draft
```

**Goal Decomposition with Dependency Tracking**:

```python
@dataclass
class TaskNode:
    id: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | running | completed | failed
    result: str | None = None


def build_task_graph(goal: str) -> list[TaskNode]:
    """Decompose a goal into a dependency-aware task graph."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=(
            "Decompose the goal into tasks. For each task, specify an ID, "
            "description, and list of dependency IDs (tasks that must complete "
            "first). Output as JSON array."
        ),
        messages=[{"role": "user", "content": goal}],
    )
    raw_tasks = json.loads(extract_text(response.content))
    return [TaskNode(**t) for t in raw_tasks]


def execute_task_graph(tasks: list[TaskNode]) -> dict[str, str]:
    """Execute tasks respecting dependency order."""
    results = {}
    while any(t.status == "pending" for t in tasks):
        ready = [
            t for t in tasks
            if t.status == "pending"
            and all(
                dep_task.status == "completed"
                for dep_task in tasks
                if dep_task.id in t.dependencies
            )
        ]
        for task in ready:
            task.status = "running"
            context = {d: results[d] for d in task.dependencies if d in results}
            task.result = run_react_agent(
                f"Execute: {task.description}\nContext: {json.dumps(context)}"
            )
            task.status = "completed"
            results[task.id] = task.result

    return results
```

### Step 5: Orchestrate Multi-Agent Systems

**Supervisor Pattern (Hub-and-Spoke)**:

```python
@dataclass
class AgentConfig:
    name: str
    system_prompt: str
    tools: list[dict]
    model: str = "claude-sonnet-4-20250514"


class SupervisorOrchestrator:
    """A supervisor agent delegates tasks to specialist agents."""

    def __init__(self, specialists: list[AgentConfig]):
        self.specialists = {s.name: s for s in specialists}

    def run(self, goal: str) -> str:
        """Supervisor decomposes goal and delegates to specialists."""
        specialist_descriptions = "\n".join(
            f"- {s.name}: {s.system_prompt[:100]}..."
            for s in self.specialists.values()
        )

        # Supervisor decides which specialists to invoke and in what order
        plan_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=(
                "You are a supervisor agent. You delegate tasks to specialists.\n"
                f"Available specialists:\n{specialist_descriptions}\n\n"
                "For the given goal, output a JSON array of delegation steps:\n"
                '[{"specialist": "name", "task": "what to do", "depends_on": []}]'
            ),
            messages=[{"role": "user", "content": goal}],
        )

        delegations = json.loads(extract_text(plan_response.content))
        results = {}

        for step in delegations:
            specialist = self.specialists[step["specialist"]]
            context = {d: results[d] for d in step.get("depends_on", []) if d in results}
            result = self._run_specialist(
                specialist, step["task"], context
            )
            results[step["specialist"]] = result

        return self._synthesize(goal, results)

    def _run_specialist(
        self, config: AgentConfig, task: str, context: dict
    ) -> str:
        """Run a single specialist agent."""
        messages = [
            {
                "role": "user",
                "content": f"Task: {task}\nContext: {json.dumps(context)}",
            }
        ]
        response = client.messages.create(
            model=config.model,
            max_tokens=4096,
            system=config.system_prompt,
            tools=config.tools,
            messages=messages,
        )
        return extract_text(response.content)

    def _synthesize(self, goal: str, results: dict) -> str:
        """Combine specialist results into a final answer."""
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Original goal: {goal}\n\n"
                        f"Specialist results:\n{json.dumps(results, indent=2)}\n\n"
                        "Synthesize these results into a coherent final answer."
                    ),
                }
            ],
        )
        return extract_text(response.content)
```

### Step 6: Add Guardrails and Safety

**Input Validation Layer**:

```python
@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""
    modified_input: str | None = None


class AgentGuardrails:
    """Safety layer wrapping agent execution."""

    def __init__(self, max_tool_calls: int = 50, max_cost_usd: float = 1.0):
        self.max_tool_calls = max_tool_calls
        self.max_cost_usd = max_cost_usd
        self.tool_call_count = 0
        self.estimated_cost = 0.0
        self.blocked_patterns = [
            r"rm\s+-rf\s+/",           # Destructive filesystem commands
            r"DROP\s+TABLE",            # SQL injection attempts
            r"curl.*\|\s*bash",         # Remote code execution
        ]

    def check_input(self, user_input: str) -> GuardrailResult:
        """Validate user input before agent processing."""
        import re
        for pattern in self.blocked_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return GuardrailResult(
                    allowed=False,
                    reason=f"Input contains blocked pattern: {pattern}"
                )
        return GuardrailResult(allowed=True)

    def check_tool_call(self, tool_name: str, arguments: dict) -> GuardrailResult:
        """Validate a tool call before execution."""
        self.tool_call_count += 1

        if self.tool_call_count > self.max_tool_calls:
            return GuardrailResult(
                allowed=False,
                reason=f"Tool call limit reached ({self.max_tool_calls})"
            )

        # Block destructive file operations outside workspace
        if tool_name in ("edit_file", "write_file", "delete_file"):
            path = arguments.get("file_path", "")
            if not path.startswith(("/workspace/", "./", "src/")):
                return GuardrailResult(
                    allowed=False,
                    reason=f"File operation outside workspace: {path}"
                )

        return GuardrailResult(allowed=True)

    def check_output(self, output: str) -> GuardrailResult:
        """Validate agent output before returning to user."""
        # Check for leaked secrets or sensitive data patterns
        import re
        sensitive_patterns = [
            r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*\S+",
            r"sk-[a-zA-Z0-9]{20,}",
            r"-----BEGIN (?:RSA )?PRIVATE KEY-----",
        ]
        for pattern in sensitive_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return GuardrailResult(
                    allowed=False,
                    reason="Output may contain sensitive data. Redacting."
                )
        return GuardrailResult(allowed=True)
```

### Step 7: Evaluate and Test Agents

**Evaluation Framework**:

```python
@dataclass
class EvalCase:
    """A single evaluation case for an agent."""
    name: str
    input: str
    expected_output: str | None = None       # For exact match
    expected_contains: list[str] | None = None  # For partial match
    max_tool_calls: int = 20
    max_seconds: float = 60.0
    tags: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    case_name: str
    passed: bool
    output: str
    tool_calls: int
    duration_seconds: float
    failure_reason: str = ""


def run_evaluation(agent_fn, cases: list[EvalCase]) -> list[EvalResult]:
    """Run an evaluation suite against an agent function."""
    import time
    results = []

    for case in cases:
        start = time.time()
        try:
            output = agent_fn(case.input)
            duration = time.time() - start

            passed = True
            reason = ""

            if case.expected_output and output.strip() != case.expected_output.strip():
                passed = False
                reason = f"Expected '{case.expected_output}', got '{output[:200]}'"

            if case.expected_contains:
                missing = [s for s in case.expected_contains if s not in output]
                if missing:
                    passed = False
                    reason = f"Output missing expected strings: {missing}"

            if duration > case.max_seconds:
                passed = False
                reason = f"Timeout: {duration:.1f}s > {case.max_seconds}s"

            results.append(EvalResult(
                case_name=case.name,
                passed=passed,
                output=output[:500],
                tool_calls=0,  # Instrumented via guardrails
                duration_seconds=duration,
                failure_reason=reason,
            ))

        except Exception as e:
            results.append(EvalResult(
                case_name=case.name,
                passed=False,
                output="",
                tool_calls=0,
                duration_seconds=time.time() - start,
                failure_reason=str(e),
            ))

    return results


def print_eval_report(results: list[EvalResult]):
    """Print a summary report of evaluation results."""
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\nAgent Evaluation: {passed}/{total} passed ({100*passed/total:.0f}%)\n")

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.case_name} ({r.duration_seconds:.1f}s)")
        if not r.passed:
            print(f"         Reason: {r.failure_reason}")
```

### Step 8: Instrument for Observability

**Structured Logging and Tracing**:

```python
import logging
import uuid
from contextvars import ContextVar
from functools import wraps

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

logger = logging.getLogger("agent")


def new_trace() -> str:
    """Start a new trace and return its ID."""
    tid = uuid.uuid4().hex[:12]
    trace_id_var.set(tid)
    return tid


def traced(func):
    """Decorator that adds trace context to log messages."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        trace_id = trace_id_var.get()
        logger.info(
            "step_start",
            extra={
                "trace_id": trace_id,
                "step": func.__name__,
                "args_summary": str(args)[:200],
            },
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                "step_end",
                extra={
                    "trace_id": trace_id,
                    "step": func.__name__,
                    "result_summary": str(result)[:200],
                },
            )
            return result
        except Exception as e:
            logger.error(
                "step_error",
                extra={
                    "trace_id": trace_id,
                    "step": func.__name__,
                    "error": str(e),
                },
            )
            raise
    return wrapper


@traced
def agent_step(task: str) -> str:
    """Example instrumented agent step."""
    return run_react_agent(task)
```

**Cost Tracking**:

```python
@dataclass
class UsageTracker:
    """Track token usage and estimated cost across agent runs."""
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0

    # Approximate pricing per million tokens (adjust to current rates)
    INPUT_COST_PER_M = 3.0
    OUTPUT_COST_PER_M = 15.0

    def record(self, response):
        """Record usage from an API response."""
        self.input_tokens += response.usage.input_tokens
        self.output_tokens += response.usage.output_tokens
        self.tool_calls += sum(
            1 for b in response.content if getattr(b, "type", "") == "tool_use"
        )

    @property
    def estimated_cost(self) -> float:
        return (
            (self.input_tokens / 1_000_000) * self.INPUT_COST_PER_M
            + (self.output_tokens / 1_000_000) * self.OUTPUT_COST_PER_M
        )

    def summary(self) -> str:
        return (
            f"Tokens: {self.input_tokens:,} in / {self.output_tokens:,} out | "
            f"Tool calls: {self.tool_calls} | "
            f"Est. cost: ${self.estimated_cost:.4f}"
        )
```

## Best Practices

- **Start simple**: Begin with a ReAct loop; add complexity only when needed
- **Fail loudly**: Agents that silently fail are harder to debug than agents that error clearly
- **Limit tool count**: Keep active tools to 10-20 for reliable selection (see `tool-design` skill)
- **Budget turns**: Set explicit turn limits to prevent runaway agent loops
- **Log everything**: Structured logs with trace IDs make debugging multi-step agents tractable
- **Test trajectories, not just outputs**: Verify the agent took the right path, not just that it arrived at a plausible answer
- **Use cheaper models for planning**: Planning steps need reasoning; execution steps often need tool use. Route accordingly
- **Keep memory lean**: Summarize aggressively; stale context degrades quality faster than missing context
- **Add guardrails early**: Safety checks are easier to add during development than to retrofit
- **Version your prompts**: System prompts are code; treat them with the same versioning discipline

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

## Quality Checklist

- [ ] Agent architecture chosen and justified for the use case
- [ ] Tools defined with clear descriptions and structured error responses
- [ ] Memory system matches persistence requirements (session vs. long-term)
- [ ] Planning loop includes replanning on failure
- [ ] Turn and cost limits configured to prevent runaway execution
- [ ] Guardrails validate inputs, tool calls, and outputs
- [ ] Evaluation suite covers happy path, edge cases, and failure modes
- [ ] Observability in place: structured logs, trace IDs, cost tracking
- [ ] Multi-agent communication protocol defined (if applicable)
- [ ] Prompts versioned and stored alongside code

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We don't need turn limits — the agent will stop when it's done" | Agents in infinite loops or with misconfigured tools have run for hours and incurred thousands of dollars in API costs before operators noticed; hard turn and cost limits are non-negotiable safety mechanisms, not optional guardrails. |
| "Guardrails slow down the agent and hurt task performance" | Guardrails that reject invalid tool calls prevent irreversible side effects (deleting production data, sending emails to real users) that no subsequent action can undo; the performance cost of validation is orders of magnitude cheaper than remediation. |
| "We'll add observability after we validate the agent works" | Agent failures in production are non-deterministic and context-dependent; without structured logs and trace IDs from the first deployment, diagnosing why the agent chose an unexpected action path is practically impossible. |
| "A single monolithic agent is simpler than multi-agent orchestration" | A single agent with 50+ tools saturates the context window with tool descriptions, degrading routing accuracy; multi-agent systems with 5-10 focused tools per agent consistently outperform monolithic agents on complex tasks. |
| "Memory is optional for agents that run on short tasks" | Short-task agents that interact with the same user across sessions without memory force users to re-explain context every time; compounding user friction is the primary reason real-world agent adoption stalls. |
| "We'll handle planning failures by restarting the agent" | Restart without replanning repeats the same failure; agents need explicit failure detection and a replanning step that incorporates the failure as new context, not a blind retry of the same plan. |

## Anti-Patterns (Opus 4.7)

Three anti-patterns that specifically hurt Opus 4.7 agent workloads. These are distinct from the Common Rationalizations above: they are patterns that feel correct and used to be correct for Opus 4.6, but compound cost without matching quality gains on 4.7.

| Anti-pattern | Why it feels right | Why it's wrong in Opus 4.7 | What to do instead |
|---|---|---|---|
| Fixed thinking budgets (`max_thinking_tokens=20000`) | Predictable cost per turn; easy to reason about. | Opus 4.7 scales thinking adaptively per turn. A fixed budget truncates reasoning on hard turns and wastes budget on easy ones. | Omit `max_thinking_tokens`; set `effortLevel` instead. Drop one tier (e.g., `xhigh` -> `high`) for cost control. |
| Excessive tool-calling as "thorough investigation" | "The agent looked at everything, so the answer is well-grounded." | Opus 4.7 prefers reasoning; too many tool calls burn tokens without adding signal and can crowd out the actual problem solving. | Reason first; invoke tools only when external state is needed. Explicit tool-invocation prompts beat implicit "check everything." |
| `max` effort level on extended runs (loop-operator, temporal workflows, multi-iteration agents) | "Best results always." | `max` compounds per iteration - 20 loop turns at `max` can 2-3x cost vs `xhigh` with no observable quality win on routine subtasks. | Default `xhigh` for runs; reserve `max` for single hard one-shot analyses. For parallel fan-out, de-escalate to `high`. |

Cross-links:
- Full decision guidance: [prompt-engineering - Effort-Level Strategy](../prompt-engineering/SKILL.md) and the [Opus 4.7 Practices](../prompt-engineering/SKILL.md#opus-47-practices) section.
- Output-side token optimization (distinct from tool-call frequency): [prompt-token-optimization](../../orchestration/prompt-token-optimization/SKILL.md).

## Verification

- [ ] Turn limit and cost limit are configured and enforced: agent stops and reports status when limits are reached
- [ ] Input guardrail validates all tool call arguments before execution; invalid inputs are rejected with an error, not silently corrected
- [ ] Structured logs with trace IDs exist for every agent run, covering tool calls, tool results, and planning decisions
- [ ] Evaluation suite runs on at least three scenarios: happy path, tool failure, and ambiguous input
- [ ] Memory layer (if applicable) persists and retrieves context across sessions: verified by running the same query in two separate sessions
- [ ] Replanning logic is triggered on tool failure: confirmed by injecting a tool error and observing the agent adjusts its plan

## References

- [references/lifecycle-hooks.md](references/lifecycle-hooks.md) - The agent-being-built lifecycle hook pattern (on_turn_start / on_turn_end / on_tool_call_pre / on_tool_call_post / on_error) for audit logging, retries, persona shifts, cost caps, and structured error recovery. Distinct from AI-assistant runtime hooks.
- [references/multimodal-ingestion.md](references/multimodal-ingestion.md) - Agent multimodal input patterns: the two ingestion shapes (in-memory bytes vs. filesystem path), supported media families, and mixed prompt lists. Agent input, as distinct from output evaluation.
- [references/sdk-structured-output.md](references/sdk-structured-output.md) - Constraining agent output to a Pydantic schema (the response-contract pattern), its failure modes, and the retry-then-fail-closed recovery. Output constraint, as distinct from output evaluation.

## Related Skills

- `tool-design` - Designing tools and APIs for agent consumption
- `prompt-engineering` - Crafting effective system prompts for agents
- `rag-implementation` - Building retrieval systems agents can query
- `context-manager` - Managing context budgets in long agent sessions
- `ai-agent-governance` - Compliance and governance for AI agent deployments

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
