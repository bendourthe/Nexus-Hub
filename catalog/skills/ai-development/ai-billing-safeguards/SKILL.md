---
name: ai-billing-safeguards
description: Implement hard spending caps and billing safeguards for autonomous AI agent systems -- per-session and per-task budget limits, provider-level quota controls, cost attribution audit trails, and graceful budget-exceeded termination. Use when deploying autonomous agents that run without continuous human oversight.
summary_l0: "Enforce hard spending caps and billing safeguards for autonomous AI agent systems"
overview_l1: "This skill provides production patterns for enforcing hard budget limits in autonomous AI agent systems, distinct from usage monitoring which only displays cost. Use it when deploying autonomous agents without continuous human oversight, running multi-agent pipelines where cost accumulates across parallel executions, managing production deployments where budget overruns have real financial consequences, or requiring cost attribution per team, project, or workflow. Key capabilities include hard session caps with automatic termination on breach, per-task cost limits, provider-level quota configuration, structured cost attribution audit trails, graceful budget-exceeded termination, and development environment loop protection. The expected output is SDK-layer billing enforcement code that blocks execution when limits are reached, with structured cost logging and clean termination. Trigger phrases: agent spending cap, LLM budget limit, AI cost guardrail, billing safeguard, prevent runaway agents, autonomous agent cost control, per-session budget."
---

# AI Billing Safeguards

Production patterns for enforcing hard budget limits in autonomous AI agent systems. Covers per-session spending caps, per-task cost limits, provider-level quota configuration, structured cost attribution, and graceful termination when budgets are exceeded. Distinct from usage monitoring (which displays cost) -- billing safeguards actively block execution when limits are reached.

Grounded in Shannon's approach: billing safeguards are built into the SDK invocation layer so that runaway agent loops terminate cleanly rather than silently draining budget.

## When to Use This Skill

Use this skill for:

- Autonomous agents that run without continuous human oversight
- Multi-agent pipelines where cost accumulates across parallel executions
- Production deployments where budget overruns have real financial consequences
- Enterprise AI deployments requiring cost attribution per team, project, or workflow
- Development environments where accidental infinite loops should not drain credits

**Trigger phrases**: "agent spending cap", "LLM budget limit", "AI cost guardrail", "billing safeguard", "prevent runaway agents", "autonomous agent cost control", "per-session budget"

**Distinguish from usage monitoring**: The `check-usage` skill and VS Code Claude Usage Monitor display current usage. This skill implements enforcement -- blocking execution when limits are reached.

## What This Skill Does

Provides billing safeguard patterns including:

- **Hard Session Caps**: Dollar limit per agent session with automatic termination on breach
- **Per-Task Limits**: Smaller caps per subtask to contain individual runaway subtasks
- **Provider Quotas**: Native billing controls in Anthropic Console, AWS Bedrock, and Google Vertex AI
- **Cost Attribution**: Structured audit trails mapping spend to agent ID, task, and workflow
- **Graceful Termination**: `BudgetExceededError` propagation that terminates cleanly without data loss
- **Alert Thresholds**: Warn at configurable % of budget before hitting the hard stop

## Instructions

### Step 1: Classify Your Budget Risk

| Agent Type | Risk Level | Recommended Pattern |
|-----------|-----------|---------------------|
| Single-turn assistant (human confirms each action) | Low | Provider-level monthly quota only |
| Batch processing (bounded input set) | Medium | Per-session cap + provider quota |
| Autonomous pipeline (runs to completion unattended) | High | Per-task cap + per-session cap + provider quota + alerts |
| Multi-agent parallel system | Critical | All of the above; per-agent caps + aggregate cap |

### Step 2: Set Provider-Level Quotas

Configure hard limits at the provider level as the last line of defense. These stop billing even if application-level safeguards fail.

**Anthropic Console**:

