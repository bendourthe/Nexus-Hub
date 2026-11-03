# Native Per-Plan Session Transfer

Summary: the separately authorized repair for resuming a signed per-plan run in another session, its local qualification and its pending genuine resume decision. This is release evidence for the coordinator; it does not grant publication, change approval classes or reset limits.

## Scope

The maintainer authorized this repair on 2026-11-02 after the installed renderer refused to resume v4.14.7 in the new session. Work began in the isolated `fix/native-session-transfer` worktree from develop `d28425cbddb236ec7874b9dd784a14011ef3e410`. The shared primary checkout and the release worktree's unrelated changes were preserved.

The installed command reported `no run record for this plan and session`. Two missing steps caused it: the per-plan renderer filtered out the foreign-session record before rendering resume, and the consumer required the old session even for resume. The old resume writer also cleared only the pause state, leaving the owner unchanged. Minor-level resume already implements the intended cross-session flow.

## Implementation

The existing renderer and consumer may load another session's record only for resume. Normal record verification still checks the plan identity and integrity signature. The existing approval-binding consumer still requires a genuinely captured, rendered, single-use decision in the bound session, including a prompt predating the challenge. Successful resume uses that consumer's actual session, clears the pause and re-signs the record. Pause and blocker answers retain the original-session requirement.

The regression compares every record field before and after resume, allowing changes only to `session_id`, `pause` and `approvals_hmac`. It includes a bounded repush approval, a zero-dollar spending cap and an open technical blocker. Both explicit-session and automatic-session resolution must preserve all other fields; the blocker must remain open and the resulting signature must verify.

construction-debt: reuse the existing native capture and signing functions; add no command, dependency or record schema. No installed native file or live run record was hand-edited.

## Verification

| Stage | Result |
|---|---|
| Original-session baseline | 2 passed: the existing session-filter and pause/blocker/resume cases |
| Corrected regressions before the implementation | 2 failed at the intended boundaries: explicit rendering could not find the record, and automatic resume rejected the new capture as a session mismatch |
| Focused repaired flow | 9 passed, 181 deselected in 72.42 seconds |
| Broader approval regressions | 107 passed, 479 deselected in 456.64 seconds; runner-generated JUnit report retained outside the repository |
| Ruff on changed Python files | Four diagnostics, all reproduced at the same locations from untouched HEAD; zero introduced diagnostics |
| Whitespace | `git diff --check` passed |

The first new-test run also exposed two malformed spending-cap fixtures; those fixtures were corrected and the two preservation cases were rerun before implementing the repair. The passing focused cases exercise actual checker CLI processes, disposable Git repositories, disposable run stores and a hosting-service stub. Their synthetic capture events exist only in those disposable fixtures and are not live user authority. All test launchers used the pinned interpreter and the verified windowless process helper. The broader test runner writes its own JUnit artifact outside the repository.

The command for the broader scope is the four existing validator modules `test_check_plan_completion.py`, `test_approval_binding.py`, `test_approval_page.py` and `test_completion_minor_record.py`, selected with `resume or pause or session or tamper or record_create or capture`. This covers the changed flow and its shared capture readers without claiming an unfiltered repository-wide test pass.

## Focused Security Review

Four of four components in the repair target were reviewed; none were omitted or left uncovered within that target. This is a manual review of the patch and its approval flow, not a complete scanner-based audit of Nexus-Hub.

| Component | Status | Review action and result |
|---|---|---|
| `scripts/check_plan_completion.py` | COVERED | Traced render, load, consume, pause, blocker answer and resume through the writer; only resume relaxes the old-owner restriction and its writer uses the captured session |
| `scripts/approval_binding.py` | COVERED | Inspected bound-session matching, pre-challenge prompt requirement, genuine capture lookup, replay refusal and integrity checks; implementation is unchanged |
| Existing checker fixture and new cases | COVERED | Inspected all-field preservation, refusal without capture, foreign capture, replay and tampered authority assertions |
| Completion contract | COVERED | Checked that the clarification preserves the existing user-origin and frozen-authority rules and describes the same flow as minor resume |

| Review level | Status | Action or omission reason |
|---|---|---|
| Whole project | OMITTED | The authorized repair concerns per-plan resume, not a repository-wide security audit |
| File by file | COVERED | Reviewed the four changed components listed above |
| Complete functionality | COVERED | Traced render to captured response to signed persistence, plus pause and blocker-answer callers of the shared helper |
| Function by function | COVERED | Inspected the changed loader, consumer return value and resume writer, with existing capture validation retained |

Considered but rejected as new findings: an unsigned record granting takeover is blocked by ordinary integrity verification; a foreign-session blocker answer retains its original-owner restriction; and replay retains the existing consumed-decision refusal. Their respective refusal paths are exercised by the selected regressions. No new dependency, network destination, secret access or cryptographic algorithm was introduced.

## Live Continuation

The current session has an existing host-created prompt-capture stream. Live transfer still requires a fresh native-rendered resume decision captured as an actual user reply. The maintainer's earlier authorization to build this repair predates that decision and is not reused as a fabricated resume capture. The repaired source can render and consume the native resume operation without editing installed helpers; the ordinary installed checker can read the resulting compatible record afterward. Publication and installed-Cursor qualification remain separate release gates.
