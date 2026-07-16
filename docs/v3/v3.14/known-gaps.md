# Known Gaps - v3.14

**Project**: Nexus-Hub
**Status**: in progress - Phases 1-2 of 6 complete on `feat/codex-lb-adoption`; Phases 3-6 pending
**Last updated**: 2026-07-16 (Phase 2 post-phase reconciliation)

> **Prior-version ingest**: the open v3.13 items (presentify DF-1..DF-5, WN-1/2, MT-1) are unrelated to this feature set and do not carry in. HO-1 (flat/nested skill-name collision across skill layouts) now ENGAGES as of Phase 2, which ships the new `review-trapdoors` catalog skill; it must be re-checked by the Phase 6 dry-run install (verify no flat/nested same-`name` collision for `review-trapdoors`).

## v3.14.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |
| Hand-offs (HO) | 1 | 0 |

### Capabilities added this version

- **Codex Usage Monitor (Phase 1)**: the `claude-usage-monitor` VS Code extension (independently versioned 0.6.2 -> 0.7.0) generalized behind a `UsageProvider` interface, with a second provider for Codex (ChatGPT / OpenAI). The Codex provider reads the local Codex app OAuth token (from `usageMonitor.codex.authPath`, `CODEX_HOME/auth.json`, or `~/.codex/auth.json`) and fetches account usage from the undocumented `chatgpt.com/backend-api/wham/usage` endpoint, mapping the primary and secondary rate-limit windows onto the session and weekly metrics plus plan type, credits, and additional-limit rows. The whole status-bar / tooltip / dashboard / warning UI is reused; recommendations are reframed for Codex (throttle, wait-for-reset, rotate-account) since Codex has no cheaper model tier. A `usageMonitor.provider` setting, a "Usage: Switch Provider" command, and a settings-panel selector switch providers. Fail-soft throughout; the Claude path is byte-for-byte unchanged; the single outbound call goes only to the user's own account. Provider logic, the Codex payload mapper, the error resolver, and the Codex recommendation branches are covered by a 35-test Vitest suite. No catalog skill, command, metadata, installer, or base-template was touched.
- **Skill-native review/verification cluster (Phase 2)**: a new `review-trapdoors` code-review skill plus a `review-trapdoors.md` style guide (a curated, project-specific recurring-blocker convention applied before review or a review-ready claim); a PR/CI-state evidence example folded into `verification-before-completion` (verify review/CI state against the authoritative current-head source; missing-review is not approval); and a merge-readiness contract extending `quality-gate-definitions` (a `merge-ready` composite gate + a `merge-readiness-contract.md` style guide documenting the configurable collaborator rules). C3 and C6 are body-only edits (no registry change); `review-trapdoors` is registered in all three metadata files. Catalog: 267 skills. Count references reconciled to 267 across skills.json, `data/SKILL_INDEX.md`, and AGENTS.md (the SKILL_INDEX total line had been stale at 265).

### Advisory

- Switching the monitored provider (`usageMonitor.provider`) clears the previously cached usage data by design, since it belongs to a different account with different semantics. The status bar then shows the empty state until the first fetch for the new provider completes.

### Open Items

#### Deferred

##### DF-1 - Exact Codex-app credential location and field shape are unverified

- **Source phase**: Phase 1 (1.2)
- **Plan reference**: sub-task 1.2 ("CONFIRM the exact path and field names at implementation time"); Phase 6.2 records this as a deferred confirmation
- **Reason**: This build targets the ChatGPT Codex **app** (not the open-source Codex CLI, per the user's clarification), and the app's on-disk credential path and field names could not be verified from this environment. The provider therefore reads a **configurable** path (`usageMonitor.codex.authPath`, then `CODEX_HOME/auth.json`, then `~/.codex/auth.json`) and parses **shape-tolerantly** (nested `tokens.{access_token,account_id}` or flat `{access_token,account_id}`, plus camelCase), failing soft when nothing usable is found.
- **Suggested next step**: Confirm the real Codex-app credential path and field names against a live install; set the probed default accordingly (or document the setting prominently). The configurable-path + fail-soft design means a wrong default is user-correctable without a code change.

##### DF-2 - wham/usage is an undocumented endpoint (durability risk)

- **Source phase**: Phase 1 (1.3)
- **Plan reference**: Phase 1 stability gate ("fail soft when the undocumented endpoint is unavailable"); Phase 6.2 durability note
- **Reason**: `chatgpt.com/backend-api/wham/usage` is an internal, undocumented ChatGPT backend endpoint that OpenAI can change without notice (the same fragility class as the Claude monitor's dependency on the Anthropic usage endpoint, arguably higher because it is reverse-engineered). The mapper validates defensively and any parse failure, HTTP error, timeout, or missing field yields the fail-soft "usage unavailable" state.
- **Suggested next step**: None guaranteeable in code; monitor for breakage. The fail-soft behavior and the manual-entry fallback contain the blast radius.

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
- **Suggested next step**: In Phase 6.3, add a path-filtered `extensions/claude-usage-monitor/**` job that runs `npm ci`, `npm run compile`, and `npm test`, mirroring the concurrency-cancelled, cached pattern of the existing workflows.

#### Hand-offs

##### HO-1 - Verify no flat/nested skill-name collision for `review-trapdoors` at install

- **Source phase**: Phase 2 (2.1)
- **Plan reference**: Prior-Version Known-Gaps Ingest (v3.13 HO-1); Phase 6.4 dry-run install
- **Reason**: Carried forward from v3.13. The flattening migration means a same-`name` skill can collide across flat and nested install layouts. Phase 2 ships the first new catalog skill of this release (`review-trapdoors`), so the collision check now applies to it.
- **Suggested next step**: The Phase 6.4 throwaway dry-run install must confirm `review-trapdoors` lands flattened at each platform's skill path with NO flat/nested same-`name` collision.
