# Settings 0.4.2 Native UI Evidence

This record covers the native effort UI adapters and Codex editor-tab fix developed on 2026-11-05. Read it when reviewing installation, investigating stale effort controls or restoring vendor originals. Automated native checks, source installation and visible editor verification are separate results.

## Cause

The stdio bridge could apply native effort while Claude's cached settings and Codex's composer state remained stale. Native acknowledgments did not prove that these visible controls changed. The prior "Effort confirmed" panel text overstated that evidence.

The Codex toolbar called its sidebar command. Its separate new-panel command also opened a fixed custom-editor URI, so repeating that command reused an existing panel. Both behaviors prevented the requested parallel-tab workflow.

## Changes

- Claude Code 2.1.318: an exact-hash adapter exposes its existing settings apply, readback and normal state-push method. Ultra supplies `effortLevel: xhigh` and `ultracode: true`.
- Codex 26.1021.22027: an exact-hash adapter calls the composer's native model-and-effort setter with its current model. Model-advertised capabilities determine the effort mapping. Draft selection does not persist an account-level model preference.
- The Codex editor-title menu calls its native new-panel command with the vendor icon. New panel URIs keep the normal `/extension/panel/new` path and add a unique query value so VS Code creates distinct documents.
- Repeated UI synchronization reaches open and newly activated vendor views. An unsupported build or independent file customization is preserved. Native originals and restore receipts are stored under `~/.nexus-hub/native-ui/`.
- The Settings panel removes the replacement-agent workaround and native acknowledgment-based "confirmed" text. Compact hover sections and narrow-panel labels are retained.

## Verification

| Check | Result |
|---|---|
| TypeScript compilation | Pass |
| Extension regression suite | 364 passed, 1 existing skip |
| Statement / branch coverage | 83.03% / 81.02% |
| Actual pinned vendor-source parsing | Both vendors pass |
| Disposable installation and repeat installation | Both vendors pass |
| Independent customization preservation | Both vendors pass |
| Exact restoration and redirected-receipt rejection | Both vendors pass |
| Native relay changes without model prompts | 12/12 pass; zero model turns |
| Actual native adapter activation | Both APIs initialize in a trusted isolated VS Code host |
| Nexus Medium then Extra high through the real extension command | Both complete without adapter errors; original Extra high preference restored |
| Native repeated Codex new-panel command | Actual editor tab groups contain Claude Code plus two distinct Codex tabs |
| Visible existing Claude and Codex effort controls | Open; Windows locked during CUA verification |

The two vendors were first tested in disposable source copies. The native host used private extension copies and separate VS Code user data. It did not restart the user's two working editor windows. Before the unique-URI correction, the same test reported only one Codex tab; after correction it reported two.

## Artifacts

- Extension tests and coverage: sibling artifact directory `settings-codex-followup-20261105-artifacts/coverage-042-final.log`.
- Exact-source adapter qualification: `settings-codex-followup-20261105-artifacts/vendor-ui-31fvly/report.json`.
- Native relay exercise: `C:/Users/you/Documents/nx live effort 042 proof/native-report.json`.
- Native API and tab reports: `settings-codex-followup-20261105-artifacts/native-ui-042-host/medium-api-result.json`, `extra-high-api-result.json` and `distinct-codex-tabs-result.json`.

## Delivery

Settings 0.4.2 is installed and registered in VS Code, Cursor and Antigravity. Twenty-three runtime/static files in each installed extension match the packaged bytes; the packaged manifest version and renamed license also verify. Package SHA-256: `14cf13dc092fafa6c8e45c99a98e876704f923dfbd1a9cd386332b0e2f57f617`.

The installed VS Code Claude and Codex adapters and all four original-file backups verify against their receipts. Receipts are `C:/Users/you/.nexus-hub/native-ui/claude-a01c7b1b963f44184b33/receipt.json` and `C:/Users/you/.nexus-hub/native-ui/codex-69360d8e1cf336febe27/receipt.json`. Installation and byte-verification reports are `settings-codex-followup-20261105-artifacts/install-042.json`, `native-ui-042-install.json` and `package-042-receipt.json`.

The private test host was stopped after its checks. The user's two working editor windows were not restarted. Visible live-effort verification remains open and must not be inferred from successful native protocol calls, queued webview messages or these unit tests. The installed update requires one editor restart to load the native adapters and menu.

## Restoration

`out/vendorUiInstall.js` exports `restoreVendorUi(receiptPath)`. It validates the receipt location, vendor version, original hashes and exact adapter output before restoring. It refuses to overwrite a vendor update or independent customization. The original vendor files are not bundled into the Settings VSIX.

## Open Verification

After loading the update in an unlocked editor, observe the same existing Claude and Codex conversation controls and an unsent Codex draft across repeated Nexus effort changes, including Ultra/Ultracode. Check the native toolbar button and parallel-tab layout visually. This gate remains open until the actual controls are observed changing without replacement tabs.

## Follow-up

The final [Nexus Hub 0.5.0 delivery](settings-050-session-overrides-evidence.md) supersedes the prototype below and records observed existing-conversation picker changes, manual overrides, explicit reapplication and installed payload verification.

Unlocked verification later confirmed a Codex draft changed from Extra high to Medium, but Claude remained Extra high even after a real request. The Claude picker deliberately seeds its effort signal once, so a backend settings push alone was insufficient. The [0.4.3 correction](settings-043-claude-picker-evidence.md) records the additional frontend adapter and its remaining verification gate.
