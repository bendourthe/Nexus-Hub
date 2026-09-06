# Approved interactive authoring contract update

**Status clarification (2026-09-05)**: This is a historical record of the local artifact and isolated, uncommitted instruction drafts. The user clarified that the requested Nexus-Hub work is consolidation of the [master v4.9.0 plan](../plans/v4.9.0-interactive-handbooks-and-presentation-default.md), not acceptance of these drafts as implemented phases. The draft references named below are candidate files, not the distributed release authority. Reconcile them against the master plan before adoption; all seven implementation phases remain pending.

Date: 2026-09-05. Local branch: `feat/approved-interactive-authoring`, based on `develop` at `68f3d082`. The user approved the rebuilt board artifact and authorized applying its lessons to presentify, documentation updates, and release updates. This is a scoped command/skill implementation, not execution or completion of the seven-phase v4.9 reusable-runtime plan.

## Completed

- [x] Make global Presentation Mode entry in the local approved artifact always start at slide 1; preserve targeted chapter entry.
- [x] Update presentify, its direct skill, navigation and visual references, documentation owners, `/update docs` and its `documentation` alias, `/update release`, and the final-plan handoff to the shared authoring contract.
- [x] Validate the affected existing helpers, cross-file instruction contracts, and local board regression checks; retain the full v4.9 runtime qualification work as pending.

## Shared lessons applied

The authoritative distributed output contract is `catalog/skills/specialized-domains/document-to-interactive-html/references/dual-view-handbooks.md`. Handbook freshness belongs to `catalog/skills/documentation/technical-documentation/references/handbook-refresh.md`.

| Concern | Required behavior |
|---|---|
| Entry and intake | Reading page first; optional presentation; global entry always slide 1; separate chapter/resume semantics; independent theme and depth; no standalone slide canvas option |
| Source fidelity | Shared facts across views; complete requested coverage; source-to-slide mapping and source-count ceiling; no automatic continuation slides |
| Figures and imagery | Recoverable charts/maps/diagrams rebuilt with truthful data and labels; photos retain meaningful subject and aspect; source comparison and enlargement |
| Brand and controls | Actual project assets; faithful vector mark and lockup; consistent visible SVG controls; project-specific branding stays local |
| Visual quality | Positive reference comparison plus contextual pattern review; no blanket ban on gradients, color, rounding, or animation; meaningful use of space and varied compositions |
| Flow | Agenda order preserved; content-sized transitions; no redundant neighboring banners; full-width waves with no interior cutoff |
| Theme | Alternate by actual rendered sequence when selected, including light banners where needed; stable presentation theme sequence independent of reading view |
| Scrolling and fit | Native transparent-track themed scrollbars; stage budget excludes chrome; all-slide checks at desktop, intermediate, and breakpoint sizes; explicit compact reflow |
| Verification | Real entry/navigation/history/focus/fullscreen-denial/chart/map/photo checks; reduced motion and offline/no-JS/print; final hashes; separate factual/visual/functional verdicts |
| Maintenance | Preserve approved choices; inventory all handbook layouts; refresh actual candidate before release version changes; deterministic retained sources and read-only freshness checks |

## Verification evidence

- Existing presentify helper and workflow suite: **266 passed**. PowerShell command: `$presentifyTests = @(rg --files tests/skills | Where-Object { $_ -match "test_presentify" }); python -m pytest @presentifyTests tests/workflows/test_presentify_extractor_workflow.py -q --disable-warnings --tb=short`.
- `python scripts/check_agentskills_conformance.py`: **329 skills, 0 errors**.
- `python scripts/validate_skills.py --bundles-only`: **0 errors, 64 advisory warnings**. These are not a clean-warning claim.
- Private local board artifact: **40/40 interaction checks**, no browser errors; all 68 slides checked over 19 desktop viewport sizes plus compact boundaries, with source chart/prose/table/photo preservation and theme/brand refinement checks passing. Final artifact SHA-256: `42162cdebc3e42af5a44bfa661e115ece836075827259c429ae93074d155ded3`. Detailed scripts and JSON evidence remain with the local artifact, not in the distributable catalog.
- `python scripts/run_trigger_evals.py --gate`: **0 routing failures, 0 unallowlisted collisions**; 513 lexical cases across 88 covered skills.
- `git diff --check`: **passed**.
- No CI pipeline, hooks, version, installer, release tag, or global installation changed. Existing hooks cannot reliably infer aesthetic quality; the new instructions require observed browser evidence instead of pretending a stylistic detector guarantees quality.

## Remaining boundary

These tests prove local artifact behavior, helper regressions, and instruction routing/contract consistency. They do not prove that every future agent will follow every instruction or that a generic reusable dual-view runtime exists. The legacy baseline builder and structural scorer remain explicitly partial helpers. Reusable runtime, deterministic generic assembler, automated cross-project quality qualification, installer distribution qualification, and the formal phase gates remain in the v4.9 plan. No phase completion, release, or production-wide guarantee is claimed here.
