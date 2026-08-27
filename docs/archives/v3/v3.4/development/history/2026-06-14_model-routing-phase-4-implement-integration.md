# Session History -- v3.4.0 model-routing Phase 4: /implement integration (per-phase re-confirmation)

**Date**: 2026-06-14
**Plan**: [`docs/releases/v3/v3.4/plans/model-routing.md`](../../plans/model-routing.md)
**Phase**: 4 of 4 -- `/implement` integration (per-phase re-confirmation); the plan's final phase
**Branch**: `feat/model-routing` (off `develop`)
**Outcome**: complete; all Phase 4 sub-tasks closed and every Phase 4 exit-checklist item except the final-phase release step is satisfied. Release readiness (via `/update release`) is handed to the user behind its own confirmation gates and is intentionally not auto-run.

## Goal

Make `/implement` re-run the routing assessment at the start of each phase -- because a stronger or cheaper model may have shipped since planning -- confirm or override the plan's recommendation, and apply the switch posture before the build step; wire a troubleshooting-loop conditional upshift (upshift-only); and update the loop documentation so routing reads as an automated part of the Nexus-Hub loop. Phase 4 folds the routing capability into the implementation half of the loop, completing the `/plan` (Phase 3) + `/implement` integration. It is skill-native catalog + docs content only -- no new dependency, credential, remote registry, or third-party processor, and zero new outbound call (the only optional call remains Phase 1's key-gated Anthropic `GET /v1/models`).

## Subtasks completed

