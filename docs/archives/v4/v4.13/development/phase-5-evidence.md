# Phase 5 Evidence -- Context fact freshness and revalidation

**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Candidate**: A5
**Phase**: 5 of 7
**Prior phase commit**: `ae496ada` (verified ancestor of HEAD)

No model was invoked. The matrix is evaluated against a fixed instant supplied by the fixture; no test reads a wall clock or sleeps.

## The gap closed

The pack format records `created` (when a fact was written) and `confidence` (how settled it was across observations). Neither answers whether the fact is still true, and both are routinely read as though they did. A fact recorded in March with high confidence is a March fact in September.

The added procedure separates three things that the format had collapsed into two fields: when a fact was **observed**, what target it was observed **of**, and what would make it **stale**.

## Dispositions

| Disposition | Meaning |
|---|---|
| `current` | verified against the present target |
| `historical` | true when observed, not revalidated since |
| `unknown` | source unreachable, or the answer cannot be established now |
| `superseded` | a newer source replaced it, with the old provenance retained |

## Scenario matrix

Evaluated at a controlled clock of `2026-09-15T12:00:00Z` against target identity `v4.13.0`.

| Fact | Scenario | Derived | Revalidation required |
|---|---|---|---|
| CF-1 | check result, high confidence, code changed since | `historical` | yes |
| CF-2 | documented architectural convention | `current` | no |
| CF-3 | source unreachable | `unknown` | yes |
| CF-4 | timestamp after the evaluation clock | `unknown` | yes |
| CF-5 | newer source contradicts an older one | `unknown` | yes |
| CF-6 | explicit supersession with a named replacement | `superseded` | no |

Every disposition is **derived** by the test from the record and the clock, then compared against the fixture's declared expectation. The derivation never reads the expectation.

### Age is not the rule

The fixture is built so that a rule keyed on age gets both of the first two cases wrong:

| Fact | Observed | Disposition |
|---|---|---|
| CF-2 (stable convention) | 2026-03-11 | **current** |
| CF-1 (check result) | 2026-08-02 | **historical** |

The stable fact is five months **older** than the stale one. What separates them is whether the world they describe can change without anyone editing the pack. A further test re-derives CF-2 at a much later instant (`2026-12-31`) and asserts it is still `current`, so a stable design fact cannot decay purely because time passed.

### Conflict and supersession are different states

CF-5 and CF-6 both involve a newer source, and both retain the older provenance. They differ in resolution:

- **CF-5 is unresolved.** A newer reading is not automatically the answer. The disposition is `unknown` and both records stand until the owning source settles it. Deleting the older one would destroy the evidence that there was a disagreement at all.
- **CF-6 is resolved.** Supersession names its replacement, so the new fact is stated and the old provenance is kept for traceability.

### Future timestamp

CF-4 carries `2027-01-04`, after the evaluation clock. It is treated as `unknown` and the anomaly is recorded. This matters because any recency ordering would rank it first, which is the exact inversion of what the reader needs.

## Verification run

```
$ python -m pytest -q tests/skills/test_evidence_driven_improvement.py --no-cov
137 passed in 0.81s

$ python scripts/validate_skills.py --bundles-only
RESULT: PASS (0 errors, 66 warnings)
```

Warning count unchanged from the Phase 1 baseline. The diff added zero non-ASCII lines.

## Ownership boundary

The procedure is optional and prose-first. It adds no required field, no schema version, and no memory-store migration, and a test asserts the text still says existing packs stay readable unchanged.

Freshness semantics are reused from `[[loop-engineering]]`'s `evidence_freshness` rather than redefined; provenance and supersession remain owned by `[[agent-memory]]`. `context-engineering` received a handoff only, bounded three ways: revalidate what the current decision depends on rather than everything, leave an unreachable source `unknown` or `historical` without endless retries, and change no reader format. A test asserts the procedure text does not appear in `context-engineering`, because a duplicated rule is a second source of truth.

## CI impact record (Phase 5)

Recorded against `[[cicd-architect]]`. No pipeline file changed; CI/CD is not this phase's deliverable.

| Dimension | This phase | Covered by existing profiles |
|---|---|---|
| New commands | none | n/a |
| New dependencies | none | yes |
| New environment variables | none | n/a |
| New test paths | none beyond the existing module | yes |
| New artifacts | none | n/a |

Nothing from this phase is carried into the terminal reconciliation.

## Phase 5 gate

| Gate element | Result |
|---|---|
| Test failures | 0 (137 passed in the phase module) |
| Lint errors | 0 new |
| Build | n/a |
| Functional smoke | six-scenario matrix derived against a controlled clock and compared to declared dispositions |
| Feature matches expected behavior | yes -- including the age-inversion and clock-stability controls |

**Verdict: GO.**

## Limitations

- The matrix exercises the disposition rules. It is not evidence about any real pack, memory store, or deployment.
- The derivation used in tests is a deterministic reference implementation for checking the rules, not a component shipped for callers to import.

## Repository-native gate

```
$ python scripts/ci/run.py --profile fast --quiet
FAIL: 14 passed, 1 failed, 0 skipped, 0 advisory in 139.2s
```

The single failure is `check_commit_attribution` over pre-existing history (WN-1), confirmed unchanged from the Phase 1 baseline of 14 passed / 1 failed.

### Targeted regression check

Rather than assume the catalog edits were isolated, every test module referencing an edited skill was run together:

```
$ python -m pytest -q --no-cov <13 modules referencing the edited skills>
632 passed in 7.08s
```

Modules covered `agent_memory`, `closure_gate`, `evaluation_methodology`, `eval_pipeline_audit`, `evidence_driven_improvement`, `functional_verification_crosslinks`, `reliability_metric_ownership`, `v4_1_skill_mechanics`, the two communication-contract validators, `loop_engineering_bundle`, `verifier_taxonomy_and_lifecycle`, and the `eval_loop` hook tests.

## Cross-phase correction made during this phase

The fast profile flagged two findings introduced by Phase 2, both from the same cause:

```
catalog/skills/.../scripts/trace-example.py:50:41: personal path leak: <redacted home path>
docs/releases/v4/v4.13/development/phase-2-evidence.md:88:21: personal path leak: <redacted home path>
```

The sentinel exception string was a POSIX home-directory path ending in an SSH private key. That is shaped exactly like a real home-directory path, which is what the repository's personal-path guard exists to catch, so the guard was correct even though the value was synthetic.

The sentinel was changed to `/srv/secrets/SENTINEL-private-key.pem`, which keeps its purpose (a filesystem path inside an exception string, proving the category-mapping discards it) without resembling a personal path. The guard now exits 0. The Phase 2 evidence file was updated with the corrected sentinel and the new script hash `2828b80a175029cc`, and the test assertion was widened to `private-key` and `/srv/secrets`.

The guard findings above are quoted with the offending value redacted. An earlier revision of this file quoted it verbatim, which reintroduced the exact string the guard exists to catch and left `validate_no_personal_paths` failing while this file claimed it passed. Corrected during Phase 6.

This is recorded here rather than silently amended into Phase 2, because the Phase 2 commit already exists and the correction happened during Phase 5.

### An open item, stated plainly

A full `pytest tests/` run was started for this phase and had not produced output when this phase closed. The evidence above rests on the 13-module targeted regression run and the repository-native fast profile, not on a completed whole-tree run. The full tree is exercised by the `full` profile in Phase 7, which has not been run.
