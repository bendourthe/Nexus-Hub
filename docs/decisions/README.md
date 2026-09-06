# Decision Records

A decision record answers one question: **why did this design win, and what did it beat?**

That second half is the load-bearing part. A decision recorded without its alternatives invites re-litigation, because the next person to encounter the problem sees only the chosen answer and has no way to know which other answers were already examined and why they lost. `## Alternatives considered` is mandatory in every record and in every lifecycle for that reason.

## The three-surface split

Nexus-Hub keeps project memory in three places. They do not overlap, and each has a question it answers:

| Surface | Question it answers | Time orientation |
|---|---|---|
| `docs/decisions/` | Why does the design look like this, and what did it beat? | Past reasoning, still binding |
| `docs/v*/known-gaps.md` | What is still open, deferred, or broken? | Present state, expected to change |
| `docs/solutions/` | How was this specific problem solved, and how do I reproduce that? | Past problem, already closed |

What does **not** belong in each:

- **Not in `docs/decisions/`**: open work with no decision yet (that is a known gap), a solved bug with no design choice behind it (that is a solution entry), feature intent and sequencing (that is a plan), or an incident writeup (that is `docs/incidents/`). A record whose Alternatives section would read "none considered" is not a decision, it is an implementation note.
- **Not in known-gaps**: settled reasoning. Once a gap is closed by a design choice worth remembering, the reasoning moves here and the gap entry records that it closed.
- **Not in `docs/solutions/`**: reasoning that applies beyond the one problem. A solution entry is reproduction-shaped ("this failed, here is the fix"); if the fix encoded a general rule, the rule belongs in a decision record.

Adjacent surfaces that are deliberately separate: `docs/incidents/` records what broke and what guardrail it motivated (see `[[incident-postmortem]]`), and `catalog/memory/decisions.md` is an unrelated **distributed template** shipped to end users' own projects. Neither is part of this tree.

## Layout

```text
docs/decisions/<lifecycle>/<class>/YYYY-MM-DD-<slug>.md
```

Lifecycle is one of `proposed`, `implemented`, `rejected`. Class is one of `architecture`, `policy`, `process`, `tooling`. There is deliberately no `feature` class: feature intent lives in plans under `docs/v*/plans/`.

| Class | Covers |
|---|---|
| `architecture` | How the system is structured: module boundaries, data flow, extension points |
| `policy` | What is allowed and what is refused: registry rules, security posture, attribution |
| `process` | How work is done: branching, release flow, review gates |
| `tooling` | What the repo builds and runs for itself: validators, hooks, CI shape |

The date is the date the decision was made or ratified, not the date the file was written. Where a decision predates this tree, use the documented date from the CHANGELOG, AGENTS.md, or the commit that carried it.

## Record format

Every record opens with exactly three lines:

```text
# Decision: <title>

Status: implemented - <one line summary of the outcome>
```

The `Status:` word must match the lifecycle folder the file sits in. The one-line summary after the dash is what a reader sees in a grep; make it say the outcome, not the topic.

Then a lifecycle-specific skeleton:

| Lifecycle | Required sections |
|---|---|
| `proposed` | `## Problem`, `## Proposal`, `## Alternatives considered`, `## Acceptance criteria`, `## Risks` |
| `implemented` | `## Problem`, `## Decision` (present tense), `## Alternatives considered`, `## Consequences` |
| `rejected` | The frozen proposal as written, with the verdict on the `Status:` line |

Two rules the validator enforces that are easy to miss:

1. **`## Consequences` is required in `implemented`.** A decision with no stated consequences has not been thought through to its cost.
2. **Proposal-era headings are rejected inside `implemented` records.** `## Proposal` and `## Acceptance criteria` describe a thing that has not happened yet. When a proposal ships, rewrite it: `## Proposal` becomes `## Decision` in the present tense, and `## Acceptance criteria` becomes `## Consequences`. A record that still reads as a pitch after shipping tells the reader it was never revisited.

## Lifecycle

A record moves by being **rewritten and moved**, not by editing its Status line in place.

- `proposed` to `implemented`: rewrite per rule 2 above, move the file, update `Status:`. The date in the filename stays the original decision date.
- `proposed` to `rejected`: move the file and put the verdict on the `Status:` line. **Do not edit the body.** The frozen proposal is the point: a future proposer needs to see what was actually proposed, not a summary of why it lost.

## Why `rejected/` exists

It is the highest-value folder in this tree and the one most likely to be skipped.

Nexus-Hub has concrete precedent for re-proposing declined designs. Two are seeded here: a platform default that was fabricated rather than found and had to be withdrawn after shipping, and a third-party extension runtime that was declined on architectural grounds and then partially re-proposed later in a different form. Both are cheap to re-propose and expensive to re-litigate, which is exactly the profile of a decision worth freezing.

Before proposing a design that touches an existing policy or platform surface, grep `rejected/` first.

## Governance

Non-trivial changes must include or update a record in the same pull request. The rule and its exemptions live in `AGENTS.md`. `scripts/validate_decision_records.py` enforces the structure and format in `make validate` and in CI.

```bash
python scripts/validate_decision_records.py
```
