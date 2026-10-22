@base-google-shared.md

## Windows Processes

On Windows, start every console child without a window: use one shared Python subprocess default with CREATE_NO_WINDOW, Node child_process options with windowsHide: true, or PowerShell ProcessStartInfo with UseShellExecute = $false and CreateNoWindow = $true. Prefer direct or in-process calls; Start-Process must use -WindowStyle Hidden (do not combine it with -NoNewWindow). Route .cmd shims through the same hidden launcher. Apply this to product code, tests, installers, builds, and agent helpers. Never use DETACHED_PROCESS or CREATE_NEW_CONSOLE for console programs. A deliberate exception needs nexus: console-window-ok <reason> on its launch line. Run the console-window-guard before test, installer, and build commands; use targeted checks for targeted changes.

## Surface: Gemini CLI (Google) -- ENTERPRISE-ONLY post-2026-06-18

This file deploys to `~/.gemini/GEMINI.md` (global) or `<project>/.gemini/GEMINI.md` (workspace) and is consumed by the standalone `gemini` CLI binary. Per the 2026-05-21 Google Developers Blog announcement, Gemini CLI stops serving free / Google AI Pro / Ultra / GitHub-installed users on 2026-06-18; enterprise tenants with a paid Gemini API key may continue using it via the Nexus-Hub installer's `--enterprise` / `-Enterprise` flag.

- Binary / invocation: `gemini -p '<prompt>'`, `gemini auth login`, `gemini --help`
- Slash commands: TOML files at `~/.gemini/commands/<name>.toml` (the Nexus-Hub installer mirrors `catalog/commands/` into this location automatically)
- Permissions: `configs/permissions/gemini-permissions.json` -- filesystem-read scoped to project roots, network scoped to trusted domains
- Migration: non-enterprise users should switch to Antigravity CLI before 2026-06-18 (see `base-antigravity-cli.md`)

## User Attribution

Use the user's Git identity, never an agent identity. Before commit, tag or push, run `nexus-hub attribution check`. Follow `~/.nexus-hub/style-guides/git-attribution.md` for setup, agent-footer restrictions and publication rules.
