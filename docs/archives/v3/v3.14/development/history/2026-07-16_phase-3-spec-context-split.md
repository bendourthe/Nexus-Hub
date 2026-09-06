# Session History - v3.14.0 Phase 3: spec/context split + spec-as-merge-gate convention

**Date**: 2026-07-16
**Branch**: `feat/codex-lb-adoption` (off `develop`)
**Plan**: [docs/releases/v3/v3.14/plans/v3.14.0-codex-lb-adoption.md](../../plans/v3.14.0-codex-lb-adoption.md), Phase 3 of 6 (not the final phase)
**Scope**: one body-only skill edit + `CHANGELOG.md` + the v3.14 ledger/devlog/history docs. No new skill, no frontmatter change, no registry update.

## Goal

Adopt codex-lb's OpenSpec discipline as a Nexus-Hub convention (C5) - a normative-spec vs free-form-context split and a spec-as-merge-gate rule - while explicitly rejecting the external `openspec` CLI, and map it onto existing surfaces rather than a parallel change-folder tree.

## Sub-tasks completed

1. **3.1 - Extend `spec-driven-development` (body-only).** Added two sections to `catalog/skills/developer-experience/spec-driven-development/SKILL.md`:
   - **Normative Spec vs Free-Form Context**: the normative spec holds only testable FR-### / SC-### items (no prose); rationale/decisions/failure-modes/examples live in free-form context on the existing per-version `docs/` tree or an optional `context.md`. The external `openspec` CLI is explicitly not adopted (convention only), cited to the MCP Registry Policy.
   - **The Spec as a Merge Gate**: behavior / API / schema / CLI changes update the spec before code, and are not review-ready until spec, code, and tests agree; mapped onto `/spec`, `cross-artifact-analyzer`, `implementation-convergence`, and the merge-readiness contract.
   - Added two Common Rationalizations rows and cross-links to `implementation-convergence`, `review-trapdoors`, and `quality-gate-definitions`.

## Validation (make unavailable on this Windows host; ran the validate target's commands directly)

- Bundle audit: PASS (0 errors).
- Quality-heuristics: 0 errors (no warnings on the skill; no dangling wikilinks).
- Unicode safety: 0 errors. My additions are ASCII; the two em-dash WARNs reported in the file are pre-existing rows whose line numbers shifted, left untouched (out of scope).
- skills.json parses at 267 skills (unchanged - body-only edit).
- Skill size: 285 -> 316 lines (under the 500 soft cap).

## Deviations

- None. The edit stayed body-only as planned; no frontmatter change means no registry update, matching the plan's Phase 3 stability gate.

## Known gaps added

- None new. Status advanced to Phases 1-3 complete; the Phase 3 capabilities bullet was added. HO-1 (skill-name collision for `review-trapdoors`) still pending the Phase 6.4 dry-run install. See [docs/releases/v3/v3.14/known-gaps.md](../../known-gaps.md).

## Next steps

- Phase 4: declarative skill-activation ruleset + guard/tracker hooks (C1) - the flagship agentic build, with an ask-first `catalog/hooks/settings.json` edit and `.py`/`.ps1` parity.
- Before `/update release` (Phase 6): resolve the v3.14.0 version-number collision with the held `feat/agentic-setup-adoption` plan.
- Phase 6.4 dry-run install: verify the HO-1 no-collision check for `review-trapdoors`.
