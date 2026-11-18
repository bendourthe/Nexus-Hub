# Settings Portability Repair

## Live Effort and Immediate Hover

The user confirmed Settings 0.8.7 repaired default writes on the second machine. Two remaining defects were traced: the status bar waited for the controller's dry run, writes and readback before moving the selected point; menu-only fallback builds were excluded from native effort synchronization, so successful default writes did not update their existing composers.

Settings 0.8.8 previews the effort immediately with a saving indicator, keeps that preview through intermediate model refreshes, and clears it after completion so a failed write shows confirmed state. The hover action also explicitly awaits native synchronization. Newer provider builds install native picker integration through unique semantic method and property contracts, without a version allowlist or fixed minified aliases. Missing, partial or ambiguous contracts preserve provider files. Installation syntax-checks complete modified modules and saves content-addressed originals under `~/.nexus-hub/native-ui/effort/`.

Codex's native model-settings owner is discovered from its named model-settings properties, with React and catalog aliases derived from the surrounding contract. Its native catalog supplies supported efforts. Existing local conversations use `setModelAndReasoningEffortForNextTurn`; drafts use `setModelAndReasoningEffort` with `persistAsDefault: false`. The model is preserved, remote owners are skipped, pending changes serialize, the latest revision follows an older pending update, and refused revisions are not repeatedly retried. Claude's registered native communication owners apply flags to each existing channel using `writeUserSettingsAndPush(..., true)`, verify returned effort, and send revision-aware state to its native `adoptAppliedEffort` signal. New channels receive the global revision; subsequent manual choices are preserved until the global revision changes. A response already running is not restarted.

Verification: 493 extension tests passed with three existing skips; compilation and package verification passed. Both actual local provider webview bundles patched idempotently and passed Node module syntax checks. The real isolated VS Code test drove the actual hover command High then Low into Claude's actual native setter using a controlled query channel, without credentials or user prompts. This is an integration check at the channel boundary, not an authenticated Claude session. Codex's actual backend restarted from PID 20632 to 20248 with its open tab preserved; subsequent effort broadcasts preserved that tab and backend, plus the unrelated sentinel. Receipt: `%TEMP%/nexus-native-effort-hover-20261116/receipt.json`. The signed-out host had no authenticated Claude session, and the Codex broadcast test does not prove its visible picker or an authenticated thread consumed the update. Codex next-turn selection, model mapping and revision behavior are verified by behavioral hook tests.

The final 0.8.8 VSIX SHA-256 is `410fd6ddfc6e64c6284cdbfb28ebb7381a4e30284bef5c4927986ebbd9e49e6c`. All 40 required packaged extension files were present. Trusted and untrusted real VS Code hosts passed using clean Python, retaining the 0.8.7 missing-TOML repair and untrusted-write protection. Package receipt: `%TEMP%/nexus-settings-effort-088-package-20261116/live-report.json`. Existing editor mutex/proposal messages remain on stderr; both hosts exited zero without timeout.

A further real-host check instrumented the actual installed status-bar instance and observed Medium plus its saving indicator before the settings file changed. The test initially missed the active prototype because Windows drive-letter casing loaded a second module instance; the corrected instrumentation matches cached module paths case-insensitively. Observation: `%TEMP%/nexus-settings-effort-088-preview-canonical-20261116/live-trusted.json.preview.json`. This confirms immediate updates to the real VS Code status-bar item's text and tooltip, not a native pixel-level visual inspection.

Local installation hash-verified all 40 prior 0.8.7 files into `~/.nexus-hub/backups/settings-effort-repair-20261116-0.8.7`; all 41 installed 0.8.8 files including editor metadata matched the isolated tested installation, allowing installation-specific package metadata. Delivery receipt: `%TEMP%/nexus-settings-088-delivery-receipt.json`. Both local provider views were prepared with content-addressed backups and verified idempotent; preparation receipt: `%TEMP%/nexus-settings-088-prepare-receipt.json`. Active user windows and sessions were not reloaded. A normal installation reload loads the newly installed native picker code. Authenticated conversation behavior, native visual rendering, second-machine 0.8.8 verification, integration and release remain open. No commit or remote publication was performed.

