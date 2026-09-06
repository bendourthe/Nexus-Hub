# Session History - Org Knowledge Layer Phase 5: Lifecycle Integration and Docs

**Date**: 2026-08-16
**Branch**: `feat/v3.17.4-org-knowledge-layer`
**Plan**: [`docs/releases/v3/v3.17/plans/v3.17.4-org-knowledge-layer.md`](../../plans/v3.17.4-org-knowledge-layer.md)
**Phase**: 5 - Lifecycle Integration and Docs
**Environment**: Windows PowerShell, Python 3.12.10, pytest, ShellCheck; GNU Make unavailable
**Outcome**: Organization knowledge is now diagnosed, repaired, synchronized, selectively removed, and documented through the complete install lifecycle. Phase-specific validation is green and Phase 6 remains the final reconciliation and CI/CD phase.

## 1. Starting State

- **Starting commit**: `d92096bd` (`feat(org): add guided standards authoring`)
- **Prior session**: [`2026-08-16_org-knowledge-layer-phase-4-guided-authoring-surface.md`](2026-08-16_org-knowledge-layer-phase-4-guided-authoring-surface.md)
- **Prerequisites**: Phase commits `af46880a`, `9742b449`, `ec6f7580`, and `d92096bd` were present on the feature branch.
- **Worktree**: clean before Phase 5 implementation.

The plan recorded `strong / high`. Deterministic implementation-time scoring raised the portable intent to `frontier / max` because task scope, context volume, risk, and reasoning were high. The dated plan map named `gpt-5.6-sol`, while the local Codex enumerator exposed `gpt-5.5` as the strongest verified fallback with `xhigh` as its maximum available effort.

## 2. Chronological Steps

### 2.1 Manifest ownership and lifecycle diagnosis

Added additive `org_tracked` and `org_shared` ownership lists to `InstallManifest`. Ordinary manifests omit both keys when empty, preserving the pre-feature serialized shape. Organization rule roots and files use tracked ownership; shared instruction files use a separate organization-marker ownership list so removing organization guidance never untracks the Nexus-Hub block in the same file.

Added organization health findings for connection readability, source reachability, bundle validity, missing materialization, marker-body drift, and rule-tree drift. The existing lifecycle doctor converts these into normal `DoctorFinding` records, so repair reuses the established affected-integration calculation. Text and JSON doctor output now carry an optional actionable detail.

### 2.2 Selective cleanup, repair, disconnect, and teardown

Added `remove_org_knowledge()` as the single manifest-driven cleanup path. It removes organization marker sections, deletes only recorded organization rule artifacts, clears their ownership records, handles read-only Windows trees, and preserves untracked pre-existing `rules/org` directories even during repair with overwrite enabled.

Marker removal now stages replacement bytes beside the destination and commits them with `os.replace`, preventing a concurrent reader from seeing a half-removed marker pair. `IntegrationBase.teardown()` invokes organization cleanup before its ordinary manifest replay. Seeding with no active connection reconciles stale organization artifacts, which lets disconnect followed by workspace repair reach zero residue.

`nexus-hub org disconnect` now cleans organization artifacts recorded by the installed global manifest before deleting connection state and a cached Git clone. Workspace manifests remain project-local; the command tells users to run repair or reinstall in each workspace. Upgrade required no extra path because `cmd_upgrade()` re-runs the platform installer, and both installers already invoke the registry dispatcher that seeds organization knowledge.

### 2.3 User and maintainer documentation

Added [`guides/ORG_KNOWLEDGE_LAYER.md`](../../../../../guides/ORG_KNOWLEDGE_LAYER.md) as the canonical bundle, lifecycle, precedence, authoring, distribution, rollback, and enforcement-escalation reference. Its release block declares the required Activation, Validation, Rollback, Authority, and Docs markers and passes the strict capability-document checker.

README now links the workflow from Quick Start. AGENTS documents the dispatcher seam, additive manifest fields, do-not-infer-ownership rule, fail-soft boundary, and no-enforcement/no-transmission authority boundary. CHANGELOG records the Phase 5 capability, and the plan plus progress dashboard advance to five of six phases complete.

## 3. Verification Gate

| Check | Result |
|---|---|
| Existing organization suites before lifecycle tests | PASS - 45 tests |
| New lifecycle suite | PASS - 9 tests |
| Atomic marker and lifecycle focused gate | PASS - 22 tests |
| Installer/integration changed-area partition | PASS - 118 passed, 1 skipped |
| Isolated retry of transient local Git fixture | PASS - 1 test |
| Python compilation | PASS |
| ShellCheck | PASS |
| Direct `make validate` constituents | PASS |
| Capability-document checker in strict mode | PASS - all five elements present |
| New-guide strict Unicode safety | PASS |
| Added-line ASCII check for README, AGENTS, and CHANGELOG | PASS |
| `git diff --check` | PASS |
| Exact monolithic `make test` recipe | NOT COMPLETE - Windows command reached the 20-minute bound without a terminal summary or reported assertion failure |

