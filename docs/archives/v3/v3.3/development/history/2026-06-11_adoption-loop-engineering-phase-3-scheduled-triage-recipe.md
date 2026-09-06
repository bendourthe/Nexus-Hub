# Session History -- v3.3.0 adoption-loop-engineering Phase 3: Scheduled-triage recipe and named loop anti-patterns

**Date**: 2026-06-11
**Plan**: [`docs/releases/v3/v3.3/plans/adoption-loop-engineering.md`](../../plans/adoption-loop-engineering.md)
**Phase**: 3 of 4 -- Scheduled-triage recipe + named loop anti-patterns
**Branch**: `feat/adoption-loop-engineering` (Phases 1-2 already complete on the branch)
**Outcome**: complete; all Phase 3 sub-tasks closed and the Phase 3 exit checklist is checked.

## Goal

Express the article's full automation-to-ship loop using only owned/host primitives, and name the loop's human-cost anti-patterns with concrete mitigations. The phase enriches the existing `loop-engineering` and `verification-before-completion` skills rather than adding a new skill. It is catalog-content only: no new skill, no reference file, no command, no JSON registry change, no dependency, no credential, and no new outbound call.

## Subtasks completed

1. **T3.1 -- Add the scheduled-triage recipe.** Added a "Scheduled-Triage Recipe" section to `catalog/skills/workflow/loop-engineering/SKILL.md`, placed after Instructions (Step 5) and before Common Rationalizations so the required-section ordering is preserved. It was added inline rather than as a `references/scheduled-triage-recipe.md` because the body is far under the 500-line size norm (118 lines after the edit), and an inline recipe avoids creating a new orphan-bundle surface while keeping the recipe adjacent to the Step 1 primitive-mapping table it builds on. The recipe is a seven-step automation-to-ship loop, and every step cites the owned/host primitive it uses: (1) cadence via host `/schedule` or `/loop` (referenced as platform commands, never reimplemented); (2) a read-only triage of CI failures / open issues / recent commits; (3) findings persisted to the memory layer via `[[dev-progress-tracker]]` (`docs/todos.md`), `[[known-gaps-tracker]]`, or `[[filesystem-context-patterns]]`; (4) one isolated `git worktree` per viable finding via `[[using-git-worktrees]]`; (5) a maker sub-agent drafting and an independent checker sub-agent reviewing, with `[[adversarial-verifier]]` as the checker, the Phase 2 exit rule, `[[verification-before-completion]]` for the evidence gate, and `[[agent-orchestration-primitives]]` Step 8 for the independent-evaluator rule, where the worktree's `check_command` is the exit evidence; (6) shipping through a host connector (MCP) gated by the MCP Registry Policy (`[[mcp-builder]]`, `catalog/mcp-configs/mcp-servers.json`) with an explicit "if no approved destination exists, stop at the worktree and report" clause; (7) routing needs-human and over-`iteration_cap` items to a human inbox so unhandleable work is surfaced, never silently dropped. The section carries the scope-first token caution, cross-links `[[ai-billing-safeguards]]`, and states it is a recipe to adapt, not a runnable script that introduces a new outbound call or dependency.
2. **T3.2 -- Name the loop anti-patterns.** Added a "Loop Anti-Patterns" section to `catalog/skills/workflow/verification-before-completion/SKILL.md` (placed after Common Rationalizations, before Spirit Over Letter) naming the two human-cost failure modes with mitigations: **cognitive surrender** (the operator stops forming an independent opinion because the automation is comfortable and the green checks feel authoritative; mitigation: verification stays a human responsibility, and the checker that certifies a loop exit must not be the maker, cross-linking `[[agent-orchestration-primitives]]` Step 8) and **comprehension debt** (the gap between shipped code and operator understanding widens each cycle; mitigation: close it deliberately with `[[session-teach-back]]`, the Socratic mastery-confirmation loop). Added `[[session-teach-back]]` to that skill's Related Skills. For the reciprocal backlink (T3.2's explicit requirement), enriched `loop-engineering`'s Step 5 risks discussion to name both anti-patterns and point at `[[verification-before-completion]]` (where they are defined) and `[[session-teach-back]]` (the comprehension-debt countermeasure), and added a `[[session-teach-back]]` entry to `loop-engineering`'s Related Skills.
3. **T3.3 -- Testing and stabilization.** Ran the validators a Markdown body edit can affect and confirmed all green; see Test results.

## Key decisions

