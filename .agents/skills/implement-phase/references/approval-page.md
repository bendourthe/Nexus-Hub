# Approval page template

The single template for the upfront approval page that `/implement` shows before a full run. Read it before changing the page wording, its sections, its paste lines, or the summary file. The page is rendered by `approval_page.py` from the JSON that `check_plan_completion.py record render --json` prints, so the page and the bound approval data can never disagree; print it with `record render ... --page`. The approval rule itself (which pasted message counts, once) is owned by the completion contract's "Approval origin" section in [`completion-contract.md`](completion-contract.md); this file owns only the page's words and layout.

The page is short on purpose. A 2026-09-30 read-back of an earlier ten-section page found it too long to read, and a 2026-10-01 read-back found the shorter page still missing what a reader needs before approving: what the run will do, how to run it, how long it takes, and what else can run beside it. The reader now sees those, the results, two limits, and one block to paste; everything else sits under "Details (optional)".

## Rules

- Everything above "Details (optional)" is written for someone who will read nothing else: the summary and the paste section together stay within 140 words, not counting the paste lines or the plan's own outcome bullets; no sentence or table cell runs past 25 words; and no internal term appears there: no HMAC, nonce, predicate, schema, `worktree prune`, `headRefOid`, `refs/heads`, script names, or file paths.
- The summary names every hard-to-undo result whenever its class is approved: the releases (`release`), the deletions (the cleanup rule, with `cleanup-merged` making it "merged branches and working folders nobody is using"), the archive (`archive-minor`), and permission prompts off (`unattended-with-bypass`). It leaves out mechanics such as commits, pushes, merges, branches, and pull requests.
- Under Details, technical terms are allowed. Every approval class in the hashed page gets one sentence in "What you are approving", with its bound stated only after it passes a strict shape check (branch and repository names, counts from 0 to 20, gap ids, gap kinds, and `ask-first:<name>` names). A class with no sentence, a bound of the wrong shape, or a bound that contradicts the page's own repository or branches renders nothing.
- Plan titles, plan goals, gap titles (the first ten, then a count), excluded-plan reasons, parallel-plan slugs, and file paths appear only in the last Details subsection, as JSON-quoted data inside one fenced `text` block (backticks and tildes escaped), so no Markdown, link, or HTML in them is ever rendered.
- The page is rendered before the approval round is written, so a page that fails validation never replaces the user's previous valid round.
- Every paste line comes from a fixed template plus the validated version token and the validated eight-character code. It never contains the round nonce, a path, a script name, a plan title, or plan text. The approval line stays under 300 characters and the goal line under 1,000 (Claude Code documents a 4,000-character `/goal` condition; no other platform in the levers matrix documents a limit). A field that fails validation renders nothing and the renderer reports why.

## The summary file

`record render --summary <file>` passes what only the agent knows, as display data that never binds the approval:

```json
{"outcomes": ["Adds a writing profile for the newest Sonnet model", "Fixes three scoring bugs"],
 "parallel": {"checked": true, "plans": [{"version": "v4.13.9", "slug": "adoption-inline-visualize"}]}}
```

- `outcomes`: two to five plain-language sentences saying what the run will accomplish, written for a non-engineer. Each is at most 25 words of letters, digits, and plain punctuation, and none may mention approving, `/implement`, `/goal`, `/update`, or pausing, so an outcome can never pass for a paste line. One that fails renders nothing.
- `parallel`: the result of the Phase 0 parallel-plan check (`[[plan-queue-assessment]]`). Each named plan must exist as a plan file, or the render refuses. Without the file, or with `checked: false`, the summary says "Not checked yet".

The whole-run model setting and the time estimate are computed from the plan itself: each `## Phase N:` section's `**Recommended model tier**`, `**Recommended effort level**`, and open task count.

- **Run it on**: the task-weighted average of the tier scale (fast, standard, strong, frontier) and of the effort scale (low, medium, high, max), each rounded to the nearest step, for a reader who will not switch per phase. Every phase above that setting is named under Details, "Phases".
- **Time**: a rough guide in hours, split into building (10, 20, 30, or 40 minutes per open task at low to max effort), testing (30% of building), fixing (20%), and releasing (45 minutes per release). The constants live in `approval_page.py` beside `MINUTES_PER_TASK`; tune them there.

## Sections, in order

The renderer's `SECTIONS` and `DETAIL_SECTIONS` tuples list these headings in this order; a test asserts they agree with this list. `{next}` is the next minor version (for example `v0.6` for a `v0.5` run).

