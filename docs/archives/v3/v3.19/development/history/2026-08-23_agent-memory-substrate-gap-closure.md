# Session history: v3.19.1 known-gap closure

**Date**: 2026-08-23
**Plan**: `docs/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md`
**Scope**: Close DF-1, DF-2, DF-3, DF-4, and WN-1 before merging PR #96.

## What was closed

- **DF-1 / DF-2 / WN-1.** A second dated pass found first-party live tool-output numbers for OpenCode (50 KiB / 2,000 lines), Copilot (20,480 bytes), Qwen (25,000 / 1,000), Kimi MCP (100,000), OpenClaw (16,000), Aider (no silent cap), and Claude's static `BASH_MAX_OUTPUT_LENGTH` table. The safe default moved from 20,000 bytes to 16,000 bytes. Windsurf and Nexus-AI remain UNVERIFIED after the search and do not move the default.
- **DF-3.** `memory-store-guard.{sh,ps1}` blocks Write, Edit, and `git add` / `git commit` of store artifacts inside a git working tree. Registered on `Write|Edit|Bash`. Security-gate posture: no `NEXUS_HOOK_PROFILE=minimal` escape.
- **DF-4.** POSIX owner-only permissions, in-repo create/append refusal, and a `.nexus-memory-store` marker. Encryption declined (no key, no network KMS). Residual same-user disk access is accepted.

## Verification

- Paging default test now asserts `16,000` / `256`.
- Store tests cover in-repo refusal, the allow override, the marker, and POSIX modes.
- Hook tests cover both implementations, including that `NEXUS_HOOK_PROFILE=minimal` does not disable the gate.
