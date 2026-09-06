# Doc Word Budgets

`docs/policy/doc-budgets.json` declares a word ceiling for each always-loaded instruction doc. `scripts/validate_doc_budgets.py` enforces it in `make validate` and in CI.

## Why these docs

The budgeted set is not "important docs". It is the set whose cost is paid **in every session, on every platform, forever**: `AGENTS.md` (inlined into `CLAUDE.md` by an `@` import and mirrored into every platform's instruction surface), `CLAUDE.md` itself, the five lockstep `templates/ai-instructions/base-*.md` files, and `catalog/style-guides/markdown.md` (referenced by every generated-Markdown task).

A reference doc that an agent reads on demand costs tokens once, when it is relevant. An always-loaded doc costs tokens whether or not it is relevant. Only the second class needs a ceiling, which is why `docs/` reference material, skill bodies, and plans are deliberately unbudgeted.

The failure mode this prevents is not any single bad edit. It is the aggregate: every addition to `AGENTS.md` is locally justified, no single one is worth arguing about, and nobody is measuring the total. The gate supplies the measurement.

## The ratchet

Ceilings move in one direction.

- **Lowering a ceiling is free.** Relocate content to a reference doc, condense it, or delete what is stale, then lower the number in the same PR. No justification needed to tighten.
- **Raising a ceiling is a decision.** It requires an explicit justification in the pull request that raises it: what was added, why it must be always-loaded rather than on-demand, and what (if anything) was removed to partly offset it. The validator's `OVER` message says "relocate or condense" first for exactly this reason, so the cheap fix stays the obvious one.
- **Keep at least 5% headroom.** Ceilings are seeded at roughly current size plus 10%. A budget with under 5% headroom is reported by `--list` with a `<- tight` marker: at that point the doc is effectively frozen, which is a stricter policy than intended and usually means the content needs relocating rather than the ceiling needs raising.

### Recorded raises

Every raise is a decision, so it is logged here as well as in the pull request that made it.

- **2026-09-04, v4.5.0 phase 1.** The five lockstep templates rose by the measured cost of the new always-loaded `## Writing Discipline` block: base-claude.md 1690 to 1800 (+110; the block cost 163 words there but retired the 54-word Claude-only `## Communication Style` section it absorbed), and base-codex.md 1320 to 1490, base-cursor.md 1290 to 1460, base-gemini.md 1310 to 1480, base-opencode.md 1290 to 1460 (+170 each, the 163-word block rounded up). Why always-loaded rather than on-demand: the rule binds the agent's own chat replies and generated files on every turn, and the `anti-slop-editing` skill it points at is trigger-gated, so a user who never asks for it never receives it; the comparison that seeded v4.5.0 found the punctuation rule shipped to one platform of twelve for that reason. What offset it: the Claude-only section was removed rather than duplicated, and the block names the highest-frequency patterns in one item each and defers the catalog to the skill, so it stays at 11 lines. Phase 7 of the same plan owns the reckoning on whether the per-turn cost earned its place.
- **2026-09-05, v4.7.0 phase 2.** The five lockstep templates rose by the measured cost of the new always-loaded `## Autonomous Operation` block plus its two cross-reference sentences (one in `## Consequential Decisions`, one in `## Skill Discovery`): base-claude.md 1800 to 2080 (+280; measured +274 words); base-codex.md 1490 to 1770 (+280; measured +274 words); base-cursor.md 1460 to 1740 (+280; measured +274 words); base-gemini.md 1480 to 1760 (+280; measured +274 words); base-opencode.md 1460 to 1740 (+280; measured +274 words). Each ceiling rose by the delta rounded up to 10, leaving the same headroom as before. Decision: the maintainer chose to author tight and raise by the measured delta rather than trim other sections. Justification: the block reconciles the autonomous-operation rule with `## Consequential Decisions` and carries the user-over-skill precedence rule; it is platform-agnostic, byte-locked across the five, and asserted on all twelve. Records: `docs/releases/v4/v4.7/development/autonomy-boundary-decision.md`, `docs/decisions/implemented/policy/2026-09-05-autonomous-operation-block-on-every-platform.md`.

## Usage

```bash
python scripts/validate_doc_budgets.py           # gate: exit 1 on any failure
python scripts/validate_doc_budgets.py --list    # usage table with headroom
```

Failure classes, all collected and printed before a single exit so one bad entry cannot mask another:

| Class | Meaning |
|---|---|
| `BAD` | Manifest missing, unparseable, not an object, or a ceiling that is not a positive integer |
| `DUPE` | Two keys naming the same file (literal duplicates, or paths that normalize equal) |
| `MISS` | A budgeted file is not on disk. Update the manifest in the same change that moves or deletes it |
| `OVER` | Word count exceeds the ceiling. Relocate or condense; raising requires PR justification |

## Counting rule

Words are whitespace-delimited across the whole file, fenced code blocks and tables included. Those are real tokens the model loads. Exempting them would make the cheapest way to pass the gate "move the prose into a code fence", which lowers the number without lowering the cost.

## Adding a doc to the budget

Add the doc only if it is genuinely always-loaded. Measure it with `--list` after adding a provisional ceiling, then set the ceiling to roughly current size plus 10%. Because `docs/policy/**` is re-included in the CI path filter, a manifest edit triggers CI on its own.
