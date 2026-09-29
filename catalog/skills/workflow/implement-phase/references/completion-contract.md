# Completion Contract

The single definition of "done" for a full `/implement` run: the predicates a plan must satisfy, the evidence each reads, what happens when evidence cannot be read, the four verdicts, and the run record that binds a run to the approvals the user gave at its start. `scripts/check_plan_completion.py` implements this file. The installer copies it to `~/.nexus-hub/scripts/check_plan_completion.py`, so in any project every `check_plan_completion.py <subcommand>` named here, in the runbook, or in the commands runs as `python ~/.nexus-hub/scripts/check_plan_completion.py <subcommand>`; a missing installed copy is `BLOCKED: platform-unavailable`, never a reason to skip the run record; the completion gate, the runner, and `/update release` consume the checker's verdict and never re-derive it. Read this before changing the checker, a gate adapter, the runner, or any approval point in the implement or release flow.

This file is the only owner of the predicate list. Commands and skills refer to "the completion contract" and to predicate ids; they do not restate a predicate's rule.

## Verdicts

The checker prints exactly one verdict line first, then one line per predicate id, and exits with the verdict's code.

| Verdict line | Exit | Meaning |
|---|---|---|
| `PLAN COMPLETE <plan> <head> <nonce>` | 0 | Every predicate is met. `<head>` is `git rev-parse HEAD`; `<nonce>` is the run record's nonce, or `-` when no record exists. When deferred gaps were accepted, the line ends with ` (N deferred)`. |
| `INCOMPLETE: <id> <id> ...` | 1 | At least one predicate is unmet or cannot be verified. Ids only, space-separated, in contract order. |
| `BLOCKED: <category>` | 3 | The run record holds an open blocker, or the record failed an integrity check. `<category>` is one value from the closed list below. |
| `PAUSED` | 4 | The user paused the run with `/implement pause`. |
| (error message) | 2 | Malformed input: a plan path outside `docs/**/plans/`, a plan with no `T###` lines, an unreadable plan. Never reported as complete. |

Every line after the verdict has the form `<id> met|unmet|cannot-verify|deferred|n/a`. The checker never prints free text taken from the plan, the gaps file, `git`, or `gh` output, so a gate or runner can pass the output to a model without relaying injected text.

Precedence when several states hold: a record that fails integrity (`record-tampered`) first, then `PAUSED`, then any other open blocker, then the predicates.

## Predicates

Ids are fixed strings. "Cannot verify" always counts as unmet: offline, unauthenticated, or slow evidence produces `INCOMPLETE`, never a pass.

| Id | Met when | Evidence source | Cannot verify when |
|---|---|---|---|
| `task.T###` (one per task line) | The line is checked (`- [x] T###`) and, when a run record exists, at least one commit since the record's `start_head` touches the path named at the end of the line | The plan file; `git log <start_head>..HEAD -- <path>` | The named path is absent from the line (reported `unmet`) |
| `gaps.version` | Every open item in `<version_dir>/known-gaps.md` under this plan's `## v<version>` subsection is resolved, or carries a gap type (`NI`, `DF`, `BG`, `MT`, `WN`, `QG`) the user named for deferral in the upfront round; an item added during the run whose Source phase names one of this plan's own tasks is never deferrable | The gaps file; the record's `deferrable_gap_types` and `start_head` | The gaps file is unreadable |
| `evidence.file` | `<version_dir>/development/<version>-last-phase-evidence.md` exists with every required section heading (see "Required evidence sections"). The legacy `last-phase-evidence.md` counts only when it names this plan's filename | The evidence file | Never (a missing file is `unmet`) |
| `tests.evidence` | The evidence file's `## Full-suite testing and stabilization` section quotes a passing command and names at least one test path this run changed | The evidence file; `git diff --name-only <start_head>..HEAD` | No run record, so the changed set cannot be computed (`cannot-verify`) |
| `approval.remote` | The live `git remote get-url --push --all origin` returns exactly one URL matching the push URL frozen in the signed approvals, and that URL names the approved GitHub `owner/repo` on a verified host | The run record; `git remote get-url --push --all origin`; `ssh -G <alias>` for an SSH host alias | No run record; a missing, unrecognized, changed, or additional push URL, or one whose host is not verified, is `unmet` |
| `integration.merged` | The plan branch's pull request into the integration branch is merged | `gh pr view <branch> --repo <owner/repo> --json state,mergeCommit` | `gh` missing, unauthenticated, offline, or over budget |
| `integration.checks` | Every required check on that pull request concluded success. Required-ness comes from `docs/policy/required-checks.json` when present, else `gh pr checks --required`, else it cannot be verified | The manifest; `gh pr checks` | As above, or no source of required-ness |
| `release.tag` | Tag `v<version>` exists locally and on the remote | `git tag -l`; `git ls-remote --tags <remote>` | Remote unreachable |
| `release.changelog` | `CHANGELOG.md` has a `## [<version>]` heading | The file | Never |
| `release.version-sync` | The project's declared version-sync command passes (Nexus-Hub: `python scripts/check_version_sync.py`); `n/a` when the project declares none | The command's exit code | The command times out |
| `release.github` | A GitHub Release for the tag is published (not a draft) | `gh release view v<version> --repo <owner/repo> --json isDraft` | As for `integration.merged` |
| `release.main` | The release branch (`main`) contains the tag | `git merge-base --is-ancestor v<version> <remote>/main` | Remote ref absent |
| `cleanup.branches` | Every branch listed in the record's `cleanup.branches` is gone locally and on the remote | `git branch --list`; `git ls-remote --heads` | Remote unreachable |
| `cleanup.worktree` | Every worktree listed in the record's `cleanup.worktrees` is absent from `git worktree list` | `git worktree list --porcelain` | Never |

