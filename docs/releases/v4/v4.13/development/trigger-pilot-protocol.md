# Trigger pilot protocol (frozen)

**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Candidate**: A3
**Phase**: 6
**Frozen on**: 2026-09-16, before any model output was observed
**Status**: frozen. Changing any parameter below after the first scored invocation invalidates the run.

## What this measures

Whether a bounded change to a skill's description and its task-specific pointers improves **observed skill selection** by a real agent, rather than whether shorter descriptions feel better. The result is attributed to the complete instruction bundle, never to description length or pointer wording independently, because only the bundle was varied.

A measured no-change outcome (`MEASURED_NO_CHANGE`) is a valid answer to the question. An unrun or partially run pilot is `UNMEASURED` and does not satisfy the phase.

## Entry prerequisite: resolved

The plan held implementation until a qualified native execution path existed. Read-only inspection on 2026-09-16, plus one calibration probe, established that the `claude` CLI supplies all five required controls:

| Control | Mechanism | Verified |
|---|---|---|
| Two accessible model tiers | `--model`; the `init` event echoes the resolved model | yes |
| Observed skill selection | the `init` event enumerates loaded `skills`; skill invocation appears as a tool call in `stream-json` | yes |
| Bounded subprocess time | `subprocess(timeout=)` plus `--max-budget-usd` per call | yes |
| Enforceable aggregate spend | `result.total_cost_usd` per call, summed by the runner against a running ceiling | yes |
| Isolation (T022) | `--setting-sources`, `--add-dir`, `--strict-mcp-config` | yes |

The prior `NOT QUALIFIED` disposition was recorded against two repository scripts (`run_trigger_evals.py`, model-free; `optimize_skill_description.py`, which forces the skill with `--skill` and has no timeout or spend accounting). Neither the CLI's structured output nor its budget flag had been examined. Both remain unqualified as runners; the CLI is the qualified path.

## Sampled skills (four, frozen)

Hashes are of the unmodified `SKILL.md` at freeze time. Variant B changes only these files.

| Skill | Path | SHA-256 (first 16) | Bytes |
|---|---|---|---|
| `plan-before-code` | `catalog/skills/workflow/plan-before-code/SKILL.md` | `386de17758b474f0` | 12469 |
| `html-output-conventions` | `catalog/skills/developer-experience/html-output-conventions/SKILL.md` | `802318b45288a5f9` | 14455 |
| `skill-description-authoring` | `catalog/skills/developer-experience/skill-description-authoring/SKILL.md` | `57ad29d70519dd00` | 21704 |
| `context-engineering` | `catalog/skills/ai-development/context-engineering/SKILL.md` | `e12e3d91e7b1f736` | 9888 |

## Variants (two, frozen)

| Variant | Definition |
|---|---|
| **A (control)** | The corpus exactly as frozen above. No edit. |
| **B (candidate)** | For each sampled skill: its `description` rewritten to lead with the action and carry explicit trigger phrases plus a `SKIP:` clause, and its body's task-specific pointers tightened. Every other file byte-identical to A. |

Variant B's changed files are hashed at run time and those hashes recorded with the results. The result is attributed to bundle B as a whole.

## Prompt set (six per skill, 24 total, frozen)

Each skill gets six prompts in three pairs. The classification is fixed here, before any run.

| Pair | Count | Intent | Correct behavior |
|---|---|---|---|
| **positive** | 2 | squarely in the skill's territory | the skill IS selected |
| **near-miss** | 2 | adjacent, deliberately outside the SKIP clause | the skill is NOT selected |
| **trivial-edit** | 2 | a small mechanical change needing no skill | no skill selected, no pause |

Two required cases are distributed within those six per applicable skill:

- **small-change itinerary**: a request whose correct handling is a direct edit, used to detect unnecessary process overhead.
- **missing-delegate**: a request naming a skill that does not exist, used to detect whether the agent fabricates coverage or declares the gap.

The prompts are synthetic and contain no private session content, repository working data, or home context.

## Models (two tiers, frozen)

| Tier | Model |
|---|---|
| fast | `claude-haiku-4-5-20251001` |
| strong | `claude-opus-5` |

Per-model results are reported separately and never averaged. A regression on one model is not cancelled by an improvement on the other.

## Budget and caps (frozen, fail-closed)

| Cap | Value | Enforcement |
|---|---|---|
| Invocations | 96 max (4 skills x 6 prompts x 2 variants x 2 models) | runner refuses call 97 |
| Aggregate spend | **USD 10.00** | runner sums `result.total_cost_usd` and stops before a call that would exceed it |
| Per-call budget | USD 0.50 | `--max-budget-usd` |
| Per-call wall time | 180 s | `subprocess(timeout=)` |
| Total wall time | 60 min | runner stops and records partial results |
| Retries | none beyond the cap | a failed call is recorded as failed |

