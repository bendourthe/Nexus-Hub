# Decision: Remove the completion gate's turn-end registration from the default install

Status: implemented - no default install registers the completion gate on any platform's turn-end event, and an install that already carries it loses the registration on the next install. The gate core, the hook scripts, and the OpenCode, OpenClaw, Pi, and Hermes plugins stay in the catalog as an explicit opt-in. Supersedes the install-by-default part of [install-completion-plugins-by-default](../architecture/2026-09-25-install-completion-plugins-by-default.md).

## Problem

The v4.13.2 completion gate runs at the end of every agent turn during a full `/implement` run and, while the checker reports `INCOMPLETE`, tells the agent to keep going. A turn often ends because the next step needs something the agent cannot supply: an answer from the user, a CI run that has not finished, or an approval. The gate cannot tell those turns apart from a premature stop, so it repeated its refusal on each of them. The result, reported by the repository owner, Benjamin Dourthe, was a run that could not wait for the thing it was waiting on, which made work impossible. The documented platform caps (8 blocks on Claude Code, Copilot CLI, and Qwen; 5 on Cursor; 3 on OpenClaw and Hermes) bound the loop but do not remove the repeated, useless re-prompts before the cap.

## Decision

- **No default registration.** `catalog/hooks/settings.json` no longer registers `completion-gate` on `Stop`. Because Claude Code, Codex, Qwen, Gemini CLI, Kimi, and Copilot render their hooks from that file, they stop registering it together. Cursor (`stop`) and Antigravity 2.0 (`Stop`) no longer render it either, and the repository's own `.agents/hooks.json` drops it.
- **Plugins become opt-in.** The OpenCode, OpenClaw, Pi, and Hermes plugins install only with `NEXUS_HUB_COMPLETION_PLUGINS=1`. Any other value, including unset, writes nothing.
- **Upgrade retires the old entry, ownership-aware.** Claude's settings reconciliation (both installers, jq and Python paths of `installer.sh`, and `installer.ps1`) removes a handler only when its command points at `.../hooks/completion-gate.sh` or `.../hooks/completion-gate.ps1`, the Nexus-Hub hooks directory name; a user's own `completion-gate.sh` elsewhere survives, and a group or event left empty by the removal is dropped. Codex, Qwen, and Gemini CLI already strip every owned handler before merging, Kimi regenerates its marker block, Copilot rewrites its owned file, and Cursor and Antigravity replace only Nexus-Hub's entries, so none needed new logic; tests cover each. A plugin file an earlier install wrote is removed when the install manifest recorded it as Nexus-Hub-owned, and never otherwise.
- **Kept, because other features depend on it.** `scripts/completion_gate.py` (its `capture` mode is how `approval-capture` records genuine approval pastes for the native approval flow, and it hosts the shared usage-decision helpers), `approval-capture`, `usage-guard`, and `check_plan_completion.py`. The `/implement` run still ends on the checker's verdict and `nexus-hub run-plan` still resumes a session that ended early.
- **Opt-in path, cheap and documented.** `catalog/hooks/completion-gate.{sh,ps1}` still install beside the other hooks, unregistered. A user who wants the old behavior registers one on their platform's turn-end event (the event and output format per platform are in `docs/policy/completion-levers.md`), or installs the plugins with `NEXUS_HUB_COMPLETION_PLUGINS=1`. No installer flag was added for the hook platforms, because a per-platform registration switch would touch every adapter for a feature the owner does not want on.

## Alternatives considered

- **Keep the gate and make it quieter.** Throttle refusals, skip them when the last assistant message ends in a question, or add a cool-down. Declined: "waiting on CI" and "waiting on an approval" do not show in the transcript in any form the hook can read reliably across eleven platforms, so any heuristic would either keep the repeated refusals or silently let a premature stop through, and every platform adapter would carry the heuristic.
- **Remove it only locally (the owner's machine).** Declined: the problem is in the shipped default, not one machine, and a local override leaves every other user with the behavior and the next install would restore it.
- **Remove it from the defaults, keep it as an opt-in (chosen).** The smallest change that ends the repeated blocking everywhere, keeps the capture and usage code the approval and handoff flows use, and leaves a documented way back.
- **Delete the stop mode and the hook scripts outright.** Declined for now: the stop mode shares one file with `capture`, the removal would rewrite tests of the usage-handoff rule that still describe real opt-in behavior, and nothing is lost by leaving unregistered code that is exercised by its own tests. It can be removed later with no migration, because no default install references it.

## Consequences

- A full `/implement` run no longer resists a stop. It ends the turn when it needs the user, CI, or an approval, and resumes through `/implement <plan>` or `nexus-hub run-plan`. The checker verdict remains the only definition of done.
- A session that stops mid-plan in an interactive session is not pulled back automatically on any platform; that was the gate's purpose and is the cost of the change.
- Windows hosts carry one more installed file than needed (`completion-gate.ps1`) until someone removes it; it is inert.
- The capability usage gate in the CHANGELOG entry states activation, validation, rollback, the authority boundary, and the documentation link for the remaining opt-in.
