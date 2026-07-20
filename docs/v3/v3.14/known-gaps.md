# Known Gaps - v3.14

**Project**: Nexus-Hub
**Status**: v3.14.0 RELEASED (2026-07-16: `feat/codex-lb-adoption` -> `develop` -> `main`, tag `v3.14.0`, pushed; GitHub Release publish handed to the user due to an invalid local `gh` token). v3.14.1 installer-hotfix on `fix/installer-hotfix` (cut off the released `develop`): all 3 phases complete; RELEASE-READY, pending `/update release` (v3.14.1 bump / `develop` -> `main` merge / tag / push / GitHub Release). v3.14.2 comparison-versioning-fix on `fix/comparison-versioning` (cut off `develop`): Phases 1-3 (Fix A adoption-target placement + Fix B from-comparison co-location + Fix C co-location drift check) complete; Phase 4 (terminal refactor/known-gaps/CI-CD) pending.
**Last updated**: 2026-07-20 (v3.14.6 release - usage-monitor fixes + installer-log overhaul)

> **Prior-version ingest**: the open v3.13 items (presentify DF-1..DF-5, WN-1/2, MT-1) are unrelated to this feature set and do not carry in. HO-1 (flat/nested skill-name collision across skill layouts) was VERIFIED clean by the Phase 6.4 dry-run install: `review-trapdoors` lands flattened at `skills/review-trapdoors/SKILL.md` across all seven platform skill paths with no nested `skills/code-review/review-trapdoors/` variant.

## v3.14.6

**Status**: RELEASED. Post-v3.14.5 fix release (`fix/usage-monitor-and-installer-ux` off `develop`): Codex auto-fetch schema-mismatch fix (retires the v3.14.5 DF-2 wham/usage uncertainty - the endpoint + schema are now verified against a live 200 response), manual-entry removal, inline dashboard settings (both extensions, gear removed), and the installer-log overhaul. No new open gaps; catalog counts unchanged (267 skills, 16 commands, 28 hooks).

### Open Items

#### Hand-offs

##### HO-1 - Host-only manual smoke for the two usage-monitor extensions (carried + extended from v3.14.5)

- **Source**: v3.14.6 (extends the v3.14.5 HO-1)
- **Reason**: the extension webview rendering + status-bar behavior can only be confirmed in a live VS Code (no automatable surface here). The unit tests lock the constants + mapper + logic; rendering is host-only.
- **Manual smoke checklist** (verified by the user this cycle for the new items):
    - Status bar shows only the two usage items (no gear); order Claude Usage, Codex Usage, Copilot. [verified]
    - The dashboard gear toggles the inline Settings section under the dashboard; Save/Reset persist; the open/closed state survives a dashboard refresh. [verified]
    - Codex auto-fetch shows the real weekly usage; the compact toggle drops the "<Name> Usage:" label live. [verified]
- **Disposition**: verified by the user during this cycle; retained as the standing per-release smoke checklist for the extensions (no code gap).

### Advisory

- **`platform-read-contracts` reaffirmed, not re-verified**: v3.14.6 touched no platform read-paths, so the 2026-07-19 full 13-platform web re-verification (v3.14.5) still holds and the freshness marker was re-stamped to 3.14.6 without a fresh web-search cycle. The additive drift (Copilot/Cursor/Codex/OpenCode gained skills/agents/hooks surfaces) remains tracked for v3.15.0 (in progress on `feat/platform-parity-all-gaps`).

## v3.14.5

**Status**: Phases 1-7 COMPLETE on `feat/installer-ux-monitor-fixes` (cut off `develop`). v3.14.5's own work is RELEASE-READY pending `/update release`. The one pre-existing release caveat (the `scan_skill_security` catalog gate red on a v3.14.3 Pexels false-positive) was RESOLVED during release-prep via a class-2 heuristic refinement (self-authenticating API clients report MEDIUM, real exfiltration stays HIGH) - the catalog gate is now green; see the third Advisory item. **Phase 1 COMPLETE**: Runner structured per-surface summary channel (`runner.py --summary-json`) + `WriteResult.detected` / `mark_not_detected()` + the five detection-gated subclasses (kimi/qwen/openclaw/windsurf/copilot) now report detected-vs-skipped, so the installer can render an accurate per-platform checklist and stop reporting undetected platforms as installed. **Phase 2 COMPLETE** (global scope): both installers now render that summary as the mockup per-platform checklist with lazy vendor headers, a single grouped "NOT DETECTED" section, colors for Kimi/Qwen/OpenClaw (+ Aider/Windsurf in bash), and the verbose per-platform caveats removed; Claude renders the unified checklist via quiet helpers (`6>$null` / `>/dev/null`). A `_surface_root`/`_join_distinct` refinement of the Phase 1 runner makes multi-root surfaces (Codex skills) render clean paths. Gates green (installer smoke 29/29; tests/integrations 354; `installer.ps1` parse + `bash -n` + ShellCheck clean). **Phase 3 COMPLETE**: the stacked blank lines between the tail sub-sections (nexus-hub CLI / Project auto-seed / Install verification) are collapsed to one blank, and the "Usage Monitors" block is split into vendor-grouped Anthropic (Claude Usage Monitor) + OpenAI (Codex Usage Monitor) sections; both installers in lockstep (installer smoke 29/29; parse + `bash -n` + ShellCheck clean; no Python changed so tests/integrations unaffected). **Phase 4 COMPLETE** (Codex Usage Monitor): manual-entry fallback (`codex-usage.enterManual` + dashboard button, writing `dataSource:"manual"`) + honest/actionable empty state + fixed usage-page deep link (`chatgpt.com/codex/settings/usage`) + theme-adaptive `codex-dark`/`codex-light` dashboard tab icon; the `wham/usage` auto-fetch mapper is broadened best-effort (added `primary_window`/`secondary_window`/`five_hour_limit`/`weekly_limit` aliases) with residual shape-uncertainty in DF-2. Gates green (tsc compile clean; Vitest 36/36; VSIX packages with the new icons included). **Phase 5 COMPLETE** (both extensions): status-bar priorities fixed so the four items read [Claude usage][Claude gear][Codex usage][Codex gear] (Claude 103/102, Codex 101/100) + a `compactStatusBar` toggle in both that drops the "<Name> Usage:" label; versions bumped (Claude 0.8.0->0.9.0, Codex 0.1.0->0.2.0). Gates green (both compile clean; Codex Vitest 38, Claude 5; both package). The priority constants + compact label are unit-tested; live left-to-right ordering + the live toggle are host-only manual smoke (HO-1 class). **Phase 6 COMPLETE** (mandatory contract-verification gate): the duplicated "expected paths per platform" data is consolidated into one machine-readable `docs/policy/platform-read-contracts.json` (`contract_checks` + `install_verify` + a `meta` marker) consumed by both `verify_platform_contracts.py` (behavior-preserving DRY refactor) and the runner's `_verify_checks`; a new `check_platform_contract_freshness.py` fails `make validate` + CI whenever `meta.verified_for_version` != the release version, so a release cannot ship on a contract not re-verified for it; the `platform-contract-verification` skill + `/update release` step 4 now re-stamp the marker at release. The `meta` marker was left honest at `last_verified` 2026-07-13 / `verified_for_version` 3.14.4 (Phase 6 builds the gate infrastructure; the actual platform web re-verification + re-stamp to 3.14.5 is `/update release`'s job) - so the gate is green now and correctly fires at the release bump. No new open gaps. Gates green (validators' suites 8/8; both guards OK on the real repo; simulated release bump fails end-to-end; workflow-security exit 0). **Phase 7 COMPLETE** (terminal refactor + known-gaps + CI/CD): the cumulative `develop..HEAD` scope is 49 files, all tracing to v3.14.5 phases (no stray artifacts); no v3.14.5-introduced empty dirs / duplicates / orphans (the new `codex-dark`/`codex-light` SVGs are referenced from `dashboardPanel.ts`; the new `platform-read-contracts.json` sits beside its prose companion); AGENTS.md updated for the new contract-freshness gate; a PRE-EXISTING AGENTS.md doc-staleness (the "legacy installer copy blocks" framing - false on `develop` too, so NOT changed by this release) triaged and deferred as DF-3 rather than rewritten mid-release; CI/CD audited (freshness guard added to the `validate` job; both extension workflows + installer smoke + integration coverage confirmed; all path-filtered + concurrency-cancelled + npm-cached). All repo validators green (no-personal-paths exit 0, unicode-safety 0 errors, base-parity 5/5, orphan-bundle PASS 0/0). Plan: [plans/v3.14.5-installer-ux-and-monitor-fixes.md](plans/v3.14.5-installer-ux-and-monitor-fixes.md).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 4 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

