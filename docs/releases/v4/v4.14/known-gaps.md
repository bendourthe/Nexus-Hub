# Known Gaps - v4.14

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-10-13
**Open items**: 83

## v4.14.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 14 | 0 |
| Bugs / regressions (BG) | 2 | 0 |
| Warnings (WN) | 25 | 0 |
| Missing tests / coverage gaps (MT) | 4 | 0 |
| Quality-gate gaps (QG) | 3 | 0 |

### Open Items

#### BG-1: The second pilot's per-call budget did not bound reported cost

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: medium - the approved USD 35 hard ceiling cannot be guaranteed when one call can exceed its USD 0.50 reservation
- **Blocker**: user-credential - BG-7-v4130 needs a Claude Console workspace API key with a provider-enforced spend cap; the host authenticates only as claude.ai Team (preflight 2026-09-24), so no bounded paid call is possible.
- **Acceptance**: A provider-enforced ceiling or proven per-call upper bound exists, pre-call reservation and crash-safe per-call receipts are fixed and tested, and a new protocol is frozen before any further paid call
- **Proving command**: manual: confirm the runner authenticates with a Claude Console workspace API key whose provider-enforced spend cap is recorded in a newly frozen trigger-pilot-2 protocol
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: 2026-09-23 post-release trigger follow-up. **Plan reference**: [`trigger-pilot-2/protocol.md`](../../../archives/v4/v4.13/development/trigger-pilot-2/protocol.md). **Reason**: the first two strong-tier calls reported USD 0.6540 and USD 0.6292, each above the runner's USD 0.50 per-call reservation, and both had unknown selector evidence. The process was interrupted; no complete result file exists. The aggregate check cannot guarantee the approved hard USD 35 ceiling when a call can exceed the amount reserved for it.

**Owner**: catalog maintainer. **Status**: open; the second pilot is `UNMEASURED`. **Suggested next step**: establish a provider-enforced ceiling or proven per-call upper bound, fix and test pre-call reservation and crash-safe per-call receipts, then freeze a new protocol before spending again. Preserve the [aborted attempt](../../../archives/v4/v4.13/development/trigger-pilot-2/attempt.md) and the original 96-call evidence unchanged.

**Local safety candidate, 2026-09-23**: The runner now rejects non-finite or negative reported cost, records an atomic in-flight receipt before each call and a completed receipt after it, refuses to overwrite an existing receipt, and stops before a second call when reported cost exceeds the per-call reservation. These controls preserve partial evidence and prevent further calls after an observed overrun; they do not retroactively bound the overrun or make USD 35 a hard ceiling. The pilot remains `UNMEASURED`, and no further paid call is authorized by this candidate alone.

**Provider-cap preflight, 2026-09-24**: The installed Claude Code 2.1.280 currently authenticates as `claude.ai` on a Team subscription, not as a Claude Console workspace API key. The [archived preflight](../../../archives/v4/v4.13/development/trigger-pilot-2/provider-cap-preflight-2026-09-24.md) distinguishes Team usage-credit limits from a dedicated Console workspace cap and records the account, key-binding, and limit-refusal evidence required before another paid call. BG-7 remains open and the second pilot remains `UNMEASURED`.

**Original source identity**: `v4.13.0#BG-7`; stable ID `BG-7-v4130` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#BG-7-v4130 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: BG-7-v4130 needs a Claude Console workspace API key with a provider-enforced spend cap; the host authenticates only as claude.ai Team (preflight 2026-09-24), so no bounded paid call is possible.

#### WN-1: The shipped catalog under-triggers on its own positive prompts

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: medium - the shipped catalog selected the skill on 1/8 (fast) and 3/8 (strong) positive prompts
- **Blocker**: user-credential - WN-3-v4130 requires a new paid frozen trigger pilot, which is blocked until BG-7 establishes a provider-enforced spend cap on a Console workspace key.
- **Acceptance**: A new frozen trigger pilot, with a candidate designed against the recorded data, decides whether the authoring guidance changes; no description changes on the strength of this finding alone
- **Proving command**: manual: a new frozen pilot's results file records positive-prompt selection for the candidate arm against the shipped control arm
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 6. **Plan reference**: T022, T023. **Reason**: the pilot's control arm is the currently shipped corpus. Across four sampled skills and eight positive prompts it selected the skill on **1/8** with the fast model and **3/8** with the strong model, while producing **zero** irrelevant selections across all 32 near-miss and trivial-edit prompts. The catalog's measured failure mode is under-triggering, not over-triggering.

**Evidence**: `development/trigger-pilot-results.md` and the raw `trigger-pilot-results.json` (96/96 calls, 0 failures, 0 evidence-missing). The regression is concentrated in `skill-description-authoring` on the strong model, 2/2 to 0/2 under the candidate wording.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: this finding is recorded, not acted on. `AGENTS.md` prescribes pushier descriptions with explicit SKIP clauses as the remedy, and the pilot measured that remedy making selection **worse** on both models, so the prescribed fix is now evidence-contradicted. Changing the authoring guidance needs its own frozen pilot with a candidate designed against this data; nothing in this release may change a description on the strength of the finding alone.

**Original source identity**: `v4.13.0#WN-3`; stable ID `WN-3-v4130` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-3-v4130 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: WN-3-v4130 requires a new paid frozen trigger pilot, which is blocked until BG-7 establishes a provider-enforced spend cap on a Console workspace key.

#### WN-2: The recorded pilot run cannot be re-audited for the loose selection matcher

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - the matcher defect can only inflate a positive, and the MEASURED_NO_CHANGE disposition does not turn on it
- **Blocker**: user-deferred - WN-5-v4130's 96 historical tool payloads were never retained and cannot be recovered; future runs retain selectors, so only maintainer acceptance can close the historical clause.
- **Acceptance**: The maintainer records acceptance that the 96 historical tool payloads are unrecoverable, with future runs retaining `skill_selectors`
- **Proving command**: manual: the ledger records the maintainer's dated acceptance of the unrecoverable historical payload gap
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 7. **Plan reference**: T030 (Tier 3 deep pass, adversarial step). **Reason**: the runner scored a selection with a substring test over the whole serialized `Skill` tool input, so a call invoking a different skill while mentioning the target would have counted. The matcher is fixed and covered by tests, but the recorded 96-call run did not retain tool-call payloads, so its five positive rows cannot be re-checked directly.

**What is known**: the `Skill` tool was invoked exactly 5 times across all 96 calls; those 5 are exactly the 5 rows scored as selected; each falls on a positive prompt for the skill under test; no row shows a `Skill` invocation without a scored selection. The defect can only inflate a positive, never hide one, so all reported counts are upper bounds and control arm A could only be equal or lower.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: retain the `Skill` tool input alongside `tools_used` in any future run so the question is answerable from the data. Do not re-run the pilot for this alone; the disposition `MEASURED_NO_CHANGE` does not turn on it, because a lower A would narrow the gap criterion 1 already failed on.

**Follow-up, 2026-09-22**: Future runner rows now retain `skill_selectors`, a bounded record of only the `command`, `skill`, and `name` selector fields from each `Skill` call. Scoring reads the same normalized values; non-skill values become `<invalid>`, and prompt or other tool arguments are never copied into results. Tests prove a different skill mentioning the target stays negative, a valid target stays positive, private non-selector text is absent, and normal and timed-out rows retain the observed selector. This mitigates future re-audit failure but cannot recover the 96 historical tool inputs, so this historical evidence gap remains open.

**Original source identity**: `v4.13.0#WN-5`; stable ID `WN-5-v4130` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-5-v4130 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: WN-5-v4130's 96 historical tool payloads were never retained and cannot be recovered; future runs retain selectors, so only maintainer acceptance can close the historical clause.

#### BG-2: A test in the full profile writes into the real user's `~/.nexus-hub`

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: medium - a full-profile run overwrote files under the real `~/.nexus-hub`; a session guard now fails the run on such a change
- **Blocker**: user-deferred - BG-2-v4131 keeps finding the concurrent writer of state/locks with a quiet machine running the full-profile groups one by one, and hosted protected-integration verification.
- **Acceptance**: The concurrent writer of `state/locks` is found by running the full-profile groups one by one on a quiet machine, and protected hosted integration verifies the repair
- **Proving command**: `python scripts/ci/run.py --profile full`
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: Both pytest roots now carry a session guard that records size and modification time of installer-owned `~/.nexus-hub` paths and six global instruction files and fails the session on any change (`NEXUS_REAL_HOME_GUARD=0` opts out for deliberate parallel runs); a deliberate offending test made a passing session exit 1. Residuals (user-deferred): the guard flagged lock files in `state/locks` written by a concurrent local process that no single test file reproduces, which needs a quiet machine running the full-profile groups one by one; and the hosted protected integration run that verifies the repair.

**Source phase**: Phase 9 (full local profile, 2026-09-26). **Plan reference**: T028. **Reason**: during `python scripts/ci/run.py --profile full` (17:46 to 19:53 local time), the real `~/.nexus-hub/scripts/nexus_git_attribution.py` was overwritten at 18:22 with this branch's version, and `~/.nexus-hub/VERSION` and `~/.nexus-hub/permissions-manifest.json` were rewritten at 18:36. Some test ran the real installer against the machine's own home folder instead of a throwaway one (a PowerShell run resolves the home from `USERPROFILE`, so redirecting `HOME` alone does not isolate it). The overwrite made `nexus-hub attribution check` fail with "Attribution guard version differs"; the file was restored from the durable guard (`~/.nexus-hub/git-hooks/guard.py`, which matches `develop`), a backup of the overwritten copy was kept outside the repository, and the check passes again. `VERSION` kept its value (4.13.0). This is most likely pre-existing: earlier runs from `develop` would have copied an identical file and gone unnoticed; it surfaced because this branch changed the script. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: in a disposable Windows account or container, snapshot the home folder, run the full profile group by group, and diff after each to find the test; then isolate it with both `HOME` and `USERPROFILE` (and `APPDATA`, `LOCALAPPDATA`), and add a guard that fails the profile when the real home changes. **Full inventory (2026-09-26)**: a scan of `~/.nexus-hub`, `~/.claude`, `~/.codex`, `~/.gemini`, `~/.cursor`, and the VS Code user settings for files modified during the run found only the three files above plus, in `~/.nexus-hub/state/`, lock files and backups of test fixtures (instruction files headed `# org-test` and `# org-lifecycle`), written by the organization-layer tests. The user's real instruction files (`~/.claude/CLAUDE.md` last changed 2026-09-23, the Codex, Gemini, OpenCode, and Qwen files 2026-09-15) and platform settings were not touched. The leftover fixture backups and locks contain no user data and are safe to delete. So at least two tests leak into the real home: one runs the real installer (the attribution script, `VERSION`, and the permissions manifest), and the organization tests write their backups and locks to the real state folder.

**Local repair (2026-09-27)**: the Bash and PowerShell selection-parity installer tests now provide a disposable `HOME`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, `NEXUS_HUB_HOME`, and Git global-config path; both real installer tests passed, and the PowerShell test confirmed the attribution script landed under the disposable Nexus home. The instruction merger's state root now honors `NEXUS_HUB_HOME` for workspace installs while retaining explicit global-target precedence; a red-then-green root test and 42 organization/merger tests passed. The local full profile was not rerun against the real account. **Status**: open until protected hosted integration verifies this repair; audit any remaining full-profile home writers separately.

**Second writer found (2026-10-02, v4.13.7 Phase 9)**: the v4.13.7 full profile rewrote 52 files under the real `~/.nexus-hub/scripts/`, `permissions-manifest.json`, and `VERSION` (content unchanged at 4.13.6) at 14:51 UTC, while `repo-tests-skills` ran; the rewritten scripts were byte-identical to the v4.13.7 worktree. The writer was `tests/skills/test_presentify_dual_view_distribution.py::test_installed_bundle_runs_offline`, which ran both real installers with the inherited environment. It now redirects the same six variables; rerun alone, it gave `2 passed` with a real-home snapshot identical before and after (v4.13.7 BG-8). The attribution script still matched the durable guard and `nexus-hub attribution check` printed `VERIFIED`. Other full-profile groups were not audited for writers one by one, so this item stays open.

**Original source identity**: `v4.13.1#BG-2`; stable ID `BG-2-v4131` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#BG-2-v4131 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: BG-2-v4131 keeps finding the concurrent writer of state/locks with a quiet machine running the full-profile groups one by one, and hosted protected-integration verification.

#### WN-3: A user edit made between sessions is preserved but not reported

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - the user edit survived in every run; only the report omitted it
- **Blocker**: user-credential - Scenario B re-measurement needs a paid Claude replay run on the maintainer's pilot keys; the hook fix is test-covered only.
- **Acceptance**: Scenario B is re-measured with the current hook and the agent names the user's between-session edit
- **Proving command**: manual: a paid scenario B replay on Claude records whether each run names the user's edit
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 8. **Plan reference**: T019, [`v4.13.1-incident-replay.md`](../v4.13/development/v4.13.1-incident-replay.md). **Reason**: in scenario B the revision request arrives in a new session. All six Claude runs edited the deck in place (so the edit survived) but none named the edit: the new session does not treat the deck as a file it wrote, and its in-place save runs as inline `python -c`, which `user-edit-guard` does not read (it reads script files). **Owner**: catalog maintainer. **Status**: open. **Update (Phase 9 deep pass)**: the hook now also reads inline `python -c`, `node -e`, and `pwsh -Command` code for document paths (`test_deep_pass_writer_routes_are_blocked`), which removes the cause observed in the replay; this is covered by tests but not re-measured. **Suggested next step**: measure scenario B again (with WN-2 and WN-5).

**Original source identity**: `v4.13.1#WN-1`; stable ID `WN-1-v4131` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-1-v4131 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: Scenario B re-measurement needs a paid Claude replay run on the maintainer's pilot keys; the hook fix is test-covered only.

#### WN-4: A moved picture was never named in the agent's report

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - the edit was preserved; only the moved picture went unreported
- **Blocker**: user-credential - Scenario C re-run (three Claude trials per condition) is a paid replay on the maintainer's pilot keys.
- **Acceptance**: Scenario C is re-run (three Claude trials per condition) with the current helper and the moved picture is named
- **Proving command**: manual: a paid scenario C replay (three Claude trials per condition) records whether the moved picture is named
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 8. **Plan reference**: T019. **Reason**: in scenario C, eight of eight runs named the user's new speaker note but none the moved picture; the helper listed the picture move only as a changed part name. The diff now prints "non-text change on slide N ...: tell the user about it", covered by tests but not re-measured by a paid run. **Owner**: catalog maintainer. **Status**: open until measured. **Suggested next step**: re-run scenario C (three Claude trials per condition) with the current helper.

**Original source identity**: `v4.13.1#WN-2`; stable ID `WN-2-v4131` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-2-v4131 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: Scenario C re-run (three Claude trials per condition) is a paid replay on the maintainer's pilot keys.

#### WN-5: Codex replay runs can see the machine's real user skills

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - affects replay isolation only; one Codex run edited without the helper
- **Blocker**: user-deferred - Codex resolves home via the Windows known-folder API, so isolation needs a separate OS account or container that is not available on this host.
- **Acceptance**: Codex replays run under a separate Windows user or in a container, and whether Codex prefers the workspace `.agents/skills` over the global one is recorded
- **Proving command**: manual: run a Codex replay under a separate OS account or container and record which `.agents/skills` directory it loads
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 8. **Plan reference**: T018. **Reason**: Codex resolves the home folder through the Windows known-folder API, not `HOME`, so replay runs also load `~/.agents/skills` from the real profile. One Codex run did not find `edit_guard.py` and edited without the helper. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: run Codex replays under a separate Windows user or in a container, and check whether Codex prefers the workspace `.agents/skills` over the global one.

**Original source identity**: `v4.13.1#WN-3`; stable ID `WN-3-v4131` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-3-v4131 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Codex resolves home via the Windows known-folder API, so isolation needs a separate OS account or container that is not available on this host.

#### WN-6: Scenario D (deck left open) was not re-measured on Claude after the fixes

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - every scenario D run preserved the edit; only the post-fix Claude result is unmeasured
- **Blocker**: user-credential - Post-fix Claude scenario D replay is a paid run on the maintainer's pilot keys.
- **Acceptance**: Scenario D is included in the WN-1 and WN-2 re-measurement on Claude
- **Proving command**: manual: the paid re-measurement record includes a post-fix Claude scenario D result
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 9 (implementation convergence). **Plan reference**: T019. **Reason**: the final replay round covered scenarios A, B, and C on Claude by the maintainer's reduced design; scenario D ran on Claude only in rounds 1 and 2 (before the second fix cycle) and on Codex in round 3, and every run preserved the edit. The post-fix Claude result for D is unmeasured. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: include scenario D in the WN-1 and WN-2 re-measurement.

**Original source identity**: `v4.13.1#WN-5`; stable ID `WN-5-v4131` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-5-v4131 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: Post-fix Claude scenario D replay is a paid run on the maintainer's pilot keys.

#### MT-1: No paid measurement of the rule on a platform other than Claude and Codex

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - the same rule and skill reach the unmeasured platforms
- **Blocker**: user-credential - Measuring the rule on Copilot, Cursor, Gemini or a rule-only platform needs a paid replay on that vendor account.
- **Acceptance**: One rule-only platform is added to the next replay and its result recorded
- **Proving command**: manual: the next replay record includes a rule-only platform result
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 8. **Plan reference**: T018. **Reason**: the replay measured Claude Code (with and without the hook) and Codex. Copilot, Cursor, Gemini, and the rule-only platforms receive the same always-loaded rule and skill but were not measured. **Owner**: catalog maintainer. **Status**: open. **Suggested next step**: add one rule-only platform to the next replay.

**Original source identity**: `v4.13.1#MT-1`; stable ID `MT-1-v4131` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#MT-1-v4131 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: Measuring the rule on Copilot, Cursor, Gemini or a rule-only platform needs a paid replay on that vendor account.

