---
name: temporal-orchestration
description: Design and implement durable, fault-tolerant AI agent pipelines using Temporal workflow orchestration. Covers when to use Temporal vs simple async code, TypeScript SDK setup, AI agent activity design, parallel agent fan-out, crash recovery, and Docker Compose deployment. Use when building multi-agent AI systems that must survive failures, run in parallel, and resume after crashes.
summary_l0: "Build durable AI agent pipelines with Temporal workflow orchestration and crash recovery"
overview_l1: "This skill designs and implements durable, fault-tolerant AI agent pipelines using Temporal workflow orchestration. Use it when building multi-agent AI systems that must survive failures, run in parallel, and resume after crashes, or when simple async code cannot provide the durability guarantees needed. Key capabilities include Temporal vs async code decision framework, TypeScript SDK setup and configuration, AI agent activity design with retry policies, parallel agent fan-out and aggregation, crash recovery and workflow replay, Docker Compose deployment, signal and query handling, and workflow versioning. The expected output is Temporal workflow definitions with activity implementations, retry policies, deployment configuration, and operational runbooks. Trigger phrases: Temporal, durable workflow, fault-tolerant agents, agent pipeline, crash recovery, workflow orchestration, parallel agents, Temporal SDK."
---

# Temporal Workflow Orchestration for AI Agents

Temporal is a durable workflow orchestration engine that solves the hardest problems in autonomous AI agent pipelines: crash recovery, parallel execution, retry semantics, and long-running workflow state. This skill covers when and how to use Temporal specifically for AI agent workloads, using Shannon's 5-phase 13-agent pipeline as the reference architecture.

## When to Use This Skill

Use this skill when your AI agent pipeline has one or more of these properties:

- **Multi-step**: The pipeline has distinct phases (e.g., pre-recon → analysis → exploitation → report) that must execute in order with state passed between them
- **Parallel**: Multiple agents run concurrently (e.g., 5 vulnerability hunters in parallel), and the pipeline must wait for all to complete
- **Long-running**: Individual agent invocations take minutes to hours; a crash mid-pipeline should not require restarting from scratch
- **Fault-tolerant**: Network failures, API timeouts, or container restarts should not corrupt workflow state
- **Resumable**: Named workflows should be queryable and resumable by ID

**When NOT to use Temporal**: Single-agent tasks, short-lived scripts (< 30 seconds), or pipelines where a simple `Promise.all()` is sufficient. Temporal has real operational overhead -- it requires a Temporal server and worker processes. The payoff is justified by the complexity of the problem.

**Trigger phrases**: "durable agent pipeline", "parallel agent fan-out", "workflow crash recovery", "agent workflow state", "Temporal for AI", "resumable agent pipeline", "multi-phase agent orchestration"

## What This Skill Does

Provides Temporal orchestration patterns for AI agents including:

- **Trigger Criteria**: Clear decision guide for when to reach for Temporal
- **Architecture Overview**: Temporal concepts mapped to AI agent use cases
- **TypeScript SDK Setup**: Worker, client, and workflow initialization
- **AI Agent Activity Design**: Idempotent, retryable activity patterns for LLM calls
- **Parallel Fan-Out**: Running multiple agents concurrently and awaiting all results
- **Named Workflows**: Queryable, resumable workflows with stable IDs
- **Docker Compose Deployment**: Temporal server + worker topology

## Instructions

### Step 1: Understand the Core Concepts

Temporal maps directly onto AI agent pipeline concerns:

| Temporal Concept | AI Agent Meaning | Shannon Example |
|-----------------|-----------------|-----------------|
| **Workflow** | The entire pipeline from start to final report | 5-phase security testing pipeline |
| **Activity** | One unit of work (one agent run, one tool call) | `runReconAgent()`, `runVulnHunter()` |
| **Worker** | Process that executes activities and workflows | Shannon's worker Docker container |
| **Task Queue** | Named channel routing work to workers | `"security-pipeline"` task queue |
| **Workflow ID** | Stable identifier for a specific pipeline run | Named workspaces in Shannon |
| **Signal** | Message sent to a running workflow | Stop/pause commands |
| **Query** | Read workflow state without modifying it | `./shannon query ID=<id>` |
| **Heartbeat** | Activity liveness signal (prevents timeout) | Shannon's 2-second heartbeat loop |

