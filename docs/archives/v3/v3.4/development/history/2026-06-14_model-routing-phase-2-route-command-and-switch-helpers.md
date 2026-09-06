# Session History -- v3.4.0 model-routing Phase 2: The /route command + switch helpers

**Date**: 2026-06-14
**Plan**: [`docs/releases/v3/v3.4/plans/model-routing.md`](../../plans/model-routing.md)
**Phase**: 2 of 4 -- The `/route` command + switch helpers (skill-native)
**Branch**: `feat/model-routing` (off `develop`; no version tag cut this phase)
**Outcome**: complete; all Phase 2 sub-tasks closed and the Phase 2 exit checklist is satisfied.

## Goal

Add a thin `/route` command that resolves what to assess (a plan phase, a free-text task, or the current in-flight task), delegates to the `model-routing` skill, presents the recommendation with reasoning, and applies the confirm-then-auto-execute switch posture using bundled per-platform `switch-model` helpers. Phase 2 is the user-facing standalone half of the feature; it is skill-native catalog content only -- no new dependency, credential, remote registry, or third-party processor, and zero new outbound call (the only optional call remains Phase 1's key-gated Anthropic `GET /v1/models`).

## Subtasks completed

1. **2.1 -- Write the `/route` command (thin dispatcher).** Created `catalog/commands/route.md` matching the `plan.md` / `implement.md` thin-dispatcher convention (a pushy SKIP-claused `description` frontmatter for the slash menu; heavy logic stays in the skill). It resolves a TARGET from `$ARGUMENTS` -- a plan phase (`/route phase N of <plan>` / `/route <plan> phase-N`), a free-text task (`/route "<task>"`), or the current in-flight task (bare `/route`) -- delegates to `[[model-routing]]` for detection / live enumeration / scoring, then applies the switch posture per platform tier (execute on scriptable, `/model`+`/effort` keystrokes on Claude Code, picker instruction on Cursor / Copilot / OpenCode). A Notes section states it is platform-agnostic and adds zero outbound calls.
2. **2.2 -- Add the per-platform switch helpers with `.ps1` parity.** Added `catalog/skills/ai-development/model-routing/scripts/switch-model.{sh,ps1}` (stdlib-only, zero outbound, referenced from SKILL.md Step 6 so the orphan-bundle audit stays clean). Contract: `switch-model <platform> <model> [effort]`. Scriptable platforms (Codex / Antigravity `agy` / Gemini CLI) validate the model against the enumerated set, then emit the exact non-interactive switch command; Claude Code prints the `/model`+`/effort` keystrokes; manual-only platforms print the picker instruction. It is idempotent and refuses cleanly: exit 2 (unknown/unrecognized platform), exit 3 (model not in set), exit 4 (set unresolvable). Both `.sh` and `.ps1` were dry-run on this Windows host with identical behavior on every tier.
3. **2.3 -- Register the command surface.** A new command needs no skill-registry edit; bumped the command count 14 -> 15 across the four current-state headline surfaces (README x3, AGENTS.md x2, `.claude-plugin/plugin.json`, `data/marketplace.json` plugin description) and left historical docs untouched. The CHANGELOG entry records the slash surfaces per the v3.3.4 channels: global on Claude (`commands/`), Codex (`prompts/`), Gemini (`workflows/`), Cursor (`~/.cursor/commands/`), Copilot (VS Code `prompts/*.prompt.md`); project-only on Antigravity 2.0 (`.agents/workflows/`, seeded by `nexus-hub init`); body-only via the instruction file on OpenCode. No static command list was touched (`/skills list` derives the cheatsheet at runtime).
4. **2.4 -- Testing and stabilization.** Added `catalog/hooks/tests/test_model_routing_switch.py` (10 cases) asserting every switch tier, the model-in-enumerated-set validation (present -> emit, absent -> exit 3), unresolvable-set refusal (exit 4), unknown/unrecognized-platform refusal (exit 2), and the `.sh`/`.ps1` parity invariant. Added the `## [Unreleased]` CHANGELOG entry. All gates green (see Test results).

## Key decisions

- **Emit the switch command rather than mutate session/config.** A subprocess helper cannot change a sibling CLI's live session, and silently rewriting a user's `~/.codex/config.toml` or `~/.gemini/settings.json` would be a surprising side effect. The deterministic, idempotent switch artifact is the exact non-interactive command (`codex -c model=... -c model_reasoning_effort=...`, `agy -m ...`, `gemini --model ...`), which the agent/user runs next. Documented inline in both helpers.
- **`NEXUS_ROUTING_MODELS` env seam for the enumerated set.** Validation reads the set from `NEXUS_ROUTING_MODELS` when present (a caller that already enumerated once for the session passes its cached set, avoiding a re-enumeration subprocess), else from the sibling `enumerate-models` helper. This also makes the validation contract deterministically testable with no platform CLI installed.
- **Robust raw-blob substring validation, not field extraction.** Platforms name the model field differently (Codex uses `"slug"`, the Anthropic API uses `"id"`) and the JSON carries unrelated ids (e.g. a service-tier `"id":"priority"`), so a targeted field parse is fragile. The helper validates by substring against the live enumeration blob (exact line-match for the clean `NEXUS_ROUTING_MODELS` list); erring toward acceptance is safe because the real CLI rejects a truly-bad model.
- **Picker/config sentinel => cannot validate => refuse (exit 4).** When `enumerate-models` returns an empty-model sentinel (Gemini CLI always; any scriptable platform whose CLI is absent), the helper refuses rather than emit an unvalidated switch.
- **Command count bumped now, not deferred to release.** Mirrors the Phase 1 decision and the plan's explicit sub-task instruction; only current-state surfaces changed (historical docs describe their own moment).

## Troubleshooting

Two defects were caught during dry-run and fixed before the gate:

- **Codex live model failed validation.** The first cut extracted `"id":"..."` fields; Codex's `codex debug models` output names models under `"slug"` and includes an unrelated `"id":"priority"` service-tier field, so a real `gpt-5.5` resolved to the wrong set and returned exit 3. Fixed by dropping field extraction in favor of the raw-blob substring match (both `.sh` and `.ps1`). Re-verified: `gpt-5.5` -> exit 0; bogus model -> exit 3.
- **PowerShell parser error.** `"$effortNote: run ..."` was parsed as a scope-qualified variable reference (`$effortNote:`), failing the whole script load. Fixed with `${effortNote}`.

Also hardened `switch-model.sh` against two ShellCheck/`set -e` patterns ShellCheck would flag (SC2155 on the `readonly SCRIPT_DIR` assignment -> split declaration; a `pipefail` edge case when the model list is whitespace-only -> `|| true`).

## Test results

`make` is not on PATH on this Windows host (WN-v33-1), so the gate was emulated by invoking the validators, scanner, and pytest directly. All green:

- JSON integrity: `data/marketplace.json` and `data/skills.json` parse.
- Orphan-bundle audit (`validate_skills.py --bundles-only`): RESULT PASS, 0 warnings -- all four Phase-1 helpers plus `switch-model.{sh,ps1}` are referenced from SKILL.md.
- `check_version_sync.py`: all six surfaces match canonical 3.3.4 (count-prose edits do not affect version sync).
- v2.3.0 CI validators (no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security): exit 0; every Phase 2 file is ASCII- and personal-path-clean (the 1051 unicode warnings are a pre-existing baseline in a legacy template, not Phase 2 files).
- Skill-security scan (`scan_skill_security.py catalog/skills/ai-development/model-routing --fail-on high`): 7 files scanned, 0 findings, score 0/100 (LOW), exit 0 -- install-OK.
- Hook pytest suite (`catalog/hooks/tests/`): 439 passed, 7 pre-existing skips, including the 10 new `test_model_routing_switch.py` cases.
- Helper dry-runs (bash + PowerShell, identical): codex live-enumerated + validated `gpt-5.5` -> emits `codex -c model=gpt-5.5 -c model_reasoning_effort=high`; codex with `NEXUS_ROUTING_MODELS` -> validate/emit or exit 3; `antigravity` with no CLI -> exit 4; `gemini-cli` no env -> exit 4; `cursor` -> picker; `claude-code` -> `/model`+`/effort`; unknown -> exit 2.

## CI/CD edits

None. The phase added catalog Markdown + a per-skill helper pair + one pytest module. The command file and the skill directory (including `scripts/`) auto-distribute via the installers' recursive copy, so no installer edit was required. CI ShellChecks `catalog/**/*.sh` on the ubuntu runner (`ci.yml`, non-blocking `|| true`), so `switch-model.sh` is linted there; `make lint` itself still covers only the installer scripts.

## Deviations

None material. The plan's sub-task 2.3 says to update `data/marketplace.json` `total_commands`; that field does not exist (the command count lives only in the plugin-description prose), so -- mirroring the Phase 1 count-bump precedent -- the prose count was bumped 14 -> 15 across the four current-state headline surfaces instead. This is a surface reconciliation, not a scope change.

## Known gaps

See [`docs/releases/v3/v3.4/known-gaps.md`](../../known-gaps.md). Open: DF-v34-1 (now narrowed -- `switch-model.sh` is pytest-gated and CI ShellChecks skill scripts; residual is a direct unit test for `detect-platform`/`enumerate-models`), WN-v33-1 (local `make`/ShellCheck unavailable; validators run directly), WN-v33-2 (benign pre-existing global-audit warnings outside this work). No resolved items this phase.

## Next steps

- **Phase 3 -- `/plan` integration (planning-time routing)**: make `/plan` assess every phase and annotate the plan with a recommended model + effort per phase (a "Phases at a Glance" column plus a per-phase field), platform-agnostic and degrading silently when routing is unavailable. Edits `catalog/commands/plan.md` and the retained planning skills, and extends the plan template in `implementation-plan/SKILL.md`.
