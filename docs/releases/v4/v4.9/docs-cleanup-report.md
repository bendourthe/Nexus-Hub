# v4.9 Documentation Cleanup Audit

This report records the Phase 1 application-security plan's documentation placement audit for maintainers closing a local phase. It covers the active release tree, its references, and the distinction between living contracts and release evidence.

**Date**: 2026-09-08. **Mode**: audit only. **Scope**: `docs/releases/v4/v4.9/` and the Phase 1 changed living references. No file moves, deletions, or sibling-plan edits.

## Evidence

`python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py inventory --root docs/releases/v4/v4.9 --repo-root .` inventoried nine existing files before this report was added. All were active release material. `refgraph` with the same root completed and identified inbound references; its basename matches are candidates, not proof that a reference names this particular release.

## Disposition

| Material | Category | Disposition |
|---|---|---|
| Application-security plan, known gaps, and Phase 1 history | Active release | Keep in this release tree; update inaccurate draft status in place. |
| Existing handbook plan, analyses, model map, and approved authoring contract | Active release, separate owner | Keep unchanged; outside this phase. |
| Security-review profile reference and skill body | Living distributed contract | Keep beside their owning skill. |
| docs/todos.md | Living progress tracker | Update only the current application-security work. |
| docs/DEVLOG.md | Released-version index | No-op: this phase has not created a release. Narrative belongs in phase history. |

## Verification and limits

No layout contradiction was found among this phase's changed documents. No rename map is required because nothing moved. This scoped audit is not a whole-repository archive cleanup; Phase 7 owns that reconciliation. This report and the phase history remain release-bound evidence, not handbook source.
