---
name: agent-orchestration-primitives
description: Decide which agent-orchestration primitive a task actually needs -- a single agent, isolated subagents, persistent agent teams, or Dynamic Workflows -- and when to escalate between them. Make sure to use this skill whenever the user asks "should I use subagents or agent teams", "subagents vs agent teams", "should I parallelize this", "how many agents should I spawn", "fan this out", "should I use a Dynamic Workflow", "turn on ultracode", "orchestrate multiple agents", or otherwise weighs single-agent vs multi-agent execution, even when they do not name a specific primitive. SKIP, do NOT use for, designing the detailed write-scope and role plan once multi-agent is already chosen (use multi-agent-coordinator), picking the best of N parallel attempts at one task (use competitive-generation), stress-testing a single implementation (use adversarial-verifier), or any plainly single-agent task.
summary_l0: "Choose between single agent, subagents, agent teams, and Dynamic Workflows for a task"
overview_l1: "This skill is a decision guide for picking the right agent-orchestration primitive and knowing when to escalate. It names the four primitives -- a single well-prompted agent, isolated fire-and-forget subagents (parallelism plus context compression, no peer communication), persistent agent teams (peers that message each other and share a blockedBy task list, but get messy past about five members), and Dynamic Workflows (a JavaScript orchestration script that fans out to up to 16 concurrent and 1,000 total subagents, keeps intermediates off the context window, supports adversarial convergence, and is crash-safe and resumable). It teaches a start-single, escalate-only-on-a-measured-problem gate, the three orchestration failure modes (vague tasks cause duplicated work, verifiers declare victory without verifying, token costs compound), and the rule against parallelizing code-writing. The five orchestration patterns live in references/five-patterns.md. Trigger phrases: subagents vs agent teams, should I parallelize, how many agents, fan out, Dynamic Workflows, ultracode, orchestrate agents."
---

# Agent Orchestration Primitives

A decision guide for the one question that matters before any multi-agent work: not "should I use multiple agents?" but "what kind of coordination does this task actually need?" It names the four primitives available to an AI coding agent, gives the envelope (the strengths and hard limits) of each, and supplies a gate that keeps you on the cheapest primitive that solves the problem in front of you.

This skill decides *which* primitive to reach for. Once you have chosen multi-agent execution, the detailed write-scope, role, and reconciliation design lives in [[multi-agent-coordinator]]; this guide hands off to it.

## When to Use This Skill

Use this skill when:

- You are about to split a task across agents and want to confirm the split is warranted at all.
- A user asks "should I use subagents or agent teams?", "should I parallelize this?", "how many agents should I spawn?", or "should I turn on a Dynamic Workflow / ultracode?".
- A single agent is struggling with a task and you are deciding whether more agents would help or just multiply the confusion.
- You are authoring a command or skill body that may *offer* a fan-out path (a large read-only audit, a large test-generation surface) and need the escalation gate and token caution to embed.

**When NOT to use this skill:**

- The task plainly fits one agent's context window and one sequential pass. Start there; this skill will only tell you the same thing at a token cost.
- You have *already* decided on multi-agent and now need the concrete coordination plan (disjoint write scopes, role catalog, wait points). Use [[multi-agent-coordinator]].
- You want N agents to attempt the *same* task so you can pick the best output. Use [[competitive-generation]].
- You want to stress-test one finished implementation. Use [[adversarial-verifier]].

**Trigger phrases**: "subagents vs agent teams", "should I parallelize", "how many agents", "fan this out", "Dynamic Workflows", "ultracode", "orchestrate multiple agents", "should I use a workflow", "multi-agent".

## The Four Primitives

Each primitive trades coordination power for cost and complexity. They form a ladder: every rung up buys a capability the rung below cannot provide, and pays for it in tokens and failure surface.

| Primitive | What it is | Strengths | Hard limits / when it breaks |
|---|---|---|---|
| **Single agent** | One well-prompted agent doing the whole task in its own context. | Cheapest, simplest, no coordination overhead, no handoff loss. | Bounded by one context window; no parallelism. |
| **Subagents** | The parent spawns isolated, fire-and-forget agents; each runs in a fresh context and returns only its conclusion. | Parallelism PLUS context compression -- vast exploration distilled to a clean signal without polluting the parent. Predictable information flow. | Subagents cannot spawn subagents and cannot talk to each other (a feature, not a bug). The parent is the sole coordinator. A "handful" at a time. |
| **Agent teams** | Persistent peer agents that message each other directly and share a `blockedBy` task list. | Long-running peers can negotiate, unblock each other, and hold state across a session. | Gets messy past about five members; dies with the session (not crash-safe); coordination chatter grows super-linearly. |
| **Dynamic Workflows** | Claude writes a JavaScript orchestration script that the runtime executes, fanning work across many subagents. The script *is* the plan. | Up to 16 concurrent / 1,000 total subagents; intermediates live in script variables (off the context window); adversarial convergence (agents attack from independent angles, others refute, iterate until answers converge); crash-safe and resumable. | Research-preview, plan-gated feature -- never assume it is present. Token-heavy. Best for read-only, embarrassingly-parallel, large-surface work. |

