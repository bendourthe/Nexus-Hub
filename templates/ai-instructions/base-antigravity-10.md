@base-google-shared.md

## Windows Processes

On Windows, start every console child without a window: use one shared Python subprocess default with CREATE_NO_WINDOW, Node child_process options with windowsHide: true, or PowerShell ProcessStartInfo with UseShellExecute = $false and CreateNoWindow = $true. Prefer direct or in-process calls; Start-Process must use -WindowStyle Hidden (do not combine it with -NoNewWindow). Route .cmd shims through the same hidden launcher. Apply this to product code, tests, installers, builds, and agent helpers. Never use DETACHED_PROCESS or CREATE_NEW_CONSOLE for console programs. A deliberate exception needs nexus: console-window-ok <reason> on its launch line. Run the console-window-guard before test, installer, and build commands; use targeted checks for targeted changes.

## Surface: Antigravity 1.0 (Google IDE, pre-I/O 2026 release)

This file deploys to `~/.gemini/antigravity/rules.md` (global) or `<project>/.gemini/antigravity/rules.md` (workspace) and is consumed by the original Antigravity IDE released ahead of Google I/O 2026. Antigravity 1.0 shares the `~/.gemini/` root with Gemini IDE and Gemini CLI but writes to its own `antigravity/` subdirectory.

- Binary / invocation: in-IDE only (Antigravity 1.0 desktop)
- Customizations: surfaced via the IDE's Customizations menu; the on-disk layout uses `rules_library/` for rule sets and `global_workflows/` for saved prompts
- Hooks: not supported on the 1.0 surface (see Antigravity 2.0 for hook support)
- Migration note: Antigravity 1.0 is superseded by Antigravity 2.0 + CLI for new users; this template remains supported for existing 1.0 installs

## User Attribution

Use the user's Git identity, never an agent identity. Before commit, tag or push, run `nexus-hub attribution check`. Follow `~/.nexus-hub/style-guides/git-attribution.md` for setup, agent-footer restrictions and publication rules.