### Advisory (pre-existing test failures, NOT caused by v3.14.5)

Three pre-existing test failures surfaced on this branch; none was caused by v3.14.5's phases. One (the `scan_skill_security` catalog gate) was RESOLVED during the v3.14.5 release-prep (see the third item); the other two remain (both env-only / pre-existing):

- `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` - the test's `overrides` set omits `copilot`, which has overridden `wire_project_surfaces` since v3.11.0 (returns a skip-note `WriteResult`, not `None`). Phase 1/2 never touched `wire_project_surfaces`. Fix: add `copilot` to the test's `overrides` set (a one-line test update, separate patch).
- `test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` - the Git-Bash `/usr/bin/tar` misparses the `C:\...` tarball path on this Windows host; env-only, does not reproduce on the Linux CI runner. No file this version changed is involved.
- `tests/validators/test_scan_skill_security.py::test_catalog_gate_is_clean` (surfaced during the Phase 7 regression net) - **RESOLVED during the v3.14.5 release-prep** (maintainer chose the heuristic-refinement adjudication). The `scan_skill_security` catalog gate had reported 1 HIGH finding: "class 2 Data Exfiltration - credential exfiltration (env read + network egress)" at `catalog/skills/specialized-domains/document-to-interactive-html/scripts/fetch_stock_media.py:481` (`os.environ.get("PEXELS_API_KEY")` + the Pexels API call). It was a FALSE POSITIVE - a legitimate, consent-gated stock-media API client that reads its own user-provided key and calls its own API (the v3.14.3 bring-your-own-key feature), not credential harvesting - and pre-existing (present at the v3.14.4 tag; `git diff develop..HEAD` shows the file unchanged by this branch). **Fix**: refined the class-2 behavioral-AST heuristic (`extensions/nexus-skill-scanner/src/nexus_skill_scanner/analyzers/behavioral_ast.py`) so an "env read + network egress" whose credential service token matches an egress host the script calls (a self-authenticating API client sending its OWN key to its OWN service) is reported at MEDIUM (still visible, below the HIGH gate) instead of HIGH; a credential going to an UNRELATED host (no shared service token), an all-generic credential name, or a non-literal key stays HIGH. The scanner's never-relax invariant is otherwise untouched. Verified: catalog gate exit 0; malicious fixture still HIGH; two new regression tests (`test_ast_self_authenticating_api_client_is_medium`, `test_ast_credential_to_unrelated_host_stays_high`) lock both sides; full scanner suite green (95 + 2).

### Open Items

#### Deferred

##### DF-1 - Workspace-scope Claude checklist + workspace undetected grouping deferred

