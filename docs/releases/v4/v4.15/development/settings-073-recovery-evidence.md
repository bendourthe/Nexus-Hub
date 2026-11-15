# Nexus Hub 0.7.3 Provider Recovery

Nexus Hub 0.7.3 groups extension controls by provider, adds current-tab Codex refresh, and replaces shared-host restarts with provider-specific recovery. This record identifies the package required for the next release and the local verification boundaries.

## Behavior

- Extensions contains separate Codex and Claude Code groups. Codex navigation and its restart action are grouped together.
- Refresh Codex Tab appears beside History in the editor toolbar. It rebuilds only the active Codex panel, replaces old listeners and coordination state, and retains its current saved conversation route. Unsent composer text may be replaced, so copy or send it before refreshing.
- Restart Codex uses the native app-server lifecycle, retains internal notification handlers, waits for initialization, then refreshes all open Codex panels. It does not restart Claude or the shared extension host. Running Codex requests may be interrupted.
- Restart Claude Code uses the native idle-boundary session lifecycle. Idle processes close immediately and resume the same conversation when next used; busy sessions restart after their current turn. Codex and the shared host remain running.
- Neither action falls back to a shared-host restart. A missing adapter reports that one window reload is needed.
- Codex's original renderer timer starts even for hidden restored panels. The adapter defers that timer until the panel is visible. A refresh disposes the previous timer, receive-message listener, coordination session and worker registration before reinitializing the panel.
- The Codex toolbar command registers before awaited adapter setup. An explicit command activation event also activates Nexus Hub when the native Codex menu requests its command during startup.

## Verification

- Full extension suite: 407 passed, one skipped, zero failed. Compilation and package-content verification passed; all 32 required payload files matched installed 0.7.3 copies in VS Code, Cursor and Antigravity, excluding installer-added manifest metadata from the semantic manifest comparison.
- Executable recovery tests cover local conversation-route validation, failed process startup, preservation of internal notification handlers, deferred hidden-panel timers, listener cleanup, current-panel refresh and native idle-boundary Claude recovery. A delayed-adapter test proves toolbar registration precedes adapter completion.
- Disposable exact-version adapter checks passed parsing, repeat installation, independent-edit preservation and exact restoration for Claude Code 2.1.318 and Codex 26.1021.22027.
- Native VS Code: inspected the grouped layout and toolbar. Refreshed saved Codex conversation `01a1ad38-3f6f-7070-8357-cf0afe78a941`, then restarted Codex and observed the same conversation reload. Native logs show app-server teardown and respawn at 09:26:23 on November 6, 2026, followed by successful resume of the same conversation. Shared extension-host PID 67648 remained unchanged during both recovery actions.
- One disposable Claude conversation received two small tool-free requests, each returning OK. Between requests, its restart action closed idle channel `tf6wifpq02` at 09:29:51. The second request resumed the same visible conversation. Codex's app-server spawn count stayed at two through the Claude-only recovery; the shared host was unchanged.
- Two explicit test-window reloads subsequently restored both conversations without a Codex renderer-timeout error. Codex came back selected, so these are reload-recovery checks, not proof of a natively hidden restored panel for the full timeout interval. Hidden-timer behavior is verified by the executable adapter regression test.
- The maintainer's working windows were not restarted. Installed Medium, Fast-off and Codex-tab preferences were not changed. Other native startup failures and future provider versions are outside this exact-version evidence.

## Delivery and Release

- Local artifact: `C:/Users/you/Documents/nx-settings073-qualification/nexus-hub-settings-0.7.3.vsix`.
- SHA-256: `5e9c2ec7ec8938942bc846d40a4c3be56ed6764bcac4e95b4fcd8607afdf8462`.
- Logs, test reports, disposable native checks and installed payload comparisons are under `C:/Users/you/Documents/nx-settings073-qualification/`.
- This supersedes the 0.7.2 shared-host restart behavior. The next release must integrate the complete `feat/settings-redesign-20261104` branch and ship extension 0.7.3 or newer with its settings engine, hook consumers and runtime adapters. Windows and POSIX installers already build and install this extension for every detected host.
- Next-release integration and publication remain pending. No remote push or release was performed for this update.
