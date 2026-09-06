# Session History - v2.4.0 (adoption-compound-engineering-plugin) Phase 4: Remaining skill-native

**Date**: 2026-05-31
**Plan**: [docs/archives/v2/v2.4/plans/adoption-compound-engineering-plugin.md](../../plans/adoption-compound-engineering-plugin.md)
**Phase**: 4 of 8 - Remaining skill-native (A10 crash-safe optimization persistence, A11 product-pulse report skill)
**Sub-tasks**: T017 (skill-eval-loop persistence discipline), T018 (product-pulse skill + registration), T019 (testing + stabilization)
**Outcome**: A "Persistence discipline (crash-safe long runs)" section added to `skill-eval-loop`; one new local-only skill (`product-pulse`) shipped and registered (business-product 5 -> 6; total 241 -> 242). All validators green; orphan-bundle 0/0 across 242 skills; MCP skill-server 43 passed; repo-level tests 331 passed. Persistence checkpoint flow dry-run-verified; product-pulse static trigger-surface check passed; live skill-eval-loop run deferred (DF-v24-3). Phase 4's prerequisite is "None beyond Phase 1", so it was implemented ahead of the still-open Phase 3.

---

## Goal

Adopt the two remaining skill-native compound-engineering items: fold the crash-safe optimization persistence discipline into `skill-eval-loop` (A10) so long-running eval loops survive context compaction and crashes, and add a `product-pulse` report skill (A11) that builds a time-windowed product-outcome report from the user's own local data sources. Both are local catalog content re-authored generically with no source-repo attribution and zero new outbound calls / credentials / dependencies.

## Steps taken

1. **Phase 0 - resolve plan / phase**: parsed the invocation (`4 of v2.4.0 adoption-compoung-engineering-plugin.md`); the real filename is `adoption-compound-engineering-plugin.md` (argument typo). Confirmed the plan at `docs/archive/v2/v2.4/plans/` (legacy flat layout). Phase 4's stated prerequisite is "None beyond Phase 1" (Phase 1 complete), so the still-open Phase 3 does not block it. Final-phase detection: false (4 of 8).

2. **Phase 1 - pre-implementation review**: read the full plan and the Phase-4 sub-tasks; the `skill-eval-loop/SKILL.md` body (244 lines - inline section fits under the 500-line norm); an exemplar business-product skill (`product-manager`) for the SKILL.md contract; the three data registries (skills.json schema + statistics, marketplace category counts, SKILL_INDEX rows + footer) to register correctly. Discovered a pre-existing drift: `SKILL_INDEX.md` footer read "239" while the table held 241 rows (a Phase-2 oversight; the validator does not check the footer, so `make validate` stayed green).

3. **T017 - persistence discipline**: added a "Persistence discipline (crash-safe long runs)" section after the per-iteration loop in `skill-eval-loop/SKILL.md` (write-immediately, verify-by-read-back, re-read-at-phase-boundary, append-only `run-log.jsonl`, per-experiment `started` / `done` crash-recovery markers with a resume procedure that never recomputes a completed experiment), plus a matching binary Verification checklist item. Re-authored generically, no source named.

4. **T018 - product-pulse skill**: created `catalog/skills/business-product/product-pulse/SKILL.md` (134 lines) - a time-windowed report across usage / performance / errors / followups built ONLY from user-supplied local sources, written to `docs/pulse-reports/<window>.md` with deltas versus a prior window. Zero-outbound is asserted in the description, overview, body, and Common Rationalizations. Registered in all three data files (skills.json total 241 -> 242 and business-product 5 -> 6; marketplace business-product 5 -> 6; SKILL_INDEX row appended and the stale footer corrected 239 -> 242).

5. **T019 - stabilization**: ran the validators directly (make unavailable on the host), the MCP skill-server suite and the repo-level pytest, the product-pulse static trigger-surface check, and the persistence checkpoint dry-run; recorded the live-eval deferral (DF-v24-3); ran the post-phase documentation sequence.

## Troubleshooting

- **`make` not on PATH (Windows host)**: invoked the `validate` target's commands directly with `python` (JSON-load checks, `validate_skills.py --bundles-only` / `--quality`, the four CI validators, and the solution-frontmatter validator). All exit 0.
- **Stale `SKILL_INDEX.md` footer**: the footer said "239" but the table held 241 rows (Phase-2 added rows without bumping the footer). Rather than propagate the error (239 + 1 = 240), set the footer to the true post-addition count (242) and recorded the correction under WN-v24-1.
- **No `marketplace.json` `total_skills` field**: unlike `skills.json`, `marketplace.json` has no aggregate `total_skills` / `statistics` block - only per-category `skill_count`. So the marketplace edit was a single `business-product` count bump (5 -> 6), confirmed by re-summing all category counts to 242.

