# Session History - v2.3.0 (adoption-superpowers) Phase 4: Eval-harness trigger techniques

**Date**: 2026-05-30
**Plan**: [docs/archives/v2/v2.3/plans/adoption-superpowers.md](../../plans/adoption-superpowers.md)
**Phase**: 4 of 6 - Eval-harness trigger techniques (`re-full`)
**Sub-tasks**: T014 (premature-action detection), T015 (multi-turn + cheap-model modes + schema extension), T016 (trigger-testing reference), T017 (pytest cases + stabilization)
**Outcome**: The three trigger-testing techniques superpowers' harness had that Nexus-Hub's `skill-eval-loop` lacked are now in the harness, reusing the existing CLI dispatcher with zero new dependencies / outbound calls / credentials and no `data/` edits. `test_eval_loop.py` 14 -> 37 passed; orphan-bundle + unicode + personal-path validators green; existing optimizer behavior and the CLI-parity invariant preserved. Ready to advance to Phase 5.

---

## Goal

Add the three trigger-testing techniques the comparison's Section 8 identified as superpowers' additive value over Nexus-Hub's (otherwise more sophisticated) `skill-eval-loop`: premature-action detection (the agent acted before loading the skill), multi-turn conversation triggering (the skill fires on a cold prompt but not deep in a workflow), and cheap-model fragility (the description triggers on a strong model but not a cheaper one). All three are local code reusing the harness's existing claude/gemini/codex/opencode dispatcher - `re-full` per the MCP Registry Policy, no new runtime dependency and no new data-flow.

## Steps taken

1. **Pre-implementation review**: read `scripts/optimize_skill_description.py`, `scripts/aggregate_benchmark.py`, the existing `catalog/hooks/tests/test_eval_loop.py`, `skill-eval-loop/SKILL.md` + its `references/{schemas,cli-adapter,description-optimizer}.md` + `agents/grader.md`, the comparison Section 8 (provenance), and the Makefile `test`/`validate` targets. Confirmed Phase 4 is not the final phase (4 of 6), so no release-readiness workflow runs. Ran the existing suite as a baseline: 14 passed.

2. **T014 - premature-action detection** (`scripts/optimize_skill_description.py`): added `extract_tool_invocations()` (walks a stream-json transcript, returns ordered tool-use names, tolerant of NDJSON or a single JSON array) and `detect_premature_action()` (first `Skill` clears the run; any non-`Skill`/non-`TodoWrite` tool before it sets the flag, including the never-loaded case). Surfaced the flag in the benchmark output: `scripts/aggregate_benchmark.py` passes `premature_action` through from the with_skill `grading.json` into `benchmark.json` (eval-level + with_skill condition; False for the without_skill baseline).

3. **T015 - multi-turn + cheap-model** (same script): extracted `build_cli_command()` out of `invoke_cli()` so both the `--model` threading and the no-cross-CLI-bleed parity invariant are testable without a subprocess; added a `--model <name>` flag threaded through `estimate_trigger_rate` / `run_iteration` / `_passes` / `render_dry_run` (per-eval `model` overrides it); added `is_multi_turn()`, `first_trigger_turn()`, `multi_turn_passes()` (pure logic), and `evaluate_multi_turn()` (replays the `turns` list and asserts the first trigger lands on `trigger_turn`). Extended the `evals.json` schema doc with optional `turns` / `trigger_turn` / `model`; added `premature_action` to the grading/benchmark schema and to `agents/grader.md`.

4. **T016 - reference + link**: created `catalog/skills/workflow/skill-eval-loop/references/trigger-testing.md` (what each technique catches, how to author an eval that exercises it, how to read the output fields, when to use each, comparison Section 8 provenance) and linked it from `skill-eval-loop/SKILL.md` via a new "Trigger-testing techniques" body section plus a Reference-files entry (orphan-bundle rule).

5. **T017 - tests + stabilization**: added 23 pytest cases to `catalog/hooks/tests/test_eval_loop.py`, ran the suite (37 passed), ran the validators individually (make unavailable on the Windows host), smoke-tested the optimizer dry-run with `--model haiku`, updated the plan checkboxes + Phase 4 exit checklist, and ran the post-phase documentation sequence.

