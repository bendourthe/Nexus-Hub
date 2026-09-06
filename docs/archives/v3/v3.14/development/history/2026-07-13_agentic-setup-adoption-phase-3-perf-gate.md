# Session History -- agentic-setup-adoption, Phase 3 (performance-regression gate)

**Date**: 2026-07-13
**Version**: v3.14.0
**Plan**: `docs/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md`
**Phase**: 3 of 8 -- Performance-regression gate
**Branch**: `feat/agentic-setup-adoption` (off `develop`)

## Goal

Adopt point 16 of the comparison: the committed-baseline regression gate that `performance-testing` leaves open. A skill plus a deterministic bundled script that records a baseline and fails when a metric degrades beyond a threshold.

## What was done

### 3.1 performance-regression-gate skill

Authored `catalog/skills/tests-generation/performance-regression-gate/SKILL.md` (82 lines): which hot-path metrics to gate, capture-and-commit a baseline, compare current-vs-baseline with a per-metric direction and noise-tolerant threshold, wire into CI, and re-baseline only deliberately. It references the bundled `scripts/perf_baseline.py` so the body stays thin. Distinguished from `performance-testing` (writes the benchmarks) and `code-optimizer` (one-off profiling). Registered across `skills.json` (270 skills), `SKILL_INDEX.md` (+1 row, total 270), and `marketplace.json` (tests-generation 19 -> 20).

### 3.2 Bundled perf_baseline.py + test + CI

- `catalog/skills/tests-generation/performance-regression-gate/scripts/perf_baseline.py` (stdlib-only, zero-network): `--record` writes a baseline (threshold + higher-is-better + metrics); `--check` compares and exits non-zero on any regression, with a per-metric direction (lower-is-better for latency/size, higher-is-better for throughput), a noise threshold, a diff table, and NEW/MISSING accounting.
- `tests/skills/test_perf_baseline.py` (8 tests): record+check pass, lower-is-better regression fail, within-threshold pass, higher-is-better drop fail and gain pass, new/missing metrics tolerated, bad input -> exit 2.
- CI: added a `pytest tests/skills -v` step to the `tests` job so the bundled-script tests run on every relevant push (ubuntu ships the needed runtime; the tests are pure Python).

## Deviations

- **No `.ps1` sibling for `perf_baseline.py`** (the plan mentioned a PowerShell wrapper). A pure-Python bundled script is already cross-platform via `python script.py`; every presentify bundled script (`extract_content.py`, `build_presentation.py`, `design_seed.py`) is `.py`-only. The AGENTS.md scripts-parity rule targets `.sh` scripts, which are bash-only. A redundant `.ps1` wrapper that just shells to Python adds no capability, so it was omitted.

## Validation

- `pytest tests/skills/test_perf_baseline.py`: 8 passed (locally, on the Windows dev host - pure Python, no bash, so no WN-3 limitation).
- `ruff check` and `ruff format --check`: clean on the script and the test.
- `skills.json`: valid JSON, 270 skills, no dupes, perf-gate present. Bundle-orphan audit: PASS (perf_baseline.py referenced from SKILL.md). New skill + script ASCII-clean.
- Quality gate: GO.

## Next steps

- Phase 4: visual-regression discipline (`visual-regression-testing` skill + bundled capture / perceptual-diff scripts + agent visual-review gate).
