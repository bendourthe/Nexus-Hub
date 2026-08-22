# Session History - v3.6.0 adoption-spec-kit Phase 2: base-*.md parity-governance check (N3a)

**Date**: 2026-06-16
**Plan**: [`../../plans/adoption-spec-kit.md`](../../plans/adoption-spec-kit.md) Phase 2 (N3a, the highest-value local re-build / Bucket B)
**Branch**: `feat/spec-kit-delta-adoption`
**Outcome**: Implementation complete; quality gate GO. Phase 2 of 5, so Phase 3 (the workflow-phase hook recipe, N1a) follows. No release work this phase.

## Goal

Ship a repo-internal validator that enforces the AGENTS.md "edit all five `base-*.md` in lockstep ... changes must be platform-agnostic" rule structurally, modeled on the existing `check_version_sync.py` guard. The crux (flagged in the comparison's Section 9 risk note) is a structural (not raw-byte) comparison: a naive whole-file diff would false-positive on every legitimate per-platform line, so the guard had to compare the shared skeleton while tolerating platform names and install paths. No new outbound call, dependency, credential, or distributed artifact (it is a repo-internal guard like `check_version_sync.py`, so no `.ps1` sibling and no installer copy step).

## Parity contract (sub-task 2.1)

Reading the five lockstep templates revealed they are NOT structurally identical today, which immediately ruled out the plan's suggested "identical heading sets / identical ordered behavioral rules" contract: `base-claude.md` is the "full" template (separate `Communication Style` + `Critical Rules` sections, plus `Agent Registry` / `Spending Controls` / `Environment Variables` / `MCP Integration`), while `base-codex/cursor/gemini/opencode.md` collapse those into one `Working Conventions` section and omit the optional blocks; the AI-attribution bullet wording differs between codex/gemini and cursor/opencode; and `base-gemini.md` omits `Context References` entirely. Per the plan's "base the contract on what the five files actually share today - do not invent requirements", the enforced contract is:

- **MUST stay identical** -- (1) the required shared section headings present in all five (`{{PROJECT_NAME}}`, Tech Stack, Project Layout, Key Commands, Non-Obvious Tooling, `{{PRIMARY_LANGUAGE}}` Conventions, Branching, Output Minimization, MCP Registry Policy, Skill Discovery); (2) the 15 placeholder tokens present in all five (`{{PROJECT_NAME}}` ... `{{SKILL_INDEX}}`, excluding the claude-only `{{AGENT_REGISTRY}}` / `{{SPENDING_CONTROLS}}` / `{{ENV_VARS_REFERENCE}}` / `{{MCP_STATUS}}`); (3) the byte-identical bodies of the four invariant sections (Tech Stack, Key Commands, Branching, MCP Registry Policy).
- **ALLOWED to differ** -- platform names and per-platform install paths (`.claude/skills/`, `.codex/skills/`, `skills/`), the claude-only optional sections and the Communication-Style+Critical-Rules vs Working-Conventions split, `Context References` (absent in gemini), the per-platform behavioral-rule bullet wording, and Output Minimization's claude-only 5th bullet.

The invariant-block check is the core lockstep enforcer and is intentionally **relative** (compares the five files to each other, not to hardcoded expected text): an in-lockstep edit applied to all five keeps the bodies equal and passes; an edit applied to a subset diverges and fails -- so it needs no maintenance when the shared content legitimately changes in lockstep. The heading/placeholder presence checks are hardcoded (a structural floor), matching `check_version_sync.py`'s philosophy so deletion-from-all-five is still caught.

## What shipped

### N3a - the parity guard (sub-task 2.2)

- **`scripts/check_base_template_parity.py`** (new, ~330 lines incl. the contract docstring): stdlib-only, modeled on `check_version_sync.py` (same `--root` / `--json` / `--verbose` CLI, same exit-code contract: 0 = parity holds, 1 = findings, 2 = IO error). Scoped to exactly the five lockstep files named in AGENTS.md -- it deliberately ignores the 10 later platform-specific `base-*.md` files (aider, windsurf, kimi, qwen, openclaw, antigravity-*, gemini-cli, google-shared) that are outside the lockstep set. Markdown parsing is code-fence-aware (a `#` inside a ```` ```bash ```` block is never treated as a heading boundary); section bodies are normalized for CRLF and trailing whitespace before comparison. A missing lockstep file is informational, never a finding (fewer than two present -> clean no-op exit 0), so the guard works on partial trees and fixtures.
- **`Makefile`**: added the guard to the `validate` target, right after the `check_version_sync.py` step.
- **`.github/workflows/ci.yml`**: added a "Validate base-*.md lockstep parity" step after the version-sync step. This was a real gap caught by the post-phase CI check: CI's `validate` job invokes each validator EXPLICITLY (it does not run `make validate`), so wiring into the Makefile alone would not have run the guard in CI -- exactly why `check_version_sync.py` is listed explicitly there. The test module lives under `tests/validators/`, which CI already runs (`pytest tests/validators -v`), so the tests needed no CI edit.
- **`AGENTS.md`**: appended one sentence to installer-checklist item 4 (the lockstep rule) documenting that the constraint is now machine-enforced by the guard via `make validate` and CI, that it tolerates intentional per-platform lines, and that it is a repo-internal guard (no `.ps1` sibling, no installer copy step).

### Tests (sub-task 2.3)

- **`tests/validators/test_check_base_template_parity.py`** (new, 9 cases, using the existing `runner` subprocess fixture from `tests/validators/conftest.py`): the must-pass baseline against the real repo; a removed `## Branching` heading -> required-heading finding; a dropped `{{SKILL_INDEX}}` -> placeholder finding; a reworded MCP Registry Policy "Hard no" line -> block-divergence finding (the core lockstep case: a policy edit applied to four of five must fail); an allowed per-platform install-path change (`.cursor/skills/` -> `.cursor/agents/skills/`) that still PASSES (no false positive -- the contract-tolerance proof the plan's Section 9 risk note demanded); a one-file partial tree and an empty tree both clean no-ops; and the `--json` shape on both the in-parity and findings paths. The fixture tree is seeded by COPYING the real templates then mutating one thing, so the tests stay valid as the templates legitimately evolve.

All added content is ASCII-only (hyphens, straight quotes); the guard introduces no external repo/product attribution.

## Key decisions

- **Reality-based contract, not the plan's suggested one.** The plan offered "identical heading sets / identical ordered behavioral rules" as an example, but the five files do not share those today. Enforcing them would have made the guard fire on day one and get disabled for crying wolf. The contract was rebuilt from the genuine intersection, with the behavioral-rule wording and the claude-only sections explicitly classified as allowed-to-differ.
- **Invariant-block check is relative (file-to-file), presence checks are hardcoded.** The highest-value check (byte-identity of Tech Stack / Key Commands / Branching / MCP Registry Policy bodies across the five) compares the files to each other, so it is maintenance-free under lockstep edits. Only the structural-floor presence lists are hardcoded, matching the `check_version_sync.py` precedent.
- **Scoped to the five, not all 15 `base-*.md`.** A naive `base-*.md` glob would have pulled in the 10 later platform-specific templates (aider, windsurf, etc.), which are NOT part of the lockstep set. The guard hardcodes the five lockstep filenames in canonical order (the first present file is the parity reference).
- **Added to CI explicitly, not just `make validate`.** CI bypasses `make` and lists each validator by hand, so the guard was added to `ci.yml` alongside version-sync; otherwise it would have enforced nothing on PRs.
- **Repo-internal, so no installer/`.ps1`/distribution surface.** Per the NI-v24-1 convention (a Python validator needs no `.ps1` sibling and is not a distributed artifact), no installer copy step was added -- matching `check_version_sync.py` and the other top-level validators.

## Verification (quality gate: GO)

`make` is not on PATH on this Windows host (WN-v33-1), so the gates were run via the documented direct equivalents:

- **The new parity guard**: exit 0 on the five in-sync templates (`--verbose` confirms 5 of 5 present); `--json` reports `in_parity: true`. The 9 pytest cases pass (`pytest tests/validators/test_check_base_template_parity.py` -> 9 passed), proving the guard FAILS on a desynced fixture (missing heading, dropped placeholder, diverged MCP-policy block) and does NOT false-positive on an allowed per-platform line.
- **`make validate` (direct chain)**: GREEN. JSON catalog integrity (256 skills / bundles / workflows / templates load), orphan-bundle audit PASS, no-personal-paths exit 0, unicode-safety 0 errors (the 1051 repo-wide warnings are all pre-existing em-dashes; the new files added none), workflow-security exit 0 (confirms the `ci.yml` edit is clean), version-sync six surfaces match 3.5.0, and the new parity guard exit 0.
- **`make test` (repo-level `pytest tests/`)**: 494 passed, 4 failed. The 4 failures (`tests/installer/test_branch_flag.py` x3, `tests/validators/test_session_query_extract.py::test_discover_obsidian_vault_marker` x1) are PRE-EXISTING and unrelated to this phase: all invoke a bash `.sh` script via `bash.EXE`, which returns exit 127 because the system bash cannot resolve a script path containing spaces ("OneDrive - Supira"); the referenced scripts exist on disk and the tests pass on the CI ubuntu runner. Recorded as WN-v36-1. Phase 2's own change is pure Python and touches none of those tests.
- **`make lint`**: no shell script was added or changed this phase (the guard is Python, no `.ps1` sibling), so ShellCheck is unaffected.
- **Diff isolation**: confirmed `git status` shows exactly the intended surfaces -- `scripts/check_base_template_parity.py`, `tests/validators/test_check_base_template_parity.py`, `Makefile`, `.github/workflows/ci.yml`, `AGENTS.md`, plus the plan checklist, this session history, and `docs/v3/v3.6/known-gaps.md`. No scope creep, no registry edit, no installer edit.

## Files changed

- `scripts/check_base_template_parity.py` (N3a, new repo-internal guard)
- `tests/validators/test_check_base_template_parity.py` (new, 9 cases)
- `Makefile` (validate target: +1 guard invocation)
- `.github/workflows/ci.yml` (validate job: +1 parity-guard step)
- `AGENTS.md` (installer-checklist item 4: +1 enforcement sentence)
- `docs/v3/v3.6/plans/adoption-spec-kit.md` (Phase 2 exit checklist checked off)
- `docs/v3/v3.6/known-gaps.md` (new; WN-v33-1 carried forward + new WN-v36-1 + WN-v33-2)
- `docs/archive/v3/v3.6/development/history/2026-06-16_adoption-spec-kit-phase-2-base-template-parity-check.md` (this file)

## Next

Phase 3: the workflow-phase hook recipe (N1a) -- document how to approximate spec-kit's per-command `before_/after_` lifecycle hooks using ONLY Nexus-Hub's four supported events (SessionStart / PreToolUse / PostToolUse / Stop), honestly documenting the 4-event constraint and adding at most one minimal, opt-in example hook (registered in `catalog/hooks/settings.json`, an ask-first area) with a pytest. The CHANGELOG `[Unreleased]` block enumerating all five v3.6.0 adoptions and the reverse-engineering-matrix rows for the N5 + N1b declines remain deferred to Phase 5 per the plan.
