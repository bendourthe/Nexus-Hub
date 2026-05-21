@base-google-shared.md

## Surface: Gemini CLI (Google) -- ENTERPRISE-ONLY post-2026-06-18

This file deploys to `~/.gemini/GEMINI.md` (global) or `<project>/.gemini/GEMINI.md` (workspace) and is consumed by the standalone `gemini` CLI binary. Per the 2026-05-21 Google Developers Blog announcement, Gemini CLI stops serving free / Google AI Pro / Ultra / GitHub-installed users on 2026-06-18; enterprise tenants with a paid Gemini API key may continue using it via the Nexus-Hub installer's `--enterprise` / `-Enterprise` flag.

- Binary / invocation: `gemini -p '<prompt>'`, `gemini auth login`, `gemini --help`
- Slash commands: TOML files at `~/.gemini/commands/<name>.toml` (the Nexus-Hub installer mirrors `catalog/commands/` into this location automatically)
- Permissions: `configs/permissions/gemini-permissions.json` -- filesystem-read scoped to project roots, network scoped to trusted domains
- Migration: non-enterprise users should switch to Antigravity CLI before 2026-06-18 (see `base-antigravity-cli.md`)
