---
name: claude-agent-sdk
description: Production-grade Claude Agent SDK integration in TypeScript -- multi-provider routing, retry logic with exponential backoff, spending cap enforcement, per-invocation audit logging, error classification, and MCP tool registration. Use when building autonomous Claude agents in Node.js/TypeScript.
summary_l0: "Integrate Claude Agent SDK in TypeScript with provider routing, spending caps, and audit logging"
overview_l1: "This skill provides production patterns for integrating the Anthropic Claude Agent SDK in TypeScript/Node.js projects. Use it when building autonomous Claude agents, implementing multi-provider LLM routing (Anthropic, AWS Bedrock, Google Vertex AI, OpenRouter), adding spending cap enforcement, structuring per-invocation audit logging, classifying errors as retryable versus fatal, registering MCP tools, or designing agent identity via system prompts. Key capabilities include provider configuration and credential setup, exponential backoff retry logic with jitter, hard budget limits with automatic session termination, structured audit trails, error classification hierarchies, and MCP tool registration within the SDK context. The expected output is production-grade TypeScript agent code with full observability, cost controls, and multi-provider failover. Trigger phrases: Claude Agent SDK, Claude SDK TypeScript, autonomous agent Node.js, multi-provider Claude, agent spending cap, Claude SDK retry, Claude SDK audit, agent SDK production."
---

# Claude Agent SDK (TypeScript)

Production patterns for integrating the Anthropic Claude Agent SDK in TypeScript/Node.js projects. Covers the full operational stack from provider routing and credential management to spending cap enforcement, structured audit logging, and MCP tool registration. Grounded in patterns from Shannon -- a 13-agent autonomous security testing pipeline achieving 96.15% benchmark success using Claude Agent SDK v0.2.38.

## When to Use This Skill

Use this skill for:

- Building autonomous Claude agents in TypeScript/Node.js
- Implementing multi-provider LLM routing (Anthropic, AWS Bedrock, Google Vertex AI, OpenRouter)
- Adding spending cap enforcement to prevent runaway agent costs
- Structuring per-invocation audit logging for agent observability
- Classifying errors as retryable vs. fatal in agent workflows
- Registering MCP tools within Claude Agent SDK context
- Designing agent identity and specialization via system prompts

**Trigger phrases**: "Claude Agent SDK", "Claude SDK TypeScript", "autonomous agent Node.js", "multi-provider Claude", "agent spending cap", "Claude SDK retry", "Claude SDK audit", "agent SDK production"

## What This Skill Does

Provides production-grade Claude Agent SDK patterns including:

- **Provider Configuration**: Credential setup for Anthropic, AWS Bedrock, Google Vertex AI, and OpenRouter
- **Retry Logic**: Exponential backoff with jitter for transient API failures
- **Spending Caps**: Hard budget limits at the SDK invocation layer with automatic session termination
- **Audit Logging**: Structured per-invocation logs with agent ID, model tier, token counts, and cost estimates
- **Error Classification**: Taxonomy of retryable vs. fatal errors to prevent infinite retry loops
- **MCP Integration**: Tool registration patterns for Playwright, filesystem, and custom MCP servers within agent context
- **Agent Specialization**: System prompt patterns for creating focused, single-responsibility agents

## Instructions

### Step 1: Install and Configure the SDK

```bash
npm install @anthropic-ai/sdk
# For AWS Bedrock provider
npm install @anthropic-ai/bedrock-sdk
# For Google Vertex AI provider
npm install @anthropic-ai/vertex-sdk
```

**TypeScript configuration** (use strict mode for agent code -- catches type errors before runtime):

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "outDir": "dist"
  }
}
```

### Step 2: Set Up Multi-Provider Client

Support multiple LLM providers behind a single interface. This allows switching between Anthropic direct, AWS Bedrock, Google Vertex AI, and OpenRouter without changing agent code.

**Environment variables** (`.env.example`):

```bash
# Provider selection (required): anthropic | bedrock | vertex | openrouter
AI_PROVIDER=anthropic

