# Known Gaps - v4.5

**Project**: Nexus-Hub
**Status**: v4.5.0 in progress on `feat/v4.5.0-anti-cliche-and-agent-security`; phases 1 to 5 complete locally, not published
**Last updated**: 2026-09-04 (v4.5.0 Phase 5)

## v4.5.0 - anti-cliche-and-agent-security

**Plan**: [v4.5.0-anti-cliche-and-agent-security.md](plans/v4.5.0-anti-cliche-and-agent-security.md)
**Base**: `develop` at `8a426441` (the v4.4.5 back-merge)

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Warnings

##### WN-2 - Phase 3 ran one effort level below the plan's recommendation

- **Source phase**: Phase 3 - Catalog Extension, the Uncovered Cliche Patterns.
- **Plan reference**: Phase 3 `**Recommended model tier**: frontier` / `**Recommended effort level**: max`.
- **Reason**: The session ran `claude-fable-5-1`, which is the frontier tier on the 2026-09-04 map, at `high`. Claude Code cannot switch effort programmatically, so the `/effort max` keystroke was surfaced at the phase boundary and, with no switch made, the phase proceeded at `high` under the in-full driver. This is a recorded delta, not a silent downshift, and the tier itself agreed with the plan.
- **Impact**: None observed. Every Phase 3 gate passed, the reference file names no upstream expression, and the body stayed at 309 lines against a 500-line target.
- **Also applies to Phase 5** (recommended frontier / max, ran frontier / high under the same constraint): every Phase 5 gate passed, the name scrub returned nothing, and the body reached 155 lines against a 500-line target. The keystroke was surfaced again at that boundary, as this entry's next step asked.
- **Suggested next step**: Phase 7 is also rated `max`; surface the keystroke again at that boundary so the choice is made deliberately rather than inherited.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| WN-1 | Pre-existing lint and format drift in the parity guard | Phase 2 | Phase 2 edits `scripts/check_base_template_parity.py` on purpose (promoting `Writing Discipline` into both guard lists), so the two ruff findings (`UP035`, `UP045`) were fixed and the file formatted in that same deliberate edit; the whole diff is 15 insertions and 3 deletions. |

### Notes (not gaps)

- The offline detector classifies the clause-joining spaced hyphen as `advisory`, not `defect`, after the phase 4 self-scan found 182 legitimate historical uses in `CHANGELOG.md` alone. The Writing Discipline rule still forbids it in new prose; the detector reports it without gating on it. Recorded here so phase 7 reads the detector's class boundary from its docstring rather than from the plan's one-line definition.

- Coverage on `scripts/check_base_template_parity.py` reads 0 percent under `pytest --cov` because its tests drive the script as a subprocess, which the tracer does not follow. No logic changed in this phase (docstring only) and the 16 behavioral tests plus 4 new template tests pass, so this is a measurement limit, not an untested path.
- The five lockstep word ceilings were raised by the measured cost of the block (+110 on `base-claude.md`, +170 on the other four). This was a maintainer decision made before implementation, recorded under Recorded raises in `docs/policy/doc-budgets.md`; it is listed here so phase 7's cost reckoning cannot miss it.
- The deterministic response class in `agentic-endpoint-hardening` is guidance only by maintainer decision: the skill tree has no `scripts/` directory and phase 6 added no executable content. Recorded here so phase 7's Goal-vs-codebase review checks the tree, not just the body's statement, when confirming the guidance-only decision.
