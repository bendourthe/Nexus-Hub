---
name: ai-output-evaluation
description: Evaluate AI-generated output quality using LLM-as-judge techniques, multi-dimensional rubrics, and bias mitigation. Use when building AI-powered features that need quality assurance, evaluating generated code or documentation, or designing automated review pipelines.
summary_l0: "Evaluate AI-generated output quality with rubrics, LLM-as-judge, and bias mitigation"
overview_l1: "This skill provides specialized expertise in systematically evaluating the quality of AI-generated output (code, documentation, analysis, tests) using structured rubrics, LLM-as-judge patterns, and bias mitigation techniques. Use it when evaluating quality of AI-generated code before merging, building automated quality gates for AI-powered pipelines, designing review rubrics for generated documentation, comparing outputs from different models or prompts, setting up continuous evaluation for AI-assisted workflows, or assessing whether AI-generated tests provide real coverage. Key capabilities include multi-dimensional rubric design, LLM-as-judge implementation with calibration, output comparison across models, bias detection and mitigation in evaluations, automated quality gate creation, and evaluation pipeline design. The expected output is evaluation reports with dimensional scores, bias analysis, and pass/fail recommendations. Trigger phrases: evaluate AI output, quality rubric, LLM as judge, output evaluation, generated code quality, review AI work, evaluation pipeline, bias in evaluation."
---

# AI Output Evaluation

Specialized expertise in systematically evaluating the quality of AI-generated output (code, documentation, analysis, tests) using structured rubrics, LLM-as-judge patterns, and bias mitigation techniques.

## When to Use This Skill

Use this skill for:

- Evaluating quality of AI-generated code before merging
- Building automated quality gates for AI-powered pipelines
- Designing review rubrics for generated documentation
- Comparing outputs from different models or prompts
- Setting up continuous evaluation for AI-assisted workflows
- Assessing whether AI-generated tests provide real coverage

**Trigger phrases**: "evaluate AI output", "quality rubric", "LLM as judge", "output evaluation", "generated code quality", "review AI work", "evaluation pipeline", "bias in evaluation"

## What This Skill Does

Provides AI output evaluation capabilities including:

- **Rubric Design**: Building multi-dimensional scoring frameworks
- **LLM-as-Judge**: Using AI to evaluate AI output systematically
- **End-State Evaluation**: Evaluating final artifacts rather than intermediate steps
- **Bias Mitigation**: Detecting and correcting systematic evaluation biases
- **Token Economics**: Understanding the cost-quality relationship
- **Evaluation Pipelines**: Automating quality assessment in workflows

## Instructions

### Step 1: Define Evaluation Dimensions

Every evaluation needs explicit dimensions. Without defined criteria, evaluation devolves into subjective "looks good" assessments.

**Multi-Dimensional Rubric Template**:

```markdown
## Evaluation Rubric: [Output Type]

### Dimensions

| Dimension | Weight | 0.0 (Fail) | 0.5 (Partial) | 1.0 (Pass) |
|-----------|--------|-----------|---------------|------------|
| **Correctness** | 30% | Contains errors or wrong logic | Mostly correct with minor issues | Fully correct, handles edge cases |
| **Completeness** | 25% | Missing major components | Covers main cases, misses edges | Comprehensive coverage |
| **Style Adherence** | 15% | Ignores project conventions | Partially follows conventions | Fully consistent with codebase |
| **Security** | 15% | Contains vulnerabilities | No obvious issues, not hardened | Proactively secure (input validation, etc.) |
| **Performance** | 15% | Obvious bottlenecks | Acceptable performance | Optimized for the use case |

### Scoring
- Weighted score: Sum of (dimension_score x weight)
- Pass threshold: >= 0.70
- Requires review: 0.50-0.69
- Fail: < 0.50
```

**Rubric Variants by Output Type**:

