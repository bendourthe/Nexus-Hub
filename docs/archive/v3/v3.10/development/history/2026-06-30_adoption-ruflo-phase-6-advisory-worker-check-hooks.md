# Session History - v3.10.0 adoption-ruflo Phase 6: advisory worker-check hooks + consolidation

**Date**: 2026-06-30
**Plan**: [`../../plans/adoption-ruflo.md`](../../plans/adoption-ruflo.md) Phase 6 (A10: advisory worker-check hooks + the six runtime-drop records, registry decision, CHANGELOG, known-gaps; re-partial, P3 + consolidation)
**Branch**: `develop`
**Outcome**: Complete. All Phase 6 exit-checklist items satisfied; quality gate GO. The final phase (6 of 6), so `/implement` routes to the release-readiness workflow.

## Goal

Adopt a small, selected set of the source's background-worker check ideas as advisory, event-driven hooks (never a daemon), record the six runtime drops in the reverse-engineering matrix, make the registry-edit decision, and finalize the catalog counts, CHANGELOG, and known-gaps. Re-partial reverse-engineer build over owned artifacts: zero new outbound call, dependency, or credential. The named care is keeping the hooks advisory and event-driven rather than importing a daemon scheduler.

## What shipped

- **`catalog/hooks/test-gap-notice.sh`** (new): advisory `PostToolUse` `Write|Edit` hook that reminds when a (non-test) source file in a strong-test-convention language is edited and no companion test is discoverable nearby.
- **`catalog/hooks/dependency-staleness-notice.sh`** (new): advisory `PostToolUse` `Write|Edit` hook that reminds to audit for stale / vulnerable dependencies when a declared-dependency manifest changes, with the matching per-ecosystem audit command.
- **`catalog/hooks/settings.json`** (edited): both hooks registered in the `PostToolUse` `Write|Edit` chain beside `workflow-phase-notice.sh`.
- **`catalog/hooks/tests/test_test_gap_notice.py`** (new, 11 cases) and **`catalog/hooks/tests/test_dependency_staleness_notice.py`** (new, 16 cases): follow the `test_workflow_phase_notice.py` pattern (jq-gated cases skip without jq).
- **`docs/policy/mcp-reverse-engineering-matrix.md`** (edited): new dated section recording the six runtime drops as `drop-outright`.
- **`AGENTS.md`, `README.md`, `.claude-plugin/plugin.json`, `data/marketplace.json`** (edited): current-state count prose corrected to 259 skills / 25 hooks.
- **`CHANGELOG.md`** (edited): `## [Unreleased]` entry for the whole v3.10.0 cycle.
- **`docs/v3/v3.10/known-gaps.md`** (edited): status advanced to all-phases-complete; new DF-v310-ruflo-A10-rest for the not-adopted worker-check ideas.
- **`docs/v3/v3.10/plans/adoption-ruflo.md`** (edited): Phase 6 exit checklist checked off.
- **`docs/DEVLOG.md`** (edited): Phase 6 entry.

## The two hooks (6.1)

Both are modeled exactly on `catalog/hooks/workflow-phase-notice.sh`: `#!/usr/bin/env bash` + `set -euo pipefail`, `trap 'exit 0' ERR`, the `NEXUS_DISABLED_HOOKS` / `NEXUS_HOOK_PROFILE=minimal` runtime controls, jq-gated file-path extraction with a silent no-op when jq is absent, Windows-path normalization, and an unconditional `exit 0`.

- **`test-gap-notice.sh`**: triggers only for source extensions with a strong file-based test convention (py / js / jsx / ts / tsx / go / rb / java / cs / php). Inline-test languages (Rust `#[cfg(test)]`, C/C++) are deliberately excluded to keep the advisory low-noise. Skips files that are themselves tests, common entrypoint/aggregator files (`__init__.py`, `conftest.py`, `setup.py`, `index.*`), and files inside test/build/vendor directories. Looks for a companion test in a bounded set of nearby directories (same dir + adjacent `tests`/`test`/`__tests__`/`spec` + their parents) by matching any nearby file whose name contains the source stem AND matches a test-name convention. Emits one advisory line to stderr only when none is found.
- **`dependency-staleness-notice.sh`**: triggers for declared-dependency manifests (package.json, requirements*.txt, pyproject.toml, Pipfile, setup.cfg, go.mod, Cargo.toml, Gemfile, composer.json, pom.xml, build.gradle[.kts], *.csproj) and NOT generated lockfiles, skipping manifests inside vendor/build dirs, and emits the matching per-ecosystem audit command.

## Key decisions / troubleshooting

