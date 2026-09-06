# Session History - Agent-Memory Substrate Phase 4: Compression Tree

**Date**: 2026-08-23
**Branch**: `feat/v3.19.1-agent-memory-substrate`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md`](../../plans/v3.19.1-agent-memory-substrate.md)
**Phase**: 4 - Compression tree
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest
**Outcome**: A store larger than the read budget still reads in full within that budget. Recent entries stay verbatim; older ranges collapse through an agent-performed merge loop. Deleting the tree loses no log entries.

## 1. Starting State and Routing

- **Starting commit**: `551eb266` (Phase 3)
- **Plan recommendation**: strong reasoning tier, high effort
- **Implementation route**: stayed on the current Cursor session; no downshift

## 2. What Was Implemented

### 4.1 - Age-decaying tiling

`tile(n, budget)` is a pure function. When `n <= budget` every entry is its own range. Otherwise a single decay parameter is binary-searched so a range stays whole when `size <= decay * age`, then leftover budget splits the newest non-singleton. Newest (`age = 0`) stays size 1. An aligned power-of-two cover has a hard minimum (binary weight of `n` plus that newest singleton); a budget below that minimum returns the coarsest legal tiling rather than leaving a gap.

### 4.2 - Summary tree

One file per level (`tree/level_{size}`), dense prefix of fixed-width records. `put` / `get` / `drop` / `pending` / `pending_count`. Pending work is one next slot per level, smallest-first. `drop` truncates the suffix at that level. A missing or blank child raises `MissingChildError` and does not fabricate. Size-2 children are log entries.

### 4.3 - Command surface and integration prose

`read`, `record`, `merge`, `search`, `zoom`, and `drop` are wired in `cli.py`. `record` emits at most one merge request, formatted per the Phase 2 contract, with a self-named return command. Nothing runs in a background process. Replaced `docs/policy/memory-integration-prose.md` with the always-loaded block: 218 tokens (tiktoken) against the 500-token cap.

## 3. Tests

37 tests green on this Windows host: tiling invariants (parametrize plus a 40-pair random sweep), tree pending/drop/cache-delete, command merge-changes-read, and an end-to-end fill-past-budget then drain-every-merge case. CI: the existing path-scoped `nexus-memory.yml` now runs the full suite on the merge-gated multi-OS matrix, not only `test_store.py`.

## 4. Verification

| Gate | Result |
|---|---|
| `extensions/nexus-memory` pytest | 37 passed |
| Integration-prose budget | 218 / 500 (tiktoken) |
| Tree-deletion cache invariant | Passed |
| CI | Existing `tests` job plus path-scoped workflow; no new required check |

## 5. Next Steps

Phase 5: `catalog/skills/workflow/agent-memory/`, registry edits, trigger evals, and the reverse-engineering matrix row.
