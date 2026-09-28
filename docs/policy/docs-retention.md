# Documentation Retention Policy

`docs/releases/v3/` holds 440 Markdown files across 21 minor-version directories and has no rule for when any of them stop being current. Every release adds plans, per-phase session histories, comparisons, and a known-gaps file, and nothing has ever moved out. The growth is not a disk problem; it is a retrieval problem. An agent needs recent history hot and old history findable, and an undifferentiated tree of 440 files gives it neither.

This policy defines a lifecycle for per-version documentation. It moves files; it never deletes them.

## The four states

### 1. ACTIVE - the current minor version

`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/` for the current minor version is unrestricted. Add plans, histories, comparisons, and notes freely. This is the working directory of the project and applying retention pressure to it would be counterproductive.

### 2. CONSOLIDATE at release

When a version is released, its `development/history/` files **stay exactly where they are**. What changes is the entry point: the release's line in the [`DEVLOG index`](../DEVLOG.md) becomes the single way in, linking the plan, the history directory, and the known-gaps file.

Nothing is rewritten, merged, or summarized at this step. "Consolidate" means consolidating *navigation*, not content. A merged summary would destroy the per-phase troubleshooting detail that makes the history worth keeping.

### 3. ARCHIVE at one minor behind

When a minor version falls **behind the current one**, its `development/history/` subtree moves from `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/` to:

```text
docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/
```

This is the canonical archive layout that [`docs-layout-refactor`](../../catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md) already owns and that `docs/archives/v0/`, `docs/archives/v1/`, and `docs/archives/v2/` already use. Files move, references are repaired, and **nothing is deleted**.

One minor is the threshold because a release's per-phase history stops changing the moment that release closes. The original rule kept the previous release's history in the working tree for an extra cycle on the theory that the current version was still stabilizing and might need to reach back into it without a directory change. That protected a real case -- a patch release revisiting the prior release's decisions -- but it protected it by keeping files in the active tree, when the DEVLOG line the move repoints already reaches them. The consultation still works; it costs one directory hop. Weighed against a full extra cycle of accumulated history in the working tree, the hop is the cheaper side. At v4.13, that makes v4.12 and older archivable and leaves only v4.13 in place.

**Only `history/` ages out, not `development/` wholesale.** The first archive pass (v3.18.0 Phase 5) discovered why this distinction is load-bearing: `development/` in this repository also holds live content.

| Also under `development/` | Why it stays |
|---|---|
| `fixtures/`, `worked-example/` (v3.9, v3.12, v3.13) | `.github/workflows/presentify-extractor.yml` **executes** six of these Python scripts directly. Archiving them breaks CI. |
| Contract documents (v3.15) | Shipped hooks (`_notify_common.sh` / `.ps1`, `notify-on-complete.*`) and tests cite them by path in comments and skip messages. |
| One-off design notes (v3.4, v3.7, v3.11) | Small, still referenced, and not the growth problem this policy exists to solve. |

A blanket `development/` rule would have archived live CI inputs and orphaned a shipped code citation. If that content should not live in a version's docs directory at all, that is a separate refactor with its own reference repair, not something a retention rule should do silently.

**Re-point same-page anchors when content moves.** A link written `](#some-heading)` targets a heading in its own file. The moment that content is relocated, the anchor silently becomes a cross-file link to a heading that is no longer there. No link checker will catch it: the link is a syntactically valid same-page reference right up until it isn't, so a checker that resolves `#` targets as same-page by definition reports it clean.

This is not hypothetical. The v3.18.0 Phase 3 ratchet-down moved a block containing three such anchors and the link check passed over all three; they were found by reading the file. Building a general anchor validator was considered and rejected, because the forge's heading-to-slug rule is subtle enough to produce false positives on legitimate content (a first implementation flagged a correct table of contents, having collapsed `Compliance & Governance` to one hyphen where the forge emits two), and a gate that cries wolf on valid documentation gets ignored. Grep the moved block for `](#` by hand instead.

`plans/`, `comparisons/`, and `known-gaps.md` are **not** swept by the one-minor-behind rule that moves `history/`. Age alone does not retire them: a plan is the durable statement of intent for its release and is linked from the DEVLOG index, and a known-gaps file is read by the next plan to decide what carries forward. A released minor whose work is still open is exactly the one a later plan needs in the active tree.

