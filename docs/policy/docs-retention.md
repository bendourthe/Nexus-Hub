# Documentation Retention Policy

`docs/v3/` holds 440 Markdown files across 21 minor-version directories and has no rule for when any of them stop being current. Every release adds plans, per-phase session histories, comparisons, and a known-gaps file, and nothing has ever moved out. The growth is not a disk problem; it is a retrieval problem. An agent needs recent history hot and old history findable, and an undifferentiated tree of 440 files gives it neither.

This policy defines a lifecycle for per-version documentation. It moves files; it never deletes them.

## The four states

### 1. ACTIVE - the current minor version

`docs/v<MAJOR>/v<MAJOR>.<MINOR>/` for the current minor version is unrestricted. Add plans, histories, comparisons, and notes freely. This is the working directory of the project and applying retention pressure to it would be counterproductive.

### 2. CONSOLIDATE at release

When a version is released, its `development/history/` files **stay exactly where they are**. What changes is the entry point: the release's line in the [`DEVLOG index`](../DEVLOG.md) becomes the single way in, linking the plan, the history directory, and the known-gaps file.

Nothing is rewritten, merged, or summarized at this step. "Consolidate" means consolidating *navigation*, not content. A merged summary would destroy the per-phase troubleshooting detail that makes the history worth keeping.

### 3. ARCHIVE at two minors behind

When a minor version falls **two or more minors behind the current one**, its `development/` subtree moves to:

```text
docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/development/
```

This is the canonical archive layout that [`docs-layout-refactor`](../../catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md) already owns and that `docs/archive/v0/`, `docs/archive/v1/`, and `docs/archive/v2/` already use. Files move, references are repaired, and **nothing is deleted**.

Two minors is the threshold because it keeps the previous release's history reachable without a directory change while the current one is still stabilizing. At v3.17, that makes v3.15 and older archivable and leaves v3.16 and v3.17 in place.

`plans/`, `comparisons/`, and `known-gaps.md` are **not** swept by this rule. A plan is the durable statement of intent for its release and is linked from the DEVLOG index; a known-gaps file is read by the next plan to decide what carries forward. Only `development/`, which holds per-phase working notes, ages out.

### 4. EXEMPT - the non-versioned subtrees

These have their own lifecycles and are never swept by a version-based rule:

| Subtree | Its own lifecycle |
|---|---|
| `docs/solutions/` | [`solution-refresh`](../../catalog/skills/workflow/solution-refresh/SKILL.md) audits entries and decides Keep / Update / Consolidate / Replace / Delete |
| `docs/decisions/` | The `proposed` / `implemented` / `rejected` lifecycle in [`docs/decisions/README.md`](../decisions/README.md); a record moves by being rewritten, never by aging |
| `docs/incidents/` | Kept indefinitely; an incident's value is precisely that it is old enough to have been forgotten |
| `docs/policy/`, `docs/specs/`, `docs/git/` | Living documents, revised in place |

A decision record does not become less binding because it is old, and that is the whole reason `docs/decisions/` is exempt: age is evidence of durability there, not staleness.

## What enforces this

`scripts/check_docs_retention.py` reports drift and **exits 0 always**. It is advisory by design:

```bash
python scripts/check_docs_retention.py
```

It prints one `WARN` line per version directory that is two or more minors old and not yet archived, naming the exact destination. It never moves or deletes a file.

Advisory rather than blocking, for two reasons. Archiving is a judgement call that repairs references across the repo, so it belongs in a reviewed `[[docs-layout-refactor]]` pass with a confirmation gate, not in a validator that runs on every commit. And a hard gate here would block an unrelated release the moment a minor version aged out, which is a cost with no matching benefit: nothing breaks when history sits in place a version longer than the rule prefers.

The archive pass itself runs through `/update refactor` or `[[docs-layout-refactor]]`, propose-then-apply.

## Related

- [`docs-layout-refactor`](../../catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md) - owns the archive layout and executes the move
- [`known-gaps-tracker`](../../catalog/skills/workflow/known-gaps-tracker/SKILL.md) - owns `known-gaps.md`, which this policy exempts
- [`session-history`](../../catalog/skills/workflow/session-history/SKILL.md) - writes the `development/history/` files this policy ages out
- [`docs/DEVLOG.md`](../DEVLOG.md) - the per-release index that is the navigation entry point after consolidation
- [`docs/decisions/implemented/policy/2026-08-18-docs-retention-policy.md`](../decisions/implemented/policy/2026-08-18-docs-retention-policy.md) - why these thresholds, and what was rejected
