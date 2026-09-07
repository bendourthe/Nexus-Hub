# Verifier Taxonomy

Every deliverable is graded by something. Naming that something is what stops "the output looks good" from being the grade. This file classifies the available verifiers, says which ones fit common knowledge-work deliverables, and states the three rules that govern how they are combined.

## Part one: the four verifier classes

| Class | Examples | Strength | Main weakness |
|---|---|---|---|
| Deterministic | Schema checks, calculations, test suites, linting, required-field presence, duplicate detection, URL resolution. | Fast, reproducible, and cheap enough to run on every iteration. | Rewards literal compliance. A deliverable can satisfy every deterministic check and still be semantically wrong. |
| Evidence-based | Citation coverage, source authority, freshness, cross-source consistency, data reconciliation against a system of record. | Grounds the output in facts outside the producer, which is the only class that can catch confident invention. | Needs a designed source policy up front: which sources count, how fresh is fresh, what authority means here. |
| Model-based | Rubric scoring, pairwise comparison, natural-language assertions, multi-judge consensus. | Scales nuanced review to a volume no human can read. | Non-deterministic, and shares the producer's biases when it shares the producer's model. |
| Human | Subject-matter review, editorial approval, risk acceptance. | Best alignment to what a stakeholder actually wants. | Slow, costly, and inconsistent without a rubric to anchor it. |

## Part two: natural verifiers by deliverable

For each knowledge-work deliverable, the deterministic and evidence-based checks that fit it without inventing new machinery. These are the cheap classes; a model-based or human pass sits on top of them, never instead of them.

| Deliverable | Deterministic checks | Evidence-based checks |
|---|---|---|
| Deep research | Required sections present, citation format valid, no duplicate sources under different labels, cited URLs resolve. | Citation coverage over factual claims, source authority and freshness, cross-source agreement on each load-bearing claim. |
| Report generation | Template sections present, figures and tables referenced from the body, internal cross-references resolve, no placeholder text left. | Every number traceable to a named source, consistency between the narrative and the figures it describes. |
| Spreadsheet or financial analysis | Formulas recalculate, totals reconcile to their components, units and currencies consistent, no hardcoded value where a reference belongs. | Inputs reconciled against the system of record, period-over-period continuity with the prior published figure. |
| Document review | Every clause or section covered exactly once, required checklist items each addressed, findings carry a location. | Each finding grounded in a quoted passage, cited authority or standard actually says what the finding claims. |
| Competitive intelligence | Entity list de-duplicated, each competitor covered on the same dimensions, no dimension silently blank. | Each claim about a competitor sourced to that competitor or a named third party, source dates recorded. |
| Data cleanup and enrichment | Schema conformance, type and range checks, duplicate-key detection, row-count reconciliation before and after. | Enriched values verified against the authoritative source, sampled records re-checked end to end. |
| Presentation generation | Slide count and section order against the brief, every claim on a slide traceable to the source document, no overflowing text box. | Figures match the underlying data, quoted material matches the original wording. |

## Part three: three rules

**Combine at least two classes.** No single class covers every failure mode: deterministic checks miss semantic weakness, evidence-based checks miss structural incoherence, model-based checks miss what their own model is blind to, and human review misses what a rubric never asked about. A deliverable graded by one class is graded on one axis, and the failures it ships are the ones that axis cannot see. Pair a cheap deterministic pass with an evidence-based pass by default, and add the expensive classes where the cheap ones have a known blind spot.

**The producer is never the sole approver.** An agent that both produced the work and judged it complete has performed one act, not two, and the judgement inherits every assumption the production made. This holds even when the judgement is sincere and the rubric is good. The carve-out is narrow: maker and checker may be the same agent when the check is a deterministic non-model oracle, such as an exit code, a numeric reconciliation, or a compiler result, because that oracle is its own independent evidence. Whenever the checker is itself a model, the maker must not also be the checker. Cross-link [[adversarial-verifier]] for the hostile pass, which is the strongest form of this rule.

**Verify progress, not only the final artifact.** A run that is graded only at the end cannot tell a productive trajectory from an expensive one, and cannot stop early either way. Track the per-cycle delta on the check metric, stagnation (no measurable movement across N cycles), and quality per unit cost rather than quality alone, because a better score bought with ten times the compute is not a better result. Review the trace rather than trusting the summary of it: see the `trace_log` field and its optional `score` in [loop-engineering's loop schema](../../../workflow/loop-engineering/references/loop-schema.md) for the per-iteration record this reads, and [`evaluator-validation.md`](evaluator-validation.md) for the held-out split that keeps an improving score honest.