**Closure does retire them, which is state 3b below.** The original exemption was written as permanent, and that produced the outcome it was meant to prevent, one level down: at v4.13.0 every released minor existed in BOTH trees, 39 active directories against 44 archived, including all 22 released v3 minors. Released is not closed, and the difference is the whole rule. The initial closure scan falsely selected v3.18, whose BG-2 remained open, and v3.5, which had no known-gaps register. Neither qualifies. Age is the wrong trigger for a plan; proven completion is the right one.

### 3b. ARCHIVE PLANS AND COMPARISONS after proven closure or transfer

Independently of the age rule above, a minor's `plans/` and `comparisons/` move to `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/` once that minor is **fully closed**. Both conditions must hold, and both are mechanically checkable:

1. Its `known-gaps.md` explicitly states a finalized or closed Status and `**Open items**: 0`, with no contradictory `OPEN` marker, in-progress or open Status, unchecked box, or gap id in an Open Items section. A missing or ambiguous register holds the minor open.
2. Every plan under its `plans/` has zero unchecked task lines (`- [ ] T...`).

The v4.0-v4.12 historical closeout has one narrow alternative: **closed by verified transfer**. The v4.13 `known-gaps.md` must link the older minor's active ledger with a matching LF-normalized SHA-256, state that source-open items remain open, and list every plan with retained strict task boxes with its matching hash, exact box count, disposition, and existing evidence. This retires only the older `plans/` and `comparisons/` directories from the active tree. It does not resolve a gap, complete a task, change a plan's historical boxes, or qualify v4.13 and later plans. A missing or stale link, hash, disposition, or evidence blocks the move. `scripts/check_docs_retention.py` checks this exception before reporting an archive candidate.

`known-gaps.md` **stays in the active tree** even for a closed minor. It is the one file the next `/plan` reads to decide what carries forward, and a closed file answering "nothing carries forward" is a cheaper answer than a directory hop into the archive. Archiving it would save one small file and cost a lookup on every plan.

Outside the bounded historical transfer, an open item or an unchecked task is a hold, not a delay: it means the minor is still live work regardless of how many releases have shipped since. This is why the trigger is completion rather than age, and why a two-year-old minor with one open gap correctly stays put while last month's fully-closed minor moves.

The move runs through `[[docs-layout-refactor]]`, propose-then-apply, with reference repair. Nothing is deleted.

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

It prints one `WARN` line per version directory that is two or more minors old and not yet archived, and one per fully-closed or verified-transferred minor whose `plans/` or `comparisons/` still sit in the active tree, naming the exact destination in each case. It never moves or deletes a file.

Advisory rather than blocking, for two reasons. Archiving is a judgement call that repairs references across the repo, so it belongs in a reviewed `[[docs-layout-refactor]]` pass with a confirmation gate, not in a validator that runs on every commit. And a hard gate here would block an unrelated release the moment a minor version aged out, which is a cost with no matching benefit: nothing breaks when history sits in place a version longer than the rule prefers.

The archive pass itself runs through `/update refactor` or `[[docs-layout-refactor]]`, propose-then-apply. `/update release` reports the closed-minor list as part of its governance pass, so a release is the moment the question gets asked; acting on it stays a separate confirmed operation, because moving a directory tree and repairing its references is not something a release flow should do unattended.

## Related

- [`docs-layout-refactor`](../../catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md) - owns the archive layout and executes the move
- [`known-gaps-tracker`](../../catalog/skills/workflow/known-gaps-tracker/SKILL.md) - owns `known-gaps.md`, which this policy exempts
- [`session-history`](../../catalog/skills/workflow/session-history/SKILL.md) - writes the `development/history/` files this policy ages out
- [`docs/DEVLOG.md`](../DEVLOG.md) - the per-release index that is the navigation entry point after consolidation
- [`docs/decisions/implemented/policy/2026-08-18-docs-retention-policy.md`](../decisions/implemented/policy/2026-08-18-docs-retention-policy.md) - why these thresholds, and what was rejected