#### WN-7: A headless OpenCode run cannot create a run record, so it cannot reach `PLAN COMPLETE`

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: medium - a headless OpenCode run cannot record approvals and so cannot reach `PLAN COMPLETE`
- **Blocker**: vendor-feature - OpenCode documents no prompt-submit event and `opencode run` attaches no terminal, so a headless approval cannot be captured.
- **Acceptance**: OpenCode is measured interactively with the user answering `yes`, or approvals are captured through a documented OpenCode event once one exists
- **Proving command**: manual: an interactive OpenCode run where the user answers `yes` at the terminal reaches a recorded run record
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 8 (T017), OpenCode pilot 3. **Plan reference**: [v4.13.2 plan, Phase 8, condition C](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `record create` accepts an approval only from a captured prompt or from `yes` typed on the terminal device, and fails closed otherwise. OpenCode documents no prompt-submit lever (`docs/policy/completion-levers.json`, checked 2026-09-25), and `opencode run` attaches no terminal, so a scripted headless first turn can never be recorded. The plan's condition C assumed it could. The pilot showed the consequence before the runbook rule existed: the agent restated the approvals in a table and pushed, tagged, and released without a record.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: measure OpenCode interactively (the user answers `yes` at the terminal), or capture approvals through a documented OpenCode event once one exists; never infer a prompt-submit lever from `message.*` events.

**Original source identity**: `v4.13.2#WN-4`; stable ID `WN-4-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-4-v4132 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: OpenCode documents no prompt-submit event and `opencode run` attaches no terminal, so a headless approval cannot be captured.

#### WN-8: On OpenCode a full run proceeds on in-prompt approvals without a run record

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: medium - the observed run pushed, merged, tagged and released without a run record
- **Blocker**: vendor-feature - No OpenCode signal identifies an `/implement` run, so a push/merge/release refusal plugin cannot be keyed reliably.
- **Acceptance**: An OpenCode plugin on `tool.execute.before` refuses `git push`, `gh pr merge` and `gh release create` while an `/implement` run holds no record, once a reliable run signal exists
- **Proving command**: manual: in an OpenCode `/implement` run with no record, `git push` is refused by the plugin
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 8 (T017), condition C runs C4 to C6. **Plan reference**: [v4.13.2 plan, Phase 8, condition C](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: with no record possible (WN-4), OpenCode 1.18.32 running Claude Sonnet 4.6 restated the approvals as a table, called them recorded, never ran `record create` or `record path`, and pushed, merged, tagged, and released. Every action matched the approval the prompt contained, and the completion gate and runner took no action without a record, but the run did not stop at the first approval point as the runbook requires. Two instruction changes (the Phase 0a rule and the point-of-use `record path` check) did not change the behavior. With the user's decision of 2026-09-27, v4.13.2 ships full-by-default on every platform with this gap recorded; OpenCode is reported as not verified.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: enforce the rule rather than state it: an OpenCode plugin on the documented `tool.execute.before` event could refuse `git push`, `gh pr merge`, and `gh release create` while an `/implement` run holds no record, once a reliable signal for such a run exists.

**Original source identity**: `v4.13.2#WN-7`; stable ID `WN-7-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-7-v4132 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: No OpenCode signal identifies an `/implement` run, so a push/merge/release refusal plugin cannot be keyed reliably.

#### MT-2: Condition B (Codex) has one passing end-to-end run

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - one passing run shows the Codex chain works; only the failure rate is unbounded
- **Blocker**: user-credential - Condition B rerun needs the OpenAI pilot key quota (last run returned Quota exceeded).
- **Acceptance**: Condition B is rerun on Codex and the result recorded in the e2e evidence
- **Proving command**: `python tests/e2e/implement_full/run_e2e.py --agent codex`
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 8 (T018). **Plan reference**: [v4.13.2 plan, Phase 8](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: after B7 reached `PLAN COMPLETE`, the OpenAI pilot key returned `Quota exceeded. Check your plan and billing details.` before any turn, so the planned second run did not happen; one run shows the chain works on Codex but bounds no failure rate.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: rerun condition B in WSL (`tests/e2e/implement_full/run_e2e.py --agent codex`) once the OpenAI limit allows, and record the result in the e2e evidence.

**Original source identity**: `v4.13.2#MT-1`; stable ID `MT-1-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#MT-1-v4132 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: Condition B rerun needs the OpenAI pilot key quota (last run returned Quota exceeded).

#### WN-9: The run record's signature does not cover `pause` or `blockers`

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: medium - an edit that clears a pause or closes a blocker is not reported as `record-tampered`
- **Blocker**: user-deferred - WN-8-v4132 signing pause and blockers changes the run-record signature format and was deliberately not changed during a live signed minor run.
- **Acceptance**: Every writer re-signs through one checker function and `pause` and `blockers` are in the signed payload
- **Proving command**: manual: editing `pause` or `blockers` in a signed run record is reported as `record-tampered`
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `approvals_hmac` now covers `start_head`, `nonce`, and `created` (fixed in this phase), but `pause` and `blockers` are rewritten by several writers (`record pause`, `record block`, the capture hook), so an edit that clears the user's pause or closes an open blocker is not reported as `record-tampered`.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: have every writer re-sign through one checker function, then add both fields to the signed payload.

**Original source identity**: `v4.13.2#WN-8`; stable ID `WN-8-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-8-v4132 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: WN-8-v4132 signing pause and blockers changes the run-record signature format and was deliberately not changed during a live signed minor run.

#### WN-10: Approval capture binds typed text, not the approval class - PARTIALLY RESOLVED 2026-09-29

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: not stated in source; maintainer to set (the original-defect text says "Severity high"; recording high here makes the item security-sensitive and its migration then needs a named approval)
- **Blocker**: vendor-feature - No platform documents a per-prompt user attestation the agent's own tool calls cannot forge.
- **Acceptance**: A capture signal the agent's own tool calls cannot produce binds each approval (for example a host-issued per-prompt attestation), or `cannot-verify` is recorded where none exists
- **Proving command**: `python -m pytest tests/validators/test_approval_binding.py -q`
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Original defect**: `approval-capture` stores a digest of every submitted prompt line, and `record create` accepts an approval whose text matches any captured line. A short reply such as `ok`, a pasted issue body containing "I approve release", or the agent piping a fabricated payload into `completion_gate.py capture` can therefore back an approval class the user never approved. Severity high: this is the threat the contract names.

**Resolved part**: [v4.13.6 Phase 1](../v4.13/plans/v4.13.6-minor-scope-implement-and-verified-cleanup.md) binds every user-origin record write (`record create`, `record answer`, `record pause`, `record resume`) to the exact line the checker generated. `record render` builds the canonical page data, draws a fresh 128-bit round nonce, derives an 8-character single-use code from `HMAC-SHA256(runs secret, page and nonce)`, and writes an owner-only pending round sealed by an HMAC over every field. The write then requires the seal and the live page's code to verify, the bound session (and, for a mid-run answer, pause, or resume, the run record's session), exactly one captured whole prompt equal to the line, and an earlier prompt in that session from before the render, and consumes the round. The capture hook stores only whole-prompt digests with a capture time and skips sessions marked `NEXUS_RUNNER_LAUNCH=1`, which `run_plan.py` sets for every session it launches. The terminal fallback was removed: a missing capture file now refuses, because a process that owns the console or a pty can type into it. So a lone "ok", a quoted code, a pasted body, a replayed or superseded line, a runner-launched prompt, an edited pending round, a fresh headless session opened only to submit the line, and an answer captured in another session never record. The rule is owned by the completion contract's Approval origin section.

**Still open**: the third bypass this item names, an approval the agent itself originates. The agent can pipe a fabricated payload into `completion_gate.py capture`, append a line to the capture file, or pre-seed a nested headless session (`claude -p` with `--session-id`, then resume it with the line), and the capture is indistinguishable from the user's paste. `tests/e2e/implement_full/stub_agent.py` does exactly the first of these to stand in for the user, and the harness passes. The original suggested step "refuse a capture the agent's own tool call produced" is not done; no signal the agent cannot also set (environment, session id, process tree) was found in this pass. Two related limits: the round expires 30 minutes after render, not when the session ends, so a later session can record a line pasted in an earlier one (bound to the session where it was captured); and on a platform with no prompt-submit capture no approval can be recorded at all, so the run asks at each approval point (see WN-4 and DF-5).

**Evidence**: `tests/validators/test_approval_binding.py` (29 passed, 1 POSIX-only skip on Windows): `test_exact_line_records_once_then_reads_code_used`, `test_a_prompt_that_is_not_the_whole_line_never_records[lone-ok|quoted-code|pasted-body|line-plus-text]`, `test_a_line_replayed_from_an_earlier_consumed_round_is_refused`, `test_a_newer_render_invalidates_the_older_code`, `test_a_runner_launched_prompt_is_never_captured`, `test_record_create_refuses_inside_a_runner_launched_session`, `test_a_plan_edit_after_render_reads_page_changed`, `test_an_expired_code_is_refused`, `test_a_mid_run_answer_needs_its_own_exact_line`, `test_a_fresh_session_that_only_carries_the_line_is_refused[auto|nested-agent]`, `test_an_edited_pending_round_is_refused[paste_digests|paste_lines|expires_at|rendered_at|session]`, `test_a_mid_run_answer_captured_in_another_session_is_refused`, `test_a_session_with_no_capture_file_refuses_without_a_terminal_fallback`, `test_pending_file_is_owner_only_on_posix`; plus `test_capture_skips_a_runner_launched_session` and `test_runner_launched_capture_drains_a_large_payload` (both hook implementations) and `test_every_launched_session_is_marked_runner_launched`.

**Owner**: catalog maintainer. **Status**: open (agent-originated capture); the resolved part is local in v4.13.6 Phase 1 and not yet integrated. **Suggested next step**: find a capture signal the agent's own tool calls cannot produce (for example a host-issued per-prompt attestation, if a platform documents one); until then, keep the threat model's statement that a deliberately forged user origin is not detected.

**Tracking alias retained**: `v4.13.6#WN-5`; the following complete historical source has the same current obligation and is not a separate future task.

##### Tracking source: v4.13.6#WN-5 (v4.13.6): v4.13.2 WN-9 is only partly closed

**Evidence**: Definition of Done 3 says it closes v4.13.2 WN-9 for every record type. Every bypass it names (a lone "ok", a quoted code, a pasted issue body, a runner-launched prompt) is refused by `tests/validators/test_approval_binding.py`, but the agent can still originate its own capture (pipe a payload into `completion_gate.py capture`, append to the capture file, or pre-seed a nested session), which is why that entry reads PARTIALLY RESOLVED. This pointer keeps the remainder visible in this plan's section; the item itself stays tracked under v4.13.2 WN-9. **Owner**: catalog maintainer. **Suggested next step**: bind a capture to a platform-authenticated user-turn signal where one exists, and record `cannot-verify` otherwise.

**Original source identity**: `v4.13.2#WN-9`; stable ID `WN-9-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-9-v4132 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: No platform documents a per-prompt user attestation the agent's own tool calls cannot forge.

#### WN-11: `run-plan` checks only global settings for an approval bypass

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: medium - rows with no bypass check can run with an approval bypass unnoticed
- **Blocker**: user-deferred - Refusing unchecked platform rows changes run-plan behavior on four platforms and needs a maintainer decision.
- **Acceptance**: A row with no documented bypass check (Copilot, OpenCode, Kimi) is refused unless `unattended-with-bypass` is approved, after the maintainer decides the behavior change
- **Proving command**: `python -m pytest tests/validators/test_run_plan.py -q`
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: `run_plan.py` now parses JSON and TOML (including single-quoted TOML) instead of regex, reads the documented project scopes (Claude settings and local settings, Codex `.codex/config.toml`, Gemini CLI and Qwen settings) and adds a Cursor `approvalMode: unrestricted` check; `tests/validators/test_run_plan.py` covers each row and scope (19 red before). Residual (user-deferred): refusing platforms with no documented bypass check (Copilot, OpenCode, Kimi) changes run-plan behavior and needs a maintainer decision.

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `bypass_configured` reads the platform's global config with regular expressions. A committed project `.claude/settings.json` with `defaultMode: bypassPermissions`, a single-quoted `approval_policy = 'never'`, or the Cursor, Copilot, OpenCode, and Kimi rows (no check at all) pass unnoticed.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: parse JSON and TOML instead of matching text, include the project-scoped settings under the launch directory, and refuse a row with no check unless `unattended-with-bypass` is approved; confirm first which platforms honor project-level bypass settings.

**Original source identity**: `v4.13.2#WN-11`; stable ID `WN-11-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-11-v4132 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Refusing unchecked platform rows changes run-plan behavior on four platforms and needs a maintainer decision.

#### WN-12: Record lifetime and environment edge cases

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - stated: three low-severity cases
- **Blocker**: user-credential - Confirming the exact `gh pr checks` no-checks stderr needs a freshly opened PR on the maintainer's GitHub account.
- **Acceptance**: The live `gh pr checks` no-checks response is captured on a newly opened PR and matches the guarded pattern
- **Proving command**: manual: run `gh pr checks <new-pr>` immediately after opening a PR and compare its stderr with the guarded `no checks reported` pattern
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: The 72-hour record expiry described above was removed in v4.13.7 (`e46a1dd48`): records never expire and stop counting as live at the signed `completed` stamp or on `record retire`; the run-record decision record carries a dated amendment. Residual (user-credential): capturing the exact `gh pr checks` no-checks stderr needs a freshly opened pull request on the maintainer's account.

**Source phase**: Phase 9 (T024), Tier 3 adversarial pass. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: three low-severity cases. A pull request opened moments ago may answer `no checks reported on the '<branch>' branch`, which is not in the not-found list and reads as `cannot-verify` (text reasoned from `gh`'s source, not reproduced). A record bound to the same session never expires, so a session resumed weeks later still carries its approvals. A home directory that is itself a git working tree, or a `GIT_DIR` in the environment, makes every record read as tampered.

**Owner**: catalog maintainer. **Status**: open, partially repaired and integrated through [PR #374](https://github.com/bendourthe/Nexus-Hub/pull/374) at `510fd987`; its required checks passed with one expected skip, and [post-merge run 36455108200](https://github.com/bendourthe/Nexus-Hub/actions/runs/36455108200) passed smoke and provenance. Same-session and unspecified-session records older than 72 hours are now ignored, and inherited Git repository selectors no longer misclassify an untracked private record inside a home Git tree; a tracked record still blocks as tampered. The 104 focused checker and runner tests passed, including negative controls for an extra `gh` error and a tracked record. The fresh-PR `no checks reported` text is handled in the checker and stub tests, but the exact stderr remains unverified: `gh pr checks 374` already showed pending jobs immediately after PR creation. **Suggested next step**: capture the live no-checks response on a future newly opened PR and compare it to the guarded pattern before closing this item; keep malformed or additional errors as `cannot-verify`.

- **Migrated from**: v4.13#WN-13 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: Confirming the exact `gh pr checks` no-checks stderr needs a freshly opened PR on the maintainer's GitHub account.

#### DF-1: Approval capture is missing on Pi, OpenClaw, Hermes, and Windsurf

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: medium - on these platforms `record create` refuses with `approval-not-captured`
- **Blocker**: vendor-feature - The prompt-event payload field carrying user text is not verified for Pi, OpenClaw and Hermes plugins.
- **Acceptance**: Approval capture runs on the documented prompt event of the Pi, OpenClaw and Hermes plugin adapters, with a parity test
- **Proving command**: manual: on each of Pi, OpenClaw and Hermes, a submitted prompt produces a stored approval-capture digest
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: Windsurf `pre_user_prompt` now runs `approval-capture.sh`; `test_pre_user_prompt_capture_stores_the_digest[sh|ps1]` feeds a documented Cascade payload through the compat wrapper and checks the stored digest. Residual (vendor-feature): the prompt-text field of the Pi, OpenClaw and Hermes plugin events is unverified.

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `docs/policy/completion-levers.json` records a VERIFIED prompt-submit lever for these four platforms, but only Claude-format registrations and Cursor carry `approval-capture`, so on them `record create` cannot record an approval (the same effect as WN-4 on OpenCode). **Update (v4.13.6 Phase 1)**: the terminal fallback was removed, so on these platforms `record create` now refuses with `approval-not-captured` even in an interactive session until capture is added.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: add capture on each platform's documented prompt event in its plugin or hook adapter, with a parity test.

**Original source identity**: `v4.13.2#DF-5`; stable ID `DF-5-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-5-v4132 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: The prompt-event payload field carrying user text is not verified for Pi, OpenClaw and Hermes plugins.

#### MT-3: No real CLI run exercised a gate refusal or a runner resume

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - gate refusal and runner resume are proven by stub tests
- **Blocker**: user-credential - Exercising a real gate refusal and runner resume needs a paid Claude/Codex session on the maintainer's keys.
- **Acceptance**: One paid condition with a fixture that cannot finish in one turn records the gate and runner cycles
- **Proving command**: `python tests/e2e/implement_full/run_e2e.py --agent claude`
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 9 (T024), Tier 3 code-vs-plan convergence. **Plan reference**: [v4.13.2 plan, Phase 9, sub-task 9.6](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: every passing Phase 8 run on Claude Code and Codex reached `PLAN COMPLETE` in its first turn, so the turn-end gate's refusal and the runner's resume are proven by stub tests (`test_harness.py`, `test_completion_gate.py`) and never by a paid session.

**Owner**: catalog maintainer. **Status**: open. **Suggested next step**: run one paid condition with a fixture that cannot finish in one turn (for example a phase whose test only passes after a second commit) and record the gate and runner cycles. **Update (v4.13.6 Phase 1)**: under exact binding, the paid conditions in `tests/e2e/implement_full/run_e2e.py` (`--agent claude|codex|opencode`) cannot record: their first turn states the approvals verbatim in the prompt, which never equals a line `record render` generates, so `record create` refuses (`approval-not-captured` or `session-too-new`) and the run cannot reach `PLAN COMPLETE`. Owner: v4.13.6 Phase 7. The paid first turn needs a render step whose printed line is then fed as a second scripted user turn in the same session, before any paid run is spent on this item.

- **Migrated from**: v4.13#MT-2 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: Exercising a real gate refusal and runner resume needs a paid Claude/Codex session on the maintainer's keys.

#### DF-2: Devin Desktop reads `.devin/hooks.json`, which the Windsurf integration does not model

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer, via `[[platform-contract-verification]]`
- **Severity**: low - the completion gate is unaffected; the drift matters for the guardrail hooks
- **Blocker**: vendor-feature - windsurf.py merges only the user-level hooks.json; adding the workspace .devin/hooks.json path needs a freshly fetched docs.devin.ai Cascade hooks page recorded at the next platform-contract pass, then an adapter change with a test.
- **Acceptance**: The Cascade workspace hook path is re-verified and `docs/policy/platform-read-contracts.json` and `scripts/lib/integrations/windsurf.py` are updated together
- **Proving command**: `python scripts/check_platform_contract_freshness.py`
- **Future plan**: next `/update release` platform-contract pass

**Source phase**: Phase 1 (T002). **Plan reference**: [v4.13.2 plan, sub-task 1.2](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the Cascade hooks page (fetched 2026-09-25, [docs.devin.ai/desktop/cascade/hooks](https://docs.devin.ai/desktop/cascade/hooks)) lists `~/.codeium/windsurf/hooks.json` (user), `.devin/hooks.json` (workspace), and a system file. The `windsurf` integration writes native hooks but its read contract predates the `.devin/hooks.json` workspace path. No continuation lever exists on this surface either way (`post_cascade_response` is asynchronous), so the completion gate is unaffected; the drift matters for the guardrail hooks.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: at the next `/update release` platform pass, re-verify the Cascade workspace hook path and update `docs/policy/platform-read-contracts.json` and `scripts/lib/integrations/windsurf.py` together.

**Original source identity**: `v4.13.2#DF-1`; stable ID `DF-1-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-1-v4132 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: windsurf.py merges only the user-level hooks.json; adding the workspace .devin/hooks.json path needs a freshly fetched docs.devin.ai Cascade hooks page recorded at the next platform-contract pass, then an adapter change with a test.

#### DF-3: Antigravity 1.0 hook support is unconfirmed while the integration declares none

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer, via `[[platform-contract-verification]]`
- **Severity**: low - the integration conservatively declares no hooks for Antigravity 1.0
- **Blocker**: vendor-feature - No first-party page confirms hooks for Antigravity 1.0 and no 1.0 install is available to observe one.
- **Acceptance**: A first-party page scoped to Antigravity 1.0, or an observed hook firing in a 1.0 install, settles `hooks_supported`
- **Proving command**: manual: observe whether a registered hook fires in an Antigravity 1.0 install and record the result
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 1 (T002). **Plan reference**: [v4.13.2 plan, sub-task 1.2](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: `scripts/lib/integrations/antigravity.py:75` sets `hooks_supported: False` for Antigravity 1.0. The hooks page ([antigravity.google/docs/hooks](https://antigravity.google/docs/hooks/), fetched 2026-09-25) says hooks work across "Antigravity 2.0, Antigravity CLI, and Antigravity IDE" without stating whether that IDE is the 1.0 product. The plan's premise that 1.0 supports hooks is therefore not confirmed; `completion-levers.json` records every 1.0 lever as "none documented".

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: confirm against a first-party page scoped to Antigravity 1.0, or by observing a registered hook fire in a 1.0 install; change `hooks_supported` only on that evidence.

**Original source identity**: `v4.13.2#DF-2`; stable ID `DF-2-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-2-v4132 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: No first-party page confirms hooks for Antigravity 1.0 and no 1.0 install is available to observe one.

#### DF-4: Devin CLI reads Claude Code's hook files, so Claude registrations also reach it

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer, via `[[platform-contract-verification]]`
- **Severity**: low - the shared read is recorded; only an untested payload shape remains
- **Blocker**: vendor-feature - Devin CLI's hook payload fields are not captured from vendor docs or a live run, so a parity case would be invented.
- **Acceptance**: A Devin-CLI payload case is added to the hook parity tests for every hook that inspects payload fields, once the payload fields are documented
- **Proving command**: manual: a fetched Devin CLI hooks document names the payload fields before the parity case is written
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: `platform-read-contracts.md` records that Devin CLI reads Claude Code's hook files while `read_config_from.claude` is on (its default), from the hooks overview re-fetched 2026-10-10. Residual (vendor-feature): Devin CLI hook payload fields are not documented, so a parity case would be invented.

**Source phase**: Phase 1 (T002). **Plan reference**: [v4.13.2 plan, sub-task 1.2](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: the Devin CLI hooks overview ([docs.devin.ai/cli/extensibility/hooks/overview](https://docs.devin.ai/cli/extensibility/hooks/overview), fetched 2026-09-25) lists `.claude/settings(.local).json`, `~/.claude.json`, and `~/.claude/settings(.local).json` among its configuration sources. Every Claude hook Nexus-Hub registers therefore also runs under Devin CLI, which the read contract does not state. The completion gate relies on this deliberately (the `top-level-block` shape matches); other hooks may meet payload shapes they were not tested against.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: record the shared read in `docs/policy/platform-read-contracts.md` and add a Devin-CLI payload case to the hook parity tests for any hook that inspects payload fields.

**Original source identity**: `v4.13.2#DF-3`; stable ID `DF-3-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-3-v4132 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: Devin CLI's hook payload fields are not captured from vendor docs or a live run, so a parity case would be invented.

#### DF-5: OpenClaw and Hermes completion plugins need a manual enable step

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer, via `[[platform-contract-verification]]`
- **Severity**: low - the installer reports NEEDS SETUP with each platform's documented enable command
- **Blocker**: vendor-feature - OpenClaw and Hermes plugin-enable config locations were not stated verbatim by first-party pages (2026-09-25).
- **Acceptance**: Both config locations are verified against first-party pages, then enablement is written through the platform CLI or seeded under the do-not-invent rule
- **Proving command**: manual: verify the OpenClaw and Hermes plugin-enable config locations against first-party pages and record the source URLs
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phase 5 (T011). **Plan reference**: [v4.13.2 plan, sub-task 5.1](../v4.13/plans/v4.13.2-implement-full-by-default-with-completion-goal.md). **Reason**: OpenClaw loads a user plugin only when `plugins.entries.<id>.enabled` is set and its conversation hook is allowed (`hooks.allowConversationAccess`); Hermes loads one only when its name is in `plugins.enabled` in `~/.hermes/config.yaml`. The research on 2026-09-25 verified both requirements but not the exact config file locations and shapes verbatim, so the installer places the plugin files and reports NEEDS SETUP with each platform's documented enable command (`openclaw plugins enable nexus-completion-gate`, `hermes plugins enable nexus-completion-gate`) instead of editing an unverified config path. Until the user runs it, a full run on those two platforms continues only through `nexus-hub run-plan`.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: verify both config locations against first-party pages, then either write the enablement through the platform's own CLI when it is detected or seed the config key under the platform-defaults do-not-invent rule.

**Original source identity**: `v4.13.2#DF-4`; stable ID `DF-4-v4132` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-4-v4132 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: OpenClaw and Hermes plugin-enable config locations were not stated verbatim by first-party pages (2026-09-25).

#### DF-6 (v4.13.3): Flip the skill-index pointer on by default, and decide todos-on-demand

**Carry-forward contract (v4.13.11)**:
- **Owner**: `v4.15.2-adoption-harness-economics-and-portable-engineering-system`
- **Severity**: low - the pointer ships opt-in; the default is unchanged
- **Blocker**: user-deferred - Owned by v4.15.2, whose full-vs-pointer pairing evaluator must produce organic-selection receipts first.
- **Acceptance**: The evaluator's `NEXUS_HUB_SKILL_INDEX=full` against `pointer` pair records organic skill selection including guard skills, and the default is decided
- **Proving command**: manual: the v4.15.2 pairing evaluator's receipt records organic selection for both variants
- **Future plan**: v4.15.2-adoption-harness-economics-and-portable-engineering-system

**Plan reference**: Resolved decisions 1 and 4. **Reason**: the pointer ships opt-in. Flipping it needs organic-selection evidence that skills the model saw in the table are still chosen when it sees only a pointer; the todos-on-demand question needs the same instruction-size evidence. **Evidence**: [`rendered-context-baseline.md`](../v4.13/development/rendered-context-baseline.md) (the index is 81-84% of each rendered file; the pointer removes 99.5% of it). **Owner**: `v4.15.2-adoption-harness-economics-and-portable-engineering-system` (moved from `v4.15.0-instruction-necessity-review` on 2026-09-28: the organic-selection evidence comes from the v4.15.2 pairing evaluator, and the v4.15.0 plan never took the item on; see [`v4.15.2-comparison-harness-economics-delta.md`](../v4.15/comparisons/v4.15.2-comparison-harness-economics-delta.md) D4). **Suggested next step**: run the evaluator's required `NEXUS_HUB_SKILL_INDEX=full` against `pointer` variant pair, recording organic skill selection including guard skills, then decide the default.

**Original source identity**: `v4.13.3#DF-1`; stable ID `DF-1-v4133` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-1-v4133 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Owned by v4.17.3, whose full-vs-pointer pairing evaluator must produce organic-selection receipts first.

#### DF-7 (v4.13.3): Pilot variant mode for instruction-file comparisons

**Carry-forward contract (v4.13.11)**:
- **Owner**: v4.15.0
- **Severity**: low - tooling gap; spend cap for this plan was 0
- **Blocker**: user-deferred - Owned by v4.15.0 instruction-necessity review; variant staging is not yet scheduled there.
- **Acceptance**: A variant mode in `scripts/run_trigger_pilot.py` stages instruction files per arm
- **Proving command**: manual: a trigger-pilot run with the variant mode stages a full-index and a pointer instruction file in separate arms
- **Future plan**: v4.15.0 instruction-necessity review

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: The handoff is recorded in the v4.15.0 plan's `## Inherited known gaps` section; implementation stays with that plan (user-deferred).

**Plan reference**: Resolved decision 6. **Reason**: `scripts/run_trigger_pilot.py` varies only SKILL.md description lines and runs with `--setting-sources project`, so it cannot compare an instruction file with the full index against one with the pointer. Spend cap for this plan: 0. **Owner**: v4.15.0. **Suggested next step**: add a variant mode that stages instruction files per arm.

**Original source identity**: `v4.13.3#DF-2`; stable ID `DF-2-v4133` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-2-v4133 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Owned by v4.16.0 instruction-necessity review; variant staging is not yet scheduled there.

#### DF-8 (v4.13.3): Static-measurement ownership split for v4.15.2

**Carry-forward contract (v4.13.11)**:
- **Owner**: v4.15.2
- **Severity**: low - ownership handoff; no defect
- **Blocker**: user-deferred - Static measurement is v4.15.2 work, which the plan already binds to the existing estimator.
- **Acceptance**: v4.15.2 static measurement imports `estimate_tokens` and `legacy_instruction_block.detect` from their current owners
- **Proving command**: manual: the v4.15.2 static-measurement code imports `estimate_tokens` and `legacy_instruction_block.detect` rather than redefining them
- **Future plan**: v4.15.2

**Plan reference**: Phase 6.2 handoff. **Reason**: `scripts/measure_rendered_context.py` owns rendered instruction-file measurement; v4.15.2's static measurement must reuse its estimator and detector rather than add a second definition of an estimated token or a candidate span. **Owner**: v4.15.2. **Suggested next step**: import `estimate_tokens` and `legacy_instruction_block.detect` from their current owners.

**Original source identity**: `v4.13.3#DF-4`; stable ID `DF-4-v4133` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-4-v4133 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Static measurement is v4.17.3 work, which the plan already binds to the existing estimator.

#### DF-9 (v4.13.3): Per-agent `omitClaudeMd` for catalog agents

**Carry-forward contract (v4.13.11)**:
- **Owner**: `v4.14.0-adoption-agent-tooling-and-subagent-cost`
- **Severity**: low - cost optimization; each catalog agent inherits about 29k estimated tokens
- **Blocker**: user-deferred - Owned by v4.14.0 and gated on a v4.15.2 cost/pass-rate pairing receipt not yet produced.
- **Acceptance**: A change is accepted only with a v4.15.2 pairing receipt showing lower cost at an unchanged pass rate
- **Proving command**: manual: a v4.15.2 pairing receipt shows lower cost at an unchanged pass rate before `omitClaudeMd` is set on any agent
- **Future plan**: v4.14.0-adoption-agent-tooling-and-subagent-cost

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: The handoff is recorded in the v4.14.0 plan's `## Inherited known gaps` section; implementation stays with that plan (user-deferred).

**Source**: [`v4.15.2-comparison-harness-economics-delta.md`](../v4.15/comparisons/v4.15.2-comparison-harness-economics-delta.md) D5, recorded 2026-09-28. **Reason**: Claude Code 2.1.271 added agent frontmatter `omitClaudeMd`, which lets a subagent run without user, project and local `CLAUDE.md` files (managed policy still loads). Each catalog agent now inherits the full rendered instruction files, measured at about 29k estimated tokens on the maintainer machine. **Owner**: `v4.14.0-adoption-agent-tooling-and-subagent-cost`. **Constraints**: decide agent by agent; exclude `project-standards-reviewer` and any agent that enforces repository conventions; confirm the Gemini and Codex agent loaders ignore an unknown frontmatter key, or emit the key only in the Claude copy. **Suggested next step**: accept a change only with a v4.15.2 pairing receipt showing lower cost at an unchanged pass rate.

- **Migrated from**: v4.13#DF-8 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Owned by v4.16.2 and gated on a v4.17.3 cost/pass-rate pairing receipt not yet produced.

#### MT-4 (v4.13.3): The full installers were not run end to end on a disposable machine

**Carry-forward contract (v4.13.11)**:
- **Owner**: release maintainer
- **Severity**: low - flag parsing, forwarding and report wiring are unit-tested and CI runs both installers on native hosts
- **Blocker**: user-deferred - A full installer run needs a disposable machine because it writes real %APPDATA% and VS Code extensions.
- **Acceptance**: A real full install runs on a disposable machine that carries a legacy block and its report is recorded
- **Proving command**: manual: run the full installer on a disposable machine carrying a legacy block and record the legacy report
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Phases 4 and 5. **Reason**: the full PowerShell installer also installs VS Code extensions through the real `code` CLI and writes the real `%APPDATA%` settings, which a redirected HOME does not isolate, so the Phase 4 and 5 verification drove the installer's own engine (per-platform runner calls plus `legacy-report`) instead. The installers' flag parsing, forwarding, and report wiring are unit-tested, and CI runs both installers on their native hosts. **Owner**: release maintainer. **Suggested next step**: the last-phase human testing suggestions include a real install on a machine that carries a legacy block.

**Original source identity**: `v4.13.3#MT-1`; stable ID `MT-1-v4133` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#MT-1-v4133 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: A full installer run needs a disposable machine because it writes real %APPDATA% and VS Code extensions.

#### WN-13 (v4.13.3): Behavioral-lever drift found by the release contract pass

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer, via `[[platform-contract-verification]]`
- **Severity**: low - stated: every seeded value remains valid
- **Blocker**: user-deferred - Seeding per-model modelSettings pins a model id; the maintainer must decide, while env CLAUDE_CODE_EFFORT_LEVEL still delivers effort.
- **Acceptance**: The maintainer decides whether to seed Claude's effort under `modelSettings` for the default model, and the lever rows and `configs/platform-defaults.json` are refreshed
- **Proving command**: `python scripts/sync_platform_defaults.py --check`
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: The Antigravity `agentMode` statement, rationale and verified date are refreshed from a 2026-10-10 re-fetch (default pauses for diff review; plan prepends `/plan`), with the levers row; `sync_platform_defaults.py --check` passes. Residual (user-deferred): seeding Claude per-model `modelSettings` pins a model id and needs a maintainer decision.

**Source phase**: `/update release` platform-contract verification, 2026-09-28. **Reason**: advisory lever changes (logged in `docs/policy/platform-defaults-levers.md`): Claude Code ignores a user-scope `effortLevel` on Opus 5.5 and later, so that seed no longer reaches the default model (the seeded `env.CLAUDE_CODE_EFFORT_LEVEL` still does); Codex's documented `model_reasoning_effort` and `approval_policy` value lists changed, and the page no longer names those keys as user-only; and Antigravity's `agentMode` values now describe different behavior. Every seeded value remains valid.

**Owner**: catalog maintainer, via `[[platform-contract-verification]]`. **Status**: open. **Suggested next step**: seed Claude's effort under `modelSettings` for the default model, refresh the Codex and Antigravity lever rows and `configs/platform-defaults.json`, then run `python scripts/sync_platform_defaults.py --check`.

**Original source identity**: `v4.13.3#WN-6`; stable ID `WN-6-v4133` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-6-v4133 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Seeding per-model modelSettings pins a model id; the maintainer must decide, while env CLAUDE_CODE_EFFORT_LEVEL still delivers effort.

#### WN-14 (v4.13.6): Claude Code interactive `/goal` capture is observed only headless

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - the headless probe already shows verbatim capture
- **Blocker**: user-deferred - Needs a human-typed /goal in an interactive Claude Code session with a logging UserPromptSubmit hook; only the headless probe exists.
- **Acceptance**: A human-typed `/goal test condition` in an interactive session logs a matching prompt and the `claude` row is set to `verbatim` with `probe_mode: interactive`
- **Proving command**: manual: type `/goal test condition` in an interactive Claude Code session of a scratch project whose `UserPromptSubmit` hook logs its payload, and compare the logged prompt
- **Future plan**: v4.14 known-gaps sweep

**Evidence**: the Phase 1 probe (Claude Code 2.1.283, 2026-09-29) ran `claude -p "/goal test condition"`: the `UserPromptSubmit` payload's `prompt` field was exactly `/goal test condition` and the transcript shows `Goal set: test condition`. A person typing `/goal` in the interactive terminal was not exercised, so the `claude` row of `docs/policy/completion-levers.json` stays `goal_capture: unverified` with `probe_mode: headless`, and the validator accepts `verbatim` only from an interactive probe. **Owner**: catalog maintainer. **Suggested next step**: type `/goal test condition` in an interactive session of a scratch project whose `UserPromptSubmit` hook logs its payload, and set the row to `verbatim` with `probe_mode: interactive` if the logged prompt matches.

**Original source identity**: `v4.13.6#WN-1`; stable ID `WN-1-v4136` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-1-v4136 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Needs a human-typed /goal in an interactive Claude Code session with a logging UserPromptSubmit hook; only the headless probe exists.

#### WN-15 (v4.13.6): The whole website guide reports 100 detector findings on views this plan did not touch

**Carry-forward contract (v4.13.11)**:
- **Owner**: guide maintainer
- **Severity**: low - pre-existing findings at the same distribution as base; the edited view passes
- **Blocker**: user-deferred - Triage of 100 pre-existing whole-guide detector findings plus a new whole-page render gate is a multi-view guide project outside this sweep.
- **Acceptance**: Each finding is fixed or allowlisted with a recorded reason and the whole-page run is added to the guide render gate
- **Proving command**: `python catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py guides/website/nexus-hub-guide.html`
- **Future plan**: v4.14 known-gaps sweep

**Evidence**: `detect_visual_defects.py guides/website/nexus-hub-guide.html` (default viewports 420, 900, 1440; light and dark) reports the capped 100 findings, 10 `parent-padding-escape` (the first is the landing view's `h1 > b`) and 90 `svg-viewbox-overflow`, with the same distribution at base `7067df15`, so none comes from this plan. The Cheatsheets view this plan edited passes with 0 findings in both themes at base and head. **Owner**: guide maintainer. **Suggested next step**: run the detector per view with `--fragment`, fix or allowlist each finding with a recorded reason, and add the whole-page run to the guide render gate.

**Original source identity**: `v4.13.6#WN-4`; stable ID `WN-4-v4136` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-4-v4136 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Triage of 100 pre-existing whole-guide detector findings plus a new whole-page render gate is a multi-view guide project outside this sweep.

#### DF-10 (v4.13.6): Copilot CLI sets no native goal headlessly

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - Copilot CLI keeps an interactive goal path
- **Blocker**: vendor-feature - Copilot CLI documents no headless /goal entry point; run_plan.py keeps copilot/cli in INTERACTIVE_GOAL_ROWS.
- **Acceptance**: Copilot CLI documents a headless goal entry point and the row is added
- **Proving command**: manual: re-check the Copilot CLI documentation for a headless `/goal` entry point and record the result
- **Future plan**: v4.17, with v4.13.2 DF-6

**Evidence**: `scripts/run_plan.py` keeps `copilot/cli` in `INTERACTIVE_GOAL_ROWS` because its headless path is `copilot --autopilot -p` with a bypass flag, not `/goal`; the plan's cut-line allowed this slip (sub-task 6.3, T051). Claude, Qwen, and Kimi launch the goal headlessly. **Owner**: catalog maintainer. **Target version**: v4.17, with v4.13.2 DF-6. **Suggested next step**: re-check the Copilot CLI documentation for a headless goal entry point and add the row when one is documented.

**Original source identity**: `v4.13.6#DF-1`; stable ID `DF-1-v4136` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-1-v4136 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: Copilot CLI documents no headless /goal entry point; run_plan.py keeps copilot/cli in INTERACTIVE_GOAL_ROWS.

#### QG-1 (v4.13.6): The non-engineer read-back of the approval page is pending

**Carry-forward contract (v4.13.11)**:
- **Owner**: the user, via the orchestrator
- **Severity**: low - the automated half passes; only the human read-back is pending
- **Blocker**: user-deferred - The redesigned approval page needs a non-engineer read-back, which an agent cannot perform.
- **Acceptance**: A non-engineer reads the redesigned page and pass or fail is recorded with the page version in `development/v4.13.6-last-phase-evidence.md`
- **Proving command**: manual: a non-engineer reads `readback-page-v2.md` and the result is recorded with the page version
- **Future plan**: v4.14 known-gaps sweep

**Evidence**: Definition of Done 6 requires one non-engineer read-back recorded in the final phase. **Read-back result, 2026-09-30**: the user read the ten-section page rendered from the two-plan fixture (`approval_page.py` at `219513b3`) and found it too wordy, noting that many users will not read it. That result led to the redesign: a results table (released, fixed, archived, cleaned up, and permission prompts when they are turned off), two bold limits, and the paste line, all within 80 words, with the technical sections moved under "Details (optional)". The redesigned page has not been read back yet, so this item stays open. The automated half (jargon list, sentence ceiling, risk order, paste line without paths) passes in `tests/validators/test_approval_page.py`. **Owner**: the user, via the orchestrator. **Suggested next step**: have a non-engineer read the redesigned page (the two-plan fixture render, saved beside the first read-back as `readback-page-v2.md`), then record pass or fail with the page version in `development/v4.13.6-last-phase-evidence.md`.

**Original source identity**: `v4.13.6#QG-1`; stable ID `QG-1-v4136` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#QG-1-v4136 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: The redesigned approval page needs a non-engineer read-back, which an agent cannot perform.

#### WN-16 (v4.13.9): The GPT-6.1 Sol announcement could not be read

**Carry-forward contract (v4.13.11)**:
- **Owner**: not stated in source; maintainer to set
- **Severity**: low - nothing in the Sol profile rests on the unread announcement
- **Blocker**: vendor-feature - openai.com/index/introducing-gpt-6-1-sol/ returned HTTP 403; profile claims rest only on the model catalog.
- **Acceptance**: The announcement is re-fetched from an unblocked session and the profile claims are checked against it
- **Proving command**: manual: re-fetch `openai.com/index/introducing-gpt-6-1-sol/` and record whether it is readable and matches the profile claims
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: Phase 1. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T403.
- **Reason**: `openai.com/index/introducing-gpt-6-1-sol/` returned HTTP 403 on 2026-09-30. The announcement's "a fifth of the price" and "Near-Astra" headline is therefore verified only as far as the wording of OpenAI's model catalog. Nothing in the Sol profile may rest on the announcement.
- **Suggested next step**: re-fetch the announcement from a session that is not blocked. If it is readable, check the profile claims against it and add any primary-source fact through the writer's `write --input` path.

**Original source identity**: `v4.13.9#WN-1`; stable ID `WN-1-v4139` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-1-v4139 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: openai.com/index/introducing-gpt-6-1-sol/ returned HTTP 403; profile claims rest only on the model catalog.

#### WN-17 (v4.13.9): Cursor's primary documentation for `/visualize` was not read

**Carry-forward contract (v4.13.11)**:
- **Owner**: not stated in source; maintainer to set
- **Severity**: low - option (b), mirroring everywhere, stands
- **Blocker**: vendor-feature - cursor.com/docs/agent/chat/commands documents neither /visualize nor command-name precedence; option (b) stands.
- **Acceptance**: Cursor documents `/visualize` or command-name precedence and T402's decision is re-run against that page
- **Proving command**: manual: re-check `https://cursor.com/docs/agent/chat/commands` for `/visualize` and command-name precedence and record the result
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: Phase 1. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T402 and T403.
- **Reason**: the comparison relied on a newsletter summary of Cursor's `/visualize`. On 2026-10-01 a `cursor.com` search and a fetch of `https://cursor.com/docs/agent/chat/commands` stated nothing about a built-in `/visualize`, about how a same-named user command takes precedence, or about where commands are stored. Only the discovery locations (`.cursor/commands/`, `~/.cursor/commands/`) were found.
- **Suggested next step**: when Cursor documents `/visualize` or command-name precedence, re-run T402's decision against that page. Option (b), mirroring everywhere, stands until then.

**Original source identity**: `v4.13.9#WN-2`; stable ID `WN-2-v4139` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-2-v4139 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: cursor.com/docs/agent/chat/commands documents neither /visualize nor command-name precedence; option (b) stands.

#### DF-11 (v4.13.9): The Codex `doctor` advisory was cut from this plan

**Carry-forward contract (v4.13.11)**:
- **Owner**: not stated in source; maintainer to set
- **Severity**: low - cut by an interview decision; a runbook covers the need
- **Blocker**: vendor-feature - Reopen requires two primary OpenAI sources confirming the fix version and a second host hazard; neither exists.
- **Acceptance**: Two primary OpenAI sources confirm the fix version and a second host hazard appears, as the Non-Goals state
- **Proving command**: manual: record two primary OpenAI sources and a second host hazard before reopening
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: Phase 1. **Plan reference**: `v4.13.9-adoption-inline-visualize-codex-disk-writes-review-flow-gpt-6-1-sol.md`, T403 and the Non-Goals.
- **Reason**: interview Q2 chose a runbook only. The `doctor` advisory, its `DIAGNOSTIC_ADVISORY` constant, a host-hazard module, and a host-hazard data file are out of scope.
- **Suggested next step**: reopen only when two primary OpenAI sources confirm the fix version and a second host hazard appears, as the Non-Goals state.

**Original source identity**: `v4.13.9#DF-1`; stable ID `DF-1-v4139` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#DF-1-v4139 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: Reopen requires two primary OpenAI sources confirming the fix version and a second host hazard; neither exists.

#### DF-12 (v4.13.9): Claude Haiku 5.5 is announced but has no profile or map cell

**Carry-forward contract (v4.13.11)**:
- **Owner**: not stated in source; maintainer to set
- **Severity**: low - no profile can exist until the model is in the models overview
- **Blocker**: vendor-feature - Claude Haiku 5.5 is announced but not in Anthropic's models overview, so no profile can be verified.
- **Acceptance**: The models overview lists Claude Haiku 5.5, its profile is written and the `fast` tier cell of the model map is refreshed
- **Proving command**: manual: when the models overview lists it, run `/tune-prompting <haiku-5-5-id> --profiles-only` and refresh the `fast` tier cell
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: Phase 1. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T304.
- **Reason**: Anthropic announced Claude Haiku 5.5 "in the coming weeks" and it is not yet in the models overview, so no prompting profile or model-map cell can be verified against a primary source.
- **Suggested next step**: when the models overview lists it, run `/tune-prompting <haiku-5-5-id> --profiles-only` and refresh the `fast` tier cell of the model map.

- **Carried from**: v4.13.8#DF-1 on 2026-10-02

- **Migrated from**: v4.13#DF-9 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: Claude Haiku 5.5 is announced but not in Anthropic's models overview, so no profile can be verified.

#### DF-13 (v4.13.9): Nine newly rostered Claude models have no prompting profile

**Carry-forward contract (v4.13.11)**:
- **Owner**: not stated in source; maintainer to set
- **Severity**: low - each model is rostered as UNVERIFIED rather than claimed
- **Blocker**: user-deferred - Nine Claude prompting profiles need per-model /tune-prompting research; claude-opus-5-5 is scheduled for v4.18.0.
- **Acceptance**: Each of the nine rostered Claude models has a verified prompting profile, starting with `claude-opus-5-5`
- **Proving command**: `python scripts/verify_model_prompting_profiles.py`
- **Future plan**: v4.18.0 for `claude-opus-5-5`; v4.14 known-gaps sweep for the remaining models

- **Source phase**: Phase 2. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T306.
- **Reason**: the live Claude roster read from the Models API on 2026-09-30 added nine ids that this plan does not research, by design (it calibrates on `claude-sonnet-5-5` only): `claude-fable-5`, `claude-haiku-4-5-20251001`, `claude-opus-4-5-20251101`, `claude-opus-4-6`, `claude-opus-4-7`, `claude-opus-4-8`, `claude-opus-5-5`, `claude-sonnet-4-5-20250929`, and `claude-sonnet-4-6`. Each is now a rostered UNVERIFIED model. The live id `claude-haiku-4-5-20251001` sits beside the existing `claude-haiku-4-5` profile, which uses the alias.
- **Suggested next step**: `claude-opus-5-5` first, through `v4.18.0`, which already plans that profile; then `/tune-prompting <id> --profiles-only` per remaining current model. Decide whether the dated Haiku id and the alias should share one profile before profiling either again.

- **Carried from**: v4.13.8#DF-3 on 2026-10-02

- **Migrated from**: v4.13#DF-11 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Nine Claude prompting profiles need per-model /tune-prompting research; claude-opus-5-5 is scheduled for v4.17.6.

#### WN-18 (v4.13.9): The primary roster mixes vendors, so its freshness check always reads DRIFTED

**Carry-forward contract (v4.13.11)**:
- **Owner**: maintainer (bendourthe)
- **Severity**: low - the freshness check is advisory and blocks nothing
- **Blocker**: user-deferred - Whether the dated Haiku 4.5 id and its alias share one profile is a maintainer decision tied to DF-11.
- **Acceptance**: The maintainer decides whether the dated Haiku 4.5 id and its alias share one profile
- **Proving command**: `python scripts/check_model_prompting_freshness.py --advisory`
- **Future plan**: v4.14 known-gaps sweep, together with DF-11

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: The profile writer no longer unions every profiled model into the primary roster, and the 11 Cursor, Gemini and GPT-5.6 ids moved into `cursor`, `gemini` and `openai` platform entries (`gpt-6-astra` stays under `codex`); the freshness check reads IN SYNC for the recorded Claude ids and for each platform, and `verify_model_prompting_profiles.py` reports OK. The `gemini` and `openai` keys are vendor labels because no record names the host those ids were listed from. Residual (user-deferred): whether the dated Haiku 4.5 id and its alias share one profile, tied to DF-11.

- **Source phase**: Phase 2. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T306 and T309.
- **Reason**: the `claude-code` roster in `profiles-index.json` was recorded on 2026-09-08 from `config` as a multi-vendor union (Claude, Cursor, Gemini, and GPT-5.6 ids). The 2026-09-30 write refreshed it from the live Models API, and by design the writer unions the live ids with every already-profiled model, so no profile was orphaned. The result is 26 ids labelled `roster_source: api`, of which 16 did not come from the API. `check_model_prompting_freshness.py --advisory` against the 13 live Claude ids therefore reports DRIFTED, listing the non-Claude ids and the `claude-haiku-4-5` alias as "no longer live". The check is advisory and blocks nothing.
- **Suggested next step**: move the Cursor, Gemini, and GPT-5.6 profiles onto their own `meta.platforms` entries (schema 1.1.0), as was done for `codex`, so the `claude-code` roster holds only Claude ids and its freshness check can read IN SYNC. Decide the `claude-haiku-4-5` alias at the same time (see DF-3).

- **Carried from**: v4.13.8#WN-3 on 2026-10-02

- **Migrated from**: v4.13#WN-23 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Whether the dated Haiku 4.5 id and its alias share one profile is a maintainer decision tied to DF-11.

#### DF-14 (v4.13.9): The first-principles pilot stopped at the smoke run because effort could not be confirmed

**Carry-forward contract (v4.13.11)**:
- **Owner**: not stated in source; maintainer to set
- **Severity**: low - the first-principles question is untested, not failed
- **Blocker**: vendor-feature - Claude Code 2.1.283 does not recognize claude-sonnet-5-5 or expose effort, so the approved paid matrix cannot run.
- **Acceptance**: A Claude Code release recognizes `claude-sonnet-5-5` and shows effort, and the identical approved matrix is re-run and decided by the rule in `## T319`
- **Proving command**: manual: confirm the run metadata shows the model and `--effort high`, then re-run the approved 15-run matrix under the USD 20 cap
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: Phase 5. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T321 to T324; record [`v4.13.8-first-principles-pilot.md`](../v4.13/development/v4.13.8-first-principles-pilot.md).
- **Reason**: the pre-registered rule in `## T319` stops the pilot when the run metadata cannot confirm `--effort high`. On the one smoke run (2026-09-30, baseline, prompt 1, passed, USD 0.0396), Claude Code 2.1.283 reported `claude-sonnet-5-5` as an unrecognized model, recorded `costBasis: "unknown"` and a fallback `maxOutputTokens` of 32000, and exposed no effort field and 0 thinking tokens. The other 14 cells were not run, and the first-principles question is untested: this is not evidence for or against the instruction.
- **Suggested next step**: once a Claude Code release recognizes `claude-sonnet-5-5` and its run metadata can show the effort in effect, re-run the identical approved matrix (same arms, prompts, model, effort, 15 runs, USD 20 cap) with `python wrapper.py run` after deleting the stale smoke result, and decide go or not shown at this power from the rule recorded in `## T319`. Any change to the matrix needs a new approval.

- **Carried from**: v4.13.8#DF-4 on 2026-10-02

- **Migrated from**: v4.13#DF-12 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: Claude Code 2.1.283 does not recognize claude-sonnet-5-5 or expose effort, so the approved paid matrix cannot run.

#### WN-19 (v4.13.9): Open Dependabot branches make the all-refs attribution check fail

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: medium - every pull request turns `ci-required` red while Dependabot branches exist
- **Blocker**: user-deferred - Scoping the all-refs attribution scan or allowing dependabot[bot] is a CI security policy decision for the maintainer.
- **Acceptance**: The maintainer decides the CI policy (close or merge Dependabot PRs under the owner identity, or scope the all-refs scan), with explicit approval for any check or workflow change
- **Proving command**: `python scripts/check_commit_attribution.py --all-refs`
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: Phase 6. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T330 and T334.
- **Reason**: `scripts/check_commit_attribution.py --all-refs` (fast and full profiles, `hygiene` group) scans every commit reachable from every ref against a closed author allowlist. On 2026-10-01 Dependabot opened PRs #402 to #404, and their branches carry `dependabot[bot]` commits (`3a940eede996`, `904486f2affb`, `16c5fc389a19`). Once those branches are fetched, the check reports `3 findings` and exits 1. None of the three commits is in this branch's history: `git merge-base --is-ancestor` is false for each, and every commit in `origin/develop..HEAD` is authored by the owner identity. The `validate` job checks out with `fetch-depth: 0`, so the hosted check sees the same refs: on PR #402 (run 36897160501) `validate` failed with `check_commit_attribution` reporting `3 findings` on Dependabot commits, which turned the required `ci-required` red. Every pull request is affected while those branches exist.
- **Mitigation applied 2026-10-01**: with the maintainer's approval, PRs #402 to #404 were closed and their branches deleted. After `git fetch --prune`, the check reads `2282 commits scanned; 0 findings` and the fast profile passes 17 of 17. The item stays open because the next scheduled Dependabot run will reintroduce such branches.
- **Suggested next step**: owner, the catalog maintainer, as a CI policy decision. Either close or merge the Dependabot PRs under the owner identity, or scope the all-refs scan to the branch under test plus the protected branches. Changing the check or the workflow is a CI security change that needs explicit approval.

- **Carried from**: v4.13.8#WN-6 on 2026-10-02

**Tracking alias retained**: `v4.13.9#WN-27`; the following complete historical source has the same current obligation and is not a separate future task.

##### Tracking source: v4.13.9#WN-27 (v4.13.9): The all-refs attribution scan fails on fetched Dependabot branches

**Evidence**: `python scripts/check_commit_attribution.py --all-refs`, run by the fast profile, uses `git log --all` and allows only approved identities, so the three `origin/dependabot/*` branches fetched into this repository on 2026-10-01 produce three `dependabot[bot]` author findings and fail the step. Commits still succeed, because the commit hook runs only the message and pending-identity checks. Merging a Dependabot pull request would put bot-authored commits into history and fail the scan permanently. **Owner**: catalog maintainer (attribution policy decision). **Suggested next step**: scope the all-refs scan to local branches, `origin/main`, `origin/develop`, and the current pull request head, and decide separately whether `dependabot[bot]` is an allowed author.

- **Carried from**: v4.13.7#WN-3 on 2026-10-02

- **Carried from**: v4.13.8#WN-14 on 2026-10-02

- **Migrated from**: v4.13#WN-26 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Scoping the all-refs attribution scan or allowing dependabot[bot] is a CI security policy decision for the maintainer.

#### WN-20 (v4.13.9): Definition of Done 7 asks for a reset's expiry; Codex serves a count and no expiry

**Carry-forward contract (v4.13.11)**:
- **Owner**: extensions owner
- **Severity**: low - the monitor shows the count and its README explains the missing date
- **Blocker**: user-credential - Needs a live Codex account with an available reset to capture whether the response carries an expiry.
- **Acceptance**: A live response with an available reset is captured; an expiry field is mapped into the reset row, or the Definition of Done is amended
- **Proving command**: manual: when a reset is available, run `Codex Usage: Save Raw Usage Response` and check the response for an expiry field
- **Future plan**: v4.14 known-gaps sweep

**Evidence**: the 2026-10-01 capture recorded in `v4.13.7-decisions.md` ("Usage-limit resets", item 1) shows `rate_limit_reset_credits` carrying only `available_count` and `applicable_available_count`, with no kind and no expiry, although the ChatGPT page shows "Full reset, expires Oct 29". The Codex monitor therefore shows "1 reset available" with no date; `extensions/codex-usage-monitor/README.md` says why. Definition of Done 7's fallback covers only the case where no reset field exists at all, so a count without an expiry is a partial result, not a pass. The Claude monitor's no-field branch is met (no reset row; its README explains). **Owner**: extensions owner. **Suggested next step**: when a reset is next available, run `Codex Usage: Save Raw Usage Response` and check for an expiry field; map it into the reset row if one appears, otherwise amend the Definition of Done to "shows it with its expiry when the vendor data carries one".

- **Carried from**: v4.13.7#WN-7 on 2026-10-02

- **Carried from**: v4.13.8#WN-18 on 2026-10-02

- **Migrated from**: v4.13#WN-31 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: Needs a live Codex account with an available reset to capture whether the response carries an expiry.

#### QG-2 (v4.13.9): The real-editor and live-limit checks are manual and pending

**Carry-forward contract (v4.13.11)**:
- **Owner**: maintainer
- **Severity**: low - every automated check passed against stubs, fixtures and throwaway homes
- **Blocker**: user-credential - Requires the maintainer's real editors, work Copilot account and live usage-limit crossings.
- **Acceptance**: Each check listed under "Human/manual testing suggestions" in the final-phase evidence is run on the maintainer's machine and recorded
- **Proving command**: manual: run each listed real-editor and live-limit check and record each result in this entry
- **Future plan**: v4.14 known-gaps sweep

**Evidence**: every automated check ran against stubs, fixtures, and throwaway homes. Not yet observed on the maintainer's machine: installing the VSIX into the real VS Code (and, if WN-6 is resolved that way, Cursor); the pinned work account's personal view and the organization pool percentage against the organization's AI usage page; the state file `~/.nexus-hub/state/usage-probe/copilot.json` written by the running monitor; the Codex reset row while a reset is available; and a live 99% crossing (with `NEXUS_HANDOFF_THRESHOLD=1`) on Codex, Cursor, and Copilot followed by pasting the prompt into a different platform. Claude Code's crossing was observed in Phase 7. **Owner**: maintainer. **Suggested next step**: run the checks listed under "Human/manual testing suggestions" in the final-phase evidence and record each result here.

- **Carried from**: v4.13.7#QG-1 on 2026-10-02

- **Carried from**: v4.13.8#QG-5 on 2026-10-02

- **Migrated from**: v4.13#QG-7 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: Requires the maintainer's real editors, work Copilot account and live usage-limit crossings.

#### WN-21 (v4.13.10): The missing-file notice is verified in Chromium only

**Carry-forward contract (v4.13.11)**:
- **Owner**: guide owner
- **Severity**: low - the notice is verified in Chromium; other browsers are unexercised
- **Blocker**: user-deferred - Safari file:// behavior needs a real macOS Safari, unavailable on this Windows host.
- **Acceptance**: Opening the guide from a folder without `training.html` in Firefox and Safari shows the notice, or the fallback notice is added
- **Proving command**: manual: open the guide from a folder without `training.html` in Firefox and Safari, click the Training tab and record whether the notice appears
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: Phase 7. **Plan reference**: [`v4.13.10-training-page-rebuild`](../v4.13/plans/v4.13.10-training-page-rebuild.md), T027.
- **Reason**: the guide detects a missing `training.html` under `file://` with a stylesheet probe (`media="not all"`, its `onload` and `onerror`). Tests run headless Chromium; Firefox and Safari treat `file://` loads differently and were not exercised.
- **Owner**: guide owner. **Suggested next step**: open the guide from a folder without `training.html` in Firefox and Safari and click the Training tab; if no notice appears, fall back to showing the notice on any `file://` load that does not navigate within a second.

**Original source identity**: `v4.13.10#WN-1`; stable ID `WN-1-v41310` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-1-v41310 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Safari file:// behavior needs a real macOS Safari, unavailable on this Windows host.

#### WN-22 (v4.13.10): The Nexus AI Studio trailer shows no screens of the app

**Carry-forward contract (v4.13.11)**:
- **Owner**: maintainer
- **Severity**: low - content decision; the trailer works as drawn scenes
- **Blocker**: user-deferred - Embedding real app screenshots in the trailer is a maintainer content decision.
- **Acceptance**: The maintainer decides whether to embed compressed app screenshots in place of the drawn icons
- **Proving command**: manual: the maintainer's decision is recorded in this entry
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: rework goal review (after R5). **Plan reference**: [`v4.13.10-training-page-rebuild`](../v4.13/plans/v4.13.10-training-page-rebuild.md), round 2 of the maintainer review.
- **Reason**: the trailer is six drawn scenes (icon, title, line) taken from the Nexus-AI README. The page is offline and self-contained, and no screenshots of the app are bundled, so it shows what the app does but not what it looks like.
- **Owner**: maintainer. **Suggested next step**: decide whether to embed a few compressed screenshots of the app (the byte ceiling now allows it) in place of the drawn icons.

**Original source identity**: `v4.13.10#WN-9`; stable ID `WN-9-v41310` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-9-v41310 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Embedding real app screenshots in the trailer is a maintainer content decision.

#### WN-23 (v4.13.10): The WebGL game's frame rate is unverified on a real GPU

**Carry-forward contract (v4.13.11)**:
- **Owner**: maintainer
- **Severity**: low - headless software-WebGL figures say nothing about a reader's machine; no stutter is observed
- **Blocker**: user-deferred - Frame rate must be measured on a real GPU laptop and phone; headless SwiftShader figures do not apply.
- **Acceptance**: The reward game is played on an integrated-graphics laptop and a phone and its frame rate recorded; particle count and mesh detail are lowered if it stutters
- **Proving command**: manual: play the reward game on an integrated-graphics laptop and on a phone and record the observed frame rate
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: revision 2 goal review. **Plan reference**: [`v4.13.10-training-page-rebuild`](../v4.13/plans/v4.13.10-training-page-rebuild.md), T067.
- **Reason**: the running game measured 19 frames per second in headless Chromium, which renders WebGL in software (SwiftShader). The figure says nothing about a reader's machine, and no real GPU was available to measure it. The IDE players measured 55 frames per second and the page 59 in the same session.
- **Owner**: maintainer. **Suggested next step**: play the reward game on a laptop with integrated graphics and on a phone; if it stutters, lower the particle count and the mesh detail on small canvases.

**Original source identity**: `v4.13.10#WN-11`; stable ID `WN-11-v41310` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-11-v41310 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Frame rate must be measured on a real GPU laptop and phone; headless SwiftShader figures do not apply.

#### WN-24 (v4.13.10): Minor visual nits left from the revision 2 review

**Carry-forward contract (v4.13.11)**:
- **Owner**: guide owner
- **Severity**: low - stated as small findings
- **Blocker**: user-deferred - WN-12-v41310 keeps five game-engine and IDE-player nits that need slow software-WebGL verification (WN-40).
- **Acceptance**: The spawn band, editor soft-wrap, highlight label, sticky Start button and HUD label timing are fixed and verified by the slow WebGL tests
- **Proving command**: `python -m pytest tests/guides/test_training_game_engine.py -q`
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: The outline rail empty-dot ring now uses `var(--ink-dim)`, measuring 6.20:1 light and 8.26:1 dark (was 3.20 and 4.65); `tests/guides/test_outline_rail_contrast.py` passes 4, red 2 before. Residual (user-deferred): the spawn band, editor soft-wrap, highlight label, sticky Start button and HUD label timing need game-engine or IDE-player changes verified by the slow WebGL tests (WN-40).

- **Source phase**: revision 2 goal review (P3 findings). **Plan reference**: [`v4.13.10-training-page-rebuild`](../v4.13/plans/v4.13.10-training-page-rebuild.md), R8 and R10.
- **Reason**: small findings were not fixed in this pass. Enemies spawn under the in-game level header for a moment. At 1280 px the rail shows dots only, with the current label on hover and low-contrast empty circles. The IDE editor soft-wraps long lines, which can leave a single word on a line. From the revision 3 review: an IDE highlight's label can cover a line of code above its box; on a phone's first view of the start screen the sticky Start button covers two ships' stat meters; mid-wormhole the HUD names the next level before the map label changes.
- **Owner**: guide owner. **Suggested next step**: start enemy spawns below the header band; raise the slim rail's empty-dot contrast; turn off soft wrap in the editor and let it scroll sideways like VS Code.

**Original source identity**: `v4.13.10#WN-12`; stable ID `WN-12-v41310` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#WN-12-v41310 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: WN-12-v41310 keeps five game-engine and IDE-player nits that need slow software-WebGL verification (WN-40).

#### QG-3 (v4.13.10): The learner check has not been run

**Carry-forward contract (v4.13.11)**:
- **Owner**: maintainer
- **Severity**: low - stated per decision 16 not to block the release
- **Blocker**: user-deferred - Two or three non-technical readers must test the page on desktop and phone; an agent cannot substitute.
- **Acceptance**: Two or three non-technical readers go through the page on desktop and phone and the results are recorded under `## Human testing suggestions` in the evidence file
- **Proving command**: manual: run the learner check script from the evidence file with two or three non-technical readers and record the results there
- **Future plan**: v4.14 known-gaps sweep

- **Source phase**: Phase 8 (8.8). **Plan reference**: [`v4.13.10-training-page-rebuild`](../v4.13/plans/v4.13.10-training-page-rebuild.md), decision 16.
- **Reason**: two or three non-technical readers must go through the page on a desktop and a phone; an agent cannot stand in for them. Per decision 16 this does not block the release.
- **Owner**: maintainer. **Suggested next step**: run it with the script in the evidence file under `## Human testing suggestions` and record the results there.

**Original source identity**: `v4.13.10#QG-2`; stable ID `QG-2-v41310` distinguishes this obligation from repeated IDs in other patch sections.

- **Migrated from**: v4.13#QG-2-v41310 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Two or three non-technical readers must test the page on desktop and phone; an agent cannot substitute.

#### WN-25 (v4.13.11): Ship-balance browser fixture takes 18-38 minutes on CI

**Carry-forward contract (v4.13.11)**:
- **Owner**: guide test maintainer
- **Severity**: low - stated: runtime cost
- **Blocker**: user-deferred - Bounding the ship-balance fixture needs same-runner CI profiling of an 18-38 minute software-WebGL run with equal balance output.
- **Acceptance**: a bounded representative fixture retains its balance guarantees and has measured lower single-runner runtime, or the full fixture remains explicitly deferred with profiling evidence.
- **Proving command**: manual: the selected ship-balance test with `pytest --durations=1` and retained before/after balance results on the same runner configuration.
- **Future plan**: v4.14 known-gaps sweep

**Source phase**: Maintainer's v4.13.10 CI profiling report on 2026-10-09. **Plan reference**: Phase 5 guide batch; retain PLAN if not bounded. **Severity**: low; runtime cost. **Owner**: guide test maintainer.

**Reason**: The maintainer reports 18-38 minutes for `tests/guides/tools/game_balance.py`, called by `test_training_game_engine.py`. Profiling is dominated by native `(program)` time. `front()` state reuse and a `fitPanel` signature guard produced identical balance output and no speed-up, and were reverted. This admission records supplied observations, not an independently repeated profiling receipt. **Suggested next step**: isolate software-WebGL rendering cost on one runner, preserve the real balance assertions, and qualify any change by equal balance output and measured runtime improvement. Do not restore pytest-xdist: concurrent software-WebGL workers on one runner starve each other. **Acceptance**: a bounded representative fixture retains its balance guarantees and has measured lower single-runner runtime, or the full fixture remains explicitly deferred with profiling evidence. **Proving command**: the selected ship-balance test with `pytest --durations=1` and retained before/after balance results on the same runner configuration.

- **Migrated from**: v4.13#WN-40 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: Bounding the ship-balance fixture needs same-runner CI profiling of an 18-38 minute software-WebGL run with equal balance output.

### AR-35: Antigravity legacy workflow retirement needs a dated vendor check

**Carry-forward contract (v4.13.11)**:
- **Owner**: Antigravity integration owner
- **Severity**: low - stated impact: none before the retirement date, and none after it for the skills surface
- **Blocker**: user-deferred - AR-77 Antigravity legacy workflow retirement applies only after the vendor's dated retirement; acting before it would remove a still-read surface.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Antigravity integration owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.12.0#DF-1`**: After2026-11-01 recheck the vendor retirement date, then remove legacy commands_to_slash workflow emission/config destinations and requalify the platform contract.

**Partial disposition**: Before that date retain dual Skill/workflow distribution so older builds keep their slash surface. AR36 can reference this dated owner without collapsing it into general readback.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.12#DF-1 (reason: vendor-feature); original `v4.12.0#DF-1`, section `v4.12.0`.

#### Original source: DF-1: Antigravity workflow surface retires on 2026-11-01

**Source phase**: v4.12.1 release, platform-contract verification (2026-09-16). **Plan reference**: /update release governance step 4. **Reason**: the vendor documents retirement of the legacy workflow format on 2026-11-01 in favour of the Agent Skills standard. Nexus-Hub already emits every command as BOTH a skill and a workflow (`scripts/lib/integrations/antigravity.py` calls `commands_to_skills` alongside `commands_to_slash`), and the vendor states skills take precedence where both exist, so the skill copy is already what Antigravity executes.

**Impact**: none before the retirement date, and none after it for the skills surface. No re-architecture is required for Antigravity to remain supported.

**Why not now**: dropping workflow emission before the date would remove the slash surface for anyone still on a pre-retirement build. Shipping both is the correct posture until the date passes.

**Owner**: Antigravity integration maintainer. **Status**: open, dated. **Suggested next step**: after 2026-11-01, remove the `commands_to_slash` workflow emission from the Antigravity integration, drop `commands_subdir`/`ide_commands_subdir` from its config, update the read-contract row, and re-run the platform-contract verification. Re-check the date against the vendor page before acting, in case retirement slips.
**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-77`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.12.0`, section `v4.12.0`, and original ID `DF-1`.

- **Migrated from**: v4.13#AR-77 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-77 Antigravity legacy workflow retirement applies only after the vendor's dated retirement; acting before it would remove a still-read surface.

### AR-34: The public contributor view needs rendered confirmation or GitHub Support disposition

**Carry-forward contract (v4.13.11)**:
- **Owner**: Repository owner
- **Severity**: low - a display discrepancy; API and Insights already passed
- **Blocker**: user-credential - AR-76 needs a fresh public contributor-view check and possibly a GitHub Support ticket from the owner.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Repository owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.12.0#QG-2`**: Recheck the public Code contributor surface and reconcile it with API/Insights/user screenshot evidence. If still incorrect, repository owner submits the prepared GitHub Support handoff for supported cache correction or explanation.

**Partial disposition**: API and Insights passed; public Code still showed five on September25. Stale cache is an inference. No ticket submitted and no additional history rewrite justified.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.12#QG-2 (reason: user-credential); original `v4.12.0#QG-2`, section `v4.12.0`.

#### Original source: QG-2: GitHub contributor-view confirmation pending

**Recheck, 2026-09-25**: A fresh unauthenticated Chromium render of the public Code page still shows `Contributors 5` and links to `bendourthe`, `cursoragent`, `benjamin-dourthe`, `claude`, and `dependabot[bot]`. The contributors API returns only `bendourthe` with 1,753 contributions, and current `main` and `develop` shortlogs contain only Ben Dourthe's author identity. A stale GitHub presentation cache is an inference, not a confirmed cause. The [Support handoff draft](../../../archives/v4/v4.12/development/contributor-sidebar-recheck-2026-09-24.md) remains ready; no ticket was submitted. QG-2 stays open.

**Recheck, 2026-09-24**: A fresh unauthenticated Chromium render still shows `Contributors 5` with the same five avatar labels, while both read-only contributor APIs return only `bendourthe`. The [dated recheck and Support handoff draft](../../../archives/v4/v4.12/development/contributor-sidebar-recheck-2026-09-24.md) retain browser version, counts, default-branch SHA and the exact acceptance boundary. QG-2 stays open; no new history rewrite is justified.

**Recheck, 2026-09-22**: The live contributors API now returns only `bendourthe` (1,753 contributions), and the statistics API also returns only `bendourthe` (1,394 non-merge commits). A fresh, unauthenticated Chromium rendering of the public [Code page](https://github.com/bendourthe/Nexus-Hub) still shows `Contributors 5`; its avatar labels identify `bendourthe`, `cursoragent`, `benjamin-dourthe`, `claude`, and `dependabot[bot]`. The rendered Code result fails the one-contributor criterion despite the API results. No new history rewrite is justified by this discrepancy.

**Source phase**: Phase 4. **Plan reference**: T021-T023. **Reason**: the owner approved publication, all 120 reviewed writable refs were updated, both protections were restored exactly, and all five required checks passed. The fresh public clone scans 1,687 commits with zero findings. At `20260914T232622Z`, the contributor API still returned `bendourthe` (1655), `dependabot[bot]` (8), while the Insights default-main graph data contained only `bendourthe` (1,345 non-merge commits). Subsequent user screenshot 1 confirms Insights with Period: All, main, excluding merge commits, showing only bendourthe with 1,345 commits. Screenshot 2 confirms the published ba468f5 tip and a Code sidebar labeled Contributors 5. The other account names cannot be established from the avatars alone. The live API recheck still lists bendourthe and dependabot[bot], while the statistics endpoint lists only bendourthe. The rendered Code result therefore fails the one-contributor criterion; Insights passes. This discrepancy is consistent with GitHub's documented refresh delay, but the Code result is not yet resolved.

**Owner**: Repository owner and publication operator. **Suggested next step**: contact GitHub Support with the publication receipts, earlier screenshots, and the fresh Code-sidebar result; request a supported contributor-cache correction or explanation. Insights is already confirmed by the user's screenshot. GitHub documents about 24 hours for contributor displays to refresh after history changes and recommends contacting Support if they remain incorrect after that window. See [GitHub's stale-contributor guidance](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-a-projects-contributors#contributor-data-is-stale-after-history-changes). No further history rewrite is warranted by the current evidence. Existing releases and assets are already verified unchanged. No public-view success or release completion is claimed.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-76`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.12.0`, section `v4.12.0`, and original ID `QG-2`.

- **Migrated from**: v4.13#AR-76 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: AR-76 needs a fresh public contributor-view check and possibly a GitHub Support ticket from the owner.

### AR-33: GitHub retained read-only PR references require an explicit scope disposition

**Carry-forward contract (v4.13.11)**:
- **Owner**: Repository owner
- **Severity**: low - a scope disposition of retained read-only refs; writable publication scope is already captured
- **Blocker**: user-deferred - AR-75 retained read-only PR refs need an owner decision or GitHub administrative action.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Repository owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.12.0#QG-1`**: Record the owner disposition of GitHub-retained read-only PR refs outside writable branch/tag publication. If complete purge is required, obtain GitHub supported administrative disposition rather than normal force pushes.

**Partial disposition**: Preserve captured writable/local proof scope and the212 read-only refs limitation. No promise that every old SHA or GitHub mirror disappears.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.12#QG-1 (reason: user-deferred); original `v4.12.0#QG-1`, section `v4.12.0`.

#### Original source: QG-1: GitHub retains read-only pull-request refs

**Source phase**: Phase 4 independent review. **Plan reference**: Goal, T020 and T023. **Reason**: 212 `refs/pull/*` exist on GitHub outside the 119 writable branches/tags. They cannot be replaced by a normal force-push; the local all-ref proof covers the captured 139 local refs, not every GitHub-retained ref.

**Owner**: Repository owner. **Suggested next step**: approve the explicit writable-ref publication scope only with this limitation understood; observe both default-branch contributor surfaces afterward. If purging every GitHub-held ref is required, obtain GitHub's supported administrative disposition separately. Do not promise old SHA disappearance or a clean GitHub mirror that fetches PR refs.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-75`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.12.0`, section `v4.12.0`, and original ID `QG-1`.

- **Migrated from**: v4.13#AR-75 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-75 retained read-only PR refs need an owner decision or GitHub administrative action.

### AR-32: Gemini and OpenCode eval configuration isolation remains unproved

**Carry-forward contract (v4.13.11)**:
- **Owner**: Eval-pipeline owner
- **Severity**: low - both branches stay fail-closed until isolation is proved
- **Blocker**: vendor-feature - AR-74 Gemini CLI and OpenCode document no flag that excludes all configuration, so all-configuration isolation cannot be proved.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Eval-pipeline owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.10#EV-1`**: Prove exclusion of Gemini CLI system,user,project,environment and command-line configuration for each eval baseline before enabling provider-backed execution.

**Partial disposition**: GEMINI_CLI_HOME and -e none affect subsets only. Keep current fail-closed behavior; no provider-backed run was made in the source recheck.

**Current residual from `v4.10#EV-2`**: Prove exclusion of OpenCode global,project,remote,managed settings,instructions and plugins before enabling provider-backed execution.

**Partial disposition**: --pure disables plugins; additive config directories/inline overrides do not remove merged layers. Keep current fail-closed behavior.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.10#EV-1 (reason: vendor-feature); original `v4.10#EV-1`, section `Open Items - found 2026-09-21 during v4.10.1 implementation`.

#### Original source: EV-1 - Gemini CLI has no documented all-configuration isolation flag

- **Source phase**: v4.10.1 Phase 2 (T005-T009).
- **What was observed**: the official CLI documents `-e none` for disabling extensions and `--model` for model selection, but separately documents system, user, project, environment, and command-line configuration layers. No flag in the checked official reference excludes them as a whole.
- **2026-09-25 source recheck**: the [current configuration reference](https://geminicli.com/docs/reference/configuration/) documents `GEMINI_CLI_HOME` for user-level configuration and storage, plus separate overrides for system settings paths. It still describes project settings and environment inputs as independent layers. A per-job home alone does not establish the all-configuration isolation needed for a comparable baseline; no provider-backed run was made in this recheck.
- **Current behavior**: provider-backed skill evals requested with `--cli gemini` fail closed before spawning the CLI. Their results are not represented as isolated or comparable.
- **Suggested next step**: establish a documented and tested per-run exclusion of every configuration source before enabling this branch; otherwise keep it fail-closed.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-74`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.10`, section `Open Items - found 2026-09-21 during v4.10.1 implementation`, and original ID `EV-1`.

- **Migrated from**: v4.10#EV-2 (reason: vendor-feature); original `v4.10#EV-2`, section `Open Items - found 2026-09-21 during v4.10.1 implementation`.

#### Original source: EV-2 - OpenCode has no documented all-configuration isolation flag

- **Source phase**: v4.10.1 Phase 2 (T005-T009).
- **What was observed**: the official CLI documents `--pure` as disabling external plugins and documents config path overrides, but no checked flag excludes all operator configuration, instructions, and saved settings.
- **2026-09-25 source recheck**: the [current configuration reference](https://dev.opencode.ai/docs/config/) says configuration files are merged, `OPENCODE_CONFIG_DIR` adds a searched directory after global and project directories, and managed settings override all user-controlled layers. A custom directory or inline override therefore does not prove that operator configuration was excluded; no provider-backed run was made in this recheck.
- **Current behavior**: provider-backed skill evals requested with `--cli opencode` fail closed before spawning the CLI. Their results are not represented as isolated or comparable.
- **Suggested next step**: establish a documented and tested per-run exclusion of global, project, remote, and managed settings before enabling this branch; otherwise keep it fail-closed.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-74`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.10`, section `Open Items - found 2026-09-21 during v4.10.1 implementation`, and original ID `EV-2`.

- **Migrated from**: v4.13#AR-74 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: AR-74 Gemini CLI and OpenCode document no flag that excludes all configuration, so all-configuration isolation cannot be proved.

### AR-31: Five historical CodeQL alerts and the required-context decision remain open

**Carry-forward contract (v4.13.11)**:
- **Owner**: Security and CI owner
- **Severity**: high - stated: high pending per-alert triage
- **Blocker**: user-credential - AR-73 still has hosted CodeQL alerts #223, #329, #330, #349 and #350 open on the 2026-10-09 read-back; each needs a fix or a maintainer dismissal through the maintainer's gh session, plus a maintainer decision on making CodeQL a required check.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Security and CI owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Security**: historical CodeQL alert disposition. **Severity**: high pending per-alert triage. **Partial closure**: hosted alert #242 is fixed (2026-09-13T03:53:12Z), with no dismissal; `_STAGING_MODE = 0o600` in current `_owned.py` and commit `5f4c76eb7` preserve owner-only staging. Alert #223 and alerts #349/#350/#329/#330 remain open on the fresh 2026-10-09 hosted read-back. SEC-1 alerts #278-285 are a different set and cannot discharge these five.

**Current residual from `v4.8#WN-K`**: Identify exact remaining historical alerts and fix or dismiss each with reasons plus a fresh scan receipt. Record whether CodeQL should be a required context and how stale-main base comparisons would be handled.

**Partial disposition**: The distributed mode defect is already repaired: commit5f4c76eb7, _owned.py _STAGING_MODE=0o600 and exclusive os.open, destination mode preservation, tests/integrations/test_owned_file_modes.py. Keep this partial closure as proof, not new installer work. Other alerts include validate_skills argparse-help false-positive shape and archived example tag/XSS findings; do not whole-close without exact receipts.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.8#WN-K (reason: user-deferred); original `v4.8#WN-K`, section `Open Items - found 2026-09-07 during the v4.8.0 adoption plan`.

#### Original source: WN-K - A high-severity CodeQL alert sits in DISTRIBUTED installer code, and the release-time CodeQL check is red against a stale base

- **Source**: found at the v4.8.0 release, on the `develop` to `main` pull request (#186).
- **What was observed**: `CodeQL` reported fail while both `Analyze` jobs succeeded and all five REQUIRED contexts passed. `CodeQL` is not a required context, so it did not block; the red is an artifact of comparing against a `main` that was 72 commits behind, which surfaces the whole accumulated line's alerts as new relative to that base. Every open high alert predates v4.8.0 and none was introduced by it, verified per-alert with `git blame`.
- **The one that matters**: `py/overly-permissive-file` at `scripts/lib/integrations/_owned.py:105`. `_atomic_replace_bytes` creates its temporary file with mode `0o666` before moving it into place, so between `os.open` and the rename the file is world-writable subject only to the caller's umask. This is DISTRIBUTED code: it ships in `scripts/` and runs on a user's machine during install. `0o600` (or `0o644` where readability matters) would close it with no behavioral cost, since the file is immediately renamed over the destination. Untouched by this release and therefore deliberately not changed inside a release flow.
- **The rest, for completeness**: `py/clear-text-logging-sensitive-data` at `scripts/validate_skills.py:1017` is an argparse help string from v1.2.0 whose wording mentions a secret scan, a false-positive-prone shape for that rule; two `py/bad-tag-filter` and two `js/xss-through-dom` alerts sit in `docs/archives/v3/v3.12/development/` worked examples, which are documentation and are not installed (`docs/` is outside the installer's copy roots).
- **Suggested next step**: fix the `_owned.py` mode in the next patch and re-run the scan, then triage the remaining four with `[[security-review]]` and either fix or dismiss each with a recorded reason. Separately, decide deliberately whether `CodeQL` should become a required context: today it can be red on a release pull request without blocking, which is either correct (it compares against a stale base and would wedge releases) or a gap (a real new vulnerability would also not block). That is a decision record, not a release-time edit.
- **Why it did not hold the release**: the required gate was fully green, the finding is pre-existing, and the one alert in distributed code is a file-mode hardening rather than an exploitable path in the install flow. Recorded rather than fixed, per the rule that a release-time finding becomes a known gap plus a follow-up patch.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-73`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.8`, section `Open Items - found 2026-09-07 during the v4.8.0 adoption plan`, and original ID `WN-K`.

- **Migrated from**: v4.13#AR-73 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: AR-73 still has hosted CodeQL alerts #223, #329, #330, #349 and #350 open on the 2026-10-09 read-back; each needs a fix or a maintainer dismissal through the maintainer's gh session, plus a maintainer decision on making CodeQL a required check.

### AR-30: Manual distribution read-path and prose false-positive exercises remain unperformed

**Carry-forward contract (v4.13.11)**:
- **Owner**: Installation and writing owners
- **Severity**: low - manual exercises of already-shipped surfaces; no defect is recorded
- **Blocker**: user-credential - AR-72 needs live non-Claude platforms and a person for MT-1 tests 1 and 3.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Installation and writing owners. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Clause ownership**: MT-1 tests 1 and 3 remain here (distribution read-back and judged prose false positives). Its test 2 is owned by AR-70 and test 4 by AR-71. AR-57 owns the overlapping agent/hook delivery proof; this entry adds the broader installed instruction read-path exercise. The complete MT-1 body below is retained as history, not a second count of AR-70/AR-71.

**Current residual from `v4.5.0#MT-1`**: Run MT-1 test 1: a throwaway installed instruction read-path exercise across three non-Claude platforms, retaining host observations. Run MT-1 test 3: a person judges prose false-positive behavior on their own writing. Tests 2 and 4 remain owned by AR-70 and AR-71, respectively.

**Partial disposition**: Keep one migration owner for this compound source to avoid duplicate provenance. Cross-link AR57 for live platform delivery, the Writing Discipline efficacy owner and the repository-isolation owner; each clause remains independently pending.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.5#MT-1 (reason: user-deferred); original `v4.5.0#MT-1`, section `v4.5.0 - anti-cliche-and-agent-security`.

#### Original source: MT-1 - The four human and manual tests have not been run

- **Source phase**: Phase 7 - final phase.
- **Plan reference**: Human and Manual Testing Suggestions, items 1 to 4.
- **Reason**: All four require a person: a throwaway install across three non-Claude platforms with a read-path check; a judged comparison of replies on two platforms; a hand-judged false-positive rate on the reader's own writing; an attempt to apply the shared-storage control to this repository's own agent surface. The installer was also not run live on this host by standing instruction, so item 1's distribution check rests on the installer smoke suites until a person runs it.
- **Suggested next step**: Run items 1 and 3 before `/update release` if time allows (they are quick); items 2 and 4 after the release, since they need the installed block and real infrastructure respectively. Record outcomes here; item 2 resolves `DF-1` and item 4 resolves `DF-2`.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-72`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.5.0`, section `v4.5.0 - anti-cliche-and-agent-security`, and original ID `MT-1`.

- **Migrated from**: v4.13#AR-72 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: AR-72 needs live non-Claude platforms and a person for MT-1 tests 1 and 3.

### AR-29: Repository agent isolation and transitive shared-service reachability remain unqualified

**Carry-forward contract (v4.13.11)**:
- **Owner**: Agent-isolation owner
- **Severity**: medium - the partial 2026-09-24 audit retained fail findings, including a shared-checkout isolation failure
- **Blocker**: user-deferred - AR-71 transitive reachability and shared-checkout isolation is a large design exercise beyond the bounded 2026-09-24 audit findings.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Agent-isolation owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.5.0#DF-2`**: Complete transitive reachability and shared-writable service enumeration for this repository agent environment. Address or explicitly disposition shared-checkout isolation failure and establish an out-of-process allowlist union with retained proof.

**Partial disposition**: Preserve the September24 partial real audit and its fail findings; do not falsely retain the title implication that no audit of any scope exists.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.5#DF-2 (reason: user-deferred); original `v4.5.0#DF-2`, section `v4.5.0 - anti-cliche-and-agent-security`.

#### Original source: DF-2 - No transitive-reachability or shared-writable-service enumeration has been performed on this repository's own agent surface

- **Source phase**: Phase 5 - Agent isolation; Phase 7 - final review.
- **Plan reference**: sub-task 7.3 prompt ("any egress reachability or shared-service enumeration this repository has not performed on its own agent surface") and Human and Manual Testing Suggestions item 4.
- **Reason**: The security comparison raised this as an open question about Nexus-Hub itself: any write-capable service reachable from more than one agent session (a package registry, an artifact store, a CI cache) is a channel until proven otherwise, and any allowlisted destination with its own reach is part of the agent's real reachability. The v4.5.0 plan shipped the controls as catalog guidance; it did not apply them to the agents that develop this repository (CI runners, the MCP servers under `extensions/`, the memory store). That application is a design exercise on real infrastructure, not a documentation task.
- **Suggested next step**: Run human test 4: take step 3 sub-steps 6 to 8 and step 5 sub-steps 5 to 7 of `agent-execution-isolation` and apply them to this repository's CI and local agent surface, producing the two named artifacts (the shared-writable-service enumeration and the transitive-reachability union). If the controls cannot be applied as written, they are too abstract and the skill should be revised.

**Bounded audit, 2026-09-24**: The [shared-writable-service inventory](../../../archives/v4/v4.5/development/isolation-audit/shared-writable-services.md) and [transitive-reachability assessment](../../../archives/v4/v4.5/development/isolation-audit/transitive-reachability.md) now name the observed local checkout, user cache, GitHub cache and artifact surfaces, direct GitHub API access, configured web-fetch egress, and CI runner limits. The local shared checkout fails the per-session isolation minimum, and no out-of-process egress allowlist was evidenced in the inspected configuration from which to prove a transitive union. DF-2 remains open; these records are findings and design inputs, not a security pass or an exhaustive host inventory.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-71`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.5.0`, section `v4.5.0 - anti-cliche-and-agent-security`, and original ID `DF-2`.

- **Migrated from**: v4.13#AR-71 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-71 transitive reachability and shared-checkout isolation is a large design exercise beyond the bounded 2026-09-24 audit findings.

### AR-28: Writing Discipline benefit has not been judged on real replies

**Carry-forward contract (v4.13.11)**:
- **Owner**: Writing Discipline owner
- **Severity**: low - efficacy measurement of an instruction clause; presence and parity are already enforced
- **Blocker**: user-deferred - AR-70 needs human judgment of replies on two platforms.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Writing Discipline owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.5.0#DF-1`**: Compare real replies across at least two platforms with human judgments of cleaner versus stiff/canned wording.

**Partial disposition**: Presence/parity and detector fixtures do not measure usefulness or human quality.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.5#DF-1 (reason: user-deferred); original `v4.5.0#DF-1`, section `v4.5.0 - anti-cliche-and-agent-security`.

#### Original source: DF-1 - Whether the always-on Writing Discipline clause improves replies is unverified by a person

- **Source phase**: Phase 1 - Writing Discipline rule; Phase 7 - final review.
- **Plan reference**: sub-task 1.5 (measured cost) and Human and Manual Testing Suggestions item 2.
- **Reason**: The cost is measured and justified on its own terms (163 words, roughly 215 tokens per turn per platform in use; ceilings raised by exactly the delta and recorded in `docs/policy/doc-budgets.md`). The benefit cannot be measured by a test: whether the self-check clause changes a live reply, and whether the change is an improvement or stiffness, is a judgment a person makes by asking a cliche-prone question on two platforms and reading the answers. Nobody has done that yet.
- **Suggested next step**: Run human test 2 after the release lands on at least two platforms; if the replies read as stiff rather than cleaner, shorten the prohibition list before touching the self-check clause, since the clause is the load-bearing part (see the decision record `docs/decisions/implemented/policy/2026-09-04-writing-discipline-binds-chat-replies.md`).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-70`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.5.0`, section `v4.5.0 - anti-cliche-and-agent-security`, and original ID `DF-1`.

- **Migrated from**: v4.13#AR-70 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-70 needs human judgment of replies on two platforms.

### AR-27: Native browser zoom and OS occlusion need real host qualification

**Carry-forward contract (v4.13.11)**:
- **Owner**: Guide and browser qualification owner
- **Severity**: low - effective-width reflow and hidden-state behavior already have automated proof
- **Blocker**: user-deferred - AR-69 native 200% zoom and OS occlusion need observation on a real host by a person.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Guide and browser qualification owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.4.6#MT-446-2`**: Verify native 200% browser zoom on a real host. Verify actual OS occlusion delivery and observed guide visibility behavior.

**Partial disposition**: Effective-width CSS reflow and an instrumented hidden-state test were explicitly narrower. Current hidden-animation fixes do not prove this host boundary.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.4#MT-446-2 (reason: user-deferred); original `v4.4.6#MT-446-2`, section `v4.4.6 - guide-learning-experience`.

#### Original source: MT-446-2 - Native 200% browser zoom and OS occlusion delivery are not proven by effective-width reflow or an instrumented hidden-state test

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: MT-446-2

**Gap and gate impact**: Native 200% browser zoom and OS occlusion delivery are not proven by effective-width reflow or an instrumented hidden-state test

**Owner**: Guide owner on the target browser/OS

**Next step**: Perform the environment exercise; retain browser, OS, observations, and any affected correction. Native/fallback fullscreen and reduced-motion handlers have automated proof.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-69`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.4.6`, section `v4.4.6 - guide-learning-experience`, and original ID `MT-446-2`.

- **Migrated from**: v4.13#AR-69 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-69 native 200% zoom and OS occlusion need observation on a real host by a person.

### AR-26: OpenClaw tool interception requires an independently scoped typed plugin

**Carry-forward contract (v4.13.11)**:
- **Owner**: OpenClaw integration owner
- **Severity**: low - the guardrail surface is explicitly reported NOT COVERED rather than claimed
- **Blocker**: vendor-feature - AR-68 typed OpenClaw interception needs a plugin surface the vendor does not expose; only lifecycle hooks are documented.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: OpenClaw integration owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.3.0#DF-4`**: Scope or explicitly decline a typed OpenClaw plugin for actual tool interception and responsive-write guard parity; retain NOT COVERED until proof exists.

**Partial disposition**: Lifecycle hooks and native skills do not gate tool calls. AR56 Gemini/Kimi upstream hook-path issues are different capabilities.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.3#DF-4 (reason: vendor-feature); original `v4.3.0#DF-4`, section `v4.3.0 - agentic-verification-discipline`.

#### Original source: DF-4 - OpenClaw tool interception requires a typed plugin

- **Source phase**: Phase 5 platform-contract verification
- **Plan reference**: `docs/archives/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T023
- **Evidence**: Current official OpenClaw documentation exposes native skills and lifecycle hooks, but those managed hooks do not intercept or gate tool calls. Tool gating requires a typed plugin.
- **Impact**: Nexus-Hub can deliver verified OpenClaw skills and document lifecycle-hook discovery, but it cannot claim responsive-write guard parity through the native hook surface.
- **Owner**: Platform integration maintainer.
- **Next step**: Scope and review a typed OpenClaw tool-interception plugin in a future platform plan; until then, keep the guardrail surface explicitly `NOT COVERED` and do not synthesize a shell-hook port.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-68`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.3.0`, section `v4.3.0 - agentic-verification-discipline`, and original ID `DF-4`.

- **Migrated from**: v4.13#AR-68 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: AR-68 typed OpenClaw interception needs a plugin surface the vendor does not expose; only lifecycle hooks are documented.

### AR-25: Technical and nontechnical comprehension and final visual review remain unverified

**Carry-forward contract (v4.13.11)**:
- **Owner**: Guide owner and representative readers
- **Severity**: low - human comprehension evidence for documentation; no product defect
- **Blocker**: user-deferred - AR-67 needs technical and nontechnical human readers and a final human visual review.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Guide owner and representative readers. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.4.6#MT-446-1`**: Obtain unassisted technical and nontechnical reader exercise results and final user visual review for D13/T026.

**Partial disposition**: Shares a human-training owner with v4.2 workshop but does not replace the five-person requirement with a two-person sample.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.4#MT-446-1 (reason: user-deferred); original `v4.4.6#MT-446-1`, section `v4.4.6 - guide-learning-experience`.

#### Original source: MT-446-1 - Technical and non-technical comprehension plus final user visual review are unverified; D13 and T026 remain open

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: MT-446-1

**Gap and gate impact**: Technical and non-technical comprehension plus final user visual review are unverified; D13 and T026 remain open

**Owner**: Guide owner and two readers

**Next step**: Complete the [unassisted exercise](../../../archives/v4/v4.4/development/guide-learning-experience/phase-7/manual-review.md), retain actual responses, and address unclear concepts before publication. Carries HT-4.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-67`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.4.6`, section `v4.4.6 - guide-learning-experience`, and original ID `MT-446-1`.

- **Migrated from**: v4.13#AR-67 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-67 needs technical and nontechnical human readers and a final human visual review.

### AR-24: The five-person Training workshop remains unperformed

**Carry-forward contract (v4.13.11)**:
- **Owner**: Guide owner and five participants
- **Severity**: low - cohort validation of training material; no product defect
- **Blocker**: user-deferred - AR-66 needs a five-person workshop cohort for the v4.2.2 and v4.2.3 origins.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Guide owner and five participants. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.2.2#DF-2`**: Run the eight-step Training walkthrough with a cohort of five and record stalls and comprehension results.

**Partial disposition**: Both source patch entries represent the same inherited workshop obligation; preserve both origins. Rendered QA, keyboard, contrast and reduced motion do not satisfy cohort evidence.

**Current residual from `v4.2.3#DF-2`**: Run the eight-step Training walkthrough with a cohort of five and record stalls and comprehension results.

**Partial disposition**: Both source patch entries represent the same inherited workshop obligation; preserve both origins. Rendered QA, keyboard, contrast and reduced motion do not satisfy cohort evidence.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.2#DF-2-v422 (reason: user-deferred); original `v4.2.2#DF-2`, section `v4.2.2 - guide-cinematic-rebuild`.

#### Original source: DF-2-v422 - The five-person workshop validation was not run

- **Source phase**: Phase 7 - Architecture refactor, known-gaps, CI/CD
- **Plan reference**: `docs/archives/v4/v4.2/plans/v4.2.2-guide-cinematic-rebuild.md` T027
- **Reason**: Inherited from v4.2.1 DF-1. No cohort of five participants exists to run a workshop against. Rendered QA, WCAG AA contrast, keyboard, and reduced-motion checks were all run and are recorded; the workshop specifically was not, and is not claimed.
- **Suggested next step**: When a cohort is available, run the eight-step Training walkthrough with five people and record where they stall. Until then this stays open rather than being marked satisfied by proxy evidence.

**Original source identity**: `v4.2.2#DF-2` in `v4.2.2 - guide-cinematic-rebuild`; normalized stable ID `DF-2-v422` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-66`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.2.2`, section `v4.2.2 - guide-cinematic-rebuild`, and original ID `DF-2`.

- **Migrated from**: v4.2#DF-2-v423 (reason: user-deferred); original `v4.2.3#DF-2`, section `v4.2.3 - guide-refinement`.

#### Original source: DF-2-v423 - The five-person workshop validation was not run

- **Source phase**: carried from v4.2.2 DF-2
- **Plan reference**: `docs/archives/v4/v4.2/plans/v4.2.3-guide-refinement.md` T031
- **Reason**: no cohort of five participants exists. Rendered QA, WCAG AA contrast, keyboard, and reduced-motion checks were all run and recorded; the workshop specifically was not, and is not claimed.
- **Suggested next step**: when a cohort is available, run the eight-step Training walkthrough with five people and record where they stall.

**Original source identity**: `v4.2.3#DF-2` in `v4.2.3 - guide-refinement`; normalized stable ID `DF-2-v423` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-66`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.2.3`, section `v4.2.3 - guide-refinement`, and original ID `DF-2`.

- **Migrated from**: v4.13#AR-66 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-66 needs a five-person workshop cohort for the v4.2.2 and v4.2.3 origins.

### AR-23: Optional scanner presets lack live none, some, and all-tool receipts

**Carry-forward contract (v4.13.11)**:
- **Owner**: Security-audit owner
- **Severity**: low - fixture tests cover the presets; only live binary execution is unrecorded
- **Blocker**: user-deferred - AR-65 all-tools leg needs a host provisioned with semgrep, gitleaks, osv-scanner, trivy, checkov and pip-audit together.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Security-audit owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.1.1#DF-1`**: On an already provisioned host execute security-audit with some, none and all applicable optional scanners, retaining UNAVAILABLE states and receipts. Cover Semgrep, gitleaks, OSV-Scanner, npm audit, pip-audit, Trivy and Checkov when applicable.

**Partial disposition**: Fixture tests are narrower than live binary execution. The source plan prohibits adding real scanner execution to repository CI.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.1#DF-1-v411 (reason: user-deferred); original `v4.1.1#DF-1`, section `v4.1.1`.

#### Original source: DF-1-v411 - Live optional scanners were not executed on the implementation host

- **Source phase**: Phase 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Plan reference**: `docs/archives/v4/v4.1/plans/v4.1.1-adoption-openworker-security-refinement.md` T025 / T032
- **Evidence**: Fixture-driven closure-gate tests pass without invoking Semgrep, gitleaks, OSV-Scanner, npm audit, pip-audit, Trivy, or Checkov. Phase 4 history records that those binaries were not present or not executed.
- **Reason deferred**: The plan forbids adding real scanner execution to Nexus-Hub CI. Host-local binaries are optional; missing tools must remain visible as `UNAVAILABLE`.
- **Next action**: On a machine that already has the optional tools, run the `security-audit` preset once with some, none, and all applicable scanners and keep the receipts.

**Original source identity**: `v4.1.1#DF-1` in `v4.1.1`; normalized stable ID `DF-1-v411` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-65`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.1.1`, section `v4.1.1`, and original ID `DF-1`.

- **Migrated from**: v4.13#AR-65 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-65 all-tools leg needs a host provisioned with semgrep, gitleaks, osv-scanner, trivy, checkov and pip-audit together.

### AR-22: Live prompting roster completeness and CLI model qualification remain unproved

**Carry-forward contract (v4.13.11)**:
- **Owner**: Prompting-profile owner
- **Severity**: low - profile and roster completeness is advisory; no install or runtime path depends on it
- **Blocker**: user-credential - AR-64 needs account-backed CLI and model enumeration to complete the canonical roster, the Codex picker entry and profiles.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: Prompting-profile owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v4.1.0#DF-1`**: Requalify prompting profiles against a complete then-current canonical model-ID roster, preserving platform/provider separation. Determine whether the old GPT-5.6 profile deficit is now fully closed by later profile publication and retain only current roster/profile mismatches.

**Partial disposition**: Group with v4.7 DF-2 and v4.9 MT-1, retaining distinct profile, CLI-picker and roster-completeness clauses. Later 16-model schema/profile qualification is not a complete account roster.

**Current residual from `v4.7.0#DF-2`**: Verify current Codex CLI/account picker availability and canonical identity of gpt-6-astra independently of the provider API catalog and profile presence.

**Partial disposition**: September24 picker still omitted it; API-profile correctness did not establish CLI availability. Group with model-roster owner without assuming the old account state remains current.

**Current residual from `v4.9#MT-1`**: Obtain a supported complete canonical-ID account roster and qualify current profiles with the deterministic writer before changing roster hashes or last_verified.

**Partial disposition**: Retain Haiku and GPT-5.6-family later profile publication closures (PR314/PR316) and 16/16 profile schema qualification. Account-backed Opus5.5 display-name picker visibility did not prove canonical ID or complete roster; helper models=[] stayed incomplete.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v4.1#DF-1-v410 (reason: user-credential); original `v4.1.0#DF-1`, section `v4.1.0`.

#### Original source: DF-1-v410 - Prompting profile layer does not match the live Codex roster

- **Source phase**: v4.1.0 release preparation
- **Evidence**: On 2026-08-31, `python scripts/check_model_prompting_freshness.py --advisory gpt-5.6-sol gpt-5.6-terra gpt-5.6-luna` reported `DRIFTED`: the three supplied live Codex model IDs are unprofiled and the four recorded Claude entries are absent from that host roster. The current v4.4 model map independently lists those three Codex IDs.
- **Reason deferred**: The advisory is intentionally not a release or CI gate, and a conformant refresh requires the separate calibrated `/tune-prompting` research and adversarial-verification workflow rather than a release-time hand edit.
- **Next action**: Run `/tune-prompting` in a separately scoped plan, calibrate on one live model before widening, and retain any unverified models as explicit gaps.

**Original source identity**: `v4.1.0#DF-1` in `v4.1.0`; normalized stable ID `DF-1-v410` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-64`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.1.0`, section `v4.1.0`, and original ID `DF-1`.

- **Migrated from**: v4.7#DF-2 (reason: user-credential); original `v4.7.0#DF-2`, section `v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)`.

#### Original source: DF-2 - The Codex CLI does not yet list `gpt-6-astra`, so the codex profile entry reads DRIFTED

- **Source phase**: Amendment Phase 3 - the first OpenAI prompting profile (T049).
- **Plan reference**: `v4.7.0-adoption-gpt-6-astra-prompting.md` sub-task 3.3.
- **Reason**: `enumerate-models.sh codex` (`codex debug models`) on 2026-09-05 returned six models (`codex-auto-review`, `gpt-5.2`, `gpt-5.3-codex`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.5`) and not `gpt-6-astra`, which the vendor's API catalog lists as generally available. The layer's invariant (the index never claims a model it has no roster entry for) widens the codex entry's roster to include the profiled model, so `check_model_prompting_freshness.py --platform codex <live ids>` reports DRIFTED with `gpt-6-astra` as "recorded but no longer live". The profile itself is correct for the API surface the vendor documents; the drift is between the CLI's picker and the API catalog.
- **Suggested next step**: Re-run `enumerate-models.sh codex` at the next release; when the CLI lists `gpt-6-astra`, re-stamp the codex entry through the writer and this item closes. If the CLI never lists it, re-home the profile under an API-platform id in a later schema decision.

**2026-09-24 recheck**: The installed Codex CLI picker still lists six models and omits `gpt-6-astra`; the [archived read-only result](../../../archives/v4/v4.7/development/model-map-followup/verification.md) keeps API availability separate from CLI availability. DF-2 remains open and no profile was re-stamped.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-64`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.7.0`, section `v4.7.0 - model-behavior-and-distribution-integrity (with the gpt-6-astra-prompting amendments folded in)`, and original ID `DF-2`.

- **Migrated from**: v4.9#MT-1 (reason: user-credential); original `v4.9#MT-1`, section `Follow-up Items - found 2026-09-08 during post-v4.8.0 follow-up`.

#### Original source: MT-1 - Incomplete prompting-profile coverage and roster freshness

- **Source**: the post-v4.8.0 `/tune-prompting` full roster sweep.
- **What was observed on 2026-09-08**: 12 of 16 rostered models were profiled. Four were not, each for a sourced reason rather than for lack of effort:
    - **`claude-haiku-4-5`**: Anthropic's model-specific guidance table lists dedicated prompting pages for Fable 5.1, Fable 5, Sonnet 5, Opus 5, and Opus 4.8 only. Haiku 4.5 is covered by the general best-practices reference, which is model-agnostic across current Claude models and therefore yields no model-SPECIFIC claim.
    - **`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`**: OpenAI's prompt-engineering guide documents `gpt-6-astra` (already profiled) and reasoning-versus-GPT guidance generally. It names no member of the 5.6 family, so there is nothing model-specific to record.
- **Why this is the correct outcome, not a shortfall**: the runbook is explicit that no primary source found means zero claims rather than a guess, because an unsourced claim in the layer is indistinguishable from a hallucinated one and every later phase treats recorded claims as verified input. All four are reported UNVERIFIED by `verify_model_prompting_profiles.py`, which treats that as tracked rather than as a gate failure.
- **Suggested next step**: re-check at the next `/tune-prompting` run. A vendor publishing a per-model page is the trigger; nothing else changes the answer. Do not fill these from the general guidance, which would silently convert model-agnostic advice into a model-specific claim.

**Source recheck, 2026-09-23**: The original observation above remains the record of the 2026-09-08 sweep, but its statement that OpenAI names no GPT-5.6 member is no longer current. [OpenAI's GPT-5.6 guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) now names Sol, Terra, and Luna and differentiates their workload and cost positioning; its prompting advice is framed for the GPT-5.6 family, not as distinct instructions for each member. [Anthropic's prompting reference](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) still has no dedicated Haiku 4.5 prompting page, although it names Haiku in a shared context-awareness subsection. No per-model profile was written or re-stamped in this source-only recheck. MT-1 remains open for a qualified `/tune-prompting` pass rather than treating family guidance or model-selection advice as a verified per-model prompting difference.

**Source recheck, 2026-09-25**: [Anthropic's advisor-tool reference](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool) contains an alternative Haiku 4.5 system prompt for predominantly coding or write-task executors using the optional `advisor` tool. Advisor calls forward the executor's full transcript to a separate server-side inference and are billed at the advisor model's rates; Anthropic also reports a browse-comprehension regression for the alternative block. This conditional tool configuration is not a generally applicable Haiku prompting profile and does not authorize transcript forwarding or extra spend in Nexus-Hub. [Anthropic's general prompting reference](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) still lists no dedicated Haiku prompting page, while [OpenAI's GPT-5.6 guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) names Sol, Terra, and Luna for model selection but frames its prompting advice at family scope. No profile or freshness stamp changed in this source-only pass; MT-1 remains open.

**Haiku calibration, 2026-09-25**: [Anthropic's Haiku 4.5 migration guide](https://platform.claude.com/docs/en/models/haiku-4-5/migration-guide) specifically recommends considering `thinking: {type: "enabled", budget_tokens: N}` for coding and reasoning tasks; its [extended-thinking reference](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) confirms that Haiku 4.5 supports this manual mode, while newer adaptive-mode guidance must not be copied to it. Independent source, currency, and actionability reviews found the recommendation usable as one conditional, model-specific profile claim after correcting the quoted API value. The installed Claude Code picker includes Haiku 4.5, but the enumeration helper returns only a picker sentinel, not a complete model-ID roster; the index's 2026-09-08 config roster cannot be re-stamped as live evidence. No profile or freshness marker was written. Capture the complete current Claude roster, run the deterministic one-model planner and writer, and verify the generated layer before closing the Haiku portion of MT-1; the three GPT-5.6 entries remain separate. The [archived calibration receipt](../../../archives/v4/v4.9/development/haiku-profile-calibration-2026-09-25/verification.md) preserves the bounded evidence.

**Claim-only qualification, 2026-09-25**: The deterministic writer now accepts a sourced claim for an already-rostered model without refreshing the roster date, provenance, or hash, and rejects unknown models and malformed roster refreshes. The qualified Haiku 4.5 claim was written through that path; the structural validator reports 13 of 16 profiled models and still dates the roster to 2026-09-08. This local qualification does not establish a complete live Claude roster, and the three GPT-5.6 entries remain unprofiled. At this local stage, MT-1 remained open for protected publication and those separate evidence gates. See the [bounded verification](../../../archives/v4/v4.9/development/haiku-profile-claim-only-2026-09-25/verification.md).

**Publication, 2026-09-25**: [PR #314](https://github.com/bendourthe/Nexus-Hub/pull/314) merged the claim-only writer and Haiku profile after 21 hosted checks passed with one intentional skip; [post-merge run 36137890656](https://github.com/bendourthe/Nexus-Hub/actions/runs/36137890656) passed smoke and provenance. The complete live Claude roster and the three GPT-5.6 profiles remain separate MT-1 gates.

**GPT-5.6 family qualification, 2026-09-25**: [OpenAI's current GPT-5.6 guide](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6) supports one family-scoped migration-effort comparison for Sol, Terra, and Luna; their official model pages confirm the available effort settings. Three independent refutation lenses per candidate qualified a claim that excludes prior effort `none` and promises no quality equivalence. The claim-only writer generated all three per-model mirrors with an explicit family-scope note, and the structural gate reports 16 of 16 models in the recorded roster profiled without changing its 2026-09-08 date. The focused set passed 123 tests after removing a shipped-seed test that incorrectly required the roster to remain incomplete; a fixture still covers the unprofiled path. Claude Code 2.1.282 still returns a picker sentinel, and its account-backed `/model` view exposes display names rather than a complete canonical ID roster. MT-1 remains open for complete live roster evidence and protected publication. See the [bounded verification](../../../archives/v4/v4.9/development/gpt56-family-profiles-2026-09-25/verification.md).

**GPT-5.6 publication, 2026-09-25**: [PR #316](https://github.com/bendourthe/Nexus-Hub/pull/316) merged the three family-scoped profiles at `65baca12`; its hosted required checks passed, and [post-merge run 36162158349](https://github.com/bendourthe/Nexus-Hub/actions/runs/36162158349) passed smoke and provenance at that merge commit. The recorded roster still dates to 2026-09-08, and neither the merged profiles nor the post-merge jobs prove a complete live Claude model-ID roster. MT-1 remains open only for that roster-freshness gate.

**Public-catalog recheck, 2026-09-27**: [Anthropic's September 24 release notes](https://platform.claude.com/docs/en/release-notes/overview) and [current models overview](https://platform.claude.com/docs/en/models/overview) name `claude-opus-5-5`, which is absent from the recorded 2026-09-08 config roster. This proves that the recorded roster is stale against the public Claude API catalog, not that this model is available in the user's Claude Code account. The local Claude Code enumeration helper still returns `{"source":"picker","models":[]}`; no complete canonical picker/API roster was available. The profile schema passes with 16 of 16 recorded models, but that result is not current-roster completeness. No profile, roster hash, or `last_verified` value changed. MT-1 remains open: obtain a complete live roster before adding a new model through the deterministic writer or refreshing the roster date.

**Account-picker recheck, 2026-09-27**: Installed Claude Code 2.1.282 opened the account-backed `/model` picker in the already trusted checkout, with Opus 5.5 selected on the Claude Team account; the picker also showed other model display names but offered no complete canonical model-ID enumeration. The session exited without selecting another model or sending an inference prompt. This establishes account picker availability of Opus 5.5, narrowing the public-catalog note above, but it does not establish the canonical ID or a complete live roster. No profile, roster hash, or `last_verified` value changed; MT-1 remains open for a supported complete-ID read path and deterministic profile qualification.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-64`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.9`, section `Follow-up Items - found 2026-09-08 during post-v4.8.0 follow-up`, and original ID `MT-1`.

- **Migrated from**: v4.13#AR-64 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: AR-64 needs account-backed CLI and model enumeration to complete the canonical roster, the Codex picker entry and profiles.

### AR-21: The four MCP scaffolders lack real generation and server-start receipts

**Carry-forward contract (v4.13.11)**:
- **Owner**: MCP scaffolder owner
- **Severity**: low - an unproved scaffolder start affects only users of the four mcp-builder scaffolders
- **Blocker**: user-deferred - AR-63 needs the scaffold, compile and stdio handshake legs on Linux and macOS; Linux can run in a local Docker container (Docker 29.2.1) but was not run in v4.13.11, and macOS needs a macOS host.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Owner**: MCP scaffolder owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v1.1#DF-007`**: Execute all four Bash/PowerShell FastMCP and TypeScript scaffolders on clean supported hosts. Check successful generation, compile/type-check and a real startup or stdio handshake against the generated server for both stacks.

**Partial disposition**: Static syntax, recursive delivery and unrelated installer smoke do not prove a scaffolded server starts.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v1.1#DF-007 (reason: user-deferred); original `v1.1#DF-007`, section `Open Items`.

#### Original source: DF-007 -- Phase 6 mcp-builder bundled scaffolders not exercised end-to-end

**Source phase**: Phase 6, sub-task 6.3 (cross-platform installer verification).
**Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../../archives/v1/v1.1/plans/adoption-skills.md) lines 445-451 (sub-task 6.3) and the cross-cutting constraint at lines 535-543.
**Reason**: Phase 6 added two new skills (`brand-styling` in specialized-domains, `mcp-builder` in ai-development) and four bundled scaffolding scripts under `mcp-builder/scripts/`: `init-mcp-fastmcp.sh`, `init-mcp-fastmcp.ps1`, `init-mcp-ts.sh`, `init-mcp-ts.ps1`. Static validation was performed and is clean: `bash -n` clean on both `.sh` files; ShellCheck (`--severity=warning`) clean on both; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on both `.ps1` files. The existing recursive-copy primitives (`safe_folder_copy` / `Safe-Folder-Copy`) auto-distribute the bundled subdirs without an installer edit (the same machinery validated in Phase 3 / WN-001). However, end-to-end execution of the four scaffolders against a real Python 3.10+ / Node 20+ host -- actually running `init-mcp-fastmcp.sh hello-server` to scaffold a working FastMCP server, then `mcp dev server.py` to confirm the inspector loads, and the equivalent for the TS path -- was NOT performed in this session. The work-environment constraint (Windows 11 + PowerShell + this conversation's tool surface) does not include a way to spin up Python venvs and full Node installs to verify a complete scaffold-and-launch cycle for both stacks.
**Resolution applied in Phase 6**: None -- intentionally deferred. The scaffolders are syntactically valid and follow the same shape as the validated Phase 4 `init-artifact.{sh,ps1}` precedent. The risk surface is "the scaffolded server actually starts under `mcp dev` / `npm run dev`", which is not catchable by static syntax validation.
**Suggested next step**: Add a CI matrix step (or a manual release-readiness smoke task before the v1.1.5 -> v1.2.0 bump) that, on a Linux runner with Python 3.10+ and Node 20+ installed, executes each of the four scaffolders against a clean fixture directory and verifies: (a) the scaffold step exits 0; (b) the resulting `server.py` (FastMCP) or `src/server.ts` (TS SDK) file exists with the expected shape; (c) `python -m py_compile server.py` (FastMCP) or `tsc --noEmit` (TS SDK) returns 0; (d) optionally, `mcp dev server.py` / `npm run dev` starts and responds to a stdio handshake from a test client. This gap rolls up into the cumulative DF-003 / DF-005 / DF-006 cross-OS verification queue scheduled for Phase 7's `/update-version` step.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-63`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v1.1`, section `Open Items`, and original ID `DF-007`.

- **Migrated from**: v4.13#AR-63 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-63 needs the scaffold, compile and stdio handshake legs on Linux and macOS; Linux can run in a local Docker container (Docker 29.2.1) but was not run in v4.13.11, and macOS needs a macOS host.

### AR-20: Exact installed helper delivery remains unproved across supported operating systems

**Carry-forward contract (v4.13.11)**:
- **Owner**: Installer-smoke test owner
- **Severity**: low - the exact helper expectation is qualified locally; only Linux and macOS installer receipts remain
- **Blocker**: user-deferred - AR-62 keeps the Linux and macOS workspace-installer receipts for v1.1 DF-006 and DF-008; the Linux leg can run in a local Docker container on this host (Docker 29.2.1) but was not run in v4.13.11, and the macOS leg needs a macOS host.
- **Acceptance**: Record an evidence-backed disposition for every current residual clause in this entry; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.
- **Proving command**: manual: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.
- **Future plan**: v4.14 follow-up plan that the named owner supplies or selects (per this entry's Future plan ownership field)

**Partial implementation, 2026-10-10 (v4.13.11 T013)**: EXPECTED_SCRIPTS now names package_skill.py, aggregate_benchmark.py, skill_eval_viewer.py, optimize_skill_description.py and generate_report.py, which both unchanged installers already distribute. Nine actual checker invocations against faithful disposable Windows copies include success and refusal for every missing helper. This closes the exact-expectation clause; actual Linux and macOS workspace-installer receipts for DF-006/DF-008 remain open. Evidence: [Phase 3 checkpoint](../v4.13/development/v4.13.11-phase-3-checkpoint.json).

**Owner**: Installer-smoke test owner. **Status**: open; PLAN except the explicitly admitted installed-helper delivery candidate.

**Future plan ownership**: The named owner must supply or select a v4.14 follow-up plan for clauses remaining after this sweep; the existing push-size-guard plan is not assigned unrelated work.

**Current residual from `v1.1#DF-006`**: Capture actual Linux and macOS workspace-installer receipts proving `aggregate_benchmark.py`, `skill_eval_viewer.py` and `optimize_skill_description.py` reach the installed scripts path, together with the retained source cumulative Phase 2, Phase 4 and Phase 5 delivery obligations. The exact `EXPECTED_SCRIPTS` additions are qualified locally by Phase 3 T013; faithful Windows copies do not prove real installer delivery.

**Partial disposition**: Existing generic recursive-copy and syntax tests do not by themselves prove these exact outputs. AR26 covers a different live macOS curl bootstrap boundary.

**Current residual from `v1.1#DF-008`**: Capture actual Linux and macOS workspace-installer receipts proving `package_skill.py` reaches the installed scripts path and covering the retained source cumulative Phase 2, Phase 4, Phase 5, Phase 6 and Phase 7 bundle/helper delivery obligations. The exact `EXPECTED_SCRIPTS` addition is qualified locally; real installer delivery remains open.

**Partial disposition**: Group with DF-006 without replacing its exact helper list. The package round-trip tests are narrower than installer delivery.

**Acceptance**: Record an evidence-backed disposition for every current residual clause above; retain unproved or account/host/human-bound clauses as PLAN. Complete original source obligations remain individually traceable below.

**Proving action**: Follow each original source's retained command or manual protocol and record its actual output, host and scope. If the required host/account/person is unavailable, do not mark this owner resolved.

- **Migrated from**: v1.1#DF-006 (reason: user-deferred); original `v1.1#DF-006`, section `Open Items`.

#### Original source: DF-006 -- Phase 5 cross-OS installer dry-run deferred (extends DF-003 / DF-005)

**Source phase**: Phase 5, sub-task 5.6 (cross-platform installer verification).
**Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../../archives/v1/v1.1/plans/adoption-skills.md) lines 387-392 (sub-task 5.6) and the cross-cutting constraint at lines 535-543.
**Reason**: Phase 5 added three repo-level Python scripts (`scripts/aggregate_benchmark.py`, `scripts/skill_eval_viewer.py`, `scripts/optimize_skill_description.py`) and registered all three in BOTH `scripts/installer.sh` and `scripts/installer.ps1` per the AGENTS.md "Installer-Aware Changes" rule. Verification on Windows + Git Bash was performed: `bash -n scripts/installer.sh` clean; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on `installer.ps1`; ShellCheck clean on `installer.sh` and `install.sh`; the three scripts compile clean (`python -m py_compile`); the new pytest module (`catalog/hooks/tests/test_eval_loop.py`) passes 14/14; the dry-run mode of `optimize_skill_description.py` is exercised under three pytest cases (schema, determinism under fixed seed, no-CLI-invocation under empty PATH). Real `bash scripts/installer.sh` execution into a throwaway directory on a real macOS or Linux host was not run.
**Resolution applied in Phase 5**: None - intentionally deferred per the same rationale as DF-003 / DF-005 (the work-environment constraint is Windows 11 + PowerShell). Both installers' `safe_copy` / `Safe-Copy` primitives are already exercised by every prior installer block in the same file, so the new copy lines exercise no new code path - they are textual additions that piggyback on already-validated machinery.
**Suggested next step**: Same as DF-003 / DF-005. The cumulative cross-OS smoke run for v1.1.5 (which now covers Phase 2 doc-coauthoring SKILL.md, Phase 4 four bundled skill folders + two scaffolder scripts, AND Phase 5 three eval-loop scripts) should happen before the v1.1.5 -> v1.2.0 version bump in Phase 7's `/update-version` step. CI matrix coverage (Linux + macOS GitHub Actions runners performing a real `bash scripts/installer.sh` workspace install) is the durable fix.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-62`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v1.1`, section `Open Items`, and original ID `DF-006`.

- **Migrated from**: v1.1#DF-008 (reason: user-deferred); original `v1.1#DF-008`, section `Open Items`.

#### Original source: DF-008 -- Phase 7 packager installer registration not exercised on macOS / Linux

**Source phase**: Phase 7, sub-task 7.1 (`scripts/package_skill.py` + installer registration) and 7.2 (cross-platform installer verification).
**Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../../archives/v1/v1.1/plans/adoption-skills.md) lines 487-501 (sub-tasks 7.1 and 7.2) and the cross-cutting constraint at lines 535-543.
**Reason**: Phase 7 added one new repo-level Python script (`scripts/package_skill.py`) and registered it in BOTH `scripts/installer.sh` (after the eval-loop dispatcher block) and `scripts/installer.ps1` (matching `Safe-Copy` block at the same logical position) per the AGENTS.md "Installer-Aware Changes" rule. Verification on Windows + Git Bash was performed: `python -m py_compile scripts/package_skill.py` clean; `bash -n scripts/installer.sh` clean; ShellCheck (`--severity=warning`) clean on `scripts/installer.sh` and `install.sh`; PowerShell parser (`[System.Management.Automation.Language.Parser]::ParseFile`) clean on `installer.ps1`; the new pytest module (`catalog/hooks/tests/test_package_skill.py`) passes 14/14; round-trip pack-and-extract works against a real Phase 5 skill bundle (`catalog/skills/workflow/skill-eval-loop/`, 8 files preserved at original relative paths). Real `bash scripts/installer.sh` execution into a throwaway directory on a real macOS or Linux host to confirm the new copy line lands `package_skill.py` at `~/.devai-hub/scripts/package_skill.py` was not run.
**Resolution applied in Phase 7**: None - intentionally deferred per the same rationale as DF-003 / DF-005 / DF-006 / DF-007 (the work-environment constraint is Windows 11 + PowerShell). The new copy line piggybacks on the same already-validated `safe_copy` / `Safe-Copy` primitives used for the four prior repo-level scripts in the same block (`generate_report.py`, `aggregate_benchmark.py`, `skill_eval_viewer.py`, `optimize_skill_description.py`). The packager itself is stdlib-only Python so the runtime risk surface is minimal once the file lands at the right path.
**Suggested next step**: Roll into the cumulative cross-OS smoke run scheduled for the v1.1.5 -> v1.2.0 bump in `/wrap-up-session` -> `/update-version`. The smoke task should now cover: Phase 2 (`doc-coauthoring` SKILL.md), Phase 4 (four bundled skill folders + two scaffolder scripts), Phase 5 (three eval-loop dispatcher scripts), Phase 6 (two skill folders + four bundled scaffolders), and Phase 7 (one packager script). CI matrix coverage (Linux + macOS GitHub Actions runners performing a real `bash scripts/installer.sh` workspace install) remains the durable fix.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-62`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v1.1`, section `Open Items`, and original ID `DF-008`.

- **Migrated from**: v4.13#AR-62 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-62 keeps the Linux and macOS workspace-installer receipts for v1.1 DF-006 and DF-008; the Linux leg can run in a local Docker container on this host (Docker 29.2.1) but was not run in v4.13.11, and the macOS leg needs a macOS host.

### AR-19: The official Claude plugin directory submission was never made

**Carry-forward contract (v4.13.11)**:
- **Owner**: maintainer (manual form)
- **Severity**: low - distribution listing only; no product defect
- **Blocker**: user-credential - AR-39 is a manual Claude plugin-directory form submission on the maintainer's Anthropic account; README still says if Anthropic later lists.
- **Acceptance**: The Claude plugin directory form is submitted and, after listing, the `@claude-plugins-official` install line is added to the README
- **Proving command**: manual: confirm the submission was made and the README carries the `@claude-plugins-official` install line in place of "If Anthropic later lists..."
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: README still says "If Anthropic later lists..."; the submission draft is `docs/archives/v3/v3.20/development/claude-marketplace-submission.md`.
- **Owner and next step**: maintainer (manual form); submit, then add the install line to the README.
- **Historical transfer note**: v3.20.3#DF-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.20#DF-2-v3203 (reason: user-deferred); original `v3.20.3#DF-2`, section `v3.20.3`.

#### Original source: DF-2-v3203 - Official Claude plugin directory listing not submitted - MIGRATED to v4.13 (AR-39)

- **Source phase**: Phase 5 - Official Claude plugin marketplace listing
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md` (sub-task 5.1)
- **Reason**: The phase prepares the package and the maintainer packet. Live Anthropic process (fetched 2026-08-24) is the [plugin directory submission form](https://clau.de/plugin-directory-submission), not a PR to `anthropics/claude-plugins-official`. Opening either from the implement loop is out of scope.
- **Suggested next step**: Maintainer submits the form using `docs/v3/v3.20/development/claude-marketplace-submission.md`. After listing, add the `@claude-plugins-official` install line to README.

**Original source identity**: `v3.20.3#DF-2` in `v3.20.3`; normalized stable ID `DF-2-v3203` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-39`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.20.3`, section `v3.20.3`, and original ID `DF-2`.

- **Migrated from**: v4.13#AR-39 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: AR-39 is a manual Claude plugin-directory form submission on the maintainer's Anthropic account; README still says if Anthropic later lists.

### AR-18: The Windows notification linger was never measured

**Carry-forward contract (v4.13.11)**:
- **Owner**: maintainer on a live Windows 10/11 desktop
- **Severity**: low - the 5500 ms default works; only a shorter safe value is unmeasured
- **Blocker**: user-deferred - AR-46 Windows toast linger needs a person watching a rendered notification to choose a value below the 5500 ms default.
- **Acceptance**: The shortest safe `NEXUS_NOTIFY_LINGER_MS` is measured on a live Windows desktop and set in `catalog/hooks/_notify_common.sh` and its `.ps1` sibling
- **Proving command**: manual: on a live Windows 10/11 desktop, watch rendered notifications at decreasing `NEXUS_NOTIFY_LINGER_MS` values and record the shortest safe value
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: the default is still 5500 ms in `catalog/hooks/_notify_common.sh` and its `.ps1` sibling.
- **Owner and next step**: maintainer on a live Windows 10/11 desktop; measure the shortest safe `NEXUS_NOTIFY_LINGER_MS`.
- **Historical transfer note**: v3.15.10#DF-16 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-16 (reason: user-deferred); original `v3.15.10#DF-16`, section `v3.15.10 - end-of-task-agent-behavior`.

#### Original source: DF-16 - Windows notification linger remains unmeasured

- **DF-16 - Windows notification linger not shortened.** The 5.5-second post-`ShowBalloonTip` sleep keeps a `powershell.exe` alive per notification. Disposing a `NotifyIcon` early can cancel a queued toast on Windows 10/11, and the shortest safe value requires observing a rendered toast on a live desktop, which no test here can do. Exposed as `NEXUS_NOTIFY_LINGER_MS` to be measured rather than guessed. - MIGRATED to v4.13 (AR-46)

**Normalization, 2026-10-09 (v4.13.11 T006)**: Converted the authoritative bullet to a supported gap heading. The complete original source paragraph is retained above. The residual belongs to AR-46; the canonical copy must be verified before a parsed forward-migration marker is added.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-46`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.10`, section `v3.15.10 - end-of-task-agent-behavior`, and original ID `DF-16`.

- **Migrated from**: v4.13#AR-46 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-46 Windows toast linger needs a person watching a rendered notification to choose a value below the 5500 ms default.

### AR-17: The Cursor usage-monitor live visual smoke was never run

**Carry-forward contract (v4.13.11)**:
- **Owner**: maintainer on a live Cursor host
- **Severity**: low - visual smoke of an extension UI; no functional defect is recorded
- **Blocker**: user-deferred - AR-44 needs a live Cursor host for the widened visual smoke; no Cursor session was available.
- **Acceptance**: The status bar, three bars and three themes are observed on a live Cursor host and the result is recorded in `cursor-usage-live-smoke.md`
- **Proving command**: manual: on a live Cursor host check the status bar, three bars and three themes and record the result in `cursor-usage-live-smoke.md`
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: `cursor-usage-live-smoke.md` has no recorded result.
- **Owner and next step**: maintainer on a live Cursor host; run status bar, three bars, and three themes and record the result.
- **Historical transfer note**: v3.15.9#QG-5 and v3.15.12#QG-4 (Cursor half) on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#QG-v31512-5 (reason: user-deferred); original `v3.15.12#QG-v31512-5`, section `v3.15.12 - cursor live transport and github billing monitor`.

#### Original source: QG-v31512-5 - Cursor on-demand bar extends the outstanding live visual smoke

| **QG-4 / QG-5 / MT-5** - MIGRATED to v4.13 (AR-44) | Maintainer-only interactive smokes. **Scope widened this version**: QG-4/QG-5 now also cover the Cursor on-demand bar (currency labels, shared-scope note, over-limit clamp, dropped-bar fallback), and MT-5 now also covers the renamed GitHub surfaces and the new Authorization panel section |

**Normalization, 2026-10-09 (v4.13.11 T006)**: The table adds a real Cursor residual: currency labels, the shared-scope note, the over-limit clamp, and the dropped-bar fallback. The original `v3.15.12#QG-4`, `v3.15.12#QG-5`, and `v3.15.12#MT-5` references and all GitHub clauses are retained in the source row above; this structural heading uses a distinct ID to preserve that widened source without colliding with v3.15.9 QG-5. GitHub-only renamed surfaces and Authorization-panel checks were superseded by withdrawal of that monitor in v3.18.2; the Cursor smoke remains open under AR-44 until its canonical copy preserves the widened scope.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-44`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.12`, section `v3.15.12 - cursor live transport and github billing monitor`, and original ID `QG-v31512-5`.

- **Migrated from**: v3.15#QG-5 (reason: user-deferred); original `v3.15.9#QG-5`, section `v3.15.9 - cross-provider-routing-and-cursor-usage-monitor`.

#### Original source: QG-5 - Cursor live visual smoke remains unobserved

**QG-5 (NEW, open at release): the Cursor live smoke was NOT executed for v3.15.9.** The checklist at `docs/v3/v3.15/development/cursor-usage-live-smoke.md` requires a human driving a real Cursor instance to confirm the status bar, meters, dashboard, threshold warning, and theme rendering; it cannot be performed by an automated agent and no local Cursor host ran it before the tag. The maintainer authorized the release to proceed without it (2026-08-04). What IS proven for the Cursor monitor is the automated surface: 132 extension tests green with coverage thresholds held, packaging verified in CI, and installer host isolation asserted by test. What is NOT proven is the rendered visual result on a live Cursor host. Close QG-5 by running the checklist post-release and recording the outcome here; treat any finding as a v3.15.10 fix candidate. This entry exists so the release record does not imply a verification that never happened. - MIGRATED to v4.13 (AR-44)

**Normalization, 2026-10-09 (v4.13.11 T006)**: Converted the authoritative prose record to a supported heading. Keep the full live-host checklist obligation open under AR-44 until its canonical source copy is verified.


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-44`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.9`, section `v3.15.9 - cross-provider-routing-and-cursor-usage-monitor`, and original ID `QG-5`.

- **Migrated from**: v4.13#AR-44 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-44 needs a live Cursor host for the widened visual smoke; no Cursor session was available.

### AR-16: Usage-monitor extension test coverage

**Carry-forward contract (v4.13.11)**:
- **Owner**: extensions owner
- **Severity**: low - origin entries state it is not a release blocker
- **Blocker**: user-deferred - AR-32 keeps the legacy-module coverage threshold, the extension-host modules that need a live VS Code host, and the original Codex icon artwork, none available locally.
- **Acceptance**: The legacy Claude monitor modules are tested to the 80 percent line and statement floor, the extension-host modules are checked through the installed-VSIX method, and the Codex icon is swapped or accepted
- **Proving command**: `npm --prefix extensions/claude-usage-monitor run test:coverage`
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: `extensions/claude-usage-monitor/test/recommendations.test.ts` adds 28 pure Vitest cases for the urgency and recommendation helpers (86 of 86 extension tests pass; four source mutants each fail the file). Residuals (user-deferred): the coverage threshold for the legacy modules, the modules that need a live VS Code extension host, and the original Codex icon artwork.

- **Current state**: Claude `recommendations.ts`, `warningView`, and `extension.ts` lack tests; `claude-usage-monitor` has no coverage threshold while the Codex and Cursor monitors do; no live render check of the theme icon; the Codex `icon.png` is still the reconstructed 512x512 asset.
- **Owner and next step**: extensions owner; add the tests and threshold, reuse the installed-VSIX method that closed v4.10 MT-2, and swap or accept the icon.
- **Historical transfer note**: v3.14.0#MT-1, v3.14.4#MT-1, v3.14.4#DF-1, v3.14.5#MT-1, and v3.17.0#MT-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.14#MT-1-v3145 (reason: user-deferred); original `v3.14.5#MT-1`, section `v3.14.5`.

#### Original source: MT-1-v3145 - Usage-monitor extensions' UI orchestration remains partially host-only - MIGRATED to v4.13 (AR-32)

- **Source phase**: v3.14.5 Phases 4-5 (carries the v3.14.4 MT-1)
- **Plan reference**: Phase 7.2
- **Reason**: Phases 4-5 ADDED Vitest coverage to both extensions - Codex 38 tests (the `wham/usage` window-alias mapper, the actionable empty-state banner, the status-bar priority constants + compact label) and Claude 5 (priority constants + compact label) - closing the largest prior gaps. What remains host-only (not unit-testable without a live VS Code extension host): the actual webview rendering (dashboard HTML, the theme-adaptive tab icon), the manual-entry input-box flow end to end, and the live status-bar left-to-right ordering. These are covered by the HO-1 manual smoke checklist below.
- **Suggested next step**: a `@vscode/test-electron` integration harness if UI-render regressions ever recur; today the unit tests plus the manual smoke checklist are proportionate.

**Original source identity**: `v3.14.5#MT-1` in `v3.14.5`; normalized stable ID `MT-1-v3145` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.5`, section `v3.14.5`, and original ID `MT-1`.

- **Migrated from**: v3.14#DF-1-v3144 (reason: user-deferred); original `v3.14.4#DF-1`, section `v3.14.4`.

#### Original source: DF-1-v3144 - Codex extension `icon.png` reconstructed from `codex-white.png`, not the user's `codex-2048x2048.png` - MIGRATED to v4.13 (AR-32)

- **Source phase**: v3.14.4 Phase 2
- **Plan reference**: Phase 2 sub-task 2.2 ("Save the two provided images")
- **Reason**: The user referenced two brand assets: `codex-white.png` (found in the user's Downloads, 640x640 white cloud silhouette with the `>_` knocked out) and `codex-2048x2048.png` (the full-color Marketplace icon). Only `codex-white.png` was on disk; `codex-2048x2048.png` could not be located anywhere on the machine, and no SVG rasterizer (ImageMagick / rsvg / cairosvg / inkscape) was available to synthesize one. `icon.png` (512x512) was therefore reconstructed with Pillow from `codex-white.png`'s exact silhouette: the cloud body filled with a periwinkle->`#5244BB` vertical gradient and the `>_` knockout painted black. The result is a faithful match to the described design, but it is a reconstruction rather than the user's original file.
- **Suggested next step**: If the user has the exact `codex-2048x2048.png`, drop it in as `extensions/codex-usage-monitor/icon.png` (a one-file swap; the manifest already points at `icon.png`, so no code change). By-design acceptable otherwise - the reconstructed icon is on-brand and functional.

**Original source identity**: `v3.14.4#DF-1` in `v3.14.4`; normalized stable ID `DF-1-v3144` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.4`, section `v3.14.4`, and original ID `DF-1`.

- **Migrated from**: v3.14#MT-1-v3144 (reason: user-deferred); original `v3.14.4#MT-1`, section `v3.14.4`.

#### Original source: MT-1-v3144 - Claude extension UI orchestration remains unit-test-light - MIGRATED to v4.13 (AR-32)

- **Source phase**: v3.14.4 Phase 1
- **Plan reference**: Phase 1 sub-task 1.4 (Testing and Stabilization)
- **Reason**: Removing the Codex provider dropped the Vitest suite from 35 tests to 3; the survivors cover `describeProviderError` and provider identity. The UI orchestration files (`statusBarManager`, `dashboardPanel`, `settingsPanel`, `warningView`, `extension`) and the `recommendations` engine have no direct unit tests. This is a pre-existing gap for a VS Code extension whose bulk is webview/status-bar UI (hard to unit-test without a VS Code host), not a regression introduced by the de-Codex work - the removed tests exercised Codex code that moves to the new extension in Phase 2.
- **Suggested next step**: In Phase 2, port the recommendations/mapping-style tests to the new Codex extension and consider adding pure-function unit tests for the shared `recommendations.ts` Claude branches (they are host-independent). Not a release blocker.

**Original source identity**: `v3.14.4#MT-1` in `v3.14.4`; normalized stable ID `MT-1-v3144` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.4`, section `v3.14.4`, and original ID `MT-1`.

- **Migrated from**: v3.14#MT-1-v3140 (reason: user-deferred); original `v3.14.0#MT-1`, section `v3.14.0`.

#### Original source: MT-1-v3140 - Extension UI modules have no automated tests - MIGRATED to v4.13 (AR-32)

- **Source phase**: Phase 1 (1.4)
- **Plan reference**: Phase 1 stability gate scoped automated tests to "provider unit tests"
- **Reason**: `statusBarManager.ts`, `dashboardPanel.ts`, `warningView.ts`, `settingsPanel.ts`, and `extension.ts` render VS Code UI and require the extension host, so they are validated by `tsc` compile and manual run only. The provider data layer, the Codex payload mapper, the error resolver, the provider factory, and the Codex recommendation branches ARE unit-tested (35 Vitest tests). This matches the pre-existing state (the extension had no tests before this phase).
- **Suggested next step**: Add a VS Code integration test harness (`@vscode/test-electron`) if the UI surface grows, or extract more pure logic behind the vscode boundary; not warranted for the current thin UI branches.

**Original source identity**: `v3.14.0#MT-1` in `v3.14.0`; normalized stable ID `MT-1-v3140` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.14.0`, section `v3.14.0`, and original ID `MT-1`.

- **Migrated from**: v3.17#MT-1-v3170 (reason: user-deferred); original `v3.17.0#MT-1`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: MT-1-v3170 - OPEN (pre-existing coverage debt): Claude Usage Monitor lacks an extension-wide coverage baseline - MIGRATED to v4.13 (AR-32)

- **Target file**: `extensions/claude-usage-monitor/src/`, `extensions/claude-usage-monitor/vitest.config.ts`
- **Source phase**: v3.17.0 Phase 5, sub-tasks 5.2 and 5.4
- **Plan reference**: 5.4 requires extension coverage of at least 80 percent.
- **Reason it is open**: the new autonomy state machine reaches 91.66 percent line coverage and is enforced at that explicit feature boundary, but enabling coverage over every imported Claude monitor module measured only 14.07 percent lines because the pre-existing provider, store, recommendation, type, and status-bar modules have little or no test coverage. Expanding those legacy tests is unrelated to the autonomy surface and would materially widen Phase 5.
- **Suggested next step**: add tests for the legacy Claude monitor modules in risk order, then remove the `coverage.include` feature boundary once the whole extension clears the same 80 percent line and statement floor that the Codex monitor already meets.

**Original source identity**: `v3.17.0#MT-1` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `MT-1-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-32`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `MT-1`.

- **Migrated from**: v4.13#AR-32 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-32 keeps the legacy-module coverage threshold, the extension-host modules that need a live VS Code host, and the original Codex icon artwork, none available locally.

### AR-15: Presentify verification residuals

**Carry-forward contract (v4.13.11)**:
- **Owner**: presentify owner
- **Severity**: low - origin entries state the residuals are non-blocking and degrade cleanly
- **Blocker**: user-deferred - AR-19 keeps live Wikimedia and Pexels source paths (Pexels needs an API key), GPU Tier-3 generation, agent-vision grading and the unimplemented composition probes; headless rendering works on this host, so only the v3.13 sample visual QA clause is locally runnable and it was not run in v4.13.11.
- **Acceptance**: The sample-deck scorer smoke runs in the render job, and each remaining checker (live fetch smoke, agent-vision grading, Gates A, B and E, composition probes) is accepted or built
- **Proving command**: `python -m pytest tests/skills/test_presentify_content_intent_and_accent.py -q`
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: `visual_qa_score.py` adds `content-intent` and `standalone-phrasing` findings and a `contrast-runtime-accent` check for `data-*accent*` values, with fixture tests in `tests/skills/test_presentify_content_intent_and_accent.py` (red before); the render job's sample smoke still exits 0. Residual (user-deferred): WN-1, MT-2, v4.9 MT-3, agent-vision grading and NI-3.

- **Current state**: no rendered QA of the v3.13 samples is recorded; no live or scheduled media-fetch smoke; a sample-deck scorer smoke in the render job is unconfirmed; the scorer cannot see runtime-injected palettes; Gates A, B, and E and the composition probes have no checker or helper.
- **Owner and next step**: presentify owner; add the smoke to the render job and accept or build each checker.
- **Historical transfer note**: v3.13#WN-1, v3.13#MT-2, v3.15.4#MT-3, v3.16.5#WN-2, v3.16.7#NI-2, and v3.16.7#NI-3 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

**Current residual from `v4.9.0#MT-3`**: Resolve real-deck fragment budgets: slides2/6 declare9/16 versus maximum8. Implement or verify a runtime structural inspection path for the three legacy static-stage checks currently UNCHECKED. Establish a verified reading-figure-to-slide model mapping and prove actual re-layout plus tick/legend fidelity. Qualify uncovered SVG marks, arrowheads and animation frames separately from settled connector/chart-line pixel proof.

**Partial disposition**: Retain the pinned 15-slide,73-fragment,four-viewport,352-state follow-ups, the stage-relative floor correction, flow-order and chart-line partial closures. Bounded settled probes do not constitute full deck qualification.

- **Migrated from**: v3.13#WN-1 (reason: user-deferred); original `v3.13.0#WN-1`, section `v3.13.0`.

#### Original source: WN-1 - Full-repo validators and browser visual-QA unavailable on the Windows dev host - MIGRATED to v4.13 (AR-19)

- **Source phase**: Phases 1-5
- **Reason**: `validate_unicode_safety.py` / `validate_no_personal_paths.py` (full-repo scans) and the compression eval time out on the dev host, and no headless browser is installed, so the rendered visual-QA loop (screenshots) and the per-aspect / hero-vs-gallery rendered demonstrations could not run locally. Change-relevant validators were run directly (bundle audit, JSON integrity, version-sync, ASCII, ruff); edited files are ASCII-verified. The imagery-and-interactivity Phase 1 Tier-1 sample (`development/worked-example/tier1-imagery-sample.html`) was likewise reviewed statically (offline-refs grep clean, tag-balance and ASCII checked), not browser-rendered.
- **Suggested next step**: Rely on CI for the full validator chain; run the rendered visual-QA of the Tier-1 sample and the universal-ingestion worked example in a browser-capable session.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `WN-1`.

- **Migrated from**: v3.13#MT-2 (reason: user-deferred); original `v3.13.0#MT-2`, section `v3.13.0`.

#### Original source: MT-2 - Live Tier-2 fetch paths and Tier-3 generation not exercised in CI (residual) - MIGRATED to v4.13 (AR-19)

- **Source phase**: Phase 2 (2.1-2.3), Phase 3 (3.1-3.2), Phase 5 (5.3)
- **Status**: the committed automated verifier is DELIVERED - `docs/v3/v3.13/development/fixtures/verify_imagery.py` (34 offline checks: license filter incl. nc/nd rejection, CC-BY attribution builder, `accept_candidate`, the credits-manifest / asset shape via a stubbed download, the consent-default-offline invariant via a stubbed transport, and the Tier-3 model-license registry / `parse_size` / degrade / no-network-import invariants), wired into `presentify-extractor.yml`. It runs on a plain ubuntu runner with no extra dependency, network, or GPU.
- **Residual gap**: only the LIVE network / GPU paths remain un-CI'd - the Wikimedia and Pexels source paths were not live-exercised (Openverse was, returning verified CC-BY assets; Pexels needs a key), and the Tier-3 diffusers generation path needs a local GPU runtime + weights absent from the dev host and CI.
- **Suggested next step**: Optionally gate a live Openverse smoke test behind a manual / scheduled CI job; keep the Tier-3 GPU generation a documented manual step on a GPU-capable host. Neither blocks release (both degrade cleanly and the pure-function logic is CI-covered).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.13.0`, section `v3.13.0`, and original ID `MT-2`.

- **Migrated from**: v4.9#MT-3 (reason: user-deferred); original `v4.9.0#MT-3`, section `v4.9.0 - adoption-visa-vulnerability-agentic-harness`.

#### Original source: MT-3 - Pre-rule handbook does not exercise the slide-specific checks

- **Source phase**: v4.9.2 Task 6, real-artifact proof.
- **Plan reference**: [v4.9.2 Task 6 Step 1](../../../archives/v4/v4.9/plans/v4.9.2-slide-build-contract-and-projection-floors.md#7-task-6-prove-it-on-a-real-artifact).
- **Reason**: the previously missing real-artifact run is now recorded in the [2026-09-27 verification](../../../archives/v4/v4.9/development/real-deck-score-2026-09-27/verification.md). The historical `lvedp-algorithm.html` blob fails `presentation-declared` at high severity and reports `slide-mode: n/a`, so none of the three structural slide checks runs on that artifact. The rendered stage-type floor was not measured on that artifact. The existing compliant two-slide fixture passes the structural report, and the stage floor has separate fixture controls; those are narrower than real-deck coverage.
- **Status**: open coverage gap, not an implementation failure attributed to the scorer.
- **Suggested next step**: use a preserved real deck that exposes actual `.slide-stage` sections, or define and verify a separate runtime-deck inspection path, then run the structural scorer and rendered stage-floor probe with artifact hashes. Merely adding a slide declaration to the historical deck does not supply stages. Keep the original undeclared-deck failure as separate evidence; do not claim that a clean synthetic fixture proves a real deck passes.

**Fail-closed follow-up, 2026-09-27**: An in-memory copy of the same historical blob added only `data-nav="slides"` to `<body>`. It still contains zero static `.slide-stage` sections; before this repair, `slide-fragments`, `slide-type-variety`, and `slide-figure-scaled` each reported `pass` without inspecting a slide. Those three checks now report `unchecked`, while `slide-structure` remains a high-severity failure and `page_pass` remains false. A clean two-slide control still reports `pass` for all three checks. The [archived verification](../../../archives/v4/v4.9/development/empty-slide-stage-coverage-2026-09-27/verification.md) retains both deck hashes and the red/green result. MT-3 remains open for real-deck structural and rendered coverage.

**Runtime render follow-up, 2026-09-27**: Chromium opened the unchanged historical blob, reached all 15 `.dkslide` articles, and measured visible text nodes at four viewports. The 2%-of-viewport stage floor failed on slides 4 and 6 at 1366x768 and on all slides at 390x844; slide 4 also exceeded four rendered sizes. The [archived runtime evidence](../../../archives/v4/v4.9/development/runtime-deck-render-2026-09-27/verification.md) records the hash, method, counts, and limits. This is one settled state per slide, not a runtime structural scorer or full build-state qualification. MT-3 remains open; the three legacy static-stage checks remain `unchecked` on this deck.

**Stage-floor correction, 2026-09-27**: The preceding viewport-relative floor verdict was wrong for the deck's scaled 900-unit stage. Fresh browser stage measurements and the preserved text-node minima show that all four sampled viewport states pass the correct 2%-of-rendered-stage floor. An in-memory undersized-text control fails that comparison. The [append-only correction](../../../archives/v4/v4.9/development/runtime-deck-stage-floor-correction-2026-09-27/verification.md) preserves the original report and its error; slide 4's excessive size variety and MT-3's missing build-state and structural coverage remain open.

**Build-state probe, 2026-09-27**: A [read-only Chromium probe](../../../archives/v4/v4.9/development/runtime-deck-build-state-2026-09-27/verification.md) reached all 15 slides at desktop and mobile sizes and sampled declared fragment completions. Slides 2 and 6 declare 9 and 16 distinct fragments, exceeding the eight-fragment contract; a zero-index in-memory control is rejected. The probe does not establish semantic build order, all-state rendered typography, or figure re-layout, and the legacy static-stage checks remain `unchecked`. MT-3 stays open; this is a real-artifact finding and bounded coverage, not full qualification.

**Four-viewport follow-up, 2026-09-27**: The same pinned blob and [probe](../../../archives/v4/v4.9/development/runtime-deck-four-viewport-build-state-2026-09-27/verification.md) were exercised at 1366x768, 1024x768, 768x1024, and 390x844. All 15 slides and 73 declared fragment completions were reached at each size, for 292 sampled completions. Slides 2 and 6 remain over the eight-fragment budget; every sample has one active slide, no network request occurs, and the zero-index control is rejected. MT-3 remains open because semantic order, SVG stroke visibility, all-state typography, and figure re-layout were not qualified.

**All-state text and SVG-box follow-up, 2026-09-27**: A separate [runtime probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/verification.md) used ArrowRight navigation on the same pinned blob at four viewports. Three runs each sampled 352 initial-or-fragment states; 8,527-8,584 text-node instances passed the corrected 2%-of-rendered-stage floor and 456-461 visible outer SVG-box instances stayed inside the viewport. Counts vary with timed animation sampling; font-size and figure-shift negative controls both failed as intended in every run. A first dot-click run that reported 61 mobile SVG-box failures was rejected after proving that Playwright had scrolled the deck overlay horizontally. MT-3 remains open for semantic order, internal SVG rendering, true figure re-layout, and the static-stage checks, which are still `unchecked` on this deck.

**Semantic flow-order follow-up, 2026-09-27**: A [pinned Chromium probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/semantic-order-verification.md) matched the source and target node of all 13 connectors across the three authored flow slides at four viewports. All 14 nodes followed the written content-order manifests, each connector arrived with its target after its source, all settled elements revealed, and early-arrow and detached-endpoint mutations were rejected at every size. This qualifies those flow diagrams only, not every deck build. MT-3 remains open for the known fragment-budget failures on slides 2 and 6, internal SVG stroke visibility, figure re-layout, and the three static-stage checks that remain `unchecked`.

**Chart-layout boundary, 2026-09-27**: A [pinned browser probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/figure-layout-verification.md) inspected 14 model-backed slide charts at four viewports. Each used authored 21-unit chart text and had no extra SVG scale beyond the stage; an in-memory half-scale mutation was rejected every time. The pinned reading page has zero `figure.fig[id]` chart instances and no verified mapping from its separately authored `.drawn` SVGs to the slide models, so this does not prove source-to-slide re-layout, tick or legend fidelity, or internal paint. MT-3 remains open alongside the fragment-budget failures and `unchecked` static checks.

**Flow-connector paint boundary, 2026-09-27**: A [pinned rendered-pixel probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/flow-paint-verification.md) checked all 13 connector bodies on the three authored flow slides at four viewports. All 52 connector-view observations changed 19-70 midpoint-window pixels when hidden; 12 fully invisible controls changed zero pixels, with no external requests or page errors. This qualifies settled connector-body paint only, not every SVG path, chart stroke, arrowhead, animation frame, or reading-figure-to-slide re-layout. MT-3 remains open for those boundaries, the known fragment-budget failures, and three `unchecked` static checks.

**Chart-line paint boundary, 2026-09-27**: A [pinned rendered-pixel probe](../../../archives/v4/v4.9/development/runtime-deck-all-state-2026-09-27/chart-line-paint-verification.md) checked all 31 `path.c-line` elements across 14 model-backed charts at four viewports. All 124 line-viewport observations changed pixels when hidden, all 124 invisible-line controls changed zero pixels, and a forced null stroke was rejected at every viewport. Other SVG marks and animation frames are not covered. MT-3 remains open for those boundaries, the fragment-budget failures, the absent reading-figure map, and the three static checks still `unchecked` on this deck.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.9.0`, section `v4.9.0 - adoption-visa-vulnerability-agentic-harness`, and original ID `MT-3`.

- **Migrated from**: v3.15#MT-3-v3154 (reason: user-deferred); original `v3.15.4#MT-3`, section `v3.15.4 - presentify-visual-fidelity`.

#### Original source: MT-3-v3154 - the visual-QA loop's agent-vision grading, fan-out, and end-to-end sample-deck smoke are behavioral (the structural scorer is the unit-tested backbone) - MIGRATED to v4.13 (AR-19)

- **Source phase**: v3.15.4 Phase 5.5.
- **Plan reference**: Phase 5.5 ("a test that the workflow template degrades ... an end-to-end smoke test on the sample board deck fixture asserting the loop reaches the pass bar").
- **Reason**: the deterministic STRUCTURAL scorer (`scripts/visual_qa_score.py`) is fully unit-tested (per-criterion defect flagging, clean pass, CLI exit codes). The AGENT-VISION grading (crop, dead space, annotation placement vs source, imagery relevance, contrast), the Dynamic-Workflow fan-out, and the full render -> grade -> fix -> re-render loop are LLM-native + runtime + browser behavior, not deterministically unit-testable; the workflow template is an adapt-me artifact asserted structurally (it carries the three mandatory rules), not executed. There is no committed "sample board deck" fixture, and the loop is agent-driven, so the e2e smoke is a browser-gated / release-time verification (the Phase 7 exit checklist verifies the four observed defects on the sample deck), not a CI unit test.
- **Suggested next step**: when a headless-browser CI job is added (gated to merges/schedule, per the plan), wire an e2e smoke that runs the scorer against a built sample-deck fixture; the agent-vision grading stays a behavioral (non-unit) check. Non-blocking.

**Original source identity**: `v3.15.4#MT-3` in `v3.15.4 - presentify-visual-fidelity`; normalized stable ID `MT-3-v3154` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.4`, section `v3.15.4 - presentify-visual-fidelity`, and original ID `MT-3`.

- **Migrated from**: v3.16#WN-2-v3165 (reason: user-deferred); original `v3.16.5#WN-2`, section `v3.16.5 - presentify-visual-overhaul`.

#### Original source: WN-2-v3165 - OPEN: the scorer cannot see runtime-injected palette values - MIGRATED to v4.13 (AR-19)

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/visual_qa_score.py` (`check_contrast`)
- **Source phase**: v3.16.5 Phase 2 (the checker gap behind BG-1)
- **Reason it is open**: `check_contrast` grades declared CSS custom properties. A page that assigns `--accent` from a `data-*` attribute in script, or paints canvas text with a literal, can pass the check and still render sub-AA text - which is exactly what BG-1 was. Statically resolving what a script assigns at runtime is not a job for a markup heuristic.
- **Suggested next step**: Phase 3 closes this by construction rather than by more parsing. A real screenshot shows the rendered color, so the AGENT-VISION half of rubric criterion 7 grades what the page actually paints. Do NOT attempt to interpret the script statically. A cheap partial guard is possible if it proves useful: collect hex literals from `data-accent`-style attributes and grade them alongside the declared tokens.

**Original source identity**: `v3.16.5#WN-2` in `v3.16.5 - presentify-visual-overhaul`; normalized stable ID `WN-2-v3165` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.5`, section `v3.16.5 - presentify-visual-overhaul`, and original ID `WN-2`.

- **Migrated from**: v3.16#NI-2-v3167 (reason: user-deferred); original `v3.16.7#NI-2`, section `v3.16.7 - presentify-first-shot-hardening`.

#### Original source: NI-2-v3167 - OPEN: Gates A, B, and E are agent behavior with no deterministic checker - MIGRATED to v4.13 (AR-19)

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/references/visual-qa-rubric.md`, `references/content-intent.md`
- **Source phase**: v3.16.7 Phase 3 (sub-tasks 3.1, 3.3, 3.6)
- **Reason it is open**: `scripts/visual_qa_score.py` can check a `content_intent` block's PRESENCE and shape, but not whether a `scope_class` is the right one, whether an assumption was genuinely accepted, or whether a visual explains its section. Those are judgments, and the same reasoning the maintainer applied to rubric criterion 10 in v3.16.5 applies here: a crude deterministic proxy produces false positives and trains the agent to satisfy the proxy. Enforcement is therefore record plus rubric, exactly as criterion 10 is.
- **Suggested next step**: consider a NARROW structural check for the mechanically-decidable half only, namely the `content_intent` block's presence and field completeness, and the `standalone` banned-phrase scan (a literal string search over visible text, which is decidable). Leave the judgments to the rubric. Do not attempt to score decision coverage.

**Original source identity**: `v3.16.7#NI-2` in `v3.16.7 - presentify-first-shot-hardening`; normalized stable ID `NI-2-v3167` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.7`, section `v3.16.7 - presentify-first-shot-hardening`, and original ID `NI-2`.

- **Migrated from**: v3.16#NI-3-v3167 (reason: user-deferred); original `v3.16.7#NI-3`, section `v3.16.7 - presentify-first-shot-hardening`.

#### Original source: NI-3-v3167 - OPEN: the composition probes are specified but not implemented in a helper - MIGRATED to v4.13 (AR-19)

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md` Step 9
- **Source phase**: v3.16.7 Phase 3 (sub-task 3.5)
- **Reason it is open**: line count, width utilization, one-word orphan detection, rectangle intersection, and per-section density deltas are specified as `page.evaluate()` probes the grading agent writes inline, matching how the existing probes (root size, per-role smallest size, band fraction, `scrollWidth`, painted-canvas) are already specified. No bundled script computes them. That is consistent rather than a shortfall, and the `AGENTS.md` scope-fit gate declines a helper with no call site, but it does mean the probes are as reliable as the agent that writes them each run.
- **Suggested next step**: if a future session finds the probes being skipped or written inconsistently, extract all of them (existing and new) into one bundled `scripts/render_probes.js` the loop injects verbatim. Do that as ONE extraction covering the whole probe set, not a second partial layer.

**Original source identity**: `v3.16.7#NI-3` in `v3.16.7 - presentify-first-shot-hardening`; normalized stable ID `NI-3-v3167` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-19`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16.7`, section `v3.16.7 - presentify-first-shot-hardening`, and original ID `NI-3`.

- **Migrated from**: v4.13#AR-19 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-19 keeps live Wikimedia and Pexels source paths (Pexels needs an API key), GPU Tier-3 generation, agent-vision grading and the unimplemented composition probes; headless rendering works on this host, so only the v3.13 sample visual QA clause is locally runnable and it was not run in v4.13.11.

### AR-14: No repository-wide Ruff baseline

**Carry-forward contract (v4.13.11)**:
- **Owner**: CI owner
- **Severity**: low - pre-existing tooling debt; the reported graph/affected.py findings are fixed
- **Blocker**: user-deferred - AR-34 measures 214 Ruff findings in scripts/lib/integrations and 1619 repo-wide on 2026-10-10, needing a dedicated baseline-and-batches lint cycle.
- **Acceptance**: A repository-wide Ruff baseline is set, the small findings are fixed in reviewable batches, and new findings are gated
- **Proving command**: `python -m ruff check scripts/lib/integrations`
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T011)**: The inherited `v3.15.1#WN-2` clause is fixed by removing only the unused EdgeKind import and frontier assignment. Ruff F401/F841 passes; affected graph, CLI and server tests pass and a tiny actual CLI graph returns exactly tests/test_utils.py. AR-34 remains open for its broader repository-wide baseline and unrelated findings. Evidence: [Phase 3 checkpoint](../v4.13/development/v4.13.11-phase-3-checkpoint.json).

- **Current state**: The two reported F401/F841 findings in graph/affected.py are fixed. Repository-wide baseline, unrelated findings in scripts/lib/integrations/ and broader Ruff gating remain open.
- **Owner and next step**: CI owner; set a baseline, fix the small findings, and gate new ones.
- **Historical transfer note**: v3.15.1#WN-2, v3.15.10 (Ruff advisory), and v3.17.0#WN-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.17#WN-2 (reason: user-deferred); original `v3.17.0#WN-2`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: WN-2 - OPEN (pre-existing tooling debt): integration framework has no clean repository-wide Ruff baseline - MIGRATED to v4.13 (AR-34)

- **Target file**: `scripts/lib/integrations/`
- **Source phase**: v3.17.0 Phase 2, sub-task 2.4 (lint verification)
- **Reason it is open**: an exploratory `python -m ruff check scripts/lib/integrations tests/integrations/test_autonomy_descriptors.py` reported 180 existing modernization, import-order, mutable-class-config, and unused-code findings across the integration framework. The Phase 2 test file passes focused Ruff validation, and Phase 2 did not suppress or introduce a new lint rule; cleaning the framework would be an unrelated broad refactor.
- **Suggested next step**: establish a deliberate Ruff baseline or scoped rule set in a dedicated lint-maintenance cycle, then reduce the existing findings in reviewable batches rather than mixing them into a release architecture phase.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-34`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `WN-2`.

- **Migrated from**: v3.15#WN-2 (reason: user-deferred); original `v3.15.1#WN-2`, section `v3.15.1 - adoption-codesight`.

#### Original source: WN-2 - Pre-existing ruff findings in graph/affected.py - MIGRATED to v4.13 (AR-34)

- **Source phase**: v3.15.1 adoption-codesight Phase 4 (4.1)
- **Reason**: ruff flags an unused `EdgeKind` import (F401) and an unused `frontier` local (F841) in `graph/affected.py`. Both are PRE-EXISTING; Phase 4 only ADDED `most_imported_files` (ruff-clean). The extension `src/` is not ruff-gated in this repo's CI. Left untouched per the no-out-of-scope-cleanup rule.
- **Suggested next step**: remove both in a dedicated extension lint pass.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-34`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.1`, section `v3.15.1 - adoption-codesight`, and original ID `WN-2`.

- **Migrated from**: v4.13#AR-34 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-34 measures 214 Ruff findings in scripts/lib/integrations and 1619 repo-wide on 2026-10-10, needing a dedicated baseline-and-batches lint cycle.

### AR-13: Subprocess-driven validator tests have no coverage measurement

**Carry-forward contract (v4.13.11)**:
- **Owner**: CI/test infrastructure owner
- **Severity**: low - stated non-blocking; behavioral coverage is strong
- **Blocker**: user-deferred - AR-33 has no subprocess coverage plumbing; adding it with a measured threshold for tests/validators is CI infrastructure deferred to its own version.
- **Acceptance**: Subprocess coverage plumbing (`COVERAGE_PROCESS_START`) is added once for `tests/validators` in `conftest.py` and CI, with a measured threshold
- **Proving command**: `grep -rn COVERAGE_PROCESS_START tests/validators/conftest.py .github/workflows`
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: no coverage configuration or `COVERAGE_PROCESS_START` anywhere.
- **Owner and next step**: CI/test infrastructure owner; add subprocess coverage plumbing and a threshold.
- **Historical transfer note**: v3.15.5#MT-2 and v3.17.6#MT-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.17#MT-2-v3176 (reason: user-deferred); original `v3.17.6#MT-2`, section `v3.17.6 - ci-gate-and-branch-hygiene`.

#### Original source: MT-2-v3176 - DEFERRED to its own version (2026-08-21): the repository has no coverage instrumentation - MIGRATED to v4.13 (AR-33)

- **Target files**: `tests/validators/conftest.py`
- **What it is**: every validator test invokes its script as a subprocess, deliberately, so the test exercises the CLI a maintainer runs. `coverage` therefore records nothing without `--parallel-mode` plus a `COVERAGE_PROCESS_START` shim, and the repository defines no threshold, `[tool.coverage]` section, or `--cov` flag anywhere.
- **How the gate was satisfied**: 90% on `check_required_check_coverage.py`, measured with a one-off out-of-tree in-process probe replaying the suite's own fixtures. The probe is scratch tooling and deliberately NOT committed, since committing it would create a second, divergent way to exercise the same code.
- **Suggested next step**: if a future version wants an enforced number, the change belongs in `conftest.py` and CI once, for all validators, not per phase.

**Original source identity**: `v3.17.6#MT-2` in `v3.17.6 - ci-gate-and-branch-hygiene`; normalized stable ID `MT-2-v3176` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-33`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.6`, section `v3.17.6 - ci-gate-and-branch-hygiene`, and original ID `MT-2`.

- **Migrated from**: v3.15#MT-2-v3155 (reason: user-deferred); original `v3.15.5#MT-2`, section `v3.15.5 - model-prompting-research`.

#### Original source: MT-2-v3155 - subprocess-invoked validator tests need explicit coverage plumbing, so coverage is not measured in CI - MIGRATED to v4.13 (AR-33)

- **Source phase**: v3.15.5 Phase 1.5.
- **Plan reference**: Phase 1.5 (stabilization) and the implement-phase coverage gate.
- **Reason**: `tests/validators/conftest.py` runs each validator as a SUBPROCESS (deliberately, so the tests exercise the real CLI surface end users run), so a plain `pytest --cov` collects nothing from the scripts under test. Coverage for this phase was measured out-of-band with `COVERAGE_PROCESS_START` plus `coverage combine` (94% validator, 97% freshness checker, 97% combined, branch coverage on), but CI does not run coverage for `tests/validators` at all, so the number is enforced nowhere. This affects the entire pre-existing `tests/validators` suite, not only the two new scripts.
- **Suggested next step**: if coverage enforcement is wanted for this suite, add the `COVERAGE_PROCESS_START` plumbing to the CI `tests` job once, for the whole `tests/validators` tree. Non-blocking; behavioral coverage is strong, since every documented structural rule has a dedicated failing-case test.

**Original source identity**: `v3.15.5#MT-2` in `v3.15.5 - model-prompting-research`; normalized stable ID `MT-2-v3155` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-33`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.5`, section `v3.15.5 - model-prompting-research`, and original ID `MT-2`.

- **Migrated from**: v4.13#AR-33 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-33 has no subprocess coverage plumbing; adding it with a measured threshold for tests/validators is CI infrastructure deferred to its own version.

### AR-12: Retired slash-command names remain in skill bodies

**Carry-forward contract (v4.13.11)**:
- **Owner**: catalog maintainer
- **Severity**: low - stated Low in origin DF-v32cmd-1 (prose-only staleness; menu noise resolved, hard breakages fixed)
- **Blocker**: user-deferred - AR-28 still has about 134 retired slash-command mentions across about 25 skills (90 found for a 10-name sample), a multi-hour context-sensitive sweep.
- **Acceptance**: No catalog skill body or style guide names a removed slash command; each old `/name` maps to its consolidated form
- **Proving command**: `grep -rn "/generate-plan\|/refactor-project\|/analyze-spec\|/run-penetration-test" catalog`
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: 134 mentions such as `/generate-plan` and `/tasks-to-issues`.
- **Owner and next step**: catalog maintainer; one modernization sweep.
- **Historical transfer note**: v3.2#DF-v32cmd-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.2#DF-v32cmd-1 (reason: user-deferred); original `v3.2#DF-v32cmd-1`, section `Open Items`.

#### Original source: DF-v32cmd-1 - MIGRATED to v4.13 (AR-28)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v32cmd-1 - MIGRATED to v4.13 (AR-28)

**Category**: DF

**Source phase**: v3.2.0 deprecated-command removal

**Plan reference**: shim cull (post-Phase-7)

**Reason**: After deleting the 40 deprecated command shims, the hard breakages were all fixed (the installer smoke test, every dangling `catalog/commands/<old>.md` file/link reference, the installer/base.py/new-feature old-command MENTIONS, and the `using-nexus-hub` onboarding command table). A residual remains: ~134 old-command slash *mentions* in ~25 catalog skill bodies + style-guides still name removed commands (e.g. `implementation-plan`, `known-gaps-tracker`, `project-refactor`, `spec-driven-development`, `cross-artifact-analyzer`, `tasks-to-issues`, `project-constitution`, `pr-description-writer`, `deep-research-compilation`, `idea-refine`, `business-logic-abuse`, `advanced-attack-patterns`, `test-strategy-doc`, `cross-project-comparison`, `docx-generation`, `mcp-builder`, `docs-layout-refactor`, plus the `commands-cheatsheet` / `markdown` style-guides and the `tasks-to-issues` helper scripts -- naming `/generate-plan`, `/refactor-project`, `/analyze-spec`, `/run-penetration-test`, etc.). These are stale prose, not broken commands: no test, slash menu, or file link is affected (all fixed), and many sit in the retained skills the consolidated commands delegate to. The slash-menu noise that motivated the removal is fully resolved.

**Suggested next step**: Run a dedicated command-reference modernization sweep mapping each old `/name` to its consolidated form per `docs/v3/v3.0/command-migration.md`, handling retained-skill self-references and step-number pointers with care; ship as a non-breaking v3.2.1 patch or a develop commit.

**Severity**: Low (prose-only staleness; menu noise resolved, hard breakages fixed)


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-28`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.2`, section `Open Items`, and original ID `DF-v32cmd-1`.

- **Migrated from**: v4.13#AR-28 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-28 still has about 134 retired slash-command mentions across about 25 skills (90 found for a 10-name sample), a multi-hour context-sensitive sweep.

### AR-11: v3.11 spec-kit items S5, S6, and S8 carry no status claim

**Carry-forward contract (v4.13.11)**:
- **Owner**: not stated in source; maintainer to set
- **Severity**: low - S5, S6 and S8 already carry recorded per-item verdicts; only the upstream re-check remains
- **Blocker**: user-deferred - AR-15 upstream delta verification needs a fresh repository comparison against github/spec-kit, which this offline audit cannot perform.
- **Acceptance**: A repository-delta comparison against `github/spec-kit` re-verifies S5, S6 and S8 and records a verdict per item
- **Proving command**: manual: the next spec-kit repository-delta comparison report records an explicit verdict for S5, S6 and S8
- **Future plan**: next spec-kit repository-delta comparison pass

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: Per-item verdicts are recorded in the archived v3.11.0 spec-kit comparison: S5 delivered (`label-gated-agent-pipelines`), S6 delivered (`agent-presets`, `loop-engineering`, `agent-orchestration-primitives`), S8 delivered for `nexus-hub init --target` via AR-01 (the suggested install-docs monorepo note was not shipped). Residual (user-deferred): the upstream repository-delta re-check needs a fresh comparison against the upstream project.

- **Current state**: no later record states their status; S8's functional half is AR-01.
- **Owner and next step**: next spec-kit delta pass; re-verify and record.
- **Historical transfer note**: v3.16#TR-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.16#TR-2 (reason: user-deferred); original `v3.16#TR-2`, section `Transferred in from v3.15.14 (spec-driven-development cycle)`.

#### Original source: TR-2 - OPEN: v3.11.0 spec-kit items S5, S6, and S8 carry no status claim - MIGRATED to v4.13 (AR-15)

- **Target**: the v3.11.0 spec-kit adoption ledger
- **Reason it is open**: the v3.15.14 comparison was article-scoped, not a repository-delta pass against `github/spec-kit`, so S5, S6, and S8 were never re-examined. The honest position is that they carry **no status claim** from this cycle rather than an implied "still open" or "now closed".
- **Suggested next step**: a future repository-delta comparison against `github/spec-kit` should re-verify all three explicitly and record a verdict per item. Do not infer their state from the v3.15.14 cycle, which did not look.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-15`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.16`, section `Transferred in from v3.15.14 (spec-driven-development cycle)`, and original ID `TR-2`.

- **Migrated from**: v4.13#AR-15 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-15 upstream delta verification needs a fresh repository comparison against github/spec-kit, which this offline audit cannot perform.

### AR-10: The skill-description eval harness builds CLI flags that do not exist

**Carry-forward contract (v4.13.11)**:
- **Owner**: eval-pipeline owner
- **Severity**: medium - stated Medium on origin BG-v30-1; the live-confirmation origins DF-v30-6 and DF-v30-7 are stated Low
- **Blocker**: user-credential - AR-04 live trigger-rate and technique checks require paid model calls under a bounded spend cap, blocked with BG-7.
- **Acceptance**: Live trigger and technique checks run under a bounded spend cap confirm 1.0 positive / 0.0 fenced-negative per listed skill and the three eval-harness techniques
- **Proving command**: manual: a capped live run of `scripts/optimize_skill_description.py` records per-skill trigger results; flag validity is covered by `python -m pytest tests/validators/test_eval_harness_cli_flags.py -q`
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: The description optimizer now builds only flags the installed CLIs accept (Claude Code 2.1.283, codex-cli 0.136.0), staging the skill in a throwaway project and reusing the trigger pilot's invocation; `tests/validators/test_eval_harness_cli_flags.py` checks every emitted flag against captured help fixtures offline and fails on the previous builder, which emitted `--skill` and `--prompt`. Residual (user-credential): the live trigger and technique checks need paid model calls under a bounded spend cap, blocked with BG-7.

- **Current state**: `scripts/optimize_skill_description.py` still adds `--skill` and `--prompt` (verified 2026-09-29), so live trigger runs and technique checks cannot run through it. `scripts/run_trigger_pilot.py` has a working `stream-json` path.
- **Owner and next step**: eval-pipeline owner; port the pilot's invocation, then run the recorded live checks.
- **Historical transfer note**: v3.0#BG-v30-1, v3.0#DF-v30-6, and v3.0#DF-v30-7 on 2026-09-29 (reason: live defect, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.0#DF-v30-6 (reason: user-deferred); original `v3.0#DF-v30-6`, section `Open Items`.

#### Original source: DF-v30-6 - MIGRATED to v4.13 (AR-04)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-6 - MIGRATED to v4.13 (AR-04)

**Category**: DF

**Source phase**: Phase 10

**Plan reference**: T045 (live skill-eval-loop)

**Reason**: Re-deferred. A model CLI IS on PATH this version (`claude` + `codex`), so the prior "no CLI" reason no longer holds -- but a faithful with-skill-vs-baseline trigger run is still not achievable: the bundled harness (`scripts/optimize_skill_description.py`) builds `claude -p ... --skill <path>` / `codex exec ... --prompt <path>`, and both flags are rejected by the shipped CLIs (`error: unknown option '--skill'`; `codex exec` has no `--prompt`). After patching detection to the real CLI surface (install the skill into a temp `.claude/skills/`, run headless `claude -p --output-format stream-json`, parse the stream for a `Skill` tool_use), 3 live runs (haiku positive, sonnet positive, sonnet fenced-negative) for `agent-orchestration-primitives` showed the skill is discoverable and the `Skill` tool is available, yet neither model invoked it on a dead-on-topic prompt -- because in a Nexus-Hub environment the real trigger path is the `search_skills` MCP (per the global skill-discovery instruction), not the bare `Skill` tool, and a capable model answers an advisory prompt directly. Carries DF-v24-8 (subsumes DF-v24-1/2/3/4/6, carries DF-v23-7) for: `agent-orchestration-primitives`, `skill-security-scan`, `verification-before-completion`, `receiving-code-review`, `using-git-worktrees`, `solution-knowledge-base`, `solution-refresh`, `multi-agent-code-review`, `plan-review`, `product-strategy`, `session-query`, `product-pulse`, `demo-capture`. Static trigger-surface checks (verbatim trigger phrases + SKIP clauses + cross-fencing) already done at authoring for all.

**Suggested next step**: A faithful live eval requires replicating the `search_skills` MCP discovery path: wire `nexus-skill-server` into each nested run (no `--strict-mcp-config`) and detect trigger via the `search_skills` call plus the subsequent `Skill` load -- tracked by BG-v30-1. Pick up once BG-v30-1 fixes the harness; author a minimal `evals.json` per skill and confirm 1.0 positive / 0.0 fenced-negative.

**Severity**: Low (static surface verified; live confirmation blocked on BG-v30-1)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-04`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-6`.

- **Migrated from**: v3.0#DF-v30-7 (reason: user-deferred); original `v3.0#DF-v30-7`, section `Open Items`.

#### Original source: DF-v30-7 - MIGRATED to v4.13 (AR-04)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-7 - MIGRATED to v4.13 (AR-04)

**Category**: DF

**Source phase**: Phase 10

**Plan reference**: T045 (eval-harness trigger techniques)

**Reason**: Re-deferred for the same root cause as DF-v30-6. The three eval-harness trigger techniques (premature-action detection, multi-turn replay, cheap-model fragility) in `scripts/optimize_skill_description.py` cannot be exercised live because the harness's `build_cli_command` targets the non-existent `--skill` / `--prompt` flags. They remain validated at v2.3.0 via dry-run + pure-logic + fixture-stream tests (+23 pytest cases in `catalog/hooks/tests/test_eval_loop.py`, still green). The one live observation this phase: cheap-model fragility is real -- haiku did not load the skill on the positive prompt (consistent with what technique 3 is designed to surface). Carries DF-v24-9 (carries DF-v23-8).

**Suggested next step**: Fold into the same live-eval pass as DF-v30-6 once BG-v30-1 fixes the harness invocation: confirm `premature_action` flips on a planted pre-`Skill` tool use, a multi-turn eval triggers at its `trigger_turn`, and a description's trigger rate is compared across default and a cheaper `--model`.

**Severity**: Low (logic-tested; live confirmation blocked on BG-v30-1)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-04`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-7`.

- **Migrated from**: v3.0#BG-v30-1 (reason: user-deferred); original `v3.0#BG-v30-1`, section `Open Items`.

#### Original source: BG-v30-1 - MIGRATED to v4.13 (AR-04)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: BG-v30-1 - MIGRATED to v4.13 (AR-04)

**Category**: BG

**Source phase**: Phase 10

**Plan reference**: T045 (live evals; harness defect found)

**Reason**: Shipped catalog tooling constructs a CLI command the shipped CLI rejects. `scripts/optimize_skill_description.py::build_cli_command` builds `claude -p <prompt> --skill <path>`, `codex exec <prompt> --prompt <path>`, `gemini --workflow <prompt> --skill-file <path>`, and `opencode run <prompt> --skill <path>` -- but the installed Claude Code CLI returns `error: unknown option '--skill'` and `codex exec` has no `--prompt` flag (verified 2026-06-04). The harness was authored against an aspirational future "skill-load flag" surface (its own docstring says "Real CLIs will eventually surface a structured `skill_loaded` flag; until then this heuristic..."). The parity test (`catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter`) only asserts no cross-CLI binary bleed, so it never caught that the flags do not exist. Discovered while running T045 live.

**Suggested next step**: Patch `build_cli_command` (and `_detect_trigger`) to the real per-CLI surface: for `claude`, drop `--skill`, install the target skill into a temp project `.claude/skills/<name>/`, run from that cwd with `--output-format stream-json --verbose`, optionally wire `nexus-skill-server` via `--mcp-config` (no `--strict-mcp-config`) to exercise the real `search_skills` discovery path, and detect trigger from a `search_skills`/`Skill` tool_use in the stream rather than the description-phrase-echo heuristic. Update the parity test to assert each branch uses a flag the CLI actually accepts. Then DF-v30-6/-7 become runnable.

**Severity**: Medium (the bundled eval harness cannot perform a live run against any shipped CLI as written)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-04`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `BG-v30-1`.

**Tracking alias retained**: `v4.13.9#WN-24`; the following complete historical source has the same current obligation and is not a separate future task.

##### Tracking source: v4.13.9#WN-24 (v4.13.9): The skill-eval-loop Claude adapter command no longer matches the installed CLI

- **Source phase**: Phase 5. **Plan reference**: `v4.13.8-adoption-sonnet-5-5-profile-and-first-principles-test.md`, T319 and T321.
- **Reason**: `catalog/skills/workflow/skill-eval-loop/references/cli-adapter.md` documents the Claude runner as `claude -p "<prompt>" --setting-sources "" --model <model> --skill <path/to/SKILL.md>` (verified 2026-09-21), and `scripts/optimize_skill_description.py` builds that command. Claude Code 2.1.283's `--help` (checked 2026-09-30) documents no `--skill` option. The pilot used `--append-system-prompt-file` instead, without changing the shared adapter. The same CLI also reports `claude-sonnet-5-5` as an unrecognized model (see DF-4).
- **Suggested next step**: owner `skill-eval-loop`. Re-verify the Claude runner against the current official Claude Code CLI reference. If `--skill` is gone, choose and document the replacement (for example `--bare` with `--append-system-prompt-file`, or `--add-dir` with skill resolution), update the adapter and the optimizer's command builder together, and keep `TestEvalLoopCLIAdapter` parity green.

- **Carried from**: v4.13.8#WN-4 on 2026-10-02

- **Migrated from**: v4.13#AR-04 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: AR-04 live trigger-rate and technique checks require paid model calls under a bounded spend cap, blocked with BG-7.

### AR-9: Agent and hook delivery never observed on real Codex, Gemini CLI, Qwen, and Kimi installs

**Carry-forward contract (v4.13.11)**:
- **Owner**: maintainer on a host with those tools
- **Severity**: low - the written artifacts are test-proven; only live loading is unobserved and a wrong Windows shell degrades to a warning
- **Blocker**: user-credential - AR-57 needs authenticated Codex, Gemini CLI, Qwen and Kimi installs to observe agent loading, hook firing and the Windows dispatch shell.
- **Acceptance**: One live pass records agent loading, hook firing and the observed Windows dispatch shell for Codex, Gemini CLI, Qwen and Kimi in the read-contract verification block
- **Proving command**: manual: on a host with each CLI installed, confirm the emitted agents are listed and a project-scope hook fires, and record the observed shell in the read-contract verification block
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: the v3.15.8 consolidated live pass has no recorded result.
- **Owner and next step**: maintainer on a host with those tools; one live pass recorded in the read-contract verification block.
- **Historical transfer note**: v3.15.8#MT-6, v3.15.8#MT-7, and v3.15.8#MT-8 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#MT-6 (reason: user-deferred); original `v3.15.8#MT-6`, section `v3.15.8`.

#### Original source: MT-6 - Codex agent and hook delivery is not observed against a real Codex install - MIGRATED to v4.13 (AR-57)

- **Source phase**: v3.15.8 Phase 5.3 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 5.3).
- **Reason**: the suite proves the TOML schema, the merge algebra, ownership, idempotence, cross-shell parity, and teardown against a temporary filesystem, and the read contract asserts the surfaces exist after an install. What no test can prove from here is that a running Codex build loads the emitted TOML as an agent and fires the merged hooks, because that needs an authorized Codex session on a host that has the product installed.
- **Suggested next step**: fold a manual Codex load check into the same release-readiness pass that owns the other live verifications, then record the observed result in the read-contract verification block.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-57`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `MT-6`.

- **Migrated from**: v3.15#MT-7 (reason: user-deferred); original `v3.15.8#MT-7`, section `v3.15.8`.

#### Original source: MT-7 - Windows shell dispatch for these two platforms is asserted, not observed - MIGRATED to v4.13 (AR-57)

- **Source phase**: v3.15.8 Phase 6.3 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 6.3).
- **Reason**: the host-aware branch is fully tested in both directions, and CI runs the suite on a Windows runner, so what gets *written* on Windows is proven. What is not proven is which shell each CLI actually launches the command with. The workspace-scope command references `$env:GEMINI_PROJECT_DIR` / `$env:QWEN_PROJECT_DIR` in PowerShell syntax; if a Windows build dispatches through `cmd.exe` instead, the variable stays literal and the hook fails to find its script. Neither platform's documentation states the Windows shell, and the failure mode is bounded: Gemini CLI's exit-code contract makes any non-zero exit other than 2 a warning that lets the interaction proceed, so a wrong guess degrades to a warning rather than a block.
- **Suggested next step**: during release readiness, run one project-scope hook on a Windows host with each CLI installed and record the observed shell in the read contract; if it is `cmd.exe`, switch the workspace reference to `%VAR%` form behind the same host check.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-57`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `MT-7`.

- **Migrated from**: v3.15#MT-8 (reason: user-deferred); original `v3.15.8#MT-8`, section `v3.15.8`.

#### Original source: MT-8 - Kimi agent and hook delivery is not observed against a real Kimi install - MIGRATED to v4.13 (AR-57)

- **Source phase**: v3.15.8 Phase 7.3 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 7.3).
- **Reason**: the suite proves the verbatim copy, the four-field schema, comment and table preservation, rollback, duplicate suppression, host-selected commands, and teardown against a temporary filesystem, and CI runs it on Windows. What no test here can prove is that a running Kimi build lists the copied agents alongside its built-ins and fires the spliced hooks. This is the same boundary as MT-6 for Codex and MT-7 for the Gemini-CLI-class platforms.
- **Suggested next step**: fold a Kimi load check into the same release-readiness pass that owns MT-6 and MT-7, confirming `/hooks` lists the block's entries and the agents appear in Kimi's agent list.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-57`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `MT-8`.

- **Migrated from**: v4.13#AR-57 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: AR-57 needs authenticated Codex, Gemini CLI, Qwen and Kimi installs to observe agent loading, hook firing and the Windows dispatch shell.

### AR-8: Upstream-blocked hook surfaces

**Carry-forward contract (v4.13.11)**:
- **Owner**: platform-contract owner
- **Severity**: low - global hooks still apply; users lose only per-project hook scoping
- **Blocker**: vendor-feature - AR-56 DF-12 needs Gemini CLI to document directly-written extension hook directories as loaded.
- **Acceptance**: Gemini CLI documents that a directly written extension hook directory is loaded (global hooks then move there), and Kimi documents a project-scoped hook path (workspace hooks then ship through the marker-block merge)
- **Proving command**: manual: re-check the Gemini CLI extension reference and the Kimi configuration reference at the next contract pass and record the result
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: the Gemini CLI extension-packaged hook path is unused, and Kimi has no project-scoped hook path.
- **Owner and next step**: platform-contract owner; re-check vendor docs at the next pass.
- **Historical transfer note**: v3.15.8#DF-12 and v3.15.8#DF-13 on 2026-09-29 (reason: vendor-dependent, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-12 (reason: user-deferred); original `v3.15.8#DF-12`, section `v3.15.8`.

#### Original source: DF-12 - Gemini CLI extension-packaged hooks are a cleaner write path left unused - MIGRATED to v4.13 (AR-56)

- **Source phase**: v3.15.8 Phase 6.1 - Map Gemini CLI Hooks.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 6.1).
- **Reason**: the [extension reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md) documents extensions as a fourth hook-precedence layer, reading `~/.gemini/extensions/<name>/hooks/hooks.json` with `${extensionPath}` and `${/}` substitution. That would give Nexus-Hub a fully-owned directory instead of a merge into the user's main config, and would solve the absolute-path and path-separator problems outright. It is not used because the reference documents only `gemini extensions install` for populating that directory, so writing it directly would be an inferred write path of exactly the kind sub-task 6.1 says to record rather than ship; it also has no project scope, where half of this phase's delivery lives. The maintainer chose settings.json now with this recorded as a follow-on.
- **Suggested next step**: if a later release can verify that a directly-written extension directory is loaded (or can shell out to `gemini extensions install` against a local path), migrate global-scope hooks there and keep the settings.json merge for workspace scope.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-56`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `DF-12`.

- **Migrated from**: v3.15#DF-13 (reason: user-deferred); original `v3.15.8#DF-13`, section `v3.15.8`.

#### Original source: DF-13 - Kimi has no project-scoped hook path, so workspace hooks are undeliverable - MIGRATED to v4.13 (AR-56)

- **Source phase**: v3.15.8 Phase 7.2 - Merge Kimi TOML Hooks.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 7.2).
- **Reason**: the matrix assumed a project `.kimi-code/config.toml`. That file does not exist -- Kimi's project-local configuration is `.kimi-code/local.toml`, which the [configuration reference](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/config-files) documents as holding only a `[workspace]` table with `additional_dir`, and `[[hooks]]` is documented exclusively in the user-level `~/.kimi-code/config.toml`. Sub-task 7.2 says to reject undocumented paths, so the workspace hook row stays finding-only with the reason recorded in the row itself rather than shipping an invented destination. The practical impact is bounded: hooks installed at global scope apply to every project, so a user loses per-project hook scoping, not the guardrails.
- **Suggested next step**: if Kimi later documents project-scoped hooks (in `local.toml` or elsewhere), deliver them through the same marker-block merge, which is scope-agnostic already.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-56`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.8`, section `v3.15.8`, and original ID `DF-13`.

- **Migrated from**: v4.13#AR-56 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: AR-56 DF-12 needs Gemini CLI to document directly-written extension hook directories as loaded.

### AR-7: The legacy Cursor global commands write is unverified and redundant

**Carry-forward contract (v4.13.11)**:
- **Owner**: installer maintainer
- **Severity**: low - stated not blocking; writing a directory Cursor ignores is harmless
- **Blocker**: vendor-feature - AR-47 needs first-party Cursor documentation or a live read-back confirming ~/.cursor/commands is unread before the redundant write is removed.
- **Acceptance**: First-party Cursor documentation or a live read-back confirms `~/.cursor/commands` is unread, and the redundant global write is removed with a test
- **Proving command**: `python -m pytest tests/integrations/test_cursor.py -q`
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: `scripts/lib/integrations/cursor.py` still writes both command directories and labels the global one UNVERIFIED.
- **Owner and next step**: installer maintainer; confirm at the next Cursor contract pass, then remove the redundant write with a test.
- **Historical transfer note**: v3.15.0#DF-1(a) and v3.15.10#DF-17 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.15#DF-17 (reason: user-deferred); original `v3.15.10#DF-17`, section `v3.15.10 - end-of-task-agent-behavior`.

#### Original source: DF-17 - Legacy Cursor global commands write remains unverified

- **DF-17 - DF-1 commands residual.** The global `~/.cursor/commands` write is now documented as redundant (Cursor no longer documents a commands directory, Cursor 2.4 migrates commands into skills, and Nexus-Hub already ships each command as a command-skill). Retained deliberately because the risk is asymmetric: writing a directory Cursor ignores is harmless, removing one it does read silently drops coverage. Remove deliberately in a later release. - MIGRATED to v4.13 (AR-47)

**Normalization, 2026-10-09 (v4.13.11 T006)**: Converted the authoritative bullet to a supported gap heading. The complete original source paragraph is retained above. The residual belongs to AR-47; the canonical copy must be verified before a parsed forward-migration marker is added.


**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-47`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.10`, section `v3.15.10 - end-of-task-agent-behavior`, and original ID `DF-17`.

- **Migrated from**: v3.15#DF-1-v3150 (reason: user-deferred); original `v3.15.0#DF-1`, section `v3.15.0 - platform-parity-all-gaps`.

#### Original source: DF-1-v3150 - Cursor global commands path UNVERIFIED (residual; hooks.json schema RESOLVED in Phase 2) - MIGRATED to v4.13 (AR-47)

- **Source phase**: v3.15.0 Phase 1.2; actioned in Phase 2 (2026-07-21)
- **Plan reference**: Phase 2 (Cursor parity - skills, hooks.json, agents, project commands)
- **Status**: PARTIALLY RESOLVED. **DF-1(b) hooks.json schema - RESOLVED**: [cursor.com/docs/hooks](https://cursor.com/docs/hooks) confirms `{version:1, hooks:{<event>:[{...}]}}` with the optional fields defaulted, so the integration's minimal `beforeShellExecution -> {command}` writer is schema-valid as-is (no code change). **DF-1(a) global `~/.cursor/commands/` - RESIDUAL (still UNVERIFIED)**: project `.cursor/commands/<name>.md` is officially documented (Cursor 1.6+) and confirmed, but the user-global `~/.cursor/commands/` dir has no reachable official doc and [forum.cursor.com](https://forum.cursor.com/t/personal-custom-slash-commands/133386) reports it as an open feature-request.
- **Decision**: the global write is RETAINED per plan sub-task 2.3 and the contract's negative-only-evidence caution; it is harmless if unread.
- **Suggested next step**: a future cycle with a reachable Cursor commands doc (or an empirical test) should confirm or drop the global `~/.cursor/commands/` write. Not blocking - the confirmed project `.cursor/commands/` surface is the load-bearing path.

**Original source identity**: `v3.15.0#DF-1` in `v3.15.0 - platform-parity-all-gaps`; normalized stable ID `DF-1-v3150` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-47`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.15.0`, section `v3.15.0 - platform-parity-all-gaps`, and original ID `DF-1`.

- **Migrated from**: v4.13#AR-47 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: AR-47 needs first-party Cursor documentation or a live read-back confirming ~/.cursor/commands is unread before the redundant write is removed.

### AR-6: Invocation-policy support remains incomplete across five platforms

**Carry-forward contract (v4.13.11)**:
- **Owner**: platform-contract owner
- **Severity**: low - incomplete native invocation support stays explicitly recorded for the retained platform clauses
- **Blocker**: vendor-feature - The 2026-10-12 primary-source review qualifies Kimi's compatible model-invocation alias and documents OpenCode native metadata, whose mapper remains unimplemented. Antigravity and Hermes document no matching per-skill toggle; the inspected Nexus-AI reader does not qualify invocation enforcement.
- **Acceptance**: All five platform clauses have a first-party invocation contract and matching delivery qualification recorded in `docs/policy/skill-invocation-policy-levers.md`; Kimi's compatible alias is already qualified, while OpenCode needs its documented metadata mapper and the remaining contracts stay unqualified.
- **Proving command**: manual: re-check each vendor's documentation at the release pass and record the dated result in `docs/policy/skill-invocation-policy-levers.md`
- **Future plan**: v4.14 known-gaps sweep

- **Current state (2026-10-12)**: [The invocation survey](../../../policy/skill-invocation-policy-levers.md) qualifies Kimi's existing generic alias, supersedes OpenCode's historical none-documented claim with native keys and an unimplemented mapper, and preserves the Antigravity, Hermes and Nexus-AI limitations. Authenticated host enforcement and whole-code absence are not claimed.
- **Owner and next step**: platform-contract owner; implement and prove the documented OpenCode mapper, re-check the remaining first-party contracts each release, and close only when every retained clause is qualified.
- **Historical transfer note**: v3.20.3#DF-1 on 2026-09-29 (reason: vendor-dependent, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.20#DF-1-v3203 (reason: user-deferred); original `v3.20.3#DF-1`, section `v3.20.3`.

#### Original source: DF-1-v3203 - No native invocation mapping for platforms with no vendor lever - MIGRATED to v4.13 (AR-38)

- **Source phase**: Phase 4 - Invocation-policy metadata
- **Plan reference**: `docs/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md` (sub-task 4.1)
- **Reason**: Antigravity, OpenCode, Kimi, Hermes, and Nexus-AI document no per-skill invocation-policy field. Generated command-skills still carry `disable-model-invocation: true` in SKILL.md; those hosts ignore the unknown key. Inventing a sidecar would repeat the v3.15.0 fabricated-companion failure.
- **Suggested next step**: Revisit when a first-party vendor document names a lever. Until then keep the honest gap note in `docs/policy/skill-invocation-policy-levers.md`.

**Original source identity**: `v3.20.3#DF-1` in `v3.20.3`; normalized stable ID `DF-1-v3203` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-38`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.20.3`, section `v3.20.3`, and original ID `DF-1`.

- **Migrated from**: v4.13#AR-38 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: AR-38 remains open after the 2026-10-12 primary-source review: Kimi compatible aliases are qualified; OpenCode documents native policy fields but Nexus-Hub has not mapped them; Antigravity and Hermes lack a documented matching per-skill lever; Nexus-AI reader evidence does not establish invocation control. See docs/policy/skill-invocation-policy-levers.md and the dated carry-forward contract in docs/releases/v4/v4.13/known-gaps.md.

### AR-5: Unverified platform read-path residuals

**Carry-forward contract (v4.13.11)**:
- **Owner**: platform-contract owner
- **Severity**: low - stated Low in the origin entries DF-v3121-agy-cli-workflows and DF-v3121-gemini-ide-skill-dir
- **Blocker**: user-credential - AR-36 needs authenticated Antigravity CLI and Cursor UI read-backs, Gemini Code Assist IDE observation and Nexus-AI private-repo access; the 2026-09-27 host was not signed in.
- **Acceptance**: Authenticated Antigravity CLI and Cursor UI read-backs, Gemini Code Assist IDE observation and the Nexus-AI project-mirror read path are recorded in `docs/policy/platform-read-contracts.md`, and the maintainer decides whether `antigravity2` stops writing the retired workflow paths after October 19
- **Proving command**: manual: with a signed-in Antigravity CLI and Cursor, read back a documented agent and a global command and record each result in `docs/policy/platform-read-contracts.md`
- **Future plan**: v4.14 known-gaps sweep

**Local clause qualification, 2026-10-10 (v4.13.11 T028)**: `platform-read-contracts.md` carries a dated Antigravity legacy-workflow retirement clause; a re-fetch of the vendor migration guide on 2026-10-10 gives October 19, 2026, earlier than the November 1 date in the archived recheck, and `check_platform_contract_freshness.py` passes. Residuals: authenticated Antigravity CLI, Cursor UI, Gemini Code Assist and Nexus-AI read-backs (user-credential), and whether the `antigravity2` adapter stops writing the retired workflow paths after October 19 (user-deferred maintainer decision).

- **Current state**: Antigravity CLI agent/workflow directories, Cursor global commands, and the Gemini Code Assist skill directory are still residuals in `docs/policy/platform-read-contracts.md`. The Antigravity part is also tracked as v4.3 WN-3 and v4.12 DF-1 above.
- **Owner and next step**: platform-contract owner; resolve at the next authenticated read-back.
- **Historical transfer note**: v3.11#DF-1 (D5, D7), v3.12.1#DF-v3121-agy-cli-workflows, and v3.12.1#DF-v3121-gemini-ide-skill-dir on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

**Current residual from `v4.3.0#WN-3`**: Obtain authenticated Antigravity CLI custom-agent/workflow and Cursor command read-backs. Qualify Gemini Code Assist IDE surfaces beyond GEMINI.md. Resolve Nexus-AI project mirrors and remaining optional mirrors independently of the already source-qualified global skill reader. Retain a separate dated retirement clause/link for Antigravity legacy workflows rather than implying immediate deletion.

**Partial disposition**: Keep 2026-09-24 shared Antigravity global/workspace hook reference and Nexus-AI global-reader source qualification as historical partial closures. The 2026-09-27 unauthenticated Antigravity empty roster was inconclusive; Cursor 3.21.18 lacked the required command UI read-back.

- **Migrated from**: v3.11#DF-1 (reason: user-deferred); original `v3.11.0#DF-1`, section `v3.11.0`.

#### Original source: DF-1 - Residual live-verification gaps (external platform contracts) - MIGRATED to v4.13 (AR-01)

- **Source phase**: Phase 7 (7.1 audit, residual gaps D1-D7)
- **Plan reference**: `docs/v3/v3.11/platform-read-contracts.md` (Residual live-verification gaps)
- **Reason**: These contracts depend on the current external platform's behavior and cannot be confirmed from the repo alone. The 7.4 `verify` and 7.5 CI smoke now REPORT/CATCH the resulting surfacing gaps, but the underlying external contracts still want a live probe.
- **Suggested next step**: Live-probe per platform: Codex prompt read path + format (D1) and skills discovery (D2); Antigravity 2.0 root-vs-`.agents/` instruction file (D3), exact global subpath (D4), `subagents`/`rules` consumption (D5), `.agents` vs `.agent` (D6); Cursor/Copilot global slash surfaces (D7); and whether `nexus-hub init` (the launcher) passes the `init` subcommand through (the on-open hook calls it fail-open). Feed results back into codex.py / antigravity.py.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-36`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.11.0`, section `v3.11.0`, and original ID `DF-1`.

- **Migrated from**: v3.12#DF-v3121-agy-cli-workflows (reason: user-deferred); original `v3.12.1#DF-v3121-agy-cli-workflows`, section `v3.12.1`.

#### Original source: DF-v3121-agy-cli-workflows - MIGRATED to v4.13 (AR-36)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v3121-agy-cli-workflows - MIGRATED to v4.13 (AR-36)

**Source**: Phase 3 (Antigravity)

**Reason**: The `agy` CLI global SKILLS path is confirmed (`~/.gemini/antigravity-cli/skills/`); the CLI global WORKFLOW dir is undocumented and written best-effort. IDE global slash works via `~/.gemini/config/global_workflows/`.

**Severity**: Low

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-36`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.12.1`, section `v3.12.1`, and original ID `DF-v3121-agy-cli-workflows`.

- **Migrated from**: v3.12#DF-v3121-gemini-ide-skill-dir (reason: user-deferred); original `v3.12.1#DF-v3121-gemini-ide-skill-dir`, section `v3.12.1`.

#### Original source: DF-v3121-gemini-ide-skill-dir - MIGRATED to v4.13 (AR-36)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v3121-gemini-ide-skill-dir - MIGRATED to v4.13 (AR-36)

**Source**: Phase 4 (sweep)

**Reason**: `~/.gemini/skills` flattening is confirmed for Gemini CLI; the Gemini IDE (Code Assist) skill dir is applied on weight-of-evidence. The SKILL_INDEX in GEMINI.md covers Code Assist regardless.

**Severity**: Low

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-36`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.12.1`, section `v3.12.1`, and original ID `DF-v3121-gemini-ide-skill-dir`.

- **Migrated from**: v4.3#WN-3 (reason: user-deferred); original `v4.3.0#WN-3`, section `v4.3.0 - agentic-verification-discipline`.

#### Original source: WN-3 - Optional platform surfaces remain unverified

- **Source phase**: Phase 5 platform-contract verification
- **Plan reference**: `docs/archives/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T023
- **Evidence**: The current official audit did not prove Antigravity CLI loose workflow or hook destinations, Cursor legacy command directories, Gemini IDE surfaces beyond `GEMINI.md`, or Nexus AI read paths. The coupled bundle removes or avoids those claims instead of guessing.
- **Impact**: Verified platform destinations continue to install, while these optional surfaces are deliberately absent or marked `UNVERIFIED`; users do not receive a false discovery guarantee.
- **Owner**: Platform integration maintainer.
- **Next step**: Recheck each surface against dated official documentation or a live-host artifact before adding a destination, default, or verification gate.

**Targeted source recheck, 2026-09-24**: [Google's current hook reference](https://antigravity.google/docs/hooks?tab=cli) confirms that Antigravity CLI reads the shared global `~/.gemini/config/hooks.json` and workspace `.agents/hooks.json`; the existing adapter already emits both, and a global-install dry-run assertion now protects that path. [Nexus-AI source at `198ff9c8`](https://github.com/bendourthe/Nexus-AI/blob/198ff9c877f258c775092761e3c67a6bed56b1d2/desktop/sidecar/src/skills/hubSkillReader.ts) qualifies its global `~/.nexus-ai/catalog/skills` reader. The [archived bounded recheck](../../../archives/v4/v4.3/development/optional-platform-surface-recheck.md) keeps CLI loose workflows and agents, Cursor legacy command directories, Gemini Code Assist IDE add-on surfaces, and Nexus-AI's project-local mirror and other mirrored surfaces unverified. WN-3 remains open; no live Antigravity or Nexus-AI host behavior was claimed.

**Targeted source recheck, 2026-09-26**: [Current Google CLI and migration documentation](../../../archives/v4/v4.3/development/optional-platform-surface-recheck-2026-09-26.md) now source-qualifies the shared Antigravity custom-agent and legacy-workflow destinations already emitted by the adapter, but the latter retires on November 1, 2026. Cursor's global command path has a vendor-reported discovery bug, Gemini Code Assist's IDE custom commands and rules use IDE settings rather than a documented CLI-file mirror, and Nexus-AI's project-local mirror still lacks a read-path proof. WN-3 remains open for those live-host and project-local questions; this addendum does not convert source evidence into a runtime pass.

**Local host read-back attempt, 2026-09-27**: Installed Antigravity CLI 1.2.12 exposes `agy agents`, but it printed no agents from either this checkout or a disposable workspace containing a documented `.agents/agents/nexus-probe/agent.md`; the empty list is inconclusive without an authenticated interactive read-back. The interactive CLI reported that this host was not signed in and rejected the existing `agentMode: "default"` setting before opening an agent session; no settings were changed. Installed Cursor 3.21.18 exposes no agent-discovery list in `cursor --help`, and its UI read-back was not exercised. WN-3 remains open for authenticated Antigravity and Cursor observations, the dated workflow-retirement decision, Gemini Code Assist IDE behavior, and Nexus-AI's project-local mirror. The disposable agent fixture was removed after the test.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-36`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v4.3.0`, section `v4.3.0 - agentic-verification-discipline`, and original ID `WN-3`.

- **Migrated from**: v4.13#AR-36 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: AR-36 needs authenticated Antigravity CLI and Cursor UI read-backs, Gemini Code Assist IDE observation and Nexus-AI private-repo access; the 2026-09-27 host was not signed in.

### AR-4: Permission distribution covers few platforms and scopes

**Carry-forward contract (v4.13.11)**:
- **Owner**: installer maintainer
- **Severity**: low - platforms without a researched target skip with a note rather than receiving a guessed path
- **Blocker**: vendor-feature - AR-17 DF-2 needs Gemini and Codex to document a project-scoped permission path; none was documented well enough to write.
- **Acceptance**: Gemini and Codex project-scoped permission paths are researched, the Copilot `.vscode/settings.json` decision is recorded, and install / uninstall / repair is exposed through the `nexus-hub` CLI
- **Proving command**: `python scripts/nexus_hub_cli.py --help`
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: only Claude is wired at workspace scope; `Install-Nexus-Hub-Permissions.ps1` has no cross-platform equivalent; `configs/permissions/` covers 4 of 16 integrations.
- **Owner and next step**: installer maintainer; research Gemini and Codex project paths, decide Copilot `.vscode/settings.json`, and add a `nexus-hub` permissions command.
- **Historical transfer note**: v3.17.0#DF-2, v3.17.0#DF-3, and v3.17.0#DF-5 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.17#DF-2-v3170 (reason: user-deferred); original `v3.17.0#DF-2`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: DF-2-v3170 - OPEN: three of four platforms have no project-scoped permission target - MIGRATED to v4.13 (AR-17)

- **Target file**: `scripts/installer.sh` and `scripts/installer.ps1` (`install_permissions` / `Install-Permissions`, workspace branch)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2
- **Reason it is open**: workspace scope is now wired and load-bearing, but only Claude Code has a confirmed target (`.claude/settings.local.json`). The other three skip WITH A NOTE, each for a stated reason: **Gemini** and **Codex** have no project-scoped permission path documented well enough to write, and a guessed path is worse than none because it reads as configured; **Copilot**'s only surface is `.vscode/settings.json`, which is commit-visible and therefore forbidden here without an explicit maintainer decision (the same reasoning that made the v3.11.0 Copilot `.github/skills/` surface opt-in).
- **Suggested next step**: run a permission-path-specific contract sweep for Gemini and Codex; the Phase 2 autonomy sweep answered a different question. The Copilot half needs a maintainer decision about writing to a commit-visible file, not more research.

**Original source identity**: `v3.17.0#DF-2` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `DF-2-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-17`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `DF-2`.

- **Migrated from**: v3.17#DF-3-v3170 (reason: user-deferred); original `v3.17.0#DF-3`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: DF-3-v3170 - OPEN: `Install-Nexus-Hub-Permissions.ps1` still has no cross-platform equivalent - MIGRATED to v4.13 (AR-17)

- **Target file**: `scripts/Install-Nexus-Hub-Permissions.ps1`, `scripts/nexus_hub_cli.py`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2 (deferred by that sub-task's own instruction)
- **Reason it is open**: that helper provides install, uninstall, and backup-repair paths for all four platforms and has no bash sibling, so POSIX users have no equivalent repair route. Sub-task 1.2 forbids porting it to bash, and correctly: a second shell script would recreate exactly the dual-implementation drift this phase removed.
- **Suggested next step**: expose install / uninstall / repair through the cross-platform `nexus-hub` CLI, whose `scripts/nexus_hub_cli.py` now includes the Phase 5 `autonomy` subcommand. One implementation, three operating systems. Phase 5 shipped autonomy only, so this separate lifecycle gap carries forward.

**Original source identity**: `v3.17.0#DF-3` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `DF-3-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-17`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `DF-3`.

- **Migrated from**: v3.17#DF-5 (reason: user-deferred); original `v3.17.0#DF-5`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: DF-5 - OPEN by design: the read-only baseline covers only four of 16 integrations - MIGRATED to v4.13 (AR-17)

- **Target files**: `configs/permissions/`, `scripts/installer.sh`, `scripts/installer.ps1`, `docs/permissions-research.md`
- **Source phase**: v3.17.0 Phase 6 reconciliation of the Phase 1 and Phase 2 coverage boundaries
- **Disposition**: deliberate non-delivery. Claude Code, Codex, Gemini, and Copilot receive the existing baseline. Aider, Antigravity 1.0, Antigravity 2.0, Cursor, Gemini CLI, Hermes, Kimi, Nexus-AI, OpenClaw, OpenCode, Qwen, and Windsurf receive no Nexus-Hub read-only baseline.
- **Why it remains open**: autonomy coverage and read-only allowlist coverage are independent. This release widened the former and deliberately did not invent permission matchers for platforms whose safe read-only contracts were not researched.
- **Suggested next step**: handle one platform at a time through a permission-contract research and validator cycle. Do not infer baseline safety from the existence of an autonomy descriptor.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-17`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `DF-5`.

- **Migrated from**: v4.13#AR-17 on 2026-10-13 (reason: vendor-feature)
- **Migration evidence**: AR-17 DF-2 needs Gemini and Codex to document a project-scoped permission path; none was documented well enough to write.

### AR-3: Permission-matcher behaviors remain unprobed

**Carry-forward contract (v4.13.11)**:
- **Owner**: `platform-contract-verification` owner
- **Severity**: medium - if the matcher admits redirects under allow rules, every trailing-wildcard baseline pattern is a file-truncation primitive
- **Blocker**: user-credential - AR-16 NI-1 needs an interactive Claude Code session on the user's account to observe whether `echo x > file` prompts under a `Bash(echo *)` allow rule.
- **Acceptance**: The Claude Code redirect probe and the Gemini compound-command probe each record a MATCH, DRIFT, or UNVERIFIED verdict, and the Gemini PowerShell / `cmd.exe` read-only set is decided after the Gemini splitting verdict
- **Proving command**: manual: in a throwaway project with one `Bash(echo *)` allow rule on a current Claude Code build, observe whether `echo x > /tmp/probe` prompts, and record the verdict beside the permission findings
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: output redirection under an explicit allow rule, whether Gemini splits compound commands, and a Gemini PowerShell / `cmd.exe` read-only set are all still UNVERIFIED in the v3.17 `development/permission-matcher-findings.md` and `configs/permissions/gemini-permissions.json`.
- **Owner and next step**: `platform-contract-verification` owner; run the recorded probes against current builds.
- **Historical transfer note**: v3.17.0#NI-1, v3.17.0#NI-2, and v3.17.0#DF-1 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.17#NI-1-v3170 (reason: user-deferred); original `v3.17.0#NI-1`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: NI-1-v3170 - OPEN: output redirection under an explicit allow rule is UNVERIFIED - MIGRATED to v4.13 (AR-16)

- **Target file**: [development/permission-matcher-findings.md](../../../archives/v3/v3.17/development/permission-matcher-findings.md) (Finding 2), `scripts/validate_permission_baseline.py` (the `redirect` rule)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1
- **Plan reference**: 1.1 required determining empirically "whether Claude Code's matcher treats a redirected command as matching the bare pattern"
- **Reason it is open**: the official permissions documentation demonstrably models redirects, but states it only for the BUILT-IN read-only command set, never for explicit `allow` rules. Redirection operators are also absent from the enumerated command-separator list, so a redirected command is one subcommand rather than two, and a wildcard "matches any sequence of characters including spaces". Per this plan's evidence discipline, absence of a statement is recorded as UNVERIFIED rather than as absence of the behavior.
- **Why it is load-bearing**: `> file` truncates its target regardless of what the command emits (`Write-Host x > f` writes nothing to the file and still truncates it). If the native matcher admits redirects under allow rules, then EVERY baseline pattern carrying a trailing wildcard is a file-destruction primitive, and no per-entry rescoping repairs that. This is a global property of the matcher, not a defect of any individual entry, which is why Phase 1.1 did not attempt to fix it per-entry.
- **Suggested next step**: run the empirical probe named in Finding 2 against a throwaway project and a current Claude Code build: add one `Bash(echo *)` allow rule and observe whether `echo x > /tmp/probe` prompts. Phase 4 verified hook independence but did not execute this separate native-matcher probe, so the evidence remains UNVERIFIED.

**Original source identity**: `v3.17.0#NI-1` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `NI-1-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-16`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `NI-1`.

- **Migrated from**: v3.17#NI-2-v3170 (reason: user-deferred); original `v3.17.0#NI-2`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: NI-2-v3170 - OPEN: whether Gemini's matcher splits compound commands at all - MIGRATED to v4.13 (AR-16)

- **Target file**: `configs/permissions/gemini-permissions.json`, [development/permission-matcher-findings.md](../../../archives/v3/v3.17/development/permission-matcher-findings.md) (Finding 1)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1
- **Reason it is open**: Finding 1 VERIFIED compound-command splitting for Claude Code, quoted from its documentation, for both the Bash and the PowerShell matcher. No equivalent statement was located for Gemini's `run_shell_command`, and the file's own shipped comment records the opposite direction ("piped commands bypass allowlists (upstream issue)"). Gemini entries are therefore treated as PREFIX matches with no separator awareness, which is the conservative reading and is what `validate_permission_baseline.py` implements via its `prefix` match mode.
- **Why it matters**: under prefix semantics with no splitting, `run_shell_command(git status)` would admit `git status; rm -rf .`. The validator's conservative mode does not make that safe; it only stops Nexus-Hub from shipping patterns that depend on splitting.
- **Suggested next step**: run a dedicated Gemini CLI matcher probe and record a MATCH, DRIFT, or UNVERIFIED verdict beside the permission findings. Phase 2 verified autonomy levers, not compound-command matcher semantics. If splitting is absent, harden the Gemini baseline under prefix-without-splitting assumptions before expanding its Windows-shell coverage.

**Original source identity**: `v3.17.0#NI-2` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `NI-2-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-16`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `NI-2`.

- **Migrated from**: v3.17#DF-1-v3170 (reason: user-deferred); original `v3.17.0#DF-1`, section `v3.17.0 - agent-autonomy-toggle`.

#### Original source: DF-1-v3170 - OPEN: `gemini-permissions.json` ships no PowerShell or `cmd.exe` read-only set - MIGRATED to v4.13 (AR-16)

- **Target file**: `configs/permissions/gemini-permissions.json`, `docs/permissions-research.md`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1 (observation only, by instruction)
- **Plan reference**: 1.1 explicitly forbids adding one ("this sub-task rescopes existing entries and deliberately does not expand coverage") and hands the observation to sub-task 5.3
- **Reason it is open**: a Windows Gemini user receives a POSIX-shaped allowlist plus a bare `run_shell_command(dir)`, so their real shell is effectively uncovered. Expanding coverage is a different risk decision from rescoping and belongs with the platform-coverage work.
- **Suggested next step**: `docs/permissions-research.md` now documents the gap. Resolve NI-2 before designing a PowerShell or general `cmd.exe` baseline, because the safe pattern shape depends on whether the matcher splits compound commands.

**Original source identity**: `v3.17.0#DF-1` in `v3.17.0 - agent-autonomy-toggle`; normalized stable ID `DF-1-v3170` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-16`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.17.0`, section `v3.17.0 - agent-autonomy-toggle`, and original ID `DF-1`.

- **Migrated from**: v4.13#AR-16 on 2026-10-13 (reason: user-credential)
- **Migration evidence**: AR-16 NI-1 needs an interactive Claude Code session on the user's account to observe whether `echo x > file` prompts under a `Bash(echo *)` allow rule.

### AR-2: Two installer tests fail intermittently in long local runs

**Carry-forward contract (v4.13.11)**:
- **Owner**: installer/test maintainer
- **Severity**: low - environment-only OneDrive contention; both tests pass in isolation and in CI, not a release blocker
- **Blocker**: user-deferred - AR-40 can only close on hosted-CI evidence plus repeated clean full installer runs, since a single green local run cannot disprove a non-deterministic OneDrive flake.
- **Acceptance**: v4.13.1 BG-2 is verified in hosted CI and a full local installer run is clean; if either test fails in CI it is treated as a real defect
- **Proving command**: `python -m pytest tests/installer -q`
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: possibly the real-home leak that v4.13.1 BG-2 fixed for `test_selection_parity.py` (commit `ad768ca9`); unproven, and `test_org_cli.py` is not covered by that fix.
- **Owner and next step**: installer/test maintainer; close after v4.13.1 BG-2 is verified in hosted CI and a full local installer run is clean.
- **Historical transfer note**: v3.18.2#BG-2 on 2026-09-29 (reason: still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.18#BG-2-v3182 (reason: user-deferred); original `v3.18.2#BG-2`, section `v3.18.2 - github-usage-monitor-withdrawal`.

#### Original source: BG-2-v3182 - OPEN, environment-only: two installer tests fail non-deterministically in long local runs on OneDrive - MIGRATED to v4.13 (AR-40)

- **Observed**: 2026-08-22, post-release, on this Windows working tree (an OneDrive-synced folder). Two separate long local runs each failed **one** test, and **a different one each time**: `tests/installer/test_org_cli.py::test_disconnect_requires_confirmation_and_yes_removes_state_and_cache` (1 failed / 3888 passed, full suite, 60 min) and `tests/installer/test_selection_parity.py::test_powershell_filtered_install_matches_bash` (1 failed / 417 passed, `tests/installer` only, 5 min).
- **Both pass in isolation** (5.1s and 7.1s respectively) and **both pass in CI**: `tests (ubuntu-latest)`, `installer-smoke` on ubuntu / macos / **windows**, and `install-smoke` were all green on the v3.18.2 PRs.
- **Assessment: environment, not product.** The failing assertion in the first is `org connect <git-uri>` returning exit 2 instead of 0 - a shell-out to `git` against a bare-repo fixture. This session independently hit `fatal: unable to write new index file` from `git checkout -b` in this same tree, which is the documented OneDrive file-locking hazard. A different test failing on each run is the signature of contention, not of a deterministic defect.
- **Explicitly NOT evidence of a regression in the v3.18.2 withdrawal.** `test_selection_parity` compares the PowerShell and bash installers, which the withdrawal edited on both sides, so it was the first candidate checked. It passes in isolation and `installer-smoke (windows-latest)` passed in CI, which is the job that exercises the retirement guard on the affected platform.
- **Disposition**: not a release blocker and not tracked as product flakiness. Recorded so the next person who sees a lone installer failure on a OneDrive tree does not spend the investigation again. **A local full-suite run on this tree is not a trustworthy signal**; CI on a clean checkout is. If either test ever fails **in CI**, treat it as a real defect and delete this entry.
- **Related process failure**: the first of these was reported to the user as a passing suite, because the run was piped (`pytest ... | tail`) and the pipeline's exit code is `tail`'s, not `pytest`'s. Never read `$?` through a pipe to judge a test run; capture the exit code directly or use `PIPESTATUS`.
- **New data point 2026-08-22 (v3.18.3 Phase 5), which does NOT close this item**: a full `tests/installer` run on this same OneDrive tree was clean (418 passed, 17 skipped, 0 failed), as was `tests/integrations` (661 passed, 1 skipped). A non-deterministic flake cannot be disproved by one green run, so the entry stays open on its stated terms. Recorded because the absence of a failure is still evidence about frequency, and because the next person needs to know a clean local run has happened rather than assuming the tests always fail here.

**Original source identity**: `v3.18.2#BG-2` in `v3.18.2 - github-usage-monitor-withdrawal`; normalized stable ID `BG-2-v3182` distinguishes this obligation from repeated IDs in other patch sections.

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-40`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.18.2`, section `v3.18.2 - github-usage-monitor-withdrawal`, and original ID `BG-2`.

- **Migrated from**: v4.13#AR-40 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-40 can only close on hosted-CI evidence plus repeated clean full installer runs, since a single green local run cannot disprove a non-deterministic OneDrive flake.

### AR-1: No live macOS installer smoke has been recorded

**Carry-forward contract (v4.13.11)**:
- **Owner**: installation owner on a macOS host
- **Severity**: low - stated Low in the origin entries (macOS bash path auto-verified in CI; only the live-network one-liner is manual)
- **Blocker**: user-deferred - AR-26 needs the macOS smoke checklist and a live --branch install on a real macOS host; the v4.13.11 host is Windows only and CI covers only the local tarball bootstrap.
- **Acceptance**: The macOS smoke checklist and a live `--branch` install are run on a real macOS host and their results recorded
- **Proving command**: manual: on a macOS host run `curl | bash` and a `--branch` install and record each step's result in the mac-smoke-test checklist
- **Future plan**: v4.14 known-gaps sweep

- **Current state**: every step in the v3.7 `development/mac-smoke-test.md` is still pending; CI covers the tarball bootstrap only.
- **Owner and next step**: installation owner on a macOS host; run `curl | bash` and a `--branch` install and record results. Related to v4.4 HT-2 in the inventory above.
- **Historical transfer note**: v3.0#DF-v30-8 and v3.7, v3.8, v3.9#WN-v37-1 on 2026-09-29 (reason: one obligation recorded four times, still open).

**Transfer review, 2026-10-09 (v4.13.11 T007)**: The blocks below preserve complete historical obligations and their later partial dispositions. Current remaining clauses are assessed independently; historical fixed clauses do not reopen.

- **Migrated from**: v3.0#DF-v30-8 (reason: user-deferred); original `v3.0#DF-v30-8`, section `Open Items`.

#### Original source: DF-v30-8 - MIGRATED to v4.13 (AR-26)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: DF-v30-8 - MIGRATED to v4.13 (AR-26)

**Category**: DF

**Source phase**: Phase 10

**Plan reference**: T046 (cross-OS installer smoke + live --branch)

**Reason**: Re-deferred. The implementation host is Windows-only (no macOS / Linux host available, verified 2026-06-04), so the full macOS 14 installer smoke (sub-steps 1a-1l of `docs/archive/v2/v2.3/installer-smoke-post.txt`) and the Ubuntu installer-probe + `make eval` could not be run, and the live `--branch <pushed-branch>` clone+install (bash + PowerShell) was not exercised end-to-end. Windows is empirically green this version (full pytest 1160 passed / 4 skipped / 0 failed; ShellCheck 0.11.0 clean on installer.sh / install.sh; all validators + scan + version-sync green) and the Linux Python suite is green via CI (`.github/workflows/ci.yml` on ubuntu-latest). Carries DF-v24-10 (subsumes DF-v24-5; carries DF-v23-6).

**Suggested next step**: Before any packaged-binary release, run sub-steps 1a-1l on a macOS 14 host and the installer-probe/eval portion on an Ubuntu host (record in `docs/<version>/installer-smoke.txt`); while on those hosts, run the live `--branch` clone+install into a throwaway target and confirm the cache dir populates, the re-exec carries `NEXUS_HUB_BRANCH_RESOLVED=1` without re-cloning, the install completes from the cache, and the working copy is untouched.

**Severity**: Low (Windows empirically green; Linux green via CI; deferral acceptable for a source release)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-26`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.0`, section `Open Items`, and original ID `DF-v30-8`.

- **Migrated from**: v3.7#WN-v37-1 (reason: user-deferred); original `v3.7#WN-v37-1`, section `Open Items`.

#### Original source: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**Category**: WN

**Source phase**: install-ux-overhaul Phase 5

**Plan reference**: 5.1

**Reason**: The real `curl \| bash` one-liner against live GitHub cannot be exercised in CI (CI drives the bootstrap from a local `git archive` tarball with zero network) and cannot be run on the Windows dev host (WN-v36-1). A manual Mac smoke-test checklist is recorded at `docs/v3/v3.7/development/mac-smoke-test.md` with results marked `pending`. Steps 1-3 (install + `nexus-hub --version` + `nexus-hub upgrade` "up to date") also require the v3.7.0 tag to be live on `main` before they exercise the documented one-liner verbatim.

**Suggested next step**: After the v3.7.0 tag is pushed to `main`, run the checklist on a real Mac and record the results table; the new `macos-latest` CI bootstrap job covers the local-tarball path in the meantime.

**Severity**: Low (macOS bash path is auto-verified in CI; only the live-network one-liner is manual, and the bootstrap fetch logic is identical to the tarball path)

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-26`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.7`, section `Open Items`, and original ID `WN-v37-1`.

- **Migrated from**: v3.8#WN-v37-1 (reason: user-deferred); original `v3.8#WN-v37-1`, section `Open Items`.

#### Original source: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**Category**: WN

**Source**: carried from v3.7.0

**Reason**: The live `curl \| bash` one-liner against GitHub cannot be exercised in CI or on the Windows dev host. The v3.7.0 tag is now live on `main`, so the documented one-liner can finally be exercised verbatim on a real Mac.

**Suggested next step**: Run the recorded macOS smoke-test checklist ([docs/archives/v3/v3.7/development/mac-smoke-test.md](../../../archives/v3/v3.7/development/mac-smoke-test.md)) on a real Mac and record the results.

**Severity**: Low (the macOS bash path is auto-verified in CI; only the live-network one-liner is manual).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-26`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.8`, section `Open Items`, and original ID `WN-v37-1`.

- **Migrated from**: v3.9#WN-v37-1 (reason: user-deferred); original `v3.9#WN-v37-1`, section `Open Items`.

#### Original source: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**v4.13.11 structural audit, 2026-10-09**: This heading preserves the historical table obligation and every original field below. Existing historical dispositions remain as written; an unsupported transfer marker is not a verified migration.

**ID**: WN-v37-1 - MIGRATED to v4.13 (AR-26)

**Category**: WN

**Source**: carried from v3.7.0 / v3.8.0

**Reason**: The live `curl \| bash` one-liner against GitHub cannot be exercised in CI or on the Windows dev host. v3.9.0 made no installer change, so the v3.7.0 smoke-test checklist remains the verification path.

**Suggested next step**: Run the recorded macOS smoke-test checklist ([docs/archives/v3/v3.7/development/mac-smoke-test.md](../../../archives/v3/v3.7/development/mac-smoke-test.md)) on a real Mac if not yet done.

**Severity**: Low (the macOS bash path is auto-verified in CI; only the live-network one-liner is manual; unaffected by v3.9.0).

**Canonical transfer, 2026-10-09 (v4.13.11 T007)**: The complete source title and body are preserved under `v4.13.0#AR-26`. This tracking-origin migration does not claim the remaining work is implemented. The destination retains the source patch `v3.9`, section `Open Items`, and original ID `WN-v37-1`.

- **Migrated from**: v4.13#AR-26 on 2026-10-13 (reason: user-deferred)
- **Migration evidence**: AR-26 needs the macOS smoke checklist and a live --branch install on a real macOS host; the v4.13.11 host is Windows only and CI covers only the local tarball bootstrap.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
