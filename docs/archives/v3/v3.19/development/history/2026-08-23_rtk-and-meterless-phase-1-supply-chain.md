# Session History - RTK and Meterless Phase 1: Supply-Chain Hardening

**Date**: 2026-08-23
**Branch**: `develop`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.2-rtk-and-meterless.md`](../../plans/v3.19.2-rtk-and-meterless.md)
**Phase**: 1 - Supply-chain hardening
**Environment**: Windows 11, PowerShell, Python 3.12, pytest
**Outcome**: Standalone bootstrap verifies SHA-256 when pinned and refuses path-traversal archives on both POSIX and Windows. A repo-internal AST guard fails CI if the context compressor grows a network import. Ready for Phase 2.

## 1. Starting State and Routing

- **Starting commit**: `dfa06b2d` (merge of the v3.19.1 backmerge)
- **Plan recommendation**: frontier model, max effort
- **Implementation route**: stayed on the current Cursor session; no downshift
- **Installer edit**: confirmed by the `/implement` request that named Phase 1 of this plan

## 2. What Was Implemented

### 1.1 - Installer integrity

`install.sh` and `install.ps1` now, in lockstep, list the archive before extract and refuse members that are absolute or contain a `..` component (CWE-22). SHA-256 is computed with `sha256sum` / `shasum` / Python hashlib on POSIX and .NET `SHA256` on Windows (not `Get-FileHash`). Pins: `NEXUS_HUB_EXPECTED_SHA256`, `NEXUS_HUB_CHECKSUMS`. `NEXUS_HUB_SKIP_CHECKSUM=1` skips the hash only. Installing from `main` without a pin prints an explicit unverified-tarball warning. `checksums.txt` is a GNU sha256sum template; tagged hashes land at release (known-gaps DF-1).

### 1.2 - Zero-outbound compressor guard

`scripts/check_no_outbound.py` AST-scans `extensions/nexus-context-compressor` (skipping `tests/`) for `requests` / `httpx` / `aiohttp` / `socket` / `http.client` / `urllib.request` and `curl`/`wget` subprocesses. Wired into `make validate` and the CI `validate` job. Listed in `DEV_ONLY_SCRIPTS` (not installer-copied). Allowlist is empty.

### 1.3 - Tests and CI

Bootstrap tests cover matching checksum, mismatch abort, and `../` refusal on both shells (bash tests skip on Windows as before; PowerShell tests run here). Guard tests cover a clean tree, injected `import requests`, `urllib.parse` allowed, commented imports ignored, and `tests/` not scanned. No new required CI job: the guard rides `validate`. Windows bootstrap remains push-gated.

## 3. Tests

- `python scripts/check_no_outbound.py`: OK
- `pytest tests/validators/test_check_no_outbound.py tests/installer/test_bootstrap.py catalog/hooks/tests/test_installer_smoke.py`: green (bash functional tests skipped on this Windows host)
- `install.sh` `bash -n`: clean
- `install.ps1` AST parse: clean

## 4. Deviations

- Tagged-release checksum fetch is best-effort (`try_download`); a missing `checksums.txt` on a tag warns rather than failing until DF-1 is closed at release.
- Did not add a new required CI job or restructure the `changes` classifier. Installer tests stay in the existing `tests` / `bootstrap` jobs.

## 5. Next Steps

Phase 2: triggering confidence bands, eval floors, and the link/convention checker.
