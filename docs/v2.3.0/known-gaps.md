# Known Gaps -- v2.3.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.3.0/plans/adoption-ecc-cybersec-skills.md](plans/adoption-ecc-cybersec-skills.md)
**Status**: Phase 1 of 9 closed (skill-native foundations); Phases 2-9 pending
**Last updated**: 2026-05-28 (Phase 1 close -- two new skill-native catalog entries shipped: `catalog/skills/workflow/context-modes/` (SKILL.md + 3 per-mode references) reverse-engineering ECC's dynamic system-prompt injection, and `catalog/skills/security/security-framework-mapping/` (SKILL.md + standards reference) reverse-engineering the cybersecurity library's MITRE/NIST framework-tag pattern. AGENTS.md "Write SKILL.md" subsection gained a new "Optional Security and Compliance Framework Mapping" block documenting the optional `mitre_attack` / `atlas_techniques` / `d3fend_techniques` / `nist_csf` / `nist_ai_rmf` frontmatter fields plus the `references/standards.md` companion convention. Both new skills pass `scripts/validate_skills.py --verbose` with zero errors and zero bundle-orphan warnings; registry updated in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` (workflow 23 -> 24, security 7 -> 8, total_skills 206 -> 208). Zero installer or extension code changed; zero runtime dependencies added.)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 0 | 0 |
| BG -- Bug or unresolved test failure | 1 | 0 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 1 | 0 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **2** | **0** |

## Open Items

| ID | Title | Category | Source phase | Plan reference | Reason | Suggested next step |
|---|---|---|---|---|---|---|
| BG-v23-1 | `scripts/validate_skills.py` reports 7 pre-existing "Generic secret assignment" false positives in unrelated skills | BG | v2.3.0 Phase 1 (sub-task T003) | [adoption-ecc-cybersec-skills](plans/adoption-ecc-cybersec-skills.md) | The strict validator flags 7 lines across `ai-development/google-antigravity-sdk/SKILL.md`, `documentation/user-documentation/SKILL.md` (2), `infrastructure/cd-pipeline-generator/SKILL.md` (2), and `infrastructure/rollback-strategy-advisor/SKILL.md` (2) as potential generic-secret assignments. Manual inspection confirms each is a documentation example, not a real secret (e.g., `password = "..."` inside a fenced code block teaching against the pattern). The Phase 1 work did not introduce any of these; they predate the phase. They block the strict-mode validator but not `make validate` (which runs `--bundles-only`). | Either (a) refine `SECRET_PATTERNS` in `scripts/validate_skills.py` to ignore matches inside fenced code blocks in `.md` files, or (b) add an in-skill suppression mechanism. Track as a quality-tooling pass; non-blocking for Phase 2. |
| WN-v23-1 | `data/skills.json` skill entry count drifted from `statistics.total_skills` before Phase 1 | WN | v2.3.0 Phase 1 (sub-task T003) | [adoption-ecc-cybersec-skills](plans/adoption-ecc-cybersec-skills.md) | At Phase 1 start, the array contained 207 skill entries while `statistics.total_skills` was `206`. The Phase 1 work added 2 entries (now 209) and bumped the statistic from `206` -> `208` per the plan's explicit instruction, leaving the same 1-skill drift behind. Drift was not introduced by Phase 1; the rebaseline in v2.2.0 known-gaps line 6 set `total_skills` to 207, and `data/skills.json` was bumped one entry beyond that without updating the statistic. | At the next `make build-catalog` / data rebaseline (likely Phase 5 or 6 of this plan), reconcile `statistics.total_skills` against `len(d['skills'])` and re-derive the per-category counts; the build script under `infrastructure/tools/build_skills_catalog.py` is the natural home. |

## Resolved

| ID | Title | Category | Resolved in | Detail |
|---|---|---|---|---|

(none yet -- Phase 1 introduced no regressions to resolve, and no v2.2.0 carryover items map onto Phase 1's skill-native foundations work; the v2.2.0 carryovers begin landing in Phases 7-9.)

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 8.4 (per-phase append), swept by `/wrap-up-session` Phase 6 (catch-all from live conversation), and finalized by `/update-version` at the v2.3.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
