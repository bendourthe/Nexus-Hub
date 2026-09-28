# Phase 5 Evidence - Attestation Gates for the Unmeasurable

**Project**: Nexus-Hub
**Plan**: [v4.11.2 document and deck quality](../../../../../archives/v4/v4.11/plans/v4.11.2-adoption-document-and-deck-quality.md)
**Phase**: 5 of 7
**Branch**: `feat/v4.11.2-document-deck-quality`
**Date**: 2026-09-13
**Status**: complete

## Model routing

Plan recommends strong tier at high effort; ran on Opus 5, which IS the strong
tier. First phase of this plan where the running model matches the plan's
recommendation exactly.

## The boundary this phase had to hold

The plan names the risk in its own text: an attestation gate must not drift into
scoring taste. Some rules cannot be judged without an authorship or beauty
detector, which this catalog forbids. The alternative is not to demote them to
prose an agent can skip in silence, but to require that the decision was MADE
AND RECORDED.

`check_attestation.py` therefore answers one question per check - "is this
recorded?" - and never "is this good?".

That boundary is asserted, not merely stated.
`test_attestation_never_scores_content` feeds the gate a structurally complete
record whose prose is deliberately terrible (`"stuff"`, `"looked at it"`,
`"it works"`) and REQUIRES a pass. If that test ever fails, someone has added a
quality heuristic; the docstring says to move it to a skill that owns authorship
or delete it.

## Delivered

- `scripts/check_attestation.py`: four required sections, per-figure classification, per-series provenance, per-claim file and function, and the shared-number source.
- Two countable AI tells in `geometric_audit.py`: `callout-stripe-default` and `uniform-card-grid`.
- Rules in `figure-reconstruction.md` (illustrative vs evidential, provenance, the shared number), `content-intent.md` (cuts and claim verification), and `anti-slop-editing` (gated vs attested tells).

## What the record must carry

| Section | Fails when |
|---|---|
| `figures` | a figure is unclassified; an evidential series names no computation; an illustrative figure does not attest that it labels the rule rather than a value |
| `content_cuts` | absent or empty |
| `code_claims` | a claim omits its file or function |
| `authorship` | absent or empty |
| `shared_numbers` | a number quoted in both a figure and its prose names no single source |

The defects behind three of these are specific. A series with no computation is
a hardcoded list chosen to look right. A claim about code is indistinguishable
from a verified one in the finished document; the difference exists only in
whether anyone opened the file. And the source project's quoted figure flipped
between 4.7 and 27.8 depending only on where a window was cut.

## The two tells both needed narrowing, and real output said so

First implementation failed BOTH repository handbooks: 8 stripes and 5 card
grids each. Inspecting the matches rather than raising the threshold:

- The grid check matched `figure > ol` - an ordered list. A list's items all span the container, so their widths are trivially equal. A card grid puts cards SIDE BY SIDE, so the check now requires more than one column per row.
- The stripe check counted bordered `<figure>` elements. A frame is not a callout; the tell is a TEXT block leaning on a coloured edge for emphasis.

Both handbooks now pass. Because a check that stops firing needs proof it still
can, `ai-tells.html` exercises each device as the document's default and
`ai-tells-restrained.html` uses the SAME stylesheet once each:

```
ai-tells             fail   callout-stripe-default=5, uniform-card-grid=4
ai-tells-restrained  pass   -
overview             pass   -
distribution         pass   -
```

The count is the tell, not the device. `--tell-threshold` exists so a document
that genuinely wants eight callouts can say so.

This is the third time in this plan that a check was too broad on first write
and real generated output corrected it within minutes. It has been the most
reliable review step available.

## Verification

```
python -m pytest tests/skills/test_attestation.py -q
  17 passed in 0.28s

python -m pytest tests/skills/test_geometric_audit.py -q
  35 passed in 27.47s

python scripts/ci/run.py --profile fast
  PASS: 14 passed, 0 failed, 0 skipped, 0 advisory in 8.5s
```

### Negative controls

| Assertion | Control |
|---|---|
| each required section is required | removing it fails; emptying it fails |
| the gate does not score content | a complete record with awful prose passes |
| the tells count a pattern | `--tell-threshold 99` silences both while the document is unchanged |
| an absent record is not a pass | a missing file exits 2, not 0 |

## CI impact

Recorded against `cicd-architect`; no pipeline file edited.

- **New test path**: `tests/skills/test_attestation.py`, covered by the existing `repo-tests` glob.
- **Two new fixtures**; static HTML.
- **No new dependency.** `check_attestation.py` is stdlib-only and launches no browser, so it runs anywhere, CI included.
- **Not yet wired into a profile.** Wiring the composite gate is Phase 6's stated deliverable; recorded here so the omission is deliberate rather than forgotten.

## Phase 5 exit checklist

- [x] A missing or empty attestation fails the build.
- [x] No attestation gate scores taste or asserts a judgement the machine made.
- [x] Mechanically detectable tells are gated directly rather than attested.
- [x] Exactly one scoped local commit; no push.
