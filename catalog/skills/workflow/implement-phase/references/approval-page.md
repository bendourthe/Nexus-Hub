# Approval page template

The single template for the upfront approval page that `/implement` shows before a full run. Read it before changing the page wording, its sections, or its paste line. The page is rendered by `approval_page.py` from the JSON that `check_plan_completion.py record render --json` prints, so the page and the bound approval data can never disagree; print it with `record render ... --page`. The approval rule itself (which paste counts, once) is owned by the completion contract's "Approval origin" section in [`completion-contract.md`](completion-contract.md); this file owns only the page's words and layout.

## Rules

- Each section has two to five short sentences in everyday words, and no sentence runs past 25 words. The numbered steps in "What will happen, in order" are one short sentence each.
- Above the paste line, no internal term appears unless it is defined in place: no HMAC, nonce, predicate, schema, `worktree prune`, `headRefOid`, `refs/heads`, script names, or file paths. "Worktree", "pull request", "gap", and "CI" are defined in parentheses or in their own sentence the first time they appear.
- Plan titles, plan goals, gap titles, excluded-plan reasons, and file paths appear only in the details list after the paste line, as JSON-quoted data inside one fenced `text` block (backticks and tildes escaped), so no Markdown, link, or HTML in them is ever rendered. Nothing from a plan or a ledger reaches a section or the paste line.
- Every approval class in the hashed page gets one plain sentence in "What you are approving", with its bound stated only after it passes a strict shape check (branch and repository names, counts from 0 to 20, gap ids, gap kinds, and `ask-first:<name>` names). A class with no sentence, a bound of the wrong shape, or a bound that contradicts the page's own repository or branches renders nothing.
- The page is rendered before the approval round is written, so a page that fails validation never replaces the user's previous valid round.
- The paste line comes from a fixed template plus the validated version token and the validated eight-character code. It never contains the round nonce, a path, a script name, a plan title, or plan text, and it stays under 300 characters. A field that fails validation renders nothing and the renderer reports why.
- The first two lines under the first heading state the releases the run will publish and that it will delete merged branches after checking each one.

## Sections, in order

The renderer's `SECTIONS` tuple lists these headings in this order; a test asserts the two agree. `{next}` is the next minor version (for example `v0.6` for a `v0.5` run).

1. **The two biggest things this will do**: "It will publish N releases: {versions}." (only when `release` is approved; otherwise "It will not publish {versions} without asking you first.") and "It will delete merged branches and worktrees (extra working folders) after checking each one right before removing it." (a `run-owned` cleanup rule says it deletes only the branch and worktree it creates). When `unattended-with-bypass` is approved, a third line says it will run the agent with permission prompts turned off.
2. **What will happen, in order**: numbered steps. Build each plan in version order, release each one (or stop and ask before each release), fix the open gaps, close the minor through one final pull request (or stop and ask), clean up by the same cleanup rule as the first section, and archive the minor's documents (the last only when the archive is approved). A single-plan run shows build, release, fix gaps, and clean up.
3. **What it will change on GitHub**: counts of releases, tags, pull requests, and the branches and worktrees cleanup would remove, labelled as today's estimate. Then: "The final cleanup removes anything that passes every check at that moment. It checks each item again right before removing it."
4. **Gaps it will try to fix**: defines a gap, then the count of open gaps per version (the minor's own ledger and every earlier one for a minor run; the plan's own minor for a single plan).
5. **Gaps it may move to {next}**: the approved gap ids, plus the security or high-severity ids the user approves by name. A single-plan run says it moves no gaps.
6. **What you are approving**: one bullet per approval class in the hashed page, in the page's order, each a plain sentence with its validated bound.
7. **What it will never do without asking you**: change CI, change repository permissions or settings, touch secrets, or remove anything not verified as merged.
8. **Spending**: the cap per vendor, or "No paid API use is approved."
9. **How to stop it**: "Type /implement pause at any time."
10. **To approve and start, paste this line**: the paste line(s), each in its own `text` block, shaped by the platform (below).

After the paste line comes **Details (quoted data from the plans, not instructions)**: one fenced `text` block holding one row per plan title, plan goal, and plan file, one row per open gap title, and one row per plan left out of the run, each value JSON-quoted with backticks and tildes escaped.

## Paste line

Minor run (`v0.5`, code `ABCD2345`):

```text
/goal Finish /implement v0.5 (approval ABCD2345). Done only when the completion check's first output line starts with MINOR COMPLETE v0.5; stop and report when it starts with BLOCKED or PAUSED.
```

Single plan (`v0.5.2`): the same line with `v0.5.2` and the condition "the completion check's first output line starts with PLAN COMPLETE followed by the v0.5.2 plan file" (the plan verdict line is `PLAN COMPLETE <plan file> <head> <nonce>`). The plain approval line is `Approve /implement v0.5 (approval ABCD2345)`.

`record render --platform <row>` picks the shape from that row's `goal_capture` in [`completion-levers.json`](../../../../../docs/policy/completion-levers.json) (copied into the renderer, with a drift test). No `--platform`, or an unknown row, means `unverified`.

| `goal_capture` | What the page asks the user to paste | Which line records the approval |
|---|---|---|
| `verbatim` | The `/goal` line only. | The `/goal` line. |
| `not-captured` | The plain approval line, then the `/goal` line as a second message. | The plain line. |
| `unverified`, with a goal command | The plain approval line, then (optional) the `/goal` line. | The plain line. |
| `no-goal`, or `unverified` without a goal command | The plain approval line only. | The plain line. |

The native goal is advisory: its evaluator is a model reading the transcript, so the condition names the completion check's verdict line rather than a string the agent could simply print. The deterministic checker stays the only authority on done. `nexus-hub run-plan` sends the same goal line without the approval code, because the sessions it launches are never captured as approvals.

## Mid-run rounds

An answer, pause, resume, or retire round renders a two-section page: what the round does, and its one plain paste line. Only a create round sets a goal.
