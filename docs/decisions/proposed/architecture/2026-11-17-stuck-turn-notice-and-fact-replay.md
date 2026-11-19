# Decision: Keep a per-user hashed turn ledger for an advisory stuck-turn notice and opt-in environment-fact replay

Status: proposed - a stdlib helper keeps a hashed per-user ledger of tool outcomes under `~/.nexus-hub/state/<project hash>/`, adds one advisory notice per stuck turn, and optionally replays allowlisted confirmed workarounds, shipped opt-in until a measurement on real transcripts decides the default

## Problem

An agent stuck retrying a failing command or rewriting one file burns tokens and time with no signal from the harness, and environment workarounds the agent finds (for example that bare `pytest` is not found and `python -m pytest` works) are relearned every session. Both gaps are local: no model call, network call, or settings write is needed to close them. The risk is in what a hook would store and what it would inject back into context, because the stored text is command text from a repository the user may not control.

## Proposal

Add one helper, `catalog/hooks/_turn_ledger.py` (stdlib only), behind thin wrappers `stuck-turn-notice.{sh,ps1}` and the existing `session-start.{sh,ps1}`.

1. **Hook registration.** Register the wrapper on `PostToolUse` with matcher `Bash|Edit|Write|MultiEdit` and on `PostToolUseFailure` with matcher `Bash` in `catalog/hooks/settings.json`. `PostToolUseFailure` is a new event for this repository: it fires after a tool call that started executing fails, so a failing Bash command arrives there and not on `PostToolUse`. The matchers are frozen after release because both installer merges key a hook by matcher plus script stem. Platforms without an equivalent event drop it with a stated reason (observed for Codex, Copilot, Gemini CLI, and Qwen); the per-platform reach is in `docs/policy/platform-read-contracts.md`.
2. **Per-user state layout.** State lives in `~/.nexus-hub/state/<first 16 hex of SHA-256 of the resolved project root>/` (mode 0700 on POSIX), never in the project tree, so a cloned repository cannot supply, forge, symlink, or publish it. `turn-ledger.jsonl` holds one line per outcome with HMAC-SHA256 keys for command and file text (key in `~/.nexus-hub/state/ledger.key`, mode 0600); no command or file text is stored there. `env-facts.json` exists only with `NEXUS_ENV_FACTS=on` and holds plain text only for facts that passed the allowlist grammar and the secret scan. Every write first checks with `lstat` that neither the directory nor the file is a symlink or reparse point.
3. **Detection.** One notice per turn when the same command fails 3 times, 6 tool calls fail, or one file is changed 4 times. The notice is three sentences from a fixed template, built with a JSON serializer, and echoes a command or file name only when it is short, ASCII, matches an allowlist pattern, and carries no credential-shaped word.
4. **Fact replay.** At most 5 facts, each a failed not-found command followed by an exact `python -m <same command>` success in the same turn, with no edit between, confirmed in 3 sessions on at least 2 calendar days, retired by a later success of the failing command, and printed as JSON-escaped data under a heading that says it is not instructions.
5. **Default.** Shipped opt-in: the wrappers do nothing unless `NEXUS_STUCK_NOTICE=on` or `NEXUS_ENV_FACTS=on`. The plan makes the default depend on firing counts measured on real local transcripts with the maintainer's consent; that measurement has not been run, so the conservative default stands until it is.
6. **Purge.** Delete `~/.nexus-hub/state/<project hash>/` for one project, or `~/.nexus-hub/state/` for all (a new key is created on next use). Stop collection with `NEXUS_DISABLED_HOOKS=stuck-turn-notice`.
7. **Worst-case concurrency.** A record is one append of one complete line, a partial last line is ignored on read, and the ledger is rotated by moving the file at session start only. Parallel tool calls can therefore cause a duplicate notice (lost `notified` marker) or a missed signal (lost outcome); neither is data loss of anything that matters. Fact-store updates write a temp file and rename it, last writer wins, so a lost update delays a confirmation by one session.

## Alternatives considered

**Keep the ledger in the project tree (`.nexus/`).** Declined: a cloned repository could ship a forged ledger or fact file, plant a symlink that redirects the write, or have the ledger published by `git add -A`.

**Reuse `.nexus/observations.jsonl` from `learning-capture.sh`.** Impossible: that file records only the event, tool name, timestamp, and a prompt sample, so it holds no outcome or command key.

**Build the unused-tool report in this plan.** Deferred to v4.16.4: Claude Code's tool search already defers unused MCP tool schemas, and the MCP config lists servers, not tools.

**Let the model judge stuck turns or propose skills from them.** Declined: a deterministic advisory needs no model call, and a model-proposed skill is a larger and harder-to-audit surface.

**Write `permissions.deny` automatically after a repeated failure.** Declined: a hook that edits permissions changes security posture without the user asking.

**Replay facts through `npx`, `uv run`, or `poetry run`.** Declined: those forms can fetch packages or run repository-defined code, so replaying them as advice widens what an untrusted repository can steer.

**Ship default-on now.** Declined until the transcript measurement supports it; an opt-in advisory costs nothing to users who never enable it.

## Acceptance criteria

- The notice fires once on every seeded stuck fixture and on no healthy fixture, for every platform fixture set (`catalog/hooks/tests/test_stuck_turn_notice.py`).
- No command or file text appears in the ledger, no file appears in the project tree, a symlinked state location is never written through, no socket opens, and no settings file changes.
- A replayed fact is at most 120 characters, ASCII, contains no absolute or parent-relative path, and never contains error text; every rejected token class and secret shape stays out of the store and the output (`catalog/hooks/tests/test_env_fact_replay.py`).
- With `NEXUS_ENV_FACTS` unset, `session-start` output is byte-identical to the script without the replay block.
- The default decision is recorded with measured firing rates and a stuck-versus-false-alarm split before the notice becomes default-on.

## Risks

- **Latency.** The Windows PowerShell wrapper measured above the 500 ms budget on a loaded host; opt-in limits the cost to users who enable it.
- **Unverified payload.** The Claude Code row rests on the official hooks page, not a captured payload; the exit-code text is read defensively.
- **Kimi matcher.** The derived Kimi matcher names `Bash|Edit|Write` while Kimi documents `Shell`, `WriteFile`, and `StrReplaceFile`; this predates the change.
- **Hash stability.** The per-project hash uses the resolved path, so moving or renaming a project starts a fresh ledger and loses confirmed facts.
- **Assumed fields.** Edit file-path field names for Gemini, Qwen, and Kimi are assumed, not documented; the helper records nothing when they are absent.
