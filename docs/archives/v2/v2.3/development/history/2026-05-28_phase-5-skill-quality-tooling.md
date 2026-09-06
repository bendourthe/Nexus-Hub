# Phase 5 -- Skill Quality Tooling

**Plan**: [`docs/archives/v2/v2.3/plans/adoption-ecc-cybersec-skills.md`](../../plans/adoption-ecc-cybersec-skills.md)
**Date**: 2026-05-28
**Status**: Closed
**Sub-tasks**: T014, T015, T016

## Goal

Add a holistic skill-quality audit and a git-history-driven skill generator, reverse-engineered from ECC's `skill-stocktake` and `skill-create` patterns, plus a non-blocking quality-heuristics pass in the structural validator. All deliverables are local and zero-outbound per the MCP Registry Policy reverse-engineer-first decision tree.

## Decisions taken before coding

- **T015 form**: the plan left T015 open between a skill-only deliverable and a skill plus a `scripts/skill_create.py` helper. The user chose **skill-only**, matching the plan's stated "preferred form" and keeping the surface minimal (no new standalone script, so no installer registration).
- **Pre-existing gate failure**: `make validate` was already red on the clean tree because `validate_no_personal_paths.py` flagged three prose self-references in Phase 3/4 docs that literally spelled out `/Users/<user>/...` while describing the redaction of personal paths. The user approved redacting those three lines to the `<user>` placeholder (the exact redaction the docs claimed was done) as part of stabilization.

## What was built

### T014 -- skill-stocktake skill + validate_skills quality pass

`catalog/skills/workflow/skill-stocktake/SKILL.md` is a two-mode holistic quality audit:

- **Quick Scan** (default when a cache exists): reads `.nexus/skill-stocktake/results.json`, recomputes a per-skill content hash, and re-scores only skills whose hash changed since the last run -- so an audit after a small edit is near-instant.
- **Full Stocktake**: scores every skill from scratch and rewrites the cache.

The deterministic half of the score is delegated to the validator's new `--quality` pass rather than re-implemented in the skill body; the skill's unique value is the caching layer and the short holistic agent judgment (does the body teach a real procedure, are the rationalizations concrete, is the Verification observable). The skill is propose-only: it ranks skills worst-first and proposes remediation but never auto-edits a SKILL.md, honoring the AGENTS.md "never delete/edit skills without maintainer approval" rule.

`scripts/validate_skills.py` gained:

1. A `_section_body(content, heading)` helper that extracts a `## <heading>` section's body (case-insensitive, runs to the next `## ` heading).
2. A `validate_skill_quality(skill_dir, content)` function returning warning strings (never errors) for four authoring norms: missing `## Common Rationalizations`, prose-only `## Verification` (no `- [ ]` checklist), over-long Tier-1 fields (`summary_l0` > 15 words, `overview_l1` > 150 words), and a missing or unlinked `## Related Skills` section. Each warning carries a `quality:` prefix.
3. A `--quality` CLI flag (mirroring the existing `--bundles-only` structure) that runs only the quality pass and always exits 0.

The pass was wired into the `make validate` target after the bundle audit. Across the catalog it currently surfaces 574 warnings on grandfathered skills (tracked as WN-v23-4); both new Phase 5 skills clear it with zero warnings.

### T015 -- skill-create from git history

`catalog/skills/workflow/skill-create/SKILL.md` teaches the agent to manufacture a new skill from evidence already in the repository: analyze `git log` / `git diff` (local only, zero outbound) for a recurring pattern (a repeated fix, a manual multi-step workflow, a class of change), confirm it with the user against cited commit SHAs, then draft a fully conformant SKILL.md (pushy description with trigger phrases + SKIP clause, quoted Tier-1 fields within their word limits, binary Verification, a Common Rationalizations table citing failure modes seen in the actual commits). The draft is surfaced for maintainer review and never auto-registered or committed. The skill body explicitly fences off the egress trap (no web fetching) as a Common Rationalization.

### T016 -- Testing and stabilization

- Six pytest cases in `tests/validators/test_validate_skills_quality.py`: a low-quality fixture trips every heuristic; a well-formed fixture stays silent; every warning carries the `quality:` prefix; `_section_body` is case-insensitive; and the `--quality` CLI exits 0 on the live catalog (both with and without `--verbose`).
- Tightened the `overview_l1` of both new skills (initially 152 and 162 words) to clear the 150-word quality heuristic they themselves enforce.
- Redacted the three pre-existing personal-path false positives to `<user>`.

## Registration

- `data/skills.json`: 210 -> 212 entries (added `skill-stocktake`, `skill-create`).
- `data/marketplace.json`: workflow `skill_count` 25 -> 27.
- `data/SKILL_INDEX.md`: two new rows; total 209 -> 211.

## Test results

| Suite | Result |
|---|---|
| `tests/` (validators + integrations + installer) | 291 passed |
| `catalog/hooks/tests` | 392 passed, 3 skipped |
| `tests/validators` (incl. 6 new) | 37 passed |
| `extensions/nexus-skill-server` (parses skills.json) | 43 passed |
| `make validate` equivalent (JSON + bundle audit + quality pass + 4 CI validators) | green (all exit 0) |

## Deviations from the plan

- T015 shipped skill-only (no `scripts/skill_create.py`) per the user's Phase 0 decision -- within the plan's stated preferred form, not a true deviation.
- Stabilization touched three Phase 3/4 docs (personal-path redaction) outside the literal Phase 5 file set. This was a pre-existing gate failure, approved by the user, required to make `make validate` green.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs the four CI validators directly and `pytest tests/validators -v`, which auto-picks up the new test file. No CI edit was required: no new standalone script was added (the quality pass extends the existing `validate_skills.py`), and the quality pass is intentionally non-blocking so it is not added as a gating CI step.

## Known gaps

- **WN-v23-4**: the new `--quality` pass surfaces 574 warnings across grandfathered skills (missing Common Rationalizations, prose-only Verification, missing Related Skills links, a few over-long Tier-1 fields). Deliberately non-blocking. Remediate via a dedicated catalog-quality pass driven by the new `skill-stocktake` skill. Does NOT resolve the separate BG-v23-1 (secret-scan false positives in the strict validator).

## Next steps

- Advance to Phase 6 (Framework coverage + defensive security content), which builds on the Phase 1 `security-framework-mapping` convention.
- Optionally run a `skill-stocktake` Full Stocktake to produce the first worst-first catalog-quality ranking and begin remediating WN-v23-4 in batches.