# Anthropic direct
ANTHROPIC_API_KEY=sk-ant-...

# AWS Bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-6-20251001-v1:0

# Google Vertex AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_MODEL_ID=claude-sonnet-4-6@20251001

# OpenRouter (unified gateway)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Model tier selection
MODEL_TIER=sonnet  # haiku | sonnet | opus
```

**Provider factory** (`src/ai/client-factory.ts`):

```typescript
import Anthropic from "@anthropic-ai/sdk";

export type Provider = "anthropic" | "bedrock" | "vertex" | "openrouter";
export type ModelTier = "haiku" | "sonnet" | "opus";

const MODEL_IDS: Record<Provider, Record<ModelTier, string>> = {
  anthropic: {
    haiku: "claude-haiku-4-5-20251001",
    sonnet: "claude-sonnet-4-6",
    opus: "claude-opus-4-6",
  },
  bedrock: {
    haiku: "anthropic.claude-haiku-4-5-20251001-v1:0",
    sonnet: "anthropic.claude-sonnet-4-6-20251001-v1:0",
    opus: "anthropic.claude-opus-4-6-20251001-v1:0",
  },
  vertex: {
    haiku: "claude-haiku-4-5@20251001",
    sonnet: "claude-sonnet-4-6@20251001",
    opus: "claude-opus-4-6@20251001",
  },
  openrouter: {
    haiku: "anthropic/claude-haiku-4-5",
    sonnet: "anthropic/claude-sonnet-4-6",
    opus: "anthropic/claude-opus-4-6",
  },
};

export interface ClientConfig {
  provider: Provider;
  tier: ModelTier;
  maxBudgetUsd?: number;
}

export function createClient(config: ClientConfig): Anthropic {
  const { provider } = config;

  switch (provider) {
    case "anthropic":
      return new Anthropic({ apiKey: process.env["ANTHROPIC_API_KEY"] });

    case "openrouter":
      return new Anthropic({
        apiKey: process.env["OPENROUTER_API_KEY"],
        baseURL: process.env["OPENROUTER_BASE_URL"] ?? "https://openrouter.ai/api/v1",
      });

    case "bedrock":
      // Use @anthropic-ai/bedrock-sdk and wrap in Anthropic-compatible interface
      throw new Error("Use createBedrockClient() for Bedrock provider");

    case "vertex":
      // Use @anthropic-ai/vertex-sdk and wrap in Anthropic-compatible interface
      throw new Error("Use createVertexClient() for Vertex provider");

    default: {
      const _exhaustive: never = provider;
      throw new Error(`Unknown provider: ${_exhaustive}`);
    }
  }
}

export function resolveModelId(provider: Provider, tier: ModelTier): string {
  const tiers = MODEL_IDS[provider];
  const modelId = tiers[tier];
  return modelId;
}
```

### Step 3: Implement Retry Logic with Exponential Backoff

Transient API failures (rate limits, network timeouts, 5xx errors) should trigger retries. Fatal errors (invalid API key, model not found, schema violation) should propagate immediately.

```typescript
// src/ai/retry.ts

export interface RetryConfig {
  maxAttempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterFactor: number;
}

export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  baseDelayMs: 1000,
  maxDelayMs: 30_000,
  jitterFactor: 0.25,
};

/** Errors that should NOT be retried -- fail immediately. */
const FATAL_STATUS_CODES = new Set([400, 401, 403, 404, 422]);

