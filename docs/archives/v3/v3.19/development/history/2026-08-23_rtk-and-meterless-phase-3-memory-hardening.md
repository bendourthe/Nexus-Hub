# Session History - RTK and Meterless Phase 3: Memory Provenance

**Date**: 2026-08-23
**Branch**: `develop`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md`](../../plans/v3.19.2-rtk-and-meterless.md)
**Phase**: 3 - Memory hardening
**Environment**: Windows 11, PowerShell, Python 3.12, pytest
**Outcome**: Every new memory write must name a source. Mutations append to a changelog. Superseded rows stay readable. Maintenance is preview-first and copies a backup. Ready for Phase 4.

## 1. Starting State and Routing

- **Starting commit**: `53530165` (Phase 2)
- **Plan recommendation**: frontier model, high effort
- **Implementation route**: stayed on the current Cursor session; no downshift

## 2. What Was Implemented

### 2.1 - Provenance as an invariant

`nexus-memory record` now wraps each write in a source/tier envelope and rejects a body with no origin. Pre-provenance rows still read as `source: legacy-import`. The `agent-memory` skill and `catalog/memory/record.md` teach the same rule. ADRs in `catalog/memory/decisions.md` gained a required **Source** field.

### 2.2 - Append-only changelog and supersede-not-delete

`changelog.log` records `added`, `superseded`, and `archived` rows. A superseding write leaves the old index in place. Tests cover missing-source rejection, a valid write, and a superseded row that remains gettable.

### 2.3 - Tiered lifecycle with preview-first backup

`python -m nexus_memory maintain` lists session-tier entries. `--apply` copies the store into `backups/<timestamp>/` and then appends changelog rows. Entries are not deleted.

### 2.4 - CI guard

`scripts/check_memory_provenance.py` (DEV_ONLY_SCRIPTS) fails `make validate` and the CI `validate` job if the catalog templates drop the contract.

## 3. Tests

- `pytest extensions/nexus-memory/tests/` plus `tests/validators/test_check_memory_provenance.py`
- `python scripts/check_memory_provenance.py`
- `python scripts/check_memory_integration_budget.py`

## 4. Deviations

- Envelope lives on the agent-facing `record` path. Low-level `append` stays a raw log write so store tests and repair tooling do not need a source.
- Archival marks session-tier rows in the changelog rather than compacting the log, which would violate append-only storage.

## 5. Next Steps

Phase 4: compressor semantic reformatters and a single rewrite-decision protocol with host-permission gating.
