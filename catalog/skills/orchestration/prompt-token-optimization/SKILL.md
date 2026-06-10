---
name: prompt-token-optimization
description: Minimize token consumption and maximize effective context window usage through programmatic tool calling, dynamic filtering, tool search deferral, and context hygiene. Use when sessions are hitting context limits, costs are too high, or tool-heavy workflows consume excessive tokens.
summary_l0: "Minimize token consumption with programmatic tool calling and context hygiene"
overview_l1: "This skill minimizes token consumption and maximizes effective context window usage through programmatic tool calling, dynamic filtering, tool search deferral, and context hygiene. Use it when sessions are hitting context limits, costs are too high, tool-heavy workflows consume excessive tokens, or you need to optimize AI coding session economics. Key capabilities include programmatic tool call optimization (batching, filtering, deferred execution), dynamic context filtering based on task relevance, tool search deferral to reduce unnecessary reads, context hygiene practices (summarizing instead of echoing, suppressing verbose output), token consumption tracking, and cost-per-task optimization. The expected output is optimized session workflows with reduced token consumption, cost metrics, and context hygiene guidelines. Trigger phrases: token optimization, reduce tokens, context window, tool tokens, session cost, programmatic tool calling, context hygiene, token budget."
---

# Prompt and Token Optimization

Specialized expertise in reducing token consumption and maximizing the value extracted from every token in an AI coding assistant session. These techniques can reduce input tokens by 24-85% depending on the workflow, directly lowering cost and improving response quality by keeping the context window focused on relevant information.

> **Programmatic counterpart -- the `nexus-context-compressor` engine.** Step 3 below (Dynamic Filtering) is the manual discipline of trimming large outputs before they enter the window. Nexus-Hub ships an engine that *enforces* that discipline at the tool boundary: `extensions/nexus-context-compressor/`, a local-first PreToolUse compressor that deduplicates JSON dumps, elides code bodies AST-aware, and persists every dropped span behind a reversible `<<ccr:HASH N_rows>>` marker. Reach for it when tool output is the measured bottleneck (the largest single category in most sessions); the techniques in this skill cover the rest of the budget (tool-call batching, deferral, tuning). See [[context-optimization]] for setup.

## When to Use This Skill

Use this skill for:

- Sessions that frequently hit context window limits and require compaction
- Workflows with many tool calls that consume tokens on repetitive patterns
- Projects with 50+ MCP tools where tool definitions alone consume significant context
- Batch processing tasks where token cost scales linearly with item count
- Teams tracking AI spend who need to reduce per-task cost
- Any situation where you notice degraded response quality late in a session (a symptom of context pressure)

**Trigger phrases**: "reduce token usage", "optimize context", "too many tokens", "context window full", "save tokens", "reduce cost", "compact context", "token budget", "context pressure", "PTC", "programmatic tool calling"

## What This Skill Does

Provides token optimization capabilities including:

- **Usage Auditing**: Measuring baseline token consumption to identify waste
- **Programmatic Tool Calling (PTC)**: Replacing sequential tool calls with scripted orchestration
- **Dynamic Filtering**: Removing irrelevant content before it enters the context window
- **Tool Search Deferral**: Loading tool definitions on demand instead of upfront
- **Tool Definition Tuning**: Adding examples to tool definitions to improve accuracy per token spent
- **Context Hygiene**: Manual compaction strategies and subagent isolation patterns

## Instructions

### Step 1: Audit Current Token Usage

Before optimizing, measure your baseline. You cannot improve what you do not measure.

**Measurement Methods**:

1. Use `/cost` in Claude Code to see cumulative session cost
2. Use `/usage` to check current context window utilization percentage
3. For API-based workflows, log `usage.input_tokens` and `usage.output_tokens` from each response

**Baseline Tracking Template**:

```markdown
## Token Audit: [Task Name]

| Metric | Value |
|--------|-------|
| Task description | [what you did] |
| Total input tokens | [number] |
| Total output tokens | [number] |
| Number of tool calls | [count] |
| Context compactions triggered | [count] |
| Session cost | [dollar amount] |
| Quality of final output | [1-5 rating] |
```

Run three representative tasks and record baselines before applying any optimizations. This gives you a reliable before/after comparison.

### Step 2: Apply Programmatic Tool Calling (PTC)

Instead of letting the model make sequential tool calls (each consuming a round-trip of tokens), write a script that orchestrates multiple tool operations in a single execution.