export function isRetryable(error: unknown): boolean {
  if (error instanceof Error) {
    const msg = error.message.toLowerCase();
    // Retry on rate limits and server errors
    if (msg.includes("rate limit") || msg.includes("429")) return true;
    if (msg.includes("timeout") || msg.includes("econnreset")) return true;
    if (msg.includes("503") || msg.includes("529")) return true;
  }
  // Check for Anthropic API error status codes
  if (typeof error === "object" && error !== null && "status" in error) {
    const status = (error as { status: number }).status;
    return !FATAL_STATUS_CODES.has(status);
  }
  return false;
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG,
  context: string = "operation",
): Promise<T> {
  let lastError: unknown;

  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (!isRetryable(error) || attempt === config.maxAttempts) {
        throw error;
      }

      const baseDelay = Math.min(
        config.baseDelayMs * Math.pow(2, attempt - 1),
        config.maxDelayMs,
      );
      const jitter = baseDelay * config.jitterFactor * (Math.random() * 2 - 1);
      const delay = Math.max(0, baseDelay + jitter);

      console.warn(
        `[retry] ${context} failed (attempt ${attempt}/${config.maxAttempts}), ` +
          `retrying in ${Math.round(delay)}ms`,
        { error: error instanceof Error ? error.message : String(error) },
      );

      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}
```

### Step 4: Enforce Spending Caps

Autonomous agents can accumulate significant API costs. Implement hard budget limits at the invocation layer -- before sending requests -- so runaway agents terminate cleanly rather than silently draining budget.

```typescript
// src/ai/budget-guard.ts

export class BudgetExceededError extends Error {
  constructor(
    public readonly spent: number,
    public readonly limit: number,
  ) {
    super(`Budget exceeded: $${spent.toFixed(4)} spent, $${limit.toFixed(2)} limit`);
    this.name = "BudgetExceededError";
  }
}

export class BudgetGuard {
  private spentUsd: number = 0;

  // Approximate pricing per million tokens (update to current rates)
  private static readonly INPUT_COST_PER_M_USD = 3.0;
  private static readonly OUTPUT_COST_PER_M_USD = 15.0;

  constructor(private readonly maxBudgetUsd: number) {}

  /** Call BEFORE each LLM invocation to check if budget allows it. */
  checkBudget(): void {
    if (this.spentUsd >= this.maxBudgetUsd) {
      throw new BudgetExceededError(this.spentUsd, this.maxBudgetUsd);
    }
  }

  /** Call AFTER each LLM invocation to record usage. */
  recordUsage(inputTokens: number, outputTokens: number): void {
    const cost =
      (inputTokens / 1_000_000) * BudgetGuard.INPUT_COST_PER_M_USD +
      (outputTokens / 1_000_000) * BudgetGuard.OUTPUT_COST_PER_M_USD;
    this.spentUsd += cost;
  }

  get totalSpent(): number {
    return this.spentUsd;
  }

  get remainingBudget(): number {
    return Math.max(0, this.maxBudgetUsd - this.spentUsd);
  }

  summary(): string {
    return (
      `$${this.spentUsd.toFixed(4)} spent / $${this.maxBudgetUsd.toFixed(2)} limit ` +
      `($${this.remainingBudget.toFixed(4)} remaining)`
    );
  }
}
```

### Step 5: Build the Agent Executor

The executor wraps the Claude SDK client with retry logic, budget enforcement, and audit logging. This is the single point through which all LLM calls flow.

```typescript
// src/ai/agent-executor.ts

import Anthropic from "@anthropic-ai/sdk";
import { withRetry, DEFAULT_RETRY_CONFIG } from "./retry.js";
import { BudgetGuard, BudgetExceededError } from "./budget-guard.js";
import { AuditLogger } from "./audit-logger.js";
import { resolveModelId, type Provider, type ModelTier } from "./client-factory.js";

export interface AgentConfig {
  agentId: string;
  systemPrompt: string;
  provider: Provider;
  tier: ModelTier;
  maxBudgetUsd: number;
  maxTokens?: number;
}

export interface AgentMessage {
  role: "user" | "assistant";
  content: string;
}

export class AgentExecutor {
  private readonly budget: BudgetGuard;
  private readonly modelId: string;

  constructor(
    private readonly client: Anthropic,
    private readonly config: AgentConfig,
    private readonly logger: AuditLogger,
  ) {
    this.budget = new BudgetGuard(config.maxBudgetUsd);
    this.modelId = resolveModelId(config.provider, config.tier);
  }

