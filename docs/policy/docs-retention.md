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

When a minor version falls **two or more minors behind the current one**, its `development/history/` subtree moves to:

```text
docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/
```

This is the canonical archive layout that [`docs-layout-refactor`](../../catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md) already owns and that `docs/archive/v0/`, `docs/archive/v1/`, and `docs/archive/v2/` already use. Files move, references are repaired, and **nothing is deleted**.

Two minors is the threshold because it keeps the previous release's history reachable without a directory change while the current one is still stabilizing. At v3.17, that makes v3.15 and older archivable and leaves v3.16 and v3.17 in place.

**Only `history/` ages out, not `development/` wholesale.** The first archive pass (v3.18.0 Phase 5) discovered why this distinction is load-bearing: `development/` in this repository also holds live content.

| Also under `development/` | Why it stays |
|---|---|
| `fixtures/`, `worked-example/` (v3.9, v3.12, v3.13) | `.github/workflows/presentify-extractor.yml` **executes** six of these Python scripts directly. Archiving them breaks CI. |
| Contract documents (v3.15) | Shipped hooks (`_notify_common.sh` / `.ps1`, `notify-on-complete.*`) and tests cite them by path in comments and skip messages. |
| One-off design notes (v3.4, v3.7, v3.11) | Small, still referenced, and not the growth problem this policy exists to solve. |

A blanket `development/` rule would have archived live CI inputs and orphaned a shipped code citation. If that content should not live in a version's docs directory at all, that is a separate refactor with its own reference repair, not something a retention rule should do silently.

**Re-point same-page anchors when content moves.** A link written `](#some-heading)` targets a heading in its own file. The moment that content is relocated, the anchor silently becomes a cross-file link to a heading that is no longer there. No link checker will catch it: the link is a syntactically valid same-page reference right up until it isn't, so a checker that resolves `#` targets as same-page by definition reports it clean.

This is not hypothetical. The v3.18.0 Phase 3 ratchet-down moved a block containing three such anchors and the link check passed over all three; they were found by reading the file. Building a general anchor validator was considered and rejected, because the forge's heading-to-slug rule is subtle enough to produce false positives on legitimate content (a first implementation flagged a correct table of contents, having collapsed `Compliance & Governance` to one hyphen where the forge emits two), and a gate that cries wolf on valid documentation gets ignored. Grep the moved block for `](#` by hand instead.

`plans/`, `comparisons/`, and `known-gaps.md` are likewise **not** swept. A plan is the durable statement of intent for its release and is linked from the DEVLOG index; a known-gaps file is read by the next plan to decide what carries forward.

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
