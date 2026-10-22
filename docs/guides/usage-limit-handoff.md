# Usage-Limit Handoff

Summary: how Nexus-Hub keeps your work resumable when an AI platform's usage limit runs out, through `/handoff` (a paste-ready prompt printed in the chat, with a file only when you ask for one) and the automatic `usage-guard` hook.
Read this when: you want to know what happens near a usage limit on your platform, how to turn the automatic guard on or off, how to check it, or what it reads and sends.
Covers: per-platform coverage, the 99% threshold and its known limitation, `/handoff` and the prompt format, the optional handoff file, activation, validation, configuration, isolating a test run of the probe, the macOS Keychain prompt, disabling, the completion-gate interaction, and the data boundary.

## What it does

A usage cap is enforced by the vendor's server. Once you hit it, the next model request is rejected and the agent gets no further turn, so nothing inside the agent can react at 100%. Nexus-Hub acts before that point, in three layers:

1. **`/handoff` (every platform).** The `session-handoff` skill prints one paste-ready prompt in the chat that another agent, on any platform, can resume from. It writes no file unless you ask for one in that request. Every installed instruction file carries a short Session Handoff rule, so the agent knows handoffs belong in the chat, and you can run `/handoff` at any time.
2. **Automatic guard (Claude Code, Codex, Cursor, GitHub Copilot).** The `usage-guard` hook reads the platform's own usage figure. When a tracked window reaches the threshold (99% by default), it tells the agent to finish the current step and ask you first: continue on pay-per-use credits, or hand off. If the agent ends its turn without asking, the guard sends one continuation asking for it. See "Continuing on pay-per-use credits" below.
3. **Manual fallback (every other platform).** Where no usage figure can be read, the guard stays silent. Run `/handoff` yourself, or the agent runs it when the platform itself warns about limits.

The handoff is printed in the chat, for you to copy. Nothing switches platforms for you and nothing sends the handoff anywhere.

## Coverage by platform

Verified against first-party hook documentation on 2026-10-01 (sources in the "Usage-limit handoff hook behaviors" section of [`docs/policy/platform-read-contracts.md`](../policy/platform-read-contracts.md)).

