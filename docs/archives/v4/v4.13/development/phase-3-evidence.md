# Phase 3 Evidence -- Approved lessons to regression evidence

**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Candidate**: A2
**Phase**: 3 of 7
**Prior phase commit**: `0d1a4ccf` (verified ancestor of HEAD)

No model was invoked. The replay is deterministic, runs over a disposable file in pytest's `tmp_path`, and touches no external tool, credential, user directory, real session, or production data.

## Artifacts

| Path | Kind |
|---|---|
| `catalog/skills/workflow/continuous-learning/references/verified-improvement-loop.md` | cross-owner lifecycle recipe |
| `tests/fixtures/agent-improvement/improvement-lifecycle.json` | synthetic lifecycle fixture |
| `catalog/skills/workflow/continuous-learning/SKILL.md` | links the recipe |
| `catalog/skills/workflow/skill-eval-loop/SKILL.md` | graduation pool contract and chain identifiers |

## The chain, observed end to end

The recipe links seven steps by stable identifier. The fixture instantiates the chain and the test walks it:

| Link | Identifier | Observed |
|---|---|---|
| Confirmed observation | `OBS-2026-0914-001` | labeled `failure` with evidence |
| Minimized regression | `REG-0031` | pool `development`, `never_holdout: true` |
| Measurement frame | `rubric-v4` / `split-2026-09-14` | `frozen_before_scoring: true` |
| Candidate diff | `CAND-0044`, `CAND-0045`, `CAND-0046` | three contents |
| Replay result | `RPL-0091` to `RPL-0093` | derived by the oracle |
| Disposition | approved / rejected | derived, then compared to declared |
| Rollback target | pre-edit SHA-256 | compared after restore |

## Oracle independence

The oracle reads only the artifact content and the check definitions. It never consults a candidate's `expected_*` fields, so the test compares a **derived** disposition against a **declared** one rather than restating the fixture.

That independence was demonstrated during the phase rather than merely asserted. The first run failed:

```
FAILED test_derived_disposition_matches_the_declared_one
assert False == True
```

`CAND-0046` had been declared `expected_existing_checks_pass: true`, but its content contains the phrase `Assume the suite passed`, which trips `CHK-3`. The oracle contradicted the fixture and the fixture was wrong. Had the oracle copied the candidate's declared expectation, the error would have passed silently.

## Replay results

| Candidate | Closes seeded failure | Existing checks hold | Derived disposition |
|---|---|---|---|
| `CAND-0044` | yes | yes | **approved** |
| `CAND-0045` | yes | **no** (`CHK-2`) | **rejected** |
| `CAND-0046` | no | no (`CHK-3`) | **rejected** |

`CAND-0045` is the load-bearing case. It closes the seeded failure while deleting the line `Never paste credentials into a shared report.` A checker watching only the target metric would accept it, and a trust-boundary rule would disappear in a change recorded as an improvement.

### Preconditions verified

Both directions were checked, because a fixture that trivially satisfies its own test proves nothing:

- The seeded check **fails** on the original content, so there is a real failure to close.
- Every existing regression check **passes** on the original content, so each can serve as a guard.

### Byte-exact rollback

For each rejected candidate the test asserts three things in order: the candidate changed the file (hash differs), the oracle rejected it, and the restored file hash equals the pre-edit hash exactly. A rollback that restored intent but reformatted whitespace would fail this.

### Fail-closed cases

| Case | Condition | Result |
|---|---|---|
| `FC-1` | same `candidate_id` recorded twice | raised; no overwrite |
| `FC-2` | one candidate both approved and rejected | raised; no later-wins resolution |
| control | two distinct candidates | accepted, so the guard is not blanket-rejecting |

An additional control asserts the oracle raises on an unknown check kind; a silently ignored kind would make every check vacuous.

## Verification run

```
$ python -m pytest -q tests/skills/test_evidence_driven_improvement.py --no-cov
88 passed in 0.60s

$ python scripts/validate_skills.py --bundles-only
RESULT: PASS (0 errors, 66 warnings)
```

Warning count unchanged from the Phase 1 baseline; the new reference produced no orphan warning. The strict ASCII check over the three changed Markdown files reports 8 non-ASCII lines in `skill-eval-loop/SKILL.md` at lines 82-89. Those are a pre-existing directory-tree diagram drawn with box-drawing characters; this phase added zero non-ASCII lines, verified by scanning the added lines of the diff. They are left untouched under the scope rule.

## CI impact record (Phase 3)

Recorded against `[[cicd-architect]]`. No pipeline file changed; CI/CD is not this phase's deliverable.

| Dimension | This phase | Covered by existing profiles |
|---|---|---|
| New commands | none | n/a |
| New dependencies | none (`hashlib` from the standard library) | yes |
| New environment variables | none | n/a |
| New test paths | none beyond the existing module | yes |
| New artifacts | none; the replay writes only into pytest `tmp_path` | n/a |

Nothing from this phase is carried into the terminal reconciliation.

## Phase 3 gate

| Gate element | Result |
|---|---|
| Test failures | 0 (88 passed) |
| Lint errors | 0 new |
| Build | n/a |
| Functional smoke | full lifecycle replayed over a disposable file, including rollback hash comparison |
| Feature matches expected behavior | yes -- approval, two distinct rejections, byte-exact restore, fail-closed conflicts |

**Verdict: GO.**

## Limitations

- The fixture demonstrates lifecycle wiring. It is not evidence that any real learned change improves model behavior.
- The oracle is a deterministic text predicate, chosen because it is independent and checkable. A production checker would be a different implementation with the same independence requirement.
- No skill was retired in this phase; retirement remains the existing advisory rule in `skill-eval-loop`.
