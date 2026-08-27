# Session History - v3.6.0 adoption-spec-kit Phase 3: workflow-phase hook recipe (N1a)

**Date**: 2026-06-17
**Plan**: [`../../plans/adoption-spec-kit.md`](../../plans/adoption-spec-kit.md) Phase 3 (N1a, a Bucket-B `re-partial` local build)
**Branch**: `feat/spec-kit-delta-adoption`
**Outcome**: Implementation complete; quality gate GO. Built after Phase 4 (the out-of-order build was tracked as NI-v36-1, now resolved). No release work this phase; only Phase 5 remains.

## Goal

Give Nexus-Hub finer-grained workflow-phase automation guidance and a concrete example hook *on its own existing hook surface* (comparison candidate N1a), without inventing new harness event types and without importing Spec Kit's per-command `before_/after_` lifecycle-hook registry (which presupposes the declined N1b third-party extension runtime). Honestly document the pattern; ship at most one minimal example hook plus a pytest.

## Pre-implementation review (plan vs codebase)

- **The "4-event model" is a simplification.** The plan, the comparison (Section 4 / 6.2), and the known-gaps NI-v36-1 all describe "four supported events (SessionStart / PreToolUse / PostToolUse / Stop)". The live `catalog/hooks/settings.json` template actually registers SEVEN events (it also uses `UserPromptSubmit`, `PreCompact`, `SessionEnd`), and the Claude Code harness defines more still. Resolution: those four ARE the events relevant to a workflow *phase* boundary (the other three are session-lifecycle), so the recipe is framed honestly on the four without claiming they are the only events the harness defines. The pre-existing AGENTS.md line 331 ("Supported events: ...") was left untouched -- correcting it is out of Phase 3 scope and conflicts with the maintainer's documented 4-event framing; the new prose simply does not repeat the false exhaustive claim.
- **Recipe home.** There is no dedicated hooks skill/style-guide; the canonical hooks-authoring guidance is AGENTS.md "Adding or Modifying a Hook". Because AGENTS.md is `@`-imported into CLAUDE.md (always loaded), the full recipe went into `guides/CLAUDE_CODE_SETTINGS_REFERENCE.md` (the deep hooks reference, not always loaded) with a concise pointer in AGENTS.md.
- **Hook conventions.** Modeled the example hook on `old-version-docs-guard.sh` (advisory-by-default, stdin `jq` extraction with a silent no-op when jq is absent, Windows-path normalization, `NEXUS_DISABLED_HOOKS` / `NEXUS_HOOK_PROFILE` runtime controls). `.sh`-only is the norm for settings.json-registered hooks (no `.ps1` sibling required; the platform-parity test governs `base-*.md`, not hooks). CI runs `pytest catalog/hooks/tests/`, so the new test belongs there.

## What shipped

### N1a - the recipe (sub-task 3.1)

- **AGENTS.md** "Adding or Modifying a Hook": a concise "Workflow-phase automation (N1a)" paragraph -- key a `PreToolUse` / `PostToolUse` matcher on the tool call that marks a `/plan`/`/implement`/`/spec` phase boundary and inspect the tool input; use `SessionStart` / `Stop` for session-level setup/teardown; no new event types; no `.specify/extensions.yml`-style registry -- pointing to the full recipe.
- **`guides/CLAUDE_CODE_SETTINGS_REFERENCE.md`** Hook Configuration: a full "Workflow-phase automation recipe" with a Spec-Kit-intent-to-Nexus-Hub-equivalent table (`before_/after_plan` -> PreToolUse/PostToolUse on Write/Edit gated on `tool_input.file_path`; `after_tasks`/`after_specify` -> PostToolUse on Write; `after_implement` -> PostToolUse on Bash gated on `git commit` in `tool_input.command`; session setup/teardown -> SessionStart/Stop), the four authoring rules, the registration block, and the Section-9 scope-creep rationale.

### N1a - the example hook (sub-task 3.2)

- **`catalog/hooks/workflow-phase-notice.sh`** (new): a `PreToolUse`/`PostToolUse`-shaped advisory hook that classifies a Write/Edit `tool_input.file_path` as a plan (`docs/**/plans/*.md`) / spec (`spec.md`) / tasks (`tasks.md`) / release (`CHANGELOG.md`) artifact and emits a cyan stderr marker; silent for anything else. Always exits 0 (advisory; never blocks a phase). jq-based extraction, Windows-path normalization, `NEXUS_DISABLED_HOOKS` + `NEXUS_HOOK_PROFILE=minimal` controls.
- **`catalog/hooks/settings.json`**: registered the hook in the default `PostToolUse` chain with a `Write|Edit` matcher -- per the maintainer's explicit "activate for all installs" decision (settings.json is an AGENTS.md ask-first area; the alternative was an opt-in/unregistered example like the `*-diff-review.sh` hooks).
- **`catalog/hooks/tests/test_workflow_phase_notice.py`** (new, 9 cases): the four phase classifications, silence on non-workflow source, silence on a bare `plan.md` outside a `plans/` dir, Windows-separator normalization, and the two env-control short-circuits -- following the `test_old_version_docs_guard.py` jq/bash skip-guard pattern.

### BG-v36-1 - a pre-existing Phase 2 defect, fixed