**Subagents = compression, not just parallelism.** The most-missed point: the value of a subagent is often *not* speed but context hygiene. A subagent that reads 10,000 files and returns a one-page summary protects the parent's context window from 10,000 files of noise. Reach for a subagent whenever you need a conclusion but not the raw exploration that produced it.

**Dynamic Workflows graceful degradation (REQUIRED).** Dynamic Workflows is a plan-gated research-preview capability (availability varies by harness, version, and `/config` toggle; an `ultracode` effort setting can let the agent auto-trigger it at high reasoning). Treat it as "if available in your harness". Never assume it is present, never hard-depend on it, and always frame a fan-out as an optional path the user confirms -- with the scope-first token caution below. When it is unavailable, fall back to subagents or a single agent.

## Instructions

### Step 1: Start with a single agent

The default is always one well-prompted agent. Multi-agent orchestration adds a 5-15x token multiplier and a coordination burden that itself produces bugs (handoff loss, duplicated work, merge conflicts). Do not escalate on a hunch that "more agents would be faster". Escalate only when Step 2 names a concrete, measured problem.

### Step 2: Name the measured problem

Write down the specific problem the single agent cannot solve. Valid problems are concrete and observable; "this feels big" is not one. The four problems that justify escalation:

| Measured problem | Symptom you can point to |
|---|---|
| **Context overflow** | The task's required reading exceeds one agent's effective window (a 10k-file repo, dozens of long docs). |
| **Embarrassing parallelism** | Many independent units of the same read-only work (audit every route, summarize every module) with no cross-dependencies. |
| **Independent verification needed** | A claim must be checked by an agent that did not produce it (refute-until-converge), because self-review is unreliable. |
| **Specialized concurrent lenses** | Distinct review lenses (security, performance, correctness) can run at the same time on the same artifact. |

If you cannot fill in the right-hand column, stay single-agent.

### Step 3: Match the problem to the cheapest primitive that solves it

| Measured problem | Cheapest primitive | Why not lower / higher |
|---|---|---|
| Context overflow, conclusion-only | **Subagents** | A single agent cannot hold the context; agent teams add peer chatter you do not need for a one-way summary. |
| Embarrassing parallelism, small surface (a handful) | **Subagents** | Fire-and-forget fan-out is exactly the shape; no peer communication required. |
| Embarrassing parallelism, large surface (tens to hundreds) | **Dynamic Workflows** (if available) | Subagents do not scale to hundreds with off-context intermediates and resumability; fall back to batched subagents if workflows are unavailable. |
| Independent verification / adversarial convergence | **Dynamic Workflows** (if available), else **subagents** | Workflows encode refute-until-converge natively; subagents can approximate it with an explicit verifier pass (see [[adversarial-verifier]]). |
| Peers must unblock each other mid-task, holding shared state | **Agent teams** | Subagents cannot communicate; this is the one shape that genuinely needs peers. Keep the team <= 5. |

**Non-blocking delegation.** When the platform offers it, prefer a subagent-start tool that returns immediately, delivers each result in a later message, and pairs with a separate wait tool for the moments the lead genuinely needs a result. The lead keeps working while the subagents run, which lowers average time to completion at similar quality, token use, and cost; a lead forced to idle on every delegation pays the subagent's latency twice. This is a property to look for in the primitive, not a reason to fan out work that Step 2 did not name.

### Step 4: Apply the escalation gate

Before committing to the chosen primitive, confirm all three:

1. **The problem from Step 2 is real and named** (not "it feels big").
2. **The chosen primitive is the lowest rung that solves it** (do not jump to Dynamic Workflows for a handful of independent reads).
3. **The token cost is justified and bounded.** Cross-link [[ai-billing-safeguards]] and apply the scope-first discipline: for any large fan-out, calibrate on a single folder first, review the execution plan on first trigger, and confirm before going full-scale. Workflows are token-heavy; some environments default them off.

If any of the three fails, drop down a rung.

### Step 5: Guard against the three failure modes

Every multi-agent design must actively defend against these. They are the reasons orchestration fails in practice:

