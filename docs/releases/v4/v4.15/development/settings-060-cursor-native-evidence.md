# Settings 0.6.0 Cursor Native Evidence

Nexus Hub 0.6.0 adds live effort synchronization for the built-in Agent in the locally installed Windows Cursor 3.29.9 build. This record distinguishes private native qualification, installed selector verification, package delivery, restoration, and remaining platform limits.

## Changes

- The existing native adapter list covered Claude Code and Codex extensions, so installing Nexus in Cursor did not control Cursor's built-in Agent.
- The new exact-build command uses Cursor's model catalog, variant resolver, and per-session setter. It changes effort while retaining model, context size, Fast mode, and Max-mode state.
- Each Nexus revision updates open sessions. A manual native choice remains until another Nexus revision. Newly connected Agents receive the current default during polling. Recreated handles receive pending changes while manual overrides remain associated with the session ID.
- New-session defaults are projected through the native configuration reader without rewriting Cursor's persisted model preferences.
- Installation backs up both the workbench and product manifest. Only the adapted workbench checksum changes; all six integrity entries remain. Unknown builds and independent edits are preserved. Install and restore validate every planned file before mutation and undo completed replacements on a later failure.
- The existing compact panel remains. Compatibility information stays inside collapsed Details. GitHub Copilot and Antigravity native effort remain manual.

## Native Qualification

Private qualification used a separate application copy and disposable draft Agents, without sending inference requests. The tested model was Grok 4.7 with 256K context and Fast enabled.

| Action | Observed result |
| --- | --- |
| Apply Low to an open High Agent | Native picker and session configuration changed to Low; Fast remained enabled |
| Manually select Medium, then repeat the same Nexus revision | Medium remained selected |
| Switch away and return to the manual session | Medium remained selected |
| Open another Agent under Low | It received Low during the one-second synchronization interval |
| Apply a new revision with Low | The manual Medium session returned to Low |
| Apply Ultra | The native picker showed the model's advertised Extra High value; Fast remained enabled |

An initial version marked session IDs applied before hidden-tab recreation was accounted for. Native testing exposed that failure. The final version records application per handle and manual choices per session, with a regression test for recreated handles.

## Installed Verification

- The installed Cursor executable was launched from `AppData/Local/Programs/cursor`, with the packaged Nexus extension and production adapter. Diagnostic and restoration test commands were absent.
- Clicking Low in the installed Nexus panel changed the already open Agent's native picker from Extra High Fast to Low Fast.
- Clicking Extra high restored both Nexus and the open native picker to Extra high. Parsed Nexus preferences matched the pre-test baseline exactly, including all guardrail values.
- Before leaving the private test run, Cursor's stored composer default was restored and the test-created Grok 4.7 preference was cleared. Existing per-model preferences matched their baseline.
- The temporary qualifier extension was uninstalled. The Windows `cursor://` handler again points to the official installed Cursor executable.
- The production workbench SHA256 is `e5f988de7ba83d5a5be0d5ec9885016e535ac93dad05f6928c27c4e3724e3e50`. Its product checksum matches, and all six checksum entries remain.
- The restore receipt is `C:/Users/BEDOURTHE/.nexus-hub/native-ui/cursor-14f84a5e23b1d5092d64/receipt.json`.

## Checks

- TypeScript compilation passed.
- Full extension suite: 378 passed, one existing skipped test, 19 test files passed.
- Disposable Cursor installation checks passed: native JavaScript syntax, checksum consistency, retained integrity entries, idempotent installation, preservation of independent edits, exact restoration, and refusal of unknown builds.
- The existing Claude Code and Codex source-adapter qualification passed against exact original vendor sources, including JavaScript parsing, repeat installation, preservation checks, and exact restoration. Their live UI behavior was not re-tested in the user's working VS Code windows during this run.
- Package content verification passed: 28 required runtime files.
- All three editor CLIs reported `nexus-hub.nexus-hub-settings@0.6.0`. Each installed payload matched all 28 packaged files, excluding only editor-added installation metadata in `package.json`.
- VSIX: `C:/Users/BEDOURTHE/Documents/nx-cursor060-qualification/nexus-hub-settings-0.6.0.vsix`; SHA256 `fb37f85be6b5d15ed5676190dd8e41af4e40111d6bc225b9863cb50268a01285`.
- One edit-guard record was reconciled for the agent-authored `cursorProductManifest` addition in the newly created `src/cursorEffort.ts`. Its diff was reviewed and contained only that addition. This was recovery from a missed pre-write check, not a user-edit approval; no user content was replaced.

## Limits

Cursor support is qualified for this exact Windows 3.29.9 workbench hash. Future Cursor builds require qualification. Auto and models without an advertised effort parameter retain their native behavior. Higher Nexus levels map to the highest compatible native level. A response already running retains its original effort; the changed native session setting applies to its next request. Native GitHub Copilot and Antigravity effort remain manual. Guardrail hook coverage was not expanded in this change. VS Code and Antigravity need a normal window reload to activate the newly installed extension version; their running work was left open.
