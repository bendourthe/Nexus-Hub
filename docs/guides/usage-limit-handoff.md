# Usage-Limit Handoff

Summary: how Nexus-Hub keeps your work resumable when an AI platform's usage limit runs out, through `/handoff`, the rolling `.nexus-hub/handoff.md` checkpoint, and the automatic `usage-guard` hook.
Read this when: you want to know what happens near a usage limit on your platform, how to turn the automatic guard on or off, how to check it, or what it reads and sends.
Covers: per-platform coverage, the 99% threshold and its known limitation, `/handoff` and the checkpoint format, activation, validation, configuration, the macOS Keychain prompt, disabling, the completion-gate interaction, and the data boundary.

## What it does

A usage cap is enforced by the vendor's server. Once you hit it, the next model request is rejected and the agent gets no further turn, so nothing inside the agent can react at 100%. Nexus-Hub acts before that point, in three layers:

1. **Checkpoint and `/handoff` (every platform).** The `session-handoff` skill writes `.nexus-hub/handoff.md` in the project root and prints one paste-ready prompt that another agent, on any platform, can resume from. Every installed instruction file carries a short Session Handoff rule, so the agent refreshes the file after each verified milestone during long work, and you can run `/handoff` at any time.
2. **Automatic guard (Claude Code, Codex, Cursor, GitHub Copilot).** The `usage-guard` hook reads the platform's own usage figure. When a tracked window reaches the threshold (99% by default), it tells the agent to finish the current step, run the handoff, and start no new work. If the agent ends its turn without doing so, the guard sends one continuation asking for it.
3. **Manual fallback (every other platform).** Where no usage figure can be read, the guard stays silent. Run `/handoff` yourself, or the agent runs it when the platform itself warns about limits.

The handoff is printed and written locally. Nothing switches platforms for you and nothing sends the handoff anywhere.

## Coverage by platform

Verified against first-party hook documentation on 2026-10-01 (sources in the "Usage-limit handoff hook behaviors" section of [`docs/policy/platform-read-contracts.md`](../policy/platform-read-contracts.md)).

