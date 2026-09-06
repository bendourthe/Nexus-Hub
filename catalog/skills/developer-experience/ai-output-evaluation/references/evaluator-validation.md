# Evaluator Validation and Calibration

How to prove an evaluator agrees with labeled evidence before you let it gate anything. Read this cold: it assumes no other part of the evaluation skill is in context.

Evaluating output and validating the evaluator are different activities. The first asks "is this output good"; the second asks "is this scorer right". An unvalidated judge that gates a release does not remove human judgment from the loop - it replaces it with an unmeasured one.

## Step 1: Separate the data three ways

An evaluator is a model of human judgment, and it is tuned. Tuned things overfit, so the split is not bureaucracy.

| Split | Used for | Never used for |
|-------|----------|----------------|
| **train** | Writing and revising the rubric; picking few-shot examples | Reporting any number |
| **development** | Tuning the threshold; comparing prompt variants; iterating | Reporting the final number |
| **held-out test** | The single final measurement | Any tuning decision, ever |

Record the division as a `split_manifest`: `split_method` (`random_seeded`, `stratified`, `temporal`, `manual`), the `seed` if seeded, and `holdout_touched_count`.

`holdout_touched_count` is the honesty mechanism. Every evaluation against the held-out split increments it. At 1, the reported number means what it says. By 10, the threshold has been fitted to the test set through your own decisions, and the number is optimism. When the count gets away from you, the fix is a fresh held-out split, not a smaller number.

**Stratify when classes are unbalanced.** If 8 percent of items fail, a random 50-item test split may contain 2 failures, and recall computed on 2 items is noise.

## Step 2: Establish ground truth

The evaluator is measured against `human_annotation` records, so their quality is the ceiling on everything downstream.

- **Blind the reviewer.** `blind: true` means the annotator cannot see the judge's verdict, the system's identity, or another reviewer's label. An unblinded reviewer confirms the judge rather than checking it, and the resulting agreement number is circular.
- **Double-label a portion.** Have two annotators label 20 percent independently. Their agreement is the ceiling for the judge: if humans agree only 70 percent of the time, a judge scoring 85 percent against one of them is fitting that annotator's idiosyncrasies, not measuring quality.
- **Record abstentions.** `abstained: true` is a signal about the rubric, not a missing value to impute. A cluster of abstentions means the rubric does not cover a real case.
- **Adjudicate disagreements and keep the record.** Every `adjudication_record` carries a `resolution_method` and `taxonomy_change_required`. A disagreement traced to an ambiguous category is a rubric defect; recording it is what causes the rubric to improve.
- **Pseudonymize annotators.** `annotator_id` is a stable opaque identifier, never a real name.

## Step 3: Build the confusion matrix

Fix a convention and state it, because every metric below flips meaning if it silently changes. Convention used here: **positive = the evaluator flags the item as failing.**

|  | Human: fail | Human: pass |
|---|---|---|
| **Judge: fail** | True Positive (TP) | False Positive (FP) |
| **Judge: pass** | False Negative (FN) | True Negative (TN) |

```
Precision              = TP / (TP + FP)
Recall (TPR)           = TP / (TP + FN)
Specificity (TNR)      = TN / (TN + FP)
False Positive Rate    = FP / (FP + TN) = 1 - Specificity
Accuracy               = (TP + TN) / (TP + TN + FP + FN)
```

Read them as a pair, never singly. Recall is how much bad output the gate catches. Precision is how much of what it blocks was genuinely bad. A gate can reach recall 1.0 by failing everything.

### Worked example

A judge run against a held-out split of 200 items, 60 of which humans labeled as failing:

```
TP = 45    FP = 30
FN = 15    TN = 110

Precision   = 45 / (45 + 30)   = 0.600
Recall      = 45 / (45 + 15)   = 0.750
Specificity = 110 / (110 + 30) = 0.786
Accuracy    = 155 / 200        = 0.775
```

The headline "77.5 percent accurate" is the least useful number here. What matters for a release gate: the judge misses 1 failure in 4 (recall 0.75), and 2 of every 5 items it blocks were actually fine (precision 0.60). Whether that is acceptable depends entirely on which error is more expensive - shipping a defect, or blocking a good release.

### Report an interval, not a point

Recall was computed on 60 items. A Wilson score interval at 95 percent (`z = 1.96`) for 45 successes in 60:

```
center    = (p + z^2/(2n)) / (1 + z^2/n)          where p = 0.75, n = 60
          = (0.750 + 0.0320) / 1.06403 = 0.735
halfwidth = z / (1 + z^2/n) * sqrt( p(1-p)/n + z^2/(4n^2) )
          = 1.8419 * sqrt(0.003125 + 0.000267) = 1.8419 * 0.05824 = 0.107
interval  = [0.628, 0.842]
```