**Key guarantee**: Temporal persists workflow state to a database after every step. If your worker crashes, Temporal replays the workflow from the last completed activity -- with deterministic replay, the workflow picks up exactly where it left off.

### Step 2: Install the Temporal TypeScript SDK

```bash
npm install @temporalio/workflow @temporalio/activity @temporalio/worker @temporalio/client
```

**Project structure for Temporal + AI agents**:

```
src/
  temporal/
    workflows/          # Workflow definitions (deterministic code only)
      pipeline.ts       # Main pipeline workflow
      activities.ts     # Activity function signatures (no implementation)
    activities/         # Activity implementations (non-deterministic code here)
      recon-activity.ts
      analysis-activity.ts
      report-activity.ts
    worker.ts           # Worker startup (registers workflows + activities)
    client.ts           # Client to start/query/signal workflows
  ai/
    agent-executor.ts   # Claude Agent SDK executor (used inside activities)
```

### Step 3: Define Activities for Agent Runs

Activities are the units of work Temporal executes. Each AI agent run should be one activity. Activities:
- Can use any non-deterministic code (API calls, file I/O, timers)
- Are retried automatically on failure based on retry policy
- Must be idempotent when possible (safe to run twice if replayed)
- Must heartbeat if they run longer than a few minutes

```typescript
// src/temporal/activities/analysis-activity.ts

import { Context } from "@temporalio/activity";

export interface VulnAnalysisInput {
  targetUrl: string;
  repoPath: string;
  reconFindings: string;
  vulnType: "injection" | "xss" | "auth" | "authz" | "ssrf";
}

export interface VulnAnalysisResult {
  vulnType: string;
  found: boolean;
  findings: string[];
  evidence: string;
  agentId: string;
}

/**
 * Run a single vulnerability analysis agent.
 * This activity is idempotent -- running it twice produces the same result
 * because the agent analyzes the same inputs each time.
 */
export async function runVulnAnalysisActivity(
  input: VulnAnalysisInput,
): Promise<VulnAnalysisResult> {
  const agentId = `vuln-${input.vulnType}-agent`;

  // 1. Start heartbeat loop -- prevents Temporal from timing out long-running activities
  const heartbeatInterval = setInterval(() => {
    Context.current().heartbeat({ agentId, status: "analyzing" });
  }, 2_000);

  try {
    // 2. Run the AI agent (using the claude-agent-sdk executor pattern)
    const executor = createAgentExecutor(agentId, input.vulnType);
    const result = await executor.analyzeVulnerabilities(input);

    return {
      vulnType: input.vulnType,
      found: result.vulnerabilitiesFound,
      findings: result.findings,
      evidence: result.evidence,
      agentId,
    };
  } finally {
    // 3. Always clear the heartbeat interval
    clearInterval(heartbeatInterval);
  }
}
```

### Step 4: Design the Workflow (Deterministic Code Only)

Workflows are the orchestration layer. They coordinate activities but must be **deterministic** -- no random numbers, no current timestamps, no direct API calls. All non-deterministic code goes in activities.

