# Phase 6 W08 re-run receipt (2026-10-31)

**Covers**: the raw result of the W08 (Claude Code `attribution`) re-proof attempt under the maintainer's USD 0.25 cap, as the harness printed it, with the real-file comparison. The reading of the result is in `v4.14.6-last-phase-evidence.md`, subsection `W08 re-proof attempt under the USD 0.25 cap`.

Command: `python -B scripts/dev/settings_proof_spike.py --paid-cap 0.25 --matrix docs/releases/v4/v4.14/development/v4.14.6-proof-matrix.md`, from `d844102cd`, started 15:41:43, finished 15:44:07.

Harness output: `swept 0 stale scratch homes; 39 candidates; real-file hashes identical`, `proven 20`, `not-proven 1`, exit 0.

Harness W08 row (not committed as the Proof Record, see the evidence file): `default: None (cost USD 0.1102) | empty strings: not-run: the default run showed no attribution lines`, verdict `not-proven`, Claude Code 2.1.283.

Sink record: attempts for 6 hosts (unparsed, api.anthropic.com, api.github.com, api.openai.com, chatgpt.com, github.com), none contacted; the paid request is the only one that left the machine.

Before and after (first 16 characters of SHA-256; `.credentials.json` with token and expiry values masked):

| File | Before | After |
|---|---|---|
| `~/.claude/settings.json` | `0dd843698768f37e` | `0dd843698768f37e` |
| `~/.claude/remote-settings.json` | `44136fa355b3678a` | `44136fa355b3678a` |
| `~/.claude/.credentials.json` (masked) | `a868953328ae27ca` | `a868953328ae27ca` |
| `~/.codex/config.toml` | `a08f300da3bc63cb` | `a08f300da3bc63cb` |
| `~/.codex/auth.json` | `5448ecae0e101a74` | `5448ecae0e101a74` |
| `~/.copilot/settings.json` | `cfb6e024984de203` | `cfb6e024984de203` |
| `~/.copilot/config.json` | `b4b7997e6fc5bccf` | `b4b7997e6fc5bccf` |
| `~/.nexus-hub/core-settings-seeds.json` | `2730eb6e87d86a11` | `2730eb6e87d86a11` |
| `~/.nexus-hub/guardrails.json`, `settings-control.json` | absent | absent |
| VS Code user `settings.json` | `2fba4c0e8293284d` | `cc2bf1bf03d3d898` (the file's other state; it flips with no probe running) |

Scratch folders: no `nexus-spike-*` folder remained under the system temp folder afterwards.
