# Usage Alert Controls

This update preserves the working Nexus Hub 0.7.4 panel hierarchy and provider recovery behavior while adding shared usage-alert controls. It covers all five monitor packages, the Nexus Hub settings panel, installed artifact checks, and next-release inclusion.

## Behavior

- Warning titles are provider-specific and concise, such as Claude: Usage Alert, rather than repeating Usage Warning twice.
- Every usage warning panel dismisses after 10 seconds. Replacing a warning resets its ten-second interval; manual dismissal cancels its pending timer.
- Nexus Hub has a Usage alerts section above Version. The prominent All usage alerts control writes all five provider choices together. A mixed state and enabled count identify partial selection; individual choices remain independent until the master is used again.
- Shared choices live in `~/.nexus-hub/usage-alerts.json`, or the selected `NEXUS_HUB_HOME`. All providers default to enabled. Validated, locked writes preserve unrelated keys and reject malformed files.
- Turning a provider off closes its currently visible warning through a file watcher and prevents future warning panels and fallback urgency toasts. It does not disable usage polling, taskbar color changes, connection-error reporting or explicit command results.
- Cursor owns its watcher in the runtime disposal list, so replacing or stopping a runtime removes its listener.
- Existing effort and recovery adapters are unchanged. Ten core compiled modules match the 0.7.4 artifact byte for byte.

## Verification

- Full package suites on the final executable source: Claude 96 passed; Codex 140 passed; Copilot 310 passed; Cursor 373 passed and two skipped; Gemini 105 passed; Nexus Hub 412 passed and one skipped. Total: 1,436 passed, three skipped, zero failures. Gemini's unchanged executable source reused its full green run; later Gemini changes were documentation only.
- Tests exercise exact ten-second expiry, replacement intervals, cancel cleanup, all five readers, suppression, re-enabling, real file-watcher dismissal, mixed master state, individual writes, validation, malformed-file preservation, concurrent-write locks, and read-only refusal. Existing polling, status-bar and provider tests also passed.
- Compilation and package checks passed. Installed eight packages across the existing host assignments: Hub plus Claude/Codex/Copilot in VS Code; Hub plus Cursor in Cursor; Hub plus Gemini in Antigravity. All 349 archived payload files matched the installed copies; installer-added metadata was excluded from the semantic manifest comparison.
- A temporary, uninstalled qualification extension hosted byte-identical compiled warning providers under the exact contributed warning titles in a disposable VS Code profile. It used test percentages and made no account-usage requests. Its helper and synthetic input are outside the shipped packages.
- The native live-disable check showed Claude's warning, disabled all alerts through the actual installed Nexus Hub API, observed the watcher hide it, and confirmed that Codex's disabled warning did not open. The actual settings panel then changed Claude alone, showed 1 of 5 enabled with a mixed master, and enabled all five through the master switch.
- Native measured expiry, in milliseconds: claude 10005, codex 10005, copilot 10006, cursor 10009, gemini 10006. All five warning providers used their real timer and hide methods. The panel title Claude: Usage Alert was inspected visually.
- The original alert preference file was absent. Final preferences explicitly enable all five providers, preserving the previous enabled default. Effort and Fast preferences and the maintainer's working editor windows were unchanged. The disposable proof window was closed.
- Qualification artifacts: `C:/Users/you/Documents/nx-usage-alerts-qualification/`, including test JSON, native event receipts, timing summary, install results and final payload verification.

## Packages

| Package | Version | SHA-256 |
|---|---|---|
| nexus-hub-settings | 0.8.0 | `1d56ebcf6d44c69ff2ccb62f8c30157cb58d40c5cc1791c0c2591e4813c8ce18` |
| claude-usage-monitor | 0.10.1 | `d4f431ff87cc8f2e104a56e6b6b077d7ee0198b4bd29dc9c154ebf368c08058a` |
| codex-usage-monitor | 0.2.12 | `cbdc1a820dbfc8a9906c79785c91474f6842fa7ce30319afdec3749a9bc15553` |
| copilot-usage-monitor | 0.1.1 | `964e6ded6df894b4e9144e2ccb719e97c70d22bf9ed8a6b55823fb6a5d6e94da` |
| cursor-usage-monitor | 0.1.1 | `954c39d45bf9ddbf2d55c3836ac24b634a4cdd524e9524b451298b8937a144ec` |
| gemini-usage-monitor | 0.1.1 | `2f29dc494820eb0b0f7be5b02771aa182e6a63e9ef8c3bd51c3d9d0a1f999ca3` |

## Release Inclusion

The next Nexus-Hub release must include this complete feature branch: the preserved 0.7.4 design and recovery baseline, Hub 0.8.0 or newer, all five updated monitor packages, and their shared preference readers. The existing Windows and POSIX installers build these package sources and target the detected editors. Integration, required release checks and publication remain pending. This task performed local commits and installations only.