| Platform | Directive reaches the agent through | Turn-end continuation | Usage source | Result |
|---|---|---|---|---|
| Claude Code | `UserPromptSubmit` and `PostToolUse` `additionalContext` | `Stop` `decision: block` | Anthropic OAuth usage endpoint | Automatic |
| Codex | `UserPromptSubmit` and `PostToolUse` `additionalContext` | `Stop` `decision: block` | `chatgpt.com/backend-api/wham/usage` (undocumented) | Automatic after you trust the hook once; fragile |
| Cursor | native `postToolUse` `additional_context` | native `stop` `followup_message` | Cursor usage RPC with the local `state.vscdb` token (undocumented) | Automatic; fragile |
| GitHub Copilot (VS Code Local hooks) | `PostToolUse` `hookSpecificOutput.additionalContext` (VS Code's `UserPromptSubmit` has no context field) | `Stop` `decision: block` | the Copilot Usage Monitor's percentages-only file; the hook reads no credential | Automatic while the monitor writes a percentage; silent otherwise |
| Gemini CLI, Qwen Code, Kimi Code CLI | hooks are delivered and recognized | hooks are delivered | none known | Checkpoint and `/handoff`; `usage-guard` stays silent |
| Windsurf, Antigravity | not registered (curated hook lists) | not registered | none known | Checkpoint and `/handoff` |
| OpenCode, Aider, Pi, OpenClaw | no shell-hook surface | none | none | Checkpoint and `/handoff` |

Tracked windows: Claude Code 5-hour and weekly (the highest of the weekly figures), Codex weekly only, Cursor monthly, Copilot monthly.

**Copilot depends on the Copilot Usage Monitor.** A hook process cannot reach VS Code's secret storage or its GitHub sign-in, so on Copilot the guard reads only `~/.nexus-hub/state/usage-probe/copilot.json`, which the monitor writes with percentages and reset times and nothing else. With the monitor not running, the file is missing or older than 30 minutes and the guard stays silent. A Business or Enterprise member without billing access gets no percentage from the monitor, so the guard stays silent for them too. Copilot CLI reads the same hooks directory, but its payload has not been captured, so it is not claimed as covered.

**Slash command reach.** `/handoff` is a slash command where the platform has a slash surface. On platforms without one, the same procedure reaches the agent through its instruction file: ask the agent to "write a handoff" or "run the session-handoff procedure".

## Why 99%, and the known limitation

The trigger is 99% of each tracked window because you chose to use as much of the window as possible before handing off. That leaves 1% of the window. On a 5-hour Claude Code window a single large turn can use more than that, so the automatic directive can arrive after the cap and never be read.

The rolling checkpoint covers that case. Because the agent refreshes `.nexus-hub/handoff.md` after each verified milestone, an abrupt cutoff still leaves a record no older than the last milestone. If you often work in large turns, lower the threshold (see Configuration).

## Using `/handoff`

Run `/handoff`, optionally with a focus:

```text
/handoff
/handoff focus on the failing migration
```

The agent writes `.nexus-hub/handoff.md` and prints one fenced prompt. Paste that block into any agent on any platform; it tells the receiving agent to check the repository state against the record, continue from the first unfinished step, and respect the constraints you stated. The prompt embeds the whole file, so it works even where the receiving agent cannot read the file.

The file has a fixed format: a header line, then the same sections in the same order every time.

```text
# Handoff | 2026-10-01T14:03:27Z | claude | usage-limit weekly 99.2
Previous handoffs: 2026-09-30T18:02:11Z codex manual
## Goal
## Done and verified
## In progress
## Next steps
## Files touched
## Constraints and decisions the user stated
## Open questions and blockers
## Repository state
```

- The header is `# Handoff | TIMESTAMP | PLATFORM | TRIGGER`. `TRIGGER` is `manual`, `checkpoint`, or `usage-limit WINDOW PERCENT`. Hooks parse this line.
- Each Done item carries the command that proved it, and each Next step carries the command that will.
- A new handoff carries forward every unfinished step from the previous one, whichever platform wrote it.
- The agent never writes secrets, tokens, or credential-file contents into the file, and scans it for secret-shaped strings before printing the prompt.
- On the first write in a repository, `.nexus-hub/` is added to the repository's `info/exclude` file, never to `.gitignore`, so the handoff stays local and uncommitted.

The full procedure is the `session-handoff` skill, `catalog/skills/workflow/session-handoff/SKILL.md`.

## Activation

The guard is on by default after a global install. The installer registers `usage-guard` on `UserPromptSubmit`, `PostToolUse`, and `Stop` for Claude Code, Codex, and Copilot, and on native `postToolUse` and `stop` for Cursor.

One platform needs a step from you:

- **Codex**: Codex skips an untrusted hook silently. Open Codex, run `/hooks`, review the `usage-guard` entries, and trust them once. Until then the guard does not run on Codex.

On Copilot, also install and sign in to the Copilot Usage Monitor, which supplies the percentage the guard reads.

## Validation

Run the probe the guard uses. It prints one JSON line and only percentages. Pick the installed copy for your platform:

| Platform | Command |
|---|---|
| Claude Code | `python ~/.claude/hooks/_usage_probe.py --platform claude --json` |
| Codex | `python ~/.codex/hooks/_usage_probe.py --platform codex --json` |
| Cursor | `python ~/.cursor/hooks/_usage_probe.py --platform cursor --json` |
| GitHub Copilot | `python ~/.copilot/hooks/nexus-hub-scripts/_usage_probe.py --platform copilot --json` |

Use `python3` where `python` is not Python 3. A working reading looks like this (values will differ):

```json
{"platform": "claude", "status": "ok", "cached": false, "fetched_at": "2026-10-01T22:34:04Z", "windows": [{"name": "five_hour", "percent": 66.0, "resets_at": "2026-10-02T00:00:00Z", "source": "anthropic-oauth-usage"}, {"name": "weekly", "percent": 98.0, "resets_at": "2026-10-06T14:00:00Z", "source": "anthropic-oauth-usage"}], "reason": null}
```

`status` is `ok`, `stale` (the last good reading, under 30 minutes old, after a failed fetch), or `unavailable` with a fixed-text `reason` such as "state file missing (Copilot Usage Monitor not running)". The probe always exits 0. A repeated call within the cache lifetime (300 seconds, or 60 seconds once a window reaches 90%) returns `"cached": true`.

To see the directive itself, start a session with a low threshold, for example `NEXUS_HANDOFF_THRESHOLD=1`. The directive starts with `Usage limit:` and names the session-handoff procedure.

## Configuration

Set these in the environment the agent host starts hooks from:

| Variable | Effect | Default |
|---|---|---|
| `NEXUS_HANDOFF_THRESHOLD` | Percentage (integer 1-100) at which the guard directs a handoff. Any other value means the default. | `99` |
| `NEXUS_USAGE_PROBE_PROVIDERS` | Comma-separated subset of `claude,codex,cursor,copilot` the probe may read. | all four |
| `NEXUS_USAGE_PROBE_DISABLED` | `1` turns the probe off, so the guard always stays silent. | unset |
| `NEXUS_HOME` | Relocates `~/.nexus-hub`, where the cache and guard state live. | `~/.nexus-hub` |

The guard warns once per window per session. It warns again only after the window drops below the threshold minus up to 5 points or its reset time moves to a new period.

## macOS: the one-time Keychain prompt (Claude Code)

On macOS, Claude Code may keep its sign-in in the login Keychain (item `Claude Code-credentials`) rather than in `~/.claude/.credentials.json`. The probe reads it with `security find-generic-password` under a 2-second limit and never waits on a dialog. The first time, macOS may show a dialog asking whether `security` may use that item. Choose **Always Allow** once. If you choose Deny or ignore the dialog, the Claude Code probe reports `unavailable` and the guard stays silent; the checkpoint and `/handoff` still work.

## Disable and rollback

| To | Do |
|---|---|
| Turn off the guard only | `NEXUS_DISABLED_HOOKS=usage-guard` |
| Turn off the probe (guard goes silent everywhere) | `NEXUS_USAGE_PROBE_DISABLED=1` |
| Run only the minimal hook set | `NEXUS_HOOK_PROFILE=minimal` |
| Stop reading one platform's usage | set `NEXUS_USAGE_PROBE_PROVIDERS` to the others |
| Remove cached readings and guard state | delete `~/.nexus-hub/state/usage-probe/` (except `copilot.json`, which the monitor owns) and `~/.nexus-hub/state/usage-guard/` |

`NEXUS_DISABLED_HOOKS` takes a comma-separated list, so add `usage-guard` to any value you already set. Disabling the guard does not remove the checkpoint rule or `/handoff`.

## Interaction with `/implement` runs

During a full `/implement` run, the completion gate also answers turn end and would normally refuse a stop while plan work remains. It yields to a usage-limit handoff only when both hold: `.nexus-hub/handoff.md` has a `usage-limit` header written after the gate's last refusal, and the probe confirms a tracked window at or over `NEXUS_HANDOFF_THRESHOLD`. The gate then lets the turn end without counting a refusal or recording a blocker, and prints one line saying the run stopped for a usage-limit handoff. The run resumes through `/implement <plan>` when you paste the prompt.

Writing a handoff file alone never releases a run, and a workspace-scoped install, whose hooks live inside the repository, never takes this exception. The rule is owned by the "Usage-limit handoff" section of `catalog/skills/workflow/implement-phase/references/completion-contract.md`.

## What is read, and where data goes

- **Claude Code**: the OAuth token in `~/.claude/.credentials.json`, or on macOS the Keychain item above. Sent only to `api.anthropic.com`.
- **Codex**: the token in `$CODEX_HOME/auth.json` or `~/.codex/auth.json`. Sent only to `chatgpt.com`. The endpoint is undocumented and can change without notice.
- **Cursor**: one allowlisted key, `cursorAuth/accessToken`, from the local `state.vscdb`, opened read-only. Sent only to `api2.cursor.sh`. The endpoint is undocumented and can change without notice.
- **GitHub Copilot**: no credential. The probe reads the monitor's `copilot.json` file and makes no network call.

The probe reads only the sign-in of the platform you are already using and calls only that platform's own vendor host over HTTPS, refusing redirects so a token cannot follow one elsewhere. It never refreshes a token, so it never writes to a vendor's credential store. Its cache under `~/.nexus-hub/state/usage-probe/` holds percentages and reset times only. The guard's per-session state under `~/.nexus-hub/state/usage-guard/` holds window names, times, and flags: no credential, no usage response, no prompt text. The guard itself makes no network call, and the handoff is written to your project and printed to you, never sent anywhere.

## Related

- `catalog/skills/workflow/session-handoff/SKILL.md`: the handoff procedure and file format.
- `catalog/commands/handoff.md`: the `/handoff` command.
- `catalog/hooks/usage-guard.py` and `catalog/hooks/_usage_probe.py`: the guard and the probe.
- [`docs/decisions/proposed/tooling/2026-09-28-usage-limit-handoff.md`](../decisions/proposed/tooling/2026-09-28-usage-limit-handoff.md): why the design reads credentials from a hook, and what it beat.
