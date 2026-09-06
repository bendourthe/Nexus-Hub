# Session History -- Phase 5 of v1.1.5 adoption-skills plan: skill-eval-loop + description optimizer (A6, A7)

**Date**: 2026-05-08
**Plan**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../plans/adoption-skills.md)
**Phase**: 5 of 7 -- skill-eval-loop + description optimizer (A6, A7)
**Status**: Complete; ready for commit. Plan advances to Phase 6 next.

## Goal

Ship the eval-iteration workflow + browser viewer + description optimizer as a single integrated skill, with a CLI-agnostic adapter following the v1.1.3 four-hook precedent (claude / gemini / codex / opencode parity, no cross-CLI fallback). The skill drives a closed-loop evaluation against any DevAI-Hub skill via paired with-skill / without-skill runs, assertion-graded outputs, browser-reviewed benchmarks, structured feedback capture, and five named improvement heuristics.

## Pre-implementation review

- Confirmed Phases 1-4 complete via `git log --oneline -20` (Phase 4's `f5660c5` is the most recent, behind `[Unreleased]`).
- Surveyed existing artifacts in parallel: read `catalog/skills/workflow/doc-coauthoring/SKILL.md` (Phase 2 reference for skill shape), `catalog/hooks/tests/test_diff_review_hooks.py` (the v1.1.3 four-hook parity-test pattern), `scripts/generate_report.py` (the lazy-import precedent for optional deps), `Makefile` (validation + lint + test wiring), `scripts/validate_skills.py` (orphan-bundle audit), `data/skills.json` (entry schema for `doc-coauthoring`), `data/marketplace.json` (workflow category before increment), `catalog/hooks/tests/test_skill_bundles.py` (the importlib-based test loader pattern).
- Located the explicit-name copy blocks in both installers: `scripts/installer.sh:1413-1416` and `scripts/installer.ps1:1722-1725` (the `generate_report.py` block to model after).

## Steps executed

### 1. Authored the skill body and bundled docs

- Created `catalog/skills/workflow/skill-eval-loop/SKILL.md` (~200 lines) with full DevAI-Hub frontmatter (`name`, pushy `description` with verbatim trigger phrases + `SKIP:` clause, `summary_l0`, `overview_l1`).
- Authored four reference files under `references/`: `schemas.md`, `improvement-heuristics.md`, `cli-adapter.md`, `description-optimizer.md`. Each is self-contained per the AGENTS.md three-tier loading model.
- Authored three sub-agent prompt files under `agents/`: `grader.md`, `comparator.md`, `analyzer.md`. The directory sits sibling to `references/` and is intentionally outside the A13 orphan-audit scope (which covers `scripts/` / `references/` / `assets/`).
- Verified every bundled file is referenced from SKILL.md so the validator's bundle audit stays clean.

### 2. Built the three repo-level dispatcher scripts

- `scripts/aggregate_benchmark.py` (stdlib-only, pure post-processing): walks `<workspace>/iteration-N/` and emits `benchmark.json` + `benchmark.md` with per-eval pass-rate / duration / tokens (mean + stddev) and the with_skill-vs-baseline delta.
- `scripts/skill_eval_viewer.py` (stdlib-only, two modes): server mode starts an `http.server`, opens the browser, accepts `POST /submit-feedback`. Static mode (`--static <path>`) writes a self-contained HTML file whose "Submit All Reviews" button downloads `feedback.json` as a JS Blob (for headless / CI environments). Two-tab UI ("Outputs" + "Benchmark") rendered via `str.format` templating.
- `scripts/optimize_skill_description.py` (description optimizer): deterministic 60/40 train-test split (`--seed` default 42), per-iteration candidate generation via the chosen CLI, held-out-test selection for `best_description` (tie-break on train rate then on length, shorter wins), `--max-iterations` early-stop on flat or perfect score. `--dry-run` prints the plan and exits 0 without invoking any CLI.
- CLI dispatch in the optimizer: a single `invoke_cli(cli, prompt, skill_path)` function with `assert cli in {"claude", "gemini", "codex", "opencode"}` and four parallel `if cli == "X":` branches; no cross-CLI fallback.

### 3. Wrote the parity pytest module

- Created `catalog/hooks/tests/test_eval_loop.py` (14 tests, three classes).
- `TestEvalLoopCLIAdapter` source-inspects each `if cli == "X":` branch in the dispatcher: locates the header line, walks forward collecting strictly-more-indented lines, stops at the next sibling line (header indent or less), and asserts no other CLI binary appears in argv-list form within that body. Parametrized over the four CLIs.
- `TestOptimizerDryRun` runs the optimizer with `--dry-run` under a real subprocess, asserts the JSON schema, asserts the split is deterministic for the same `--seed`, and asserts the optimizer does NOT invoke any CLI under an empty `PATH`.
- `TestAggregator` and `TestViewerStaticMode` build a fixture iteration directory and round-trip the aggregator + static viewer end-to-end.

### 4. Registered the three scripts in both installers

- `scripts/installer.sh` (line ~1424): added a `safe_copy` block per script with the same shape as the existing `generate_report.py` and `devai_mcp_benchmark.py` blocks.
- `scripts/installer.ps1` (line ~1735): added the matching `Safe-Copy` block per script in lockstep, using `Join-Path $RepoRoot "scripts\<name>.py"` and `Join-Path $scriptsDest "<name>.py"`.
- Both blocks share the same comment header explaining why these are repo-level scripts that need explicit registration (vs the per-skill bundled scripts under `catalog/skills/.../scripts/` which are auto-distributed by the recursive copy).

### 5. Registry and gitignore updates

- `data/SKILL_INDEX.md`: 1 new row, total 191 -> 192.
- `data/skills.json`: 1 new entry; `statistics.total_skills` 193 -> 194; `statistics.categories.workflow` 18 -> 19.
- `data/marketplace.json`: workflow `skill_count` 19 -> 20; description updated to mention "skill evaluation".
- `.gitignore`: new `*-workspace/` entry to ignore user-generated eval workspaces.

## Troubleshooting

The first run of `test_eval_loop.py::TestEvalLoopCLIAdapter` failed with:

> AssertionError: optimize_skill_description.py `if cli == "codex":` branch must not invoke opencode CLI

The regex `(?:[ \t]+.*\n)+` was too greedy and consumed lines from subsequent branches because every subsequent branch is also indented. Fixed by replacing the regex-based body extraction with an indent-anchored line walk: locate the `if cli == "X":` header, record its indent depth, then walk forward collecting lines until hitting a non-blank line whose indent is less than or equal to the header indent. This isolates each branch's body cleanly.

Re-ran: 14/14 green.

## Verification

- `python -m py_compile scripts/aggregate_benchmark.py scripts/skill_eval_viewer.py scripts/optimize_skill_description.py` - clean.
- `python -m pytest catalog/hooks/tests/` - 332 passed, 0 failures (+14 new from this phase).
- `python -m pytest catalog/hooks/tests/test_eval_loop.py -v` - 14/14 green.
- `python scripts/validate_skills.py --bundles-only` - 198 skills scanned, 0 errors, 4 pre-existing warnings (carried from WN-001).
- `python scripts/validate_skills.py --path catalog/skills/workflow/skill-eval-loop` - PASS, 0 errors, 5 warnings (optional fields only).
- `python -c "json.load(...)"` - all 5 catalog JSONs parse.
- `bash -n scripts/installer.sh` - clean.
- PowerShell parser-check (`[System.Management.Automation.Language.Parser]::ParseFile`) on `scripts/installer.ps1` - clean.
- ShellCheck (`--severity=warning`) on `scripts/installer.sh` and `install.sh` - clean.

## Outcomes

- 1 new skill (`skill-eval-loop`) registered across all three `data/` files.
- 4 new reference files + 3 sub-agent prompt files bundled under the skill folder (auto-distributed by the existing recursive-copy primitives).
- 3 new repo-level scripts registered in BOTH installers in lockstep.
- 1 new pytest module with 14 tests, all green; cumulative `catalog/hooks/tests/` count now 332 (was 318 at Phase 4 close).
- Quality gates clean: 0 lint errors, 0 test failures, 0 catalog validation errors, both installers parse.

## Known gaps recorded

- DF-006 (Phase 5 cross-OS installer dry-run deferred -- extends DF-003 / DF-005). Real `bash scripts/installer.sh` execution on a real macOS / Linux host is the cumulative deferred item across all 5 phases; recommended fix is a CI matrix step before the v1.1.5 -> v1.2.0 version bump in Phase 7.
- MT-001 (the optimizer's `run_iteration()` lacks a stub-CLI-on-PATH integration test analogous to the v1.1.3 hooks). Covered indirectly via the parity test + dry-run schema test, but a direct integration test would be stronger; out of scope for v1.1.5 if Phase 7 ships first.

Cumulative known-gaps total: 9 open, 0 resolved this version.

## Next steps

- Phase 6 starts next: `brand-styling` (specialized-domains, token-pattern only -- no vendor assets) and `mcp-builder` (ai-development, FastMCP + TS SDK runbook with bundled scaffolding scripts). Both Phase 6 skills will exercise the same `safe_folder_copy` / `Safe-Folder-Copy` recursive-copy primitives this Phase 5 work confirmed clean.
- The cross-OS verification gap (DF-003 / DF-005 / DF-006) becomes more important to close before the v1.2.0 version bump in Phase 7.

## Files touched

**New** (10):

- `catalog/skills/workflow/skill-eval-loop/SKILL.md`
- `catalog/skills/workflow/skill-eval-loop/references/schemas.md`
- `catalog/skills/workflow/skill-eval-loop/references/improvement-heuristics.md`
- `catalog/skills/workflow/skill-eval-loop/references/cli-adapter.md`
- `catalog/skills/workflow/skill-eval-loop/references/description-optimizer.md`
- `catalog/skills/workflow/skill-eval-loop/agents/grader.md`
- `catalog/skills/workflow/skill-eval-loop/agents/comparator.md`
- `catalog/skills/workflow/skill-eval-loop/agents/analyzer.md`
- `scripts/aggregate_benchmark.py`
- `scripts/skill_eval_viewer.py`
- `scripts/optimize_skill_description.py`
- `catalog/hooks/tests/test_eval_loop.py`

**Modified** (8):

- `scripts/installer.sh` (3-script `safe_copy` block added)
- `scripts/installer.ps1` (matching 3-script `Safe-Copy` block added in lockstep)
- `data/SKILL_INDEX.md` (1 new row; total 191 -> 192)
- `data/skills.json` (1 new entry; statistics updated)
- `data/marketplace.json` (workflow count 19 -> 20; description updated)
- `.gitignore` (new `*-workspace/` entry)
- `CHANGELOG.md` (Phase 5 sections appended under `[Unreleased]`)
- `docs/archive/v1/v1.1/known-gaps.md` (DF-006 + MT-001 added; summary table updated; last-updated stamped 2026-05-08)
- `docs/DEVLOG.md` (this phase's entry prepended)
