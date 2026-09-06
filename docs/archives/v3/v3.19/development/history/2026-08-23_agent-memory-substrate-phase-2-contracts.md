# Session History - Agent-Memory Substrate Phase 2: Contracts and Conventions

**Date**: 2026-08-23
**Branch**: `feat/v3.19.1-agent-memory-substrate`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md`](../../plans/v3.19.1-agent-memory-substrate.md)
**Phase**: 2 - Contracts and conventions
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest
**Outcome**: The substrate relationship, the agent-performed compression protocol, the subagent write-exclusion clause, and a CI-enforced 500-token budget for the always-loaded integration prose are all written down. No storage code exists yet.

## 1. Starting State and Routing

- **Starting commit**: `c51697e2` (Phase 1)
- **Plan recommendation**: mid reasoning tier, medium effort
- **Implementation route**: stayed on the current Cursor session; no downshift

## 2. What Was Implemented

### 2.1 / 2.2 - Contract and compression protocol

Wrote `docs/policy/memory-substrate-contract.md` (64 lines, under the 150-line cap). It records the 2026-07-28 decision that `nexus-memory` is the durable source of truth and a harness-native memory surface is an index; the session-start read order; the substrate-wins conflict rule; the distinction from `session-query`, `context-pack-builder`, `continuous-learning`, and `solution-knowledge-base`; and the compression protocol (no model call, one merge at a time, refuse on a missing child, tree is a rebuildable cache).

### 2.3 - Subagent write exclusion

Added one write-scope rule to `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` and the same exact one-line prompt form to the contract: `Do not write to persistent agent memory. You are a spawned subagent; only the parent session may record memory.` Parallel top-level sessions may still write.

### 2.4 - Token-budget guard

Added `scripts/check_memory_integration_budget.py` measuring `docs/policy/memory-integration-prose.md` against a 500-token ceiling. Counting prefers local `tiktoken` and degrades to the same stdlib estimator `nexus-context-compressor` uses. The script is in `DEV_ONLY_SCRIPTS`, `make validate`, and the CI `validate` job. The prose file is a stub that Phase 4 replaces; the guard already has a real file to measure.

## 3. Tests

`tests/validators/test_check_memory_integration_budget.py`: shipped file under budget; under-budget fixture passes; over-budget fixture fails with `OVER`; missing file is `MISS`; invalid budget is `BAD`; Makefile and CI invoke the guard; the exclusion line is in both the coordinator skill and the contract. Installer smoke still passes with the new `DEV_ONLY_SCRIPTS` entry.

## 4. Verification

| Gate | Result |
|---|---|
| New budget-guard tests | 8 passed |
| Installer smoke (copy-every-script) | Passed |
| Contract length | 64 lines (cap 150) |
| CI | Existing `validate` job; no new required check |

## 5. Next Steps

Phase 3: scaffold `extensions/nexus-memory/` and implement the append-only, crash-safe, concurrently-writable fixed-width store.
