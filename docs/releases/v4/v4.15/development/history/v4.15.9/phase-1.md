# v4.15.9 Phase 1 (reduced): living agent classification

Started 2026-11-17T23:51Z. Worktree `v4.15.9` under the centralized worktree root, base `4d6316cc0`.

## Done

- T001: `docs/reference/agent-classification.md` created from the archived v4.14 rationale, with new "Fast-tier agents" (empty) and "Effort" sections. The Effort section states the D1 decision and that the declaration is not yet applied.
- T002: `tests/validators/test_agent_model_pinning.py` now reads the living file, the duplicated archive fallback is removed, and the unpinned section ends at "Fast-tier agents".

## Deferred (after v4.15.5 merges)

T003 to T008. Adding `effort: high` without the shared Claude-only key list would leak the key to platforms that do not read it. Listed in the lane delta file.

## Verification

- `pytest tests/validators/test_agent_model_pinning.py`: 2 passed. With the `planner` row removed the roster test fails; the row was restored.
- `python scripts/ci/run.py --profile fast --quiet`: 18 passed, 0 failed.
- Verification Expectation (fresh install showing `effort: high`) is not exercisable until T003 lands.

## CI impact

No new commands, dependencies, or test paths.
