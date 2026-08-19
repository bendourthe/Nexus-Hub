# Decision: Split project memory across three surfaces with a gated decision-record tree

Status: implemented - decisions hold settled reasoning, known-gaps holds open work, solutions holds closed problems, each with a stated exclusion list

## Problem

Nexus-Hub accumulated project memory in places that overlapped without a stated boundary: per-version known-gaps files, a solutions knowledge base, an incident archive, and a distributed ADR template. Nothing recorded *why a design won and what it beat*, so declined designs were re-proposed. Two concrete cases: a platform default that was fabricated rather than found, shipped, and had to be withdrawn; and a third-party extension runtime declined on architectural grounds, then partially re-proposed later in a different form.

Adding a fourth store without defining the boundaries would have made the problem worse rather than better. The source comparison that motivated this work flagged it as the highest-conflict item for exactly that reason.

## Decision

Three surfaces, each answering one question, each with an explicit exclusion list in `docs/decisions/README.md`:

- `docs/decisions/` holds settled reasoning that is still binding: why a design won, and what it beat.
- `docs/v*/known-gaps.md` holds open work, expected to change.
- `docs/solutions/` holds closed problems with reproduction context.

`docs/incidents/` stays separate, answering what broke and what guardrail it motivated.

Records live at `docs/decisions/<lifecycle>/<class>/YYYY-MM-DD-<slug>.md` across a closed lifecycle set (`proposed`, `implemented`, `rejected`) and a closed class set (`architecture`, `policy`, `process`, `tooling`). `## Alternatives considered` is mandatory in every lifecycle. `scripts/validate_decision_records.py` enforces the structure in `make validate` and CI, and an `AGENTS.md` rule requires a record in the same pull request for non-trivial changes.

## Alternatives considered

- **Extend the existing known-gaps tracker with a "decisions" section.** Rejected: known-gaps is per-version and its entries are expected to close. Settled reasoning is not versioned and does not close, so it would have been repeatedly archived away with the version that happened to record it.
- **Use the distributed `catalog/memory/decisions.md` ADR template for this repo's own decisions.** Rejected, and the confusion is now guarded against. That file is shipped to end users' own projects; it is not this repository's memory. Writing repo decisions into it would change what every user receives.
- **A single flat `docs/decisions/*.md` directory with a Status field.** Rejected: the value of `rejected/` comes from being greppable as a unit before proposing something. A flat directory requires reading every file's frontmatter to find the declined ones, which nobody does.
- **Free-form ADRs with no validator.** Rejected: the mandatory-alternatives rule is the entire point, and an unenforced rule that costs effort is one people drop under deadline. The failure is silent, since a record with no alternatives still looks complete.
- **Migrate first, formalize later.** Rejected because there was nothing to migrate; see the withdrawn migration step recorded as `MT-4` in the v3.17 known-gaps.

## Consequences

- Non-trivial pull requests now carry documentation cost that they did not before. The exemption for mechanical and local edits is what keeps that proportionate, and it is stated in the rule rather than left to judgment.
- `rejected/` only pays off if people grep it before proposing. That habit is not enforceable by a validator, so the README states it explicitly and the tree ships seeded with two real declined designs rather than empty. An empty `rejected/` folder teaches nobody to look.
- A record moves between lifecycles by being rewritten and moved, not by editing a status field in place. That is more work than a one-word edit, and it is deliberate: an implemented record that still reads as a pitch tells the reader it was never revisited.
- `docs/decisions/**` had to be re-included in the CI path filters, because it is validator input sitting under a blanket `docs/**` exclusion. This is the third time that fix has been needed (after `docs/policy/**` and `docs/incidents/**`), which suggests the exclusion's default is wrong for guarded paths and may be worth inverting.
- The class set is closed, so a decision that fits none of the four classes is a signal to reconsider the taxonomy rather than to invent a folder. There is deliberately no `feature` class; feature intent lives in plans.
