# Session History - Agent-Memory Substrate Phase 3: Storage Engine

**Date**: 2026-08-23
**Branch**: `feat/v3.19.1-agent-memory-substrate`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md`](../../plans/v3.19.1-agent-memory-substrate.md)
**Phase**: 3 - Storage engine
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest
**Outcome**: `extensions/nexus-memory/` is an append-only, crash-safe, concurrently-writable fixed-width store with a relocatable user-scoped root. Compression is not implemented yet.

## 1. Starting State and Routing

- **Starting commit**: `991dfe46` (Phase 2)
- **Plan recommendation**: strong reasoning tier, high effort
- **Implementation route**: stayed on the current Cursor session; no downshift

## 2. What Was Implemented

Scaffolded the package on the sibling extension layout (`pyproject.toml` with a `[dev]` extra, `src/nexus_memory/`, README, tests). Runtime dependencies are empty. The README carries the policy-compliance paragraph and states that compression is performed by the calling agent.

The log uses a 4-byte little-endian length prefix plus UTF-8 payload, padded with NUL to `record_width` (default 1024). `append`, `get`, `slice`, and `count` are implemented. Over-length entries raise. Existing records are never rewritten.

Write locking uses `fcntl` on POSIX and `msvcrt` on Windows, selected at import time, with a mkdir fallback. `repair` truncates only a non-integral tail. A blank or impossible record raises with `python -m nexus_memory repair --root ...`.

`NEXUS_MEMORY_ROOT` relocates the store. The default remains `~/.nexus-hub/memory/`. `config show` / `config set` cover read budget, max entry length, record width, and the two Phase 1 paging limits. `gitignore.recommended` ships the accidental-commit pattern. README cross-references egress-redaction.

## 3. Tests

10 tests, all green on this Windows host, including four-process concurrent append (60 entries, no loss, no interleaving) and kill-mid-append repair. CI: added to the required `tests` job (Ubuntu, every relevant change) and a path-scoped `nexus-memory.yml` whose multi-OS locking matrix runs on merge/dispatch only.

## 4. Next Steps

Phase 4: age-decaying tiling, the summary tree, and the agent-driven merge loop.
