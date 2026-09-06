# Session History - v3.16.2 Phase 3: Incident archive practice and backfill

**Date**: 2026-08-09
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.2-loop-longevity-and-doctor-preflight.md](../../plans/v3.16.2-loop-longevity-and-doctor-preflight.md)
**Phase**: 3 of 6 (not the final phase; no release-readiness workflow ran)
**Branch**: `develop`
**Outcome**: Complete. Quality gate GO.

## Goal

Turn three skills that already exist into a practice that produces artifacts, without letting the archive become a directory of notes nobody reads.

## Sub-tasks completed

### 3.1 - Establish the incident artifact type

Created `docs/incidents/` with four files:

- **`README.md`** - the artifact type, the `<slug>-YYYYMMDD.md` convention (slug names the failure, not the fix; date is when it was identified), the closed-by-a-change rule, the public-safe requirement and the two mechanical controls behind it, the five required sections, and an index.
- **`TEMPLATE.md`** - title, date, Audience line naming the maintainers and owning skill, Summary, mandatory Public-Safe Shape, mandatory Durable fix as a named-and-linked table. Carries no date suffix, which is how the naming convention keeps it distinguishable from a real note.
- **`shapes.md`** - reusable abstracted patterns, stated once and referenced from each note.
- The two backfilled notes (3.2).

The README states the load-bearing rule plainly: an incident is closed by a change, not by an explanation, and a note with no linked fix is an open item rather than an archive entry. It also gives the practical test - if this failure recurred next quarter with a different person at the keyboard, would anything stop it? - because "someone would remember reading the note" is the answer that means there is no durable fix yet.

### 3.2 - Backfill two real incidents

Both drawn only from what `AGENTS.md` already records; no detail was invented. Both durable fixes were verified to exist before being linked.

- **`powershell-sibling-parse-error-20260709.md`** - the v3.11.0 `session-summary.ps1` parse error that stayed dead on Windows for four minor versions because nothing parsed catalog `.ps1` files. Durable fixes: the unconditional AST-parse gate in CI's `shellcheck` job and `test_hook_sibling_parity.py`.
- **`provenance-ledger-sibling-divergence-20260722.md`** - the v3.15.6 case where the `.ps1` parsed, ran, and disagreed with its `.sh` sibling in two ways (a UTF-8 BOM from `Add-Content -Encoding utf8` on PowerShell 5.1, and `sha256sum` escaping backslash-containing filenames). Durable fixes: the parametrized `run` fixture making every behavioral assertion a parity assertion, and the Windows PowerShell 5.1 CI leg.

The shared shape is written once as **S-1: An unverified cross-platform sibling is silently non-functional**, with its two failure modes separated because they need different controls - mode 1 (never runs) needs an unconditional syntax gate, mode 2 (runs but disagrees) needs parametrized parity plus a real interpreter-version leg. Each note names its blind spot: mode 1's gate cannot see a runtime disagreement, and parity testing cannot tell you both implementations are wrong in the same way.

### 3.3 - Wire the practice into the owning skill

`catalog/skills/infrastructure/incident-postmortem/SKILL.md`:

- **Step 10** now names `docs/incidents/<slug>-YYYYMMDD.md` as the canonical output, makes Public-Safe Shape and Durable fix mandatory, states the closed-by-a-change rule, routes an unfixed incident to [[known-gaps-tracker]], and routes a third recurrence of a failure class to [[solution-knowledge-base]].
- **New surprising-behavior trigger** under When to Use: behavior that is surprising, contradictory, smaller than expected, or called out by the user as likely wrong is an incident, not just a correction. Justified by the observation that the most instructive failures in a catalog-and-installer project never page anyone.
- **New Step 8b, responsible-layer classification**: agent behavior / projection or payload / authoring gap / docs or process, with what a fix at each layer looks like, and the rule to repair at the lowest DURABLE layer - with both error directions named, since "be more careful" is too low and rewriting a process for one malformed payload is too high.
- Four verification items and three Related Skills entries added.

Frontmatter deliberately untouched: its `description` already exceeds the 250-character ceiling and is allowlisted, so editing it would risk the gate and force a `skills.json` sync for no benefit. Body went from 227 to 271 lines, inside the 500-line target.

### 3.4 - Testing and stabilization

Built `scripts/check_incident_notes.py` (stdlib only, repo-internal), because the README promised it and a promised-but-absent script is the same defect this cycle has now flagged twice. It asserts every note carries both required sections and that the Durable fix section holds at least one link, exempts `README.md` / `TEMPLATE.md` / `shapes.md`, and no-ops when the directory is absent so it is safe in a fork.

Wired into `make validate`, the CI `validate` job, and `DEV_ONLY_SCRIPTS` in `test_installer_smoke.py` (repo-internal guard, no installer copy step). Covered by `tests/validators/test_check_incident_notes.py`, 12 tests asserting failure in each direction.

