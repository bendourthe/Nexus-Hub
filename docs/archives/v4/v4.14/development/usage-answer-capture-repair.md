# Usage Answer Capture Repair

Date: 2026-11-02. Publication branch: `fix/usage-answer-capture-publish`, initially refreshed onto develop at `92face60b` and then onto the v4.14.7 release merge `bd2c558ba`. All seven qualified runtime and regression blobs are byte-identical across that final base refresh. The initially approved repair remains in `fix/usage-answer-capture` at base `bd49b4cf32bd0e755aa1497ca39a717c8380bec6`. The publication tree preserves upstream later-session status notices and the removed default completion gate. The main checkout and its unrelated edits remain separate.

## Defect

An offered usage decision was injected on every hook event, including blocking Stop events. Answer persistence required agent-run claim, request and response transitions. Claude's question tool does not provide the agent all those identifiers, and an auto-mode spending classifier can reject those commands. Choosing credits in the question UI therefore left the ledger pending. The CLI also treated claude-code and claude as different platforms.

## Repair

- Capture a submitted choice from the existing wildcard PostToolUse registration before probing usage. Match its question to the current decision marker or question ID. Claude's answers map, Codex's structured answers, and Cursor's question/option IDs are supported. Typed exact answers are captured on UserPromptSubmit, and Cursor registers the guard on beforeSubmitPrompt for capture without injected context.
- Persist the answer under the existing project/platform ledger. Local receipt keys identify captured events without claiming to be host-issued IDs. Ignore unrelated results, stale question IDs, cancellations, empty acknowledgments and prose that merely mentions credits. Answers remain immutable.
- Save the first instruction-delivery mark before emitting it. Repeated events stay silent. Stop may block once only when it is the first delivery. stop_hook_active=true and Cursor loop_count greater than zero return silently before probing.
- Canonicalize provider aliases and resolve the same Git root or non-git directory in hooks and CLI. Failed legacy lookups report the stored platform, project and decision ID.
- Add nexus-hub usage status and nexus-hub usage decide --answer wait|handoff|credits. Selection must identify one pending decision. The installed launcher invokes the guard in-process; no script-path Python command is required. Stdin imports use the explicit NEXUS_USAGE_GUARD_DIR when no script directory exists.
- Retain plain text questions when a native tool or legacy claim cannot succeed. Never run recovery on the user's behalf or infer credits from silence.

The first 19 regression cases failed against the unchanged guard and passed after the repair. The original 50 native-decision cases passed before implementation. Final Windows qualification consists of a 698-test broad run and a 298-test final-source usage recheck. These sets overlap and must not be added together.

Those runs qualify the initial repair. Publication review added durable first-answer receipts, capture-only Copilot prompt handling, legacy identity migration, older installed-helper discovery and trusted stdin imports. Final broad publication qualification passes 763 cases with zero failures or skips in 763.79 seconds, including the Windows launcher, Cursor integration and CLI regression suites. The 18-check fast profile also passes with zero failures or skips. An export of the staged distributed runtime trees passes all 106 focused integration cases, including 45 new capture regressions, in 72.08 seconds. These current-source results supersede the initial-source evidence for changed behavior; overlapping sets are not added together.

## Functional Evidence

The executable exercises use temporary homes and projects. They never answer or alter a live spending decision.

| Boundary | Input and observed result | Evidence |
|---|---|---|
| Actual Python hook process | Cached weekly usage at 100 percent creates one instruction. A tagged AskUserQuestion result with Continue on credits persists credits. The next Stop and PostToolUse emit nothing. A prior Stop continuation and malformed unrelated tool result also emit nothing. | test_real_hook_sequence_records_answer_and_stays_silent |
| Packaged Windows launcher | A temporary bin/nexus-hub.cmd, scripts core and hook package answer a pending decision in a non-git OneDrive-style path with spaces using --platform claude-code. Exit 0; the ledger records credits under claude. | test_packaged_windows_launcher_recovers_non_git_project |
| Source CLI and stdin | The source CLI persists a genuine fixture recovery answer. The guard piped to python - resolves its sibling module and reports the already-answered state instead of ModuleNotFoundError. | test_user_recovery_entry_point_and_stdin_imports |
| Console-window pre-hook | The new user CLI command and the stdin Python entry form both pass the actual console-window-guard executable with exit 0 and no rejection. | test_console_guard_allows_recovery_entry_points |
| Reminder/reset lifecycle | Captured credits stay silent below the next tier; 50, 75 and 90 percent each emit one reminder. Stop remains silent. A new usage reset creates a new pending decision. Another project receives its own decision. | test_captured_credits_remind_at_tiers_and_rotate_after_reset; test_captured_credits_replay_and_project_scope |