## Troubleshooting

- **Surfacing point for `premature_action`**: T014 says "surface in the grading/benchmark output", but the optimizer does not write `grading.json` (a sub-agent does) and its own trigger-rate loop discards everything but the trigger boolean. Resolved by keeping the canonical detection logic in `optimize_skill_description.py` (the T014-named file) and having `aggregate_benchmark.py` surface the field as a pass-through from the with_skill `grading.json`, with `agents/grader.md` + `schemas.md` documenting how the grader records it. No cross-script import (the aggregator reads a plain field).

- **Preserving the CLI-parity test through the refactor**: moving the `if cli == "X":` branches into `build_cli_command()` had to keep the parity test (`TestEvalLoopCLIAdapter`, which scans the script source for per-CLI branches and the `assert cli in {...}` guard) passing. Kept the branches and the assert in `build_cli_command`, with `invoke_cli` now a thin wrapper; the test stays green.

- **PowerShell BOM false alarm in a smoke test**: an initial dry-run smoke wrote the fixture `evals.json` via `Out-File -Encoding utf8`, which on Windows PowerShell 5.1 prepends a UTF-8 BOM; the optimizer's `read_text("utf-8")` correctly rejected the BOM, so the run errored. Re-ran with `[System.IO.File]::WriteAllText` (no BOM): dry-run exit 0, `model=haiku`, split + selection metric unchanged. Not an optimizer bug - the pytest fixtures (written by Python, no BOM) had already passed.

## Assumptions

- Multi-turn entries are consumed by `evaluate_multi_turn()`, not the optimizer's description-optimization loop (which is single-turn by contract); the `turns` / `trigger_turn` / `model` fields are opt-in, so existing single-turn / default-model eval sets are unaffected.
- The subprocess-driving wrappers (`evaluate_multi_turn`, `invoke_cli` with a model) are intentionally not unit-tested because they spawn a real CLI - consistent with the existing harness pattern (the optimizer's `invoke_cli` was never unit-tested; parity is enforced by source inspection). The pure logic they delegate to is fully covered.
- `make test`/`make validate` were invoked as direct `python`/`pytest` calls because `make` is unavailable on this Windows host (same as prior phases).

## Testing results

- `catalog/hooks/tests/test_eval_loop.py`: **37 passed** (was 14; +23 new). New cases: premature-action detection (stream parsing, ordering, single-array fallback, allowlist, never-loaded, empty), multi-turn pure-logic (`is_multi_turn` / `first_trigger_turn` / `multi_turn_passes`), cheap-model `--model` argv threading across all four CLIs (+ omitted-by-default), dry-run model surfacing, benchmark `premature_action` pass-through.
- Existing optimizer behavior preserved: dry-run exit 0, train/test split deterministic, `test_trigger_rate` selection metric unchanged; CLI-parity test green after the `build_cli_command` extraction.
- Validators: orphan-bundle audit **PASS 0/0** across 237 skills (`trigger-testing.md` linked); `validate_unicode_safety.py --strict` 0 findings on the six changed files; `validate_no_personal_paths.py` exit 0. No `data/` edits, so no `make build-catalog` reconciliation.
- `py_compile` on both changed scripts: OK.
- **Not regressions**: 73 failures elsewhere in `catalog/hooks/tests/` are pre-existing bash-hook-on-Windows environmental failures in five unrelated test files (test_diff_review_hooks 44, test_session_digest 11, test_learning_capture 10, test_old_version_docs_guard 6, test_installer_smoke 2) - none imports the Python eval scripts; same cross-OS class as DF-v23-6, green on Linux CI. CI runs `pytest catalog/hooks/tests/` (ci.yml line 94), so the new cases are gated with no CI edit.

## Next steps

- Phase 5: flaky-test tooling cluster - `find-polluter.{sh,ps1}` bisector + the `waitFor` helper bundled under `flaky-test-detector` (the `condition-based-waiting.md` reference from Phase 3 T011 forward-references the helper).
- DF-v23-8 (new this phase): run the three trigger-testing modes live against a real model CLI in the Phase 6 final validation, paired with the DF-v23-7 live `skill-eval-loop` run. Both are low-priority verification-method deferrals, not defects.