- **Source phase**: v3.14.5 Phase 2
- **Plan reference**: Phase 2 (2.1/2.3 - the plan's stability gate is a global side-by-side install)
- **Reason**: Phase 2 scoped the checklist + grouping to the GLOBAL install (`Install-Global` / `install_global`), which is what every screenshot showed. Workspace-scope registry platforms already get the checklist automatically via the shared `Invoke-RegistryPlatform` / `invoke_registry_platform` (the rewrite is scope-agnostic), but the workspace-scope Claude block still prints its bespoke verbose output, and workspace undetected platforms print an inline `(reason)` note rather than being collected into a grouped section (the grouping is gated on the `-Provider` arg, which only the global caller passes).
- **Suggested next step**: apply the same `6>$null`/`>/dev/null` + checklist treatment to the workspace Claude block and add `reset_undetected_platforms`/`write_undetected_group` (+ pass provider) to `Install-Workspace` / `install_workspace`. Low risk (mirrors the global rewrite); out of scope for the global-focused Phase 2.

##### DF-2 - Codex `wham/usage` response schema unverified (auto-fetch is best-effort; manual entry is the guaranteed path)

- **Source phase**: v3.14.5 Phase 4 (carries the v3.14.0 DF-2 "wham/usage is undocumented" and the v3.14.4 DF-2 "Codex-app credential path unverified")
- **Plan reference**: Phase 4.1 ("Record any residual uncertainty about the shape as a known-gap")
- **Reason**: `https://chatgpt.com/backend-api/wham/usage` is the real endpoint the official Codex CLI polls, but it is undocumented and could not be exercised from this environment (no live ChatGPT auth/network), so the exact response schema is unverified. `locateWindows` now probes a broadened alias set based on public reports (`primary`/`secondary`, `primary_window`/`secondary_window`, `five_hour_limit`/`weekly_limit`, `five_hour`/`weekly`/`5h`/`7d`, plus an array form), and every accessor stays fail-soft. But because the shape is a best-effort guess, auto-fetch may still return `usage-unavailable`; the GUARANTEED path is the new manual-entry fallback (`codex-usage.enterManual` + the dashboard "Enter usage manually" button), and the empty state is honest about which is which.
- **Suggested next step**: capture a real `wham/usage` response from a live ChatGPT/Codex login and tighten `locateWindows` + `readWindow` to the confirmed field names; add a fixture test from the captured shape. Until then, manual entry covers the user.

##### DF-3 - Pre-existing: AGENTS.md "legacy installer copy blocks" framing predates the registry migration

- **Source phase**: v3.14.5 Phase 7 (observed during the terminal refactor audit; pre-existing, NOT caused by this release)
- **Plan reference**: Phase 7.1 (flagged the "legacy 4 copy blocks" line as stale prose to update)
- **Reason**: AGENTS.md (lines ~381/389) describes Codex / Gemini / Copilot as installing via "legacy installer copy blocks", but `install_global` in both installers routes every platform except Claude through `invoke_registry_platform` -> `runner.py` (the integration registry). `git show develop:scripts/installer.sh` confirms this was already true on `develop`, so the framing was stale BEFORE v3.14.5 - this release did not change the install mechanism. Per the "every changed line traces to the request; no out-of-scope cleanup" rule, rewriting the canonical historical architecture prose (intertwined with the v2.1.0/v2.2.0 migration notes + DF-001) was judged out of scope for a release that did not touch it, and higher-risk than leaving it. The genuinely-new fact (the contract-freshness gate) WAS documented. The plan's 7.1 premise that "this release changed the fact" was incorrect (recorded as the Phase 7 DEVIATION in the session history).
- **Suggested next step**: a dedicated AGENTS.md doc-accuracy pass to reframe "Original 4 (legacy copy blocks) / Extended 4" around the current reality (Claude = the one bespoke installer block; every other platform = the integration registry), keeping the separate permissions "legacy 4" grouping intact.

##### DF-4 - Platform additive-surface drift deferred to v3.15.0 (found by the v3.14.5 release re-verification)

- **Source phase**: v3.14.5 release governance step 4 (full 13-platform web re-verification, 2026-07-19)
- **Plan reference**: `/update release` governance step 4; maintainer chose "fix dead-path bugs now, defer additive"
- **Reason**: the release re-verification found the DEAD-PATH bugs (OpenCode `~/.config/opencode`, Kimi `.kimi/AGENTS.md`, OpenClaw `~/.openclaw/workspace/`) - all FIXED in v3.14.5 - plus a larger set of ADDITIVE drift: platforms that GAINED reusable-action surfaces Nexus-Hub does not yet target. These are net-new capability, not breakage, and are the scope of the already-planned v3.15.0 platform-parity release. Deferred items (full detail + sources in `docs/policy/platform-read-contracts.md` Re-verification log): (1) **Copilot** now natively reads Agent Skills on by default (`.github/skills/`, `~/.copilot/skills/`, `~/.claude/skills/`), custom agents (`.github/agents/*.agent.md`), and hooks; (2) **Cursor** gained Agent Skills (`.cursor/skills/`, `~/.cursor/skills/`, `.agents/skills/`), subagents, and hooks; (3) **Codex** gained a hooks system (`~/.codex/hooks.json`) and one source reports `~/.codex/skills` is no longer read (kept pending a second confirmation - removing a possibly-live path on single-source evidence could break delivery, and `~/.agents/skills` already covers Codex); (4) **OpenCode** supports agents (`~/.config/opencode/agents/`) + plugin hooks, commands are a TUI slash surface, and it has no `rules/` dir. UNVERIFIED (official docs unreachable): **Antigravity** global-workflows dir community-reported as `~/.gemini/antigravity/global_workflows/` (vs contract `~/.gemini/config/global_workflows/`; SPA docs unfetchable) and `.agents/subagents/` appears obsolete; **Gemini IDE** per-tool paths undocumented + IDE sunset for free/Pro/Ultra. NOTE: Windsurf rebranded "Devin Desktop" (legacy surfaces still served; `.devin/rules/` now preferred).
- **Suggested next step**: fold these verified findings into `docs/v3/v3.15/plans/v3.15.0-platform-parity-all-gaps.md` (the plan already targets Cursor skills/hooks/agents, OpenCode agents/plugins, Copilot skill broadening). Confirm the Antigravity global-workflows path against an authoritative source and the Codex `~/.codex/skills` read-status before acting on either.

#### Warnings

##### WN-1 - Pre-existing: `qwen.py` imports `FileAction` unused

- **Source phase**: v3.14.5 Phase 1 (observed during lint; pre-existing, NOT introduced by this phase)
- **Plan reference**: Phase 1 (Phase 3 lint gate)
- **Reason**: `scripts/lib/integrations/qwen.py` line 20 imports `FileAction` from `.result` but never uses it. `git show HEAD:scripts/lib/integrations/qwen.py` confirms the import predates this phase (Phase 1 edited only the `install_global` body, not the imports). Ruff flags it F401, but ruff is not a project gate (no ruff config; not in the Makefile or CI - the repo gates on the python validators + pytest + ShellCheck), so it does not fail validation. Left untouched per the "every changed line must trace to the request; no out-of-scope cleanup" rule.
- **Suggested next step**: drop the unused import in a dedicated lint-cleanup patch (or opportunistically when a later phase legitimately edits qwen.py's imports); trivial and safe, just out of this phase's scope.

#### Missing tests / coverage gaps

##### MT-1 - Usage-monitor extensions' UI orchestration remains partially host-only

- **Source phase**: v3.14.5 Phases 4-5 (carries the v3.14.4 MT-1)
- **Plan reference**: Phase 7.2
- **Reason**: Phases 4-5 ADDED Vitest coverage to both extensions - Codex 38 tests (the `wham/usage` window-alias mapper, the actionable empty-state banner, the status-bar priority constants + compact label) and Claude 5 (priority constants + compact label) - closing the largest prior gaps. What remains host-only (not unit-testable without a live VS Code extension host): the actual webview rendering (dashboard HTML, the theme-adaptive tab icon), the manual-entry input-box flow end to end, and the live status-bar left-to-right ordering. These are covered by the HO-1 manual smoke checklist below.
- **Suggested next step**: a `@vscode/test-electron` integration harness if UI-render regressions ever recur; today the unit tests plus the manual smoke checklist are proportionate.

#### Hand-offs

##### HO-1 - Host-only manual smoke for the two usage-monitor extensions

- **Source phase**: v3.14.5 Phases 4-5 (carries the v3.14.4 HO-1)
- **Plan reference**: Phase 7.2
- **Reason**: A handful of the extension changes can only be confirmed in a live VS Code (no automatable surface here). The unit tests lock the constants + logic; the rendering + live behavior are host-only.
- **Manual smoke checklist** (run once in a live VS Code with both extensions installed):
    - The four status-bar items render left-to-right as [Claude usage][Claude gear][Codex usage][Codex gear].
    - Toggling `compactStatusBar` on either extension updates its status-bar text live (drops the "<Name> Usage:" label).
    - The Codex dashboard tab icon appears dark on light themes and light on dark themes (matching Claude's).
    - "Codex Usage: Enter Usage Manually" (palette + dashboard empty-state button) accepts two percentages and fills the dashboard + status bar.
    - Both extensions install and run side by side with no id / command / view collision.

## v3.14.4

**Status**: Phases 1-4 COMPLETE on `feat/usage-monitor-split` (cut off `develop`); RELEASE-READY, pending `/update release` (v3.14.4 bump 3.14.3 -> 3.14.4 / CHANGELOG `[Unreleased]` -> `[3.14.4]` / `develop` -> `main` merge / tag / push / GitHub Release). Phase 1 (de-Codex the Claude extension): `claude-usage-monitor` is Claude-only again (`0.7.0 -> 0.8.0`), 3 Vitest tests green. Phase 2 (scaffold the separate Codex extension): new `extensions/codex-usage-monitor/` (`0.1.0`), Codex-only, own identity/branding/glyph-font/`#5244BB` bars, collision-free with the Claude extension, 34 Vitest tests green, VSIX packages, path-filtered CI workflow added. Phase 3 (distribution wiring): both installers generalized to build/install both extensions via a shared per-extension helper, dependabot entry added for the Codex extension, installer smoke test asserts both (29 pass); `bash -n` + ShellCheck + `installer.ps1` parse all clean. Phase 4 (terminal refactor + docs): repo-wide sweep found no stale live "unified extension" references (only historical change-records + the v3.14.0 plan, correctly frozen); root `README.md` (extensions section + a v3.14.4 What's New), `llms.txt`, and `SECURITY.md` now describe both extensions; per the implement-phase runbook the version bump / changelog finalization / merge / tag / push are handed to `/update release`, so the CHANGELOG stays under `[Unreleased]` and version-sync stays consistent at 3.14.3 until release. Phase 4 validation: no empty dirs / orphans; `validate_skills --bundles-only` PASS (267 skills, 0/0); `check_version_sync` consistent at 3.14.3; `validate_workflow_security` + `check_base_template_parity` PASS; both extension suites green (Claude 3, Codex 34); hooks/installer suite 460 passed / 36 skipped; no new TODO/FIXME/DEVIATION markers. Plan: [plans/v3.14.4-usage-monitor-split.md](plans/v3.14.4-usage-monitor-split.md).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

### Open Items

#### HO-1 - Runtime side-by-side install not verified in this environment

- **Source phase**: v3.14.4 Phase 3
- **Plan reference**: Phase 3 sub-task 3.4 ("side-by-side coexistence verification")
- **Reason**: The static coexistence guarantees were verified (both extensions build + package to distinct VSIX; a scan confirms zero shared extension-id / command / `globalState`-key / webview-id / view-container / `when`-context; the smoke test asserts both installers wire both ids). The runtime confirmation that BOTH status-bar items render simultaneously in a live VS Code window (`$(claude-icon) Claude Usage: ...` and `$(codex-icon) Codex Usage: ...`) could not be automated here - it needs an interactive VS Code instance.
- **Suggested next step**: On any machine with VS Code, run the installer (or install both VSIX with `code --install-extension`), reload, and confirm both status-bar items appear and each dashboard/settings/warning surface targets the correct extension. Low risk given the static guarantees; a manual smoke check before release is sufficient.

#### DF-1 - Codex extension `icon.png` reconstructed from `codex-white.png`, not the user's `codex-2048x2048.png`

- **Source phase**: v3.14.4 Phase 2
- **Plan reference**: Phase 2 sub-task 2.2 ("Save the two provided images")
- **Reason**: The user referenced two brand assets: `codex-white.png` (found in the user's Downloads, 640x640 white cloud silhouette with the `>_` knocked out) and `codex-2048x2048.png` (the full-color Marketplace icon). Only `codex-white.png` was on disk; `codex-2048x2048.png` could not be located anywhere on the machine, and no SVG rasterizer (ImageMagick / rsvg / cairosvg / inkscape) was available to synthesize one. `icon.png` (512x512) was therefore reconstructed with Pillow from `codex-white.png`'s exact silhouette: the cloud body filled with a periwinkle->`#5244BB` vertical gradient and the `>_` knockout painted black. The result is a faithful match to the described design, but it is a reconstruction rather than the user's original file.
- **Suggested next step**: If the user has the exact `codex-2048x2048.png`, drop it in as `extensions/codex-usage-monitor/icon.png` (a one-file swap; the manifest already points at `icon.png`, so no code change). By-design acceptable otherwise - the reconstructed icon is on-brand and functional.

#### DF-2 - Exact Codex-app credential location and field shape are unverified (carried from v3.14.0)

- **Source phase**: v3.14.4 Phase 2 (inherited from the v3.14.0 Codex provider)
- **Plan reference**: Known-Gaps Ingest
- **Reason**: The Codex provider targets the ChatGPT Codex **app** (not the open-source CLI); the app's on-disk credential path and field names could not be verified from this environment. The provider reads a configurable path (`codexUsage.authPath`, then `CODEX_HOME/auth.json`, then `~/.codex/auth.json`) and parses shape-tolerantly (nested `tokens.{access_token,account_id}` or flat, plus camelCase), failing soft when nothing usable is found.
- **Suggested next step**: Confirm the real path/field shape against a live Codex-app install and tighten the default if warranted. Fail-soft behavior means this is not a blocker.

#### MT-1 - Claude extension UI orchestration remains unit-test-light

- **Source phase**: v3.14.4 Phase 1
- **Plan reference**: Phase 1 sub-task 1.4 (Testing and Stabilization)
- **Reason**: Removing the Codex provider dropped the Vitest suite from 35 tests to 3; the survivors cover `describeProviderError` and provider identity. The UI orchestration files (`statusBarManager`, `dashboardPanel`, `settingsPanel`, `warningView`, `extension`) and the `recommendations` engine have no direct unit tests. This is a pre-existing gap for a VS Code extension whose bulk is webview/status-bar UI (hard to unit-test without a VS Code host), not a regression introduced by the de-Codex work - the removed tests exercised Codex code that moves to the new extension in Phase 2.
- **Suggested next step**: In Phase 2, port the recommendations/mapping-style tests to the new Codex extension and consider adding pure-function unit tests for the shared `recommendations.ts` Claude branches (they are host-independent). Not a release blocker.

## v3.14.3

**Status**: Phases 0-4 COMPLETE on `feat/presentify-upfront-questions` (cut off `develop`) - 0 (restore skill loading), 1 (hoist + batch the four design questions, forbid memory pre-answering), 2 (imagery stock-first priority + gated stock video, "video out of scope" reconciled), 3 (bring-your-own-key `nexus-hub setup-media`), 4 (terminal refactor + known-gaps reconciliation + CI/CD). RELEASE-READY, pending `/update release` (v3.14.3 bump / `develop` -> `main` merge / tag / push / GitHub Release) - which per the plan's sequencing must run only AFTER v3.14.0, v3.14.1, and v3.14.2 land. Phase 4 audit: all 66 changed files traced to a phase; no `data/` or `base-*.md` drift; installer parity confirmed (Phase 0 flatten + Phase 3 `setup-media` copy in both); CI wired (validate_skills.py strict-YAML gate + new `tests/skills` step).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 6 | 0 |
| Bugs / regressions (BG) | 0 | 2 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |
| Hand-offs (HO) | 0 | 0 |

### Capabilities added this version (Phases 0-3)

- **Strict-YAML frontmatter gate** (`scripts/validate_skills.py`): a new `validate_frontmatter_strict_yaml` check feeds each SKILL.md frontmatter block to `yaml.safe_load` and fails the run (in the full validator AND `--bundles-only`, the mode CI runs) on any `YAMLError`, closing the gap where the tolerant line-split parser accepted frontmatter a strict consumer rejects. Degrades to an unquoted-`: `-scalar heuristic when PyYAML is absent.
- **Claude skill flatten in both installers** (`scripts/installer.sh` `flatten_skills_into`, `scripts/installer.ps1` `Flatten-SkillsInto`): the Claude global and workspace blocks now flatten `catalog/skills/<category>/<name>/` to `<claude>/skills/<name>/` (one level, discoverable), staging a flattened copy and reusing the existing `safe_folder_copy` / `Safe-Folder-Copy` refresh-prune / merge machinery, plus an explicit category-directory cleanup so a prior nested layout never lingers. Verified: refresh prunes stale flat + category dirs, merge preserves user extras, target skill discoverable at one level, 275-dir parity with the Python `flatten_skills` adapter, bundled `scripts/`/`references/` preserved; ShellCheck green, `installer.ps1` parses clean.
- **Presentify upfront batched design questions + no memory pre-answer (Phase 1, instruction-only)** (`catalog/commands/presentify.md`, `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md`, `references/interactive-features.md`): the four high-level design choices (style, output aspect, interactivity, imagery) are hoisted to a new up-front Step 2 (a single batched round before extraction / figure analysis), the generative token brainstorm stays at Step 5 (after extraction), the pipeline diagram / rationalizations / verification bullets are aligned, and an explicit rule forbids pre-answering any of the four from a recalled memory / saved preference / prior run / inferred context (only an explicit flag or the headless fallback skips a question). Verified: validator PASS 0/0, stale-sequencing grep ZERO, SKILL.md frontmatter byte-identical to the Phase 0 baseline (body-only), all three files ASCII-only.
- **Imagery stock-first priority + gated stock video + video-scope reconciliation (Phase 2, instruction-only)** (`SKILL.md` Step 2 + Step 6 + "When NOT to use"; `references/interactive-features.md` imagery tiers + new "Stock video (Pexels-only, gated)" material + stock-first priority rule; `references/extraction-runbook.md` out-of-scope line; `catalog/commands/presentify.md` `--images` bullet + merged design section): when opting beyond the procedural default the pipeline prefers real license-free stock and minimizes AI (Tier 3 last resort; "mix" = procedural base + real stock accents first); stock VIDEO is offered under stock / mix but gated to `--source pexels` + `PEXELS_API_KEY` + `--consent`, degrading to images-only / Tier 1 otherwise, never hotlinking; and the "video out of scope" wording is reconciled (source-embedded media ignored by the extractor vs output-side stock video supported by the gated tier). `fetch_stock_media.py` was read and its gate confirmed to match the wording; NO Python changed. Verified: validator PASS 0/0, no Python in the diff, all four edited files ASCII-only.
- **Bring-your-own-key media setup `nexus-hub setup-media` (Phase 3, code-bearing + installer-aware)** (new `scripts/setup_media_keys.py`; `scripts/nexus_hub_cli.py` `cmd_setup_media` + subparser; `fetch_stock_media.py` `_resolve_pexels_key`; `scripts/installer.sh` + `scripts/installer.ps1` copy blocks; `.gitignore`; skill-side first-time guidance in `SKILL.md` / `presentify.md` / `references/interactive-features.md`; new `tests/skills/test_media_key_setup.py`): a guided, opt-in, hidden-input helper stores a free Pexels key at `~/.nexus-hub/config/media.env` (0600), `_resolve_pexels_key` reads env-then-file, and the skill points first-time video users at the terminal command instead of the chat. The subcommand is dispatched from the single cross-platform `nexus_hub_cli.py` (the `verify` sibling pattern), and both installers register the helper by explicit name. 9/9 tests pass, including the secret-hygiene invariant (full key never on stdout/stderr). **DEVIATION**: the plan said "dispatch the subcommand in both installer shells"; the actual architecture centralizes CLI dispatch in `nexus_hub_cli.py` (a `scripts/` artifact both installers already copy; the launchers are thin shims per NI-v24-1), so the dispatch lives there (one cross-platform file) and the only installer edits are the explicit-name helper copies - lower-risk and consistent with the repo's convention.

### Resolution

The "Unknown skill: document-to-interactive-html" load failure had TWO independent root causes, both **RESOLVED in v3.14.3 Phase 0**: (1) an invalid unquoted `description` YAML scalar containing a `: ` sequence across 47 skills (quoted, byte-identical parsed value, with a strict-YAML validator gate so it cannot regress), and (2) both installers never flattening skills for Claude (now flattened to the one-level layout Claude Code discovers). Three stray `scripts/__pycache__/` directories (gitignored, never shipped) were removed from the working tree. Separately, the two presentify UX defects from Finding B are **RESOLVED in Phase 1**: the design questions arriving too late / one at a time (the last three often never appearing) is fixed by hoisting all four into one up-front batched round before extraction, and the memory-pre-answer defect (a recalled `presentation-style-preference` silently selecting the style) is fixed by an explicit no-memory rule in the skill and command. No new gaps were opened in Phase 1 (instruction-only, verified clean); DF-1..DF-3 and MT-1 remain as recorded. Phase 2 (also instruction-only) upgraded the imagery choice to prefer real license-free stock over AI and to offer gated Pexels-only stock video, and reconciled the "video out of scope" wording (source-embedded media stays ignored; output-side stock video is supported through the consent-gated stock tier); the described gate was confirmed against `fetch_stock_media.py` with no script change, and no new gaps were opened. Phase 3 (code-bearing) makes stock video "just work" after a guided one-paste `nexus-hub setup-media` setup that stores a free Pexels key securely under `~/.nexus-hub/`, adds `_resolve_pexels_key` env-then-file resolution, and points first-time video users at the terminal command rather than the chat; it opened two accepted by-design limits (DF-4 can't auto-provision a Pexels key; DF-5 Windows 0600 is best-effort) and no defects. Phase 4 (terminal gate) confirmed the release-readiness of the whole set: (0) the "Unknown skill: document-to-interactive-html" load failure is FULLY resolved (both root causes - invalid YAML across 47 skills, and the missing Claude installer-flatten); (1) the presentify late-and-partial design-question defect and the memory-pre-answer defect are resolved (four choices batched up front, no memory/preference pre-answering); (2) stock-video setup is a guided one-paste `nexus-hub setup-media` flow. The diff-scope / parity audit passed (no `data/` or `base-*.md` drift, installer parity), CI is wired (strict-YAML validator gate + new `tests/skills` step, resolving QG-1), and the remaining open items are all deferred by-design limits (DF-1..DF-6) or a low-priority test-coverage nice-to-have (MT-1) - none a release-blocker.

### Advisory (pre-existing failures surfaced during Phase 3 testing, NOT caused by this plan)

Two `tests/installer/` tests fail on this branch, and BOTH were verified to fail identically on the Phase 2 baseline with the Phase 3 changes stashed - so neither is caused by the presentify work, and neither touches any file in this plan's diff. Left unfixed to stay in scope (they are unrelated to presentify-upfront-questions); flagged here for a separate fix.

- **`test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` (pre-existing test drift)**: the test's `overrides` set is `{cursor, claude, antigravity2}`, but the `copilot` integration gained a `wire_project_surfaces` override in v3.11.0 (it returns a `WriteResult` with a "NEXUS_HUB_COPILOT_SKILLS=1 not set" skip note rather than None), so the test fails asserting copilot returns None. Fix: add `copilot` to the test's `overrides` set (a one-line test update, in a separate patch). Not a runtime defect - the copilot behavior is correct per AGENTS.md; the test is stale.
- **`test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` (environment-only)**: on this Windows host the Git-Bash `/usr/bin/tar` misparses the `C:\...\catalog.tar.gz` path as a remote host ("Cannot connect to C: resolve failed") when `install.ps1` extracts the tarball. A local MSYS-tar-vs-Windows-path artifact; it does not reproduce on the Linux CI runner and is not a code defect.

### Open Items

#### Deferred

##### DF-1 - Pre-existing `data/skills.json` description drift (not parse-truncation; shares a root with v3.14.2 WN-1 / Advisory)

- **Source phase**: Phase 0 (0.4 registry re-verify)
- **Plan reference**: sub-task 0.4 ("re-verify the data/ registry ... re-sync only if a stored value had been truncated")
- **Reason**: The mandatory 0.4 check found NO parse-truncation (the registry generator uses a tolerant parser, so it stored the full description, never cutting at the `: `), so the Phase 0 quoting fix required no registry edit (the parsed value is byte-identical). However, `data/skills.json` stores an older, SHORTER `description` for 17 of the 47 fixed skills (and more catalog-wide) - pre-existing content drift where SKILL.md descriptions were expanded without a registry re-sync. This is the same root as the v3.14.2 Advisory and WN-1 (auto-generated `data/skills.json` out of step with the current SKILL.md set).
- **Suggested next step**: fold a hand-synced `data/skills.json` description reconciliation into the WN-1 cleanup patch; do NOT run the full catalog rebuild (it rewrites the whole tree).

##### DF-2 - `.claude-plugin/plugin.json` declares a category-nested skills path; PLUGIN-surface discovery unverified

- **Source phase**: Phase 0 (0.5 installer flatten)
- **Plan reference**: sub-task 0.5 ("confirm whether Claude Code's PLUGIN discovery reads that recursively ... flag this if reproduction shows the plugin surface is also affected")
- **Reason**: `.claude-plugin/plugin.json` sets `"skills": "./catalog/skills"` (category-nested). The installer path (what users run) is fixed by 0.5, but whether Claude Code's PLUGIN/marketplace skill discovery reads the nested tree recursively could not be reproduced in this environment. If it does not, the plugin surface needs the same flat layout (a flattened skills dir or a manifest pointing at one).
- **Suggested next step**: reproduce a plugin install and confirm discovery; if nested is unreadable, add a flat skills path for the plugin manifest. Feeds Phase 4.2.

##### DF-3 - 8 non-skill level-2 directories are flattened identically to the Python adapter

- **Source phase**: Phase 0 (0.5 installer flatten)
- **Plan reference**: sub-task 0.5
- **Reason**: `catalog/skills` has 275 level-2 directories but only 267 carry a `SKILL.md`; the other 8 are a shared `code-review/references/` directory and 7 skill-named dirs without a `SKILL.md` (`lint-repair-loop`, `helper-script-authoring`, `visual-regression-testing`, `false-confidence-test-audit`, `performance-regression-gate`, `commit-sweep`, `end-of-shift-validation`). The new flatten copies all 275 to `<claude>/skills/<name>/`, exactly as the Python `flatten_skills` adapter already does for Codex/Gemini - harmless (Claude ignores a dir with no `SKILL.md`) but a catalog-hygiene item, and a flattened shared `references/` could break a `../references/` relative link if any code-review skill uses one.
- **Suggested next step**: catalog-hygiene sweep - give the 7 skill-named dirs a `SKILL.md` (or remove them) and confirm no skill relies on a cross-skill `../references/` path; out of scope for this patch (pre-existing, affects all flattened platforms equally).

##### DF-4 - Stock video requires a user-provided Pexels key (cannot auto-provision)

- **Source phase**: Phase 3 (bring-your-own-key media setup)
- **Plan reference**: Phase 3 goal + Phase 4.2 residual (b)
- **Reason**: Stock VIDEO needs a free Pexels key, and we cannot auto-provision one - a key is tied to the user's own free account, and shipping a shared embedded key is a terms-of-service violation and a secret-handling hazard. `nexus-hub setup-media` guides the ~30-second signup and stores the key, but a user who never runs it (or declines) gets images-only. This is an accepted, by-design limit, not a defect.
- **Suggested next step**: none (won't fix - inherent). Stock images need no key; the guidance fires only for a video choice with no key.

##### DF-5 - Windows file-permission hardening for media.env is best-effort

- **Source phase**: Phase 3
- **Plan reference**: Phase 4.2 residual (c)
- **Reason**: `setup_media_keys.py` sets mode `0o600` on `media.env` via `os.chmod`, which is exact on POSIX but has no direct equivalent on Windows (the file lives under the user profile, so it inherits the profile ACLs). Accepted limit; the test skips the 0600 assertion on non-POSIX.
- **Suggested next step**: none for this patch; a future hardening could set an explicit Windows ACL (`icacls`) if a stronger guarantee is ever required.

##### DF-6 - Headless aspect auto-pick uses the deck_like signal only after extraction (by design)

- **Source phase**: Phase 1 (design intake) / Phase 4.2 residual (a)
- **Plan reference**: Phase 4.2 residual (a)
- **Reason**: The four design choices are resolved up front in the batched round (Phase 1). In the non-interactive / headless fallback, the aspect auto-pick uses a coarse "deck -> full-width, report -> standard" rule at intake, but the FINE-GRAINED `deck_like` signal is only available after extraction, so the headless path resolves the precise aspect slightly later than the interactive batch. This is by design - nothing waits on it, and the coarse intake pick is recorded and refined post-extraction. Not a defect.
- **Suggested next step**: none (by design).

#### Missing tests / coverage gaps

##### MT-1 - No dedicated automated regression test for the new strict-YAML gate

- **Source phase**: Phase 0 (0.3 validator gate)
- **Plan reference**: sub-task 0.3 ("Confirm the gate fails on a deliberately-broken fixture")
- **Reason**: The strict-YAML gate was validated by a manual broken-fixture run (fails as expected) and is effectively covered in CI by the existing `validate_skills.py --bundles-only` run against the real catalog (a reintroduced unquoted `description` would fail it). There is no dedicated unit test asserting the gate's behavior in isolation.
- **Suggested next step**: add a small `tests/validators/` regression test that feeds a broken and a good frontmatter block through `validate_frontmatter_strict_yaml`; low priority given the CI coverage.

#### Quality-gate gaps

##### QG-1 - The new tests/skills/ module was not CI-gated (RESOLVED in Phase 4.3)

- **Source phase**: Phase 3 (3.5 test module); resolved Phase 4.3
- **Plan reference**: sub-task 3.5 + Phase 4.3 ("CI runs the new `tests/skills/test_media_key_setup.py`")
- **Reason**: The CI `tests` job ran `catalog/hooks/tests/`, `tests/integrations`, `tests/installer`, `tests/validators`, and the extension suites, but NOT `tests/skills/`, so the new `tests/skills/test_media_key_setup.py` (and the pre-existing `tests/skills/test_audit_docs_version_topic.py`) were not gated per-PR.
- **Resolution**: Phase 4.3 added a `pytest tests/skills -v` step to the CI `tests` job (after the validator-tests step). The workflow already scopes to non-docs changes (`paths-ignore: docs/**`), so the step runs on `scripts/`, `tests/`, and `catalog/skills/` changes; this also fixes the pre-existing `tests/skills` coverage gap. `ci.yml` re-parses clean.

## v3.14.2

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

### Capabilities added this version

- **Adoption-target placement (Phase 1, Fix A)**: `cross-project-comparison` gains Step 6.5 "Resolve Adoption Target" (and a matching Verification item), which resolves the release that will ADOPT a comparison (default: the next free version slot after the locked in-flight release, always confirmed with the user) and records it in the report header as an `Adoption target: vX.Y.Z` field. `catalog/commands/compare.md` now versions and places the report under that adoption target's directory and filename prefix, not the in-flight authoring cycle, and documents the field as the authority for the `/plan from-comparison` hand-off (forward reference to Phase 2). The two live reports were given the field retroactively (codex-lb -> v3.14.0, codesight -> v3.15.0). Skill `version` bumped 1.1.0 -> 1.2.0 and hand-synced in `data/skills.json`; a `python scripts/validate_skills.py --bundles-only` step was added to the CI `validate` job. Instruction-level only; no installer copy-step edit, no `base-*.md` change, no new outbound call/dependency.
- **From-comparison co-location (Phase 2, Fix B)**: `implementation-plan` From-comparison mode (Step 0.5) and its Phase C version resolution now read the comparison's `Adoption target: vX.Y.Z` field and write the generated plan into the SAME `version_dir` as the comparison (`vX.Y.Z-adoption-<name>.md`, with matching `**Version**`/`**Filename**`/`**Seeded from**`), instead of re-resolving a fresh in-flight version; a legacy comparison lacking the field degrades gracefully to the prior resolution plus a one-line note. `catalog/commands/plan.md` documents the co-location guarantee (dispatcher stays thin). Body-only change (the skill carries no frontmatter `version:`; footer bumped 1.4.0 -> 1.5.0), so no registry sync per the "sync only if frontmatter version changed" rule; existing CI `--bundles-only` step already covers the skill. Instruction-level only.
- **Co-location drift check + reconcile (Phase 3, Fix C)**: `documentation-consistency` gains a "Comparison / Adoption-Plan Co-location" step (audit-process item + inline bash + Verification item) that flags any comparison whose seeded plan lives in a different `version_dir` and any plan whose `**Seeded from**:` comparison lives elsewhere, grandfathering `docs/archive/**` and prior-major trees by scoping to `docs/v<CURRENT_MAJOR>/`. A one-time run reported zero mismatches across the current active versions (codex-lb -> v3.14, both v3.15 reports OK; older pre-convention comparisons noted, not failed), so no reconciliation was needed. A dedicated path-filtered CI workflow (`.github/workflows/doc-colocation.yml`, `docs/**` + `catalog/skills/**`, concurrency cancel-in-progress) fails on any mismatch - the one place a docs-only misplacement is gated, since `ci.yml` skips `docs/**`. Inline bash (no `scripts/` artifact); skill footer `version` 1.0.0 -> 1.1.0, body-only (no registry sync). Verified with a throwaway fixture (flags both mismatch directions; archive grandfathered).

### Resolution

The comparison-versioning convention flaw (comparisons versioned and placed by the authoring cycle instead of the adoption target, and `/plan from-comparison` ignoring the comparison's stated target) is **RESOLVED in v3.14.2** by Fixes A-C above: a comparison now declares an `Adoption target: vX.Y.Z` and is placed by it (A), `/plan from-comparison` co-locates the seeded plan in that same version tree (B), and `documentation-consistency` plus a dedicated CI workflow flag any co-location drift so it cannot silently recur (C). Pre-Phase-1 comparisons that lack an `Adoption target:` field are handled gracefully rather than broken: Fix B falls back to the prior version resolution with a one-line note recommending the field be added, and Fix C treats a field-less comparison as a non-fatal legacy note rather than a failure. Historical and archived comparisons under `docs/archive/**` and prior-major trees are grandfathered.

### Advisory

- **Pre-existing `data/skills.json` staleness for `implementation-plan` (observed Phase 2, informational, not an open gap)**: the `implementation-plan` entry in `data/skills.json` records `"version": "1.0.0"` (the SKILL.md footer is 1.5.0), `"description": ">-"` and `"overview_l1": ">-"` (the naive frontmatter parser captured the YAML block-scalar markers rather than the folded text), and a `summary_l0` pointing at the retired `docs/versions/<vMAJOR>/<vSEMVER>/plans/` layout. This drift is pre-existing (this skill uses a footer `**Version**:` convention, not a frontmatter `version:`, so it was never synced) and was NOT introduced by this phase; it was left untouched to stay in scope. It shares a root with WN-1: the auto-generated `data/skills.json` is out of step with the strict validator's expectations for several skills. Suggested next step: fold a `data/skills.json` reconciliation for block-scalar-frontmatter skills into the same cleanup that addresses WN-1 (do NOT run the full catalog rebuild - hand-sync, per the registration rule).

### Open Items

#### Warnings

##### WN-1 - Pre-existing: 8 recent skills fail the strict `validate_skills.py` description-length check and are not allowlisted

- **Source phase**: Phase 1 (1.3b, CI wiring); pre-existing on the branch, NOT introduced by this phase
- **Plan reference**: sub-task 1.3 ("Create or update the CI job so `python scripts/validate_skills.py` runs ... with a path filter")
- **Reason**: The strict `python scripts/validate_skills.py` enforces a 250-char single-line `description` budget. 165 skills exceed it; 157 are grandfathered via `scripts/validate_skills.allowlist.json` under `--allow-existing`, but 8 recent v3.x skills are neither trimmed nor allowlisted, so even `--allow-existing` fails with 8 errors: `implementation-convergence`, `review-trapdoors`, `analyze-codebase`, `label-gated-agent-pipelines`, `setup-project`, `document-to-interactive-html`, `implement-phase`, `platform-contract-verification`. None is the skill this phase edited (`cross-project-comparison` validates clean in strict mode). To avoid a red-on-arrival CI gate over pre-existing drift outside this phase's scope, the new CI step runs `--bundles-only` (the same mode `make validate` uses), which passes catalog-wide (0 errors). This is a warning, not a blocker: the AGENTS.md "pushy description" guidance and the 250-char cap are in tension, so the cap itself may warrant review.
- **Suggested next step**: In a dedicated cleanup (a separate patch), either top up `scripts/validate_skills.allowlist.json` with the 8 offenders (or trim them via `scripts/optimize_skill_description.py`), then upgrade the CI step from `--bundles-only` to the stricter `--allow-existing` so genuinely new frontmatter/description/secret violations are caught per-PR. Separately, reconcile the 250-char cap with the AGENTS.md long-description guidance.
- **Phase 4 disposition**: kept OPEN as a deferred follow-up. It is pre-existing, out of scope for the comparison-versioning fix, and NOT a release-blocker (CI is green on `--bundles-only`). Deliberately not fixed in v3.14.2, to avoid touching 8 unrelated skills or padding the grandfathering allowlist for them inside a focused patch; carried forward for a dedicated skills.json / description-cap cleanup (see also the Advisory above, same root).

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