1. Go to [console.anthropic.com](https://console.anthropic.com) → Settings → Billing
2. Set a **Monthly Spend Limit** for your workspace
3. Set per-API-key limits if you use separate keys for different environments
4. Enable **Low Credit Notifications** at 80% of your monthly limit

**AWS Bedrock**:

```bash
# Set model invocation limits via Service Quotas
aws service-quotas request-service-quota-increase \
  --service-code bedrock \
  --quota-code L-XXXXXXXX \
  --desired-value 1000

# Set CloudWatch billing alert
aws cloudwatch put-metric-alarm \
  --alarm-name "BedrockDailySpend" \
  --metric-name "EstimatedCharges" \
  --namespace "AWS/Billing" \
  --statistic Maximum \
  --period 86400 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:AlertTopic
```

**Google Vertex AI**:

```bash
# Set quota limit for Claude requests per minute
gcloud alpha services quota update aiplatform.googleapis.com \
  --consumer=project/YOUR_PROJECT \
  --service=aiplatform.googleapis.com \
  --metric=aiplatform.googleapis.com/custom_model_serving_dedicated_replicas_per_project_per_region \
  --unit=1/min/{project}/{region} \
  --value=100

# Set billing budget alert in GCP Console:
# Billing → Budgets & alerts → Create Budget
# Set threshold alerts at 50%, 90%, 100% of monthly budget
```

### Step 3: Implement Application-Level Budget Guards

Application-level guards catch runaway behavior before it reaches provider limits. They are faster (no round-trip to the API) and more granular (per-agent, per-task).

```typescript
// src/ai/budget-guard.ts

export class BudgetExceededError extends Error {
  constructor(
    public readonly spent: number,
    public readonly limit: number,
    public readonly agentId: string,
  ) {
    super(
      `Budget exceeded for agent "${agentId}": ` +
        `$${spent.toFixed(4)} spent, $${limit.toFixed(2)} limit`,
    );
    this.name = "BudgetExceededError";
  }
}

export interface BudgetGuardOptions {
  maxBudgetUsd: number;
  warnAtPercent?: number;  // Default: 80
  agentId: string;
  /** Per-million-token costs. Defaults to Sonnet 4.6 pricing. */
  inputCostPerM?: number;
  outputCostPerM?: number;
}

export class BudgetGuard {
  private spentUsd: number = 0;
  private warned: boolean = false;

  private readonly maxBudgetUsd: number;
  private readonly warnAtPercent: number;
  private readonly agentId: string;
  private readonly inputCostPerM: number;
  private readonly outputCostPerM: number;

  constructor(options: BudgetGuardOptions) {
    this.maxBudgetUsd = options.maxBudgetUsd;
    this.warnAtPercent = options.warnAtPercent ?? 80;
    this.agentId = options.agentId;
    this.inputCostPerM = options.inputCostPerM ?? 3.0;
    this.outputCostPerM = options.outputCostPerM ?? 15.0;
  }

  /** Call BEFORE each LLM invocation. Throws if budget is exhausted. */
  checkBudget(): void {
    const utilization = (this.spentUsd / this.maxBudgetUsd) * 100;

    if (utilization >= 100) {
      throw new BudgetExceededError(this.spentUsd, this.maxBudgetUsd, this.agentId);
    }

    if (!this.warned && utilization >= this.warnAtPercent) {
      this.warned = true;
      console.warn(
        `[budget] Agent "${this.agentId}" has used ${utilization.toFixed(1)}% ` +
          `of budget ($${this.spentUsd.toFixed(4)} / $${this.maxBudgetUsd.toFixed(2)})`,
      );
    }
  }

  /** Call AFTER each successful LLM invocation to record usage. */
  recordUsage(inputTokens: number, outputTokens: number): void {
    const cost =
      (inputTokens / 1_000_000) * this.inputCostPerM +
      (outputTokens / 1_000_000) * this.outputCostPerM;
    this.spentUsd += cost;
  }

  get totalSpentUsd(): number {
    return this.spentUsd;
  }

  get remainingBudgetUsd(): number {
    return Math.max(0, this.maxBudgetUsd - this.spentUsd);
  }

  get utilizationPercent(): number {
    return (this.spentUsd / this.maxBudgetUsd) * 100;
  }

  summary(): string {
    return (
      `Agent "${this.agentId}": ` +
      `$${this.spentUsd.toFixed(4)} spent / $${this.maxBudgetUsd.toFixed(2)} limit ` +
      `(${this.utilizationPercent.toFixed(1)}% used, $${this.remainingBudgetUsd.toFixed(4)} remaining)`
    );
  }
}
```

### Step 4: Integrate Budget Guards into the Agent Executor

The budget guard must sit inside the agent executor -- wrapping every LLM call -- not at a higher orchestration level. This ensures that even if orchestration logic has a bug, individual agents cannot overspend.

```typescript
// Integration in agent-executor.ts (see claude-agent-sdk skill for full executor)

export class AgentExecutor {
  private readonly budget: BudgetGuard;

  constructor(config: AgentConfig, client: Anthropic, logger: AuditLogger) {
    this.budget = new BudgetGuard({
      maxBudgetUsd: config.maxBudgetUsd,
      agentId: config.agentId,
      warnAtPercent: 75,
    });
    // ...
  }

  async invoke(messages: AgentMessage[]): Promise<Anthropic.Message> {
    // Step 1: Check budget BEFORE the API call
    this.budget.checkBudget();

    const response = await this.client.messages.create({ /* ... */ });

    // Step 2: Record usage AFTER successful response
    this.budget.recordUsage(response.usage.input_tokens, response.usage.output_tokens);

    return response;
  }
}
```

### Step 5: Handle BudgetExceededError Gracefully

`BudgetExceededError` should propagate up to the workflow/orchestration level, trigger a clean shutdown, and produce a partial report. Never silently swallow this error.

```typescript
// In your workflow or main orchestration function

async function runAgentWorkflow(config: WorkflowConfig): Promise<WorkflowResult> {
  const agents = createAgents(config);
  const results: PartialResult[] = [];

  try {
    for (const agent of agents) {
      const result = await agent.run();
      results.push(result);
    }
    return { status: "complete", results };

  } catch (error) {
    if (error instanceof BudgetExceededError) {
      // Log clearly -- this is expected behavior, not a bug
      console.error(`[budget] Workflow terminated: ${error.message}`);
      console.error(`[budget] Partial results: ${results.length} of ${agents.length} agents completed`);

      // Return partial results -- don't discard completed work
      return {
        status: "budget_exceeded",
        results,
        reason: error.message,
        spent: error.spent,
        limit: error.limit,
      };
    }

    // Re-throw unexpected errors
    throw error;
  }
}
```

### Step 6: Implement Cost Attribution

In multi-agent or multi-project systems, attribute cost to the specific agent, task, and workflow for chargeback or optimization.

```typescript
// src/ai/cost-ledger.ts

export interface CostEntry {
  timestamp: string;
  workflowId: string;
  agentId: string;
  taskId?: string;
  model: string;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
}

export class CostLedger {
  private readonly entries: CostEntry[] = [];

  record(entry: Omit<CostEntry, "timestamp">): void {
    this.entries.push({
      ...entry,
      timestamp: new Date().toISOString(),
    });
  }

  totalByAgent(): Record<string, number> {
    return this.entries.reduce<Record<string, number>>((acc, entry) => {
      acc[entry.agentId] = (acc[entry.agentId] ?? 0) + entry.costUsd;
      return acc;
    }, {});
  }

  totalByWorkflow(): Record<string, number> {
    return this.entries.reduce<Record<string, number>>((acc, entry) => {
      acc[entry.workflowId] = (acc[entry.workflowId] ?? 0) + entry.costUsd;
      return acc;
    }, {});
  }

  grandTotal(): number {
    return this.entries.reduce((sum, e) => sum + e.costUsd, 0);
  }

  /** Export as JSONL for ingestion into cost analytics systems. */
  exportJsonl(): string {
    return this.entries.map((e) => JSON.stringify(e)).join("\n");
  }
}
```

## Best Practices

- **Default conservative**: Start with a budget 2x your expected cost per run. Agents find unexpected paths.
- **Budget per agent, not per workflow**: Per-workflow budgets allow one runaway agent to starve others. Per-agent budgets contain the blast radius.
- **Never silently swallow BudgetExceededError**: It must propagate to the orchestration layer so partial results are preserved and the caller knows why the workflow terminated.
- **Set provider quotas AND application guards**: Provider quotas are the safety net; application guards are the primary control. Both are necessary.
- **Alert before the hard stop**: Warn at 75-80% of budget so operators can intervene before the hard stop terminates work in progress.
- **Log every invocation with cost**: Structured cost logs (`cost-attribution.jsonl`) are the audit trail for billing disputes and optimization decisions.
- **Different budgets for different tiers**: Use tighter budgets for Opus (expensive) and looser for Haiku (cheap). Calibrate to the actual per-model pricing.
- **Test the hard stop**: Explicitly unit-test that `BudgetExceededError` is thrown at the correct threshold and that the caller handles it correctly.

## Common Patterns

### Pattern 1: Budget Configuration via Environment

```bash
# .env
# Per-agent session budgets (in USD)
AGENT_BUDGET_HAIKU=0.50
AGENT_BUDGET_SONNET=2.00
AGENT_BUDGET_OPUS=10.00

# Global session cap across all agents
SESSION_MAX_BUDGET_USD=20.00

# Alert threshold (% of budget before warning)
BUDGET_WARN_PERCENT=75
```

```typescript
function getBudgetForTier(tier: ModelTier): number {
  const key = `AGENT_BUDGET_${tier.toUpperCase()}`;
  const raw = process.env[key];
  if (!raw) throw new Error(`${key} environment variable not set`);
  const value = parseFloat(raw);
  if (isNaN(value) || value <= 0) throw new Error(`${key} must be a positive number`);
  return value;
}
```

### Pattern 2: Aggregate Budget Guard (Multiple Agents)

```typescript
export class AggregateBudgetGuard {
  private readonly individual: Map<string, BudgetGuard> = new Map();
  private readonly session: BudgetGuard;

  constructor(sessionMaxBudgetUsd: number) {
    this.session = new BudgetGuard({
      maxBudgetUsd: sessionMaxBudgetUsd,
      agentId: "session",
      warnAtPercent: 75,
    });
  }

  getOrCreateGuard(agentId: string, maxBudgetUsd: number): BudgetGuard {
    if (!this.individual.has(agentId)) {
      this.individual.set(agentId, new BudgetGuard({ maxBudgetUsd, agentId }));
    }
    return this.individual.get(agentId)!;
  }

  checkAndRecord(agentId: string, inputTokens: number, outputTokens: number): void {
    // Check both individual and session budgets before recording
    this.session.checkBudget();
    this.individual.get(agentId)?.checkBudget();

    // Record to both
    this.session.recordUsage(inputTokens, outputTokens);
    this.individual.get(agentId)?.recordUsage(inputTokens, outputTokens);
  }

  sessionSummary(): string {
    return this.session.summary();
  }
}
```

### Pattern 3: Python Budget Guard

```python
from dataclasses import dataclass, field


class BudgetExceededError(Exception):
    def __init__(self, spent: float, limit: float, agent_id: str):
        super().__init__(f'Budget exceeded for "{agent_id}": ${spent:.4f} spent, ${limit:.2f} limit')
        self.spent = spent
        self.limit = limit
        self.agent_id = agent_id


@dataclass
class BudgetGuard:
    max_budget_usd: float
    agent_id: str
    warn_at_percent: float = 80.0
    input_cost_per_m: float = 3.0   # Sonnet 4.6 pricing
    output_cost_per_m: float = 15.0

    _spent_usd: float = field(default=0.0, init=False)
    _warned: bool = field(default=False, init=False)

    def check_budget(self) -> None:
        utilization = (self._spent_usd / self.max_budget_usd) * 100
        if utilization >= 100:
            raise BudgetExceededError(self._spent_usd, self.max_budget_usd, self.agent_id)
        if not self._warned and utilization >= self.warn_at_percent:
            self._warned = True
            print(f"[budget] Agent '{self.agent_id}' at {utilization:.1f}% of budget")

    def record_usage(self, input_tokens: int, output_tokens: int) -> None:
        cost = (input_tokens / 1_000_000) * self.input_cost_per_m + \
               (output_tokens / 1_000_000) * self.output_cost_per_m
        self._spent_usd += cost

    @property
    def total_spent_usd(self) -> float:
        return self._spent_usd
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll add the budget cap once the agent works" | An autonomous loop with a tool-call bug can burn the month's budget in a single overnight run before anyone notices; the cap has to exist before the first unattended run, not after. |
| "Checking the budget after the call is good enough" | Recording usage after the response cannot stop the call that blew the limit; `checkBudget()` must run BEFORE the API call so the over-limit request is never sent. |
| "A console-level quota is sufficient protection" | A provider quota fails the whole key for every workflow at once and gives no per-agent attribution; a per-agent `BudgetGuard` stops one runaway agent while others keep working. |
| "Re-raising BudgetExceededError is the clean way to stop" | An unhandled exception discards the partial results the agent already produced and paid for; catch it at the workflow level and return what was completed. |

## Verification

- [ ] Provider-level quota set in Anthropic Console / AWS Bedrock / GCP Billing
- [ ] Per-agent `BudgetGuard` initialized with a concrete dollar limit
- [ ] `checkBudget()` called BEFORE every LLM API call
- [ ] `recordUsage()` called AFTER every successful response
- [ ] `BudgetExceededError` is caught at the workflow level and returns partial results (not re-raised as an unhandled exception)
- [ ] Warning threshold set at 75-80% to alert before the hard stop
- [ ] Cost attribution logs written to a durable location (JSONL file or database)
- [ ] Budget hard stop is covered by a unit test
- [ ] Budget limits are configurable via environment variables (not hardcoded)
- [ ] Different budget tiers for different model tiers (Haiku / Sonnet / Opus)

## Related Skills

- [[claude-agent-sdk]] -- agent executor pattern where budget guards are integrated
- [[multi-provider-ai]] -- provider-specific quota configuration (Bedrock, Vertex, OpenRouter)
- [[temporal-orchestration]] -- handling BudgetExceededError in durable workflow activities
- [[observability-setup]] -- usage and cost monitoring dashboards alongside enforcement
- [[ai-agent-governance]] -- enterprise governance framework for AI agent deployments
- [[model-routing]] -- task-time model / effort recommendation that respects the hard spend caps this skill enforces

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Reference Implementation**: Shannon (KeygraphHQ) -- spending caps integrated at the Claude SDK invocation layer to prevent runaway costs during autonomous security testing (~$50/run)
