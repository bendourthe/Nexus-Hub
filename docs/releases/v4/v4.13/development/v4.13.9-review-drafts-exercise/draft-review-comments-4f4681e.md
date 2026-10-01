# Draft review comments

**Scope**: commit 4f4681e75773cba509392faef8c600e0de364b6d (normal commit, reviewed as `git diff --end-of-options <sha>^ <sha>`)
**Status**: DRAFT. Nothing here has been posted. Post it yourself if you choose.

## Drafted (CONFIRMED)

### 1. scripts/optimize_skill_description.py:178 - P2 - Splitter and scorer disagree on entries without should_trigger

- **Path**: `scripts/optimize_skill_description.py`
- **Line**: 178
- **Severity**: P2
- **Verdict**: CONFIRMED (confidence 100, deterministic: reproduced against this commit's code)
- **Body**: The splitter reads a missing `should_trigger` as negative (`bool(members[0].get("should_trigger"))`), but `estimate_trigger_rate` scores it as positive (`bool(q.get("should_trigger", True))`, line 465). With 14 labelled positives and 10 unlabelled entries, `resolve_split` returns three-way mode with `reported_optimistic: false`, yet the test split holds zero entries the scorer treats as negative. A description that always triggers would score 1.0 and be reported as a held-out result. Suggest one shared class helper used by both the splitter and the scorer.
- **Evidence**:

    ~~~text
    178:        cls = bool(members[0].get("should_trigger"))
    465:            should_trigger = bool(q.get("should_trigger", True))
    reproduction: mode three-way, reported_optimistic False, scorer-negatives in test 0
    ~~~

### 2. scripts/optimize_skill_description.py:225 - P3 - Fallback from three-way mode is silent

- **Path**: `scripts/optimize_skill_description.py`
- **Line**: 225
- **Severity**: P3
- **Verdict**: CONFIRMED (confidence 100, deterministic: reproduced against this commit's code)
- **Body**: A set of 24 or more entries that fails the class minimum (27 positives, 3 negatives) silently drops to the two-way split. The only sign is `reported_optimistic: true`, with no stated reason. Suggest a one-line stderr note naming why three-way mode was not used.
- **Evidence**:

    ~~~text
    225:    train, test = split_train_test(evals, train_fraction, seed)
    reproduction: mode two-way, stderr ''
    ~~~

### 3. scripts/optimize_skill_description.py:155 - P3 - A one-turn entry and the same query get different group keys

- **Path**: `scripts/optimize_skill_description.py`
- **Line**: 155
- **Severity**: P3
- **Verdict**: CONFIRMED (confidence 100, deterministic: reproduced against this commit's code)
- **Body**: `group_key` prefixes multi-turn entries with `turns:` and queries with `query:`, so `{"query": "Fix the bug!"}` and `{"turns": ["fix the bug"]}` land in different groups and can sit in different splits, which the grouping exists to prevent. Suggest one `text:` key for both forms.
- **Evidence**:

    ~~~text
    155:        return "turns:" + _normalize_text(" ".join(str(t) for t in turns))
    156:    return "query:" + _normalize_text(str(entry.get("query", "")))
    reproduction: query:fix the bug vs turns:fix the bug
    ~~~

## Not drafted (PLAUSIBLE)

| Path | Line | Severity | Title | Why not drafted |
|---|---|---|---|---|
| `scripts/optimize_skill_description.py` | 927 | P3 | The one-time test scoring uses the same `--repeats` as the loop, so a low repeat count makes the reported score noisy | Not validated: no repeated-run measurement of the variance was made, so the size of the effect is unknown |

## General notes

- The two-way split stays ungrouped by design, to keep legacy partitions identical. It is recorded in the decision `docs/decisions/proposed/tooling/2026-09-30-optimizer-selection-reporting-split.md`, not raised as a finding.
