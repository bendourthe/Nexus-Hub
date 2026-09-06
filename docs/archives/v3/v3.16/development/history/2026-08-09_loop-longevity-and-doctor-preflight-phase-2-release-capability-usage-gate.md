# Session History - v3.16.2 Phase 2: Release capability usage gate

**Date**: 2026-08-09
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.2-loop-longevity-and-doctor-preflight.md](../../plans/v3.16.2-loop-longevity-and-doctor-preflight.md)
**Phase**: 2 of 6 (not the final phase; no release-readiness workflow ran)
**Branch**: `develop`
**Outcome**: Complete. Quality gate GO.

## Goal

Make it impossible to ship an opt-in capability that the release notes do not teach the user how to operate, validate, and turn off.

## Sub-tasks completed

### 2.1 - Add the capability usage gate to /update release

Added governance step 6 to the `## release scope: known-gaps, architecture refactor, and CI/CD` section of `catalog/commands/update.md`, alongside the five existing governance steps. The five required elements are given as a table (activation, validation, rollback, authority boundary, documentation link), each with a statement of what it must contain rather than just its name.

Three things were written in deliberately:

- **The asymmetry behind element 4.** Elements 1 through 3 fail loudly - a user who cannot activate, verify, or disable a surface discovers it immediately. An unstated authority boundary fails silently, by letting a user over-trust a surface they enabled. That is why it is the most-skipped and the most damaging, and the gate says so rather than listing all five as equals.
- **Grounding in real surfaces.** `NEXUS_HUB_COPILOT_SKILLS` (commit-visible `.github/skills/` writes), `--enterprise` / `-Enterprise` (activation differs per shell, so element 1 must give both forms), and `NEXUS_DISABLED_HOOKS` / `NEXUS_HOOK_PROFILE=minimal` (where element 4 must state that suppressing a guardrail hook does not make the underlying action safe).
- **A tightly-scoped no-change path.** The gate applies only to opt-in surfaces and is explicitly not a checklist against the diff. A release with no applicable change satisfies it with one declaration. The declaration is required rather than optional, because an explicit "checked and none applied" is the only thing distinguishing a run from a skip.

Added a compact cross-reference in `AGENTS.md` immediately after the branching-and-release rationale, carrying the five elements, the four worked surfaces, the element-4 warning, and the scope limit, then pointing at governance step 6 for the full definition.

### 2.2 - Testing and stabilization

## Test results

| Suite | Result |
|-------|--------|
| `tests/skills` | 509 passed, 3 skipped |
| `tests/validators` | 542 passed |
| `tests/workflows` | 91 passed |
| `tests/plans` | 91 passed |
| `tests/integrations` + `tests/installer` | 924 passed, 17 skipped, **1 failed** (inherited BG-1) |
| `catalog/hooks/tests/test_installer_smoke.py` | 33 passed |
| `validate` guards (7, run individually) | All pass |

Both edited files are read by tests rather than being untested prose: `AGENTS.md` is the instruction-file source for the integration suites and is asserted by `test_end_of_task_rule.py` and `test_check_base_template_parity.py`, and `update.md` is covered by the registry-consistency and command checks. `check_base_template_parity.py` was run explicitly and passes - `AGENTS.md` is not one of the five lockstep `base-*.md` templates, so editing it requires no template change, which is the same invariant Phase 4.5 will need to re-verify.

Coverage is not applicable: this phase changed two Markdown files and zero executable lines.

## Dry-run of the gate against the two most recent releases

The plan asked for this explicitly as evidence the gate is worth having.

| Release | Verdict | Detail |
|---|---|---|
| **v3.15.10** | **Would have FAILED** | Introduced `NEXUS_NOTIFY_DRY_RUN`, `NEXUS_NOTIFY_DISABLED_FILE`, and the `~/.nexus-hub/notifications-disabled` switch file. Element 1 partial (env vars named, accepted values not), element 3 effectively present (the switch file is the disable path), elements 2, 4, and 5 absent - no readback command, no authority boundary, no canonical documentation link. |
| **v3.15.11** | **Out of scope** | Internal hook-delivery fixes (`build_hook_entries` module resolution, `CODEX_EVENT_ALIASES`) to hooks that are on by default. No opt-in surface introduced or materially changed, so the single no-change declaration satisfies it. |

One fail and one out-of-scope is the discriminating result. Per the plan's instruction, neither release's notes were retroactively edited; the finding is recorded here and in the gap log.

## Composition check

The full release section was read end to end. Step 6 composes with rather than duplicates the existing flow: the version bump, changelog, merge, tag, and GitHub-Release-publish steps all concern *whether the release ships correctly*, while step 6 concerns *whether its notes teach an operable surface*. It sits with the other governance steps before the commit, which is the correct point - release notes are authored during the `changelog` scope, so the gate must run after that and before the tag is cut. The no-change path was verified to be genuinely one line of work.

## Deviations

1. **The Phase 5 validator is described but not named.** Sub-task 2.1's prompt did not ask for it, but 5.3's does, and writing `scripts/check_release_capability_docs.py` into `update.md` now would have created a reference to a nonexistent path. That is the identical defect as NI-1, which was discovered in this very file during this phase. The text states a checker is planned and describes its advisory posture; Phase 5.3 replaces that sentence with the real invocation.

2. **One line outside the sub-task's stated scope was edited.** The section's closing summary enumerated the governance work as "refactor + known-gaps + CI/CD + platform-contract + prompting-staleness"; `capability-usage` was appended so the summary does not under-report the list directly above it.

## Incidental finding

`catalog/commands/update.md` already referenced `nexus-hub doctor` in two places (the `config` delegation line and the `config scope` section) as though it existed. No `doctor` subcommand exists in either installer today. Recorded as NI-1 and deliberately left unedited, because Phase 5.1 and 5.2 build exactly that subcommand and will make the reference true - deleting it now would be churn. It is worth noting that this is the same failure the new gate guards against: documentation asserting a capability the user cannot operate.

## Post-phase steps

| Step | Result |
|------|--------|
| 8.1 gitignore | 0 patterns added (no new artifact) |
| 8.2 Test review | Both edited files are referenced by 20 test modules across `tests/validators`, `tests/integrations`, `tests/installer`, and `tests/plans`; all were run and pass |
| 8.3 CI/CD | No change needed. `catalog/commands/**` and `AGENTS.md` are both outside `docs/` and already inside the `'**'` path filter |
| 8.4 Known gaps | NI-1 and DF-1 raised; dry-run evidence recorded; summary table and Last-updated line refreshed |
| 8.5 Docs cleanup audit | No-op. No documentation file added, moved, or renamed |
| 8.6 Devlog | Entry added at the top of `docs/DEVLOG.md` |
| 8.7 Docs | `AGENTS.md` updated as part of the phase deliverable. README needs no change: no count, frontmatter, or user-facing surface changed |
| 8.8 Session history | This file |

## Next steps

Phase 3 (incident archive practice and backfill) has no prerequisite and can start immediately. Phase 5 now carries three obligations traceable to Phases 1 and 2: MT-1 (schema assertions), DF-1 (the capability-doc validator), and NI-1 (building the `doctor` subcommand that `update.md` already advertises).
