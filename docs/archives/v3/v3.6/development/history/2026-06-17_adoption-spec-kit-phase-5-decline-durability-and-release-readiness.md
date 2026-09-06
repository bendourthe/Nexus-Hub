# Session History - v3.6.0 adoption-spec-kit Phase 5: decline-durability and release readiness

**Date**: 2026-06-17
**Plan**: [`../../plans/adoption-spec-kit.md`](../../plans/adoption-spec-kit.md) Phase 5 (the final, close-out phase)
**Branch**: `feat/spec-kit-delta-adoption`
**Outcome**: Implementation complete; quality gate GO. Docs-only phase. v3.6.0 is implementation-complete and release-ready; the version bump / tag / push hand off to `/update release` (not run automatically).

## Goal

Make the v3.5.0 Spec Kit re-comparison's two deliberate declines durable (so a future comparison recognizes them as already-adjudicated rather than re-surfacing them as fresh candidates), log the two deferred items so the next plan can pick them up, enumerate the v3.6.0 adoptions in the CHANGELOG, and bring the release to a verifiable, documented, release-ready state.

## Pre-implementation review (plan vs codebase)

- **`docs/v3/v3.6/known-gaps.md` already existed** (created in Phase 2, updated through Phase 3), so sub-task 5.2 is an *update* (add DF rows + bump the summary), not a create. The file's table schema (ID / Category / Source phase / Plan reference / Reason / Suggested next step / Severity) was followed for the two new DF entries.
- **The reverse-engineering matrix is an internal policy doc, not a distributed artifact.** Every existing row names its upstream in the "Current source" and "Rationale" columns, so naming GitHub Spec Kit there is correct (the Attribution Rule forbids naming the source only in user-facing *distributed* artifacts -- skills, commands, MCPs). N5 / N1b are external systems, not MCPs, so the rows use `n/a (... not MCP)` MCP keys, consistent with the existing v3.4.0 `n/a (skill, not MCP)` / `n/a (integration subclasses, not MCP)` rows. The MCP-registry-size Summary table was deliberately left unchanged (these are not MCPs), matching how the v3.4.0 skill-native / re-full rows were also kept out of that count.
- **CHANGELOG header choice: `## [Unreleased]`, not `## [3.6.0]`.** `check_version_sync.py`'s CHANGELOG extractor is `^##\s*\[(\d+\.\d+\.\d+)\]`, which matches only a real semver heading -- so an `## [Unreleased]` heading is skipped and the guard still reads the first semver heading (`[3.5.0]`), keeping the version-sync surfaces in sync at 3.5.0. The promotion to `## [3.6.0]` + the atomic version bump across all surfaces is `/update release`'s job, per the v3.0.0 final-phase release routing. Verified the regex before editing.

## What shipped

### 5.1 - decline durability (the reverse-engineering matrix)

`docs/policy/mcp-reverse-engineering-matrix.md`: a new "Declined in v3.6.0 (Drop-Outright under the MCP Registry Policy)" section with two `drop-outright` rows:

- **N5 (authentication framework)**: GitHub Bearer / Azure DevOps Basic-PAT credentials for private remote catalog fetches, stored in plaintext in `~/.specify/auth.json`. Grounds: plaintext PAT storage contradicts the `catalog/rules/*/security.md` secret-handling rules; remote credentialed catalog fetch is N/A for a local-first catalog that ships in the repo and installs locally. v3.7.0+ action: reconsider only in the architecturally-absent event of a private *remote* catalog, and even then only with a secrets-manager / OS-keychain backend.
- **N1b (third-party extension install)**: unsandboxed community-catalog plugin code installed with agent privileges. Grounds: code-distribution-as-service is on the policy hard-no spectrum; the capability is already met by the skill catalog (`marketplace.json` + `bundles.json` + `nexus-skill-server` + `/skills import`) WITH a pre-install scanner (`skill-security-scan` + `nexus-skill-scanner`) the upstream lacks (and the v3.6.0 N6 work further hardened the import path). Adopting the upstream model would be a trust regression.

### 5.2 - deferred items (the known-gaps tracker)

`docs/v3/v3.6/known-gaps.md`: two new DF rows + summary bump (DF 0->2, total open 3->5) + Status/Last-updated refresh.

- **DF-v36-1 (N4 self-upgrade CLI)**: deferred low-ROI; the installer re-run already performs in-place upgrade and the architecture diverges from spec-kit's packaged-CLI `specify self upgrade`. Reconsider on user friction with the installer-re-run path.
- **DF-v36-2 (N2b portable YAML workflow engine)**: deferred + policy-disfavored as a runtime; Dynamic Workflows cover Claude Code and only N2a's vocabulary was adopted (Phase 1). Reconsider only if cross-agent declarative orchestration becomes a stated goal.

### 5.3 - CHANGELOG + final verification

`CHANGELOG.md`: a `## [Unreleased]` block with a headline summary (5 adoptions / 2 deferred / 2 declines; no new outbound call, dependency, credential, or processor; catalog unchanged at 256 skills / 15 commands) and:

