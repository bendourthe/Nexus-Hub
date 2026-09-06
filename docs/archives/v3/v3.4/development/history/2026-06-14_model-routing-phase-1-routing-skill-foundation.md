# Session History -- v3.4.0 model-routing Phase 1: Routing skill foundation

**Date**: 2026-06-14
**Plan**: [`docs/releases/v3/v3.4/plans/model-routing.md`](../../plans/model-routing.md)
**Phase**: 1 of 4 -- Routing skill foundation (skill-native)
**Branch**: `develop` (integration branch; no version tag cut this phase)
**Outcome**: complete; all Phase 1 sub-tasks closed and the Phase 1 exit checklist is satisfied.

## Goal

Add the `model-routing` skill -- the brain of the v3.4.0 model-routing feature -- encoding how to detect the agentic platform, enumerate its models live (no hardcoded list), score a task on a complexity rubric, map the score to a model + reasoning effort with a conservative strong-tier default, and describe each platform's switch mechanics. Phase 1 is skill-native catalog content only: no new slash command (that is Phase 2), no code dependency, no credential, no remote registry, no third-party processor, and one optional, key-gated, best-effort outbound call.

## Subtasks completed

1. **1.1 -- Design the routing model and platform-capability abstraction.** Produced an output-only design note fixing the scope (detect / enumerate-live / score / recommend with citations / describe-switch; explicitly NOT switching the Claude Code main loop, NOT keeping a hardcoded list, NOT duplicating `check-usage`), the five-signal complexity rubric (task scope, structural complexity, context volume, risk/blast-radius, mechanical-vs-novel) with the strong-tier-default rule, and the per-platform routing-profile schema (`can_script_switch`, `enumerate_command`, `switch_mechanism`, `effort_knob`, `model_list_source`). Reused the tier abstraction from `multi-provider-ai` (whose matrix is hardcoded) and operationalized `prompt-engineering`'s routing table + effort-level strategy. No file edits.
2. **1.2 -- Write SKILL.md.** Created `catalog/skills/ai-development/model-routing/SKILL.md` (149 lines) per the AGENTS.md contract: pushy SKIP-claused `description` with the plan's verbatim trigger phrases, `summary_l0` (15 words, quoted), `overview_l1` (within the 150-word soft limit, quoted), When to Use + explicit When NOT, numbered Instructions (detect -> enumerate -> score -> map -> assemble -> switch), a "Platform routing profiles" capability table for all 7 platforms across the three switch tiers (scriptable / one-action / manual), 4 Common Rationalizations rows, a binary Verification checklist, and Related Skills. States explicitly that the skill adds no outbound call/dependency/credential and that the optional Anthropic `GET /v1/models` enumeration is best-effort and key-gated.
3. **1.3 -- Add the Tier-3 helpers with `.ps1` parity.** Added `scripts/detect-platform.{sh,ps1}` (normalized platform id from env cues + binary/config presence, zero outbound) and `scripts/enumerate-models.{sh,ps1}` (per-platform enumeration surface; the only optional outbound call is the Anthropic `GET /v1/models` for Claude Code, made strictly when `ANTHROPIC_API_KEY` is set, else a picker sentinel). All four basenames are referenced from SKILL.md (orphan-bundle audit clean). Both `.sh` files pass `bash -n`; both pairs were dry-run on this Windows host (bash + PowerShell) and behave identically.
4. **1.4 -- Register the skill in all three registries.** Added the row to `data/SKILL_INDEX.md`, inserted a full `data/skills.json` entry (after `multi-provider-ai`), and bumped `data/marketplace.json` `ai-development` `skill_count` 10 -> 11. Bumped the catalog total 252 -> 253 across the machine-readable statistics (`skills.json` `statistics.total_skills` + `categories.ai-development`) AND the headline count-prose surfaces the plan named: README (x3 headline lines, leaving the v3.3.4-scoped "still 252 skills" note untouched), AGENTS.md (x2), the SKILL_INDEX Total label, the `marketplace.json` plugin description, and `.claude-plugin/plugin.json`. The bump mirrors the live value (252) + 1 per the plan's no-hardcoded-target rule, since the sibling v3.4.0 adoption plan may also add a skill.
5. **1.5 -- Testing and stabilization.** Added the pushy description to `scripts/validate_skills.allowlist.json` (between `mcp-builder` and `multi-provider-ai`) without shortening it, per the combat-undertriggering mandate. Added a `## [Unreleased]` CHANGELOG entry. Added the four bidirectional `[[model-routing]]` backlinks in `multi-provider-ai`, `prompt-engineering`, `ai-billing-safeguards`, and `agent-orchestration-primitives`. All gates green (see Test results).

