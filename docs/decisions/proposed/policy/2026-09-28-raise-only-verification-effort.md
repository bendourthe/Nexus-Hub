# Decision: Raise-Only Verification Effort

Status: proposed - implemented in v4.14.1 Phase 4; integration and release pending.

Maintainers of the routing contract use this record when changing how `/plan` and `/implement` recommend reasoning effort. It covers the optional per-phase verification effort, the raise-only edge-case and unattended modifiers and their `high` cap, where each modifier is evaluated, and the new `plan_status.py --check` mode.

**Date**: 2026-10-20. **Source**: `docs/releases/v4/v4.14/plans/v4.14.1-adoption-effort-allocation.md`, resolved decisions 3 to 9.

## Problem

Nexus-Hub computed one effort per phase from the same aggregate score as the tier, and ran verification at that effort. Higher effort mostly buys verification and independent judgment: it fixes failures caused by missed edge cases and matters most when nobody is steering. An edge-case-dense phase with a modest overall score therefore verified at the same effort it was built at, and an unattended run had no way to ask for more.

## Proposal

1. A plan phase may carry an optional `**Recommended verification effort**` in the vocabulary `low`, `medium`, `high`, `max`. An absent field equals the phase's effort.
2. `model-map.py score` gains `--edge-cases {low,medium,high}` and `--unattended` and returns `verification_effort` beside `tier` and `effort`. Tier and effort are computed exactly as before. Verification effort starts at the effort, rises to at least `medium` or `high` for edge-case density `medium` or `high`, rises one more level when unattended on top of that density, never exceeds `high` through the modifiers, and is never lower than the effort. Unattended alone never raises it.
3. `/plan` records only the edge-case-driven value; the `/implement` pre-flight applies `--unattended` from the actual run mode and keeps the higher of the field and the re-score.
4. `plan_status.py --check <plan>` prints `phase N: verification effort X below effort Y` or `phase N: invalid verification effort X` on stderr per violation and exits 3. `--plan`, `--next`, and `hardest()` are unchanged: `hardest()` still returns the maximum implementation effort, because `--next` sets the session effort for implementation and verification effort is applied per phase at the GO/NO-GO gate.

The definitions live in `catalog/skills/ai-development/model-routing/references/effort-modifiers.md`.

## Consequences

- Every existing recommendation is unchanged: without the new flags `score` returns today's output plus `verification_effort` equal to `effort`, and `plan_status.py --plan` and `--next` output is byte-identical for every existing plan.
- The installed `plan_status.py` gains exactly one behavior, the `--check` mode; `/update release` calls only `--next`.
- Phases that verify above their effort request the behaviors in `implement-phase/references/verification-behaviors.md`; a missing result becomes a NO-GO for them and stays advisory elsewhere.
- The raise direction ships unmeasured. The `high` cap bounds it, and known gap `DF-16` in `docs/releases/v4/v4.14/known-gaps.md` holds the measurement that would lift or keep the cap. Lowering effort stays out of scope until measured (`DF-15`).

## Alternatives considered

1. **Raise the tier-coupled effort directly.** Rejected: every recommendation for an edge-case-dense phase would change, the implementation itself would run at the higher effort where only verification benefits, and the no-degradation guarantee would be harder to audit because one number would carry two meanings.
2. **Add a glance-table column.** Rejected: the Phases at a Glance grammar is asserted by `tests/plans/test_v3_15_9_routing_contract.py` and read by tooling across every historical plan; a per-phase field carries the same information without changing that grammar.
3. **Compute verification effort only at run time, with no plan field.** Rejected: the planner is where edge-case density is judged with the whole plan in view, and a recorded value is reviewable before any code runs. The run mode, by contrast, is known only at `/implement`, which is why the unattended modifier stays a run-time step.

## Acceptance criteria

- `model-map.py score low medium low low medium --edge-cases high --unattended` returns `{"tier": "standard", "effort": "medium", "verification_effort": "high"}`, and `score medium medium medium low low --edge-cases high --unattended` returns `verification_effort` `high`, not `max`.
- `plan_status.py --check` exits 0 on every existing `docs/**/plans/*.md` and exits 3 with the exact line on a fixture whose phase records a lower value.
- `--plan` and `--next` output is byte-identical between the baseline-commit script and the changed script on every plan.

## Risks

- An unmeasured raise can spend more on verification than it returns; the `high` cap and `DF-16` bound that.
- A planner can omit the field on an edge-case-dense phase. The pre-flight re-score still applies the edge-case modifier, so the omission costs a recorded value, not the raise itself.
- Platforms with a narrower effort knob (Codex accepts `low`, `medium`, `high`; Gemini CLI documents none) cannot always apply the computed value. The gate clamps it, records the shortfall, and requests the behaviors explicitly instead.
