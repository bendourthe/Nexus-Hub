# Settings 0.4.3 Claude Picker Evidence

This unreleased prototype was superseded by [Nexus Hub 0.5.0](settings-050-session-overrides-evidence.md). Its raw message transport did not establish native live picker synchronization. The final adapter uses Claude's normal update_state public-state and configuration path; the prototype results below are historical and are not delivery evidence.

This record covers the Claude effort picker correction developed on 2026-11-05. Read it when evaluating live effort synchronization and distinguishing automated qualification from observed native editor behavior. Topics include the seeded picker state, native readback, exact-version adapters and pending delivery.

## Cause

Unlocked native testing of Settings 0.4.2 confirmed that the same open Codex draft changed from Extra high to Medium. Claude stayed Extra high after the preference change and after answering a small test request. The native Claude frontend seeds its effort signal once and ignores later connection settings for that signal. A successful backend update was insufficient to change its visible picker.

## Correction

The exact-hash Claude frontend adapter registers native session models using weak references. Host updates call the model's existing applied-effort adoption method, preserving feature availability flags. Ultra supplies xhigh and enables Ultracode; subsequent ordinary levels disable Ultracode. Closed models are not retained. Active native channels must report the requested effort before the host broadcasts a picker update. Drafts adopt the saved default and retain normal request-time enforcement.

Both Claude files are backed up before replacement. Unsupported versions and independently modified files remain unchanged. Codex adapter behavior is unchanged from 0.4.2.

## Verification

| Check | Result |
|---|---|
| Extension suite | 366 passed, 1 existing skip |
| Statement / branch coverage | 82.90% / 80.83% |
| Native source parsing | Both vendors pass |
| Idempotent install, customization preservation, exact restore | Both vendors pass |
| Failed Claude readback | Regression test rejects without a UI broadcast |
| Seeded Claude picker adoption | Regression test covers Ultra then Medium |
| Codex same open draft on 0.4.2 | Observed Extra high to Medium |
| Claude same open conversation on 0.4.3 | Pending native UI verification |
| Codex existing conversation on 0.4.3 | Pending native UI verification |
| Visible parallel Codex tabs | Pending native UI verification |

Native UI verification is blocked because the active VS Code updater holds the startup mutex. Private test launches wait 30 seconds and exit before opening a window. The updater and working editor windows were not stopped. A private Cursor fallback initialized the extensions but displayed a mandatory account login surface, so that private window was closed without signing in. No claim of successful existing-conversation UI synchronization follows from the unit tests or source qualification.

## Artifacts

- Coverage: `C:/Users/you/Documents/nx-ui043-qualification/test-coverage.log`.
- Pinned source qualification: `C:/Users/you/Documents/nx-ui043-qualification/vendor-ui-Y6brgg/report.json`.
- Private launch diagnostic: `C:/Users/you/Documents/nx-ui042-live/startup-043.log`.

## Delivery

The 0.4.3 source, private Claude adapter and VSIX are prepared. Packaging and the 26 required package contents pass. VSIX: `C:/Users/you/Documents/nx-ui043-qualification/nexus-hub-settings-0.4.3.vsix`; SHA-256: `01bc29868831f261cb19e1ec1548405e03355e85ee45c7de2a56cdb2fa4f327f`. Installation is deferred until actual native controls can be verified. Settings 0.4.2 remains installed. Nexus effort was restored to its pre-test Extra high preference through the normal settings command after an unchanged official edit-guard check. The 0.4.3 work is uncommitted and has not been published.
