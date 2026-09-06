# Session History - v3.16.0 Phase 4: Freshness governance and documentation

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.0-platform-defaults-config.md](../../plans/v3.16.0-platform-defaults-config.md)
**Phase**: 4 of 5 (not the final phase)
**Branch**: `feat/platform-defaults-config`
**Outcome**: Complete. All four quality gates passed. No production code changed.

## Goal

Keep the lever contract from silently rotting, without adding a new blocking gate, and document the new config surface for future contributors.

## Sub-tasks completed

### 4.1 - Lever re-verification folded into the existing remit

Extended `catalog/skills/workflow/platform-contract-verification/SKILL.md` so its per-release pass covers `docs/policy/platform-defaults-levers.md` alongside the read-contract:

- A per-contract scope table in Step 1 stating what each owns and which one gates.
- Step 2 now re-checks the lever row during the same visit to the vendor's docs, treating a **redirect** as an early signal of vendor reorganization.
- Step 3 classifies lever rows MATCH / DRIFT / UNVERIFIED, with a removed lever flagged as the highest-severity finding (Nexus-Hub may be seeding a setting the platform no longer honours).
- Step 4 gains a shorter lockstep for lever drift: doc, then `configs/platform-defaults.json`, then `--check`, then CHANGELOG. No installer is involved.
- Step 6 states the asymmetry explicitly and forbids adding a marker, script, or CI check for the lever contract.

**No new gate, no new script, no new CI check.** The skill went from 86 to 122 lines, well inside the 500-line norm.

### 4.2 - AGENTS.md documentation

Added a **Per-Platform Install Defaults (v3.16.0)** section covering what the source is, which artifacts are derived and must never be hand-edited, the generator commands, the do-not-invent rule with its `.kimi/agent.yaml` precedent, the seeding semantics, and the scope boundary. Added two "Distribution channels" rows classifying `configs/platform-defaults.json` as a repo-internal source and `scripts/sync_platform_defaults.py` as a repo-internal guard requiring no installer copy step.

The five `base-*.md` templates were **not** touched, and a test now asserts they carry none of this text: a per-platform install default is maintainer-facing configuration, not always-loaded instruction content.

### 4.3 - Verification

The plan asked to "verify the documented generator command works exactly as written by running it", so the commands were run verbatim from the docs rather than paraphrased.

## Test results

| Check | Result |
|---|---|
| `sync_platform_defaults.py --check` (as documented) | exits 0 |
| `--apply` (as documented) | "Already in sync"; tree byte-identical afterwards |
| `--check` again | exits 0 |
| `tests/validators` + `tests/skills` | **800 passed, 3 skipped** |
| Trigger-and-routing gate (description changed) | PASS - 0 collisions, 0 routing failures |
| `validate` guards (7, incl. base-template parity) | All pass |
| `data/*.json` parse | All 5 valid |

## Decisions

- **The advisory/gating asymmetry is now written into the skill, not just practised.** The obvious future edit is someone "tidying up" the inconsistency, so the skill carries a `"The lever contract should hard-gate too, for consistency"` rationalization row answering it: a stale read-contract silently empties an install, while a stale lever contract at worst seeds an outdated default the user can change.
- **The three new rationalization rows are drawn from real Phase 2 findings**, not invented hazards: three vendor doc hosts moved (one a full rebrand), and every Codex search returned a confident secondary source.
- **The AGENTS.md correction was dated and inline.** Silently rewriting a claim leaves a reader who remembers the old one confused about whether the repo changed or the doc was always wrong.

## Troubleshooting trail

- **The first governance test was too crude to be correct.** It asserted `Makefile` and `ci.yml` contain no mention of the lever contract, and failed immediately, because `ci.yml` names it in a comment explaining Phase 2's paths fix -- a comment that should stay. Rewritten to inspect only executed lines (Makefile recipe lines, CI `run:` steps), then verified against a simulated gate line to confirm it still bites rather than passing vacuously.
- **A self-inflicted false alarm.** A probe for `statistics.total_skills` in `marketplace.json` printed MISMATCH; that field does not exist (the file carries per-category `skill_count`). No skill was added, so no marketplace edit was needed.
- **A CHANGELOG edit created a duplicate section.** Inserting Changed and Fixed entries left two `### Fixed` headings and an Added-after-Fixed ordering. Reordered to Keep-a-Changelog convention (Added, Changed, Fixed) with the two Fixed sections merged: 3 sections, 6 bullets, no duplicates.

## Deviations from the plan

None. Sub-task 4.3 also asked to "update CI"; no change was needed, because the skill, AGENTS.md, `data/`, and the tests all live outside `docs/` and therefore already trigger the full job set. The one CI change this cycle needed was made in Phase 3 (installing `tomlkit` and `PyYAML` so the seeding tests cannot silently skip).

**Scope note**: correcting the stale installer/registry claim in AGENTS.md was not in the plan's sub-task list. It was corrected because sub-task 4.2 required adding rows to that exact table, and a new row asserting "no installer copy step needed" sitting above prose claiming platforms bypass the registry would have been actively misleading. Recorded as DF-4.

## Known gaps

DF-4 closed in-phase. No new open items. NI-5 (four declared-but-not-writable platforms) and NI-6 (hermes seedable but not installed by default) remain open for Phase 5.2's disposition.

## Next steps

**Phase 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD**, the plan's final phase. It runs the mandatory refactor plus known-gaps plus CI/CD gate, then hands off to `/update release`; no version bump, tag, merge, or push happens in-phase. Sub-task 5.1 specifically asks whether the four documentation surfaces corrected in v3.15.5 should now point at the defaults file rather than restating a literal value, which is the remaining half of the drift problem this release addresses. Sub-task 5.2 must give an explicit disposition to every UNVERIFIED platform from Phase 2 and every declared-but-not-writable platform from Phase 3.
