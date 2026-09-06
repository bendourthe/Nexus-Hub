# Session History -- v2.3.0 Phase 1: Skill-native foundations

**Date**: 2026-05-28
**Plan**: [docs/archives/v2/v2.3/plans/adoption-ecc-cybersec-skills.md](../../plans/adoption-ecc-cybersec-skills.md)
**Phase**: 1 -- Skill-native foundations (sub-tasks T001-T003)
**Result**: shipped; all gates green; ready to advance to Phase 2

---

## Goal

Ship the two zero-code, skill-native deliverables that close two capability gaps without changing any installer or extension code: (1) reverse-engineer ECC's `contexts/{dev,review,research}.md` dynamic system-prompt injection as a Nexus-Hub skill for named agent modes; (2) reverse-engineer the cybersecurity library's framework-tag pattern as a cross-mapping skill plus the optional MITRE / NIST frontmatter convention documented in AGENTS.md, paving the road for Phase 6's coverage-matrix generator.

## Sub-tasks completed (3 of 3)

### T001 -- context-modes skill

- Created `catalog/skills/workflow/context-modes/SKILL.md` (104 lines, 8.8 KB) with mandatory `summary_l0` / `overview_l1` quoted strings, a pushy description with verbatim trigger phrases ("switch to dev mode", "review mode", "research mode") and a SKIP clause routing one-off tone changes and persona role-play to other skills.
- Body covers: detecting mode switches (explicit vs implicit), entering / operating / switching / exiting rules, an announcement convention so mode changes are never silent, Common Rationalizations table, binary Verification, Related Skills cross-links to `[[context-engineering]]`, `[[context-optimization]]`, `[[plan-before-code]]`, `[[research-plan-implement]]`, `[[incremental-implementation]]`.
- Three per-mode reference fragments under `references/`: `dev.md` (38 lines -- code-first posture, tight commit loop), `review.md` (54 lines -- read carefully, cite file:line, no edits), `research.md` (57 lines -- compare options, written report). Each fragment lists primary tools, stopping conditions, forbidden actions, common failures, and an exit-hint to the next mode.
- Re-authored from ECC pattern; no upstream source named in the user-facing artifact per the Reverse-Engineering Attribution Rule.

### T002 -- security-framework-mapping skill + AGENTS.md frontmatter convention

- `AGENTS.md` "Write SKILL.md" subsection gained a new "Optional Security and Compliance Framework Mapping" block (inserted between "Three-Tier Loading Model" and "Required body sections"). The block:
    - Documents the five optional fields with a table: `mitre_attack`, `atlas_techniques`, `d3fend_techniques`, `nist_csf`, `nist_ai_rmf`.
    - Shows an example frontmatter for `hunting-credential-dumping`.
    - Requires a companion `references/standards.md` whenever any field is set; the file is purely additive (no Tier-1 cost, validated as optional by `scripts/validate_skills.py`).
    - Names `scripts/build_framework_coverage.py` (Phase 6) as the planned consumer.
