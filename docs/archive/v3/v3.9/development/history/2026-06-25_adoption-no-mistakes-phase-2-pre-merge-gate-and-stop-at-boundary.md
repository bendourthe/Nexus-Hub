# Session History - v3.9.0 adoption-no-mistakes Phase 2: Pre-merge gate and stop-at-boundary doctrine

**Date**: 2026-06-25
**Plan**: [`../../plans/adoption-no-mistakes.md`](../../plans/adoption-no-mistakes.md) Phase 2 (N2 canonical pre-merge gate, N6 stop-at-the-human-decision-boundary; skill-native)
**Branch**: `develop`
**Outcome**: Complete. All Phase 2 exit-checklist items satisfied; quality gate GO. Phase 2 of 3; not the final phase, so no release-readiness run.

## Goal

Import two more pieces of doctrine from the source tool's agent skill into Nexus-Hub's workflow skills, as local Markdown enrichment only (no new skill, command, hook, outbound call, dependency, or credential): a canonical pre-merge verification gate, a fixed and justified sequence of checks so that "cleared the gate" means the same thing every time (N2, P1), and the stop-at-the-human-decision-boundary doctrine that returns control to the human at a human-owned decision point rather than blocking or busy-polling (N6, P3), split across the shipping skill (ship half) and the loop skill (loop half).

## What shipped

