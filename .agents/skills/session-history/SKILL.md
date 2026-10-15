---
name: session-history
description: Generate a comprehensive, standalone session history document at the end of a development session capturing chronological steps, troubleshooting, assumptions, testing results, decisions, error timelines, command outcomes, verification evidence, unresolved blockers, and next steps. Use when finishing a coding session, documenting a development phase, creating handoff context for the next session, writing a troubleshooting narrative, or recording a chronological work log. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/.
summary_l0: "Write standalone session histories only in release-scoped evidence trees"
overview_l1: "This skill generates comprehensive session history documents at the end of a development session or retrospectively from archived sources. Use it when finishing a coding session, documenting a completed phase, creating handoff context for the next session, or reconstructing history from git and past session files. Key capabilities: conversation context mining, git delta analysis, plan cross-referencing with TODO tracking, troubleshooting trails with actual error messages, assumption tracking, verification gate tables, plan discrepancy detection, and next-steps generation. It operates in session mode (mines the live conversation) and retrospective mode (reconstructs from archived session files, git, DEVLOG, and plans). Output is a standalone Markdown file with 9 sections: Starting State, Chronological Steps, Verification Gate, Known Issues, Plan Discrepancies, Assumptions Made, Testing Summary, TODO Tracker, and Summary and Next Steps. Trigger phrases: session history, document session, session recap, end of session, session summary, session log, generate session history. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Session History

Generate a comprehensive, standalone session history document that captures everything accomplished in a development session: what was done, what was troubleshot, what assumptions were made, what was tested, and what remains.

The output file is designed to be readable months later by a different developer or AI assistant, without access to the original conversation. It serves as both a durable record and a handoff document.

## When to Use This Skill

Use this skill when you need to:

-   Document what happened at the end of a development session before closing the chat
-   Record a completed phase of an implementation plan with full traceability
-   Create handoff context for the next developer or AI assistant
-   Preserve troubleshooting trails that would otherwise be lost when the session ends
-   Capture a session that involved significant debugging or decision-making
-   Resume work in a future session with full context of where things left off
-   Reconstruct development history from past session files and git history (retrospective mode)

**Trigger phrases**: "session history", "document this session", "session recap", "end of session summary", "what did we do", "generate session history", "document this phase", "development history"

## What This Skill Does

### Core Capabilities

| Capability | Description |
|---|---|
| Conversation Mining | Extract steps, errors, decisions, and assumptions from the live chat session |
| Git Delta Analysis | Identify commits, branches, PRs, and file changes within the session window |
| Plan Cross-Reference | Compare completed work against the implementation plan to track subtask progress |
| Troubleshooting Documentation | Capture failed attempts, actual error messages, root causes, and resolutions |
| Assumption Tracking | Record both explicit assumptions ("I'm assuming X") and implicit ones (library choices, skipped checks) |
| Verification Gate | Structured pass/fail table for every check performed during the session |
| Testing Summary | Aggregate automated test results. Emit manual testing suggestions only when the session is the plan's last phase, or when there is no plan. Non-final phase histories record automated results only and may say "human QA is deferred to the last phase". |
| TODO Tracking | Show done, remaining, and deferred items aligned with the implementation plan |
| Next-Steps Generation | Prioritized list of what the next session should tackle first |

### Operating Modes

**Session mode** (default): Run at the end of the current chat session. The live conversation is the primary and richest source of information, supplemented by git changes since the session started. Produces one file for the current session.

**Output path**: resolve `<version_dir>` through `[[docs-layout-refactor]]`, then write `<version_dir>/development/history/<YYYY-MM-DD>_<slug>.md`. Session histories are frozen-at-close release evidence: never write them into a living subtree such as `docs/handbooks/` or an append-only subtree such as `docs/decisions/`.

**Retrospective mode**: Reconstruct history from archived AI session files (Claude Code, Codex, Gemini, Copilot), git history, DEVLOG.md, CHANGELOG.md, and planning documents. Can produce one file per phase. Use this when the session has already ended and the conversation context is no longer available.

**Summarize from here (mid-session handoff)**: Produce a compact handoff message *just before* invoking `/rewind` or `/clear`, so the next session starts with the current session's learnings as its opening context. Distinct from the full session-history file - this mode emits a short paste-ready message, not a 9-section document. Use when the current session is about to reset but the work is still live.

