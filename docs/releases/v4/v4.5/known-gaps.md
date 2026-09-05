# Known Gaps - v4.5

**Project**: Nexus-Hub
**Status**: v4.5.0 in progress on `feat/v4.5.0-anti-cliche-and-agent-security`; phase 1 complete locally, not published
**Last updated**: 2026-09-04 (v4.5.0 Phase 1)

## v4.5.0 - anti-cliche-and-agent-security

**Plan**: [v4.5.0-anti-cliche-and-agent-security.md](plans/v4.5.0-anti-cliche-and-agent-security.md)
**Base**: `develop` at `8a426441` (the v4.4.5 back-merge)

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Warnings

##### WN-1 - Pre-existing lint and format drift in the parity guard, left untouched by design

- **Source phase**: Phase 1 - The Always-On Writing Discipline Rule.
- **Plan reference**: `docs/releases/v4/v4.5/plans/v4.5.0-anti-cliche-and-agent-security.md` sub-task 1.2 / T002 (the docstring edit that retired `## Communication Style`).
- **Reason**: `scripts/check_base_template_parity.py` carries two auto-fixable ruff findings (`UP035` at line 84, `UP045` at line 207) and would be reformatted by `ruff format`; all three are present on `develop` before this phase and sit in regions this phase did not change. Phase 1 edited only the module docstring, so fixing them would be adjacent cleanup outside the stated scope. They are not gating: `make lint` runs ShellCheck, and `make validate` does not run ruff on `scripts/`.
- **Suggested next step**: Fold the three fixes into phase 2, which edits this script's `INVARIANT_SECTIONS` on purpose and can format the file as part of that change; record the format pass in that phase's history so the diff is explained.

### Notes (not gaps)

- Coverage on `scripts/check_base_template_parity.py` reads 0 percent under `pytest --cov` because its tests drive the script as a subprocess, which the tracer does not follow. No logic changed in this phase (docstring only) and the 16 behavioral tests plus 4 new template tests pass, so this is a measurement limit, not an untested path.
- The five lockstep word ceilings were raised by the measured cost of the block (+110 on `base-claude.md`, +170 on the other four). This was a maintainer decision made before implementation, recorded under Recorded raises in `docs/policy/doc-budgets.md`; it is listed here so phase 7's cost reckoning cannot miss it.