- **Event-driven, not a daemon.** The source runs a timer-driven background-worker daemon; the adopted intent ("check X when X changes") maps cleanly onto a `PostToolUse` `Write|Edit` matcher that inspects the tool input, with zero background process. No timer/scheduler is imported - this is the reverse-engineered, advisory-only equivalent.
- **Two hooks, not three.** The two highest-value, lowest-noise ideas (test-gap, dependency-staleness) were adopted. The rest of the worker catalog (periodic audit/optimize, docs-staleness, duplicate-elimination, cost) was considered and not adopted (recorded as DF-v310-ruflo-A10-rest): each lacks a clean Write/Edit trigger (it is a periodic-scan idea), is already covered by an existing skill/command (`/review` + `code-optimizer`; `/update docs` + `documentation-consistency`; `dead-code-eliminator` + `code-simplification`), or would be redundant with the hard cost controls in `ai-billing-safeguards`.
- **Low-noise by construction.** test-gap only fires on a source-file edit when NO companion test is found nearby, and only for languages with a strong file-based convention; dependency-staleness only fires on declared-manifest edits (infrequent). Both are silent for everything else.
- **No `.ps1` siblings.** The hooks run via `bash .claude/hooks/<name>.sh` (the settings.json convention for every existing hook); the scripts-parity `.ps1` rule applies to distributed `scripts/`, not `catalog/hooks/`, and the precedent `workflow-phase-notice.sh` has no `.ps1` sibling.
- **Registry-edit decision: none needed.** The two new skills were already registered in Phases 1-2 (259 skills across the three data registries). The Phase 3 / Phase 5 refinements changed no `summary_l0` / `overview_l1`, so no further `data/` registry edit is required (the v3.8.0 / v3.9.0 in-scope-refinement precedent). Only the current-state count PROSE in AGENTS.md / README / plugin.json / marketplace.json needed correcting (257/23 -> 259/25); the version fields and the v3.9.1 release narrative are left to `/update release`.
- **Attribution discipline in the matrix.** The six drops are described generically (no upstream product/component brand names) with the MCP Registry Policy + v3.1.0 / v3.8.0 precedents cited, matching the prior declined sections; the comparison report is cited as the report's subject.
- **A test-shim false alarm, root-caused.** A first full `catalog/hooks/tests` run (with a local jq SHIM on PATH that only implements the `.tool_input.file_path` filter) produced 4 failures in `git-guardrails` / `compress-output` - those hooks query `.tool_input.command`, which the shim returned empty for, so they no-op'd. Confirmed by stashing all changes and re-running the 4 tests on clean HEAD (they passed) and by re-running the full suite WITHOUT the shim (445 passed / 36 skipped). The failures were an artifact of the test shim, not a regression; CI has real jq.

## Verification (quality gate: GO)

`make` is not on PATH (WN-v33-1), so the gate ran via its documented Windows equivalents.

- **ShellCheck**: clean on both new hooks.
- **Hook behavior (advisory contract)**: both hooks use only `exit 0` (no blocking path), contain zero network primitives, and carry both disable mechanisms. Exercised end to end via bash with a jq shim across every marker and silent case (untested source -> marker; sibling/`__tests__` test -> silent; test file / non-source / inline-test language / entrypoint / node_modules -> silent; each manifest type -> the right ecosystem hint; lockfile / non-manifest / node_modules -> silent; Windows-path normalization).
- **pytest**: full `catalog/hooks/tests` suite 445 passed / 36 skipped (the skips are jq-gated cases that run in CI; the two new suites add 27 cases). Full `tests/` suite: **615 passed / 15 skipped / 1 pre-existing environmental failure** (`test_bootstrap.py::test_ps_standalone_extracts_and_hands_off`, the Windows `tar` extraction error exercising the untouched root `install.ps1`; identical numbers and identical failure to the Phase 4 / Phase 5 record, and Phase 6 touches no installer/bootstrap or `tests/` code, so not a regression).
- **CI validators**: JSON catalogs OK (259 skills); bundle-audit PASS; quality-heuristics 0 warnings; `validate_unicode_safety` / `validate_no_personal_paths` / `scan_supply_chain_iocs` / `validate_workflow_security` exit 0; `check_version_sync` all surfaces match (versions untouched); `check_base_template_parity` exit 0.
- **No-outbound invariant**: both hooks are stdlib bash with no network primitive; the matrix/CHANGELOG/known-gaps edits add no code.
- **Attribution grep**: across all distributed trees (`catalog/`, `data/`, `templates/`, `scripts/`), zero matches for `ruflo` / `AIDefence` / `AgentDB` / `RuVector` / `SONA` / `ReasoningBank` / `MetaHarness` / `SPARC` / `rvf` / `rvagent` / `ruv.io` / branded `arena` (the only `arena` hit is the pre-existing C "arena allocator" term in an unrelated template; `ruflo` appears only in internal `docs/`, which the attribution rule permits).
- **Norms**: all Phase 6 files ASCII-clean; the new RE-matrix link target resolves; both new hooks have no `.ps1` sibling by design (the precedent).

## Files changed

- `catalog/hooks/test-gap-notice.sh` (new)
- `catalog/hooks/dependency-staleness-notice.sh` (new)
- `catalog/hooks/settings.json` (register both hooks)
- `catalog/hooks/tests/test_test_gap_notice.py` (new)
- `catalog/hooks/tests/test_dependency_staleness_notice.py` (new)
- `docs/policy/mcp-reverse-engineering-matrix.md` (six runtime drops)
- `AGENTS.md`, `README.md`, `.claude-plugin/plugin.json`, `data/marketplace.json` (count prose 259 / 25)
- `CHANGELOG.md` (Unreleased entry)
- `docs/v3/v3.10/known-gaps.md` (Phase 6 status + DF-v310-ruflo-A10-rest)
- `docs/v3/v3.10/plans/adoption-ruflo.md` (Phase 6 exit checklist)
- `docs/DEVLOG.md` (Phase 6 entry)
- `docs/archive/v3/v3.10/development/history/2026-06-30_adoption-ruflo-phase-6-advisory-worker-check-hooks.md` (this file)

## Next

This is the final phase of the plan, so `/implement` routes to the release-readiness workflow. The v3.10.0 Definition of Done is met (the P0 egress skill, the P1 prompt-injection-defense skill and `nexus-hub verify` command, the P2 iterative-competition enrichment and agent-setup grade, and the P3 advisory hooks + recorded decisions are all delivered; counts 259 / 16 / 25; all validators green). Route the version bump / changelog finalization / tag / push to `/update release`; never auto-tag or auto-push (the release flow keeps its own confirmation gates).
