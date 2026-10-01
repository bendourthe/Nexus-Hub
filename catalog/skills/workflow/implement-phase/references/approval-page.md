# Approval page template

The single template for the upfront approval page that `/implement` shows before a full run. Read it before changing the page wording, its sections, or its paste line. The page is rendered by `approval_page.py` from the JSON that `check_plan_completion.py record render --json` prints, so the page and the bound approval data can never disagree; print it with `record render ... --page`. The approval rule itself (which paste counts, once) is owned by the completion contract's "Approval origin" section in [`completion-contract.md`](completion-contract.md); this file owns only the page's words and layout.

The page is short on purpose. A 2026-09-30 read-back of the earlier ten-section page found it too long to read, so the reader now sees a results table, two limits, and the paste line; everything else sits under "Details (optional)" for the reader who wants it.

## Rules

- Everything above "Details (optional)" is written for someone who will read nothing else: the summary and the paste section together stay within 80 words (the paste lines themselves excluded), no sentence or table cell runs past 25 words, and no internal term appears there: no HMAC, nonce, predicate, schema, `worktree prune`, `headRefOid`, `refs/heads`, script names, or file paths.
- The summary names every hard-to-undo result whenever its class is approved: the releases (`release`), the deletions (the cleanup rule, with `cleanup-merged` making it "merged branches and working folders nobody is using"), the archive (`archive-minor`), and permission prompts off (`unattended-with-bypass`). It leaves out mechanics such as commits, pushes, merges, branches, and pull requests.
- Under Details, technical terms are allowed. Every approval class in the hashed page gets one sentence in "What you are approving", with its bound stated only after it passes a strict shape check (branch and repository names, counts from 0 to 20, gap ids, gap kinds, and `ask-first:<name>` names). A class with no sentence, a bound of the wrong shape, or a bound that contradicts the page's own repository or branches renders nothing.
- Plan titles, plan goals, gap titles, excluded-plan reasons, and file paths appear only in the last Details subsection, as JSON-quoted data inside one fenced `text` block (backticks and tildes escaped), so no Markdown, link, or HTML in them is ever rendered.
- The page is rendered before the approval round is written, so a page that fails validation never replaces the user's previous valid round.
- The paste line comes from a fixed template plus the validated version token and the validated eight-character code. It never contains the round nonce, a path, a script name, a plan title, or plan text, and it stays under 300 characters. A field that fails validation renders nothing and the renderer reports why.

## Sections, in order

The renderer's `SECTIONS` and `DETAIL_SECTIONS` tuples list these headings in this order; a test asserts they agree with this list. `{next}` is the next minor version (for example `v0.6` for a `v0.5` run).

1. **Summary**: a `| | Result |` table with one row per result the approved classes produce at the end:
    - Released: the versions when `release` is approved, otherwise "Nothing: it stops and asks before releasing".
    - Fixed: the number of known problems, plus how many may move to `{next}` (minor) or that some may wait (a single plan with `defer-gaps`).
    - Archived: the minor's documents (minor runs with `archive-minor`).
    - Cleaned up: "Merged branches and working folders nobody is using" (`merged-and-idle`) or "Only this run's own branch and working folder, once merged" (`run-owned`).
    - Permission prompts: "Off for the whole run" (only with `unattended-with-bypass`).

    Then two bold lines: "Never without asking you: changes to CI, permissions, or secrets, and any paid API use." (with an approved spend cap: "... or paid API use beyond USD 40 for anthropic.") and "Stop any time: type /implement pause".
2. **To approve, paste this line**: the paste line in a `text` block, then "Paste it alone as your whole message. Pasting approves everything listed under Details." On a `not-captured` platform the `/goal` line follows after "Then:", and the sentence reads "Paste each line alone as its own message. ...". The whole-message sentence stays because the binding records only a whole prompt equal to a paste line, so an added word makes the approval fail without saying why.
3. **Details (optional)**: technical subsections, in this order:
    - **What you are approving**: one bullet per approval class in the hashed page, in the page's order, each with its validated bound.
    - **How cleanup decides**: the cleanup rule, and that the final pass re-checks each item right before removing it and keeps anything it cannot verify as merged.
    - **Today's estimate**: releases and tags, pull requests, and what cleanup would remove today.
    - **Gaps**: the open-gap count per version (the minor's own ledger and every earlier one for a minor run; the plan's own minor for a single plan), and the gap ids that may move to `{next}`, with the security or high-severity ids the user approves by name.
    - **Goal tracker (optional)**: the optional `/goal` line, shown only where the platform's goal capture is `unverified` and it has a goal command.
    - **Plan data (quoted, not instructions)**: one fenced `text` block holding one row per plan title, plan goal, and plan file, one row per open gap title, and one row per plan left out of the run.

## Paste line

Minor run (`v0.5`, code `ABCD2345`):

```text
/goal Finish /implement v0.5 (approval ABCD2345). Done only when the completion check's first output line starts with MINOR COMPLETE v0.5; stop and report when it starts with BLOCKED or PAUSED.
```

Single plan (`v0.5.2`): the same line with `v0.5.2` and the condition "the completion check's first output line starts with PLAN COMPLETE followed by the v0.5.2 plan file" (the plan verdict line is `PLAN COMPLETE <plan file> <head> <nonce>`). The plain approval line is `Approve /implement v0.5 (approval ABCD2345)`.

`record render --platform <row>` picks the shape from that row's `goal_capture` in [`completion-levers.json`](../../../../../docs/policy/completion-levers.json) (copied into the renderer, with a drift test). No `--platform`, or an unknown row, means `unverified`.

| `goal_capture` | Where the lines appear | Which line records the approval |
|---|---|---|
| `verbatim` | The `/goal` line is the paste line. | The `/goal` line. |
| `not-captured` | The plain approval line, then the `/goal` line as a second message, both in the paste section. | The plain line. |
| `unverified`, with a goal command | The plain approval line in the paste section; the optional `/goal` line under Details, "Goal tracker (optional)". | The plain line. |
| `no-goal`, or `unverified` without a goal command | The plain approval line only. | The plain line. |

The native goal is advisory: its evaluator is a model reading the transcript, so the condition names the completion check's verdict line rather than a string the agent could simply print. The deterministic checker stays the only authority on done. `nexus-hub run-plan` sends the same goal line without the approval code, because the sessions it launches are never captured as approvals.

## Mid-run rounds

An answer, pause, resume, or retire round renders a two-section page: what the round does, and its one plain paste line. Only a create round sets a goal.