## Effort Follow-Up

The second machine's settings readback confirms internal High, Claude High with `matches_default: true` but `state: cannot-detect` solely because `version: the command is not on PATH`, and Codex Medium with `matches_default: false`. The missing standalone Claude CLI is a false warning about a successfully read default. On 2026-11-16, the requested dry run confirmed both Codex default writes were refused because `tomlkit is not installed, so this file was not written: run pip install tomlkit`. The project override was correctly skipped because Codex did not trust the project; that trust setting remains unchanged. The existing Claude session's Medium picker is separate from the saved-default readback and remains unverified.

Local changes now attach provider-specific application issues to the model, display them in Details and the hover, open the actual Nexus panel after a failed hover action, and reread settings after editor synchronization. The CLI bridge normalizes only matching effort records whose sole diagnostic starts with `version:`; parse errors and mismatches retain their failure state.

A clean Python environment with no `tomlkit` reproduced Claude JSON writes succeeding while Codex TOML writes were refused. The bridge prepares tested TOML support in a private directory only after an explicit effort save encounters that exact refusal, then retries once with the same interpreter. Dry runs do not install dependencies. The real write test exited zero, both defaults read High, the TOML comment survived, and the bare Python interpreter still could not import `tomlkit`. Receipt: `%TEMP%/nexus-effort-clean-python-20261115/receipt.json`. Dependency preparation failure reports a specific error and recovery command instead of suggesting a window reload.

Settings 0.8.7 is packaged and installed locally. All 480 extension tests passed with three existing skips, compilation passed, and package verification found all 39 required extension files. The final VSIX SHA-256 is `e6a4e774c459e421921bf84872ba5d5787b88b52cf343949a8115caffb8d42dc`. Real trusted and untrusted VS Code hosts exercised the installed package using a clean Python interpreter without `tomlkit`; the trusted hover command prepared private support and confirmed matching Medium defaults for internal, Claude and Codex, while the untrusted host preserved settings. Both hosts exited zero without timeout. Existing editor mutex/proposal messages appeared on stderr; this is not an empty-editor-log claim. Receipt: `%TEMP%/nexus-settings-effort-087-live-20261116/live-report.json`.

Local delivery backed up and hash-verified all 39 installed 0.8.6 files at `~/.nexus-hub/backups/settings-effort-repair-20261116-0.8.6`. The CLI installed and listed 0.8.7, and all 40 installed files including editor metadata matched the isolated tested installation, allowing VS Code's installation-specific package metadata. Receipt: `%TEMP%/nexus-settings-087-delivery-receipt.json`. Active user windows were not reloaded. Second-machine behavior, active Claude session picker synchronization, native visual verification, source integration and release remain open. No commit or remote publication was performed.

Investigation date: 2026-11-15. Scope: v4.15.1 Settings warnings, recovery controls, first-start Codex routing, and the missing effort meter. The second machine was not accessible; findings distinguish released-source proof from inferred machine behavior.

## Native Recovery and Labeled Hover

Current local candidate: Settings 0.8.6, superseding the 0.8.5 compact follow-up and the initial 0.8.4 repair below. The user confirmed that 0.8.5 removed the second machine's warning, but rejected its window-reload recovery fallback and unlabeled, crowded hover.

Restart actions no longer offer or execute a window reload. Existing native recovery exports remain usable. Other builds register the actual provider lifecycle owners using unique method signatures, without matching a version number or minified variable name. Codex calls its own `startCodexProcess`, retains notification subscribers, and waits for its native initialization handshake. Its existing initialization broadcast clears the frontend's fatal-error state; tabs stay open. Claude calls its existing `restartSessionsWhenIdle`: idle channels restart, while busy channels restart at their turn boundary. Missing registrations and native failures are reported without restarting unrelated extensions or claiming success.

