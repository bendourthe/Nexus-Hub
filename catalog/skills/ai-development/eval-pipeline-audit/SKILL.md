---
name: eval-pipeline-audit
description: Audit an existing LLM or RAG evaluation pipeline end to end, produce a gap matrix over ten evaluation concerns, and route each gap to the skill that owns the fix. Make sure to use this skill whenever the user says "audit our evals", "review our evaluation setup", "why are our evals unreliable", "our eval scores do not match production", "is our LLM judge trustworthy", "we have evals but they never catch anything", "our eval suite is green and users still complain", or otherwise asks about the health of an evaluation process rather than about running one measurement. SKIP, do NOT use for, writing unit or integration tests for ordinary code (use unit-tests or integration-test-generator), rewriting a single judge or system prompt (use prompt-engineering), building or tuning a RAG pipeline itself (use rag-implementation), or scoring one batch of outputs against a rubric (use ai-output-evaluation).
summary_l0: "Audit an evaluation pipeline end to end and route each gap to its owning skill"
overview_l1: "This skill audits an existing evaluation process rather than performing one evaluation. It inventories ten concerns in a fixed order - objectives, datasets, split provenance, evaluators, thresholds, traces, human labels, regression cases, feedback loops, and deployment gates - records what exists for each as a present, partial, or absent finding, and only then produces a prioritized gap matrix. Each gap routes to the skill that owns the method: retrieval measurement to rag-implementation, error analysis and evaluator calibration to ai-output-evaluation, paired benchmark runs to skill-eval-loop, judge-prompt design to prompt-engineering, and any export of traces or labels to egress-redaction. It duplicates no specialist method, which is what keeps it thin and keeps the owners authoritative. All inputs stay local by default. Trigger phrases: audit our evals, review our evaluation setup, why are our evals unreliable, is our LLM judge trustworthy, our eval suite never catches anything."
---

# Evaluation Pipeline Audit

Audit an evaluation process as a system. The question this skill answers is not "how did the model score" but "would this pipeline have told us if the model got worse". Those are different questions, and a green eval suite that has never failed is usually evidence for the second one being answered badly.

This is a router. It owns one thing - the inventory-then-gap-matrix pass - and delegates every method to the skill that owns it. When you find yourself explaining how to compute Recall@k or how to validate a judge, stop and route instead.

## When to Use This Skill

Use this skill when:

- An evaluation suite exists and its trustworthiness is in question ("our evals are green and users still complain")
- Eval scores and production behavior disagree
- Someone is about to gate a release on an LLM judge that has never been validated
- An evaluation process was inherited and nobody knows what it covers
- A team wants to know what to build next in their evaluation, and needs the gaps ranked

**When NOT to use this skill:**

| The ask | Route to |
|---------|----------|
| Write unit or integration tests for ordinary code | `[[unit-tests]]`, `[[integration-test-generator]]` |
| Rewrite one judge prompt or system prompt | `[[prompt-engineering]]` |
| Build, tune, or debug the RAG pipeline itself | `[[rag-implementation]]` |
| Score one batch of outputs against a rubric | `[[ai-output-evaluation]]` |
| Benchmark one Nexus-Hub skill against a no-skill baseline | `[[skill-eval-loop]]` |

**Trigger phrases**: "audit our evals", "review our evaluation setup", "why are our evals unreliable", "our eval scores do not match production", "is our LLM judge trustworthy", "we have evals but they never catch anything".

## Instructions

### Step 1: Inventory before recommending

Walk all ten concerns in order and record what exists. Do not skip ahead to recommendations: an audit that starts with an opinion finds evidence for that opinion. Each concern maps to a named artifact so the finding is checkable rather than impressionistic.

| # | Concern | What to look for | Artifact |
|---|---------|------------------|----------|
| 1 | Objectives | A written statement of what "good" means, and the decision each score informs | - |
| 2 | Datasets | The evaluation cases, their count, and what they are meant to cover | `dataset_manifest` |
| 3 | Split provenance | How data divides into tune and held-out portions, and how often the held-out portion has been used | `split_manifest` |
| 4 | Evaluators | What produces each score: a rubric, a model judge, a deterministic check, or a human | `evaluator_result` |
| 5 | Thresholds | The pass bar, who set it, and what evidence set it there | - |
| 6 | Traces | Whether real executions are captured, and how they were sampled | `trace_sample` |
| 7 | Human labels | Ground-truth annotations, who produced them, and whether review was blind | `human_annotation` |
| 8 | Regression cases | Confirmed failures promoted into permanent checks | `regression_case` |
| 9 | Feedback loops | Whether findings change the system, and whether the change is verified | `adjudication_record` |
| 10 | Deployment gates | What the scores actually block, and whether anyone can override | - |

Record each as **present**, **partial**, or **absent**, with the evidence you saw. "They said they have a test set" is not evidence; a file, a count, and a field are.

The artifact names come from the shared evaluation artifact contract. A project that has never heard of that contract still has these things or lacks them; the names give the audit a stable vocabulary, not a prerequisite.

### Step 2: Build the gap matrix

One row per concern. Severity is determined by consequence, not by how far the finding sits from best practice.

```markdown
| # | Concern | Status | Evidence | Severity | Owner |
|---|---------|--------|----------|----------|-------|
| 3 | Split provenance | absent | One `cases.json`, no split; threshold tuned on all 40 cases | BLOCKING | ai-output-evaluation |
| 6 | Traces | partial | Failures captured, successes not | HIGH | ai-output-evaluation |
```

Severity rules, applied in order:

