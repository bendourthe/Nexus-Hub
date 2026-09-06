# Session History -- agentic-setup-adoption, Phase 5 (profiling harness)

**Date**: 2026-07-13
**Version**: v3.14.0
**Plan**: `docs/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md`
**Phase**: 5 of 8 -- Performance profiling harness
**Branch**: `feat/agentic-setup-adoption` (off `develop`)

## Goal

Adopt point 17 of the comparison: runnable profiling tools the agent can use for targeted benchmarking and profile comparison. Per the plan's Complexity Tracking, augment the existing `code-optimizer` skill rather than mint a new skill.

## What was done

### 5.1 Bundled profiler scripts (into code-optimizer)

Added two Tier-3 scripts under `catalog/skills/developer-experience/code-optimizer/scripts/` (no new skill, no frontmatter change):

- `profile_run.py`: runs a Python target under `cProfile` and writes a structured JSON profile (top-N functions by cumulative time, with ncalls / tottime / cumtime). It restores `sys.argv` in a `finally`, treats the target's `sys.exit()` as normal completion, and downgrades any target crash to a reported exit 2 - a profiler must survive the code it profiles.
- `profile_compare.py`: diffs two profiles and reports faster / slower / NEW / GONE per function by cumulative-time delta. Informational (always exit 0); the pass/fail regression gate is the separate `performance-regression-gate` skill.

### 5.2 SKILL.md reference + test + CI

- Added a "Bundled profiling harness" subsection to `code-optimizer/SKILL.md` referencing both scripts (orphan-bundle audit clean).
- `tests/skills/test_profiling_harness.py` (7 tests): profile_run emits a profile containing the expected function, missing target -> exit 2, survives a target `sys.exit`; profile_compare reports faster/slower and NEW/GONE, bad input -> exit 2.
- CI: no change needed - the Phase 3 `pytest tests/skills -v` step already runs this test, and `cProfile` is stdlib (no new CI dependency).

## Bug caught by the test

`profile_run.py` initially used `nargs=argparse.REMAINDER` for the pass-through target args, which greedily swallowed `--out` / `--top` into the target-args list, so `--out` never parsed and argparse exited 2. The two `profile_run` tests caught it; fixed by switching to `nargs="*"` (which respects `--` as the pass-through separator).

## Deviations

- **`.py`-only bundled scripts** (no `.sh`/`.ps1` runners), consistent with Phases 3-4.
- **No registry change**: augmenting an existing skill's bundle leaves its frontmatter (and therefore `skills.json` / `SKILL_INDEX` / `marketplace`) untouched. `code-optimizer`'s `skills.json` `size` field is now slightly stale (it was already stale before this phase; `make validate` does not gate it) - reconciled at the next catalog rebuild.

## Validation

- `pytest tests/skills`: 35 passed (including the 7 new profiling tests).
- `ruff check` + `ruff format --check`: clean on both scripts and the test.
- Bundle-orphan audit: PASS (both scripts referenced from SKILL.md). New scripts + test ASCII-clean.
- Quality gate: GO.

## Next steps

- Phase 6: skill-native conventions and refinements (doc-header summary convention, run-the-app verb in the five base templates, session worksheet handoff + git-tag convention, helper-script-authoring skill, persona-owned-docs binding).