Post-integration predicates (`release.*`, `cleanup.*`) are derived from repository and hosting state, never from checkboxes, because the tasks that produce them are ticked by the same agent the checker is judging.

Every hosting call is pinned with `--repo <owner/repo>` from the record's frozen approvals, runs with `GH_PROMPT_DISABLED=1` and `GIT_TERMINAL_PROMPT=0`, resolves `git` and `gh` to absolute paths outside the working tree, and shares one 20-second wall-clock budget for the whole check. `owner/repo` is resolved by the installed `repo_host.py`: the record's frozen repository when one exists, otherwise the `origin` URL (`https://`, `ssh://`, or `git@host:owner/repo`), accepted only when its host is the one `gh --repo` queries (`GH_HOST` when set, otherwise `github.com`). An SSH host alias is replaced by the `hostname` that `ssh -G <alias>` reports and is refused when routed through a proxy, and without a record the answer is cross-checked with `gh repo view`; an unverified host or a disagreement yields no repository, so every hosting predicate is `cannot-verify`, never a lookup of a same-named github.com repository. `record create` refuses a push URL that does not name that approved repository; a later push-URL change makes `approval.remote` unmet and permits an `approval-not-covered` blocker even when `push-merge` was approved. Local predicates run first so an offline check still reports them.

A hosting answer that the pull request or release does not exist (`gh`'s whole stderr line is `no pull requests found for branch "<branch>"` or `release not found`) is `unmet`, not `cannot-verify`: GitHub was reached and the run's next step is to create it. Only an unreachable, unauthenticated, or over-budget call is `cannot-verify`. The agent probes hosting the same way, always with `--repo <owner/repo>` from the record; an un-pinned `gh` call that fails is not evidence that the platform is unavailable, and never justifies merging, tagging, or releasing through `git` alone.

### Required evidence sections

The evidence file must carry these `##` headings, matching the implement-phase runbook's last-phase list: `Architecture refactor`, `Known-gaps reconciliation`, `Living docs architecture`, `Git-tree hygiene`, `CI/CD coverage`, `Tier 3 deep pass`, `Goal-vs-codebase review`, `Human/manual testing suggestions`, `Full-suite testing and stabilization`, `Publication and integration`.

### Definition-of-Done mapping

| Plan DoD item (v4.13.2) | Predicates |
|---|---|
| Every task, phase, and known gap | `task.T###`, `gaps.version` |
| Green CI with the tests the work needs | `tests.evidence`, `integration.checks` |
| The merged integration | `approval.remote`, `integration.merged` |
| The full release | `release.tag`, `release.changelog`, `release.version-sync`, `release.github`, `release.main` |
| Removal of merged branches and worktrees | `cleanup.branches`, `cleanup.worktree` |
| Last-phase duties recorded | `evidence.file` |

## Run record

### Location and binding

One file per run at `~/.nexus-hub/runs/<key>.json`, where `<key>` is the sha256 of the repository root, the remote URL, and the plan path, joined by newlines. The directory is created owner-only (0700; owner-only ACL on Windows) and the file 0600. The record lives outside every working tree so no commit, branch switch, or `git clean` can create, alter, or delete it. The location decision and its alternatives: `docs/decisions/implemented/tooling/2026-09-25-completion-run-record-outside-the-working-tree.md`.

Fields: `schema` (currently `1`), `plan` (repository-relative path), `plan_sha256` (at approval time), `repo_root`, `remote_url`, `repo` (`owner/repo`), `session_id`, `worktree`, `start_head`, `nonce` (the approval round's 128-bit nonce, 32 hex characters; see Approval origin), `created`, `approvals`, `approvals_hmac`, `deferrable_gap_types`, `cleanup` (`branches`, `worktrees`), `blockers`, `pause`.

### Approvals as exact actions

Each approval is a tuple of exact values plus the verbatim user text that granted it: the plan path; the fetch remote URL, push remote URL, and `owner/repo`; source and target branch; release version and tag name; the branches and worktrees to remove; and each approval class with its bound. The classes are: `push-merge`, `release` (version, tag, publication, release pull requests, and back-merge for that one version), `repush` (after a locally reproduced fix, bound 3), `release-notes`, `refactor-moves` (inside plan-touched folders only), `spend` (a USD cap per vendor), and one `ask-first:<surface>` per "Ask first" surface the plan names. CI workflow, permission, and secret changes are never approvable in advance; they are always a `ci-security-change` blocker.

An older signed record without `push_remote_url` yields `approval.remote unmet`; creating a fresh record from a current user approval is required before publication. A changed destination cannot be authorized by editing the old record.

`approvals_hmac` is an HMAC-SHA256 over the canonical JSON of `approvals`, `plan_sha256`, `session_id`, `repo`, `deferrable_gap_types`, `start_head`, `nonce`, and `created`, keyed by the owner-only secret `~/.nexus-hub/runs/.secret`, which `record render` or `record create` creates when it is absent. `pause` and `blockers` are not yet signed (v4.13.2 known gap WN-8). No prompt text, command, or skill references the secret's content.

### Approval origin

This section is the single owner of the exact-binding rule; other documents link here and do not restate it. An approval is recorded only when the user's submitted prompt equals, as a whole, the exact paste line the checker generated for that page, once. This holds for every user-origin record write: `record create`, `record answer`, `record pause`, and `record resume`. `record block` records the agent's own stop and needs no user origin.

1. **Render.** `record render <plan> --session <id|auto>` (with `--approvals <file>` for `create`, or `--action answer --blocker <n>`, `--action pause`, `--action resume`) builds the canonical JSON of exactly what the page shows: for `create`, the scope, each member with its `plan_sha256`, the verified `owner/repo`, the current `HEAD`, the source and target branches, the releases and tags, the cleanup rule and today's estimate, the migratable gap ids, the spend caps, and the approval classes with their bounds; for a mid-run action, the scope, the record's `nonce`, and (for an answer) the blocker's index and category. It draws a fresh 128-bit round nonce and derives `code` = the first 8 base32 characters of `HMAC-SHA256(runs secret, canonical {page, nonce})`. Only the checker generates codes; the agent never does. It writes an owner-only pending round at `~/.nexus-hub/runs/pending/<key>.json` (same `<key>` as the record, same permission helper) holding the page, code, nonce, the render time, a 30-minute expiry, the bound session, and the exact paste line(s) with their digests, sealed by an HMAC under the runs secret over every one of those fields, and prints the line(s). A round whose seal does not verify (for example one whose digests, expiry, or session were edited) is refused as `pending-unreadable`. The line is built only from validated fields (a version token, a blocker index, the code) and carries no path or script name. A newer render for the same record replaces the older round, whose code is then refused as `code-superseded`.
2. **Paste.** The user pastes the line as their whole prompt. On platforms with a documented prompt-submit hook (Claude Code `UserPromptSubmit` and the equivalents in `docs/policy/completion-levers.json`), the `approval-capture` hook stores, per session, the sha256 of the whole submitted prompt (normalized: trimmed, internal whitespace collapsed) in hook-owned state at `~/.nexus-hub/runs/prompts/<sha256(session id)>.jsonl`, one JSON line `{"session": ..., "prompt": <digest>, "at": <capture time>}` per prompt. No prompt plaintext and no per-line digest is stored, so a line inside a longer prompt, a quoted code, or a pasted body never matches. The hook skips capture in any session whose environment has `NEXUS_RUNNER_LAUNCH=1`, which `nexus-hub run-plan` sets for every session it launches.
3. **Record.** The write recomputes the page from live state and requires, in order: not a runner-launched environment; an open round of the same action whose seal verifies; not expired; the same code (any change to the page, such as a plan edit outside task checkboxes or a moved `HEAD`, fails here); the bound session, when the round names one, and for `record answer`, `record pause`, and `record resume` also the session the run record is bound to (`session-mismatch` otherwise); exactly one captured whole prompt in that session equal to each paste line; and at least one other prompt captured in that session before the round was rendered (`session-too-new` otherwise), since the user's own session already holds the `/implement` request while a headless session launched only to submit the line does not. It then deletes the pending round, leaves a used marker, and, for `create`, adopts the round nonce as the record's `nonce` and stores the pasted line as each class's verbatim text. With `--session auto`, the session is the newest one whose captured whole prompts include the line. The round lives for 30 minutes from render; the end of a session is not detected, so within that window a later session can record a line the user pasted in an earlier one, and the record is then bound to the session where the paste was captured.
4. **No capture.** Where no prompt-submit hook exists, or the named session has no capture file, the write refuses with `approval-not-captured`. There is no terminal fallback: a process that owns the console or a pseudo-terminal can type into `/dev/tty` or `CONIN$`, so a terminal read would not show that the user typed the line. On such a platform the run records no approval and asks at each approval point, as a one-phase run does.

A refusal prints `BLOCKED: approval-not-covered` on the first line, so existing consumers parse it unchanged, and `reason: <id>` on the second, where `<id>` is one of: `runner-launched`, `not-rendered` (no open round for this action), `pending-unreadable`, `code-used` (the round was already consumed), `code-superseded`, `code-expired`, `session-mismatch`, `session-too-new`, `page-changed`, `approval-not-captured`, or `push-remote-outside-approval`. A refused write does not consume the round, except that a claimed `--text` different from the pasted line spends it.

### Integrity

The checker rejects a record, reporting `BLOCKED: record-tampered`, when any of these hold: the record path is inside a git working tree or tracked by git; `plan_sha256` differs from the plan file's current hash for any change outside task checkboxes; `approvals_hmac` does not verify; the record's `schema` is unknown. Task checkbox ticks are excluded from the plan hash so the run can progress.

**Threat model (honest boundary).** These controls stop an agent from widening its authority through ordinary actions: editing the record or a pending round, rewriting the plan, or treating a reply that is not the generated line (a lone "ok", a quoted code, a pasted body, a replayed or superseded line, a runner-launched prompt, a fresh headless session opened only to submit the line) as an approval. They do not stop an agent that deliberately forges a user origin. A prompt submitted by a headless CLI the agent launched, a payload the agent pipes into `completion_gate.py capture`, or a line appended to the capture file is indistinguishable from the user's paste, and none of them is a user origin; this residual is open as v4.13.2 WN-9 in `docs/releases/v4/v4.13/known-gaps.md`. They are not a sandbox. A process with the user's file access can read the secret and recompute the HMAC, and the prompt digests sit in the same home directory. The design therefore relies on three things together: the approval-origin rule (an approval must match text the user submitted), the fixed-id output that keeps injected text out of the loop, and the named-blocker rule that makes widening an approval a visible stop rather than a silent success.

### Blockers

A blocker is an entry in the record's `blockers` list with exactly one category from this closed list, the evidence (the command run and its output, truncated to 2000 characters), and `open: true`:

`approval-not-covered`, `unreproducible-red-check`, `user-edit-guard`, `destructive-outside-approval`, `ci-security-change`, `no-progress`, `record-tampered`, `platform-unavailable`.

A blocker whose question the frozen approvals already answer is rejected at write time. `no-progress` is written by the gate or the runner when the progress score has not increased over three consecutive refusals or cycles.

### Pause and resume

`/implement pause` writes a user-origin `pause` entry (subject to the approval-origin rule, so the user pastes the rendered pause line) and is always honored; the checker then reports `PAUSED`. `/implement <plan>` resumes: the upfront round shows any open blocker and the pause, records the user's pasted answer or resume line as an approval, and clears them.

### Hook-owned state

The refusal counter and the last progress score live beside the record at `~/.nexus-hub/runs/<key>.gate.json`, never inside it, so writing them never invalidates the HMAC.

### Stale records

A record whose session is gone and whose `created` is older than 72 hours is stale: the checker reports it once on stderr and treats it as absent for any other session.

## Progress score

`check_plan_completion.py score <plan>` prints `<met-count> <head> <latest-ci-run-id-or-dash>`. The gate and runner compare scores lexicographically on the met count first; a larger count or a new `HEAD` is progress.
