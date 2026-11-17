# Settings Restore Split

Summary: investigation of why a Claude Code tab and a Codex tab that were split side by side can reopen merged into one editor group after VS Code restarts, and the opt-in Nexus Hub Settings 0.8.9 setting `nexusHubSettings.restoreAgentSplit` that restores the split through public VS Code APIs. Read it to see what was reproduced, what was not, which vendor code paths are the likely cause, and what remains unverified on the maintainer's real setup. Work branch: `feat/settings-restore-split`, based on `origin/develop` at `85180a89d`. Nothing was pushed, installed into the live profile, or changed in either vendor extension.

## Question

After closing and reopening VS Code, a window that had a Claude Code tab and a Codex tab split side by side reopens with both tabs in one editor group. The maintainer's settings are `window.restoreWindows: preserve` and `files.hotExit: onExitAndWindowClose`. Claude Code is `anthropic.claude-code` 2.1.326 and Codex is `openai.chatgpt` 26.1111.21308.

## Method

Every run used a throwaway `--user-data-dir`, `--extensions-dir` and home, with read-only copies of the two installed vendor extensions (the Codex copy already carries the Nexus Hub toolbar patch, as installed). Ordinary VS Code windows were used, not an extension test host, so VS Code's own shutdown, storage flush and window restore ran. A small probe extension logged `window.tabGroups` on every tab change and on a timer, opened the layout, and ended the window with a command. No process was found by name or command line: each window was started by the script and ended by its own process id. The real profile, sessions and `~/.nexus-hub` were never opened.

The layout under test: Claude Code opened with `claude-vscode.editor.open`, then Codex opened beside it with `vscode.openWith(openai-codex://route/extension/panel/new, "chatgpt.conversationEditor", { viewColumn: Beside })`, the same call Nexus Hub Settings uses.

## Results

| Run | Close method | Active group at close | Result after reopening |
| --- | --- | --- | --- |
| 1: text editor, Claude, Codex (3 groups) | `workbench.action.quit` | Codex | All three groups restored in order |
| 2: Claude, Codex (2 groups) | `workbench.action.closeWindow` | Codex | Claude group 1, Codex group 2 restored |
| 3: Claude, Codex | `workbench.action.quit` | Claude | Claude group 1, Codex group 2 restored |
| 4: as 3, repeated | `workbench.action.quit` | Claude | Same |
| 5: as 3, process ended abruptly (taskkill on its own process id) about 15 seconds after the last change | process id kill | Claude | Codex tab and its group missing; Claude restored |

Finding: a clean close and reopen did not merge the tabs in any variant. VS Code restored both groups, and both vendor extensions restored their own tab into the group VS Code had saved. The only loss seen was run 5, where an abrupt end left the saved layout one change behind (no Codex tab at all, not a merge). The merge the maintainer sees was therefore not reproduced here, and its cause is not confirmed.

## Vendor Code Paths That Can Merge Tabs

Both are read from the shipped minified bundles. They are explanations to test, not observed causes.

- **Codex reopens restored tabs without a group.** On provider construction, `ensureRestoredConversationTabsResolved` walks `tabGroups` and, for every `TabInputCustom` or `TabInputText` whose resource scheme is `openai-codex`, runs `vscode.openWith(uri, "chatgpt.conversationEditor", { preserveFocus: true, preview })` with no `viewColumn`. That opens in the active group. When the tab already exists as a resolved custom editor, VS Code reveals it where it is (runs 3 and 4, where the Claude group was active, show no merge). If the restored tab is unresolved or dropped at that moment, the same call lands in whichever group is active, which would put Codex in the Claude group and leave the other group empty, and VS Code closes empty groups by default.
- **Claude Code reopens tabs it considers lost.** `watchForLostTabs` and `reopenLostTabs` recreate a tab in the group where it stopped responding. This code reopens into the same column, so it can reorder a group but is not by itself a merge. Claude also locks the group it creates (`lockEditorGroups`, on by default), and a locked group refuses other editors, which changes where a placeless open lands.

Neither path was observed to merge tabs with the fixtures available here, which have no signed-in sessions. Real sessions give each tab a conversation resource and saved state, a slower provider start, and a different restore timing, none of which could be recreated without credentials.

## Public API Result

A public path exists to repair the layout without touching the vendors. The Tab Groups API (`window.tabGroups`, `TabInputWebview`, `TabInputCustom`) reports which group holds which agent tab, and built-in editor commands move a tab. The Claude Code tab is a webview panel with view type `mainThreadWebview-claudeVSCodePanel`; the Codex tab is a custom editor with view type `chatgpt.conversationEditor`. The Tab Groups API cannot select or move a tab directly, so the move is done by focusing the group (`workbench.action.focus<Nth>EditorGroup`), selecting the tab by index (`workbench.action.openEditorAtIndexN`, positions 1 to 9), checking through the API that the intended tab is now active, then `workbench.action.moveEditorToRightGroup`, which creates the group on the right when it does not exist. Moving keeps the same editor, so Claude's webview and Codex's conversation are not recreated.

## Approach

`src/agentSplit.ts` adds `nexusHubSettings.restoreAgentSplit` (application scope, default off).

- It records `{ apart, rightKind }` in workspace storage whenever both agents have a tab, on every tab change, only in a trusted workspace. Recording on change covers shutdown, because the last change is the last state. Recording needs both agents present, so tabs closing during shutdown cannot erase it.
- During startup it records nothing until it has made its one decision, so a merged restore cannot overwrite the remembered split.
- Once both agents are present and the tabs have not changed for three seconds (or after 60 seconds, whichever applies), it checks whether every agent tab is in one group while the remembered layout was split. If so it moves the last tab of the remembered right-hand agent into its own group on the right, then returns focus to the original group. Otherwise it does nothing.
- It never closes or reopens a tab, never moves a tab it could not first confirm as active, and skips positions beyond 9.

## Verification

- Unit tests (`test/agentSplit.test.ts`, 16 tests) cover layout description, merge detection, the settle delay, no overwrite during startup, a user's own merge being respected, disabled and untrusted behavior, give-up, a failed move not stopping recording, disposal, and the real-host adapter's tab classification, setting, storage and move safety checks. The full Settings suite is green at 509 passed and 3 skipped (the 493 baseline plus 16), with `agentSplit.ts` at 100 percent line coverage.
- `scripts/restore-split-live.js` runs the real Claude Code and Codex extensions with the packaged 0.8.9 `.vsix` in a private profile. The setup window builds the split and lets Settings record it, turns the setting off, merges the tabs, and quits. The profile is copied. The window with the setting on started merged, and 3.0 seconds after the tabs appeared ended as `claude | codex` with Claude's group focused again. The control window with the setting off ended as `claude+codex`, unchanged.
- Packaged trusted and untrusted host checks (`scripts/live-check.js`) passed with clean Python 3.11; both hosts exited zero.

## Not Verified

- The merge itself was not reproduced, so the restore is verified against a merge produced by the test (tabs merged by command before shutdown), not against the maintainer's real merge.
- Authenticated sessions: Claude Code with a real conversation, and Codex with a conversation resource (`openai-codex://route/local/<id>`), were not tested.
- The maintainer's installed extensions, other windows, multi-root workspaces and the Nexus Hub native adapters running together were not exercised; the live check used a private home, so the Nexus Hub adapters did not see the real one.
- Whether a vendor re-merges the tabs after Settings has moved one is untested; Settings acts once.
- Closing through the window close button on a machine with several windows, and Windows sign-out or update restarts, were not tested.