- **Purpose**: Carry decisions and the next concrete step across a `/rewind` or `/clear` boundary, without the raw tool outputs and exploration noise that made the reset necessary.
- **Trigger**: The user says "summarize from here" or invokes the skill with a `--handoff` intent.
- **Output**: 5-10 bullets capturing (1) current task goal, (2) decisions made and why, (3) files touched with one-line purpose each, (4) known blockers or open questions, (5) next concrete step. No verification tables, no TODO tracker - those belong in the full session-history file, not the handoff.
- **Usage pattern** (four steps):
  1. Ask the AI to "summarize from here" while the session is still healthy (before degradation sets in - see [context-degradation](../../orchestration/context-degradation/SKILL.md) for the 1M-window threshold table).
  2. AI outputs the 5-10 bullet handoff message.
  3. User runs `/rewind` (to drop recent noise) or `/clear` (to fully reset).
  4. User pastes the handoff as the opening message of the new turn; work resumes with the learnings but without the noise.
- **Cross-link**: see [SESSION_LIFECYCLE_DECISIONS.md](../../../../guides/reference/SESSION_LIFECYCLE_DECISIONS.md) section 2 ("When to `/rewind`") for the decision logic on when this handoff is the right choice vs a full `/clear` or proactive `/compact focus on X, drop Y`.

**Template for the handoff message**:

```markdown
## Handoff from prior session

**Task goal**: <one sentence - what "done" looks like>
**Live thread**: <one sentence - where we are right now>

**Decisions made**:
- <decision + one-line rationale>
- <decision + one-line rationale>

**Files touched**:
- `path/to/file.ext` - <one-line purpose>
- `path/to/other.ext` - <one-line purpose>

**Blockers / open questions**:
- <blocker or unresolved question>

**Next concrete step**: <one sentence - the exact next action>
```

## Mid-Task Handoff Worksheet and Git Tags

Beyond the retrospective history, keep a live HANDOFF WORKSHEET when a task may span sessions or be handed to another agent: a committed artifact detailed enough that a DIFFERENT agent could resume mid-task if this one fails partway. Structure it as Goal, Plan reference, State/progress so far, Next concrete action, Open questions, and Verification status. Commit it with the work (not as a scratch file) so the trail stays connected and referenceable later.

Git-tag convention: tag the commit that carries a worksheet with a predictable name - `worksheet/<slug>` - so a specific in-progress state is retrievable by name (`git tag --list 'worksheet/*'`, then `git show worksheet/<slug>`), which is exactly what a resuming agent needs. Keep it advisory and lightweight: a one-paragraph worksheet beats none, and not every session needs one.

## Output Template

Each session history file follows this structure. All 9 sections must be present; sections with no content should state "None identified" or "N/A" rather than being omitted.

```markdown
# Development Log: [Phase Name or Task Name]

**Date**: YYYY-MM-DD [or range: YYYY-MM-DD to YYYY-MM-DD]
**Operator**: [Name]
**Assisted by**: [AI model and platform]
**Objective**: [1-2 sentences from plan or user description]
**Outcome**: [1-2 sentence summary of what was achieved, version tags if applicable]

---

## 1. Starting State

- **Branch**: `<branch>` [ahead of `<base>` by N commits]
- **Starting tag/commit**: `<ref>`
- **Environment**: [OS, runtime versions, relevant tools/containers]
- **Prior session reference**: [path to previous session history file, or "first session"]
- **Plan reference**: [path to implementation plan, or "no plan file"]

Context: [2-3 sentences on what motivated this session's work]

---

## 2. Chronological Steps

### 2.1 [Subtask name from plan, or descriptive title]

**Branch**: `<branch>` | **PR**: #NNN | **Merged to**: `<target>`

**Plan specification**: [What the plan said to do, if a plan exists]

**What happened**: [Narrative of what was implemented, key decisions made]

**Key files changed**: `file1.py`, `file2.ts`

**Troubleshooting**: [If issues occurred]
- **Problem**: [What broke, with actual error messages]
- **Attempted**: [What was tried first]
- **Root cause**: [Why it happened]
- **Resolution**: [What fixed it]

**Verification**:
[command and output showing success]

---

### 2.2 [Next subtask]
...

---

## 3. Verification Gate

| Check | Result |
|---|---|
| [Test suite or command] | PASS / FAIL / NOT RUN |
| [Lint check] | PASS / FAIL / NOT RUN |
| [Build check] | PASS / FAIL / NOT RUN |
| [Custom acceptance check] | PASS / FAIL |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| [Description] | [P0/P1/P2/Cosmetic] | [Deferred / Accepted / Workaround] |

(or: "None identified during this session.")

---

## 5. Plan Discrepancies

- [Deviation from original plan and why]

(or: "None; all work followed the implementation plan.")

---

## 6. Assumptions Made

- **[Assumption]**: [Why it was made and potential impact if wrong]

---

## 7. Testing Summary

### Automated Tests
- [Suite name]: X passed, Y failed, Z skipped

### Manual Testing Performed
- [Last phase or no plan: what was manually verified and result. Non-final phase: "None; human QA is deferred to the last phase."]

### Manual Testing Still Needed
- [Last phase or no plan: checklist of scenarios requiring manual verification. Non-final phase: write "human QA is deferred to the last phase" and do not list scenarios.]

---

## 8. TODO Tracker

### Completed This Session
- [x] [Subtask from plan or derived task]

### Remaining (Not Started or Partially Done)
- [ ] [Subtask with notes on current state]

### Out of Scope (Deferred)
- [ ] [Item deferred to a later phase, with reason]

---

## 9. Summary and Next Steps

[2-4 sentence summary of what was achieved and the current state]

**Next session should**:
1. [First priority]
2. [Second priority]
3. [Third priority]
```

