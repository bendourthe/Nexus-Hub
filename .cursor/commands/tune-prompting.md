---
description: Refresh how the catalog prompts each current model - enumerate the live roster, web-verify each vendor's own prompting guidance, record it in the per-model profile layer, and auto-apply only model-agnostic authoring improvements behind the full guard suite on an isolated branch. Use when "a new model shipped", "tune prompting for X", "refresh our prompting conventions", "are our prompts stale", "the model roster drifted". SKIP - choosing which model to run (use /route), tuning one prompt for an application (prompt-engineering), or checking usage against limits (use /usage).
---

# /tune-prompting Command

Keep the catalog's prompting conventions current as models ship. `/tune-prompting` enumerates the live model roster, researches each model against its own vendor's primary sources, proves every finding by refutation before recording it, writes the survivors into a bundled per-model profile layer, and then auto-applies only the genuinely model-agnostic authoring improvements to shared bodies, behind the repo's own guard suite, on a branch that stops for human merge.

This is a thin dispatcher over the retained `model-prompting-research` skill. The heavy logic (live enumeration, the research fan-out, the verification bar, the profile schema, the edit-routing hard rail, and the guard-gated apply loop) lives in that skill; this file resolves the arguments and delegates.

Run it the day a new model ships. It is deliberately NOT wired to the release clock: `/update release` only reports roster drift and offers to run this command, never blocks on it.

## Argument resolution

Resolve from `$ARGUMENTS`:

- `/tune-prompting` (bare) - the full flow across every rostered model that needs research.
- `/tune-prompting <model-id>` - restrict to one model. This is the scope-first calibration path and is the right first run on any new setup, because a roster fan-out is a 5-15x token multiplier.
- `/tune-prompting --dry-run` - research, verify, write the profile layer, and emit the gap report, but propose shared-body edits WITHOUT applying them. Nothing outside the profile layer changes.
- `/tune-prompting --profiles-only` - skip the shared-body apply stage entirely. Research and profiles only, no branch, no edits.

`--dry-run` and `--profiles-only` may be combined with a model id. The two differ in intent: `--dry-run` still shows you what it WOULD change in shared bodies, while `--profiles-only` never considers a shared-body edit at all.

## Delegation

Dispatch to the `[[model-prompting-research]]` skill:

      (any invocation) -> model-prompting-research

The skill runs its own sequence, and its `references/research-runbook.md` carries the full procedure. In order:

1. **Precondition check.** No web tool means STOP: log the reason, write nothing, re-stamp nothing. A stale-but-honest layer beats an invented one.
2. **Enumerate the live roster** via `[[model-routing]]`, recording the provenance (`api`, `picker`, `config`, or `manual`). Never a hardcoded model list.
3. **Build the work-list** deterministically with `write_model_prompting_profile.py plan`, which returns the models that are unprofiled, claimless, or carrying only unverified claims.
4. **Calibrate on one model** and confirm the scale before fanning out.
5. **Research each model** against that vendor's own primary sources only, fetching every page it cites.
6. **Adversarially verify** each claim; a claim is recorded only on a primary source plus a majority of independent skeptics failing to refute it.
7. **Write the profile layer** through the deterministic writer, per model as verification completes.
8. **Classify** each survivor with `apply_prompting_edits.py classify` (skipped under `--profiles-only`).
9. **Apply eligible edits** behind the full guard suite on `feat/tune-prompting-<stamp>`, auto-reverting and quarantining anything a guard rejects (skipped under `--dry-run` and `--profiles-only`).
10. **Emit the gap report** and record every quarantined edit and unverified model as a known gap.

## Safety posture

Three properties are load-bearing; state which ones applied on every run:

- **The hard rail.** Model-specific guidance can only ever reach the bundled profile layer. On top of the declared scope, the apply engine blocks any edit that would INTRODUCE a model identifier into a shared body. Note that `check_base_template_parity.py` does NOT enforce this (it checks lockstep between the five templates, so the same model-named line in all five passes it); the engine is what enforces it. See the skill's `references/edit-routing.md`.
- **Branch isolation and human merge.** Every shared-body edit lands on `feat/tune-prompting-<stamp>`, never on `develop` or `main`, and the run always stops for human merge. Confirm before the first commit. Nothing here merges, tags, or pushes.
- **Budget and degradation.** The fan-out is capped per model with a kill switch that stops starting branches at the ceiling, leaving a valid partial layer plus a logged shortfall. The flow degrades from Dynamic Workflows to isolated subagents to a single sequential agent, and to a logged no-op when offline.

## Platform surfaces

As a new command, `/tune-prompting` gets a global slash surface on Claude (`commands/`), Gemini (`workflows/`), Codex (`prompts/`), Cursor (`~/.cursor/commands/`), and Copilot (VS Code `prompts/*.prompt.md`). It is project-scoped via `nexus-hub init` on Antigravity 2.0 (`.agents/workflows/`) and Cursor (`.cursor/commands/`), and reaches OpenCode body-only through its instruction file. Qwen Code receives it as a Markdown command; Kimi Code CLI surfaces it as `/skill:tune-prompting`.

## Notes

- Keep this dispatcher thin. The procedure lives entirely in the `model-prompting-research` skill.
- Adds no outbound call, dependency, or credential: web access is the agent's own `WebSearch` / `WebFetch`, so the MCP Registry Policy is not engaged.
- The standalone command is the primary trigger because model releases do not align with Nexus-Hub releases. The release-time staleness check is a reminder, not a gate.