## Assumptions

- Phase 4 may run ahead of Phase 3 because the plan declares its prerequisite as "None beyond Phase 1" and the two phases touch disjoint artifacts (Phase 3: planning-loop wiring + session-query; Phase 4: skill-eval-loop persistence + product-pulse). Phase 3's sub-tasks remain open in the plan.
- The persistence guidance belongs inline in `skill-eval-loop/SKILL.md` (body 244 -> ~275 lines, under the 500-line norm) rather than in a `references/` file; no orphan-bundle concern since nothing new was bundled.
- Coverage gate is not applicable: the phase added Markdown + registry JSON, not executable code, so the plan's skill-native bar (`make validate` + trigger checks) is the operative gate, not an 80% line-coverage threshold.
- Catalog count-prose in README.md ("208 skills") and AGENTS.md ("230 skills across 23 categories", "10 agents") stays deferred to the version bump per WN-v24-1; per-phase doc sync does not touch it.
- `make` / a model CLI are unavailable on this Windows host, so validators were invoked directly and the live skill-eval-loop run is deferred (same constraint as Phase 1's DF-v24-1 and Phase 2's DF-v24-2).

## Testing results

- Registry reconciliation: skills.json array 242 == statistics.total_skills 242; business-product = 6 in skills.json / statistics / marketplace; marketplace category sum 242; SKILL_INDEX footer 242; both modified frontmatter blocks parse as YAML with all required keys.
- `make validate` equivalent (direct): JSON catalogs OK, orphan-bundle audit PASS 0/0 across 242 skills, quality pass 0 errors / 576 warnings (pre-existing Phase-7 debt; neither modified file flagged), no-personal-paths / unicode-safety / supply-chain-iocs / workflow-security / solution-frontmatter all exit 0. None of the Phase-4 files appear in any finding (both ASCII-clean).
- MCP skill-server (`extensions/nexus-skill-server`): 43 passed - confirms the new `product-pulse` frontmatter is consumed by the `search_skills` index.
- `tests/` (repo-level): 331 passed in ~5m20s (no regression; no test hardcodes a skill count).
- `make lint`: N/A - Phase 4 added no shell scripts.
- **Persistence dry-run (PASS)**: simulated the T017 checkpoint flow on a trivial eval - wrote a `started` marker, wrote `grading.json`, verified it by read-back, wrote a `done` marker, appended to `run-log.jsonl`, then simulated a resume that re-read the marker and correctly declined to recompute the completed experiment.
- **product-pulse trigger-surface (PASS, static)**: 7/7 verbatim positive trigger phrases present, an explicit SKIP clause fencing dashboards / real-time monitoring / external-analytics routing / one-off greps, the zero-outbound assertion present, and all six required body sections present.

## Deviations

- **DF-v24-3**: the live `skill-eval-loop` trigger run (1.0 positive / 0.0 fenced-negative) for `product-pulse` was deferred - no model CLI (`claude` / `codex` / `gemini` / `opencode`) on PATH. Substituted with the static trigger-surface check above; foldable into the Phase-8 T037 live run alongside DF-v24-1 / DF-v24-2.
- **WN-v24-1 extended**: updated the count-prose deferral to the 242-skill truth (Phase 4 added `product-pulse`) and recorded that the `SKILL_INDEX.md` footer was corrected from a stale 239 to 242. No README / AGENTS.md prose edited this phase (deferred to bump).
- No `# DEVIATION:` markers were left in any artifact; the plan was followed as written.

## Next steps

- Phase 3 (close the compound loop) is still open: STRATEGY anchor (A5), wire `generate-plan` / `implement-phase` / `continuous-learning` to read `docs/solutions/` (A5), and the cross-tool `session-query` skill (A7).
- Phase 5 (internal RE builds - per-platform capability specs A6, installer `--branch` testing A9) follows.
- Phase 8 T037 should fold in the deferred live `skill-eval-loop` runs for the Phase-1, Phase-2, and Phase-4 skills (DF-v24-1 / DF-v24-2 / DF-v24-3) when a model CLI is available.