All five boundary exercises passed in the expanded regression module. They establish executable behavior with fixture readings, not a rendered host question or real spending-meter observation.

## Checks

Final affected test command:

```powershell
python -m pytest catalog/hooks/tests/test_usage_answer_capture.py catalog/hooks/tests/test_usage_native_decision.py catalog/hooks/tests/test_usage_guard.py catalog/hooks/tests/test_completion_gate_usage_handoff.py catalog/hooks/tests/test_hook_sibling_parity.py tests/integrations/test_cursor.py tests/installer/test_native_cli_launcher.py -q --tb=short
```

Result: 698 passed, zero failed, zero skipped in 637.01 seconds. During review, the expired-answer history warning was restricted to tool events so that it cannot block the same decision again at Stop. After that last scoped correction, every affected usage module was rerun on the final source:

```powershell
python -m pytest catalog/hooks/tests/test_usage_answer_capture.py catalog/hooks/tests/test_usage_native_decision.py catalog/hooks/tests/test_usage_guard.py -q --tb=short
```

Result: 298 passed, zero failed, zero skipped in 127.95 seconds. This includes all 31 new regression cases. Unchanged completion-gate, sibling-parity, Cursor integration and launcher results come from the broader run. This is split qualification, not a single final-source all-suite claim.

Ruff comparison against the base reports zero introduced diagnostics: two existing in usage-guard.py, four existing in nexus_hub_cli.py and one existing in the Cursor integration. The new regression module is clean. Skill bundle validation passes with zero errors and 66 warnings. Registry consistency passes. The changed Markdown passes strict Unicode validation, and the checked guide/test paths pass the personal-path validator. git diff --check passes. Initial edit-guard checks needed no baseline accepts; the later publication-stage write-window recovery is recorded below.

Initially qualified distributed Git-blob SHA-256 values, exercised from the exported runtime; the later fixture correction is recorded below:

| Path | SHA-256 |
|---|---|
| catalog/hooks/usage-guard.py | 1741642e35644e584c0a53953b98ce04975414ca69955502fa59c8f037451c86 |
| scripts/nexus_hub_cli.py | 1d9913239632ed7c790f52c2a7307601d688946a9f166d06b9c43e78a3fd4f74 |
| scripts/lib/integrations/cursor.py | 63a2233c0e109088f3b1c5996b28b02864108dce68c2ba8cf8efbdf492e16207 |
| catalog/hooks/tests/test_usage_answer_capture.py | c5504fc96a5292c1ee92fe8ff0b47abe179756b360452b09c3e7752499222240 |

## Credential Isolation Correction

The Windows CI hook group on `93719263e` reported 3182 passed, one failed and 15 skipped. The sole failure was the real subprocess sequence's initial offer. Its cache fixture used `private-fixture` as the source, which the real probe correctly rejects. Earlier local passes could fall back to available Claude credentials instead of exercising that cache, so they do not establish the claimed cached subprocess boundary. The other focused results and runtime hashes remain applicable; the cached subprocess proof is withdrawn and replaced by the credential-isolated run below.

The failure was reproduced locally by giving pytest an empty `HOME` and `USERPROFILE`: the same initial offer assertion failed in 0.45 seconds. The fixture now uses the probe's accepted provider-source identifier, asserts that the cached reading contains 100 percent usage, and gives the child hook its own empty home. Hook opt-out variables are removed from that child's environment and the provider set is explicit. No runtime behavior was changed to accommodate the test.

The corrected capture and native-decision modules pass all 106 cases with zero failures or skips under the empty-home environment in 27.21 seconds. The new test module passes Ruff and the distribution manifest is regenerated. Its staged Git-blob SHA-256 is `d37369c57a006e0500e5a973b39193fbba40930bdbad589cd5ebb9773c97d563`. The guard, CLI, Cursor and handoff-skill blobs are unchanged. The protected CI suite must pass again at the new head before integration.

## Publication Review