1. **Vague task descriptions cause duplicated work.** Two agents handed fuzzy scopes re-derive the same thing or make incompatible assumptions. Mitigation: give every agent an explicit, disjoint scope and a precise output contract (the [[multi-agent-coordinator]] write-scope discipline).
2. **Verification agents declare victory without verifying.** A reviewer agent will happily report "looks good" without running anything. Mitigation: give the verifier a concrete, falsifiable instruction -- "run the full test suite; do not mark complete until each test passes; paste the passing output" -- not "check that it works".
3. **Token costs compound.** Aggregate cost grows with every agent in the fan-out. Mitigation: tier models to the cognitive demand of each role (cheap model for mechanical work, capable model for design and spec-compliance judgment) and add budget controls. Cross-link [[ai-billing-safeguards]] and [[prompt-token-optimization]].

### Step 6: Do not parallelize code-writing

The single most important warning. Use subagents to *explore and answer questions*, not to write production code alongside the main agent. Parallel agents writing code make incompatible assumptions about interfaces, naming, and shared state, and the merge cost exceeds the parallelism gain. Decompose by *context boundaries*, not by role: the agent that implements a feature should also write that feature's tests, because it already holds the context (see [[multi-agent-coordinator]] context-centric decomposition). Reserve parallel code-writing for genuinely disjoint file sets with pre-agreed contracts, and even then prefer sequential integration.

### Step 7: The five orchestration patterns

Once a primitive is chosen, the *shape* of the orchestration follows one of five named patterns (prompt chaining, routing, parallelization, orchestrator-worker, evaluator-optimizer). These are documented with selection guidance and worked examples in [references/five-patterns.md](references/five-patterns.md). Read that file when you need to pick a pattern; this body does not duplicate it.

When you reach for **Dynamic Workflows** specifically, [assets/example-fanout-workflow.js](assets/example-fanout-workflow.js) is a copy-adaptable reference template: a read-only fan-out-and-synthesize workflow (audit every file under a directory, then merge the findings) that begins with the required `export const meta = {...}` literal and carries the mandatory graceful-degradation fallback and the scope-first token caution inline. It is a TEMPLATE TO ADAPT, not a script to run verbatim -- copy `example-fanout-workflow.js` into your skill's `scripts/` or `assets/` directory and rewrite the meta, schema, and prompts for your task. This is the workflow-as-skill-bundle distribution pattern documented under "Per-skill Bundled Resources" in `AGENTS.md`.

### Step 8: Pair workflows with the platform's continuous-operation commands

A Dynamic Workflow run is one-shot by default. When a task must persist beyond a single run, two Claude Code built-in commands compose with it: `/loop` re-runs a workflow (or any prompt) on an interval or until you stop it (scheduled audits, continuous monitoring of a changing surface), and `/goal` attaches a hard, explicit completion requirement the agent must satisfy before it is allowed to stop. These are platform commands you reference and invoke directly in your harness -- NOT catalog artifacts Nexus-Hub ships; this skill names them so the choice is on the table, but does not provide them.

#### Goal-based stopping: the exit must be a checked command, not a judgement

A continuous loop is only as safe as its stopping rule. Two requirements make a loop's exit trustworthy:

1. **The exit condition is a falsifiable command, not a vibe.** The thing that ends the loop must be a `check_command` whose output and exit code can be read (`npm test`, `gh pr checks`, `make validate`), paired with an `exit_condition` derived from that output ("exits 0", "0 failing required checks"). "Looks ready" or "seems green" cannot terminate a loop, because the loop has no way to disprove it. A loop with no command-derived exit is an unbounded token burn waiting to happen, so it also needs a hard iteration cap.
2. **The exit is evaluated by a checker that did not produce the work.** This is failure mode 2 ("verification agents declare victory without verifying") applied to termination: if the maker that wrote the iteration is also the agent that decides the loop is done, it will declare victory on plausible-looking output. Give the exit decision to an independent checker with a falsifiable instruction -- run the command, read the full output, and only then certify (the [[verification-before-completion]] evidence gate) -- using [[adversarial-verifier]] for high-risk exits.

Assembling a named, goal-terminated loop from these parts (the loop-definition schema, the iteration cap, the maker/checker split, the host driver) is the job of [[loop-engineering]]; this step states the termination rule, that skill is where you compose the whole loop. Do not duplicate the loop schema here -- reference it through that skill.

#### Workflow-control vocabulary: gate, resume, continue-on-error

Beyond the exit rule, a multi-step workflow or loop needs three control patterns. All three are **agent-instruction patterns** (LLM-native) you encode in the orchestration, NOT a new runtime to build:

