# Session History - v3.16.2 Phase 4: Engineering discipline transfers

**Date**: 2026-08-09
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.2-loop-longevity-and-doctor-preflight.md](../../plans/v3.16.2-loop-longevity-and-doctor-preflight.md)
**Phase**: 4 of 6 (not the final phase; no release-readiness workflow ran)
**Branch**: `develop`
**Outcome**: Complete. Quality gate GO.

## Goal

Fold four bounded doctrine items into the files that already own their concerns, without creating a new skill.

## Sub-tasks completed

### 4.1 - Smoke and test retention policy (L7)

Added a `#### Test retention policy` subsection to the hook-testing section of `AGENTS.md`, carrying both halves of the rule.

The keep rule lists five durable-behavior categories (shipped CLI/runtime behavior, a reusable contract, a boundary enforcement, a regression that previously broke something real, a representative fixture). The delete rule -- the half usually missing -- rejects tests whose main purpose is asserting the exact text of a dated note, a transitional decision, or a temporary artifact, and directs shared invariants to a single data-driven aggregate test rather than one near-identical test per artifact. The 500-line size trigger is included, framed as "re-check whether it is really one test" and preferring to move reusable logic into the product module.

**The collision with the existing parity rule was handled explicitly.** In this repo a `.sh` assertion and its `.ps1` twin look exactly like the "near-identical tests to consolidate" the delete rule targets, and consolidating them would destroy the parity property two shipped incidents exist to protect. The policy closes with a paragraph stating that a behavioral assertion parametrized over both implementations is ONE test covering a durable contract, and that the aggregate-test advice applies to per-artifact duplication only.

### 4.2 - Scope-fit pre-add gate (L8)

Added a scope-fit review as the opening of the `## Boundaries` section in `AGENTS.md`, leading with the framing that makes it stick -- treat code volume as a cost, and a good change makes the next change easier to localize, test, and revert.

The gate itself: before adding a module, builder, protocol field, CLI option, fixture, or abstraction, name the shipped behavior, active call site, or explicit compatibility contract requiring it. An uncommitted future runner, a design note, or a hypothetical extension with no validation contract is not one, and the design stays in docs or todo state until the real call site appears. Closes with "we will need it when X lands is a plan, not a call site", and positions the gate as the complement to [[code-simplification]] with a cross-link. Kept to four short paragraphs, because `AGENTS.md` is already long and this is a gate rather than an essay.

### 4.3 - Peer claim and lease arbitration (L9)

Added to Step 2 of `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md`, immediately after the write-scope rules it qualifies and before the role-assignment template.

The distinction from the skill's existing role guidance is stated in one line: a role says what an agent does, a claim says which agent does this specific item right now. An agent holds its role for the whole run and a claim for one item. The minimum claim fields are given as a table (`agent_id`, `item`, `expires_at`), each with the reason it exists rather than just its name.

The expiry case is treated as the load-bearing one, because an expired lease nobody reclaims is the real failure mode and the part most designs leave undefined: the item returns to the queue, its attempt count increments, and after N attempts it routes to the human queue instead of cycling. The note connects a perpetually claimed-expired-reclaimed item to the no-progress stall signature in [[loop-engineering]], since it looks like progress from outside while making none.

Applicability is scoped narrowly and deliberately: only when multiple agents genuinely contend for one shared queue whose items are not knowable in advance. A fan-out with disjoint write scopes -- the case the surrounding rules already cover -- needs no leases and gains only a new expiry bug from adding them.

### 4.4 - Projection sink design rule (L10)

Added a `## Projection-Sink Design Rule` section to `catalog/skills/infrastructure/observability-setup/SKILL.md`, between Best Practices and Common Patterns.

The rule: render an operator-facing display from bounded, public-safe projections with stable ids, never by parsing a project-specific private document, raw transcript, or local path. The reasons are given concretely (coupling to prose formatting, breakage on a reworded heading, widened blast radius) rather than as principle.

The lineage requirement is presented as the non-obvious half, with the four lifecycle fields as a table (`row_lifecycle`, `supersedes`, `superseded_by`, `source_id`) and a stated test: a reader should never have to open a private source document to understand why a row changed. The secondary argument is that ad hoc prose cannot be queried, sorted, or diffed, so a display built on it degrades into something only its author can read.