- **Added**: N3a (`base-*.md` lockstep parity-governance guard), N1a (workflow-phase hook recipe + example hook), N6 (`/skills import` hygiene gate).
- **Changed**: N2a (workflow gate / persisted-resume / continue-on-error vocabulary in loop-engineering + agent-orchestration-primitives), N3b (template composition-strategy vocabulary in agent-presets + theme-tokens).
- **Notes**: the durable N5 + N1b declines (matrix rows) and the deferred N4 + N2b items (known-gaps).

All added content is ASCII-only; per the Reverse-Engineering Attribution Rule the upstream is named only in the internal matrix / known-gaps / comparison docs, never in a shipped catalog artifact.

## Key decisions

- **`## [Unreleased]` over `## [3.6.0]`.** Keeps version-sync green (the semver regex skips `[Unreleased]`) and respects the v3.0.0 final-phase routing that hands the bump/tag/push to `/update release`. The release flow promotes the block atomically.
- **Matrix Summary left unchanged.** N5 / N1b are external systems, not MCP registry entries, so they do not change the MCP-registry-size counts -- consistent with the v3.4.0 skill-native / re-full rows.
- **No pre-existing-warning cleanup.** The unicode-safety run surfaced pre-existing em-dash WARNs in AGENTS.md and older CHANGELOG sections; per the "every changed line traces to the request" rule, none were touched -- only my three edited files were checked (clean).
- **Release not auto-run.** Per the `/implement` final-phase routing and the AGENTS.md ask-first rule, the version bump / tag / push are NOT performed; the user is prompted to run `/update release`.

## Verification (quality gate: GO)

`make` is not on PATH on this Windows host (WN-v33-1), so the gates ran via the documented direct equivalents:

- **`make validate` (direct chain)**: GREEN. JSON catalog integrity (256 skills / 15 bundles / 17 workflows), orphan-bundle audit PASS, unicode-safety confirmed the three edited files introduced 0 non-ASCII punctuation (remaining em-dash WARNs are pre-existing AGENTS.md / older-CHANGELOG lines, out of scope), no-personal-paths / supply-chain-iocs / workflow-security / solution-frontmatter all exit 0, version-sync CHANGELOG matches 3.5.0 (the `[Unreleased]` header is skipped by the semver regex), base-template parity guard exit 0, compression accuracy-regression gate PASS (CCR 100.0%, reduction 45.8%).
- **`make test`**: `tests/validators` 199 passed (1 bash-test deselected), including the v3.6.0 guards 51/51 (`test_check_base_template_parity.py` + `test_import_skills.py`); `catalog/hooks/tests/` 441 passed + 14 jq-skips. The bash-invoking suites (`tests/installer/*`, `tests/integrations/test_parity_with_legacy_installer.py`, and `tests/validators/test_session_query_extract.py::test_discover_obsidian_vault_marker`) HANG with no output on this space-containing checkout -- a Phase-5 refinement of WN-v36-1 (a full `pytest tests` run never completes here, rather than fast-failing with exit 127, because `bash.EXE` cannot resolve a script path containing the space in "OneDrive - Supira"). They are unrunnable on this host but pass on CI / space-free checkouts, and Phase 5 changed no code so no regression is possible.
- **`make lint`**: ShellCheck is not on PATH and no shell script changed this phase (docs-only), so there is nothing to lint.
- **Diff isolation**: changes are exactly `docs/policy/mcp-reverse-engineering-matrix.md`, `docs/v3/v3.6/known-gaps.md`, `CHANGELOG.md`, plus the plan checklist, DEVLOG, and this session history. No code, no `data/` / registry edit, no installer edit.

## Files changed

- `docs/policy/mcp-reverse-engineering-matrix.md` (5.1: new "Declined in v3.6.0" section with N5 + N1b drop-outright rows)
- `docs/v3/v3.6/known-gaps.md` (5.2: DF-v36-1 / DF-v36-2 added; summary DF 0->2, total open 3->5; Status + Last-updated refreshed)
- `CHANGELOG.md` (5.3: `## [Unreleased]` block enumerating the five adoptions + the declines / deferrals note)
- `docs/v3/v3.6/plans/adoption-spec-kit.md` (Phase 5 exit checklist checked off)
- `docs/DEVLOG.md` (Phase 5 entry)
- `docs/archive/v3/v3.6/development/history/2026-06-17_adoption-spec-kit-phase-5-decline-durability-and-release-readiness.md` (this file)

## Next

v3.6.0 is implementation-complete -- all five phases of `adoption-spec-kit` are done and the full quality gate is green. The final step is release readiness: run **`/update release`** to promote the CHANGELOG `## [Unreleased]` block to `## [3.6.0]`, bump every version-carrying surface from 3.5.0 to 3.6.0 atomically (validated by `check_version_sync.py`), refresh the README "What's New", and -- with its own confirmation gates -- merge `develop` -> `main`, tag `v3.6.0`, and push. No version bump, tag, or push was performed automatically in this phase.
