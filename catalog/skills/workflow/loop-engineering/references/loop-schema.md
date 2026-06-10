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
| `maturity` | Local maturity flag. Use `experimental` for new or unproven definitions and `hardened` only after repeated successful local use. | `experimental` |
| `agents` | Platforms or harnesses the loop is known to run on. Include fallback notes when the host lacks a driver. | `Claude Code, Codex manual fallback` |
| `tags` | Discovery labels for library search and plan selection. | `ci`, `pr`, `checks` |

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
- Maker self-certifies exit: the same agent that produced the work should not be the only judge of whether the loop is complete.
- Host-driver assumption: if `/loop` or `/goal` is unavailable, fall back to manual re-invocation with the same schema fields.
