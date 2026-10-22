@base-antigravity-20.md

## Windows Processes

On Windows, start every console child without a window: use one shared Python subprocess default with CREATE_NO_WINDOW, Node child_process options with windowsHide: true, or PowerShell ProcessStartInfo with UseShellExecute = $false and CreateNoWindow = $true. Prefer direct or in-process calls; Start-Process must use -WindowStyle Hidden (do not combine it with -NoNewWindow). Route .cmd shims through the same hidden launcher. Apply this to product code, tests, installers, builds, and agent helpers. Never use DETACHED_PROCESS or CREATE_NEW_CONSOLE for console programs. A deliberate exception needs nexus: console-window-ok <reason> on its launch line. Run the console-window-guard before test, installer, and build commands; use targeted checks for targeted changes.

## Surface note: Antigravity CLI (standalone)

This file is a thin alias for `base-antigravity-20.md`. The Antigravity CLI and the Antigravity 2.0 desktop IDE share a backend and on-disk conventions per the 2026-05-21 Google Developers Blog announcement (legacy migration-source path `docs/archive/v2/v2.2/antigravity-cli-probe.md`), so the `Antigravity20Integration` in `scripts/lib/integrations/antigravity.py` covers both surfaces with a single class.

This wrapper exists as a placeholder for a hypothetical future split where Google diverges the CLI from the desktop. Until then, the Antigravity 2.0 integration is the canonical Antigravity CLI integration.

- Binary / invocation: `agy --help`, `agy -p '<prompt>'` (verified 2026-05-29; the CLI ships as `agy`, not `antigravity`)
- Migration timeline: non-enterprise Gemini CLI users transition to Antigravity CLI before 2026-06-18

## User Attribution

Use the user's Git identity, never an agent identity. Before commit, tag or push, run `nexus-hub attribution check`. Follow `~/.nexus-hub/style-guides/git-attribution.md` for setup, agent-footer restrictions and publication rules.
