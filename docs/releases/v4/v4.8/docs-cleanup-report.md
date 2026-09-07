# Docs Cleanup Audit - v4.8

Audit-mode report from [[docs-layout-refactor]], run at each phase boundary of the v4.8.0 adoption plans. Audit mode moves no files; it reports what a later apply-mode run would propose.

**Last run**: 2026-09-07, at the v4.8.0 Phase 1 boundary.

## Phase 1 (loop intake and run contract)

**Finding: clean. Nothing to propose.**

Every documentation file this phase created or changed is already at its canonical path under the lifespan rule:

| File | Placement | Correct because |
|---|---|---|
| `docs/releases/v4/v4.8/development/history/2026-09-07_...phase-1-loop-intake-and-run-contract.md` | Active release tree, `development/` subtree | Per-phase evidence stops changing when the release closes, so it belongs to the release tree and ages out under the retention policy. |
| `docs/releases/v4/v4.8/known-gaps.md` | Active release tree, root | The gap ledger is release-scoped by design and never ages out. |
| `docs/releases/v4/v4.8/docs-cleanup-report.md` (this file) | Active release tree, root | Audit output for one release; superseded when the next release audits itself. |

No scratch, draft, or working document was created outside those paths, so there is nothing to propose cleaning up and no reference to repair.

The phase's other deliverables are catalog content (`catalog/skills/**`), not project documentation, and are outside this audit's scope: their placement is governed by the skill-bundle convention in `AGENTS.md` and is enforced by `validate_skills.py --bundles-only`, which reported `0 errors` with no orphan-bundle warning for the affected skill.

## Phase 2 (autonomy ladder and graph gate)

**Finding: clean. Nothing to propose.**

One documentation file added, at its canonical path: `docs/releases/v4/v4.8/development/history/2026-09-07_...phase-2-autonomy-ladder-and-graph-gate.md`. No scratch or draft document was created, and no reference needed repair. The phase's other deliverables are catalog content, outside this audit's scope and covered by the bundle audit, which reported 0 errors with no orphan warning for the affected skill.

## Phase 3 (verifier taxonomy, research finish line, and skill lifecycle)

**Finding: clean. Nothing to propose.**

One documentation file added, at its canonical path: `.../development/history/2026-09-07_...phase-3-verifier-taxonomy-research-finish-line-and-skill-lifecycle.md`. No scratch or draft document was created. This phase also changed a file outside `docs/` and outside `catalog/skills/` for the first time in the plan (`catalog/commands/research.md`); that is catalog content governed by the commands convention in `AGENTS.md`, not project documentation, so it is outside this audit's scope and needs no registry update (a command change requires none).

## Phase 4 (OWASP agentic framework mapping)

**Finding: clean. Nothing to propose.**

Two documentation files added, both at canonical paths: the Phase 4 session history under `.../development/history/`, and a decision record at `docs/decisions/implemented/policy/2026-09-07-owasp-agentic-top-10-as-seventh-framework-field.md`. The decision record's placement was checked against `docs/decisions/README.md` rather than assumed: lifecycle `implemented` because the design shipped in this phase, class `policy` because it settles what the catalog is allowed to claim about framework coverage rather than how the repo is structured. `validate_decision_records.py` accepts it (38 records OK).

`docs/framework-coverage.md` and `docs/attack-navigator-layer.json` were regenerated in place. Both are generated artifacts with an existing `--check` freshness gate, so they are neither new files nor candidates for relocation.

No scratch or draft document was created. The one scratch skill used to exercise the validator's negative case was written outside the repository tree and removed, so it never entered the catalog or this audit's scope.

## Phase 5 (architecture refactor, known-gaps reconciliation, and CI/CD)

**Finding: clean. Nothing proposed, nothing applied.**

This phase ran the audit as a last-phase DUTY rather than as a per-phase pass, so its full output (empty directories, root tracked-status table, retention result) is quoted under `## Architecture refactor` in [`development/last-phase-evidence.md`](development/last-phase-evidence.md) rather than duplicated here. Summary: no empty tracked directory, no duplicate, no non-version orphan, no structure to simplify; one advisory (`image.png` is untracked and unignored, pre-existing and the maintainer's) reported and deliberately not acted on.

Documentation files added by this phase, all canonical: `development/last-phase-evidence.md` (the release-blocking artifact) and the Phase 5 session history under `development/history/`. `known-gaps.md` gained seven entries across phases 1, 4, and 5. The plan file's completed task and exit-checklist lines were marked, with three lines deliberately left unchecked because they describe remote work that has not happened.

`docs/handbooks/` was checked and correctly holds no generated HTML: `markdown/` has no authored pages, and `handbooks/README.md` states that an atlas and per-component companions are deliberately not invented for a catalog repository. That is a self-gate holding, not an omission.

## Standing note

`scripts/check_docs_retention.py` (advisory, never fails) reported no v4.8 subtree due for archival, which is expected: v4.8 is the active minor.