Registration syntax-checks the modified modules before an atomic write and keeps content-addressed originals under `~/.nexus-hub/native-ui/recovery/`. It preserves ambiguous, missing, or partially changed lifecycle signatures. This removes the version allowlist from recovery, not the requirement for a compatible native lifecycle. Installation can require an initial normal reload to load newly registered code; the Restart buttons themselves never reload the window. The local provider registrations were prepared before installing 0.8.6 so the next normal reload loads them.

The hover uses a 264-by-48-pixel stepped track with all six labels beneath their points. Each 44-pixel segment and label is a command link to its own allowlisted effort value. The Markdown trust list contains only `nexusHubSettings.setEffort`, and read-only or busy states have no active effort links. Guardrails are rendered in a 264-by-66-pixel, two-column grid with three rows, full labels and aligned on/off states, avoiding the native Markdown table's collapsed spacing. The [rendered preview](settings-hover-labeled-preview.png) is 282 by 188 pixels with representative styling; it is not a native VS Code screenshot.

Final extension verification: 471 tests passed across 29 files, with three existing skips. Compilation and package-content checks passed. The packaged build passed the isolated trusted and untrusted VS Code checks, including actual effort-command persistence and compact-mode toggling. The six rendered hover links are contiguous, have valid command arguments, and retain their labels. Actual native hover clicking and appearance remain unverified because native computer access is unavailable.

The final VSIX SHA-256 is `d7e4562b158a49fdd0057f68bcf3fd0f139d3e1693e3c754e2e6f4e47261ef37`. All 38 installed extension files match it, excluding only VS Code's added package metadata. Final packaged-host receipt: `%TEMP%/nexus-settings-recovery-final-package-20261115/live-report.json`. Codex tab refresh also no longer offers a window reload: when native panel refresh is unavailable it offers a confirmed Codex-only restart.

Native boundary verification: `scripts/native-recovery-live.js` copies the installed provider packages into a disposable extension directory, uses a scratch home, and submits no user prompts. In the final run, actual Codex backend PID 29684 changed to 21292, completed initialization, and remained initialized after a one-second stability check. The existing Codex tab, extension host PID 41244, and unrelated sentinel PID 33304 remained running. Claude's real session owner registered and its selected restart action returned zero sessions; no active authenticated Claude session existed in the scratch host. Idle/busy Claude behavior and isolation from Codex are verified by lifecycle tests, not by an active authenticated Claude restart. Receipt: `%TEMP%/nexus-provider-recovery-final-20261115/receipt.json`.

Local delivery: both installed provider modules received their backed-up lifecycle registrations. All 38 installed Settings 0.8.5 files were backed up and hash-verified under `~/.nexus-hub/backups/settings-native-recovery-20261115-0.8.5`; the CLI installed and listed Settings 0.8.6. Current user windows were not reloaded. Source integration, release, the second machine, an active Claude restart, and native visual verification remain open.

## Compact Follow-Up

Current local candidate: Settings 0.8.5. This supersedes the initial 0.8.4 repair described below. The source remains on `fix/settings-portable-recovery`; no integration or release is claimed.