**The Problem**: A typical file exploration sequence might involve 8-10 sequential tool calls (list directory, read file, read another file, grep for pattern, etc.), each requiring the model to generate a tool call and process the result.

**The Solution**: Write a Python or Bash script that performs all the exploration in one shot and returns a structured summary.

**Example: Before PTC (8 tool calls, ~12,000 tokens)**:

```
1. list_directory("src/")
2. read_file("src/main.py")
3. read_file("src/utils.py")
4. grep("def process", "src/")
5. read_file("src/processor.py")
6. list_directory("tests/")
7. read_file("tests/test_processor.py")
8. grep("import processor", "src/")
```

**Example: After PTC (1 tool call, ~4,500 tokens)**:

```python
# explore_codebase.py
import os
import re
import json

results = {}

# List key directories
for d in ["src/", "tests/"]:
    results[f"files_in_{d}"] = os.listdir(d)

# Read and summarize key files
for f in ["src/main.py", "src/utils.py", "src/processor.py"]:
    with open(f) as fh:
        content = fh.read()
        # Extract only function signatures, not full bodies
        results[f"signatures_{f}"] = re.findall(r"^(def \w+\(.*?\)):", content, re.MULTILINE)

# Find specific patterns
results["process_functions"] = []
for root, dirs, files in os.walk("src/"):
    for fname in files:
        if fname.endswith(".py"):
            path = os.path.join(root, fname)
            with open(path) as fh:
                for i, line in enumerate(fh, 1):
                    if "def process" in line:
                        results["process_functions"].append(f"{path}:{i}: {line.strip()}")

print(json.dumps(results, indent=2))
```

**Typical savings**: 30-40% token reduction for exploration-heavy tasks.

### Step 3: Implement Dynamic Filtering

Filter large outputs before they enter the context window. This is especially important for web searches, file reads, and API responses.

**Filtering Strategies**:

1. **Truncate file reads**: Read only the first N lines of large files, or read specific line ranges when you know where the relevant code lives
2. **Grep before read**: Use grep to find relevant lines first, then read only the surrounding context
3. **Summarize API responses**: Pipe large JSON responses through `jq` to extract only the fields you need
4. **Filter search results**: When searching documentation or the web, extract only titles and URLs first, then fetch only the most relevant pages

**Example: Before Filtering (8,000 tokens of package.json)**:

```
read_file("package.json")  # Returns entire 400-line file
```

**Example: After Filtering (800 tokens)**:

```bash
# Extract only dependency names and versions
jq '{dependencies, devDependencies}' package.json
```

**Typical savings**: 20-30% input token reduction for data-heavy workflows.

### Step 4: Use Tool Search for Large Tool Sets

When a project configures many MCP tools (50+), every tool definition is included in the system prompt, consuming tokens before you even start working. Tool search defers loading until a tool is actually needed.

**How It Works**:

1. Tools are registered as "deferred" and only their names are listed in the system prompt (minimal tokens)
2. When you need a tool, call `ToolSearch` with a keyword query or `select:tool_name`
3. The tool definition is loaded into context only when selected
4. Unused tools never consume context tokens

**Impact by Tool Count**:

| Total Tools | Without Deferral | With Deferral | Savings |
|-------------|-----------------|---------------|---------|
| 10 tools | ~3,000 tokens | ~3,000 tokens | 0% (not worth it) |
| 25 tools | ~7,500 tokens | ~2,500 tokens | 67% |
| 50 tools | ~15,000 tokens | ~2,500 tokens | 83% |
| 100 tools | ~30,000 tokens | ~2,500 tokens | 92% |

**When to Apply**: If your project has more than 20 MCP tools, configure infrequently-used tools as deferred. Keep your 5-10 most-used tools loaded eagerly.

### Step 5: Optimize Tool Use Examples

Adding concrete `input_examples` to tool definitions improves the model's ability to call tools correctly, reducing wasted tokens from failed or incorrect tool calls.

**Before (no examples, 72% accuracy)**:

```json
{
  "name": "query_database",
  "description": "Run a SQL query against the project database",
  "parameters": {
    "query": { "type": "string", "description": "SQL query to execute" }
  }
}
```

**After (with examples, 90%+ accuracy)**:

```json
{
  "name": "query_database",
  "description": "Run a SQL query against the project database",
  "parameters": {
    "query": { "type": "string", "description": "SQL query to execute" }
  },
  "input_examples": [
    { "query": "SELECT id, name FROM users WHERE active = true LIMIT 10" },
    { "query": "SELECT COUNT(*) FROM orders WHERE created_at > '2026-01-01'" }
  ]
}
```

