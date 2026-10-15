---
name: commit-sweep
description: Sweep a window of recent commits at a higher altitude than per-diff review, surfacing problems that no single commit review would catch - partial or abandoned refactors spread across commits, convention drift, accumulated TODO/FIXME debt, undocumented dependency changes, and cross-cutting inconsistencies. Make sure to use this skill whenever the user says "sweep the recent commits", "review the last N commits", "cross-commit review", "what did we miss across these commits", "look over the recent work at a high level", "periodic commit audit", or wants a periodic higher-level pass over recent history, even if they do not say "sweep". SKIP, do NOT use for, reviewing a single diff or PR (use /review diff), finding which commit introduced a specific bug (use git-bisect-assistant), or explaining one known regression (use regression-root-cause-analyzer).
summary_l0: "Sweep recent commits for cross-commit problems a per-diff review misses"
overview_l1: "This skill sweeps a window of recent commits (default the last 10, configurable) at a higher altitude than per-diff review, surfacing problems that emerge only across commits and that no single-commit review would flag: partial or abandoned refactors, convention drift, TODO/FIXME debt introduced and never resolved, security-relevant deltas, dependency changes without lockfile or doc updates, and cross-cutting inconsistencies. It is read-only over history: read the window via git log and a range diff, cluster the changes by subsystem, evaluate each cluster for what emerged across the commits, then emit a severity-tagged findings list with commit references and offer to open follow-ups. It complements per-diff review, bisect, and regression analysis rather than replacing them. Trigger phrases: sweep recent commits, review the last N commits, cross-commit review, what did we miss across these commits, periodic commit audit, high-level review of recent work."
---

# Commit Sweep

Review a window of recent commits from above. Per-commit and per-PR review each judge one change in isolation, which is the right altitude for most work but blind to problems that only exist in the aggregate: a refactor started in one commit and abandoned two commits later, a naming convention that drifted halfway through, TODOs added and never closed, a dependency bumped without a lockfile or a doc update. This skill sweeps the last N commits for exactly those cross-commit problems, read-only, and turns what it finds into follow-ups.

## When to Use This Skill

- Periodically (end of a work session, before a release, at a sprint boundary) to catch cross-commit drift while it is still cheap to fix.
- After a burst of autonomous or multi-session work, when many commits landed without a human reviewing the whole arc.
- When something feels inconsistent across recent work but no single diff is obviously wrong.
- As a composed step in an end-of-shift validation pass.

**Trigger phrases**: "sweep the recent commits", "review the last N commits", "cross-commit review", "what did we miss across these commits", "periodic commit audit", "high-level pass over recent work".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Review one diff, PR, or branch | `/review diff` |
| Find which commit introduced a bug | `git-bisect-assistant` |
| Explain the root cause of one known regression | `regression-root-cause-analyzer` |
| Deep single-file or single-function review | `multi-agent-code-review` |

## How this differs from per-commit review

`/review diff` answers "is this change correct?" for one change. `git-bisect-assistant` answers "which commit broke X?". `regression-root-cause-analyzer` answers "why did X regress?". This skill answers a question none of them ask: "across these last N commits, what emerged that no single commit review would flag?". It is deliberately low-resolution and wide - it trades line-by-line depth for the altitude to see drift, half-finished work, and accumulation.

## What to look for

| Cross-commit problem | Signal in the window |
|---|---|
| Partial / abandoned refactor | A rename or pattern change applied to some call sites in one commit, never completed in later ones |
| Convention drift | New code in later commits diverges from the style/pattern established earlier in the window |
| Accumulated debt | `TODO` / `FIXME` / `XXX` / `HACK` added and not resolved within the window |
| Undocumented dependency change | A dependency added/bumped without a lockfile update, a doc note, or a CHANGELOG entry |
| Security-relevant delta | New handling of secrets, auth, input parsing, or external calls that crossed several commits |
| Test/behavior mismatch | Behavior changed in one commit; the test that should cover it added (or not) in another |
| Reverted-and-reintroduced churn | The same lines changed, reverted, and changed again across commits (thrash) |
| Doc / code divergence | Code behavior changed but the doc that describes it (per the doc-header convention) was not touched |

## Instructions

1. **Fix the window.** Default to the last 10 commits; honor an explicit count, a `since` reference, or a base branch. State the exact range you swept (e.g. `HEAD~10..HEAD`).
2. **Read the window read-only.** Use `git log --stat` for the shape and `git log -p` or `git diff <base>..HEAD` for the content. Never rewrite, squash, rebase, or otherwise mutate history in this skill - it observes only.
3. **Cluster by subsystem.** Group the changed files by area (module, package, layer, doc set) so each cluster can be judged as a unit rather than commit by commit.
4. **Evaluate each cluster at altitude.** For each cluster, ask the "what to look for" questions: is any refactor half-applied, did a convention drift, was debt added and left, did a dependency or behavior change without its companion doc/test/lockfile update? Record findings with the specific commit SHAs and files.
5. **Severity-tag findings.** Tag each finding (for example: HIGH security-relevant or release-blocking, MEDIUM correctness/consistency risk, LOW cleanup) so the follow-up list is prioritized.
6. **Offer follow-ups.** Present the severity-ordered findings with commit/file references. Offer to open tracked follow-ups (cross-link `[[tasks-to-issues]]`) or to record them in the version's known-gaps log. Apply fixes only when asked; the sweep itself is diagnostic.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Every commit was reviewed when it landed, so a sweep is redundant." | Per-commit review cannot see a refactor abandoned two commits later or a convention that drifted across five. The whole point of the sweep is the altitude a single-diff review structurally lacks. |
| "If there were a bug, a test would have caught it." | Many cross-commit problems are not test failures: a half-finished rename compiles, drifted naming passes, an undocumented dependency bump is green. The sweep catches what the suite is silent about. |
| "I will just diff HEAD against the base and skim it." | A flat range diff hides the sequence. Reading commit by commit within the window is what reveals thrash, abandonment, and the order in which behavior and its tests/docs did (or did not) change together. |
| "This is just a big code review, I can do it ad hoc." | Ad hoc skimming reliably misses accumulation. The value is the systematic per-cluster pass against the fixed checklist, which is what makes the sweep repeatable and its output trackable. |

## Verification

- [ ] The exact commit range swept is stated (count or ref range).
- [ ] History was treated read-only - no rebase, squash, amend, or force operation was performed by this skill.
- [ ] Changes were clustered by subsystem and each cluster evaluated against the "what to look for" checklist.
- [ ] Every finding cites the specific commit SHA(s) and file(s) and carries a severity tag.
- [ ] Findings were offered as tracked follow-ups (issues or known-gaps entries); fixes were applied only on explicit request.

## Related Skills

- [[multi-agent-code-review]] -- deep per-diff review with reviewer personas; the sweep operates one altitude above it and can feed it targets.
- [[git-bisect-assistant]] -- pinpoints the single commit that introduced a defect; the sweep is breadth-first, bisect is a targeted search.
- [[regression-root-cause-analyzer]] -- explains one known regression in depth; the sweep surfaces candidates it can then investigate.
- [[tasks-to-issues]] -- turns the sweep's findings into tracked GitHub issues.
- [[known-gaps-tracker]] -- the per-version log where sweep findings can be recorded when not opened as issues.

---

**Version**: 1.0.0
**Last Updated**: July 2026
