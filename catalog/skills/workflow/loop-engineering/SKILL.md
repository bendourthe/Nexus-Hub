---
name: loop-engineering
description: 'Assemble named, goal-terminated agentic loops from Nexus-Hub primitives. Use whenever the user says "run this in a loop", "loop until tests pass", "set up an agentic loop", "iterate until green", "build a loop that ships PRs", "what loop should I use", or asks for continuous agent work with a stopping rule. SKIP: a one-shot task with no iteration; choosing between single-agent / subagents / workflows -- use agent-orchestration-primitives; the host /loop or /goal command mechanics themselves.'
summary_l0: "Assemble goal-terminated agentic loops from Nexus-Hub primitives"
overview_l1: "This skill turns Nexus-Hub's existing agentic primitives into named, goal-terminated loops. Use it to choose or author a loop definition with a falsifiable goal, iteration cap, check command, checker-evaluated exit condition, host driver, maturity flag, agents, and tags. It maps automations, worktrees, skills, plugins/connectors, sub-agents, and external memory to owned catalog surfaces, then points operators to a local loop schema and seeded loop library. The loop driver remains the host platform's /loop or /goal command; Nexus-Hub references those commands and never reimplements them."
---

# Loop Engineering

Loop engineering is the connective layer between Nexus-Hub's primitives and the host harness that runs repeated work. A loop definition names the goal, bounds the cost, chooses the check, records the exit condition, and says which owned primitive handles each part so an operator can iterate deliberately instead of asking an agent to "keep going" until the session drifts.

## When to Use This Skill

Use this skill when:

- A user asks to "run this in a loop", "loop until tests pass", "set up an agentic loop", "iterate until green", "build a loop that ships PRs", or "what loop should I use".
- A task needs repeated maker/checker cycles with a durable stopping rule, not a single implementation pass.
- You need to choose from a local loop library or write a new loop definition that another agent can run later.
- You are composing host `/loop`, `/goal`, or `/schedule` behavior with Nexus-Hub worktrees, skills, agents, connectors, and memory files.
- You need to explain where loop cost, human-review bandwidth, and termination risk enter the design.

When NOT to use this skill:

- The task is a one-shot change with no iteration. Implement it directly.
- The question is only "single agent, subagents, agent teams, or Dynamic Workflows?" Use [[agent-orchestration-primitives]].
- The user needs detailed host-command syntax for `/loop` or `/goal`. Those are platform commands, not Nexus-Hub catalog artifacts.
- The loop would run without a falsifiable `check_command`, an `iteration_cap`, and a checker-evaluated `exit_condition`.

## Instructions

### Step 1: Map the loop pieces to owned primitives

Use the owned surface for each loop piece. Do not introduce a new service, dependency, credential, or remote registry just to make a loop feel packaged.

| Loop piece | Nexus-Hub owner | How to use it |
|---|---|---|
| Automations and loop driver | Host `/loop`, `/goal`, and `/schedule`; documented as platform commands in `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md` Step 8 and the v3.1.0 note in `CHANGELOG.md` | Reference the host command that runs the loop. Nexus-Hub does not ship or reimplement these commands. |
| Worktrees | `catalog/skills/workflow/using-git-worktrees/SKILL.md` | Isolate each writable iteration, especially PR-fixing and multi-branch loops. |
| Skills | `data/SKILL_INDEX.md` and `catalog/skills/` | Treat skills as the reusable procedure library a loop invokes at each iteration. |
| Plugins and connectors | `catalog/skills/ai-development/mcp-builder/SKILL.md` and `catalog/mcp-configs/mcp-servers.json` | Use only approved local or trusted-destination MCP surfaces; follow the MCP Registry Policy before adding any connector. |
| Sub-agents | `catalog/agents/`, `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md`, and `catalog/skills/orchestration/adversarial-verifier/SKILL.md` | Split maker and checker roles when independent verification matters. Keep output contracts falsifiable. |
| External memory layer | `catalog/skills/workflow/dev-progress-tracker/SKILL.md`, `catalog/skills/workflow/known-gaps-tracker/SKILL.md`, and `catalog/skills/workflow/filesystem-context-patterns/SKILL.md` | Persist state, open gaps, and cross-session context in files instead of trusting the loop's working memory. |

### Step 2: Start from the local schema

Read [references/loop-schema.md](references/loop-schema.md) before writing or running a loop definition. Every loop must declare `name`, `goal`, `iteration_cap`, `check_command`, `exit_condition`, `driver`, `maturity`, `agents`, and `tags`.