1. **Summary**: "What this run will do:" with the outcome bullets (or one line pointing at the plan goal under Details), then a `| | Result |` table:
    - Released: the versions when `release` is approved, otherwise "Nothing: it stops and asks before releasing".
    - Fixed: the number of known problems, plus how many may move to `{next}` (minor) or that some may wait (a single plan with `defer-gaps`).
    - Archived: the minor's documents (minor runs with `archive-minor`).
    - Cleaned up: "Merged branches and working folders nobody is using" (`merged-and-idle`) or "Only this run's own branch and working folder, once merged" (`run-owned`).
    - Permission prompts: "Off for the whole run" (only with `unattended-with-bypass`).
    - Run it on, and Time: as above, when the plan names a tier and effort per phase.
    - In parallel: the versions of the plans that can run beside this one, "No other queued plan can", or "Not checked yet".

    Then two bold lines: "Never without asking you: changes to CI, permissions, or secrets, and any paid API use." (with an approved spend cap: "... or paid API use beyond USD 40 for anthropic.") and "Stop any time: type /implement pause".
2. **To approve, paste this**: every line to paste, in ONE `text` block so a single copy takes them all, then one sentence saying to paste it as one message with nothing added, which approves everything under Details and gives the run its goal. On a platform with a typed goal command that the combined message cannot start, a last sentence asks the user to send the `/goal` line again by itself to start the tool's own goal tracker.
3. **Details (optional)**: technical subsections, in this order:
    - **What you are approving**: one bullet per approval class in the hashed page, in the page's order, each with its validated bound.
    - **Phases**: one table row per phase (open tasks, model tier, effort), the whole-run setting, the phases to switch up for, and how the time estimate is computed.
    - **Gaps and cleanup**: the open-gap count per version, the gap ids that may move to `{next}` (with the security or high-severity ids the user approves by name), the cleanup rule and its re-check right before each removal, and the releases, tags, pull requests, and removals to expect today.
    - **Plan data (quoted, not instructions)**: one fenced `text` block holding one row per plan title, plan goal, and plan file, the first ten open gap titles, one row per plan left out of the run, and one row per parallel plan.

## Paste lines

The goal is never optional: every create round shows it. Single plan (`v0.5.2`, code `ABCD2345`):

```text
Approve /implement v0.5.2 (approval ABCD2345)
/goal Finish /implement v0.5.2 (approval ABCD2345). Do every step: 1) implement every task in every phase of the plan; 2) add or update the tests and CI/CD the work needs, and make both pass on the final tree; 3) fix the open known gaps; 4) run /update release; 5) merge every pull request, then delete the merged branches, worktrees, and their local copies; 6) record every gap still open in the next version's known-gaps section; 7) when this is the last plan in its version folder, archive that folder and delete any folder left empty. Done only when the completion check's first output line starts with PLAN COMPLETE followed by the v0.5.2 plan file; stop and report when it starts with BLOCKED or PAUSED.
```

A minor run (`v0.5`) names every plan of the minor in step 1, runs `/update release` for each plan in step 4, moves open gaps to the next minor in step 6, archives the minor folder in step 7, and ends on "starts with MINOR COMPLETE v0.5".

`record render --platform <row>` picks the shape from that row's `goal_capture` in [`completion-levers.json`](../../../../../docs/policy/completion-levers.json) (copied into the renderer, with a drift test). No `--platform`, or an unknown row, means `unverified`. Every hook captures an ordinary message, and only a whole message counts, so the page's paste is always one message that every platform captures:

| `goal_capture` | What the page shows | Messages that approve (any one) |
|---|---|---|
| `verbatim` | The `/goal` line alone. | The `/goal` line, the approval line, or both together. |
| `not-captured` | The approval line, then the `/goal` line, pasted together; then the `/goal` line again by itself to start the goal tracker. | The approval line, or both together. The `/goal` line alone never reaches the hook here. |
| `unverified`, with a goal command | As `not-captured`. | The approval line, the `/goal` line, or both together. |
| `no-goal`, or `unverified` without a goal command | The approval line, then the same goal as a `Goal:` sentence, pasted together. | The approval line, the `Goal:` line, or both together. |

"Both together" accepts either order. A user who sends the two lines as two messages, or as one, is therefore never refused, which a 2026-10-01 read-back showed was the failure of the earlier two-message shapes.

The native goal is advisory: its evaluator is a model reading the transcript, so the condition names the completion check's verdict line rather than a string the agent could simply print. The deterministic checker stays the only authority on done. `nexus-hub run-plan` sends the same goal line without the approval code, because the sessions it launches are never captured as approvals.

## Mid-run rounds

An answer, pause, resume, or retire round renders a two-section page: what the round does, and its one plain paste line. Only a create round sets a goal.