- **BLOCKING** - the pipeline can report a passing score while the system is broken. Any of: no held-out split when a threshold gates a release; an unvalidated judge used as a gate; retrieval never measured in a RAG system; no regression cases despite known past failures.
- **HIGH** - the pipeline gives a real signal but a known failure mode is invisible to it. Typically: failure-biased sampling reported as a base rate, no human labels behind a judge, thresholds with no recorded rationale.
- **MEDIUM** - the pipeline is sound but expensive, slow, or awkward to maintain.

The order matters. Teams routinely fix MEDIUM items because they are easy, while a BLOCKING gap keeps shipping regressions.

### Step 3: Route each gap to its owner

Never fix a gap inline by explaining the method. Hand it to the owner:

| Gap area | Owner |
|----------|-------|
| Retrieval quality never measured, or measured after generation | `[[rag-implementation]]` (its `references/evaluation.md`) |
| Failures never classified; no taxonomy; no regression cases | `[[ai-output-evaluation]]` (`references/error-analysis.md`) |
| Judge never validated against labels; thresholds tuned on the test split | `[[ai-output-evaluation]]` (`references/evaluator-validation.md`) |
| Rubric has no dimensions, no evidence requirement, or unmitigated bias | `[[ai-output-evaluation]]` |
| Evaluation set too small or unrepresentative | `[[ai-output-evaluation]]` (`references/synthetic-data.md`) |
| Human review is unblinded, unadjudicated, or has no schema | `[[ai-output-evaluation]]` (`references/review-interface.md`) |
| The judge prompt itself is weak or unstable | `[[prompt-engineering]]` |
| A Nexus-Hub skill needs a paired with-skill / baseline benchmark | `[[skill-eval-loop]]` |
| Any trace, label, or example needs to leave the host | `[[egress-redaction]]` |

If a gap has no owner in this table, say so plainly in the report rather than inventing a method for it.

### Step 4: Report

Deliver three things and nothing else:

1. The inventory, ten rows, with evidence.
2. The gap matrix, sorted by severity.
3. A next-three list: the three gaps to close first, each naming its owning skill and the observable condition that will show it is closed.

Cap the recommendation list at three. An audit that returns fourteen action items returns none.

## Local-data handling

Evaluation inputs are among the most sensitive artifacts a project holds: real user prompts, production traces, and human labels about real interactions. This skill reads them and must not spread them.

- **Local by default.** Everything the audit reads stays on the host. The audit produces findings, not copies of the data.
- **Bounded excerpts only.** When a finding needs an example, quote the smallest excerpt that supports it - a single field, a one-line snippet - never a full trace.
- **Redact identifiers in the report.** Names, emails, account ids, and tokens appearing in a quoted excerpt are replaced with typed markers before the finding is written down. The finding survives redaction; that is how you know the excerpt was the right size.
- **Explicit authorization before any egress.** An audit report shared into a ticket, a chat, or a third-party service is an egress event. Apply `[[egress-redaction]]`'s per-category policy first. Reporting an aggregate never requires exporting the underlying data.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Our eval suite is green, so the pipeline is healthy." | A suite that has never failed is more often unable to fail than proof of quality. Concern 8 exists for this: if no past production failure has a regression case, the suite is measuring what already worked. |
| "We have a test set, so we can trust the threshold." | Ask concern 3 instead: how many times has that set been used to pick the threshold? A held-out split evaluated against twenty times during tuning is a training set with a misleading name, and the score it reports is optimism, not accuracy. |
| "The judge agrees with me when I spot-check it, so it can gate the release." | Spot-checking confirms agreement on the cases you chose to look at, which are rarely the ambiguous ones. A gate needs measured agreement against held-out labels; without it the judge's failure mode is unknown, and that is a BLOCKING gap, not a MEDIUM one. |
| "Answers look bad, so I will start with the generation prompt." | In a RAG system this skips concern 6 and the retrieval-first order. A passage never retrieved cannot be used, and every hour spent on the prompt is spent on the half that was working. Measure retrieval first. |
| "I already know the main problem, so a full inventory is wasted effort." | The ten-concern walk is what separates the gap you noticed from the gap that is actually blocking. Starting from a conclusion reliably finds the MEDIUM item you already had in mind and misses the missing split behind it. |
| "I will just explain how to validate a judge while I am here." | That method belongs to `ai-output-evaluation`, and a second copy of it starts drifting the day it is written. Routing keeps one authoritative version; explaining creates two. |

## Verification

- [ ] All ten concerns were inventoried before any recommendation was made
- [ ] Each concern is marked present, partial, or absent with concrete evidence, not a claim someone made
- [ ] Every gap carries a severity assigned by consequence, and the BLOCKING rules were applied
- [ ] Every gap names an owning skill, or is explicitly reported as having no owner
- [ ] No specialist method (metric formulas, calibration procedure, rubric design) is reproduced in the audit output
- [ ] The recommendation list contains at most three items, each with an observable closing condition
- [ ] Every quoted excerpt is bounded and has identifiers replaced with typed markers
- [ ] No trace, label, prompt, or example left the host without an explicit authorization step

## Related Skills

- [[rag-implementation]] -- owns retrieval measurement and the retrieval-before-generation diagnostic order
- [[ai-output-evaluation]] -- owns error analysis, evaluator validation, synthetic data, and human review
- [[skill-eval-loop]] -- owns paired with-skill / baseline benchmarking for Nexus-Hub skills
- [[prompt-engineering]] -- owns the design of the judge prompt this skill only assesses the trustworthiness of
- [[egress-redaction]] -- owns the policy applied before any audit artifact crosses a trust boundary
- [[verification-before-completion]] -- the wider discipline of requiring fresh evidence before a completion claim

---

**Version**: 1.0.0
**Last Updated**: August 2026
**Author**: Nexus-Hub