**Why This Matters**: Every failed tool call wastes tokens on the call itself, the error response, and the retry. Improving first-call accuracy from 72% to 90% eliminates roughly 20% of wasted tool-call tokens.

### Step 6: Context Window Hygiene

Manage the context window proactively rather than waiting for automatic compaction (which loses information unpredictably).

**Manual Compaction Strategy**:

1. Monitor context usage with `/usage` periodically
2. When usage reaches 50%, run `/compact` with a summary prompt that preserves key decisions and file paths
3. Structure your compact prompt to retain: current task, files modified so far, decisions made, next steps

**Subagent Isolation Pattern**:

For tasks with distinct phases, use subagents (via the `Task` tool or separate sessions) to isolate each phase's context:

```
Main session (orchestrator):
  ├── Subagent 1: Research (explores codebase, returns summary)
  ├── Subagent 2: Implementation (receives plan, returns code changes)
  └── Subagent 3: Testing (receives file list, returns test results)
```

Each subagent starts with a clean context window and returns only a compact summary to the parent. This prevents context accumulation across phases.

**The 50% Rule**: Design each subtask to complete within 50% of the context window. This leaves room for tool outputs, errors, and iteration without triggering compaction.

### Step 7: Measure and Iterate

After applying optimizations, re-run the same representative tasks and compare.

**After-Optimization Tracking**:

```markdown
## Token Optimization Results: [Task Name]

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total input tokens | [number] | [number] | [percentage] |
| Total output tokens | [number] | [number] | [percentage] |
| Number of tool calls | [count] | [count] | [reduction] |
| Context compactions | [count] | [count] | [reduction] |
| Session cost | [amount] | [amount] | [savings] |
| Quality of output | [1-5] | [1-5] | [change] |

### Techniques Applied
- [ ] Programmatic Tool Calling
- [ ] Dynamic Filtering
- [ ] Tool Search Deferral
- [ ] Tool Definition Examples
- [ ] Manual Compaction
- [ ] Subagent Isolation
```

**Iterate**: If savings are below 20%, identify which technique has the most room for improvement. Typically, PTC and dynamic filtering yield the largest gains for interactive coding sessions, while tool deferral dominates for tool-heavy MCP setups.

## Best Practices

- **Measure before optimizing** to avoid premature optimization on the wrong bottleneck
- **Start with the highest-impact technique** for your workflow (PTC for exploration-heavy, filtering for data-heavy, deferral for tool-heavy)
- **Do not sacrifice quality for token savings**; if compacting too aggressively causes the model to lose critical context, back off
- **Keep exploration scripts version-controlled** so they can be reused across sessions
- **Review compaction summaries** to ensure no critical information was lost
- **Combine techniques** for compounding savings (e.g., PTC + filtering can yield 50%+ reduction)
- **Set token budgets per task** and treat them as soft constraints to build discipline around context management
- **Revisit your optimization strategy** monthly as model capabilities and pricing change

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will optimize the prompt that feels longest." | Intuition picks the wrong target. Without a baseline token audit you often shave a 200-token prompt while a tool-definition block silently eats 8,000 tokens per turn. Measure first, then optimize the actual bottleneck. |
| "Compacting harder always saves more, so more is better." | Past a point, aggressive compaction strips the context the model needs and quality drops, forcing re-work that costs more tokens than it saved. Token reduction that degrades output is a net loss, not a win. |
| "Programmatic tool calling is overkill; I will just call the tools one at a time." | For an exploration-heavy workflow, sequential tool calls re-pay the round-trip token cost on every step. A single script that batches the calls and returns only the relevant slice is where the 24-85% reduction comes from. |

## Verification

- [ ] A baseline token audit was captured before any optimization
- [ ] The chosen technique targets the measured bottleneck (PTC, filtering, or tool deferral)
- [ ] Post-optimization token consumption is measured and compared to baseline
- [ ] Output quality was checked to confirm compaction did not strip critical context
- [ ] The savings (percent reduction) are documented for the task

## Related Skills

- [[context-compression]] - Techniques for compressing context content
- [[context-manager]] - Managing information flow across workflow phases
- [[context-degradation]] - Detecting and recovering from context quality loss
- [[context-optimization]] - Configures the `nexus-context-compressor` engine that enforces Step 3's dynamic filtering automatically at the tool boundary

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Anthropic tool use best practices, programmatic tool calling patterns, MCP optimization techniques
