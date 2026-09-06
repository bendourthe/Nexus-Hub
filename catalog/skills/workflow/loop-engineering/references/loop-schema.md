# Loop Definition Schema

This schema is the local, service-free structure for reusable loop definitions. Each loop definition must be readable cold by an agent or operator and must make termination observable before the first iteration starts.

## Fields

| Field | Purpose | Example |
|---|---|---|
| `name` | Kebab-case identifier used in the library and references. | `ship-pr-until-green` |
| `goal` | Falsifiable end state in one sentence. | `The pull request has no failing required checks.` |
| `iteration_cap` | Hard maximum number of iterations before the loop stops and asks for human review. | `10` |
| `check_command` | Exact shell command run between iterations to measure progress. Use a project-specific command when possible. | `gh pr checks` |
| `exit_condition` | Observable, command-derived condition that ends the loop. A checker evaluates this condition; the maker does not self-certify it. A loop MAY also require the agent to emit a structured status block carrying an explicit completion signal, in which case it terminates only on the dual condition of that signal AND this command-derived corroboration -- the signal alone never terminates the loop. | `check_command exits 0 and reports no failing required checks.` |
| `driver` | Host command that runs the loop, or the fallback when unavailable. Use `/loop` for interval or continuous work, `/goal` for a hard completion requirement, and manual re-invocation when the host lacks those commands. | `/loop`, with manual re-invocation fallback |
| `maturity` | Local maturity flag and a hardening progression. `experimental` = new or unproven; run it with a human in the verification seat. `hardened` = repeatedly successful locally AND its consistently-correct steps have been moved out of the LLM prompt into deterministic code. A loop advances from `experimental` to `hardened` as you replace each reliably-correct step with code. | `experimental` |
| `agents` | Platforms or harnesses the loop is known to run on. Include fallback notes when the host lacks a driver. | `Claude Code, Codex manual fallback` |
| `tags` | Discovery labels for library search and plan selection. | `ci`, `pr`, `checks` |
| `per_iteration_budget` | Optional. Hard cost ceiling for a single iteration (wall-clock, tokens, or tool calls), orthogonal to `iteration_cap`, which bounds the number of iterations rather than the cost of each one. | `5 min wall-clock per iteration` |
| `trace_log` | Optional. Path or sink where each iteration's reasoning, tool calls, and outcome are recorded, so a production loop's decisions can be debugged after the fact. Prefer a JSON Lines sink: one object appended per iteration carrying `loop_number` (int), `success` (bool), `duration` (seconds), `calls` (LLM/API calls this iteration), `tokens` (optional), `exit_reason` (one of `in_progress`, `completed`, `stalled`, `repeated_error`, `permission_denied`, `cap_reached` -- matching the Stall and Fault Detection classes and the Exit-Signal Protocol), and `timestamp` (ISO-8601). JSONL keeps the trace append-only and trivially aggregatable (total iterations, success rate, average duration, total calls). | `docs/loops/<name>-trace.jsonl` |
| `progress_check` | Optional. Stall-detection rule that terminates the loop early when the last N iterations show no measurable progress on `check_command`, distinct from `iteration_cap`, which is a hard count limit. Detects distinct fault classes -- no-progress (no measurable change across N iterations) and repeated-error (the same error recurs even when files change) -- rather than one generic "stuck" check. | `stop if val metric has not improved for 3 iterations` |
| `handoff` | Optional. Human-review destination for items the loop cannot resolve - the inbox, queue, or assigned issue that post-cap failures route to. | `docs/todos.md needs-human section` |
| `gates` | Optional. Typed, blocking, MID-loop pauses that stop the loop to ask a human one concrete question, then resume on the answer. Distinct from `handoff`, which is only a post-cap destination for work the loop could not finish: a gate interrupts a running loop that is otherwise succeeding. Each gate declares its `type` (`owner`, `safety`, `publication`, or `private-data`), the exact `question`, what `unblocks_on` it, and what the loop does `while_waiting`. See "Human-Judgment Gates" below. | `type: publication, question: "Approve this PR body before push?"` |
| `evidence_freshness` | Optional. How long a piece of evidence stays authoritative, and what re-validates it once the window expires. Applies only to long-horizon loops, where a check that passed twenty iterations ago may no longer be true. See "Evidence Freshness" below. | `gh pr checks result: 30 min, revalidate with check_command` |

