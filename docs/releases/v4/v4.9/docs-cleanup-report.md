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

## Phase 2 audit update

The inventory helper completed with ten existing release files before the Phase 2 history was added. New routing policy, explanatory reference, and bundled scripts live beside their owning skills; Phase 2 history remains in development/history. No paths moved, no sibling-plan files changed, and no rename map is needed. Existing inbound-reference evidence remains applicable to unchanged paths; added relative links were checked against their actual targets. No scratch-document deletion is proposed.

## Phase 3 audit update

Graph-seeding guidance and its pure helper remain under security-review. Capability probes and historical/repaired evidence remain under active v4.9 development; no paths moved or living release records were added. The blocked history is preserved and superseded by the Phase 3 completion history. Link, ASCII, and diff checks run before the phase commit.

## Phase 4 audit update

The inventory completed for 16 existing release files before adding Phase 4 history. The normalized-envelope contract and helper remain with security-review; golden inputs/outputs remain test fixtures. The user guide remains living documentation. No files moved or sibling-plan records changed. New relative links and ASCII are checked before the phase commit; no scratch deletion is proposed.

## Phase 5 audit update

The SARIF mapping and both runtime files remain bundled with security-review. Golden SARIF outputs stay under tests/fixtures/security-audit and the phase history stays under development/history. The release inventory is refreshed, with no moves, archival changes, sibling-plan edits or proposed scratch deletion. Local links, ASCII and staged diff checks precede the commit.

## v4.9.1 handbook phase audits

The active handbook implementation retains living instructions with their owners and release-only evidence under this tree. No cleanup moves or deletions were required.

- [Phase 1 audit](development/interactive-handbooks/phase-1-docs-audit.md).
- [Phase 2 audit](development/interactive-handbooks/phase-2-docs-audit.md).
- [Phase 3 audit](development/interactive-handbooks/phase-3-docs-audit.md).
- [Phase 4 audit](development/interactive-handbooks/phase-4-docs-audit.md).