- **`catalog/skills/workflow/shipping-and-launch/SKILL.md`** (body now 172 lines): two additive sections inserted after "When to Use This Skill", before "The Launch Protocol".
    - **Canonical Pre-Merge Gate (2.1, N2)**: a fixed, ordered, seven-step sequence (review the diff, run tests and gather evidence, update docs, run lint and static analysis, rebase then commit and push, open or update the PR, watch CI) with a one-line rationale per ordering decision (review first so the reviewer reads fresh code; docs after tests so they describe code known to work; lint last among local checks so it does not churn over code that may still change). States the "stable meaning" payoff, frames the order as opinionated on purpose with per-run skips as the deliberate exception, and explicitly composes (does not redefine) the per-step skills. Cross-links `[[intent-based-review]]`, `[[multi-agent-code-review]]`, `[[verification-before-completion]]`, `[[demo-capture]]`, `[[pre-commit-checklist]]`, `[[git-branching-workflow]]`, `[[code-commit-workflow]]`, `[[pr-description-writer]]`.
    - **Stop at the Human-Decision Boundary (2.2, N6 ship half)**: distinguishes "validated and ready for a human decision" from "the decision was made"; instructs the agent to stop driving at a human-owned gate (the common case: change validated, CI green, PR open, merge is the human's call), tell the user what is ready and what decision is theirs with the link they need, and hand control back rather than blocking, polling, or re-running. States the busy-wait failure mode (wasted turn loop, possible re-trigger of work) and generalizes beyond merges to any human-owned gate. Cross-links `[[loop-engineering]]` and `[[verification-before-completion]]`.
- **`catalog/skills/workflow/loop-engineering/SKILL.md`** (body now 211 lines): one short paragraph added at the end of the "Stall and Fault Detection" section, before "Workflow-Control Patterns". Frames a human-owned wait (an approval, a merge, an external sign-off) as a fourth pattern that looks like a stall but is not a fault: do not busy-poll for it, because a loop that re-runs waiting for a human is a no-progress signature; hand control back with a crisp summary of what is ready and what decision is requested, and treat the human action as an external resume signal rather than a condition to spin on. Cross-links `[[shipping-and-launch]]`.

## Key decisions / troubleshooting

- **Gate placed before the Launch Protocol, not inside it.** The canonical pre-merge gate is the upstream stage a change passes through to become shippable, so it reads naturally before the existing deploy-focused Launch Protocol phases. The stop-at-boundary subsection sits immediately after the gate because the gate ends at "PR open, CI green" and the merge decision is exactly the boundary it describes.
- **Loop-side note framed as a fourth, non-fault stall class.** Placing it at the end of "Stall and Fault Detection" ties the no-busy-poll rule directly to the existing no-progress detector (a loop re-running while waiting for a human shows no measurable progress), which is the seam the plan called for.
- **Composition, not redefinition.** Each gate step ends with a `See [[skill]]` pointer to the skill that owns the step, and the section states outright that it composes the per-step skills rather than redefining them. Verified non-conflict against `pre-commit-checklist` (format/lint/type/security/fast-tests pre-commit), `code-commit-workflow` (review/stage/message/commit/rebase/push), and `verification-before-completion` (fresh-evidence gate on every claim): the gate orders these, it does not restate their internals.
- **Bidirectional cross-link for the split doctrine.** N6 lives in two skills, so the ship half links `[[loop-engineering]]` and the loop half links `[[shipping-and-launch]]`, establishing the round-trip (the loop file did not previously link the shipping skill).
- **"cleared the gate" instead of "passed the gate".** The forbidden-token discipline flags `passed`/`checks-passed` as the source tool's status enum. To keep the diff unambiguous against both the Phase 2 and the Phase 3 consolidation greps, the framing phrase uses "cleared the gate" rather than the verb "passed".
- **Pre-existing em-dashes left untouched.** The Unicode validator reports 10 em-dash warnings in `shipping-and-launch`, all on pre-existing lines outside the inserted range; per the changed-lines-only scope rule (and the precedent Phase 1 set for `intent-based-review`), they were not modified. All 26 added lines are ASCII-only.
- **Frontmatter deliberately untouched.** Per the plan, the registry/summary-edit decision is deferred to Phase 3 sub-task 3.4; Phase 2 changes only the bodies. CHANGELOG and `docs/v3/v3.9/known-gaps.md` updates are likewise consolidated in Phase 3.

## Verification (quality gate: GO)

- `make` is not on PATH, so the gate ran via its documented Windows equivalents:
    - **Bundle audit** (`python scripts/validate_skills.py --bundles-only`): PASS, 0 errors, 257 skills scanned. The single warning is a pre-existing stray `scripts/__pycache__/*.pyc` under `demo-capture`, unrelated to this phase. No new bundle files were added.
    - **ASCII safety**: a Python scan of all 26 added (`+`) diff lines found zero non-ASCII characters. The 10 em-dash warnings from `validate_unicode_safety.py --path` are all on pre-existing lines (frontmatter and Launch Protocol body), not added content; `loop-engineering` reports 0 warnings.
    - **Dangling-wikilink audit**: all 10 added cross-link targets resolve to real skills (`intent-based-review`, `multi-agent-code-review` under `catalog/skills/code-review/`; `verification-before-completion`, `demo-capture`, `pre-commit-checklist` [under `security/`], `code-commit-workflow`, `pr-description-writer`, `git-branching-workflow`, `loop-engineering`, `shipping-and-launch` under their categories).
    - **Body size**: 172 / 211 lines, both under the 500-line norm.
    - **Attribution grep**: zero matches in the added lines for `no-mistakes`, `kunchenguid`, `checks-passed`, `auto-fix`, `ask-user`, `no-op`, `--intent`, `a.kunchenguid.com`, `NO_MISTAKES_TELEMETRY`, `TOON`, `axi`, and `passed`.
    - **Consistency**: the canonical gate cross-links (does not redefine) the per-step skills; the ship-half and loop-half of the stop-at-boundary doctrine use consistent vocabulary and cross-link each other.

## Files changed

- `catalog/skills/workflow/shipping-and-launch/SKILL.md`
- `catalog/skills/workflow/loop-engineering/SKILL.md`
- `docs/v3/v3.9/plans/adoption-no-mistakes.md` (Phase 2 exit checklist checked off)
- `docs/archive/v3/v3.9/development/history/2026-06-25_adoption-no-mistakes-phase-2-pre-merge-gate-and-stop-at-boundary.md` (this file)

## Next

Phase 3: PR body, optional session matching, and consolidation. Add the optional deterministic-PR-body-from-audit-trail pattern to `pr-description-writer` (N5); make and record the build-or-defer decision on the diff-to-session matching enrichment of `session-query` (N7, recommended default: defer); record the host-side runtime decline and the default-on-telemetry cautionary in `docs/policy/mcp-reverse-engineering-matrix.md`; make the registry-edit decision; and add the consolidated CHANGELOG `## [Unreleased]` entry and `docs/v3/v3.9/known-gaps.md` updates for the whole cycle.
