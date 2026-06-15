# Loop Definition Schema

This schema is the local, service-free structure for reusable loop definitions. Each loop definition must be readable cold by an agent or operator and must make termination observable before the first iteration starts.

## Fields

| Field | Purpose | Example |
|---|---|---|
| `name` | Kebab-case identifier used in the library and references. | `ship-pr-until-green` |
| `goal` | Falsifiable end state in one sentence. | `The pull request has no failing required checks.` |
| `iteration_cap` | Hard maximum number of iterations before the loop stops and asks for human review. | `10` |
| `check_command` | Exact shell command run between iterations to measure progress. Use a project-specific command when possible. | `gh pr checks` |
| `exit_condition` | Observable, command-derived condition that ends the loop. A checker evaluates this condition; the maker does not self-certify it. | `check_command exits 0 and reports no failing required checks.` |
| `driver` | Host command that runs the loop, or the fallback when unavailable. Use `/loop` for interval or continuous work, `/goal` for a hard completion requirement, and manual re-invocation when the host lacks those commands. | `/loop`, with manual re-invocation fallback |
| `maturity` | Local maturity flag and a hardening progression. `experimental` = new or unproven; run it with a human in the verification seat. `hardened` = repeatedly successful locally AND its consistently-correct steps have been moved out of the LLM prompt into deterministic code. A loop advances from `experimental` to `hardened` as you replace each reliably-correct step with code. | `experimental` |
| `agents` | Platforms or harnesses the loop is known to run on. Include fallback notes when the host lacks a driver. | `Claude Code, Codex manual fallback` |
| `tags` | Discovery labels for library search and plan selection. | `ci`, `pr`, `checks` |
| `per_iteration_budget` | Optional. Hard cost ceiling for a single iteration (wall-clock, tokens, or tool calls), orthogonal to `iteration_cap`, which bounds the number of iterations rather than the cost of each one. | `5 min wall-clock per iteration` |
| `trace_log` | Optional. Path or sink where each iteration's agent reasoning and tool calls are recorded, so a production loop's decisions can be debugged after the fact. | `docs/loops/<name>-trace.md` |
| `progress_check` | Optional. Stall-detection rule that terminates the loop early when the last N iterations show no measurable progress on `check_command`, distinct from `iteration_cap`, which is a hard count limit. | `stop if val metric has not improved for 3 iterations` |
| `handoff` | Optional. Human-review destination for items the loop cannot resolve - the inbox, queue, or assigned issue that post-cap failures route to. | `docs/todos.md needs-human section` |

The first nine fields are required for every loop definition. Any field whose Purpose begins with "Optional" (such as `per_iteration_budget`, `trace_log`, `progress_check`, or `handoff`) is additive: existing loop definitions stay valid without it.

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
```

## Evaluation Rule

The `exit_condition` is a completion claim. Treat it as evidence-bearing: run the `check_command`, read the output and exit code, and let a checker that did not produce the work evaluate whether the condition is met. Cross-link [[verification-before-completion]] for the evidence gate and [[agent-orchestration-primitives]] for the independent-evaluator rule.

## Anti-Patterns

- No `iteration_cap`: the loop can burn tokens indefinitely and should not run.
- Vibe-based `exit_condition`: "looks better" or "seems ready" cannot terminate a loop.
- Maker self-certifies exit: the same agent that produced the work should not be the only judge of whether the loop is complete. Carve-out: the maker and checker may be the same agent only when the checker is a deterministic, non-LLM oracle (a numeric metric, an exit code, or a compiler result), because a deterministic oracle is its own independent check. Whenever the checker is itself an LLM, the maker must not also be the checker.
- Host-driver assumption: if `/loop` or `/goal` is unavailable, fall back to manual re-invocation with the same schema fields.

The no-`iteration_cap` and vibe-based-`exit_condition` anti-patterns together are what the skill body names "loopmaxxing" (open-ended iteration betting the agent will eventually converge); the required `iteration_cap` and command-derived `exit_condition` exist precisely to prevent it.

## Production Loops

A production loop (one that runs unattended or on a schedule, not a one-off local loop) should declare more than the mandatory `iteration_cap`:

- Set `trace_log` so each iteration's reasoning and tool calls are recorded and the loop's decisions can be debugged after the fact.
- Set `progress_check` so a stuck loop stops on no measurable progress instead of burning its full `iteration_cap`.
- Set `handoff` so any item the loop cannot resolve routes to a human review destination instead of being silently dropped.