## Test results

| Suite | Result |
|-------|--------|
| `tests/validators` | 554 passed (was 542; +12 new) |
| `tests/skills` | 509 passed, 3 skipped |
| `tests/validators/test_check_incident_notes.py` | 12 passed |
| `catalog/hooks/tests/test_installer_smoke.py` | 33 passed |
| `validate` guards (10, run individually) | All pass |
| `check_incident_notes.py` negative direction | Exit 1 on unlinked fix, on each missing section, and on a bad filename |

Coverage of the new script is exercised through both in-process cases and CLI subprocess runs, including the real repository's notes.

## The CI path-filter decision

Sub-task 3.4 asked to add `docs/incidents/**` to the docs path filters. Taken, but only after building the guard, and the reasoning is recorded because it inverts the instruction's implied order.

`ci.yml` excludes `docs/**` deliberately, with two documented exceptions (`docs/policy/**` and the per-version development contract docs) and an explicit rationale for why session histories stay excluded: no test reads them, so re-including them would run the full matrix on every phase write-up for no signal. Adding `docs/incidents/**` with nothing reading it would have repeated exactly the cost that comment argues against. Building `check_incident_notes.py` first makes the trigger earn its keep, and the added comment states the general rule so the next editor inherits it: a docs path earns a CI trigger only when a guard actually reads it.

Recorded as QG-1, raised and closed inside the phase.

## What verification found: BG-2

The `secret-scan` coverage claim was checked by exercising the hook through its real stdin contract rather than by reading its matcher registration. That found a genuine defect.

**`secret-scan.sh` fails OPEN on a host without `jq`.** It extracts `file_path` and `content` via `jq` and takes an explicit `exit 0` when `jq` is missing. On this host a payload carrying a well-formed AWS access key ID returned exit 0 with no output at all. `secret-scan.ps1` was then verified in both directions on the same host - exit 2 with a correct BLOCKED message on the seeded key, exit 0 on a clean note - so the `docs/incidents/` coverage claim holds on Windows and the finding is bounded rather than total. `AGENTS.md` already documents the asymmetry as acceptable; what is new is evidence that the bash side is inert rather than merely degraded.

A security guard that fails open is worth naming plainly. It is also, precisely, shape S-1: registered, executable, permanently silent. Recorded as BG-2 with a suggested remedy; no hook logic was changed, which is outside this plan's scope.

No scratch incident file was created and deleted. Piping the payloads through the hooks' real stdin contract is the same evidence with no risk of a seeded secret reaching a commit, which is a better outcome than the sub-task's literal "seed a file then remove it" instruction.

## Deviations

1. **A script was built that the sub-task did not name.** `check_incident_notes.py` is not in 3.1-3.4's text. It was built because 3.1's README had to describe how the Durable-fix requirement is "enforced rather than merely requested", and because 3.4's path-filter instruction needs a reader to justify it. Without it, both instructions would have been satisfied in letter and not in substance.
2. **The seeded-secret test was performed against the hook's stdin contract rather than by writing a file.** Same evidence, no risk of committing a seeded credential.
3. **The path filter was added after the guard rather than on its own.** See the CI section above.

## Post-phase steps

| Step | Result |
|------|--------|
| 8.1 gitignore | 0 patterns added. The new files are intentionally tracked; no build artifact or cache was produced |
| 8.2 Test review | Every file added or modified has a test referencing it: the new script has 12, the skill is read by `tests/skills`, `DEV_ONLY_SCRIPTS` by `test_installer_smoke.py`, the workflow by `validate_workflow_security.py`, and the notes themselves by the new guard |
| 8.3 CI/CD | Changed this phase: added the `check_incident_notes.py` step to the `validate` job and `docs/incidents/**` to both events' path filters. Optimization unchanged and already in place |
| 8.4 Known gaps | BG-2 raised; QG-1 raised and closed; an ID collision with Phase 1's BG-1 was caught and renumbered; summary table and Last-updated refreshed |
| 8.5 Docs cleanup audit | `docs/incidents/` is new and sits at the docs root deliberately, because incidents are cross-version and not per-release. Phase 6.1 is instructed to ratify that placement |
| 8.6 Devlog | Entry added at the top of `docs/DEVLOG.md` |
| 8.7 Docs | README and AGENTS.md need no change: no count, frontmatter, or user-facing surface changed. Catalog stays at 271 skills |
| 8.8 Session history | This file |

## Next steps

Phase 4 (engineering discipline transfers: smoke-retention policy, scope-fit pre-add gate, peer claim/lease, projection-sink rule) has no prerequisite and can start immediately. Phase 5 now carries four traceable obligations: MT-1, DF-1, NI-1, and the incident notes' own instruction that the `doctor` PowerShell sibling must be read against both backfilled notes before it is written.
