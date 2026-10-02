# Decision: Hand a session off before a usage window runs out, with a hook that reads the platform's own usage

Status: proposed - a default-on `usage-guard` hook reads the running platform's own usage through a stdlib probe and, at 99% of a tracked window, directs `/handoff`; a rolling `.nexus-hub/handoff.md` checkpoint covers the overshoot, and on Copilot the hook reads only the Copilot Usage Monitor's percentages file

## Problem

A usage cap is enforced by the vendor's server. Once it is hit, the next model request is rejected and the agent never gets another turn, so the work in progress, and the context needed to resume it on another platform, is lost at the moment it matters. Nothing inside the agent can react at 100%; any reaction has to happen before the cap, and it has to reach the model through the platform's own hook protocol, because only text the model reads changes what it does next.

Two facts decide what is possible per platform: whether a hook can put text in front of the model mid-session and at turn end, and whether the platform's usage can be read from a local process. Both were checked against first-party documentation (recorded in `docs/policy/platform-read-contracts.md`, "Usage-limit handoff hook behaviors"). Claude Code, Codex, and Cursor have both. GitHub Copilot's VS Code Local hooks have the hook channel, but the usage figure sits behind the GitHub sign-in that only a VS Code extension can reach. The remaining platforms have no readable usage source, and some have no shell-hook surface at all.

Reading usage means reading a credential: the Claude Code OAuth token, the Codex `auth.json`, or the Cursor `state.vscdb` token. A hook that reads credentials on every tool call is a new trust surface and needs to be justified, bounded, and recorded.

## Proposal

Ship three layers, owned by distinct artifacts:

1. **Portable contract.** The `session-handoff` skill and `/handoff` command write `.nexus-hub/handoff.md` in a fixed, parseable format and print one paste-ready prompt. Every substantive instruction template carries a parity-guarded Session Handoff block that asks the agent to refresh the file after each verified milestone. This layer works on every platform.
2. **Automatic guard.** The `usage-guard` hook, registered by default on `UserPromptSubmit`, `PostToolUse`, and `Stop` (Cursor: native `postToolUse` and `stop`), calls `catalog/hooks/_usage_probe.py`. At `NEXUS_HANDOFF_THRESHOLD` (default 99) of a tracked window it injects one directive to finish the current step and hand off, and at turn end sends one continuation if the agent stopped without doing so. Platforms are identified by positive payload signatures only; anything unrecognized is silent.
3. **Manual fallback.** Where no usage figure is readable, the guard stays silent and the checkpoint plus `/handoff` carry the load.

The probe reads only the credential of the platform already running, calls only that platform's vendor host over HTTPS with redirects refused, never refreshes or writes a token, and caches percentages and reset times only. It is stdlib-only and runs under a 3-second deadline inside the hook's 5-second budget.

**The one accepted exception: Copilot.** A hook is a child process of the agent host and cannot reach VS Code's `context.secrets` or `vscode.authentication.getSession`. Rather than have the hook open a credential store of its own, the Copilot Usage Monitor writes a percentages-only file, `~/.nexus-hub/state/usage-probe/copilot.json`, and the probe's Copilot provider reads that file and nothing else: no network call and no credential. Without the monitor, or for a member with no percentage, the file is missing, stale, or empty and the guard stays silent on Copilot.

**The completion gate yields to a confirmed handoff (v4.13.7 decision 5).** During a full `/implement` run the completion gate and the guard both answer `Stop` and, at the threshold, give opposite instructions. The gate allows the stop, counts no refusal, and writes no blocker only when `.nexus-hub/handoff.md` carries a `usage-limit` header newer than its last refusal AND the probe confirms a tracked window at or over the threshold. It loads the guard and probe only from its own hook directory, never from the repository, so a workspace-scoped install never takes the exception. The completion contract's "Usage-limit handoff" section owns this rule.

## Alternatives considered

