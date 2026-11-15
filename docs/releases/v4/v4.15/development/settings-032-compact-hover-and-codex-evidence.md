# Settings 0.3.2 Delivery

This record covers the compact taskbar hover and the reproduced Codex effort behavior for the local Settings 0.3.2 update. It distinguishes saved defaults for new agents from the explicit effort held by existing Codex conversations and drafts.

## Changes

The hover has exactly five compact lines: one effort line, two lines of named guardrail on/off indicators, a session/application note and the allowed navigation links. It has no effort scale, table or blank paragraph spacing. The selector remains the only effort control.

New Codex agent is now directly beside the selector, with the message `New agents only. Existing Codex chats keep their effort.` The action rereads and reconciles configuration before opening the native composer. It does not open one after a failed read or an unresolved Codex default mismatch. The footer explains that Max and Ultra use the compatible Extra high setting for Codex.

## Reproduction

The actual installed selector was changed to Low. The saved preference and shared Codex configuration changed, and a fresh native Codex panel displayed `Light`, the client's label for that effort. The already-running Codex conversation remained at High. The initial Max preference was restored after testing and verified on disk.

In a separate real VS Code window with Settings 0.3.2 active, the inline New Codex agent button opened a composer displaying `GPT-6.1 Sol Extra High`, matching the saved Max mapping. No inference request was sent by either reproduction.

The examined Codex extension 26.1021.22027 registers commands for opening panels and creating chats, but no active-conversation effort setter. Its existing composer holds its own model settings. Therefore automatic effort changes in already-open Codex chats remain unresolved. This update improves and verifies the new-agent path; it does not claim full active-chat synchronization. Use the native model/effort picker for an existing chat. The shared mapping remains compatible with the installed CLI 0.136.0, which rejects raw `ultra`.

An initial saved-value/display mismatch was observed before Refresh. It did not persist after the actual selector flow; a specific watcher defect was not established or claimed fixed.

## Verification

- 97 focused UI/controller tests passed. The extension suite passed 309 tests with one existing skip, 98.60 percent line coverage and 91.37 percent branch coverage. After the final line-spacing adjustment, all 19 hover tests passed again, including the exact five-line contract.
- The real CLI/browser flow passed seven persisted actions and six dark/light screenshots at 320, 420 and 900 pixels, without overflow or page errors.
- The final package compiled and passed the 19-file contents check. Actual trusted and untrusted VS Code installed-host checks passed for 0.3.2.
- VS Code, Cursor and Antigravity each register Settings 0.3.2. All 19 installed payload files per editor match the final VSIX, excluding only editor-added manifest installation metadata. SHA-256: `a2a74ac13d7242b9d7cc384ff2496f429b33832b5b14a5a7764919f2b7bc7264`.
- The real installed panel and its inline action were observed. The open native hover was not captured as a screenshot; its contents and native Markdown structure were exercised through tests and the actual extension host.

Reports are retained in the sibling `settings-codex-followup-20261105-artifacts` directory. Browser evidence is under Documents `nx-settings-032-browser`, and the installed host report is under `nx-settings-032-code`. Existing windows need one reload to activate 0.3.2. No settings-engine files or guardrail choices changed, and no remote publication was performed.
