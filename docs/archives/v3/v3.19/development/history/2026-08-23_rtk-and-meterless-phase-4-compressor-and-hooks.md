# Session History - RTK and Meterless Phase 4: Compressor and Hook Depth

**Date**: 2026-08-23
**Branch**: `develop`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md`](../../plans/v3.19.2-rtk-and-meterless.md)
**Phase**: 4 - Compressor and hook depth
**Environment**: Windows 11, PowerShell, Python 3.12, pytest
**Outcome**: One rewrite decision (0/1/2/3, default ask) with host-permission gating, thin hook delegates, and a short list of semantic reformatters that beat a 60% token-reduction bar. Ready for Phase 5.

## 1. Starting State and Routing

- **Starting commit**: `3db18aa1` (Phase 3)
- **Plan recommendation**: frontier model, high effort
- **Implementation route**: stayed on the current Cursor session; no downshift

## 2. What Was Implemented

### 2.1 - Single rewrite protocol

`nexus_context_compressor.rewrite.decide` returns allow / passthrough / deny / ask. A proposed rewrite with no host allow is ask, never auto-allow. Deny beats ask beats allow. Compound commands (`&&` `||` `;` `|`) allow only when every segment matches allow. CLI: `python -m nexus_context_compressor rewrite --cmd ...`.

### 2.2 - Thin hook delegates

`catalog/hooks/rewrite-command.sh` and `.ps1` call that CLI and map exit codes onto a PreToolUse `permissionDecision`. Missing Python is passthrough. Registered on Bash in `catalog/hooks/settings.json`. Host `permissions.deny` / `ask` / `allow` are read from `CLAUDE_CONFIG_DIR/settings.json` when present.

### 2.3 - Semantic reformatters

`reformatters.py` handles git status, pytest/vitest/jest failures-only, and ruff/eslint/tsc grouped by file. `compress_output` tries them before the content router. Unrecognized text is unchanged. Coverage vs a ~60-handler compressor is recorded as **DF-3**.

## 3. Tests

- `pytest extensions/nexus-context-compressor/tests/test_rewrite.py extensions/nexus-context-compressor/tests/test_reformatters.py catalog/hooks/tests/test_rewrite_command.py`
- `python scripts/check_no_outbound.py`

## 4. Deviations

- Command rewrite does not invent equivalents; with no proposed rewrite the decision is passthrough. Auto-allow requires an explicit host allow on every segment.
- Reformatters are a named short list (DF-3), not handler-count parity.

## 5. Next Steps

Phase 5: BYO filters with a SHA-256 trust store, non-destructive truncation plus a recovery pointer, session mining, and a signed-execution-contract design study.
