# Known Gaps - v4.5

**Project**: Nexus-Hub
**Status**: v4.5.0 in progress on `feat/v4.5.0-anti-cliche-and-agent-security`; phases 1 and 2 complete locally, not published
**Last updated**: 2026-09-04 (v4.5.0 Phase 2)

## v4.5.0 - anti-cliche-and-agent-security

**Plan**: [v4.5.0-anti-cliche-and-agent-security.md](plans/v4.5.0-anti-cliche-and-agent-security.md)
**Base**: `develop` at `8a426441` (the v4.4.5 back-merge)

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

None.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| WN-1 | Pre-existing lint and format drift in the parity guard | Phase 2 | Phase 2 edits `scripts/check_base_template_parity.py` on purpose (promoting `Writing Discipline` into both guard lists), so the two ruff findings (`UP035`, `UP045`) were fixed and the file formatted in that same deliberate edit; the whole diff is 15 insertions and 3 deletions. |

### Notes (not gaps)

- Coverage on `scripts/check_base_template_parity.py` reads 0 percent under `pytest --cov` because its tests drive the script as a subprocess, which the tracer does not follow. No logic changed in this phase (docstring only) and the 16 behavioral tests plus 4 new template tests pass, so this is a measurement limit, not an untested path.
- The five lockstep word ceilings were raised by the measured cost of the block (+110 on `base-claude.md`, +170 on the other four). This was a maintainer decision made before implementation, recorded under Recorded raises in `docs/policy/doc-budgets.md`; it is listed here so phase 7's cost reckoning cannot miss it.
