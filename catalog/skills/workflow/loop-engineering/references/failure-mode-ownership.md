# Loop Failure-Mode Ownership

A rule-ownership table per the "Rule ownership for overlapping skills" section of `AGENTS.md`. Each loop failure mode has exactly ONE owning skill. Non-owners hand off to the owner and never restate the owned rule, so a multi-skill review reports each root cause once instead of reporting the same defect under three names.

The Owning skill column quotes the section heading in that skill where the rule actually lives, so a reader can check the claim rather than trust it.

| Failure mode | What happens | Owning skill (exactly one) | Design response | Handoff from non-owners |
|---|---|---|---|---|
| Runaway spend | The loop consumes budget far beyond the task's value before anything stops it. | `loop-engineering` -- the `budgets` field in `references/loop-schema.md` | Declare per-run ceilings on cost, tool calls, subagents, retries, and wall time; record an unmeasurable dimension as `unmeasured` rather than as satisfied. | `ai-billing-safeguards` owns HARD enforcement ("Step 2: Set Provider-Level Quotas", "Step 3: Implement Application-Level Budget Guards"); a declared budget is a plan, a provider quota is a wall. Route anything that must be impossible, not merely discouraged, there. |
| Stuck cycle | The loop iterates without advancing, burning its full `iteration_cap`. | `loop-engineering` -- "Stall and Fault Detection" | Distinguish no-progress, repeated-error, and permission-denial as separate trip conditions read from real signals, and pause with a cooldown rather than hard-aborting. | Any skill observing a non-advancing loop reports it here rather than adding its own stuck check. |
| Premature convergence | The loop terminates on the first green signal it can produce while other dimensions are still broken. | `verification-before-completion` -- "The Gate Function" | Completion criteria are multi-dimensional; every dimension the claim spans needs its own fresh evidence. | `loop-engineering` supplies the dual-condition `exit_condition` mechanism; whether the criteria are sufficient is decided by the owner. |
| Metric gaming | The tracked score improves while the underlying quality does not. | `ai-output-evaluation` -- "Evaluating Output vs Validating the Evaluator" | Keep a held-out grading set the loop never sees, and re-measure there before accepting any improvement. | `loop-engineering` "Reward Hacking in Self-Improving Loops" is the loop-side handoff: it names the loop shapes that invite gaming and routes grader design to the owner. |
| Self-rubber-stamping | The agent that produced the work is also the only judge of whether it is done. | `agent-orchestration-primitives` -- "Step 5: Guard against the four failure modes", mode 2 | Give the verifier a concrete falsifiable instruction and keep maker and checker distinct unless the checker is a deterministic non-LLM oracle. | `adversarial-verifier` is the EXECUTOR of an independent pass, not the owner of the discipline. `loop-engineering`'s maker-self-certifies anti-pattern points here. |
| Context rot | Accumulated context degrades the agent's judgement as the run lengthens. | `context-degradation` | Probe for degradation, then compress, re-ground, or restart from a checkpoint. | `loop-engineering`'s `state_contract` provides the compact state a restart resumes from; deciding that a restart is needed belongs to the owner. |
| Tool thrashing | The agent repeatedly calls, abandons, and re-calls overlapping tools without advancing. | `tool-design` -- "Step 3: Manage Tool Count" | Treat thrashing as a tool-surface defect: near-duplicate tools, an unclear description boundary, or an error message that does not say what to do next. | A loop that observes thrashing files it as a surface defect here instead of instructing the agent to try harder. |
| State poisoning | A wrong fact is written once and then trusted by every later run. | `agent-memory` -- "2b. Provenance, tiers, and maintenance" | Append-only provenance with `source` and `supersedes`, so a bad row can be located and the affected facts rolled back to the last good changelog index. | `loop-engineering`'s `state_contract` declares WHAT persists; the integrity and recovery of what persisted is the owner's. |
| Side-effect drift | The loop's real-world effects widen past the authority it was given. | `agent-access-policy` -- "Containing a Commandeered Agent (Blast-Radius Limit)" | Least-privilege allowlists plus typed approval gates on dangerous actions. | `agent-execution-isolation` is the sandbox EXECUTOR. `loop-engineering`'s `scope` and `permissions` fields declare the intended boundary; enforcing it is the owner's. |
| Cascading error | One unverified upstream result propagates through a fan-out, multiplying instead of being caught. | `agent-orchestration-primitives` -- "Step 5: Guard against the four failure modes", mode 4 | Verify the upstream result before fanning out on it, and version any shared state the peers read so a corrupted revision can be identified and rolled back. | `loop-engineering` bounds fan-out cost through `budgets`; the ordering rule (verify, then fan out) is the owner's. |

## Owners edited to state their rule

Five owners did not yet state the rule this table assigns them, so one sentence was added to each owner rather than restating the rule here:

- `verification-before-completion` -- "The Gate Function" gained the multi-dimensional completion-criteria sentence.
- `ai-output-evaluation` -- "Evaluating Output vs Validating the Evaluator" gained the held-out-grader sentence.
- `tool-design` -- "Step 3: Manage Tool Count" gained the tool-thrashing definition.
- `agent-memory` -- "2b. Provenance, tiers, and maintenance" gained the state-poisoning recovery sentence.
- `agent-orchestration-primitives` -- "Step 5" gained cascading error as a fourth failure mode, and its heading changed from three to four modes accordingly.

The remaining five owners already stated their rule at the heading quoted in the table.

## The design rule these modes share

Expensive fan-out, irreversible actions, and large context expansion happen ONLY after earlier gates have shown a productive trajectory. Every mode above is a case of spending late-stage authority on an early-stage trajectory: budget before the check converges, a fan-out before the premise is verified, a write before the boundary is declared. Order the loop so the cheap gate runs first and the expensive step is a reward for passing it.