- **Recipe inline, not a reference file.** The plan authorized a `references/scheduled-triage-recipe.md` only if the body would exceed the 500-line norm. At 118 lines it does not, so the recipe is inline. This keeps a single source of truth, avoids a new orphan-bundle candidate, and keeps the recipe next to the primitive-mapping table it extends.
- **Every recipe step cites an owned primitive.** The acceptance bar for T3.1 is that each step names the Nexus-Hub surface it uses. The recipe reuses the `[[wikilinks]]` already established in the Step 1 mapping table rather than inventing new primitive claims, so no step introduces an unowned dependency.
- **No new connector is introduced.** The "ship through host connectors" step defers entirely to the existing MCP Registry Policy and instructs the operator to stop at the worktree and report when no approved destination exists. The recipe therefore adds zero new outbound call, dependency, or credential.
- **Pre-satisfied the Phase 4 cross-link audit.** Beyond T3.2's required backlink, `[[session-teach-back]]` was added to both edited skills' Related Skills so the four-skill family (`loop-engineering`, `agent-orchestration-primitives`, `verification-before-completion`, `session-teach-back`) is already bidirectionally linked, reducing Phase 4 rework. `session-teach-back`'s own backlinks are left for the Phase 4 family audit, out of Phase 3 scope.

## Test results

- `make validate`: not runnable locally because `make` is not on PATH (standing condition WN-v33-1). Emulated by invoking the affected underlying validators directly.
- Orphan-bundle audit: `python scripts/validate_skills.py --bundles-only` -- PASS, 0 errors, 1 pre-existing warning (WN-v33-2: `demo-capture` orphan `.pyc`), 252 skills scanned. No new reference file was added, so no new bundle surface.
- Quality heuristics: `python scripts/validate_skills.py --quality` -- PASS, 0 errors, 1 pre-existing warning (`git-branching-workflow` 169-word `overview_l1`), 252 skills scanned. No warning on either edited skill.
- Unicode safety: `python scripts/validate_unicode_safety.py` -- exit 0, 0 errors; the two edited files have zero warnings (additions are ASCII-clean).
- Body size: `loop-engineering/SKILL.md` is 118 lines and `verification-before-completion/SKILL.md` is 111 lines, both well under the 500-line soft norm and the 800-line hard cap.
- Catalog count: `data/skills.json` and `data/marketplace.json` untouched; total unchanged at 252, as required for an enrichment-only phase.
- Cross-link resolution: all 11 distinct `[[...]]` skill names added across the two files resolve to real catalog skill directories (`dev-progress-tracker`, `known-gaps-tracker`, `filesystem-context-patterns`, `using-git-worktrees`, `adversarial-verifier`, `verification-before-completion`, `agent-orchestration-primitives`, `mcp-builder`, `ai-billing-safeguards`, `session-teach-back`, `loop-engineering`).
- MCP Registry Policy: re-confirmed -- the recipe references existing host connectors gated by the policy and introduces no new connector, outbound call, dependency, or credential.

## CI/CD edits

None. The phase edited two catalog Markdown bodies only. The skills auto-distribute via the installers' recursive skill copy, and no shell surface was added, so `make lint` / ShellCheck was not applicable.

## Deviations

None. The validators unaffected by Markdown body edits (version-sync, supply-chain IOCs, workflow-security, solution-frontmatter, context-compressor eval) were not re-run this phase; this is the standing WN-v33-1 local limitation, to be confirmed green on CI, not a scope deviation. The `nexus-skill-scanner` gate (`make scan`) is owned by Phase 4 (T4.2) and was not run here.

## Known gaps

See [`docs/releases/v3/v3.3/known-gaps.md`](../known-gaps.md). Phase 3 introduced no new gaps. The four open items carry forward unchanged: DF-v33-1 (pushy-description allowlist, owned by Phase 4), WN-v33-1 (local `make` / temp-access limitation), WN-v33-2 (pre-existing global audit warnings outside this phase), and WN-v33-3 (headline count prose deferred to release reconciliation).

## Next steps

- **Phase 4 -- Catalog integration, validation, and release readiness**: add `catalog/skills/workflow/loop-engineering/SKILL.md` to `scripts/validate_skills.allowlist.json` (DF-v33-1) without shortening the pushy description; run the `nexus-skill-scanner` gate (`make scan`) and confirm no HIGH/CRITICAL on the new skill; run the cross-link and consistency audit (including `session-teach-back`'s own backlinks for full four-skill bidirectionality); add the `## [Unreleased]` CHANGELOG entry; and walk one seeded loop (e.g. `ship-pr-until-green` with `make validate` as the repo's check) end-to-end as the deliverable demonstration. Then the develop-to-main release via `/update version` (MINOR -> v3.3.0) reconciles the headline count prose (WN-v33-3).