| Platform | Directive reaches the agent through | Turn-end continuation | Usage source | Result |
|---|---|---|---|---|
| Claude Code | `UserPromptSubmit` and `PostToolUse` `additionalContext` | `Stop` `decision: block` | Anthropic OAuth usage endpoint | Automatic |
| Codex | `UserPromptSubmit` and `PostToolUse` `additionalContext` | `Stop` `decision: block` | `chatgpt.com/backend-api/wham/usage` (undocumented) | Automatic after you trust the hook once; fragile |
| Cursor | native `postToolUse` `additional_context` | native `stop` `followup_message` | Cursor usage RPC with the local `state.vscdb` token (undocumented) | Automatic; fragile |
| GitHub Copilot (VS Code Local hooks) | `PostToolUse` `hookSpecificOutput.additionalContext` (VS Code's `UserPromptSubmit` has no context field) | `Stop` `decision: block` | the Copilot Usage Monitor's percentages-only file; the hook reads no credential | Automatic while the monitor writes a percentage; silent otherwise |
| Gemini CLI, Qwen Code, Kimi Code CLI | hooks are delivered and recognized | hooks are delivered | none known | `/handoff`; `usage-guard` stays silent |
| Windsurf, Antigravity | not registered (curated hook lists) | not registered | none known | `/handoff` |
| OpenCode, Aider, Pi, OpenClaw | no shell-hook surface | none | none | `/handoff` |

Tracked windows: Claude Code 5-hour and weekly (the highest of the weekly figures), Codex weekly only, Cursor monthly, Copilot monthly.

**Copilot depends on the Copilot Usage Monitor.** A hook process cannot reach VS Code's secret storage or its GitHub sign-in, so on Copilot the guard reads only `~/.nexus-hub/state/usage-probe/copilot.json`, which the monitor writes with percentages and reset times and nothing else. With the monitor not running, the file is missing or older than 30 minutes and the guard stays silent. A Business or Enterprise member without billing access gets no percentage from the monitor, so the guard stays silent for them too. Copilot CLI reads the same hooks directory, but its payload has not been captured, so it is not claimed as covered.

**Slash command reach.** `/handoff` is a slash command where the platform has a slash surface. On platforms without one, the same procedure reaches the agent through its instruction file: ask the agent to "write a handoff" or "run the session-handoff procedure".

## Why 99%, and the known limitation

The trigger is 99% of each tracked window because you chose to use as much of the window as possible before handing off. That leaves 1% of the window. On a 5-hour Claude Code window a single large turn can use more than that, so the automatic directive can arrive after the cap and never be read.

Handoffs are printed in the chat only when asked for, so no agent keeps a rolling record on disk, and an abrupt cutoff leaves nothing to paste. If you often work in large turns, lower the threshold (see Configuration) so the question arrives while a turn is still left, or run `/handoff` yourself before a long step.

## Using `/handoff`

Run `/handoff`, optionally with a focus:

```text
/handoff
/handoff focus on the failing migration
```

The agent prints one fenced prompt in the chat and writes no file. Copy that block and paste it into any agent on any platform; it tells the receiving agent to check the repository state against the handoff, continue from the first unfinished step, and respect the constraints you stated. The prompt carries the whole handoff, so it works on another machine or in a chat-only tool.

The handoff has a fixed format: a header line, then the same sections in the same order every time.

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

- The header is `# Handoff | TIMESTAMP | PLATFORM | TRIGGER`. `TRIGGER` is `manual` or `usage-limit WINDOW PERCENT`. The next handoff parses this line when it carries the steps forward.
- Each Done item carries the command that proved it, and each Next step carries the command that will.
- A new handoff carries forward every unfinished step from a handoff prompt you pasted into the session, whichever platform wrote it.
- The agent never puts secrets, tokens, or credential-file contents into the prompt, and scans it for secret-shaped strings before printing it.

**A file only when you ask.** Run `/handoff file` to also write the handoff to `.nexus-hub/handoff.md`, or `/handoff file PATH` (or say "write the handoff to a file") to choose the place. The prompt is still printed. The request covers that one handoff; the next one is chat only again. When the file goes under `.nexus-hub/`, that directory is added to the repository's `info/exclude` file, never to `.gitignore`, so it stays local and uncommitted.

**Older handoff files.** Earlier Nexus-Hub versions kept `.nexus-hub/handoff.md` up to date after each milestone. If one is still in your project, the next handoff reads it (unless it is committed or dated in the future), carries its unfinished steps into the new prompt, and tells you the file can be deleted. Nothing deletes it for you.

The full procedure is the `session-handoff` skill, `catalog/skills/workflow/session-handoff/SKILL.md`.

## Activation

The guard is on by default after a global install. The installer registers `usage-guard` on `UserPromptSubmit`, `PostToolUse`, and `Stop` for Claude Code, Codex, and Copilot, and on native `postToolUse` and `stop` for Cursor.

One platform needs a step from you:

- **Codex**: Codex skips an untrusted hook silently. Open Codex, run `/hooks`, review the `usage-guard` entries, and trust them once. Until then the guard does not run on Codex.

On Copilot, also install and sign in to the Copilot Usage Monitor, which supplies the percentage the guard reads.

## Validation

Run the probe the guard uses. It prints one JSON line with percentages and, where the platform reports them, pay-per-use credit amounts; never a credential or account detail. Pick the installed copy for your platform (in PowerShell, write `$HOME` instead of `~`):

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

To see the directive itself, start a session with a low threshold, for example `NEXUS_HANDOFF_THRESHOLD=1`. The directive starts with `Usage limit:` and asks the agent to put the credits-or-handoff question to you.

## Continuing on pay-per-use credits (v4.13.11)

Reaching a subscription limit is not treated as a decision to hand off, because your account may have pay-per-use credits (extra usage). At the threshold the agent finishes or safely stops the current step, records the open question in `.nexus-hub/usage-decision.json` as `pending`, and asks you once. Where the platform has an interactive question tool (in Claude Code, `AskUserQuestion`), the question appears as three clickable choices, none preselected: **Continue on credits**, **Wait for reset**, and **Hand off to another agent or platform**, each describing its cost, the reset time, or what the handoff does. On a platform without such a tool, the agent asks the same three choices once in one short message. While the question is open, a continuation from another hook or a goal does not ask it again; the agent says it is waiting and ends the turn. It records your answer in the same file:

- **Continue on credits**: the agent carries on with the task. The guard remembers the approval in `~/.nexus-hub/state/usage-guard/<platform>.credits.json` until the limited window resets, so new sessions in that period do not ask again.
- **Wait for the reset**: the agent stops and starts no new work.
- **Hand off**: the agent runs the session-handoff procedure: it prints the paste-ready prompt in the chat, writes no handoff file, and starts no new work.

What the agent tells you, and when it asks again, depends on the credit reading (the probe's `extra_credits` window):

| Credit state | At the limit | After you choose credits |
|---|---|---|
| Capped (a fixed allowance) | the amount spent, the limit, and the percent | asks again at 50%, 75%, and 90%; also every reminder step if `creditReminderWhenCapped` is on; once more if the allowance runs out |
| Uncapped (no spending limit) | the amount spent this period | asks again every reminder step of spend; no figure means no reminders, and the agent says so |
| None (credits disabled, or a zero allowance) | warns that continuing will fail until the reset unless you enable credits first; offers enabling them, waiting, or the handoff | no reminders; requests fail until credits are enabled |
| Exhausted (allowance used up) | warns that continuing will fail unless you raise the limit; offers raising it, waiting, or the handoff | announced once; again only after the allowance resets or is raised and runs out again |
| Unknown (no reading) | says it cannot tell whether continuing will work or remind you | no reminders |

Reminders arrive during a turn, never at turn end. The reminder step is set in the Claude, Codex, and Cursor usage monitor extensions (`claudeUsage.creditReminderStep`, `codexUsage.creditReminderStep`, `cursorUsage.creditReminderStep`, each with a `creditReminderWhenCapped` switch). Each extension saves its own file under `~/.nexus-hub/config/`: `credit-reminders-claude.json`, `credit-reminders-codex.json`, or `credit-reminders-cursor.json`. Separate files keep simultaneous editor hosts from overwriting another provider's settings. You can also edit the matching file by hand, for example `{"providers": {"claude": {"step": 100, "when_capped": true}}}`. The step is in the provider's own unit: US dollars for Claude Code and Cursor (default 50), Codex credits for Codex (default 500). A step of 0 turns spend reminders off. The existing shared `credit-reminders.json` remains a fallback when the provider file cannot be read or contains no entry for that provider.

Credit readings by platform: Claude Code from `extra_usage`, Codex from `credits` and `spend_control.individual_limit`, and Cursor from `spendLimitUsage` (your individual on-demand limit, else the team pool). Copilot's monitor writes no credit figure, so Copilot is always "unknown". Antigravity, Gemini CLI, Qwen Code, and Kimi Code CLI have no usage source, so the guard does not run there; the ask-first rule still reaches the agent through its instruction file when the platform itself warns about a limit.

The repository cannot approve spending for you: only the guard writes the persisted approval, and only from an answer recorded after its own question in the current session. To withdraw an approval early, delete the `.credits.json` file.

## Configuration

Set these in the environment the agent host starts hooks from:

| Variable | Effect | Default |
|---|---|---|
| `NEXUS_HANDOFF_THRESHOLD` | Percentage (integer 1-100) at which the guard directs a handoff. Any other value means the default. | `99` |
| `NEXUS_USAGE_PROBE_PROVIDERS` | Comma-separated subset of `claude,codex,cursor,copilot` the probe may read. | all four |
| `NEXUS_USAGE_PROBE_DISABLED` | `1` turns the probe off, so the guard always stays silent. | unset |
| `NEXUS_HOME` | Relocates `~/.nexus-hub`, where the cache and guard state live. | `~/.nexus-hub` |

The guard warns once per window per session. It warns again only after the window drops below the threshold minus up to 5 points or its reset time moves to a new period.

## Testing the probe in isolation

A probe run reads the real sign-in of every provider it is allowed to read and, on a cache miss, sends that token to the vendor's host. Redirecting `HOME` alone does not isolate it:

- On Windows, Python takes the home folder from `USERPROFILE` and ignores `HOME`, so `~/.claude/.credentials.json` and `~/.codex/auth.json` still resolve inside the real profile.
- Cursor's `state.vscdb` is found through `APPDATA` on Windows and through `XDG_CONFIG_HOME` (else `~/.config`) on Linux, so a run with only `HOME` and `USERPROFILE` redirected still reads the real Cursor token on Windows.
- Codex reads `CODEX_HOME` before the home folder.
- On macOS, Claude Code falls back to the login Keychain, which no environment variable redirects.

Use one of these two recipes. Never use the live account state on the machine in place of a fixture.

1. **Exclusion (no credential read, no network call).** Set `NEXUS_USAGE_PROBE_PROVIDERS=copilot` and point `NEXUS_HOME` at a temporary folder. Claude Code, Codex, and Cursor then report `unavailable` with the reason `provider disabled by NEXUS_USAGE_PROBE_PROVIDERS` before any file is opened, and Copilot reads only `copilot.json` under `NEXUS_HOME` with no network call. An empty `NEXUS_USAGE_PROBE_PROVIDERS` means all four providers, not none; to read nothing at all, set `NEXUS_USAGE_PROBE_DISABLED=1`.
2. **Redirection (exercise a provider against fixture files).** Point all six of `HOME`, `USERPROFILE`, `APPDATA`, `XDG_CONFIG_HOME`, `CODEX_HOME`, and `NEXUS_HOME` at folders under one temporary directory, then place the fixture credentials there. On macOS also leave `claude` out of `NEXUS_USAGE_PROBE_PROVIDERS`, because the Keychain fallback is not redirected. A fixture token is still sent to the vendor's host on a fetch.

The probe has no offline switch. A test that must exercise a fetch without any network call uses the unit tests in `catalog/hooks/tests/test_usage_probe.py`, which replace the probe's single network seam (`_open`). `test_the_documented_redirection_recipe_isolates_every_credential_path` in that file checks recipe 2 in a child process, and `test_the_documented_exclusion_recipe_reads_no_provider` checks recipe 1.

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

`NEXUS_DISABLED_HOOKS` takes a comma-separated list, so add `usage-guard` to any value you already set. Disabling the guard does not remove the Session Handoff rule or `/handoff`.

## Interaction with `/implement` runs

During a full `/implement` run, the completion gate also answers turn end and would normally refuse a stop while plan work remains. It yields to a usage-limit stop only when both hold: `.nexus-hub/usage-decision.json` records your answer to the usage question (`pending`, `wait`, or `handoff`) after the gate's last refusal, and the probe confirms a tracked window at or over `NEXUS_HANDOFF_THRESHOLD`. The handoff itself is printed in the chat, so the recorded `handoff` answer is its only evidence; a `.nexus-hub/handoff.md` file is never read. The gate then lets the turn end without counting a refusal or recording a blocker, and prints one line saying the run stopped for a usage-limit handoff. The run resumes through `/implement <plan>` when you paste the prompt.

A recorded answer alone never releases a run, and a workspace-scoped install, whose hooks live inside the repository, never takes this exception. The rule is owned by the "Usage-limit handoff" section of `catalog/skills/workflow/implement-phase/references/completion-contract.md`.

## What is read, and where data goes

- **Claude Code**: the OAuth token in `~/.claude/.credentials.json`, or on macOS the Keychain item above. Sent only to `api.anthropic.com`.
- **Codex**: the token in `$CODEX_HOME/auth.json` or `~/.codex/auth.json`. Sent only to `chatgpt.com`. The endpoint is undocumented and can change without notice.
- **Cursor**: one allowlisted key, `cursorAuth/accessToken`, from the local `state.vscdb`, opened read-only. Sent only to `api2.cursor.sh`. The endpoint is undocumented and can change without notice.
- **GitHub Copilot**: no credential. The probe reads the monitor's `copilot.json` file and makes no network call.

The probe reads only the sign-in of the platform you are already using and calls only that platform's own vendor host over HTTPS, refusing redirects so a token cannot follow one elsewhere. It never refreshes a token, so it never writes to a vendor's credential store. Its cache under `~/.nexus-hub/state/usage-probe/` holds normalized usage windows: percentages, reset times and source names, plus credit state, numeric spend/allowance and units where available. The guard's state under `~/.nexus-hub/state/usage-guard/` holds window names, times, flags and credit-approval reminder markers. These files contain no credential, raw usage response or prompt text. The guard itself makes no network call, and the handoff is written to your project and printed to you, never sent anywhere.

## Related

- `catalog/skills/workflow/session-handoff/SKILL.md`: the handoff procedure and prompt format.
- [`docs/decisions/implemented/tooling/2026-10-21-handoff-prompt-in-chat.md`](../decisions/implemented/tooling/2026-10-21-handoff-prompt-in-chat.md): why the handoff is a chat prompt and the checkpoint is retired.
- `catalog/commands/handoff.md`: the `/handoff` command.
- `catalog/hooks/usage-guard.py` and `catalog/hooks/_usage_probe.py`: the guard and the probe.
- [`docs/decisions/proposed/tooling/2026-09-28-usage-limit-handoff.md`](../decisions/proposed/tooling/2026-09-28-usage-limit-handoff.md): why the design reads credentials from a hook, and what it beat.