The first nine fields are required for every loop definition. Any field whose Purpose begins with "Optional" (such as `per_iteration_budget`, `trace_log`, `progress_check`, `handoff`, `gates`, or `evidence_freshness`) is additive: existing loop definitions stay valid without it.

## Worked Example

```yaml
name: ship-pr-until-green
goal: The pull request has no failing required checks.
iteration_cap: 10
check_command: gh pr checks
exit_condition: check_command exits 0 and reports no failing required checks.
driver: /loop, with manual re-invocation fallback when the host lacks /loop.
maturity: experimental
agents:
  - Claude Code
  - Codex manual fallback
  - Cursor manual fallback
tags:
  - ci
  - pr
  - checks
gates:
  - type: safety
    question: The base branch moved. Approve a force-push that rewrites this PR's history?
    unblocks_on: An explicit approve or reject from the PR owner.
    while_waiting: Hold the rebase unpushed and idle. Does not consume iteration_cap.
```

Note what this gate does NOT do: it does not fire on the ordinary fix-and-push each iteration, which is already inside the loop's authority and would make the loop manual if gated. It fires only on the rare step that rewrites shared history. A gate that trips every iteration is a sign the loop's authority was drawn too narrowly, not a sign the loop is being careful.

## Human-Judgment Gates

A gate is a typed, blocking pause in the MIDDLE of a running loop. The loop stops, asks one question, and resumes on the answer. This is a different mechanism from `handoff`: `handoff` routes work the loop could not finish AFTER the cap is reached, while a gate interrupts a loop that is succeeding, because the next step needs judgment the loop does not own.

Four gate types cover the decisions a loop must not make alone:

| Type | Trips when | Example question |
|---|---|---|
| `owner` | The next step is a decision only the work's owner can make. | `Ship the v2 rename now, or hold it for the next release?` |
| `safety` | The next action's blast radius exceeds the loop's authority. | `Approve deleting the 14 orphaned branches listed above?` |
| `publication` | The next step makes something externally visible. | `Approve this release-note text before it is published?` |
| `private-data` | The next step would read or emit private context. | `Approve reading the customer transcript at the path above?` |

Every gate declares four things: its `type`, the exact `question` to ask, what `unblocks_on` it (who can answer and what counts as an answer), and what the loop does `while_waiting`.

Two rules are mandatory:

1. **A gate asks ONE concrete answerable question**, never "how should I proceed". A vague gate is the same failure as a vibe-based `exit_condition`: it moves the loop's judgment problem onto the human without making the decision any easier to make. If the question cannot be answered yes or no, or by picking one named option, it is not yet a gate.
2. **A gate pause is not a loop failure and must not consume `iteration_cap`.** Waiting is not iterating. Charging the cap for a pause penalizes a well-behaved loop that correctly asks for judgment against one that plows ahead, which is exactly the wrong incentive.

This field declares WHICH steps gate and what each one asks. HOW the pause is carried out in the loop body, including the `on_reject` policy (`abort`, `skip`, or `retry`) that makes a rejection deterministic, is the "Human gate checkpoint" pattern in the skill body's Workflow-Control Patterns section. A `retry` counts against `iteration_cap`, because re-running the gated step is real work; the wait that preceded it does not.

## Evidence Freshness

`evidence_freshness` declares how long a piece of evidence stays authoritative and what re-validates it once it expires.

This is not already covered by the existing telemetry fields. `trace_log` is append-only per-iteration telemetry: it records what happened, not what is still true. `progress_check` detects a stalled metric: it fires when nothing is changing, not when something that passed long ago has since decayed. Neither expresses that a check which passed twenty iterations ago may no longer hold.

This matters only for long-horizon loops. A ten-iteration loop that finishes in an hour has no staleness problem, and adding a freshness window to it is ceremony. Declare `evidence_freshness` when the loop runs long enough, or sleeps between wakes long enough, that its evidence can decay underneath it: a scheduled loop that wakes nightly, a loop gated on a slow external check, or any loop whose `check_command` reads state another actor can change.

## Evaluation Rule

The `exit_condition` is a completion claim. Treat it as evidence-bearing: run the `check_command`, read the output and exit code, and let a checker that did not produce the work evaluate whether the condition is met. Cross-link [[verification-before-completion]] for the evidence gate and [[agent-orchestration-primitives]] for the independent-evaluator rule.