| Output Type | Key Dimensions |
|-------------|---------------|
| **Generated code** | Correctness, completeness, style, security, performance |
| **Documentation** | Accuracy, clarity, completeness, structure, audience-appropriateness |
| **Test suites** | Coverage, edge case detection, isolation, maintainability, speed |
| **Analysis reports** | Factual accuracy, completeness, actionability, source quality |
| **Refactoring** | Behavior preservation, code quality improvement, test continuity |

### Step 2: Implement LLM-as-Judge

Use a structured prompt to have an LLM evaluate output against the rubric. The key is requiring **evidence-based justification** for each score (chain-of-thought improves reliability by 15-25%).

**Direct Scoring Prompt Template**:

```markdown
## Evaluation Task

You are evaluating the following [output type] against a quality rubric.

### Output to Evaluate
[The AI-generated output]

### Context
- Task description: [What was requested]
- Project conventions: [Relevant style/patterns]
- Constraints: [Requirements, limitations]

### Rubric
[Paste the rubric from Step 1]

### Instructions
For each dimension:
1. Quote specific evidence from the output (good or bad)
2. Assign a score (0.0-1.0) with justification
3. List specific improvements needed

### Required Output Format
```json
{
  "dimensions": {
    "correctness": {
      "score": 0.8,
      "evidence": ["Line 45: correctly handles null case", "Line 72: missing boundary check for negative values"],
      "improvements": ["Add check for negative input values"]
    },
    // ... other dimensions
  },
  "weighted_score": 0.76,
  "verdict": "PASS",
  "summary": "One-sentence overall assessment"
}
```
```

**Critical rule**: Always require evidence quotes. Without evidence, LLM judges default to generous scores (verbosity bias).

### Step 3: Design End-State Evaluation

Evaluate **final artifacts**, not intermediate steps. AI agents are non-deterministic; two agents may take completely different paths to equally good results. Evaluating the process (number of steps, tools used, approach taken) penalizes valid alternative solutions.

**End-State Evaluation Principles**:

| Principle | Explanation |
|-----------|------------|
| **Evaluate artifacts, not steps** | A working function matters more than how it was written |
| **Allow multiple valid solutions** | Don't penalize creative approaches that achieve the goal |
| **Test behavior, not structure** | Run the code; check the output; verify the tests pass |
| **Measure what matters** | "Does it solve the problem?" over "Does it look like what I expected?" |

**End-State Evaluation Checklist**:

```markdown
## End-State Evaluation: [Task]

### Functional Verification
- [ ] Output compiles/parses without errors
- [ ] All existing tests still pass
- [ ] New functionality works as specified
- [ ] Edge cases handled (or explicitly documented as out of scope)

### Quality Verification
- [ ] Rubric score >= threshold (Step 1)
- [ ] No security vulnerabilities introduced
- [ ] Performance acceptable for the use case
- [ ] Code follows project conventions

### Integration Verification
- [ ] Changes integrate with existing codebase
- [ ] No regressions in dependent components
- [ ] Documentation updated if needed
```

### Step 4: Mitigate Evaluation Bias

LLM judges exhibit systematic biases that skew scores. Recognizing and mitigating the top 3 biases significantly improves evaluation reliability.

**Top 3 Practical Biases**:

| Bias | Description | Mitigation |
|------|-------------|------------|
| **Verbosity bias** | Longer, more detailed outputs receive higher scores regardless of quality. A 100-line function gets rated higher than a correct 10-line function. | Include rubric criterion: "Conciseness: penalize unnecessary complexity." Explicitly state: "A shorter correct solution is better than a longer correct solution." |
| **Position bias** | In pairwise comparisons, the first option is favored. | Evaluate twice with swapped positions; flag inconsistencies. |
| **Self-enhancement bias** | Models rate their own output (or output in their style) higher than alternatives. | Use a different model as judge when possible, or use human spot-checks to calibrate. |

**Bias Mitigation Protocol**:

```markdown
## Bias Mitigation Checklist

### Before Evaluation
- [ ] Rubric explicitly penalizes unnecessary verbosity
- [ ] "Shorter correct > longer correct" stated in instructions
- [ ] Evidence requirement included (no scoring without quotes)

### During Evaluation (for pairwise comparisons)
- [ ] Evaluate with options in original order
- [ ] Evaluate with options in swapped order
- [ ] Flag if scores differ by > 0.2 between orderings
- [ ] Use majority vote across 3 evaluations for high-stakes decisions

### After Evaluation
- [ ] Spot-check 10-20% of scores against human judgment
- [ ] Track score distributions; investigate if average is consistently > 0.8 (calibration drift)
- [ ] Update rubric if a dimension consistently scores too high or too low
```

### Step 5: Track Token Economics

Understanding the relationship between token usage and output quality helps allocate resources effectively.

**Key Finding**: Token usage accounts for approximately **80% of output quality variance** in agent tasks. Tool call frequency contributes ~10%, and model selection ~5%.

**What This Means in Practice**:

| Situation | Implication |
|-----------|------------|
| Agent produces low-quality output | First check if it had enough context (tokens); model switching is rarely the fix |
| Budget is constrained | Invest tokens in context quality (better prompts, relevant file reads) over more turns |
| Evaluation scores are inconsistent | Check if the evaluator has enough context to judge properly |

**Cost-Quality Framework**:

```markdown
## Token Budget for Evaluation Pipeline

### Per-Item Evaluation Cost
- Input: ~2,000 tokens (output + rubric + context)
- Output: ~500 tokens (structured evaluation result)
- Total: ~2,500 tokens per evaluation

### Pipeline Cost Estimate
- Items to evaluate: [N]
- Per-item cost: ~2,500 tokens x [price/1K tokens]
- Total: [N x 2,500 / 1000 x price]
- Budget for re-evaluation (20% of items flagged): + 20%
```

## Evaluating Output vs Validating the Evaluator

Steps 1 through 5 above score output: given a rubric, how good is this artifact. A separate question is whether the scorer itself is right. An unvalidated judge that gates a release has not removed human judgment from the loop; it has replaced it with an unmeasured one.

Two Tier-3 references own the deeper methods. Read them when the work goes past scoring a batch:

| You need to ... | Read | It covers |
|---|---|---|
| Turn failing outputs into quantified categories and permanent coverage | `references/error-analysis.md` | Trace sampling and what each method can and cannot support, non-overlapping taxonomies with exclusion criteria, multi-label conventions, severity x frequency ranking, root-cause hypotheses with refuting evidence, promotion to regression cases |
| Prove a judge agrees with labeled evidence before it gates anything | `references/evaluator-validation.md` | Train / development / held-out separation, blind annotation and adjudication, the confusion matrix, precision / recall / specificity, threshold tuning on development data only, confidence intervals, prevalence effects, recalibration triggers |
| Build an evaluation set that covers what it claims to cover | `references/synthetic-data.md` | Dimensions and allowed values, constraints, pairwise coverage targets, batched generation against named cells, duplicate and source-leakage filters, difficulty validation, human spot checks, and keeping synthetic cases out of the held-out split |
| Collect human labels whose bias you can reason about | `references/review-interface.md` | Annotation schema, blind review, randomized ordering, keyboard-first and accessible controls, confidence and abstention, adjudication, append-only history, local autosave and resume, deterministic export with no implicit upload |

Two rules from those references are load-bearing enough to state here:

- **Thresholds are tuned on development data and measured once on held-out data.** Re-tuning against the held-out split and reporting the improved number converts a test set into a training set, and the reported figure into optimism.
- **Precision is not a property of the judge.** Hold recall and specificity fixed and change only how often failures actually occur, and precision moves enormously - in the worked example, from 0.60 at a 30 percent failure rate to 0.16 at 5 percent. Always re-check precision at the prevalence the evaluator will actually meet.
- **Coverage is verified after generation, not assumed from the plan.** Declaring a pairwise target and generating against it does not mean the target was hit. Recompute achieved coverage from the promoted cases and report the uncovered cells; those are the next batch's plan.
- **Abstention is a signal, never an imputed label.** A reviewer forced to choose on an item the rubric does not cover produces a fabricated label indistinguishable from a real one. Report abstention rate alongside every label distribution.

