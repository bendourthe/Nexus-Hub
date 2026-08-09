# Human Review Interface

The contract a local annotation interface must satisfy for its labels to be usable as ground truth. Read this cold: it assumes no other part of the evaluation skill is in context.

This describes what to build when a review interface is requested, not which framework to build it in. Any stack that satisfies the observable checks below is acceptable, including a terminal prompt loop. It requires no hosted annotation vendor and no account.

The reason to be strict here: labels collected through a careless interface are not merely noisy, they are biased in a specific direction, and every metric computed against them inherits that bias while looking perfectly precise.

## The annotation schema

Each review produces one `human_annotation`:

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Stable, never reused |
| `item_id` | yes | What was reviewed |
| `annotator_id` | yes | Pseudonymous and stable. Never a real name |
| `label` | yes | Drawn from a closed set defined before review starts |
| `confidence` | yes | The reviewer's own confidence |
| `abstained` | yes | Boolean, and a first-class outcome |
| `blind` | yes | Whether the reviewer could see any competing signal |
| `annotated_at` | yes | ISO 8601 |
| `notes` | no | Free text; scan for sensitive content before export |
| `provenance`, `redaction_status` | yes | Per the shared artifact contract |

Define the label set before the first review. Adding a label mid-pass invalidates comparability with everything reviewed before it; if it must happen, version the schema and re-review the earlier items or report the two groups separately.

## Blind review

The interface must not show the reviewer any signal that could anchor the label:

- the model's or judge's verdict on this item
- another reviewer's label, in a double-labeled pass
- which system produced the output, in a comparison
- aggregate statistics on progress so far ("82 percent passed so far")

An unblinded reviewer confirms rather than checks, and the resulting agreement figure is circular: it measures whether the human read the judge's answer. Record `blind: true` only when all four hold.

Where the interface reveals system identity by necessity (outputs differ visibly in format), normalize the presentation or record `blind: false` honestly rather than claiming a blindness the setup does not have.

## Randomized ordering

Present items in an order randomized per reviewer, from a recorded seed.

Sequential order carries structure: items sorted by timestamp cluster by incident, items sorted by score cluster by difficulty. A reviewer who hits twenty failures in a row starts expecting failure, and the drift lands entirely on the items at the end of the queue. Randomizing spreads fatigue and expectation effects evenly instead of concentrating them.

Record the seed so a pass can be reconstructed.

## Keyboard-first controls and accessibility

Reviewers label hundreds of items. An interface requiring a mouse per item is slow enough that reviewers rush, and rushing shows up as noise attributed to the rubric.

- Every label is reachable by a single keypress; the mapping is visible on screen.
- Navigation (next, previous, submit) is keyboard-driven.
- Undo is available for at least the previous item, since a mis-keyed label is the most common input error.

Accessibility is part of the contract, not decoration:

- Every control has a programmatic label; the keyboard shortcut is not the only affordance.
- Focus is visible at all times and moves predictably; after submitting, focus lands on the next item's first control, not back at the page top.
- Label choice never depends on color alone.
- Any timing element is adjustable or absent.
- Screen-reader users get item content and controls announced in a sensible order.

## Confidence and abstention

Both are load-bearing, and both are commonly dropped as clutter.

- **Confidence** separates "this is clearly a failure" from "this is borderline". Low-confidence items are where a rubric is ambiguous and where evaluator disagreement will concentrate; without the field, they are invisible inside the aggregate.
- **Abstention** must be a real option. A reviewer forced to choose on an item the rubric does not cover produces a fabricated label that is indistinguishable from a real one. Cluster the abstentions afterwards: they are the strongest available signal about which cases the rubric is missing.

Never impute an abstention to a label. Report abstention rate alongside every label distribution.

## Adjudication and audit history

When two reviewers disagree, produce an `adjudication_record`: the conflicting annotation ids, the resolution, the `resolution_method` (`third_reviewer`, `discussion`, `rubric_clarification`, `escalation`), a one-or-two-sentence rationale, and `taxonomy_change_required`.

That last flag is what makes disagreement productive. A disagreement caused by an ambiguous category is a rubric defect; if it is only ever resolved item by item, the same disagreement recurs forever.

Keep an append-only audit history. Never overwrite an annotation in place: a changed label is a new record referencing the old one. The history is what lets a later reader tell a genuine correction from a quietly reversed judgment.

## Local autosave and resume

- Persist after every submission, not at the end of a session. A crash at item 180 of 200 must cost one item.
- Writes go to a local path the operator confirmed before the session starts.
- Reopening resumes at the first unreviewed item, with completed work intact.
- Resume must not re-present a completed item as new, and must not silently skip a genuinely unreviewed one.

## Deterministic export

Export to JSON, JSONL, or CSV with:

- **Stable key order** and **stable row order** (sort by `id`), so two exports of unchanged data are byte-identical and diffable.
- **Explicit encoding** (UTF-8) and explicit null handling. An empty string and an absent value are different; a CSV that conflates them loses the abstention distinction.
- **The schema version** recorded in the export.
- **A confirmed output path**, shown before writing.

Nothing uploads. Export writes a local file; moving that file anywhere else is a separate, explicitly authorized act. An interface with an implicit "sync" or "share" is out of contract, not merely undesirable.

## Local-data handling

- Reviewed items are typically real production content, and annotations are judgments about real interactions. Both stay local: `state: raw`, `export_authorized: false`.
- `annotator_id` is pseudonymous. No metric here needs reviewer identity.
- The `notes` field is free text and is the most likely place for sensitive content to enter unnoticed. Scan it before any export.
- Any export applies the per-category policy in `[[egress-redaction]]` as an explicit, separately authorized step.

## Verification

- [ ] The label set was fixed before the first review, and the schema is versioned
- [ ] The interface hides the judge verdict, other reviewers' labels, system identity, and running aggregates; `blind` reflects reality
- [ ] Item order is randomized per reviewer from a recorded seed
- [ ] Every label is reachable by a single keypress, and the mapping is visible
- [ ] Every control has a programmatic label, focus is visible and moves predictably after submit, and no choice depends on color alone
- [ ] Confidence is captured on every annotation
- [ ] Abstention is selectable, is never imputed to a label, and its rate is reported with every label distribution
- [ ] Disagreements produce an `adjudication_record` with a resolution method and a `taxonomy_change_required` flag
- [ ] Annotation history is append-only; a changed label creates a new record referencing the old
- [ ] Autosave persists after every submission to an operator-confirmed local path
- [ ] Resume returns to the first unreviewed item without re-presenting or skipping any
- [ ] Export is deterministic: stable key and row order, explicit encoding and null handling, schema version recorded
- [ ] The output path is confirmed before writing, and nothing uploads implicitly