## Synthesis Rules

These rules govern how information is extracted and assembled into the output file.

### Source Priority (Session Mode)

1.  **Live conversation context** -- primary source for troubleshooting, assumptions, decisions, and error messages
2.  **Git commits and diffs** -- authoritative for file changes, timestamps, and branch/PR state
3.  **Implementation plan** -- authoritative for subtask names, acceptance criteria, and TODO alignment
4.  **DEVLOG.md / prior session files** -- provide starting state context and continuity
5.  **Code annotations** (TODO, FIXME, HACK) -- signal incomplete work or workarounds introduced this session

### Source Priority (Retrospective Mode)

1.  **Archived AI session files** -- richest source when available (Claude Code JSONL, Codex logs, Gemini logs, Copilot chat history)
2.  **Git history** -- authoritative timeline; cross-reference with session timestamps
3.  **DEVLOG.md / CHANGELOG.md** -- version boundaries and troubleshooting context
4.  **Implementation plan** -- phase structure and subtask definitions
5.  **ADR files and documentation** -- decision rationale
6.  **Code annotations** -- dead-end signals and workaround markers

### Content Rules

-   **Never fabricate**. If a section cannot be populated from available evidence, state so explicitly (e.g., "No troubleshooting occurred for this step" or "*(Inferred from commit messages only; conversation context unavailable)*").
-   **Flag thin evidence**. When a section is populated from a single, low-detail source, add an inline note: *(Inferred from git commit messages only)* or *(No session data available for this step)*.
-   **Include actual errors**. Troubleshooting entries must contain the real error message, stack trace fragment, or failing test output. "There was an error" is never sufficient.
-   **Capture implicit assumptions**. These include: choosing a library version not specified in the plan, skipping a test because of an environment constraint, assuming a service is running, and treating a requirement as out of scope.
-   **Manual testing suggestions** are last-phase (or no-plan) only. When the session is a non-final plan phase, record automated test results only and write "human QA is deferred to the last phase". When the session is the plan's last phase, or there is no plan, prioritize user-facing workflows that automated tests cannot cover, external service integrations, edge cases requiring specific data or environment conditions, and scenarios where the fix might have introduced regressions.
-   **TODO tracker alignment**. In session mode with a plan, every subtask in the plan's current phase should appear in the TODO Tracker as completed, remaining, or deferred. If no plan exists, derive TODOs from conversation topics and git commit subjects.
-   **Cross-reference timestamps**. Every entry in Chronological Steps should correspond to at least one git commit. If a step produced no commits (e.g., research or manual testing), note "No commits; manual/exploratory work".
-   **Source attribution** (retrospective mode). Each section should note its evidence source: *(from git)*, *(from Claude Code session)*, *(from DEVLOG)*, etc.

## Platform-Specific Guidance

### Claude Code
Full conversation context is available in the current session. Git commands available via Bash tool. Can read implementation plan files directly. Session files for past conversations are stored in `~/.claude/projects/` as `*.jsonl` files.

### Codex CLI (OpenAI)
Conversation context is available within the current session. Git and file operations available. Past session logs may be in `~/.codex/` or `~/.openai/`. Use `AGENTS.md` context for plan references.

### Gemini CLI
Conversation history is accessible in the current session. Git and file operations available. Use `@` file references to pull in plan documents. Past sessions may be in `~/.gemini/` or `~/.config/gemini/`.

### GitHub Copilot Chat
Conversation context is available within the VS Code chat panel. Git operations via integrated terminal. Use `#file` references for plan documents. Workspace context is automatically included. Past sessions may be in `.vscode/chatHistory.json`.

## Handling Edge Cases