## Reproducible Receipts

When an evaluation produces a headline score (an LLM-as-judge rate, a rubric average, a pass/fail proportion), back it with a reproducible receipt rather than reporting the bare number. Attach three things: a committed artifact from which the score recomputes (the per-item results file the dimensional scores roll up from), a single documented recompute step so a reader can verify the headline without rerunning the judge, and a confidence interval - or, when the sample is too small for a meaningful interval, an explicit "preliminary / small-sample" label instead of a bare percentage. A score with no committed source and no interval is an opinion wearing a number. This is the same discipline `[[skill-eval-loop]]` applies to skill benchmarks; see it for the fuller treatment (committed `benchmark.json`, a single aggregate step, and a Wilson interval per rate).

### Step 6: Report Reliability as pass@k and pass^k

A single pass or fail is one sample of a distribution. Agent reliability is a measured metric across repeated independent trials, and this skill owns the two definitions every other skill references:

- **pass@k**: the eval passes in at least one of k independent trials. Use it for capability ("can the agent do this at all").
- **pass^k**: the eval passes in all k independent trials. Use it for safety-critical behavior, where one failure in k is the finding.

Rules that make the numbers honest:

1. Record every individual trial result (pass, fail, errored, incomplete), not only the aggregate; the aggregate must recompute from the recorded trials.
2. An errored or incomplete trial is recorded as such and counts as a non-pass in both metrics. It is never dropped, because dropping it inflates the figure.
3. A retried trial is not an independent trial. Record the retry as a new trial alongside the one it repeats; it does not replace it.
4. Report k and the individual results next to the figure, and attach the receipt-and-interval discipline from the eval loop (a committed artifact, one recompute step, an interval or an honest small-N label).

**Rule ownership**: `ai-output-evaluation` owns these definitions and the counting rules. `skill-eval-loop` runs the trials and reports with them; `quality-gate-definitions` consumes them in its gates. Neither restates the definitions.

## Best Practices

- **Define rubrics before generating output**: Knowing evaluation criteria shapes better prompts
- **Require evidence for every score**: Unjustified scores are unreliable
- **Evaluate end states, not processes**: Allow creative solutions
- **Calibrate with human judgments**: Spot-check regularly to catch drift
- **Use appropriate granularity**: Binary (pass/fail) for simple checks; 0.0-1.0 for nuanced assessment
- **Track trends over time**: If average scores drift upward, tighten rubrics or re-calibrate
- **Budget for evaluation tokens**: Evaluation is not free; plan token costs into pipelines

## Common Patterns

### Pattern 1: Code Review Rubric

**Situation**: Evaluating AI-generated code before merging to main.

**Solution**:
1. Define rubric: correctness (30%), completeness (25%), style (15%), security (15%), performance (15%)
2. Run end-state checks: compilation, existing tests, new functionality
3. Apply LLM-as-judge with evidence requirement
4. Flag items scoring <0.70 for human review

### Pattern 2: Documentation Quality Gate

**Situation**: Automated documentation generation needs quality assurance.

**Solution**:
1. Define rubric: accuracy (35%), clarity (25%), completeness (20%), structure (10%), audience fit (10%)
2. Evaluate against the actual codebase (does the doc match the code?)
3. Check for common doc failures: outdated API references, missing parameters, wrong examples

### Pattern 3: Generated Test Evaluation

**Situation**: AI-generated test suites need validation that they provide real coverage.