The two non-negotiable safety fields are `iteration_cap` and `exit_condition`. Without a cap, the loop can burn tokens indefinitely. Without an observable exit, the maker agent can declare victory because the output feels plausible.

### Step 3: Choose or adapt a library loop

Read [references/loop-library.md](references/loop-library.md) and prefer a seeded definition when it fits. If a first-class Nexus-Hub command already owns the loop shape, use that command instead of duplicating the loop in prose.

When adding a new loop to the library, keep it local and service-free: no install counts, no remote fetch, no third-party processor, and no outbound call unless the operator's own destination is intrinsic to the task and already covered by the MCP Registry Policy.

### Step 4: Assemble the loop

1. Write the loop goal as a falsifiable end state.
2. Set a hard `iteration_cap` before the first run.
3. Pick one `check_command` that measures progress between iterations.
4. Define `exit_condition` as command-derived evidence, not reassurance from the maker.
5. Choose the host driver: `/goal` for a hard completion requirement, `/loop` for interval or continuous re-runs, or manual re-invocation when the host lacks those commands.
6. Decide whether writable work belongs in a git worktree via [[using-git-worktrees]].
7. Assign maker and checker roles. For high-risk loops, the checker should be independent and should use [[adversarial-verifier]] or the evidence discipline in [[verification-before-completion]].
8. Persist state and unresolved work through [[dev-progress-tracker]], [[known-gaps-tracker]], or [[filesystem-context-patterns]].

### Step 5: Budget the orchestration tax

Loops multiply every cost in the underlying workflow: model tokens, tool calls, reviewer attention, merge risk, and stale-context risk. Before running at scale, apply the same scope-first discipline used by [[agent-orchestration-primitives]] and [[ai-billing-safeguards]]: calibrate one iteration, inspect the plan and check output, cap the run, and only then widen the loop.

Human-review bandwidth is also a budget. A loop that produces more PRs, findings, or plan diffs than a human can review safely is not "automated"; it is accumulating unreviewed risk. Prefer fewer hardened loops with crisp exits over broad continuous work with vague triage.

Two human-cost risks attack long-running loops directly: **cognitive surrender** (the operator stops judging loop output because the green checks feel authoritative) and **comprehension debt** (the gap between what the loop shipped and what the operator understands widens each cycle). Both are named with mitigations in [[verification-before-completion]]; close comprehension debt deliberately with [[session-teach-back]].

## Scheduled-Triage Recipe

This is the full automation-to-ship loop: a scheduled run that triages incoming work, fixes what it can in isolation, and routes the rest to a human. It is a recipe to adapt, not a runnable script. Every step uses a primitive Nexus-Hub already owns or a host command it references; the recipe introduces no new outbound call, dependency, credential, or third-party processor.

1. **Cadence** -- host `/schedule` for a fixed clock (e.g. nightly) or host `/loop` for interval re-runs. These are platform commands referenced per Step 1 and `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md` Step 8; Nexus-Hub does not reimplement them. Set the `iteration_cap` and the cadence before the first run.
2. **Triage** -- at each wake, read the incoming surface: CI failures, open issues, or recent commits. Triage classifies each item as auto-fixable, needs-human, or ignore. Triage is a read step; it makes no change yet.
3. **Persist findings to the memory layer** -- write the triaged list to a durable file rather than the loop's working memory: `docs/todos.md` via [[dev-progress-tracker]], the version gap log via [[known-gaps-tracker]], or a scratch file per [[filesystem-context-patterns]]. The next wake reads this file, so state survives across runs.
4. **Isolate each viable finding in a worktree** -- for every auto-fixable item, create a dedicated `git worktree` via [[using-git-worktrees]] so concurrent fixes never collide on the main worktree.
5. **Maker drafts, independent checker reviews** -- inside each worktree, a maker sub-agent drafts the fix and an independent checker sub-agent reviews it. The checker must not be the maker (the Phase 2 exit rule): use [[adversarial-verifier]] for the checker role and treat the loop exit as the evidence-bearing completion claim in [[verification-before-completion]], with the independent-evaluator rule from [[agent-orchestration-primitives]] (Step 8). The fix's `check_command` (the worktree's tests or build) is the exit evidence, not the maker's confidence.
6. **Ship through host connectors** -- open the PR or update the ticket through a host connector (MCP), using only surfaces approved by the MCP Registry Policy: see [[mcp-builder]] and `catalog/mcp-configs/mcp-servers.json`. Do not add a connector just to close the loop; if no approved destination exists, stop at the worktree and report.
7. **Route the rest to a human inbox** -- every needs-human item (and any finding that failed its checker after the `iteration_cap`) goes to a human review queue: a tracked list in the memory layer, an assigned issue, or a digest. Unhandleable work is surfaced, never silently dropped.