### No Implementation Plan Available
Derive structure from conversation topics and git commits. Use "Ad-hoc Development Session" as the session title. The TODO Tracker section uses conversation-derived items instead of plan subtasks. Plan Discrepancies section shows "N/A -- no plan file referenced".

### No Git Repository
Document the session from conversation context only. Flag all sections that would normally use git data: "*(No git repository; based on conversation context only)*". Chronological Steps uses conversation flow instead of commit timestamps.

### Very Short Session (1-2 Commits)
Produce a condensed format. Sections 4-6 (Known Issues, Plan Discrepancies, Assumptions) may be collapsed into a single "Notes" section if they would all be empty or trivial. Do not pad with filler.

### Multi-Day Session
Use the date range format "YYYY-MM-DD to YYYY-MM-DD" in the header. Session start point should reference the earliest commit or the start of the first day's work.

### Multiple Branches Worked On
Create subsections within Chronological Steps grouped by branch. Note merge ordering and any conflicts between branches.

### Retrospective Mode With No Session Files
Rely on git history, DEVLOG, CHANGELOG, and planning documents. Flag all troubleshooting and decision sections as low-confidence: "*(Reconstructed from git history; no session data available)*". Recommend the user review and enrich flagged sections.

### Session With No Code Changes
Document research, planning, or investigation sessions. Note "No code changes were committed this session" in the Starting State. Chronological Steps captures the research or discussion topics instead.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I remember the session well enough to summarize it from memory" | Memory compresses away the failed attempts and exact error strings that make a handoff useful; the next session repeats the same dead ends because the trail was never recorded. |
| "Ask the user to click through the feature after Phase 1" | The feature is incomplete. Non-final session histories record automated results only and say "human QA is deferred to the last phase"; manual testing suggestions wait until the last phase. |
| "An empty section can just be dropped" | Dropping a section hides whether it was empty by design or forgotten; emit all 9 sections with "None" or "N/A" so a reader can trust the document is complete. |
| "I can describe the error in my own words instead of pasting it" | Paraphrased errors are unsearchable and lossy; the actual error message is what the next developer greps for, so capture it verbatim. |

## Verification

Before finalizing the output file, verify:

- [ ] Every git commit from the session window appears in at least one Chronological Steps subsection
- [ ] Troubleshooting entries include actual error messages, not just descriptions
- [ ] Assumptions section captures both explicit and implicit assumptions
- [ ] TODO Tracker aligns with the plan's subtask list (if a plan exists)
- [ ] Verification Gate has a result for every check that was performed
- [ ] Testing Summary records automated results; manual testing suggestions appear only on the last phase of a plan (or when there is no plan); non-final phases say "human QA is deferred to the last phase"
- [ ] The file exists at `<version_dir>/development/history/<YYYY-MM-DD>_<slug>.md` and no session history was written into a living or append-only subtree
- [ ] No fabricated content; thin sections are explicitly flagged
- [ ] The file is standalone -- readable without access to the conversation
- [ ] All 9 sections are present (with "None" or "N/A" for empty sections)
- [ ] Dates and commit hashes are accurate (cross-referenced with git)
- [ ] File naming follows the convention: `<YYYY-MM>_<kebab-title>.md`

## Related Skills

-   [[devlog-generation]] -- retroactive full-project DEVLOG.md from git history (different output format and purpose)
-   [[plan-before-code]] -- creating the implementation plan that this skill cross-references
-   [[research-plan-implement]] -- RPI workflow with artifact generation and quality gates
-   [[code-commit-workflow]] -- commit conventions that feed into session history timestamps
-   `docs/policy/docs-retention.md` -- the lifecycle of the files this skill writes: they stay in place at release with the DEVLOG index line as their entry point, and the `development/` subtree is archived once its minor version falls two or more behind current
-   [[documentation-consistency]] -- verifying documentation stays in sync with code changes
-   [[session-teach-back]] -- this skill writes the session record; session-teach-back quizzes you on what that session produced to confirm you understood it
-   See also: [SESSION_LIFECYCLE_DECISIONS](../../../../guides/reference/SESSION_LIFECYCLE_DECISIONS.md) -- the "summarize from here" handoff pattern and when to pair session-history output with `/rewind` or `/clear`

---

**Version**: 1.0.0
**Last Updated**: March 2026


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1.  **Execute**: Perform the core steps defined above.
2.  **Review**: Critically analyze the output (coverage, quality, completeness, standalone readability).
3.  **Refine**: If targets are not met, revisit specific sections with improved context from additional sources.
4.  **Loop**: Continue until the quality checklist is satisfied.