  async invoke(
    messages: AgentMessage[],
    tools?: Anthropic.Tool[],
  ): Promise<Anthropic.Message> {
    // 1. Check budget before invoking
    this.budget.checkBudget();

    const startMs = Date.now();

    // 2. Call the SDK with retry
    const response = await withRetry(
      () =>
        this.client.messages.create({
          model: this.modelId,
          max_tokens: this.config.maxTokens ?? 8192,
          system: this.config.systemPrompt,
          messages,
          ...(tools && tools.length > 0 ? { tools } : {}),
        }),
      DEFAULT_RETRY_CONFIG,
      `${this.config.agentId}:invoke`,
    );

    // 3. Record usage after successful response
    const { input_tokens, output_tokens } = response.usage;
    this.budget.recordUsage(input_tokens, output_tokens);

    // 4. Audit log
    this.logger.log({
      agentId: this.config.agentId,
      model: this.modelId,
      inputTokens: input_tokens,
      outputTokens: output_tokens,
      durationMs: Date.now() - startMs,
      stopReason: response.stop_reason ?? "unknown",
      budgetStatus: this.budget.summary(),
    });

    return response;
  }

  get budgetStatus(): string {
    return this.budget.summary();
  }
}
```

### Step 6: Implement Structured Audit Logging

Every LLM invocation should produce a structured log entry. This enables cost attribution, performance profiling, and debugging of multi-agent sessions.

```typescript
// src/ai/audit-logger.ts

import { appendFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

export interface AuditEntry {
  agentId: string;
  model: string;
  inputTokens: number;
  outputTokens: number;
  durationMs: number;
  stopReason: string;
  budgetStatus: string;
  timestamp?: string;
}

export class AuditLogger {
  private readonly logPath: string;

  constructor(logDir: string = "audit-logs") {
    mkdirSync(logDir, { recursive: true });
    this.logPath = join(logDir, `session-${Date.now()}.jsonl`);
  }

  log(entry: AuditEntry): void {
    const record: AuditEntry = {
      ...entry,
      timestamp: new Date().toISOString(),
    };
    appendFileSync(this.logPath, JSON.stringify(record) + "\n", "utf8");
  }
}
```

### Step 7: Register MCP Tools

The Claude Agent SDK supports MCP (Model Context Protocol) servers as tool providers. Register them per-agent to give each agent access to the tools it needs.

```typescript
// src/ai/mcp-registry.ts

import Anthropic from "@anthropic-ai/sdk";

export interface McpServerConfig {
  name: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
}

/**
 * Convert MCP server configs to Anthropic SDK tool format.
 * Each agent should get its own Playwright instance to avoid session conflicts.
 */
export function buildMcpTools(servers: McpServerConfig[]): Anthropic.Tool[] {
  // Note: MCP server connection is handled by the SDK internally via beta APIs.
  // For stdio-based MCP servers, pass server configs when creating the client session.
  // This utility builds the tool definitions from known server schemas.
  return servers.map((server) => ({
    name: server.name,
    description: `MCP server: ${server.name} (${server.command} ${server.args.join(" ")})`,
    input_schema: {
      type: "object" as const,
      properties: {
        command: { type: "string", description: "Tool command to invoke" },
        args: { type: "object", description: "Command arguments" },
      },
      required: ["command"],
    },
  }));
}

/** Standard MCP servers for web-automation agents. */
export const PLAYWRIGHT_MCP_CONFIG: McpServerConfig = {
  name: "playwright",
  command: "npx",
  args: ["@playwright/mcp@latest"],
};

/** Standard MCP servers for filesystem agents. */
export const FILESYSTEM_MCP_CONFIG: McpServerConfig = {
  name: "filesystem",
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
};
```

### Step 8: Define Agent Specialization via System Prompts

Single-responsibility agents outperform general-purpose agents. Give each agent a narrow, precise identity with explicit tool permissions and output format requirements.

```typescript
// src/agents/agent-definitions.ts

export interface AgentDefinition {
  id: string;
  tier: "haiku" | "sonnet" | "opus";
  systemPrompt: string;
  maxBudgetUsd: number;
}

// Pattern: Identity → Scope → Tools → Output format → Constraints
export const RESEARCH_AGENT: AgentDefinition = {
  id: "research-agent",
  tier: "sonnet",
  maxBudgetUsd: 2.0,
  systemPrompt: `You are a research agent specialized in gathering and summarizing information.

SCOPE: You answer factual questions using web search and document reading. You do not write code, make recommendations, or take actions beyond information retrieval.

TOOLS: Use the web_search tool for recent information. Use the read_document tool for specific documents.

OUTPUT: Return findings as structured JSON with fields: { summary, sources, confidence, gaps }.

CONSTRAINTS:
1. Never access URLs not provided in the task
2. Never execute code or system commands
3. Always cite sources with URLs
4. Mark uncertain facts with confidence < 0.8`,
};

export const SYNTHESIS_AGENT: AgentDefinition = {
  id: "synthesis-agent",
  tier: "opus",  // More capable model for synthesis
  maxBudgetUsd: 5.0,
  systemPrompt: `You are a synthesis agent that combines research findings into coherent reports.

SCOPE: You receive structured research from multiple sources and produce executive-level summaries. You do not conduct new research.

INPUT FORMAT: JSON array of research objects from the research agent.
OUTPUT FORMAT: Markdown report with sections: Executive Summary, Key Findings, Gaps, Recommendations.

CONSTRAINTS:
1. Only use information provided in the input -- no inference beyond what sources support
2. Explicitly note gaps and contradictions
3. Keep executive summary under 200 words`,
};
```

## Best Practices

- **One executor per agent**: Each agent gets its own `AgentExecutor` with its own `BudgetGuard`. Never share executors across agents in parallel workflows.
- **Classify errors before retrying**: Not all errors are transient. 401 (invalid key), 403 (forbidden), and 422 (schema error) should propagate immediately.
- **Set spending caps conservatively**: Start at 2x your expected cost per run. Autonomous agents can find unexpected paths that cost more than anticipated.
- **Log every invocation**: Audit logs are the primary debugging tool for multi-agent systems. Structured JSONL is easier to query than plain text.
- **Pin SDK version**: Lock `@anthropic-ai/sdk` to a specific version in `package.json`. Minor SDK updates can change tool call behavior.
- **Use strict TypeScript**: `noUncheckedIndexedAccess` prevents the most common runtime errors in agent code (array index out of bounds, optional property access).
- **Per-agent Playwright instances**: If using Playwright MCP, give each parallel agent its own browser instance to avoid session state conflicts.
- **Append-only history**: append each assistant turn to the conversation exactly as the API returned it and never edit earlier turns between requests; deliver per-turn reminders or injected context as new content rather than by rewriting history, because an edited transcript invalidates the model's own prior reasoning and any prompt cache built on it.
- **Batch independent tool calls**: prefer requesting every independent item in one response rather than one per turn; a loop that serializes independent reads pays a full round trip per item for no gain. These two are provider-specific API concerns, which is why they live here and not in the platform-agnostic instruction templates.
- **Design for idempotency**: Agent activities in durable workflow engines (Temporal) will be replayed on failure. Activities must produce the same result when run twice.

## Common Patterns

### Pattern 1: Pre-Flight Validation

Validate all prerequisites before launching expensive agent workflows.

```typescript
async function preflight(config: AgentConfig): Promise<void> {
  // 1. Check API key is present
  if (!process.env["ANTHROPIC_API_KEY"]) {
    throw new Error("ANTHROPIC_API_KEY environment variable not set");
  }

  // 2. Verify connectivity with a minimal test call
  const client = createClient({ provider: "anthropic", tier: "haiku", maxBudgetUsd: 0.01 });
  await client.messages.create({
    model: resolveModelId("anthropic", "haiku"),
    max_tokens: 1,
    messages: [{ role: "user", content: "ping" }],
  });

  // 3. Check spending cap is reasonable
  if (config.maxBudgetUsd < 0.10) {
    throw new Error(`Budget $${config.maxBudgetUsd} is too low for meaningful agent execution`);
  }
}
```

### Pattern 2: Agent-as-Tool (Nested Agents)

Use one agent as a tool for another to create hierarchical multi-agent systems.

```typescript
const orchestratorTools: Anthropic.Tool[] = [
  {
    name: "invoke_research_agent",
    description: "Delegate research tasks to the research agent. Use for any information-gathering subtask.",
    input_schema: {
      type: "object",
      properties: {
        task: { type: "string", description: "The research task to perform" },
      },
      required: ["task"],
    },
  },
];

async function handleToolCall(
  toolName: string,
  toolInput: Record<string, unknown>,
  researchExecutor: AgentExecutor,
): Promise<string> {
  if (toolName === "invoke_research_agent") {
    const task = toolInput["task"] as string;
    const response = await researchExecutor.invoke([
      { role: "user", content: task },
    ]);
    return response.content
      .filter((b) => b.type === "text")
      .map((b) => (b as { type: "text"; text: string }).text)
      .join("\n");
  }
  throw new Error(`Unknown tool: ${toolName}`);
}
```

### Pattern 3: Error Classification and Reporting

```typescript
export type ErrorClass = "retryable" | "fatal" | "budget_exceeded" | "unknown";

export function classifyError(error: unknown): ErrorClass {
  if (error instanceof BudgetExceededError) return "budget_exceeded";

  if (error instanceof Error) {
    const msg = error.message.toLowerCase();
    if (msg.includes("401") || msg.includes("403") || msg.includes("invalid api key")) {
      return "fatal";
    }
    if (msg.includes("400") || msg.includes("422") || msg.includes("schema")) {
      return "fatal";
    }
    if (msg.includes("rate limit") || msg.includes("timeout") || msg.includes("503")) {
      return "retryable";
    }
  }

  return "unknown";
}
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll call `client.messages.create` directly here, it is one call" | A direct call bypasses the `AgentExecutor`, so it has no budget check, no retry classification, and no audit entry; the one bypass is exactly the call that overspends or fails silently. |
| "An unpinned SDK version stays current automatically" | A minor SDK bump can change default model routing or tool-call serialization and break the agent at runtime with no diff in your code; pin the version and upgrade deliberately. |
| "Retrying every error is the robust default" | Retrying a fatal 400 (bad request) wastes budget and never succeeds; retry logic must distinguish retryable (429/5xx) from fatal errors. |
| "Parallel agents can share one executor and budget guard" | A shared budget guard double-counts under concurrency and a shared Playwright instance corrupts cross-agent state; each parallel agent needs its own executor and guard. |

## Verification

- [ ] SDK pinned to a specific version in `package.json`
- [ ] `BudgetGuard` initialized with a concrete dollar limit per agent
- [ ] All LLM calls routed through `AgentExecutor` (no direct `client.messages.create` outside executor)
- [ ] Retry logic distinguishes retryable from fatal errors
- [ ] Every invocation produces an audit log entry with token counts and duration
- [ ] TypeScript strict mode enabled with `noUncheckedIndexedAccess`
- [ ] Pre-flight validation runs before expensive workflow starts
- [ ] Agent system prompts include explicit output format and constraints
- [ ] Parallel agents each have their own executor, budget guard, and (if needed) Playwright instance
- [ ] `BudgetExceededError` is caught at the workflow level and terminates cleanly

## Related Skills

- [[ai-agent-development]] -- general agent architecture patterns (ReAct, planning, memory) in Python
- [[multi-provider-ai]] -- detailed provider selection criteria and configuration for Anthropic, Bedrock, Vertex, OpenRouter
- [[ai-billing-safeguards]] -- comprehensive spending cap strategies and cost attribution patterns
- [[temporal-orchestration]] -- durable workflow orchestration for parallel, fault-tolerant agent pipelines
- [[mcp-builder]] -- building custom MCP servers for Claude Agent SDK integration
- [[prompt-engineering]] -- crafting effective system prompts for specialized agents

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Reference Implementation**: Shannon (KeygraphHQ) -- 13-agent autonomous security testing pipeline
