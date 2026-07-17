# Known Gaps - v3.14

**Project**: Nexus-Hub
**Status**: v3.14.0 RELEASED (2026-07-16: `feat/codex-lb-adoption` -> `develop` -> `main`, tag `v3.14.0`, pushed; GitHub Release publish handed to the user due to an invalid local `gh` token). v3.14.1 installer-hotfix on `fix/installer-hotfix` (cut off the released `develop`): all 3 phases complete; RELEASE-READY, pending `/update release` (v3.14.1 bump / `develop` -> `main` merge / tag / push / GitHub Release).
**Last updated**: 2026-07-16 (v3.14.1 Phase 1)

> **Prior-version ingest**: the open v3.13 items (presentify DF-1..DF-5, WN-1/2, MT-1) are unrelated to this feature set and do not carry in. HO-1 (flat/nested skill-name collision across skill layouts) was VERIFIED clean by the Phase 6.4 dry-run install: `review-trapdoors` lands flattened at `skills/review-trapdoors/SKILL.md` across all seven platform skill paths with no nested `skills/code-review/review-trapdoors/` variant.

## v3.14.1

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 2 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

### Capabilities added this version

- **Global-install manifest path + graceful degradation (Phase 1)**: `scripts/lib/integrations/runner.py` now centralizes the target-root fallback in a single `_resolve_target_root(args)` helper, so a `--scope global` install resolves the manifest under the user home (`~/.nexus-hub/install-manifest.json`) regardless of the process CWD. This resolves the `PermissionError [WinError 5]` traceback (one per integration) that fired when the one-line bootstrap ran from an elevated `C:\Windows\System32` prompt and the manifest write resolved to `C:\Windows\System32\.nexus-hub\`. A failed `manifest.save(...)` in `cmd_install` / `cmd_teardown` now degrades to one stderr warning instead of aborting the runner with a traceback and a non-zero exit. Covered by `tests/integrations/test_runner_target_root.py` (7 tests). Installer-side only (auto-distributed via the integration-registry folder copy); no installer copy-step edit and no `base-*.md` change.
- **Orphaned auth-monitor scheduled-task cleanup (Phase 2)**: `scripts/lib/integrations/legacy.py` gains `_cleanup_windows_auth_monitor_task` (unregisters the orphaned DevAI-Hub "Claude Code Auth Monitor" Windows scheduled task via `schtasks /Delete`, Windows-only and no-op without `schtasks`, idempotent, dry-run-aware, no elevation needed since the task is user-level) plus two sibling cleanups that sweep leftover `~/.devai-hub/scripts/run-auth-monitor.vbs` / `claude-auth-monitor.ps1` launchers without ever removing the whole `~/.devai-hub/` tree (that stays gated on `~/.nexus-hub/`). All three are registered under `LEGACY_CLEANUPS["claude"]`, so `run_cleanups` reports one `FileAction` per artifact removed. This stops the recurring "Can not find script file" Windows Script Host popup on the next install / `nexus-hub upgrade`. Covered by 9 new cases in `tests/integrations/test_legacy_cleanups.py`. Installer-side only; no installer copy-step edit and no `base-*.md` change.

### Advisory

- **CI (Phase 1.3), informational (not an open gap)**: no dedicated path-filtered CI job was added for the integration tests. The existing `tests` job in `.github/workflows/ci.yml` already runs `pytest tests/integrations` on every non-docs change (changes under `scripts/lib/integrations/` and `tests/integrations/` are outside `docs/`, so they trigger it), and workflow-level `concurrency: cancel-in-progress` is already set, so a separate path-filtered job would only duplicate the run and raise action minutes. Phase 3.3 confirmed this holistically.
- **Residual latent installer behavior (Phase 3.2), informational (not an open gap)**: `scripts/installer.ps1` and `scripts/installer.sh` still pass `--target` to the integration runner only for workspace scope, never for global scope. This is now correct-by-construction and needs no change: the runner resolves global scope to the user home centrally in `_resolve_target_root(args)` (Phase 1), so a global install with no `--target` writes the manifest under `~/.nexus-hub/` regardless of the installer's invocation directory. The fix was deliberately centralized in the runner (which both installers already call) rather than duplicated into the two installer scripts, avoiding a `base-*.md` lockstep change and an installer copy-step edit.

### Open Items

None open. Phases 1-2 resolved both reported defects (BG resolved 2); Phase 3 (architecture refactor confirmed clean, known-gaps reconciled, CI/CD confirmed) is complete. Ready to hand off to `/update release` for the v3.14.1 bump / changelog finalize / `develop` -> `main` merge / tag / push / GitHub Release.

## v3.14.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 3 | 0 |
| Bugs / regressions (BG) | 0 | 1 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |
| Hand-offs (HO) | 0 | 1 |

### Capabilities added this version

- **Codex Usage Monitor (Phase 1)**: the `claude-usage-monitor` VS Code extension (independently versioned 0.6.2 -> 0.7.0) generalized behind a `UsageProvider` interface, with a second provider for Codex (ChatGPT / OpenAI). The Codex provider reads the local Codex app OAuth token (from `usageMonitor.codex.authPath`, `CODEX_HOME/auth.json`, or `~/.codex/auth.json`) and fetches account usage from the undocumented `chatgpt.com/backend-api/wham/usage` endpoint, mapping the primary and secondary rate-limit windows onto the session and weekly metrics plus plan type, credits, and additional-limit rows. The whole status-bar / tooltip / dashboard / warning UI is reused; recommendations are reframed for Codex (throttle, wait-for-reset, rotate-account) since Codex has no cheaper model tier. A `usageMonitor.provider` setting, a "Usage: Switch Provider" command, and a settings-panel selector switch providers. Fail-soft throughout; the Claude path is byte-for-byte unchanged; the single outbound call goes only to the user's own account. Provider logic, the Codex payload mapper, the error resolver, and the Codex recommendation branches are covered by a 35-test Vitest suite. No catalog skill, command, metadata, installer, or base-template was touched.
- **Skill-native review/verification cluster (Phase 2)**: a new `review-trapdoors` code-review skill plus a `review-trapdoors.md` style guide (a curated, project-specific recurring-blocker convention applied before review or a review-ready claim); a PR/CI-state evidence example folded into `verification-before-completion` (verify review/CI state against the authoritative current-head source; missing-review is not approval); and a merge-readiness contract extending `quality-gate-definitions` (a `merge-ready` composite gate + a `merge-readiness-contract.md` style guide documenting the configurable collaborator rules). C3 and C6 are body-only edits (no registry change); `review-trapdoors` is registered in all three metadata files. Catalog: 267 skills. Count references reconciled to 267 across skills.json, `data/SKILL_INDEX.md`, and AGENTS.md (the SKILL_INDEX total line had been stale at 265).
- **Spec/context split + spec-as-merge-gate convention (Phase 3, C5)**: a body-only extension to `spec-driven-development` adding a normative-spec vs free-form-context split (the normative `spec.md` holds only testable FR-### / SC-### items; rationale/decisions/failure-modes/examples ride the existing per-version `docs/` tree) and a spec-as-merge-gate rule (behavior / API / schema / CLI changes update the spec before code; not review-ready until spec, code, and tests agree), mapped onto `/spec`, `cross-artifact-analyzer`, `implementation-convergence`, and the merge-readiness contract. The external `openspec` CLI is explicitly not adopted (convention only, per the MCP Registry Policy). No new skill, no frontmatter change, no registry update; catalog stays 267 skills.
- **Declarative skill-activation ruleset + guard/tracker hooks (Phase 4, C1)**: a project-local `skill-rules.json` schema (`catalog/hooks/skill-rules.example.json` + `catalog/style-guides/skill-activation-rules.md`) and three opt-in, fail-open hooks (`skill-activation-suggest.py` on UserPromptSubmit, `skill-guard.py` on PreToolUse Edit|MultiEdit|Write, `skill-tracker.py` on PostToolUse Skill, plus a shared `_skill_rules.py`), registered in `settings.json` (ask-first, confirmed). The guard suggests by default and blocks only under `NEXUS_SKILL_GUARD_BLOCK=1` with an `enforcement: block` rule (fail-open inversion of the source pattern). All hooks are no-ops without `skill-rules.json`, honor `NEXUS_DISABLED_HOOKS` / `NEXUS_HOOK_PROFILE=minimal`, are stdlib-only with no outbound calls, and never log secrets; `.py` hooks run cross-platform via `python3` (no `.ps1` sibling, matching the existing `.py` hooks). Covered by `test_skill_activation.py` (14 tests). Hooks 25 -> 28.
- **Cross-model review recipe concretization (Phase 5, C2)**: a body-only extension to `cross-model-orchestrator` adding a runnable, vendor-neutral "Cross-Model Review Loop" recipe (resolve scope -> review on a different operator-configured model -> findings schema -> HITL gate -> atomic per-finding fix-verify-commit -> re-review with safety limits max 3 iterations + recurrence do-not-refix -> final report), with an inline env-var-driven invocation, a vendor-neutrality rationalization, and cross-links. Cites the MCP Registry Policy generation-as-service hard-no (adopts the loop shape, not a Codex-CLI lock-in). No wrapper script bundled (documented inline); no frontmatter change, no registry update; catalog stays 267 skills / 28 hooks.
- **Terminal refactor + reconciliation + CI/CD (Phase 6)**: a repo-wide consistency pass over all Phase 1-5 additions found no drift (no empty dirs, no orphaned bundle files, all validators green). BG-1 resolved (declared `verify_platform_contracts.py` dev-only). QG-1 resolved (new path-filtered `.github/workflows/claude-usage-monitor.yml` compiles + Vitest-tests the extension). HO-1 verified clean by the dry-run install. Full validation green: catalog validators 0 errors; workflow-security / platform-contracts / base-template-parity PASS; full pytest suite 459 passed / 0 failed; extension compiles + 35 tests pass; version-sync consistent at 3.13.0 (bumps to 3.14.0 at `/update release`).

### Advisory

- Switching the monitored provider (`usageMonitor.provider`) clears the previously cached usage data by design, since it belongs to a different account with different semantics. The status bar then shows the empty state until the first fetch for the new provider completes.

### Open Items

#### Deferred

##### DF-1 - Exact Codex-app credential location and field shape are unverified

- **Source phase**: Phase 1 (1.2)
- **Plan reference**: sub-task 1.2 ("CONFIRM the exact path and field names at implementation time"); Phase 6.2 records this as a deferred confirmation
- **Reason**: This build targets the ChatGPT Codex **app** (not the open-source Codex CLI, per the user's clarification), and the app's on-disk credential path and field names could not be verified from this environment. The provider therefore reads a **configurable** path (`usageMonitor.codex.authPath`, then `CODEX_HOME/auth.json`, then `~/.codex/auth.json`) and parses **shape-tolerantly** (nested `tokens.{access_token,account_id}` or flat `{access_token,account_id}`, plus camelCase), failing soft when nothing usable is found.
- **Suggested next step**: Confirm the real Codex-app credential path and field names against a live install; set the probed default accordingly (or document the setting prominently). The configurable-path + fail-soft design means a wrong default is user-correctable without a code change.

##### DF-3 - P1: provider failover / settlement invariants as multi-provider-ai reference content

- **Source phase**: comparison scope (out of the seven selected v3.14 candidates); the Definition of Done defers it here
- **Plan reference**: plan "Definition of Done" ("P1 (provider-routing reference content) is deferred to `docs/v3/v3.14/known-gaps.md` as an optional follow-up")
- **Reason**: codex-lb's provider failover / settlement invariants (from its load-balancer product) are a different product category from Nexus-Hub's catalog and were not selected for adoption. They survive only as OPTIONAL reference content for the `multi-provider-ai` skill.
- **Suggested next step**: If provider-routing reference content is wanted later, distill the failover / settlement invariants into `multi-provider-ai` as a body-only reference (skill-native, no external dependency), in a separate version.

##### DF-2 - wham/usage is an undocumented endpoint (durability risk)

- **Source phase**: Phase 1 (1.3)
- **Plan reference**: Phase 1 stability gate ("fail soft when the undocumented endpoint is unavailable"); Phase 6.2 durability note
- **Reason**: `chatgpt.com/backend-api/wham/usage` is an internal, undocumented ChatGPT backend endpoint that OpenAI can change without notice (the same fragility class as the Claude monitor's dependency on the Anthropic usage endpoint, arguably higher because it is reverse-engineered). The mapper validates defensively and any parse failure, HTTP error, timeout, or missing field yields the fail-soft "usage unavailable" state.
- **Suggested next step**: None guaranteeable in code; monitor for breakage. The fail-soft behavior and the manual-entry fallback contain the blast radius.

#### Bugs / regressions

##### BG-1 - Pre-existing: verify_platform_contracts.py not registered in either installer

- **Source phase**: discovered during Phase 4 validation (pre-existing on the branch; NOT introduced by this release)
- **Plan reference**: none (out of the codex-lb plan's scope; traces to v3.12.1 when the script was added)
- **Reason**: `scripts/verify_platform_contracts.py` (a v3.12.1 script) is registered in NEITHER `scripts/installer.sh` NOR `scripts/installer.ps1`, and is not in the test's `DEV_ONLY_SCRIPTS` allow-list, so `catalog/hooks/tests/test_installer_smoke.py::test_installers_copy_every_scripts_dir_py_file` fails. Phase 4 touched no `scripts/` or installer files (`git diff main...HEAD -- scripts/` is empty), so this failure is inherited, not caused by this phase.
- **Resolution (Phase 6.3)**: RESOLVED. `verify_platform_contracts.py` added to `DEV_ONLY_SCRIPTS` in `test_installer_smoke.py` (it is a repo-internal validator like `check_base_template_parity.py`, correctly not installer-copied). `test_installer_smoke.py` now passes (28/28); the full suite is 459 passed / 0 failed.

#### Missing tests / coverage gaps

##### MT-1 - Extension UI modules have no automated tests

- **Source phase**: Phase 1 (1.4)
- **Plan reference**: Phase 1 stability gate scoped automated tests to "provider unit tests"
- **Reason**: `statusBarManager.ts`, `dashboardPanel.ts`, `warningView.ts`, `settingsPanel.ts`, and `extension.ts` render VS Code UI and require the extension host, so they are validated by `tsc` compile and manual run only. The provider data layer, the Codex payload mapper, the error resolver, the provider factory, and the Codex recommendation branches ARE unit-tested (35 Vitest tests). This matches the pre-existing state (the extension had no tests before this phase).
- **Suggested next step**: Add a VS Code integration test harness (`@vscode/test-electron`) if the UI surface grows, or extract more pure logic behind the vscode boundary; not warranted for the current thin UI branches.

#### Quality-gate gaps

##### QG-1 - The claude-usage-monitor extension is not exercised in CI

- **Source phase**: Phase 1 (1.5 / post-phase 8.3)
- **Plan reference**: Phase 6.3 ("add or extend a path-filtered job that compiles and tests the `claude-usage-monitor` extension only when `extensions/claude-usage-monitor/**` changes")
- **Reason**: `.github/workflows/ci.yml`'s `tests` job installs and tests the Python extensions only; there is no Node/npm job that runs `tsc` compile + the Vitest provider suite for this extension. Editing CI is an ask-first gate and Phase 6.3 formally owns creating this job, so it is deferred rather than wired in this non-final phase.
- **Resolution (Phase 6.3)**: RESOLVED. Added `.github/workflows/claude-usage-monitor.yml` - a path-filtered (`extensions/claude-usage-monitor/**`), concurrency-cancelled job running `npm ci` + `npm run compile` + `npm test` (Vitest). Passes the workflow-security validator (checkout pinned to SHA; GitHub-owned `setup-node@v4`).

#### Hand-offs

##### HO-1 - Verify no flat/nested skill-name collision for `review-trapdoors` at install

- **Source phase**: Phase 2 (2.1)
- **Plan reference**: Prior-Version Known-Gaps Ingest (v3.13 HO-1); Phase 6.4 dry-run install
- **Reason**: Carried forward from v3.13. The flattening migration means a same-`name` skill can collide across flat and nested install layouts. Phase 2 ships the first new catalog skill of this release (`review-trapdoors`), so the collision check now applies to it.
- **Resolution (Phase 6.4)**: RESOLVED. The throwaway dry-run global install (`runner.py`, all platforms) confirmed `review-trapdoors` lands flattened at `skills/review-trapdoors/SKILL.md` across all seven platform skill paths with NO nested `skills/code-review/review-trapdoors/` variant; the C1 hooks + `skill-rules.example.json` landed at `.claude/hooks/` and are registered in the installed `settings.json`.