The protected Windows hook job passes on `d735c8d25` after credential isolation. Its Linux test profile found one additional stale assertion in `tests/integrations/test_usage_guard_delivery.py`: Cursor was expected to register only postToolUse and stop, excluding the newly required beforeSubmitPrompt answer-capture event. That expectation and the test's description now include the third event, with one handler required per event. All 142 affected capture, native-decision, Cursor and delivery cases pass locally with zero failures or skips in 138.48 seconds. The actual installer remains the subject under test; no runtime code was changed to satisfy either CI correction. Focused assertion review classifies the corrected subprocess and installer cases as REAL: their checks depend on actual cache validation, child-process output, persisted decision state and emitted installer configuration. This is a narrow review of these two boundaries, not a whole-suite mutation audit.

The complete repair received ten focused lenses: correctness, maintainability, testing, project standards, security, performance, API contract, reliability, adversarial inputs and action/context availability. Eight distinct findings were corrected: Copilot prompt capture, contention loss, older helper shadowing, repository-owned stdin imports, conflicting-choice tests, the Unreleased changelog entry, queued-answer overwrite and legacy schema-3 key compatibility. Duplicate contention findings were combined before triage. No remaining reportable finding was returned after the targeted follow-up checks.

| Considered Candidate | Disposition |
|---|---|
| Recovery is deliberately user-run | Intentional; native question and typed-answer capture provide the agent path without delegating spending authorization to it. |
| Extra receipt I/O affects ordinary hook events | No directory scan or network was added to the normal path; receipt publication and fsync occur for genuine answers. No busy-host timing claim is made. |
| Local capture keys resemble host IDs | Existing readers accept the shape; documentation labels generated keys as local audit receipts. Legacy answers retain genuine request and response IDs. |
| Retaining different provider result shapes in one parser | Its responsibility is normalization and the provider-specific branches have focused rejection and acceptance tests. |
| Fixtures establish every native host behavior | Rejected as insufficient evidence; real Desktop and current host payloads remain separately open below. |

Two edit-guard baseline refreshes recovered a write-window expiry for catalog/hooks/usage-guard.py and catalog/hooks/tests/test_usage_answer_capture.py. The official diffs contained only the approved repair's own writes, including the retained upstream changes. They were inspected before accept; no unrelated user edits were overwritten. Authority was the user's explicit approval to continue the repair, not a fabricated native plan receipt.

## Source Contracts

The hook field and loop checks follow the [Claude hook reference](https://code.claude.com/docs/en/hooks). Claude's submitted answers map follows the [Agent SDK Python tool reference](https://code.claude.com/docs/en/agent-sdk/python). Cursor's JSON-stringified tool_output is documented in its [hook reference](https://cursor.com/docs/hooks); its nested outcome and selectedOptionIds are documented in the [question schema](https://cursor.com/docs/cli/acp). These references were checked on 2026-11-02. Codex result handling is covered by structured fixtures; no new live host capture is claimed.

## Open Checks

- PR #599 publishes the repair. Its first validation run exposed stale distribution-handbook evidence for the changed CLI and Cursor adapter. The handbook now explains recovery in both views, tracks the guard as an input and carries a fresh content/build/browser review. The runtime blobs qualified above are unchanged by the documentation and test corrections. Protected integration remains pending until the current head passes all required checks.
- The approved local hotfix is installed from published candidate `d735c8d25`: sixteen managed files were backed up, checked and updated under the runtime activity lock. The actual CLI finds the existing pending Claude decision using claude-code. Temporary-ledger exercises of the installed Claude, Codex and Cursor hooks each persist credits and leave subsequent tool and Stop events quiet. The live ledger and VERSION are unchanged. This is a component hotfix on 4.14.5, not a release installation; installation proceeded before protected integration to end the interruption while CI reruns. Local backups and receipts are retained under the account's `.nexus-hub/state/runtime-adoptions/usage-answer-d735c8d25-20261102` directory.
- Verify one genuine Claude Code Desktop question at the limit after adoption: choose the desired answer once, inspect the project ledger, then observe that subsequent Stop and tool events stay quiet.
- Observe native Cursor and Codex result payloads after installation. Fixture coverage establishes the supported schemas, but does not prove every host version emits them. Typed replies and user-run recovery remain available.
- The existing live pending spending decision was not changed. The user can select its answer through the repaired capture flow or recovery CLI after installation.
