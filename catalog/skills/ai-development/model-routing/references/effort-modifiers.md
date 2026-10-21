# Effort Modifiers

**Covers**: the edge-case density, unattended, and failure-class definitions that modify an effort recommendation, how a failing phase escalates by failure class, and which skill owns each effort-related rule. Read when scoring a phase's verification effort, deciding the run mode at the `/implement` pre-flight, or escalating a phase that keeps failing.

This file is the single owner of these definitions. Every other file references `[[model-routing]]` by name and never restates them.

## Edge-case density

How much of a phase's correctness depends on inputs and states beyond the common path. Score it from the phase's stated work, not from how hard it feels.

| Density | Criteria |
|---|---|
| `high` | The phase parses or sanitizes untrusted input, crosses a security or permission boundary, touches concurrency, storage, or crash recovery, implements a numeric or search algorithm with a correctness or performance target, or fixes a bug in existing code from a failure report. |
| `medium` | The phase handles several input shapes or states with known boundaries. |
| `low` | Mechanical, documentation, or configuration work. |

**Evidence to quote**: the boundary the phase crosses, the input or state variants it handles, its stated correctness or performance target, or the failure report it fixes.

**Examples**: a sanitizer for user-supplied file names is `high`; a CLI flag that accepts three documented value forms is `medium`; renaming a documentation link is `low`.

## Unattended

A phase is unattended when no human is expected to answer within it: an `/implement` full run (the default mode), a loop-operator run, or a scheduled run. A single-phase or `phase-by-phase` run in an interactive session is attended.

- Evaluate it at the `/implement` pre-flight from the actual run mode, never at `/plan`, because the run mode is known only when `/implement` is invoked.
- It adds one level only on top of `medium` or `high` edge-case density, and never above `high`. Unattended work alone never raises effort.

**Evidence to quote**: the invocation and the mode it resolved to, for example `/implement v4.14.1` resolving to the full driver.

**Examples**: a scheduled overnight parser repair is unattended; `/implement <plan> phase 2` in an interactive session is attended.

## Verification effort

The effort at which a phase's verification runs. It starts at the phase's effort and only ever rises:

1. Edge-case density `medium` raises it to at least `medium`; `high` raises it to at least `high`.
2. When the phase is unattended and density is `medium` or `high`, it rises one more level.
3. The modifiers never raise it above `high`. `max` appears only when the phase's effort is already `max`, and it is never lowered.

`/plan` records the result of step 1 alone, as the optional `**Recommended verification effort**` field, and omits the field when it equals the effort. The `/implement` pre-flight re-scores with step 2 from the actual run mode and keeps the higher of the field and the re-score. `scripts/model-map.py score --edge-cases <density> [--unattended]` computes it.

The `high` cap holds until the raise direction is measured (known gap `v4.14#DF-16` (the raise-direction measurement) in the Nexus-Hub repository's v4.14 ledger). Lowering any effort stays out of scope until measured (known gap `v4.14#DF-15` (the lower-direction modifier)).

## Failure class

Applies only to troubleshooting failures classified `IMPL`. `TEST` and `ENV` failures keep their existing handling. Classify at the end of troubleshooting iteration 2, and quote the evidence. A phase's failures are repeating when any `IMPL` failure remains after iteration 2; classify from the whole sequence of attempts, not from a single test.

| Class | Evidence |
|---|---|
| Edge-case miss | Each attempt fixed some failing cases, and the new failures are specific inputs. |
| Wrong approach | The same failure persists across both attempts, a fix reintroduced an earlier failure, or the failure contradicts a stated constraint. |

**Evidence to quote**: the failing test names and inputs after each attempt, and which earlier failures each attempt fixed.

**Ties**: any failure that persists unchanged across both attempts makes it a wrong approach, even when the attempts fixed other cases. When a phase's repeating failures fall into both classes, the phase escalates by the wrong-approach row.

**Examples**: a sanitizer that passes the original five cases after each fix but fails on two new inputs each time is an edge-case miss; a migration test that fails with the same assertion after both attempts is a wrong approach.

## Escalation by failure class

The routed escalation is option D of the troubleshooting loop's exhaustion menu. Every option is confirm-first and upshift-only, as Step 7 of `SKILL.md` requires.

The class decided at iteration 2 guides the iteration-3 fix; option D is offered with the exhaustion menu when failures remain after it. "One level" is the next value in the portable vocabulary `low`, `medium`, `high`, `max`; Step 6's platform profile maps it to the host's own knob.

| Class | Current effort | Escalation |
|---|---|---|
| Edge-case miss | below `max` | Raise effort one level. |
| Edge-case miss | `max` | Not fixable by effort: re-plan the failing sub-task or ask the user, or upshift the tier when it is below `frontier`. |
| Wrong approach | any, below `frontier` | Upshift the tier, re-plan the failing sub-task, or ask the user. Never raise effort alone: more effort mostly adds verification and does not change the approach. |
| Wrong approach | `frontier` | Re-plan the failing sub-task or ask the user. |

## Rule ownership

| Concern | Owner | Non-owners do |
|---|---|---|
| Edge-case density, unattended, and failure-class definitions; failure-class escalation routing; the verification-effort computation and its `high` cap | `model-routing` (this file, Step 7, `model-map.py`) | Reference `[[model-routing]]`; never restate a definition |
| Effort-level guidance: what effort buys, the decision table, one long task vs a loop, when `max` pays | `prompt-engineering` (`references/effort-level-strategy.md`) | Point at it for level choice |
| Whether an effort change keeps the prompt cache | `prompt-engineering` (`references/step-8-optimize-cost-and-latency.md`) | Link to it; never restate the rule |
| When verification runs, the troubleshooting loop, the GO/NO-GO gate, and which behaviors it requests | `implement-phase` (runbook, `references/verification-behaviors.md`) | Reference the gate |
| The optional plan field in the phase template | `implementation-plan` | Reference the template |
| The procedure behind each verification behavior | The owner skill named in `verification-behaviors.md` (for example `functional-verification` for the real-boundary exercise) | Name the behavior and delegate |
