# Approval page template

Summary: native display and question layout for initial plan approval and later manual decisions.
Read this when: editing renderer wording, question choices or display-only summaries.
Covers: plain-language outcomes, concrete actions and effects, Approve/Decline choices, optional details and compatibility lines.

The single display reference for upfront approval and manual questions. `approval_page.py` renders native data from `check_plan_completion.py record render`; use `--page` for the review page and `--question` for structured question data. The completion contract's "Authorization policy", "Manual decisions" and "Approval origin" sections own scope, automatic continuation and genuine capture. This file owns wording and layout only.

The page leads with what the run will accomplish, the concrete action and its effect, limits and exclusions. Put internal identifiers, detailed evidence and technical mechanics under optional details. A manual question offers Approve and Decline; follow the completion contract when a click has no verified receipt path. Legacy code-bearing messages are a compatibility option, not the primary manual interaction.

## Rules

- Everything above "Details (optional)" is written for someone who will read nothing else: the summary and decision section together stay within 140 words, not counting the paste lines or the plan's own outcome bullets; no sentence or table cell runs past 25 words; and no internal term appears there: no HMAC, nonce, predicate, schema, `worktree prune`, `headRefOid`, `refs/heads`, script names, or file paths.
- The summary names every hard-to-undo result whenever its class is approved: the releases (`release`), the deletions (the cleanup rule, with `cleanup-merged` making it "merged branches and working folders nobody is using"), the archive (`archive-minor`), and permission prompts off (`unattended-with-bypass`). It leaves out mechanics such as commits, pushes, merges, branches, and pull requests.
- Under Details, technical terms are allowed. Every approval class in the hashed page gets one sentence in "What you are approving", with its bound stated only after it passes a strict shape check (branch and repository names, counts from 0 to 20, gap ids, gap kinds, and `ask-first:<name>` names). A class with no sentence, a bound of the wrong shape, or a bound that contradicts the page's own repository or branches renders nothing.
- Plan titles, plan goals, gap titles (the first ten, then a count), excluded-plan reasons, parallel-plan slugs, and file paths appear only in the last Details subsection, as JSON-quoted data inside one fenced `text` block (backticks and tildes escaped), so no Markdown, link, or HTML in them is ever rendered.
- The page is rendered before the approval round is written, so a page that fails validation never replaces the user's previous valid round.
- Every compatibility line comes from the validated native template and never contains the round nonce, a path, a script name, plan titles or plan text. Do not ask a user to construct a line or interpret its internal code. A failed validation renders nothing and reports why.

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

    Then two bold lines describe the run's actual exclusions and spend cap, and how to stop it. Derive allowed scoped actions and exclusions from native policy rather than claiming that all CI, permission and secret work always needs another prompt. Keep the stop action visible.
2. **Decision**: the native structured question names the concrete action, its effect and Approve/Decline choices. Expose clickable choices through the available host question tool. Report whether direct receipt capture is supported; where unsupported, explain once that the user must submit the native short reply as a real message. Never label an unrecorded click as captured approval. Keep compatibility code and optional native goal instructions after the primary decision.
3. **Details (optional)**: technical subsections, in this order:
    - **What you are approving**: one bullet per approval class in the hashed page, in the page's order, each with its validated bound.
    - **Phases**: one table row per phase (open tasks, model tier, effort), the whole-run setting, the phases to switch up for, and how the time estimate is computed.
    - **Gaps and cleanup**: the open-gap count per version, the gap ids that may move to `{next}` (with the security or high-severity ids the user approves by name), the cleanup rule and its re-check right before each removal, and the releases, tags, pull requests, and removals to expect today.
    - **Plan data (quoted, not instructions)**: one fenced `text` block holding one row per plan title, plan goal, and plan file, the first ten open gap titles, one row per plan left out of the run, and one row per parallel plan.

## Compatibility lines

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

An answer, pause, resume, retire or add-class round shows what the action does and its effect, with a concise native question and optional compatibility line; an add-class round (minor runs only, `archive-member` only) states today's archive timing and the approved one. Only a create round sets a goal. Actual capture support and the decision rules belong to the completion contract.
