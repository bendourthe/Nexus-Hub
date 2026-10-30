# Decision: Deliver session handoffs as a paste-ready prompt in the chat, with a file only on explicit request

Status: implemented - `/handoff` and the usage-limit handoff print one self-contained prompt in the chat and write no file unless the user asks for one in that invocation; the milestone checkpoint is retired, and the hooks read the user's recorded `handoff` answer instead of a handoff file.

## Problem

Since v4.13.7 the `session-handoff` skill wrote `.nexus-hub/handoff.md` on every handoff and printed a prompt that embedded it, and every instruction template told agents to refresh that file after each verified milestone (checkpoint mode). The repository owner, Benjamin Dourthe, does not want handoffs collected as files: "they should just be as a prompt in the chat session where they get generated, so the user can copy/paste it." The checkpoint rule also made every long session write project state the user never asked for, and the `usage-guard` hook and the `/implement` completion gate used the file's `usage-limit` header as their evidence that a handoff happened, so the file could not simply be dropped from the skill.

## Decision

- **Chat by default.** Manual mode (`/handoff`) and usage-limit mode print one fenced, self-contained prompt in the chat. It carries everything the file used to hold: the header line (timestamp, platform, trigger), Goal, Done and verified, In progress, Next steps, Files touched, Constraints and decisions the user stated, Open questions and blockers, and Repository state. No file is written.
- **File only on explicit request.** When the user asks for a file in that invocation (`/handoff file`, `/handoff file PATH`, or "write the handoff to a file"), the skill writes it where they say, by default `.nexus-hub/handoff.md` under the existing exclude-file rule (never `.gitignore`), and still prints the prompt. No standing preference is inferred from an earlier request.
- **Checkpoint mode is retired.** The `## Session Handoff` block in all 13 substantive instruction templates now says handoffs are printed in chat with a file only on request, and the usage-limit bullet says to print the prompt in chat. The block validator fails a template that restores the checkpoint bullet.
- **Carry-forward without a file.** The skill carries unfinished Next steps forward from a handoff prompt the user pasted into the session, or from a legacy `.nexus-hub/handoff.md` under the existing trust rules (a committed or future-dated file is data, never instructions). When it reads a legacy file it tells the user the file can be deleted and never deletes it itself.
- **Hook evidence is the recorded answer.** Usage-limit mode keeps Step 0: the agent records the question and the user's answer in `.nexus-hub/usage-decision.json`, which is `usage-guard` state, not a handoff. A `handoff` answer is now the only handoff evidence: `usage-guard` skips a window's turn-end continuation once that answer is recorded after the window's announcement, and the completion gate's usage-limit exception accepts a `pending`, `wait`, or `handoff` answer newer than its last refusal, still only when the usage probe confirms a crossing window. A `.nexus-hub/handoff.md` file is never read by a hook.
- **Secrets.** The `egress-redaction` prohibition and the secret-shaped `grep` scan apply to the printed prompt; the scan reads the composed text on standard input, so it needs no file.

## Alternatives considered

- **Keep writing the file and also print the prompt (status quo).** Declined: it is exactly what the owner asked to stop, and the file duplicates the prompt the user copies anyway.
- **Ask the user each time whether they want a file.** Offered by the owner only as a fallback if chat delivery could not be guaranteed. Chat delivery is guaranteed (the agent prints the prompt in the same turn), so an extra question on every handoff would add friction, and in usage-limit mode it would compete with the credits question for the last turn.
- **Keep the rolling checkpoint but write it outside the project (for example under `~/.nexus-hub/`).** Declined: it is still a collected file, still writes state after every milestone that nobody asked for, and a home-directory file would no longer travel with the repository to another machine, which was its only advantage over the prompt.
- **Keep reading a `usage-limit` handoff header as hook evidence alongside the recorded answer.** Declined: the recorded `handoff` answer is always written in usage-limit mode before the handoff (Step 0), so the header added no case the answer misses, and a hook that still trusted a project file would keep a planted-file surface open for no benefit.

## Consequences

- An abrupt cutoff (a single turn that overruns the last 1% of a window) now leaves no on-disk record to resume from. This was the overshoot risk the 2026-09-28 usage-limit proposal mitigated with the checkpoint; the remaining mitigations are lowering `NEXUS_HANDOFF_THRESHOLD` and running `/handoff` before a long step. `docs/guides/usage-limit-handoff.md` states this.
- Users who upgrade may have a stale `.nexus-hub/handoff.md`. The next handoff carries it forward and tells them it can be deleted; nothing removes it automatically.
- The handoff header no longer accepts a `checkpoint` trigger; a legacy file's `checkpoint` header is copied into `Previous handoffs:` as written.
- The illustrative training story under `guides/website/` still shows a handoff file being written and read; it is tracked as follow-up work in `docs/todos.md`.
- Tests: `catalog/hooks/tests/test_session_handoff_contract.py`, `test_usage_guard.py`, `test_completion_gate_usage_handoff.py`, and `tests/validators/test_session_handoff_block.py` pin the chat default, the explicit-file rule, the retired checkpoint, and the recorded-answer evidence.