**Measured baseline**: one calibration probe on 2026-09-16 cost **USD 0.0967**, dominated by 76,923 cache-creation tokens rather than output. At that rate 96 calls project to ~USD 9.30 against a USD 10.00 ceiling, a margin of roughly 7 percent. A calibration slice therefore runs first and its real per-call cost decides whether the full run proceeds, is reduced in scope, or is recorded UNMEASURED.

No new credential, provider, or account is introduced. The run uses the already-authenticated CLI.

## Isolation (T022, fail-closed)

Before any scored call:

1. A disposable workspace holds a frozen copy of the public skill corpus only.
2. `--setting-sources` excludes project and local settings; ambient project and home memory discovery is off.
3. `--add-dir` scopes filesystem access to the fixture.
4. `--strict-mcp-config` admits no MCP server.
5. Egress reaches only the already-configured model endpoint.

If any control cannot be demonstrated, the pilot does not launch and the result is `UNMEASURED`. The prompt alone is not an access boundary.

## Acceptance criteria (frozen, per model)

Variant B is promoted for a model only when **all four** hold for that model:

1. **No loss of positive selections.** Every prompt where A selected the skill correctly, B also selects it.
2. **No increase in irrelevant loads.** B does not select the skill on more near-miss or trivial-edit prompts than A.
3. **At least one strict reduction** in irrelevant loading or unnecessary pauses across the pilot.
4. **No trust-boundary or required-verification loss** in any B response.

Failing any criterion on a model means B is not promoted for that model. If no variant qualifies after a fully measured pilot, the result is `MEASURED_NO_CHANGE` and no cosmetic edit is made.

## Ordering and blinding

Calls are emitted in a fixed, seeded shuffle of (skill, prompt, variant, model) so variant order does not correlate with time or rate-limit state. The seed is recorded with the results. The grader reads only the recorded selection evidence, not the variant label, where the runner supports it; where it does not, that limitation is stated in the results.

## Recorded per call

Exact command, CLI version, model id, prompt id, variant id, changed-file hashes, the `init` event's enumerated skills, every tool call observed, `num_turns`, pauses, `total_cost_usd`, `usage`, duration, and terminal status. A call whose selection evidence is missing is recorded as evidence-missing, not as a non-selection.

## What this cannot show

The pilot measures two models on 24 synthetic prompts on one host. It is not a general claim about description style, not a claim about other models, and not a measurement of downstream task quality. Keyword or structural checks cannot substitute for it; a runtime capability gap leaves the affected outcome `UNMEASURED` and licenses no adapter, backend, or budget expansion.

## Amendment 1 (2026-09-16): budget and wall-clock caps

Two frozen caps are revised **before the scored run begins**, on measured evidence and with explicit maintainer authorization. No selection criterion, prompt, skill, variant or model is changed.

### What was measured

| Calibration call | Model | Cost |
|---|---|---|
| Capability probe | `claude-haiku-4-5-20251001` | USD 0.0967 |
| Calibration 1 | `claude-opus-5` | USD 0.5850 |
| Calibration 2 | `claude-sonnet-5` | USD 0.6554 |

Cost is dominated by roughly 77,000 cache-creation tokens per invocation (62 tools and 441 slash commands loaded per call), not by output. `cache_read_input_tokens` was 0 on every call, so each paid full context creation.

Projected for the frozen 96-call matrix: 48 fast calls at ~USD 0.097 (~USD 4.66) plus 48 strong calls at ~USD 0.585 (~USD 28.08), totalling **~USD 32.7**.

### What changed and why

| Cap | Was | Now | Reason |
|---|---|---|---|
| Aggregate spend | USD 10.00 | **USD 35.00** | The original ceiling was set without a measured per-call cost. It is under a third of what the frozen matrix costs, so the run would have stopped partway and recorded UNMEASURED. |
| Total wall time | 60 min | **120 min** | Set without a measured per-call duration, for the same reason. |

Authorized explicitly by the maintainer on 2026-09-16 after the measured projection was presented. This is recorded rather than silently applied because a budget raised quietly is indistinguishable from a budget that was never enforced.

### Rejected alternative

Substituting a cheaper second tier was tried and **failed on measurement**: `claude-sonnet-5` cost USD 0.6554, more than `claude-opus-5` at USD 0.5850. The saving assumed by that approach does not exist, because the dominant cost is per-call context creation rather than the model's token rate.

### Disposition of the calibration calls

The three calls above are **cost measurements, not scored results**. Two used a strong tier that was subsequently reverted, so including them would mix models within one cell. The scored run starts fresh over the full 96-call matrix, and their USD 1.34 is additional to the USD 35.00 ceiling.

### Entry prerequisite: re-dispositioned

The plan recorded Phase 6 as `NOT QUALIFIED`. That disposition is now **RESOLVED on capability**: all five required controls exist and the runner demonstrates them. The residual constraint is **cost**, not capability, which is a different and better-evidenced finding than the plan began with.
