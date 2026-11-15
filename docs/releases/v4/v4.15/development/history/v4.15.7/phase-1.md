# CI Speed Phase 1

**Version**: v4.15.7
**Phase**: 1, Latency Audit and Baseline
**Started**: 2026-11-15T13:23:58-08:00
**Ended**: 2026-11-15T13:53:07-08:00 (work complete; the local commit follows immediately)
**Base**: `40f9b0b1c90ee48d2f2fc679b3bfd228ed2d4d74` (origin/develop)
**Branch**: `feat/v4.15.7-adoption-ci-speed-without-coverage-loss`
**Worktree**: `C:\Users\BEDOURTHE\.worktrees\nexus-hub\v4.15.7`

## Outcome

T001 to T004 are complete. `cicd-architect` now ships a read-only, stdlib-only latency audit (`scripts/ci_latency_audit.py`, 331 lines), a latency step (Step 1a) and a reference (`references/ci-latency.md`), and the slow-CI trigger phrases. The baseline is recorded in `v4.15.7-ci-latency-baseline.md`.

## Verification

| Check | Result | Meaning |
|---|---|---|
| `ci_latency_audit.py --repo bendourthe/Nexus-Hub --run-ids <14 IDs> --gate ci-required` | `tests` 47.8 min, queue 37 s, work 2826 s; critical path `tests`; gate mean 49.5 min (median 49.7) | Reproduces the comparison table within 0.1 minute. Three runs of the 17 in the ID range are excluded with reasons (docs-only, two re-run attempts). |
| `ci_latency_audit.py --repo bendourthe/Nexus-AI --workflow ci.yml --runs 5 --conclusion any` | A 10-row table, exit 0 | Works on a second repository. |
| Non-GitHub `--repo https://gitlab.com/a/b` | "only GitHub Actions is supported", exit 2 | Clear refusal. |
| `python -m pytest tests/skills/test_ci_latency_audit.py` | 24 passed | Fixtures cover every failure mode in T002; no stub process starts. |
| `ruff check` on both new Python files | All checks passed | Lint clean. |
| `validate_skills.py --bundles-only`, `check_agentskills_conformance.py` | PASS, 0 errors | Description is 1017 characters (limit 1024); the script and reference are linked from SKILL.md. |
| `python scripts/ci/run.py --profile fast` | 17 passed, 1 failed in 153.8 s | The one failure is `check_registry_entries`: `skills.json` description drift for `cicd-architect`. The data file belongs to the coordinator (delta D1); it is the only failing check. |
| `nexus-hub attribution check` | VERIFIED for the configured identity | Run before the commit. |

The Verification Expectation was exercised through the real boundary (live `gh` against both repositories) and the observed values matched the expected ones.

## CI Impact

One new test file and one fixture folder under trees the `tests` job already collects (`tests/skills/`, `tests/fixtures/`); no new command, dependency, environment variable, secret, workflow change, or artifact. The audit script is distributed inside the skill and is not called by any pipeline.

## Plan delta

Disposition: Incomplete, non-blocking. Evidence: the plan expects 14 baseline runs and 20 integration pull requests; the history holds 14 usable runs only after excluding three, and 10 plan branches (14 pull requests) in the last 120 merged pull requests. PR #650 already delivered Phases 2 and 3. Consequence for remaining phases: Phases 2 and 3 become verification and measurement work; the evidence-based pre-push value is smaller than the plan assumed (1 of 3 red first attempts was a fast-profile kind of failure).

## Deferred Final Validation

None added by this phase; the full profile runs once in 9B (T027). T027 additionally needs the coordinator's data/skills.json delta D1.

## Preservation

The worker wrote only admitted paths. The plan file received checkbox ticks only.

## Open Work

- Coordinator: apply D1 (`data/skills.json` description); known-gaps and DEVLOG entries are in the coordinator deltas file.
- `catalog/skills/infrastructure/cicd-architect/evals/trigger-cases.json` is outside the admitted paths; the two new trigger phrases have no positive eval case yet (proposed in the coordinator deltas).