- Created `catalog/skills/security/security-framework-mapping/SKILL.md` (143 lines, 13 KB) carrying the five optional fields in its OWN frontmatter as a worked example (`mitre_attack: [T1003.001, T1071]`, `atlas_techniques: [AML.T0047]`, `d3fend_techniques: [D3-NTA]`, `nist_csf: [DE.CM, ID.RA]`, `nist_ai_rmf: [MEASURE-2.6]`).
- Body covers: which framework fits which artifact (a 3-question decision tree), how to resolve identifiers in each catalog with deep-link references, how to record the mapping in frontmatter (bracketed-list convention) and a companion `references/standards.md`, a worked example mapping the canonical `analyzing-network-traffic-of-malware` artifact across all five frameworks, Verification rules (every cited ID must resolve on the framework's current public site), Common Rationalizations, and Related Skills cross-links to `[[nist-ai-rmf]]`, `[[traceability-matrix-generator]]`, `[[security-review]]`, `[[ai-agent-governance]]`, and the four compliance skills.
- Companion `references/standards.md` (58 lines) documents seven framework IDs (T1071, T1003.001, AML.T0047, D3-NTA, DE.CM, ID.RA, MEASURE-2.6) with framework name, short title (cited, not paraphrased), rationale, and deep link. Closing attribution section names MITRE and NIST as taxonomy authorities and reiterates that framework prose is not redistributed.
- Re-authored from public MITRE/NIST frameworks (Reverse-Engineering Attribution Rule); the upstream cybersecurity library is not named in the user-facing artifact.

### T003 -- Validation and registry update

- `data/SKILL_INDEX.md` gained two rows (context-modes under workflow, security-framework-mapping under security); Total bumped from 206 to 208.
- `data/skills.json` gained two skill entries with security defaults `{structural: 100, integrity: 100, semantic: 95, validated: true}`; `statistics.total_skills` bumped from 206 to 208; per-category counts: `workflow` 22 -> 23, `security` 7 -> 8.
- `data/marketplace.json` workflow `skill_count` 23 -> 24, security `skill_count` 7 -> 8, plugin description "206+ curated" -> "208+ curated", category description lines extended to name the new capabilities.
- Cross-surface skill-count sync: `AGENTS.md` line 9 ("Current catalog: 207 skills") -> 208; AGENTS.md project-structure tree comment ("207 skills") -> 208; `README.md` line 7 and line 23 ("206 skills" / "206 curated") -> 208 in both locations; `README.md` line 113 ("206 skills") -> 208 (caught by the global replace).
- Validation results:
    - `python scripts/validate_skills.py --path catalog/skills/workflow/context-modes --verbose` -> PASS, 0 errors, 5 warnings (optional fields `version` / `license` / `author` / `category` / `tags` -- the same warnings every existing Nexus-Hub skill carries).
    - `python scripts/validate_skills.py --path catalog/skills/security/security-framework-mapping --verbose` -> PASS, 0 errors, 5 warnings (same optional fields).
    - `python scripts/validate_skills.py --bundles-only` (the `make validate` audit) -> PASS, 0 errors, 0 warnings across 215 scanned skills. The four new reference files (`workflow/context-modes/references/{dev,review,research}.md` and `security/security-framework-mapping/references/standards.md`) are all referenced from their parent `SKILL.md` body.
    - JSON parse for all 5 registry files -> OK.
    - Strict full-catalog validator surfaces 7 pre-existing false-positive "Generic secret assignment" hits across 4 unrelated skills (`google-antigravity-sdk`, `user-documentation`, `cd-pipeline-generator`, `rollback-strategy-advisor`); none are Phase 1 introductions. Captured as `BG-v23-1` in `docs/archive/v2/v2.3/known-gaps.md`.

## Deviations from the plan

- The plan's T001 prompt suggested "Optionally ship per-mode fragments under references/"; I shipped all three because the SKILL.md body would otherwise have exceeded the 500-line soft target and each mode's specifics (forbidden actions, common failures) reads better as its own scoped reference.
- The plan's T002 prompt described the AGENTS.md change as an addition to the "Write SKILL.md" subsection; I inserted the new "Optional Security and Compliance Framework Mapping" block between the Three-Tier Loading Model and Required body sections so a reader processes the loading-cost framing first (the new block reads more naturally with that context).
- No deviation from the registry instructions: increment `total_skills` (206 -> 208), increment per-category `skill_count`. The pre-existing one-entry drift between `len(d['skills'])` and `statistics.total_skills` was preserved per the plan and tracked as `WN-v23-1` rather than silently corrected.

## Tests added / changed

None. Phase 1 is pure-additive catalog content. The validation surface (`scripts/validate_skills.py`) already exists and was exercised against the two new skills; no new test file was needed because the validator's existing fixtures cover the bundle-orphan and frontmatter parse paths.

## CI/CD edits

None. The CI pipeline (`.github/workflows/ci.yml`) already runs the JSON-parse + `--bundles-only` audit that the new skills feed; both pass under the existing job.

## Known gaps captured

Two entries in `docs/archive/v2/v2.3/known-gaps.md`:

- `BG-v23-1`: 7 pre-existing false-positive secret-pattern hits in unrelated skills; non-blocking for `make validate`; suggested fix is to refine `SECRET_PATTERNS` to ignore matches inside fenced code blocks in `.md` files, or add an in-skill suppression mechanism.
- `WN-v23-1`: `data/skills.json` actual entry count (209 post-Phase-1) drifted by 1 from `statistics.total_skills` (208 post-Phase-1) -- predates Phase 1. Suggested fix is to reconcile at the next `make build-catalog` / data rebaseline (likely Phase 5 or 6 of the active plan).

## Quality gates

| Gate | Threshold | Status |
|---|---|---|
| All tests passing | 0 failures | Pass (no tests touched; validation green) |
| Line coverage | >= 80% | N/A (no code added) |
| Lint errors | 0 errors | Pass (no shell touched; not applicable) |
| Build / compile | Succeeds | Pass (JSON parse clean) |

## Next phase

Phase 2: Security & quality CI validators. Reverse-engineer ECC's four local static-analysis validators (`validate-no-personal-paths`, `check-unicode-safety`, `scan-supply-chain-iocs`, `validate-workflow-security`) as Python scripts wired into `make validate` and both installers. Independent of Phase 1 outputs.