Running the full `catalog/hooks/tests/` suite surfaced `test_installer_smoke.py::test_installers_copy_every_scripts_dir_py_file` FAILING at HEAD: Phase 2 added `scripts/check_base_template_parity.py` as a repo-internal guard (correctly not copied by the installers) but never added it to the test's `DEV_ONLY_SCRIPTS` allowlist, which requires every `scripts/*.py` to be either distributed by both installers or marked dev-only. Fixed via the documented mechanism -- added `check_base_template_parity.py` to `DEV_ONLY_SCRIPTS` with a one-line reason, distinguishing it from the distributed `check_version_sync.py`. Recorded as BG-v36-1 (resolved) in the known-gaps tracker.

All added content is ASCII-only; per the Reverse-Engineering Attribution Rule no upstream repo/product is named in any shipped artifact.

## Key decisions

- **Recipe framed on four phase-relevant events, no false exhaustive claim.** Honors the plan's "4-event model" intent and the "do not invent new event types" rule while staying factually accurate about the harness's actual (larger) event surface.
- **Split placement (lean AGENTS.md pointer + full recipe in the settings guide).** Keeps the always-loaded AGENTS.md cost low while putting the detailed recipe where hook authors look.
- **Example hook activated for all installs (maintainer's call).** The plan left registration optional (documentation-only was acceptable) and settings.json is an ask-first area, so the choice was surfaced; the maintainer chose to register it. It is advisory-only and disablable, so the blast radius is a single stderr line on workflow-artifact writes.
- **Modeled on `old-version-docs-guard.sh`.** Reuses the established advisory-hook conventions (jq stdin, Windows normalization, runtime controls, exit-0 default) so the example is idiomatic, not novel machinery.
- **Fixed BG-v36-1 in scope.** Phase 3's stability gate requires `make test` to pass; a pre-existing failing test blocked that gate and Phase 5's full-green run. The fix is the test's own documented mechanism, minimal and unambiguous.

## Verification (quality gate: GO)

`make` is not on PATH on this Windows host (WN-v33-1), so the gates were run via the documented direct equivalents:

- **`make validate` (direct chain)**: GREEN. JSON catalog integrity (256 skills / 15 bundles / 17 workflows), orphan-bundle audit PASS (0 errors, 1 pre-existing WN-v33-2 warning), unicode-safety 0 errors (0 in the changed files), no-personal-paths exit 0, supply-chain-iocs exit 0, workflow-security exit 0, version-sync surfaces match 3.5.0, base-template parity guard exit 0, compression accuracy-regression gate PASS (CCR 100.0%).
- **`make test`**: `catalog/hooks/tests/` 441 passed + 14 jq-skips (the new `test_workflow_phase_notice.py` is 9/9 under a temporary jq shim; without jq its seven marker cases skip cleanly, like `old-version-docs-guard`); repo-level `pytest tests/` 540 passed / 0 failed (no space-path failures on this space-free checkout). The 7 transient `git_guardrails`/`compress_output` "failures" seen mid-run were an artifact of an over-narrow local jq shim (it returned `file_path` for every jq filter), not a regression -- they pass under real jq (CI) and skip without jq.
- **`make lint`**: ShellCheck is not on PATH, so the new hook was verified with `bash -n` (clean). No installer changed.
- **settings.json**: re-validated as JSON; the new `PostToolUse` `Write|Edit` block referencing `workflow-phase-notice.sh` is present (3 PostToolUse blocks total).
- **Diff isolation**: changes are exactly `catalog/hooks/workflow-phase-notice.sh`, `catalog/hooks/tests/test_workflow_phase_notice.py`, `catalog/hooks/settings.json`, `catalog/hooks/tests/test_installer_smoke.py` (the BG-v36-1 allowlist fix), `AGENTS.md`, `guides/CLAUDE_CODE_SETTINGS_REFERENCE.md`, plus the plan checklist, DEVLOG, known-gaps, and this session history. No `data/` / registry edit, no installer edit.

## Files changed

- `catalog/hooks/workflow-phase-notice.sh` (N1a, new advisory example hook)
- `catalog/hooks/tests/test_workflow_phase_notice.py` (new, 9 cases)
- `catalog/hooks/settings.json` (registered the hook in the PostToolUse `Write|Edit` chain)
- `catalog/hooks/tests/test_installer_smoke.py` (BG-v36-1: added `check_base_template_parity.py` to `DEV_ONLY_SCRIPTS`)
- `AGENTS.md` ("Adding or Modifying a Hook": concise Workflow-phase automation pointer)
- `guides/CLAUDE_CODE_SETTINGS_REFERENCE.md` (full Workflow-phase automation recipe)
- `docs/v3/v3.6/plans/adoption-spec-kit.md` (Phase 3 exit checklist checked off; Phase 4 note updated)
- `docs/v3/v3.6/known-gaps.md` (NI-v36-1 resolved; BG-v36-1 added + resolved; WN-v33-1 re-confirmed for Phase 3; summary updated)
- `docs/DEVLOG.md` (Phase 3 entry)
- `docs/archive/v3/v3.6/development/history/2026-06-17_adoption-spec-kit-phase-3-workflow-phase-hook-recipe.md` (this file)

## Next

Phase 5: decline-durability and release readiness -- the only remaining phase. Add reverse-engineering-matrix rows for the two declines (N5 authentication framework, N1b third-party extension install), log the two deferred items (N4 self-upgrade CLI, N2b portable workflow engine) in the known-gaps tracker, add the CHANGELOG `[Unreleased]` block enumerating all five adoptions (N2a, N3b, N3a, N1a, N6) plus the declines note, and run the full `make validate && make lint && make test` gate before `/update release`.