```typescript
// src/temporal/workflows/pipeline.ts

import { proxyActivities, sleep } from "@temporalio/workflow";
import type * as Activities from "./activities.js";

// Proxy wraps activity calls with Temporal's retry and timeout management
const {
  runPreReconActivity,
  runReconActivity,
  runVulnAnalysisActivity,
  runExploitationActivity,
  runReportActivity,
} = proxyActivities<typeof Activities>({
  // Retry policy for AI agent activities
  retry: {
    maximumAttempts: 3,
    initialInterval: "5s",
    maximumInterval: "30s",
    backoffCoefficient: 2,
    // BudgetExceededError is non-retryable -- propagate immediately
    nonRetryableErrorTypes: ["BudgetExceededError", "InvalidConfigError"],
  },
  // Heartbeat timeout -- activity must heartbeat within this window
  heartbeatTimeout: "10s",
  // Schedule-to-close timeout -- max total time for the activity including retries
  scheduleToCloseTimeout: "2h",
});

export interface PipelineInput {
  targetUrl: string;
  repoPath: string;
  workspaceId: string;
}

export interface PipelineOutput {
  report: string;
  vulnerabilitiesFound: number;
  exploitsConfirmed: number;
  status: "complete" | "partial" | "failed";
}

/**
 * Main pipeline workflow -- deterministic orchestration only.
 * All AI agent execution happens inside activities.
 */
export async function securityPipelineWorkflow(
  input: PipelineInput,
): Promise<PipelineOutput> {
  // Phase 1: Pre-reconnaissance (static code analysis)
  const preReconResult = await runPreReconActivity({
    repoPath: input.repoPath,
  });

  // Phase 2: Reconnaissance (live application mapping)
  const reconResult = await runReconActivity({
    targetUrl: input.targetUrl,
    preReconFindings: preReconResult.findings,
  });

  // Phase 3: Parallel vulnerability analysis (5 agents simultaneously)
  const vulnTypes = ["injection", "xss", "auth", "authz", "ssrf"] as const;
  const vulnResults = await Promise.all(
    vulnTypes.map((vulnType) =>
      runVulnAnalysisActivity({
        targetUrl: input.targetUrl,
        repoPath: input.repoPath,
        reconFindings: reconResult.findings,
        vulnType,
      }),
    ),
  );

  // Phase 4: Conditional exploitation (only for confirmed vulnerabilities)
  const confirmedVulns = vulnResults.filter((r) => r.found);
  const exploitResults = await Promise.all(
    confirmedVulns.map((vuln) =>
      runExploitationActivity({
        targetUrl: input.targetUrl,
        vulnType: vuln.vulnType,
        findings: vuln.findings,
      }),
    ),
  );

  // Phase 5: Report generation
  const report = await runReportActivity({
    targetUrl: input.targetUrl,
    vulnResults,
    exploitResults,
    workspaceId: input.workspaceId,
  });

  return {
    report: report.content,
    vulnerabilitiesFound: confirmedVulns.length,
    exploitsConfirmed: exploitResults.filter((r) => r.exploited).length,
    status: "complete",
  };
}
```

### Step 5: Start Workers

Workers connect to the Temporal server, register workflows and activities, and execute them. Run one or more workers as separate processes.

```typescript
// src/temporal/worker.ts

import { Worker } from "@temporalio/worker";
import * as activities from "./activities/index.js";

async function startWorker(): Promise<void> {
  const worker = await Worker.create({
    workflowsPath: new URL("./workflows/index.js", import.meta.url).pathname,
    activities,
    taskQueue: "ai-pipeline",
    // Optional: limit concurrent activities to control API rate
    maxConcurrentActivityTaskExecutions: 10,
  });

  console.log("[worker] Starting Temporal worker on task queue: ai-pipeline");
  await worker.run();
}

startWorker().catch((err) => {
  console.error("[worker] Fatal error:", err);
  process.exit(1);
});
```

### Step 6: Start and Query Workflows

```typescript
// src/temporal/client.ts

import { Client, Connection } from "@temporalio/client";
import { securityPipelineWorkflow } from "./workflows/pipeline.js";
import type { PipelineInput, PipelineOutput } from "./workflows/pipeline.js";

async function startPipeline(input: PipelineInput): Promise<string> {
  const connection = await Connection.connect({ address: "localhost:7233" });
  const client = new Client({ connection });

  const handle = await client.workflow.start(securityPipelineWorkflow, {
    taskQueue: "ai-pipeline",
    workflowId: `pipeline-${input.workspaceId}`,  // Stable, resumable ID
    args: [input],
  });

  console.log(`[client] Workflow started: ${handle.workflowId}`);
  return handle.workflowId;
}

async function queryPipeline(workflowId: string): Promise<PipelineOutput | null> {
  const connection = await Connection.connect({ address: "localhost:7233" });
  const client = new Client({ connection });

  try {
    const handle = client.workflow.getHandle(workflowId);
    return await handle.result();
  } catch (err) {
    console.error(`[client] Could not query workflow ${workflowId}:`, err);
    return null;
  }
}
```