## Key decisions

- **No hardcoded model list.** The skill and the `enumerate-models` helper detect and enumerate live from each platform's own surface; the body and Common Rationalizations call out staleness as the reason. This is the central design invariant carried from the plan.
- **Conservative strong-tier default.** Any single `high` rubric signal, or an uncertain reading, pins the strongest available tier + high effort; downshift only on a high-confidence all-low reading. Encoded in both the tier-mapping table and a dedicated rationalization rebuttal.
- **Switch posture branches on `can_script_switch`.** Scriptable (Codex / agy / Gemini CLI) execute; Claude Code emits the `/model`+`/effort` keystroke and auto-routes delegated subagent work; Cursor / Copilot / OpenCode get a picker instruction. The actual `switch-model` helper is Phase 2 scope.
- **`check-usage` cross-referenced as plain `/usage`, not a wikilink.** `check-usage` is a retained skill, not a `catalog/skills` directory, so a `[[check-usage]]` link would dangle; it is referenced as the `/usage` command instead, keeping the dangling-wikilink count at 0.
- **Count prose bumped now, not deferred to release.** Unlike v3.3.0 (which deferred the headline-count reconciliation to release-time), the model-routing plan's sub-task 1.4 explicitly instructs updating the count-prose surfaces during the phase, mirroring the live value + 1.

## Test results

`make` is not on PATH on this Windows host (WN-v33-1), so the gate was emulated by invoking the validators, scanner, and pytest directly. All green:

- JSON integrity: `skills.json` 253 skills; `statistics.total_skills` 253; `categories.ai-development` 11. `marketplace.json` and `plugin.json` parse.
- `check_version_sync.py`: all six surfaces match canonical 3.3.4 (the `[Unreleased]` CHANGELOG heading does not shift the detected version).
- Full validator (scoped, `--allow-existing`): PASS, 0 errors (the 660-char pushy description is correctly grandfathered to a warning; the author/category/version/tags/license soft warnings match the other ai-development skills).
- Bundle orphan audit (scoped): PASS, 0 orphans (all four helper basenames referenced from SKILL.md).
- Quality heuristics (new skill + the four edited skills): PASS, 0 warnings.
- v2.3.0 CI validators (no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security, solution-frontmatter): 0 errors; the new/edited files are ASCII-clean and personal-path-free (pre-existing unicode warnings are elsewhere in the tree).
- Skill-security scan (`scan_skill_security.py ... --fail-on high`): 5 files scanned, 0 findings, score 0/100 (LOW), exit 0 -- install-OK.
- Hook pytest suite (`catalog/hooks/tests/`): 429 passed, 7 skipped.
- MCP skill-server pytest (`extensions/nexus-skill-server`, consumes `skills.json`): 43 passed.
- Helper dry-runs: `detect-platform.{sh,ps1}` both return `claude-code`; `enumerate-models.{sh,ps1} claude-code` both return the picker sentinel (no `ANTHROPIC_API_KEY` set); unknown platform refuses cleanly with exit 2; missing arg errors. Identical behavior on bash and PowerShell.

## CI/CD edits

None. The phase added catalog Markdown + JSON and per-skill helper scripts only. The skill directory (including `scripts/`) auto-distributes via the installers' recursive skill copy, so no installer edit was required. `make lint` (ShellCheck) covers only the installer scripts, so the new `.sh` helpers are not yet gated by CI lint -- recorded as DF-v34-1.

## Deviations

None. The plan's sub-task 1.4 referenced `total_skills` "in `statistics`" of `marketplace.json`; the actual `statistics.total_skills` field lives in `skills.json` (marketplace carries per-category `skill_count` + the plugin-description count prose). Both were updated to keep every surface consistent; this is a file-location reconciliation, not a scope change.

## Known gaps

See [`docs/releases/v3/v3.4/known-gaps.md`](../../known-gaps.md). Three open items: DF-v34-1 (helper ShellCheck/pytest gate deferred to Phase 2.4), WN-v33-1 (local `make`/ShellCheck unavailable; validators run directly), WN-v33-2 (benign pre-existing global-audit warnings outside this work). No resolved items yet.

## Next steps

- **Phase 2 -- The `/route` command + switch helpers**: add `catalog/commands/route.md` as a thin dispatcher to `model-routing`, ship `scripts/switch-model.{sh,ps1}` with `.ps1` parity (validating the requested model against the enumerated set and refusing unknown platforms cleanly), bump `total_commands`, and add the helper unit tests that close DF-v34-1.