- **A lower default threshold (for example 90% or 95%).** Declined. The maintainer chose 99% to use as much of each window as possible. The overshoot risk this creates, where one large turn on a 5-hour window consumes more than the remaining 1%, is covered by the rolling checkpoint rather than by spending more of the window early. The threshold stays configurable through `NEXUS_HANDOFF_THRESHOLD`.
- **Manual-only `/handoff`, with no hook.** Declined. The maintainer asked for the handoff to happen automatically; a user deep in a task rarely watches a usage meter, and the cutoff gives no second chance. `/handoff` remains as the fallback and on-demand path.
- **A status-line-only warning.** Declined. A status line is shown to the human, not to the model, so the agent keeps starting new work into the cap. Only hook context and a turn-end continuation change what the agent does.
- **Reading usage from a user-installed VS Code extension on every platform.** Declined. The usage monitor extensions are optional, are absent from terminal-only platforms such as Claude Code and Codex CLI, and a hook process has no API to query an extension. The probe reads each platform's own source directly; the extension route is used only for Copilot, where no other route reaches the figure.
- **The hook calling `api.github.com/copilot_internal/user` itself on Copilot.** Declined. It cannot obtain the token without reading a credential store of its own, which resolved decision 3 forbids.
- **Inferring the platform by elimination (or from an explicit `--platform` argument).** Declined. Qwen Code receives the same Claude-style events and sets `CLAUDE_PROJECT_DIR`, so elimination would misread it as Claude Code; three hook parsers read the script name from the last command token, so a trailing argument breaks registration. Positive signatures with a silent default were chosen.
- **For the gate interplay: status quo, the guard yielding to the gate, or the gate yielding to the handoff file alone.** Declined respectively because the run records a false `no-progress` blocker at the cap, because the agent keeps working into the cap, and because any agent could release a run by writing the file. The chosen rule needs both the file and a probe-confirmed window.

## Acceptance criteria

- `/handoff` and the `session-handoff` skill produce `.nexus-hub/handoff.md` and a paste-ready prompt on every platform, and all 13 substantive instruction templates carry the parity-guarded Session Handoff block.
- `usage-guard` emits one directive and at most one continuation per window period per session on Claude Code, Codex (after the user trusts it through `/hooks`), Cursor, and Copilot with the monitor running, and emits nothing for Gemini CLI, Qwen Code, Kimi Code CLI, or an unrecognized payload.
- No token appears in the probe cache, the guard state, logs, stdout, or exception text; `catalog/hooks/tests/test_usage_probe.py` carries a leak test that catches each planted leak.
- A handoff file without a probe-confirmed window never releases a completion-gated run.
- `docs/guides/usage-limit-handoff.md` documents activation, validation, configuration, disabling, and the data boundary, and the CHANGELOG carries the five capability-gate elements for `usage-guard`.

## Risks

- **Overshoot.** At 99% the directive can arrive after the cap on a large turn. Mitigated by the rolling checkpoint, not eliminated.
- **Undocumented endpoints.** The Codex `wham/usage` and Cursor `GetCurrentPeriodUsage` endpoints can change shape without notice. The probe then reports `unavailable` and the guard goes silent, which fails safe but silently; the checkpoint still applies.
- **Credential reads on every tool call.** Bounded by the cache (300 seconds, 60 seconds near the threshold), single-flight fetches, a fetch backoff, and the per-vendor host allowlist. The residual is that a hook process with the user's file access reads the user's own sign-in token, the same access the platform itself has.
- **Copilot depends on an optional extension.** Without the Copilot Usage Monitor the guard is silent on Copilot. Copilot CLI's payload is uncaptured and is not claimed as covered.
- **Cursor merge order.** How Cursor combines `followup_message` from two entries of one `hooks.json` `stop` array is undocumented; the directive tells the agent to write the handoff first if another hook asks it to continue.
- **Forged probe cache.** A process with the user's file access could write a cache under `~/.nexus-hub/state/usage-probe/` and release a gated run; this is the same home-directory boundary the completion contract's threat model already states.
