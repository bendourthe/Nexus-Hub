---
name: usage
description: "Run the /usage command. Check Claude Code usage limits and get smart model-switching recommendations based on current consumption. Use to \"check my usage\", \"how much have I used\", \"am I near my limit\", \"should I switch models\", \"what's my token consumption\", \"check usage limits\". SKIP - billing safeguards for autonomous agent systems (that is the ai-billing-safeguards skill) or project cost estimation."
disable-model-invocation: true
---

# /usage Command

Check current usage against the limits of this platform's tracked windows (five-hour, weekly, or monthly) and get a model-switching recommendation based on how much has been consumed. `/usage` has no scopes; it reports usage and advice directly.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The reading comes from the shared usage probe the `usage-guard` hook already uses; this file only delegates.

## Delegation

Run the installed probe for the platform you are on, then interpret its JSON:

      (any invocation) -> _usage_probe.py --platform <claude|codex|cursor|copilot> --json

| Platform | Command |
|---|---|
| Claude Code | `python ~/.claude/hooks/_usage_probe.py --platform claude --json` |
| Codex | `python ~/.codex/hooks/_usage_probe.py --platform codex --json` |
| Cursor | `python ~/.cursor/hooks/_usage_probe.py --platform cursor --json` |
| GitHub Copilot | `python ~/.copilot/hooks/nexus-hub-scripts/_usage_probe.py --platform copilot --json` |

Use `python3` where `python` is not Python 3. The probe always exits 0 and prints one JSON line with `status` (`ok`, `stale`, or `unavailable`), `windows` (each with `name`, `percent`, and a display-only `resets_at`), and a `reason` when unavailable. It prints percentages only, never a token or a credential.

Then report, in this order:

1. Each window's name and percent, and whether the reading is `stale` (cached) rather than live.
2. A recommendation: at 90 percent or more on any window (the probe's `NEAR_LIMIT_PERCENT`; the guard hands off at `NEXUS_HANDOFF_THRESHOLD`, default 99), suggest moving the remaining work to a cheaper tier and use the `model-routing` skill to name the tier and effort; below that, say no switch is needed.
3. When `status` is `unavailable`, quote the `reason` and stop. Do not estimate usage from anything else.

## Notes

- This command replaces `/check-usage` (removed in v3.2.0). The `check-usage` skill it once named was not kept, so the probe is the procedure (v4.13.9 BG-12).
- The probe is installed for Claude Code, Codex, Cursor, and GitHub Copilot. On any other platform, say that no usage source exists there.
- Setup, validation, and the off switch (`NEXUS_USAGE_PROBE_DISABLED=1`) are documented in `docs/guides/usage-limit-handoff.md`.