Grounded in Nexus-Hub's four existing usage-monitor extensions (Claude, Codex, Cursor, GitHub) as the local reference for the artifact class, and cross-links [[egress-redaction]] with the observation that the projection boundary is the natural enforcement point, being the one place every outgoing field is already enumerated.

### 4.5 - Testing and stabilization

## Test results

| Suite | Result |
|-------|--------|
| `tests/skills` | 509 passed, 3 skipped |
| `tests/validators` | 554 passed |
| `tests/plans` | 91 passed |
| `tests/validators/test_end_of_task_rule.py` (reads `AGENTS.md`) | 20 passed |
| `validate` guards (8, run individually) | All pass |

`check_base_template_parity.py` was run explicitly, as 4.5 requires, and passes. `AGENTS.md` is not one of the five lockstep `base-*.md` templates, so these edits disturbed no invariant block and required no template change.

Coverage is not applicable: four Markdown edits, zero executable lines.

## Verification of the 4.5 assertions

| Assertion | Result |
|---|---|
| No new skill was created | Confirmed. Catalog is 271 skills, unchanged since before Phase 1 |
| `data/skills.json` synced only where frontmatter actually changed | Confirmed. Neither skill's `name` / `description` / `summary_l0` / `overview_l1` was touched, checked against the diff; `data/` shows no modification at all |
| Both edited skills stayed within the 500-line body target | **Could not pass as written.** See NI-2 below |
| `AGENTS.md` edits disturbed no `check_base_template_parity.py` invariant | Confirmed by running the guard |

## Deviation: NI-2, a check the plan assumed rather than verified

Sub-task 4.5 asked to confirm both edited skills stayed within the 500-line body target. Both were already over it before this phase: `observability-setup` at 742 lines and `multi-agent-coordinator` at 685. They are now 763 and 703.

Both are grandfathered -- `AGENTS.md` states the size norm is forward-looking and applies to new and substantially-rewritten skills -- and both remain under the 800-line hard cap. So nothing here violates a rule. But reporting "the check passed" would have been false, and reporting nothing would have hidden that a plan instruction described an impossible state.

The additions were kept in the body rather than pushed into `references/` deliberately: each is a short rule that belongs where the reader already is, and relocating a 25-line rule to protect a line count trades discoverability for a number, which inverts what the norm exists to achieve.

`observability-setup` is now within 37 lines of the hard cap. Recorded as NI-2 with the recommendation that the next cycle to add to it splits it into `references/` first rather than discovering the cap mid-edit, and that Phase 6.1's refactor pass makes that call.

## Post-phase steps

| Step | Result |
|------|--------|
| 8.1 gitignore | 0 patterns added (no new artifact) |
| 8.2 Test review | `AGENTS.md` is read by `test_end_of_task_rule.py`, `test_check_base_template_parity.py`, and the integration suites; both skills are read by `tests/skills`. All run and pass |
| 8.3 CI/CD | No change needed. `AGENTS.md` and `catalog/skills/**` are outside `docs/` and already inside the `'**'` path filter; the `docs/incidents/**` filter added in Phase 3 is unaffected |
| 8.4 Known gaps | NI-2 raised; summary table and Last-updated refreshed |
| 8.5 Docs cleanup audit | No-op. No documentation file added, moved, or renamed |
| 8.6 Devlog | Entry added at the top of `docs/DEVLOG.md` |
| 8.7 Docs | No README change needed: no count, frontmatter, or user-facing surface changed |
| 8.8 Session history | This file |

## Next steps

Phase 5, the last substantive phase, and the only one with a prerequisite (Phase 2, now complete). It carries five traceable obligations accumulated so far: MT-1 (schema assertions), DF-1 (the capability-doc validator), NI-1 (building the `doctor` subcommand `update.md` already advertises), the instruction that the PowerShell sibling be written only after reading both backfilled incident notes, and the v3.15.8 QG-2 constraint that any new test directory must be named explicitly in `ci.yml`.
