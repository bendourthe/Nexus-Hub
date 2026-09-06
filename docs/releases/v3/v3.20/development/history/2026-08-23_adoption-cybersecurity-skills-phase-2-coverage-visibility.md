# Session History - Cybersecurity Skills Adoption Phase 2: Coverage Visibility

**Date**: 2026-08-23
**Branch**: `feat/v3.20.1-adoption-cybersecurity-skills`
**Plan**: [`docs/releases/v3/v3.20/plans/v3.20.1-adoption-cybersecurity-skills.md`](../../plans/v3.20.1-adoption-cybersecurity-skills.md)
**Phase**: 2 - Coverage visibility
**Environment**: Windows 11, PowerShell, Python 3, pytest
**Outcome**: Committed coverage map is freshness-gated; every framework-declaring skill has `references/standards.md`. Ready for Phase 3.

## 1. Starting State and Routing

- **Starting commit**: `b3b7ce31` (Phase 1: `mitre_f3`, Navigator export, agentskills.io guard)
- **Plan recommendation**: standard model, medium effort
- **Implementation route**: stayed on the current Cursor session (Grok 4.6 / frontier). No downshift.
- **Installer edit**: none. `--check` is an additive flag on an already-copied script.

## 2. What Was Implemented

### 2.1 - Committed coverage map with `--check`

- Markdown header marks `docs/framework-coverage.md` GENERATED and names the regenerate command.
- `--check` regenerates Markdown and the Navigator layer in memory, normalizes CRLF to LF, and exits 1 on missing or stale files.
- Defaults: `docs/framework-coverage.md` and `docs/attack-navigator-layer.json`. `--out` / `--navigator-layer` override those paths for tests.
- Wired into `Makefile` `validate` and the existing CI `validate` job (no new required-check context).
- Live catalog: 62 control rows, 38 ATT&CK techniques.

### 2.2 - `references/standards.md` backfill

- Live catalog has **21** framework-declaring skills, not the 19 the plan counted.
- 20 already had complete `references/standards.md` files naming every declared ID.
- Authored the missing file for `skill-security-scan` from official ATT&CK / ATLAS / D3FEND / NIST URLs (no third-party catalog prose). Linked it from that SKILL.md so the orphan-bundle audit passes.

### 2.3 - Tests

- `--check` passes in sync, fails on drift, fails on missing files, treats CRLF as equal to LF, and passes against the committed catalog artifacts.
- One aggregate test over all framework-declaring skills (not 21 near-identical tests).
- Makefile/CI wiring assertion.

## 3. Tests

- `python -m pytest tests/validators/test_build_framework_coverage.py tests/validators/test_framework_standards_files.py`: 18 passed
- `python scripts/build_framework_coverage.py --check`: PASS
- `python scripts/validate_skills.py --bundles-only`: PASS (0 errors, 0 warnings)
- `python scripts/validate_doc_budgets.py`: PASS

## 4. Deviations

- **21 declaring skills, not 19.** Two skills landed after the plan was written. Covered all 21; only `skill-security-scan` needed a new `standards.md`.
- **Committed paths follow the generator defaults** (`docs/framework-coverage.md`, `docs/attack-navigator-layer.json`) rather than the plan's slightly different filenames. `--check` and `make validate` use those defaults.
- **DEVLOG index line deferred** until `/update release`.

## 5. Next Steps

Phase 3: relocate SKILL.md bodies over 800 lines into `references/`, then machine-enforce the cap in `validate_skills.py`.