### Step 7: Deploy with Docker Compose

Temporal requires a server (PostgreSQL-backed for production). The worker runs alongside it.

```yaml
# docker-compose.yml

version: "3.8"

services:
  # Temporal server (development: in-memory; production: PostgreSQL backend)
  temporal:
    image: temporalio/auto-setup:1.24
    ports:
      - "7233:7233"   # gRPC (SDK connects here)
      - "8233:8233"   # Web UI (workflow visibility)
    environment:
      - DB=sqlite
    healthcheck:
      test: ["CMD", "temporal", "workflow", "list", "--namespace", "default"]
      interval: 5s
      timeout: 5s
      retries: 20
      start_period: 30s

  # AI agent worker
  worker:
    build: .
    command: ["node", "dist/temporal/worker.js"]
    depends_on:
      temporal:
        condition: service_healthy
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AI_PROVIDER=${AI_PROVIDER:-anthropic}
      - MODEL_TIER=${MODEL_TIER:-sonnet}
      - MAX_BUDGET_USD=${MAX_BUDGET_USD:-20}
    volumes:
      - ./audit-logs:/app/audit-logs
      - ./output:/app/output
    # Required for Playwright/Chromium if using browser automation
    shm_size: "2gb"
```

**Temporal Web UI** (available at `http://localhost:8233` after startup): shows all workflow runs, their status, activity history, and event log. This is your primary debugging interface for multi-agent pipelines.

## Best Practices

- **Keep workflows deterministic**: Never call APIs, generate random numbers, or use `Date.now()` directly in workflow code. Wrap all non-deterministic operations in activities.
- **Heartbeat long-running activities**: Any activity that runs longer than 1-2 minutes must heartbeat on a regular interval (every 2-5 seconds). Without heartbeats, Temporal will time out the activity and retry.
- **Mark non-retryable errors explicitly**: `BudgetExceededError`, configuration errors, and permanent failures should be in `nonRetryableErrorTypes`. Otherwise Temporal will retry them up to `maximumAttempts` times.
- **Use stable workflow IDs**: Use a human-readable, deterministic ID like `pipeline-${workspaceId}` rather than a random UUID. This makes workflows queryable and resumable by name.
- **Limit concurrent activities**: Set `maxConcurrentActivityTaskExecutions` on the worker to prevent one pipeline from exhausting all API rate limits.
- **Separate worker and client processes**: The client (which starts workflows) and the worker (which executes them) should be separate Node.js processes. This allows scaling workers independently.
- **Use PostgreSQL in production**: The default `sqlite` backend is for development only. Use the PostgreSQL or MySQL backend for production deployments.
- **Test workflows with Temporal's test environment**: The `@temporalio/testing` package provides a test environment that runs workflows synchronously without a live Temporal server.
- **Default agent `effortLevel` to `high`, never `max`**: Long-running Temporal workflows multiply effort-level cost across iterations and parallel activities. `max` on an iterative pipeline compounds cost without matching quality gains. See the **Effort-Level Strategy** section of [catalog/skills/ai-development/prompt-engineering/SKILL.md](../../ai-development/prompt-engineering/SKILL.md) for the decision table.

## Common Patterns

### Pattern 1: Conditional Parallel Fan-Out

Only run expensive activities (exploitation) when the prerequisite activity (vulnerability analysis) succeeded.

