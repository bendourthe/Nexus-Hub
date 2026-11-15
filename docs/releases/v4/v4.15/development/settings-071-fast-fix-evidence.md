# Nexus Hub 0.7.1 Fast Mode Fix

This record covers the VS Code Fast synchronization regression, repeated model-setting errors, the single divider below Fast mode, local installation, and restored preferences. The earlier 0.7.0 draft-tab checks did not establish correct existing-conversation behavior.

## Causes and Corrections

- Codex draft tabs and existing conversations have different native update contracts. Existing conversations now use the next-turn setter with nested `threadSettings.serviceTier`; writable drafts use their native draft setter. Empty restored tabs wait until a conversation or writable draft exists. A rejected revision is attempted once, with a changed default or Apply to all allowing a new attempt.
- Claude's old Fast payload was put in model configuration while the listener read session state. The replacement uses the native session-scoped `apply_flag_settings` request, then native initialization readback. Only the returned `fast_mode_state` updates the matching channel's indicator. Confirmed channel states remain available until the composer consumes them. Native model, account, usage-credit and managed-policy checks remain in the native engine.
- Claude startup receives an explicitly configured shared Fast value through its launch settings. Unset speed preserves native settings; speed alone preserves native effort. The effort proxy now distinguishes its first startup handshake from later metadata refreshes, preserving subsequent session overrides.
- Native providers update independently with a bounded wait and one outstanding request per provider. A stalled Claude request cannot prevent Codex from receiving changes or create an accumulating retry queue.
- The Fast row no longer has a bottom border. The Details border is the single line below it.

## Verification

- Fresh final suite: 395 passed, one skipped, zero failed. Compilation and package-content checks passed.
- Regression tests cover native Claude flags and confirmed per-channel state, manual state preservation, both Codex request shapes, rejected-revision suppression, draft readiness, independent launch settings, repeated metadata initialization, and a stalled provider without duplicate requests.
- Disposable Claude Code 2.1.318 and Codex 26.1021.22027 adapter checks passed parsing, repeat installation, independent-edit preservation, exact restoration, and redirected-receipt rejection.
- Native Claude protocol probes changed Fast off/on/off within the same disposable process and read the actual state back from initialization. These metadata-only probes did not submit model prompts.
- One disposable Claude conversation was created with `Reply exactly OK. Do not use tools.` and returned `OK`. It and a saved Codex test conversation remained open during the installed-build off/on checks. Neither conversation was replaced to apply each change.
- In the final installed build, both existing conversations switched to Standard and back to Fast. Claude's composer was focused for both observations: its accessible `Fast mode enabled` indicator was absent when off and present when on. Codex's native lightning indicator also disappeared and reappeared. Both native effort controls remained Medium.
- Final verification windows 4 and 5 recorded zero `Failed to update model and reasoning effort` entries. The last such error in the earlier candidate's window 3 was at 07:26:31.706 on November 6. No repeated model-setting toast appeared during the final checks.
- The panel was visually inspected with one divider beneath Fast mode. Cursor's native workbench adapter was unchanged, and all installed native files matched their receipt hashes.
- All 30 packaged files matched the registered 0.7.1 copies in VS Code, Cursor and Antigravity. Installer-added manifest metadata was excluded from the semantic `package.json` comparison.

## Restoration and Scope

The original `session-defaults.json` was restored byte-for-byte with Fast on. Nexus effort remains exactly `medium`. Claude's native user settings still have no `fastMode` key. No billing setting, managed restriction or permission guardrail was changed. The test-only diagnostic extension only read the installed status API and was loaded through a development-host path; it was not installed or included in the VSIX. The diagnostic window was closed after verification. Working user windows were not reloaded or closed.

The final VSIX SHA-256 is `4f6c0f72cbb500be79156e03a6ff3dce1cb23f9310a369c75aaf7ad97768a18c`. Reports and the package are under `C:/Users/you/Documents/nx-settings071-qualification/`, including `final-delivery-2.json`, `final-payloads-2.json`, `final-tests-2.json`, and the `release-checks` reports. The primary checkout retained its 34 unrelated changed files. No edit-guard baseline acceptance was used in this run.

## Open Items

Working VS Code windows must reload to unload 0.7.0's in-memory retry loop. A separate native Codex renderer-ready timeout for restored inactive blank tabs was still observed; it is the previously tracked startup issue, not a repeated model-setting failure. No general Codex startup-reliability claim is made. Cursor's native Fast flow was not rerun because its adapter was unchanged and the user confirmed it worked; this run specifically qualified the VS Code fixes.