When the loop declares `evidence_freshness`, the checker must also confirm that the corroborating evidence is still inside its freshness window. Evidence past its window is not evidence: re-run its declared re-validation before treating the `exit_condition` as met, and never terminate on a stale pass. This directly extends the fresh-evidence requirement in [[verification-before-completion]] across the time axis, which is the axis a single-pass verification gate does not have to consider.

## Anti-Patterns

- No `iteration_cap`: the loop can burn tokens indefinitely and should not run.
- Vibe-based `exit_condition`: "looks better" or "seems ready" cannot terminate a loop.
- Maker self-certifies exit: the same agent that produced the work should not be the only judge of whether the loop is complete. Carve-out: the maker and checker may be the same agent only when the checker is a deterministic, non-LLM oracle (a numeric metric, an exit code, or a compiler result), because a deterministic oracle is its own independent check. Whenever the checker is itself an LLM, the maker must not also be the checker.
- Host-driver assumption: if `/loop` or `/goal` is unavailable, fall back to manual re-invocation with the same schema fields.
- Single-claim exit: terminating on the agent's first "done" without corroboration; require the dual-condition gate (the explicit signal AND command-derived evidence).
- Proceeding without authority: making a `safety`, `publication`, or `private-data` decision the loop does not own, because pausing felt like failing. A loop that publishes, deletes, or reads private context on its own judgment has not saved an interruption; it has spent authority it never had. Declare the gate and take the pause.

The no-`iteration_cap` and vibe-based-`exit_condition` anti-patterns together are what the skill body names "loopmaxxing" (open-ended iteration betting the agent will eventually converge); the required `iteration_cap` and command-derived `exit_condition` exist precisely to prevent it.

## Production Loops

A production loop (one that runs unattended or on a schedule, not a one-off local loop) should declare more than the mandatory `iteration_cap`:

- Set `trace_log` to a JSON Lines sink (see the `trace_log` field above) so each iteration's reasoning, tool calls, and `exit_reason` are recorded and the loop's decisions can be debugged and aggregated after the fact.
- Set `progress_check` so a stuck loop stops on no measurable progress instead of burning its full `iteration_cap`.
- Set `handoff` so any item the loop cannot resolve routes to a human review destination instead of being silently dropped.

A single `trace_log` line (one JSON object per iteration):

```jsonl
{"loop_number": 3, "success": false, "duration": 42, "calls": 5, "exit_reason": "repeated_error", "timestamp": "2026-06-18T17:04:11Z"}
```

## Instance State

Everything above describes a loop DEFINITION: the reusable template, checked into the catalog or the project, that any operator can run. A loop INSTANCE is one running execution of that template. The definition is stable and shared; the instance is mutable, local, and disposable. Keeping them in one file is what forces a cold start to re-derive its own context instead of resuming.

An instance record is a single local file per running loop, carrying:

- The resolved objective for this run (the definition's `goal` with the actual target substituted in).
- Open gates and their exact questions, so a cold start knows what it is waiting on and whom to ask.
- Evidence pointers with their freshness stamps, so a resumed run can tell which evidence it may still trust and which it must re-validate.
- The iteration counter, measured against the definition's `iteration_cap`.
- The next continuation step, written plainly enough that a different agent (or a different tool) can pick the instance up.

The point of the record is that a cold start CONTINUES rather than re-derives, and that an instance is portable across agents and harnesses.

Three constraints are mandatory:

1. **Nexus-Hub ships no runtime that maintains this file.** This is a pattern an operator or a host driver implements, not a component to install. The standing decision that the loop driver is a host command (`/loop`, `/goal`, `/schedule`) covers the instance record too: Nexus-Hub documents the shape and never runs it.
2. **The file is gitignored by default and carries the [[egress-redaction]] discipline.** An instance record accumulates exactly the working context most likely to hold something private: resolved paths, evidence excerpts, and the text of open questions. Treat any copy of it that leaves the machine as an egress event.
3. **It composes with, rather than replaces, the existing memory layer.** [[filesystem-context-patterns]] owns the general discipline of using files as durable agent context, and the instance record is one application of it. [[dev-progress-tracker]] owns forward-looking project work in `docs/todos.md`, which outlives any single run. The instance record owns only the state of one execution, and it is deleted when that execution finishes; anything worth keeping afterwards is promoted to the tracker, not left in the instance file.

This is the local pattern reverse-engineered from an external control plane's durable state kernel, per the reverse-engineer-first rule in the MCP Registry Policy. The doctrine transfers; the runtime is explicitly out of scope.