- The hover shows the selected effort name, a 132-by-12-pixel track, and five guardrails in one horizontal table. The previous track was 264 pixels wide. The selected name remains readable text rather than six tiny labels.
- The hover contains no command links, compatibility paragraphs, routine connection notes, or redundant Nexus heading. Status-bar clicking still opens the Nexus panel; compact/full status-bar labels remain available.
- Unsupported optional Claude composer adapters now return an unavailable capability without attempting a vendor-code patch or raising an installation error. Codex's menu-only fallback also completes without a compatibility error. The protocol bridge continues to own live effort updates; no unsupported composer update is claimed.
- The extension supplies the installed Claude extension's bundled executable to its settings subprocess. A separately installed CLI and a fresh editor PATH are no longer prerequisites for this version probe. The parent environment is unchanged, and executable locations come from installed extensions, never the workspace.
- The harness resolver also reports readable effort configuration directly when a CLI version probe is unavailable. Invalid JSON still returns `cannot-detect`; other version-sensitive controls keep their existing checks. This engine change is source for the next release; the standalone VSIX uses bundled-executable discovery to work with the currently installed engine.
- Actual failed updates and unreadable settings retain a short attention message. Failure details are available inside the panel's collapsed Details section. Optional adapter absence is not an error to hide or a promise that a native composer changed.

Verification: 463 extension tests passed with three existing skips; 406 settings-engine tests passed with three existing skips. Compilation and package-content verification passed. The final VSIX contains 37 extension files plus two package metadata files, with no test logs. Its SHA-256 is `a629bb901e6351a77c857b70bce18a92cb0edea6c582d92dcc533196fe24725e`.

A real settings subprocess was exercised against a scratch copy of the installed harness, with no standalone Claude CLI on PATH and the actual Claude 2.1.325 bundled executable. Setting and reading Medium returned `state=in-effect`, `matches_default=true`, and the correct detected version. Receipt: `%TEMP%/nexus-settings-native-cli-20261115/receipt.json`. Both trusted and untrusted isolated VS Code hosts installed and exercised the final 0.8.5 VSIX successfully. Receipt: `%TEMP%/nexus-settings-compact-live-20261115/live-report.json`.

The [rendered preview](settings-hover-compact-preview.png) measures approximately 321 by 125 pixels with a 132-by-12-pixel track and two table rows. It uses the actual generated Markdown and SVG with representative dark-theme styling; it is not a native VS Code screenshot. Native computer access remains unavailable. Actual native rendering and the second machine remain unverified.

Local delivery: all 38 installed 0.8.4 files were backed up and hash-verified at `~/.nexus-hub/backups/settings-compact-20261115-0.8.4`. The CLI installed and listed `nexus-hub.nexus-hub-settings@0.8.5`. Existing user windows were not reloaded. No additional preservation accept events occurred during this follow-up.

## Findings

| Symptom | Evidence | Cause or limit |
| :--- | :--- | :--- |
| Effort meter disappeared | Commit `2fdf2685530db9a408be1f2857ee447680637328` is reachable only from `feat/settings-effort-meter`, not from v4.15.1. The tag's statusBar.ts still returns the text label. | The local meter change was never integrated into the release. The installer force-installs the extension built from released source. |
| Version-specific recovery errors | Released vendorUiPatch.ts pins Claude 2.1.318 and Codex 26.1021.22027 by version and bundle hashes. Released extension.ts requires their injected recovery exports. | Codex 26.1111.21308 and Claude 2.1.325 have no matching recovery adapter. v4.15.1 added a readable rejection, not universal recovery. |
| Codex opens in the sidebar on first startup | codexTabManifest changes the vendor's editor/title contribution on disk during activation. VS Code has already read its contributions. | The native icon's rerouting needs a subsequent window reload. The existing Nexus command already calls chatgpt.newCodexPanel when the saved preference selects tabs. |
| Settings link appears ineffective | The open command is registered before the Settings view provider, with two awaited adapter installations between them. | Slow setup leaves the command available before its view is registered. This path is reproduced by a pending-setup regression test; the exact second-machine failure is not confirmed without its logs. |
| Generic warning | Released statusBar.ts collapses preference conflicts and live-connection errors into "Review application in Settings". | The hover discards the reason and does not identify the Nexus panel. |
| Different behavior on this machine | Its installed Nexus VERSION read 4.15.0, its Settings extension was 0.8.3, and its installed Codex manifest already contained Nexus routing. Both provider versions match the reported second-machine versions. | Installed product version, extension version, and prior adapter state can differ. Provider version alone does not explain the machine difference. |