## 4. Known Issues

No Phase 5 product defect remains open. The monolithic test recipe remains too slow to produce a local Windows terminal result inside the 20-minute bound; the green changed-area partition covers every modified runtime path, and protected CI remains the authoritative unbounded full-repository gate.

## 5. Plan Discrepancies

- **Routing upshift**: implementation used approved `frontier / max` portable intent instead of the plan's `strong / high` because destructive cleanup and cross-lifecycle proof raised the risk and reasoning scores.
- **GNU Make unavailable**: every `make validate` constituent and the ShellCheck lint target ran directly. The exact `make test` recipe was reproduced directly but did not complete inside its bound.
- **Manifest extension**: the plan required the manifest as source of truth but did not prescribe distinct ownership fields. Additive organization-specific lists were necessary to remove organization content without untracking or deleting co-located Nexus-Hub and user content.

## 6. Assumptions Made

- **Global versus workspace manifests**: the installed global manifest is at `~/.nexus-hub/install-manifest.json`; workspace manifests remain under each project and cannot be discovered safely from a global disconnect command.
- **Ownership requires evidence**: a pre-existing untracked `rules/org` directory is user-owned even if its name matches the organization convention. Nexus-Hub preserves it and does not adopt it based on path shape.
- **Upgrade seam**: re-running the existing installer is sufficient because both installers reach `IntegrationBase.install()` through the registry dispatcher after their catalog refresh steps.
- **Full-suite authority**: a bounded local timeout is not a pass. Phase completion relies on all phase-specific and changed-area tests passing, with hosted CI responsible for the unbounded full matrix in Phase 6.

## 7. Testing Summary

### Automated tests

- Organization bundle, CLI, materialization, lifecycle, instruction-merge, integration lifecycle, and teardown suites: 118 passed, 1 skipped.
- The new `test_org_lifecycle.py` covers vanished sources, drift repair with outside-text preservation, selective teardown, immediate global cleanup, workspace zero-residue cleanup, unowned rule preservation, two-platform source synchronization, upgrade dispatcher reuse, and documentation contracts.
- Validation, lint, Python compilation, strict capability documentation, strict guide Unicode safety, and diff whitespace checks pass.

### Troubleshooting evidence

- The first combined changed-area run reported `assert 2 == 0` while creating a local bare Git connection fixture. The exact test passed alone immediately and the final 118-test partition passed, so no production change was made for the transient fixture failure.
- The exact full test recipe ended with `command timed out after 1204172 milliseconds`; it emitted no assertion failure and no completed constituent summary because output was intentionally captured per suite.
- A first strict Unicode run over all of AGENTS reported 36 historical em-dash findings. The Phase 5 guide passes strict scanning and every added line in README, AGENTS, and CHANGELOG is ASCII-clean; unrelated historical prose was not rewritten.

### Manual testing still needed

- [ ] Run the complete repository and cross-operating-system matrix in protected CI during Phase 6.
- [ ] Exercise connect, repair, and disconnect against an installed release candidate on macOS or Linux in Phase 6 release preparation.

## 8. TODO Tracker

### Completed this session

- [x] Add doctor, repair, teardown, uninstall, disconnect, and upgrade lifecycle behavior.
- [x] Add atomic and ownership-aware organization cleanup.
- [x] Add the canonical user guide and release capability block.
- [x] Add comprehensive lifecycle and documentation regression coverage.
- [x] Update CHANGELOG, AGENTS, README, the implementation plan, and `docs/todos.md`.

### Remaining

- [ ] Complete Phase 6 architecture reconciliation, known-gaps audit, CI/CD coverage confirmation, and release-readiness handoff.

### Deferred

- [ ] Obtain authoritative unbounded full-suite and cross-OS evidence from protected CI in Phase 6.

## 9. Summary and Next Steps

Phase 5 closes the organization layer's install-lifecycle and user-operability gaps. Organization artifacts now have explicit ownership, doctor and repair understand connected-source drift, cleanup is atomic and selective, disconnect has a safe global/workspace boundary, and the opt-in surface has a complete operating guide.

The next session should implement Phase 6, run the architecture and known-gaps reconciliation, confirm existing CI includes the new lifecycle test paths on Linux and Windows, obtain authoritative remote matrix results, and hand release readiness to `/update release`.