**Solution**:
1. Run the tests (do they pass?)
2. Check coverage metrics (do they cover the target code?)
3. Mutation testing (do they catch intentional bugs?)
4. Review test quality: independence, meaningful assertions, edge cases

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The output looks good, so it passes" | "Looks good" is the verbosity-bias trap this skill exists to break; a 100-line function that reads well can still fail a correctness dimension a rubric would have caught. |
| "I trust the LLM judge's score, no need for evidence" | Without an evidence quote per dimension, judges default to generous scores; an unjustified 0.9 hides the missing boundary check on line 72. |
| "One evaluation pass is enough for this comparison" | Position bias favors the first option; a single pairwise pass can flip verdict when the order is swapped, so high-stakes calls need a swapped re-run. |
| "We can skip token budgeting for the eval pipeline" | Evaluation costs ~2,500 tokens per item plus 20% re-eval; skipping the estimate means the pipeline silently blows its budget partway through a batch. |
| "The judge agrees with my spot-checks, so it can gate releases" | Spot-checks confirm agreement on the cases you chose to look at, which are rarely the ambiguous ones. A gate needs precision and recall measured against held-out labels; without them the judge's failure mode is unknown, and at production prevalence its precision can be a quarter of what the validation set showed. |
| "The judge is 95% accurate, so it is ready" | Accuracy alone hides the imbalance: when 95% of items pass, a judge that passes everything scores 0.95 accuracy with 0.0 recall and catches nothing. Report precision, recall, and specificity together or the headline is meaningless. |
| "We fixed the three failures we looked at, so error analysis is done" | Fixing sampled failures produces no reusable knowledge. Without a taxonomy, frequencies, and regression cases, the same patterns return and are rediscovered from scratch each time. |
| "I'll just generate 200 test cases and we'll have good coverage" | Unbounded generation clusters around whatever the generating model finds salient and almost never produces unanswerable queries, which is usually where a system behaves worst. Declaring dimensions first is what surfaces the cells nobody would have thought to ask for. |
| "The reviewers can see the model's verdict, it just speeds them up" | It speeds them up by turning checking into confirming. The resulting agreement number measures whether the human read the judge's answer, so it cannot be used to validate that judge. |

## Verification

- [ ] Any reliability figure is reported as `pass@k` or `pass^k` with k stated, every individual trial recorded (errored and incomplete trials included as non-passes), and no retry counted as an independent trial.
- [ ] A weighted rubric exists with explicit dimensions and a documented pass threshold
- [ ] Every LLM-as-judge score is accompanied by at least one evidence quote from the output
- [ ] Pairwise comparisons were run in both orderings and any >0.2 score divergence was flagged
- [ ] End-state checks ran: the output compiles/parses and existing tests still pass
- [ ] A 10-20% human spot-check of scores was performed for calibration
- [ ] Any evaluator used as a release gate has held-out evidence: precision, recall, and specificity measured once on a split never used for tuning, each with a confidence interval
- [ ] Any evaluator used as a release gate has a documented disagreement review: blind annotation, adjudicated conflicts, and rubric defects recorded as such
- [ ] Confirmed failure patterns were promoted to regression cases with minimized inputs and binary assertions (see `references/error-analysis.md`)
- [ ] Any generated evaluation cases declare their coverage dimensions, were filtered for duplicates and source leakage, were human spot-checked, and are absent from the held-out split (see `references/synthetic-data.md`)
- [ ] Any human review was blind, randomized, and captured confidence and abstention, with disagreements adjudicated and exported deterministically to a confirmed local path (see `references/review-interface.md`)

## Related Skills

- [[code-quality]] -- supplies the code-quality standards and review criteria a code rubric scores against
- [[testing-review]] -- the test-quality assessment methodology used when evaluating generated test suites
- [[final-report]] -- consolidates the dimensional scores and verdicts into an actionable review report
- [[context-manager]] -- ensures the judge has sufficient context, the dominant driver of evaluation quality
- [[eval-pipeline-audit]] -- audits a whole evaluation process and routes gaps here; this skill owns the methods it routes to
- [[rag-implementation]] -- owns retrieval measurement, which must be read before any generation metric in a RAG system
- [[egress-redaction]] -- governs any authorized export of traces, annotations, or labeled items produced by these workflows

---

**Version**: 1.0.0
**Last Updated**: February 2026
**Author**: Nexus-Hub
**Attribution**: Adapted from [Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) (MIT License)


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