```typescript
// In workflow code:
const vulnResults = await Promise.all(
  vulnTypes.map((type) => runVulnAnalysisActivity({ type, ...input })),
);

const confirmedVulns = vulnResults.filter((r) => r.found);

// Only launch exploitation for confirmed vulnerabilities
const exploitResults = await Promise.all(
  confirmedVulns.map((vuln) => runExploitationActivity(vuln)),
);
```

### Pattern 2: Workflow Signal for External Control

```typescript
// In workflow definition:
import { defineSignal, setHandler } from "@temporalio/workflow";

export const cancelSignal = defineSignal("cancel");

export async function myWorkflow(input: Input): Promise<Output> {
  let cancelled = false;
  setHandler(cancelSignal, () => { cancelled = true; });

  for (const step of steps) {
    if (cancelled) {
      return { status: "cancelled", completedSteps: results };
    }
    const result = await runActivity(step);
    results.push(result);
  }
}

// From client:
// await handle.signal(cancelSignal);
```

### Pattern 3: Activity Retry Tuning for LLM Calls

```typescript
const { runAgentActivity } = proxyActivities<typeof activities>({
  retry: {
    maximumAttempts: 3,
    initialInterval: "5s",       // Wait 5s before first retry
    backoffCoefficient: 2,       // Double the wait each retry: 5s → 10s → 20s
    maximumInterval: "30s",      // Cap at 30s
    nonRetryableErrorTypes: [
      "BudgetExceededError",     // Hard stop -- don't retry
      "AuthenticationError",     // Invalid API key -- don't retry
      "ValidationError",         // Bad input -- don't retry
    ],
  },
  heartbeatTimeout: "10s",       // Must heartbeat every 10s
  scheduleToCloseTimeout: "1h",  // Max 1 hour per activity including retries
});
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "A `Promise.all()` over my agents is simpler than standing up Temporal." | For a short-lived, single-shot fan-out it is -- and the When NOT section says to use it. But the moment a worker crashes mid-pipeline, `Promise.all()` loses all state and restarts from scratch, while Temporal replays from the last completed activity. The overhead buys crash recovery you cannot bolt on later. |
| "I will put the LLM API call directly in the workflow function to keep it readable." | Workflow code must be deterministic so Temporal can replay it; an API call, timer, or random value inside the workflow corrupts replay and silently produces wrong results. Non-deterministic work belongs in activities, always. |
| "Retries are automatic, so I do not need to classify error types." | Blind retries loop forever on a non-retryable error (bad input, budget exceeded) and burn API spend. Listing `nonRetryableErrorTypes` is what stops a deterministic failure from retrying until the budget guard or the bill stops it. |

## Verification

- [ ] All non-deterministic code (API calls, timers, random) is inside activities, not workflows
- [ ] Long-running activities (> 1 min) have a heartbeat loop
- [ ] Non-retryable error types are explicitly listed in the retry policy
- [ ] Workflow IDs are stable and human-readable (not random UUIDs)
- [ ] `maxConcurrentActivityTaskExecutions` is set to prevent rate limit exhaustion
- [ ] Temporal Web UI (port 8233) is accessible for debugging
- [ ] Production deployment uses PostgreSQL backend (not SQLite)
- [ ] `BudgetExceededError` is in `nonRetryableErrorTypes` for all activities that use the budget guard
- [ ] Worker and client are separate processes
- [ ] Workflow tested with `@temporalio/testing` in CI

## Related Skills

- [[claude-agent-sdk]] -- The agent executor pattern that runs inside Temporal activities
- [[ai-billing-safeguards]] -- Budget guard integration with Temporal's non-retryable error classification
- [[multi-provider-ai]] -- Multi-provider client configuration for agents inside Temporal activities
- `ai-docker-orchestration` -- Docker Compose topology for Temporal server + worker containers
- [[workflow-orchestrator]] -- Simpler Markdown-phase orchestration for workflows that don't need Temporal's guarantees

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Reference Implementation**: Shannon (KeygraphHQ) -- 5-phase, 13-agent autonomous security testing pipeline achieving 96.15% XBEN benchmark success using Temporal for durable, parallel workflow orchestration