## Initial Repair

Branch: `fix/settings-portable-recovery`, based on `origin/develop` at `da1dfd4a7`. Settings extension version: 0.8.4. No Nexus-Hub release version was changed.

- Restore the existing six-segment effort meter, lowercase level, and compact/full presentation.
- Replace the hover's inline guardrail groups with a two-column Markdown table.
- Remove the hover's "New Codex agent" link and trust only "Open Nexus Hub".
- Identify effort overrides, unreadable settings, adapter errors, and reload requirements in the hover.
- Register the Settings view before awaiting native setup; open its named container before focusing its view.
- Select recovery by available capability. When targeted recovery is unavailable or fails, offer "Reload Window" and explain that all extensions in that window restart and requests may be interrupted. Cancellation leaves them running.
- Offer an explicit reload after native toolbar installation, including when no effort or Fast preference exists.

VS Code's public Extension API has activation but no individual-extension restart operation. This repair provides a version-independent window-reload fallback; it does not claim version-independent individual-provider restart. Existing native effort/Fast UI patch recipes remain build-specific. The native Codex icon still requires a reload after its first manifest rewrite. These are material limits, not verified removals of every adapter dependency.

## Initial Verification

- TypeScript compilation passed.
- All 28 Settings test files passed: 461 tests passed, three skipped. The skipped tests are not counted as passing.
- Package verification passed: 37 files, all 37 required runtime files present. VSIX contains 39 entries including its two package metadata files; temporary logs were removed before the final package.
- The final VSIX was installed in isolated trusted and untrusted VS Code hosts through scripts/live-check.js. Both hosts exited 0 without being killed, opened the Settings view, toggled compact mode, and produced ready models. Trusted mode saved Medium effort and observed the meter summary. Untrusted mode preserved preferences.
- Recovery fallback and tab-command routing are covered by regression tests. Actual restart of installed Codex/Claude processes was not exercised, to avoid interrupting active work.
- Native computer access returned "Computer Use native pipe is unavailable". Native hover alignment, actual hover-link clicking, and the second machine are not visually verified.
- Isolated VS Code startup logged an existing mutex message and built-in proposed-API warnings; the host tests still completed successfully. This is not a claim of an empty editor error log.

Final host receipt: `%TEMP%/nexus-settings-portable-final-20261115/live-report.json`. Source test log: settings-tests-final.log in this worktree. Local artifact: extensions/nexus-hub-settings/nexus-hub-settings-0.8.4.vsix.

## Initial Delivery

The installed 0.8.3 extension was copied to `~/.nexus-hub/backups/settings-portable-recovery-20261115-0.8.3`; all 38 source files matched their backup SHA-256 hashes. The VS Code CLI installed 0.8.4 and listed `nexus-hub.nexus-hub-settings@0.8.4`. Existing windows were not reloaded; they need a reload to activate it. The installed Nexus VERSION remains unchanged.

Two test-file preservation records exceeded the helper's two-minute check-to-record window. Official diffs were inspected and contained only this session's test edits; those own edits were re-recorded with accept. No user edit was adopted or overwritten, and no user consent event is claimed.

## Open Work

- Visually verify the labeled hover and its effort links after reloading this machine into 0.8.6.
- Install the supplied 0.8.6 VSIX on the second machine and verify its first-start, provider-only restarts, hover links, and full guardrail labels. Complete the initial registration reload if setup requires it; the restart actions must not reload the window. Capture the exact row detail and extension-host errors if a genuine failure remains.
- Integrate the local source repair through develop and include it in an authorized release. No commit, push, PR, or release was performed in this task. Reinstalling v4.15.1 will replace the local repair.
- Verify an active authenticated Claude session restart; the disposable signed-out host had no active channels. Retain native idle-boundary behavior and preserve other providers and the extension host.
