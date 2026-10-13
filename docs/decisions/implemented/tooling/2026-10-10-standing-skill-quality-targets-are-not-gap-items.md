# Decision: standing skill-quality targets are not known-gap items

Status: implemented - the SKILL.md body-length target and trigger-eval coverage stay as per-edit rules and are no longer tracked as known-gap items.

## Problem

Two v4.13 ledger items, AR-07 ("Many SKILL.md bodies exceed the 500-line target", 68 of 340 on 2026-10-10) and AR-09 ("Most skills lack trigger-case evals", 89 of 340), describe catalog-wide coverage levels rather than discrete defects. Both rules already say how they improve: AGENTS.md sets a 500-line target with an 800-line hard cap that `scripts/validate_skills.py --bundles-only` enforces, and asks for long-tail sections to move to `references/` when a skill is substantially edited. `guides/reference/SKILL_BUNDLED_RESOURCES.md` declares `evals/trigger-cases.json` optional, so a missing file warns and never fails. Neither item can reach a terminal state through one change, so each would migrate to every future minor without ever closing.

## Decision

Retire AR-07 and AR-09 as known-gap items. The rules stay in force and unchanged: the body-length target and hard cap in AGENTS.md, and optional trigger evals added when a skill is next rewritten, prioritizing dual-use and high-traffic routing collisions. Progress is read from the source whenever wanted, with `find catalog/skills -name trigger-cases.json | wc -l` for evals and the `validate_skills.py` size warnings for body length.

Reopening trigger: a specific skill whose length or missing evals causes a measured routing or loading failure, which becomes its own discrete gap item.

## Alternatives considered

**Keep both items migrating.** Rejected. A standing target as a gap item never closes, inflates every successor ledger's open count, and hides the discrete items that can close.

**Bulk-rewrite the 68 long skills and author 251 eval files in one patch.** Rejected. AGENTS.md explicitly forbids bulk-rewriting skills in a patch, and generated evals written without real routing collisions would assert nothing useful.

**Make the eval file mandatory and fail validation without it.** Rejected. It would turn an optional contract into a hard gate for 251 skills at once and block unrelated work.

## Consequences

- v4.13 AR-07 and AR-09 close on this record, approved by the maintainer on 2026-10-10 during v4.13.11 Phase 8.
- The existing validator warnings and the per-edit rules remain the only mechanism; nothing in the catalog changes.
