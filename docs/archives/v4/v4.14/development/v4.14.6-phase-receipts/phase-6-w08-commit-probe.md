# Phase 6 W08 commit-probe receipt (2026-10-31)

**Covers**: the raw result of the W08 (Claude Code `attribution`) commit probe under the maintainer's USD 0.50 cap, with the git isolation evidence and the real-file comparison. The reading of the result is in `v4.14.6-last-phase-evidence.md`, subsection `W08 proof history and final outcome`.

Command: `python -B scripts/dev/settings_proof_spike.py --paid-cap 0.50 --matrix docs/releases/v4/v4.14/development/v4.14.6-proof-matrix.md`, from `ca3c97ce0` plus the harness change, started 15:58:37, finished 16:01:08.

Free isolation check before the paid run (`git_isolation_check`): `ok`. Every `git config --show-origin --list` origin is the scratch `gitconfig` or the repository's `.git/config`; no `hooksPath` or `templateDir` key; no `.git/hooks` directory (the repository is created with `--template=`); a plain `git commit` with a `Co-Authored-By: Probe` trailer keeps the trailer.

Harness output: `swept 0 stale scratch homes; 39 candidates; real-file hashes identical`, `proven 20`, `not-proven 1`, exit 0.

| Request | Cost (USD) | Observed |
|---|---|---|
| W08 default attribution | 0.7662 | commit message `Add probe.txt` then `Co-Authored-By: Claude Code <noreply@anthropic.com>` |
| W08 attribution empty strings | not started | the tally (0.7662 + 0.20 reserve) is over the 0.50 cap |
| **Total** | **0.7662** | cap USD 0.50, exceeded by 0.2662 |

Harness W08 row: verdict `not-proven`, `default: 2 line(s), attribution: "Co-Authored-By: Claude Code <noreply@anthropic.com>" | empty: not-run: the next request could exceed the paid cap`.

Before and after (first 16 characters of SHA-256; `.credentials.json` with token and expiry values masked): `~/.claude/settings.json` `0dd843698768f37e`, `~/.claude/remote-settings.json` `44136fa355b3678a`, `~/.claude/.credentials.json` `a868953328ae27ca`, `~/.codex/config.toml` `a08f300da3bc63cb`, `~/.codex/auth.json` `5448ecae0e101a74`, `~/.copilot/settings.json` `cfb6e024984de203`, `~/.copilot/config.json` `b4b7997e6fc5bccf`, `~/.nexus-hub/core-settings-seeds.json` `2730eb6e87d86a11`, `~/.nexus-hub/guardrails.json` and `settings-control.json` absent, VS Code user `settings.json` `cc2bf1bf03d3d898`. All identical before and after.

Scratch folders: none left under the system temp folder (the harness cleanup now clears read-only git objects; two folders left by an earlier development run of the harness were removed by hand).