Scope first. A scheduled triage loop multiplies token, tool-call, and reviewer cost on every wake, so calibrate on one finding, inspect the plan and check output, cap the run, and only then let it run unattended. Bound the spend with [[ai-billing-safeguards]] before scheduling, and keep the human-inbox volume inside what a person can actually review.

## Strict Control Loops

The most effective loops are not open-ended agentic cycles; they are strict control loops where deterministic code drives the iteration and the LLM is invoked only for the decisions code cannot make. This is complementary to the host `/loop` + `/goal` driver model from Step 1, not a replacement: the host command still drives the run, but the loop body should push as much as possible into deterministic code.

- **The operator owns the shell.** Write the desired end state and the observation/check mechanism, then let deterministic code handle iteration, execution, and every tool or API call. The loop is a control structure first and a prompt second.
- **The LLM handles only the dynamic decision.** Reserve the model for the one genuinely-dynamic step traditional code cannot make. A hallucinating model's blast radius is then bounded by the hard-coded checks surrounding it, rather than corrupting the whole run.
- **Wrap risky steps in deterministic checks.** Every repetitive or risky action you wrap in a code-level check (an exit code, a schema validation, a numeric threshold) is how you limit the blast radius of a bad decision. Push the cheapest-primitive discipline of [[agent-orchestration-primitives]] and the cost-bounding of [[ai-billing-safeguards]] into the loop body, not just the loop driver.

### Progressive hardening

Loops earn determinism over time. Start with the minimal loop run with a human in the verification seat, run it several times to learn which steps the agent gets right consistently, then replace the LLM prompt for each consistently-correct step with deterministic code. The LLM's role shrinks every cycle. This progression is exactly how an `experimental` loop (run with human verification) becomes `hardened` (repeatedly successful, with its consistently-correct steps moved into code); see the `maturity` field in [references/loop-schema.md](references/loop-schema.md).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will just loop without an exit condition and stop when it looks good." | That creates unbounded token burn and invites goal drift; the loop ends when a command-derived condition is met, not when the maker feels finished. |
| "The maker agent can grade its own exit." | Self-certification recreates the `agent-orchestration-primitives` failure mode where verifiers declare victory without verifying; use an independent checker or fresh command evidence. |
| "The library should fetch popular loops from a remote registry." | A remote registry would add a service dependency and a supply-chain surface. Nexus-Hub ships local loop definitions and lets operators adapt them. |
| "A loop means I do not need to understand each iteration." | That produces comprehension debt: the system changes faster than the operator's model of it. Keep state files readable and require human review at bounded checkpoints. |
| "More agents inside the loop will make it safer." | More agents multiply coordination and token cost. Escalate only when [[agent-orchestration-primitives]] names a measured problem that the cheaper primitive cannot solve. |

## Verification

- [ ] The selected loop definition declares every schema field from [references/loop-schema.md](references/loop-schema.md).
- [ ] The loop has a hard `iteration_cap` before the first run.
- [ ] The `exit_condition` is derived from `check_command` output and can be checked by someone other than the maker.
- [ ] The driver is identified as host `/loop`, host `/goal`, host `/schedule`, or manual re-invocation; no Nexus-Hub command is invented.
- [ ] Any writable iteration has an isolation plan through [[using-git-worktrees]] or an explicit reason isolation is unnecessary.
- [ ] State and unresolved gaps persist through [[dev-progress-tracker]], [[known-gaps-tracker]], or [[filesystem-context-patterns]].
- [ ] The loop introduces no new outbound call, dependency, credential, or third-party processor beyond existing approved project destinations.

## Related Skills

- [[agent-orchestration-primitives]] - chooses the cheapest agent primitive and owns the goal-based-stopping + independent-evaluator rule for `/loop` and `/goal` (Step 8).
- [[using-git-worktrees]] - isolates writable loop iterations so repeated attempts do not damage the main worktree.
- [[adversarial-verifier]] - supplies the independent checker role for loop exits and high-risk claims.
- [[verification-before-completion]] - requires fresh evidence before treating a loop exit as complete.
- [[dev-progress-tracker]] - persists forward-looking loop state in `docs/todos.md`.
- [[known-gaps-tracker]] - records deferred or failed loop outcomes into the version gap log.
- [[ai-billing-safeguards]] - bounds runaway loop cost with hard spending controls and budget gates.
- [[session-teach-back]] - the comprehension-debt countermeasure: confirms the operator understands what a loop shipped before the gap compounds.
- [[context-pack-builder]] - distills cross-session context into a durable memory artifact a loop can load at each iteration.