1. **4.1 -- Add a per-phase routing pre-flight to the implement workflow.** Added a new "Per-phase model-routing pre-flight (graceful degradation)" section to `catalog/commands/implement.md` (placed after "Delegation", before "Final-phase release routing"). The pre-flight reads the phase's `**Recommended model**` field (written by `/plan` in Phase 3), invokes `[[model-routing]]` to re-assess against the currently-enumerated live model set, applies the confirm-then-auto-execute posture per platform tier on agreement, surfaces the delta and defaults up on disagreement, and degrades silently to the plan's recommendation (or the session's current model) when routing is unavailable. `implement.md` stays a thin dispatcher (59 lines, well under the 150-line norm); the heavy logic lives in `[[model-routing]]`.
2. **4.2 -- Wire the troubleshooting-loop escalation (conditional upshift).** Added "Step 7: Mid-task escalation during an implement loop (upshift only)" to the `model-routing` skill body and a matching binary Verification item. The rule: when a phase's tests fail repeatedly during the troubleshooting loop (an under-tiering signal), recommend (and, with confirmation, apply) an UPSHIFT to a stronger tier / higher effort; never auto-downshift a model mid-phase while a task is failing. Best-effort and platform-aware (same posture as Step 6). Skill footer bumped to v1.1.0.
3. **4.3 -- Update the loop documentation, the interactive guide, and CHANGELOG.** Extended the `AGENTS.md` "Model Routing in the Plan/Implement Loop" section with a paragraph describing the `/implement` re-confirmation, the disagreement/stronger-default behavior, the graceful degradation, and the troubleshooting-loop upshift; updated `guides/interactive-guide/nexus-hub-guide.html` (a routing note under "The Nexus-Hub loop" covering both `/plan` and `/implement` plus the standalone `/route`, and a `/route` row in the Reference cheatsheet's Plan group); added a routing note to the README core-loop description; and added a `## [Unreleased]` -> `### Changed` CHANGELOG entry. Confirmed and stated in each surface that this is command + skill + docs behavior, NOT a `base-*.md` lockstep change.
4. **4.4 -- Testing and stabilization.** Ran the full validate chain and both pytest suites directly (WN-v33-1). All gates green (see Test results). Confirmed the pre-flight degrades to a non-blocking note and the escalation is upshift-only.

## Key decisions

- **No `implement-phase` skill exists; the pre-flight lands in `implement.md`.** The plan's 4.1/4.2 reference "the retained `implement-phase` skill". Git history confirms there has never been such a skill folder: `implement-phase` was a COMMAND (`catalog/commands/implement-phase.md`, created v0.9.x), renamed to `implement.md` and condensed into a thin dispatcher in v3.0.0; the only file holding the `/implement` workflow is `catalog/commands/implement.md`. This exactly mirrors Phase 3, where the plan named a `generate-plan` skill that also does not exist and the implementer edited `plan.md` + the one real retained skill (`implementation-plan`). So the routing pre-flight (4.1) went into `implement.md` (the command, the dispatcher) and the durable escalation logic + Verification (4.2) went into the `model-routing` skill (the brain, which has a body and Verification). Surface reconciliation, not a scope change.
- **Escalation rule homed in `model-routing`, not in the command.** 4.2 says "document it in the skill body and its Verification". With no `implement-phase` skill to hold a troubleshooting loop, the `model-routing` skill is the correct home for an upshift-on-repeated-failure rule (it is routing logic with a Verification section). `implement.md` carries a one-line pointer to it; the rule itself (Step 7 + a Verification item) lives in the skill.
- **No `data/` edits and no `skills.json` version sync.** Phase 4 adds no skill and no command, so no registry count changes. The `model-routing` SKILL.md footer bump (1.0.0 -> 1.1.0) was NOT synced into `data/skills.json`, matching the Phase 3 precedent (its `implementation-plan` v1.4.0 bump likewise touched only the SKILL.md footer, not `skills.json`). Keeps the change minimal and consistent.
- **No project version bump this phase.** The version surfaces stay at canonical 3.3.4; the v3.4.0 tag is cut by `/update release` at release time, not during phase implementation.
- **`/route` placed in the guide's Plan group.** The new command row was added next to `/plan` in the Reference cheatsheet, because routing is introduced as a planning/loop concern; the row notes it is also auto-run per phase inside `/plan` and `/implement`.

## Troubleshooting

None. The phase is catalog Markdown / prose plus the HTML guide; no defect surfaced during validation. The pre-existing unicode baseline (em-dashes in grandfathered/legacy AGENTS.md, CHANGELOG, README content) is unchanged; every line added this phase is ASCII-clean (verified by a targeted non-ASCII scan of the added lines, and by a strict unicode-safety pass on the two edited catalog files, which is clean).

## Test results

`make` and ShellCheck are not on PATH on this Windows host (WN-v33-1), so the gate was emulated by invoking the validators and pytest directly. Phase 4 is pure catalog Markdown + repo docs + the HTML guide (no new `.sh`), so ShellCheck is not implicated this phase. All green:

- JSON integrity: `data/skills.json` parses (253 skills; unchanged this phase).
- Orphan-bundle audit (`validate_skills.py --bundles-only`): RESULT PASS, 0 errors, 1 warning -- the pre-existing `demo-capture` orphan `.pyc` (local-only/gitignored, WN-v33-2), not Phase 4 content.
- Quality pass (`validate_skills.py --quality`) on the edited `model-routing` skill: PASS, 0 errors / 0 warnings (Common Rationalizations, binary Verification, Tier-1 fields, and Related Skills links all intact after the Step 7 addition).
- Unicode-safety (`--strict`) on the two edited catalog files (`implement.md`, `model-routing/SKILL.md`): clean. Added lines in AGENTS.md / README.md / CHANGELOG.md / the HTML guide verified ASCII-clean by targeted scan.
- No-personal-paths on the changed catalog files: exit 0.
- `check_version_sync.py`: all six surfaces match canonical 3.3.4 (this phase changed no version-carrying surface).
- Hook pytest suite (`catalog/hooks/tests/`): 439 passed, 7 pre-existing skips.
- Repo-level suite (`tests/` -- installer + integrations + validators): 415 passed in 360s (matches the Phase 3 baseline of 415 -- no regressions).

## CI/CD edits

None. The phase edited catalog Markdown (`implement.md`, `model-routing/SKILL.md`) and repo docs (`AGENTS.md`, `README.md`, `CHANGELOG.md`, the interactive guide, plan + known-gaps + this session history). The command file and skill directory auto-distribute via the installers' recursive copy, so no installer edit was required. No new script, hook, dependency, or `base-*.md` template was touched.

## Deviations

- **No `implement-phase` skill to edit.** The plan's 4.1/4.2 assume a retained `implement-phase` skill; none exists (it was always a command). The routing pre-flight landed in `implement.md` and the escalation rule + Verification in the `model-routing` skill -- the architecturally correct homes -- mirroring Phase 3's `generate-plan` resolution. Not a scope change.
- **AGENTS.md routing section extended, not newly created.** Phase 3 created the "Model Routing in the Plan/Implement Loop" section; Phase 4 appended the `/implement` re-confirmation + upshift paragraph to it, as Phase 3's session history anticipated.

## Known gaps

See [`docs/releases/v3/v3.4/known-gaps.md`](../../known-gaps.md). Open: DF-v34-1 (Phase 1-2 helper unit-test residual -- untouched this phase, no helper scripts changed), WN-v33-1 (local `make`/ShellCheck unavailable; validators run directly -- re-confirmed for Phase 4), WN-v33-2 (benign pre-existing global-audit warnings outside this work). No new gaps introduced and none resolved this phase.

## Next steps

- **Release readiness (final phase).** Phase 4 is the plan's final phase, so `/implement` hands off to `/update release` for the consolidated release flow (docs + devlog + gitignore + version bump via `check_version_sync.py` + changelog + refactor, then commit + tag + push) behind its own confirmation gates. This is offered to the user, not auto-run -- no tag or push happens automatically. The `[Unreleased]` CHANGELOG entries for Phases 1-4 become the v3.4.0 release block at that step. Note the separate `adoption-nessie-and-agency-agents` plan is also in v3.4.0 scope; coordinate the version cut accordingly.