The judge's true recall plausibly sits anywhere from 63 to 84 percent. Any threshold decision that depends on distinguishing 0.75 from 0.80 is not supported by this sample.

### Prevalence changes precision, and nothing about the judge

Precision is not a property of the evaluator. Hold recall and specificity fixed at 0.75 and 0.786, and change only how often failures actually occur - from 30 percent in the test set to 5 percent in production, over 1000 items:

```
Positives = 50   -> TP = 0.750 * 50  = 37.5
Negatives = 950  -> FP = 0.214 * 950 = 203.6
Precision = 37.5 / (37.5 + 203.6)    = 0.156
```

Same judge, same measured metrics: precision falls from 0.60 to 0.16. In production, five of every six items it blocks would be false alarms, and the team would learn to ignore it within a week. Always state the prevalence your validation set was built at, and re-check precision at the prevalence the judge will actually meet.

## Step 4: Tune the threshold on development data only

1. Sweep candidate thresholds against the **development** split.
2. At each, compute precision, recall, and specificity.
3. Choose using the cost asymmetry you can state in words: "a missed defect costs more than a blocked release" argues for recall; the reverse argues for precision.
4. Write down the chosen threshold and the sentence justifying it.
5. Measure once on the **held-out test** split. Report that number. Increment `holdout_touched_count`.

If the test number disappoints, the honest moves are to accept it, improve the evaluator and build a fresh held-out split, or declare the judge advisory. Re-tuning against the test split and reporting the improved figure is the one move that is not available.

## Step 5: Decide advisory or gate

| Posture | Requirements |
|---------|--------------|
| **Advisory** - surfaces suggestions, blocks nothing | A rubric and a sanity check. Wrong scores cost attention. |
| **Release gate** - blocks a merge or deploy | Held-out measurement with an interval; a documented disagreement review; precision and recall stated at the production prevalence; a named human override path; a recalibration trigger |

The gap between the rows is the whole point of this reference. A judge promoted from advisory to gate without the second column's evidence has changed from a suggestion nobody must follow into an unmeasured blocker nobody can appeal.

Recalibrate when any of these fires: the underlying model or its version changes; the rubric changes; the input distribution shifts; the override rate rises (humans overriding often means the judge is wrong, or the threshold is); or on a fixed schedule as a backstop.

## Failure modes

| Failure mode | How it shows up | What it does |
|---|---|---|
| **Leakage** | Test items also appear in the few-shot examples or rubric-tuning set | Reported accuracy is unreachable in production |
| **Class imbalance** | 95 percent of items pass; the judge passes everything | Accuracy 0.95, recall 0.0, and the gate catches nothing |
| **Rubric drift** | The rubric is edited between runs without a version bump | Two scores compared as if measuring the same thing |
| **Tuning on test** | `holdout_touched_count` climbing over many iterations | The test split has become a training set |
| **Unblinded annotation** | Reviewers see the judge's verdict first | Agreement is circular; the judge validates itself |
| **Single-annotator ground truth** | No double-labeled portion | No way to know if the judge beats human noise |
| **Prevalence mismatch** | Validated at 30 percent failure, deployed at 5 percent | Precision collapses; alerts get ignored |

## Local-data handling

- Annotations, adjudications, and the items behind them stay local by default; `export_authorized` is `false` until a human decides otherwise.
- `annotator_id` is pseudonymous. Reviewer identity is never needed to compute any metric here.
- Report aggregates, not the labeled corpus. Precision, recall, and an interval carry the finding; the annotated items do not need to travel with them.
- Any export applies the per-category policy in `[[egress-redaction]]` as an explicit, separately authorized step.

## Verification

- [ ] Data is split three ways, recorded in a `split_manifest` with its method and seed
- [ ] `holdout_touched_count` is recorded and was incremented on each held-out evaluation
- [ ] No threshold or rubric decision was made using the held-out split
- [ ] Ground-truth annotations were collected blind, with a double-labeled portion measuring annotator agreement
- [ ] Disagreements were adjudicated and recorded, with rubric defects marked as such
- [ ] The positive-class convention is stated explicitly
- [ ] Precision, recall, and specificity are reported together, never accuracy alone
- [ ] Every reported rate carries a confidence interval or an explicit small-sample label
- [ ] Precision is re-checked at the prevalence the evaluator will meet in production
- [ ] Any release-gating evaluator has held-out evidence, a documented disagreement review, a human override path, and a recalibration trigger
- [ ] No annotation, adjudication, or labeled item left the host without explicit authorization