- **Gate** -- a human approve/reject checkpoint between stages, with an explicit `on_reject` policy (`abort` / `skip` / `retry`). In a Dynamic Workflow it is an `AskUserQuestion` between stages; in a `/loop` run it is a pause-for-approval step.
- **Resume-from-checkpoint** -- record per-step state so an interrupted run re-enters at the failed step instead of restarting. Dynamic Workflows are crash-safe and resumable natively (the runtime journals each `agent()` call); a plain loop persists the same state to a run file.
- **Continue-on-error** -- record a step's failure and continue, leaving it visible to downstream conditional logic, instead of aborting the whole run. In a workflow this is a per-item `try/catch` whose result is `null`; the canonical `.filter(Boolean)` then drops failed items while the rest proceed.

Composing these into a named, goal-terminated loop (the schema, the `iteration_cap`, the maker/checker split, the `on_reject` policy) is the job of [[loop-engineering]]; this step names the vocabulary, that skill assembles the loop. Do not build a bespoke YAML workflow engine for them -- they are instructions over the harness's existing Dynamic Workflows or a `/loop` driver.

Two step-type vocabulary notes round out the orchestration surface, distinct from the control patterns above:

- **Init / bootstrap step** -- a workflow's first step may bootstrap the project or workspace (install dependencies, seed config, create the scratch directory) so the workflow is self-contained on a fresh checkout rather than assuming a prepared environment.
- **Structured step output** -- a step may opt into machine-parseable output (JSON) that later steps consume instead of free text; the structured-output contract makes downstream steps deterministic (parse a named field, not prose).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "More agents will obviously be faster." | Faster is not free. The 5-15x token multiplier and coordination overhead routinely make a fan-out slower in wall-clock *and* worse in quality than one focused agent. Step 2 forces you to name the problem that more agents actually solve; if you cannot, parallelism is pure cost. |
| "Let me spin up an agent team -- peers talking sounds powerful." | Agent teams are the most expensive, most failure-prone rung and die with the session. They are justified only when peers must unblock each other mid-task while holding shared state. For one-way summarization or independent fan-out, subagents are strictly cheaper and more predictable. |
| "I will have several agents write the code in parallel to finish sooner." | Parallel code-writers make incompatible interface and naming assumptions; reconciling them costs more than the time saved, and the bugs are subtle. Subagents are for exploration and verification, not concurrent production code. Decompose by context, not role. |
| "Dynamic Workflows is the most capable option, so I will default to it." | It is a plan-gated research-preview feature that may not exist in the user's harness, and it is the most token-heavy primitive. Defaulting to it assumes a capability you have not confirmed and burns budget on tasks a handful of subagents would handle. Escalate to it only for large-surface, read-only work, and always with graceful degradation. |
| "My verifier agent said it looks good, so verification is done." | A verifier given a vague instruction declares victory without running anything. Unless the verifier was told to run the suite and paste passing output (failure mode 2), its "looks good" is worthless. The verification is the artifact, not the agent's reassurance. |

## Verification

- [ ] The chosen primitive corresponds to a concrete, named problem from Step 2 (not "it feels big").
- [ ] The chosen primitive is the lowest rung that solves that problem (no skipping straight to Dynamic Workflows / agent teams).
- [ ] If Dynamic Workflows was chosen, the design states explicitly that it degrades gracefully to subagents / single-agent when unavailable, and never hard-depends on it.
- [ ] If a fan-out was chosen, a scope-first plan exists (calibrate on one folder, review plan on first trigger, confirm before full scale) and a token-budget control is referenced.
- [ ] No production code is being written by parallel agents; subagents are scoped to exploration / verification only.
- [ ] Each agent has an explicit disjoint scope and a falsifiable output contract (defends failure modes 1 and 2).
- [ ] Per-role model tiering is specified for any fan-out (defends failure mode 3).
- [ ] If multi-agent was chosen, the design is handed off to [[multi-agent-coordinator]] for the detailed write-scope / role / reconciliation plan.

## Related Skills

- [[multi-agent-coordinator]] - the detailed coordination plan (write scopes, roles, wait points, reconciliation) once this guide has chosen multi-agent execution.
- [[adversarial-verifier]] - the refute-until-converge verification pass referenced in the independent-verification problem and the independent-checker for loop exits.
- [[loop-engineering]] - assembles named, goal-terminated loops on top of `/loop` and `/goal`; consumes the goal-based-stopping rule from Step 8.
- [[competitive-generation]] - the variant where N agents attempt the same task and you select the best output.
- [[ai-billing-safeguards]] - hard spending caps and budget controls for the token-cost failure mode.
- [[prompt-token-optimization]] - reducing per-task token consumption inside any chosen primitive.
- [[task-coordinator]] - general task decomposition and dependency tracking that feeds the primitive choice.
- [[model-routing]] - picks the model tier each agent runs on once this guide has chosen the orchestration primitive.
