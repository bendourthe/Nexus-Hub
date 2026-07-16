# Review Trapdoors Convention

A **review trapdoor** is a concrete, project-specific failure mode that repeatedly gets a change sent back in review. A project's review-trapdoors artifact is a short, curated list of those failure modes, each phrased as a check, that an agent reads BEFORE reviewing a change or before declaring its own change review-ready. It is a deterministic backstop against the small set of recurring blockers that a project keeps hitting.

This convention is distributed with Nexus-Hub as a style guide (installed at `~/.nexus-hub/style-guides/review-trapdoors.md`) and is applied by the [`review-trapdoors`](../skills/code-review/review-trapdoors/SKILL.md) skill.

## Why a curated list

Model judgment reliably catches general review issues (a null deref, a missing test) but under-triggers on the narrow, project-specific gotchas that are not obvious from the diff alone: a registry file that must be updated in lockstep, an installer that copies by explicit name, a header that must be set on every response. Those are exactly the blockers that recur, because nothing in the changed code signals the missing step. A short list of them, kept in context during review, converts "the reviewer will probably catch this" into "this was checked".

The list is small on purpose. A trapdoors file with fifty entries stops being read; one with five to fifteen high-frequency entries stays read. Prune aggressively.

## Where it lives

Pick one location and keep it stable so agents and humans always look in the same place:

- A dedicated `review-trapdoors.md` at the repo root or under `docs/`, or
- A `## Review Trapdoors` section inside `AGENTS.md`, `CONTRIBUTING.md`, or the project constitution.

For a project that already has an `AGENTS.md`, a section there is usually best: it is already in the agent's context.

## Format

Each trapdoor is a single line phrased as a check the reviewer can pass or fail. The strongest form is "X changes must prove Y", because it names both the trigger (what kind of change) and the evidence (what must be shown):

```markdown
## Review Trapdoors

- Adding a file under `scripts/*.py` must register a copy step in BOTH installers.
- A new outbound network call must cite the policy bucket that permits it.
- A new public API export must update the API reference AND the changelog.
- A new hook must ship a test and be registered in the settings template.
- Any change to a shared config schema must update every environment's config in the same PR.
```

Rules:

- One line per trapdoor. If it needs a paragraph, it is a design principle, not a trapdoor - put it in the project constitution instead.
- Phrase it as a check, not a value ("must prove Y", not "we care about Y").
- Name the concrete trigger so the reviewer knows when it applies.
- Group by area with `###` subheadings only once the list is long enough to need it.

## How to maintain it

The list is grown from real review history, not invented up front:

1. **Add on recurrence.** When a review surfaces a blocker that has now shown up more than once (or is clearly a whole *class* of blocker), add a one-line trapdoor for it. A single one-off does not earn an entry.
2. **Source from instincts.** The [`continuous-learning`](../skills/workflow/continuous-learning/SKILL.md) skill mints local YAML instincts from observed mistakes; a recurring review-blocker instinct is the upstream signal that a trapdoor is warranted. Promote it into the trapdoors list when it is review-time-actionable.
3. **Prune the stale.** Remove a trapdoor when its underlying cause is gone (the lockstep files were merged, the footgun API was deleted). A trapdoor for a problem that can no longer occur is noise that costs attention on every review.
4. **Keep it short.** If the list grows past ~15 entries, the lowest-frequency ones are candidates for removal or promotion into an automated check (a hook or a CI gate is stronger than a human-read reminder).

## Relationship to adjacent conventions

- **`continuous-learning`** mints local instincts from observed mistakes; it is the raw feed. Review trapdoors are the curated, review-keyed subset of those instincts.
- **The project constitution** (`project-constitution`) holds durable MUST/SHOULD principles that govern all work. Trapdoors are narrower and more operational: review-time gotchas, not governing principles.
- **The merge-readiness contract** (`merge-readiness-contract.md`, applied via `quality-gate-definitions`) treats "the project's review trapdoors were checked" as one condition of a mergeable change.

## Self-check for a trapdoors file

- [ ] Every entry is a single line phrased as a check ("X changes must prove Y").
- [ ] Every entry names a concrete trigger, so a reviewer knows when it applies.
- [ ] The file lives in one stable, agent-visible location.
- [ ] The list is short enough to actually be read every review (roughly 5-15 entries).
- [ ] Entries trace to real recurring blockers, and obsolete entries have been pruned.
