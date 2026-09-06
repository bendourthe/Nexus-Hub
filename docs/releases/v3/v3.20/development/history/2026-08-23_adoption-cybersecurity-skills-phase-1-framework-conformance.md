# Session History - Cybersecurity Skills Adoption Phase 1: Framework and Conformance Tooling

**Date**: 2026-08-23
**Branch**: `feat/v3.20.1-adoption-cybersecurity-skills`
**Plan**: [`docs/releases/v3/v3.20/plans/v3.20.1-adoption-cybersecurity-skills.md`](../../plans/v3.20.1-adoption-cybersecurity-skills.md)
**Phase**: 1 - Framework and conformance tooling
**Environment**: Windows 11, PowerShell, Python 3, pytest
**Outcome**: `mitre_f3` is a validated sixth optional framework field; Navigator layer export is deterministic; agentskills.io conformance is a `make validate` / CI hard gate. Ready for Phase 2.

## 1. Starting State and Routing

- **Starting commit**: `9ddb7634` (`feat/v3.20.0-adoption-agent-security-layers`, v3.20.0 catalog bump)
- **Plan recommendation**: strong model, high effort
- **Implementation route**: stayed on the current Cursor session (Grok 4.6 / frontier). Stronger than planned; Cursor cannot script a model switch; no downshift.
- **Installer edit**: none. `check_agentskills_conformance.py` is repo-internal (`DEV_ONLY_SCRIPTS`). `build_framework_coverage.py` was already installer-copied; `--navigator-layer` is an additive flag.

## 2. What Was Implemented

### 1.1 - `mitre_f3` optional field

- `AGENTS.md` optional-fields table gained `mitre_f3` / MITRE Fight Fraud Framework (F3) / `[F1005.006, F1010]`. Absence remains never an error.
- `scripts/validate_skills.py` now checks all six framework fields for YAML list shape in `--bundles-only` and the full validator. A scalar is an error naming the skill and field.
- `scripts/build_framework_coverage.py` `FRAMEWORKS` includes `("mitre_f3", "MITRE F3")`.
- `security-framework-mapping` documents F3 v1.1 (2026-04-09, MITRE CTID), when to declare it (cyber-enabled financial fraud TTPs after initial compromise), and the `F<NNNN>` / `F<NNNN>.<NNN>` ID shape. Registries updated to match the new Tier-1 fields.

### 1.2 - ATT&CK Navigator layer export

`--navigator-layer <path>` writes a v4.5 layer JSON (`name`, `versions.layer/navigator/attack`, `domain: enterprise-attack`, `techniques[]` with `techniqueID`, `score`, `comment`) derived solely from parsed `mitre_attack` values. Score is skill count. Output uses sorted keys and LF so two runs are byte-identical. Live catalog currently yields 38 techniques. Markdown/JSON matrix output is unchanged and still emitted alongside the layer.

### 1.3 - agentskills.io conformance guard

Created `scripts/check_agentskills_conformance.py` (stdlib, read-only). Walks `catalog/skills/*/*/SKILL.md` and asserts name + description present, name 1-64 matching `^[a-z0-9]+(-[a-z0-9]+)*$`, description 1-1024. Extra top-level keys are INFO. Does not re-check name-equals-directory and does not ban `<`/`>`. Wired into `Makefile` `validate` and the existing CI `validate` job (no new required-check context). Listed in `DEV_ONLY_SCRIPTS`.

### 1.4 - Tests

- `tests/validators/test_framework_field_shape.py`: absent / list / scalar `mitre_f3`, block sequences.
- `tests/validators/test_agentskills_conformance.py`: real catalog, empty description, invalid name, extra keys as INFO, `--json`, collect-all-failures, Makefile/CI wiring, new over-long description fails.
- `tests/validators/test_build_framework_coverage.py`: `mitre_f3` in the matrix; Navigator layer schema, distinct-ID count, score, byte-identical re-run.

## 3. Tests

- `python -m pytest tests/validators/test_agentskills_conformance.py tests/validators/test_framework_field_shape.py tests/validators/test_build_framework_coverage.py tests/validators/test_invocation_policy.py`: 37 passed
- `python scripts/check_agentskills_conformance.py`: PASS (275 skills, 13 grandfathered over-long descriptions)
- `python scripts/validate_skills.py --bundles-only`: PASS
- `python scripts/check_registry_entries.py --check --strict`: PASS
- `python scripts/validate_doc_budgets.py`: PASS (AGENTS.md 7726 / 8150)
- `python -m pytest catalog/hooks/tests/test_installer_smoke.py::test_installers_copy_every_scripts_dir_py_file`: PASS
- `python scripts/build_framework_coverage.py --navigator-layer`: 38 techniques, required keys present

## 4. Deviations

- **List-shape validation did not previously exist.** AGENTS.md claimed framework fields were "checked for list shape only", but `validate_skills.py` had no such check. Phase 1 implemented the check for all six fields, not only `mitre_f3`, so the documented contract is now real.
- **Thirteen pre-existing descriptions exceed 1024 characters.** A naive hard error would fail the current catalog and miss the phase acceptance criterion. Those names are grandfathered (`WN-1`); a new over-long description still fails.
- **DEVLOG index line deferred** until `/update release` (one line per released version, not per phase).

## 5. Next Steps

Phase 2: commit `docs/framework-coverage.md` and `docs/attack-navigator-layer.json` with a `--check` freshness gate, and backfill `references/standards.md` for the 19 framework-declaring skills.
