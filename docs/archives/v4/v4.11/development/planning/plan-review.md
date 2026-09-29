# v4.11.0 planning review

This record covers the independent review of the cache-accounting and diagram-quality adoption plan, the author's resolutions, and the seeded design-interview outcome. It is planning evidence, not proof that any implementation or benchmark passed.

Date: 2026-09-09

Plan: [v4.11.1 adoption](../../../../../archives/v4/v4.11/plans/v4.11.1-adoption-cache-and-diagram-quality.md)

**Renumbered 2026-09-12**: the plan reviewed here was authored as v4.11.0 and is now v4.11.1. The v4.11.0 slot went to the interactive-handbooks plan, which was promoted from a patch because it changes the default output of /presentify. The review below is unchanged; only the slot moved.

## Coverage

| Lens | Reviewer | Scope | Result |
|---|---|---|---|
| Coherence | Independent coherence agent | All 25 tasks, D1-D7, ownership, local links and exit gates | No reported finding |
| Feasibility | Independent feasibility agent | Six phases, real versus structural installer evidence, CI ordering, scorer/browser boundaries | Two P2 findings |
| Product | Independent product agent | A1-A6 coverage, user value, evidence limits, prompt-audit categories | One P2 finding |
| Design | Independent design agent | Owner boundaries, reconstruction entry contract, scorer result/CLI compatibility | One P2 finding |
| Scope | Independent scope-guardian agent | Construction ceiling, sequencing, exclusions, mandatory final-phase scope | No reported finding |
| Security | Independent security agent | Source screening, synthetic telemetry, XML refusal, offline authored fixtures, resource limits | One P2 finding |
| Adversarial | Same reviewer as security, distinct pass | Mixed coverage, malformed/non-finite data, badge exceptions and resource exhaustion | No additional distinct finding |

The harness returned "agent thread limit reached" when spawning a seventh agent and when trying an idle-agent follow-up. The running security reviewer performed the adversarial pass separately. All seven lenses were covered, but there were six independent agents, not seven. No review agent edited the plan. The author applied and checked the revisions; a second independent review of the revised file was not run.

## Findings and disposition

Locations refer to the reviewed draft and can shift in the final file.

| Severity | Lens | Draft location | Finding | Confidence | Resolution |
|---|---|---|---|---|---|
| P2 | Feasibility | T020, line 390 | Target-OS installer proof precedes the hosted runners that supply it. | 100 | Added Phase 6 subordering: native Windows proof and local comparison first; remote-only T020 evidence remains pending until T025's approved Ubuntu/macOS/Windows PR matrix. Merge and Phase 6 completion wait for it. T001 now distinguishes structural tests from actual installers plus the shared postcondition checker. |
| P2 | Feasibility | T025, line 430 | An unconditional local-reproduction rule has no recovery path for a hosted infrastructure failure. | 100 | Retain the template's default no-rerun rule. Proven infrastructure failure stays blocked while the implementer presents logs and a one-retry proposal for explicit user authorization. No automatic retry or code-failure bypass is authorized. |
| P2 | Product | T007, line 220 | The prompt audit omits several of the six adopted categories. | 75 | Explicitly cover redundant verification, emphasis, scaffolds, stale examples, contradictions and retired settings. Hand currency-dependent judgments to the existing model-prompting-research owner; unresolved facts stay unresolved. |
| P2 | Design | T011, line 274 | A concise reconstruction would conflict with the existing lossless-only entry contract. | 75 | Preserve lossless reconstruction and add a separately labeled, authorized derived summary with provenance, complete accounting and access to the source. Specify the Step 4/part 5 handoff and prohibit a summary passing the lossless gate. |
| P2 | Security | T014, line 320 after initial edits | The scorer has no per-input static resource bound; the outer test timeout is insufficient. | 75 | Require bounded file reads/direct-input checks, 16 MiB HTML, 1 MiB SVG, 4096 elements, depth 64, one million geometry comparisons, non-finite-value rejection and a real-scorer subprocess regression capped at 10 seconds. Limit hits are rejected/unchecked, never silently truncated or counted as fully checked. |

Aggregation order: fingerprint deduplication by document/section/normalized finding, cross-lens agreement promotion, then confidence gate. Five distinct findings survived; none needed promotion. The resource issue was also examined in the adversarial pass by the same reviewer, which is not independent agreement and was not counted twice. No P0/P1 finding was raised.

Suppressed appendix: none. No submitted finding fell below the 75 confidence gate. Considered-but-rejected candidates below are inspected non-findings, not artificially suppressed defects.

## Considered but rejected

- Broad final-phase refactoring as automatic scope expansion: the required template remains, but the execution contract permits only necessary scoped corrections and requires approval for broader work.
- Known gaps as a way to claim an incomplete Goal: D1-D6 cannot be waived; the final exit checklist leaves uncovered Goal evidence incomplete.
- Dependency on uncommitted v4.9.1 work: Phase 4 reconciles against the integrated owner and reports the pending contract instead of treating the dirty plan as released behavior.
- A paid runner prerequisite for synthetic examples: live savings and automatic skill-selection claims are explicitly excluded and remain with v4.11.
- Missing browser tooling: the existing visual-defect tests already use Playwright and boundary checks; the plan reuses that tooling.
- A new general SVG framework: geometry is limited to two failure classes and supported constructs; unsupported constructs remain unchecked.
- An optional coverage field alone proving correctness: T014 requires testing the consuming gate, not just emitting metadata.
- A new persistent ledger schema: the ledger is an authoring worksheet under the existing reference, with no new service/schema.
- Missing simple-fact fallback: the existing HTML owner's subtractive test already allows omission of a visual with no explanatory value.

## Seeded design-interview outcome

The five findings seeded the decision frontier. Four resolutions are established by current source/local contracts: restore adopted audit categories; preserve lossless reconstruction; use the existing target-OS CI matrix; and keep infrastructure reruns behind explicit authorization. The resource limits are bounded implementation defaults needed to make the accepted geometry scope testable. They add no dependency, credential, external service or product feature.

Decided branches: six existing-owner additions; synthetic-only cache/prompt evidence; separate authorized derived summaries; bounded local geometry; host-local proof followed by the approved cross-OS PR matrix.

Parked branches: none introduced by this review. The comparison's excluded live experiments, importers and presentation runtime remain outside the plan.

Glossary: no newly ambiguous load-bearing terms arose; definitions already appear in the plan. No CONTEXT.md addition was needed. The design-interview gate does not reopen the confirmed target version or ask the user to decide facts available in the repository.

**Verdict**: READY for phase-breakdown confirmation, with five P2 findings addressed and zero unresolved P0/P1 findings. This is the author's post-revision disposition, with the independent-review coverage limitation stated above. Implementation remains 0/25 tasks and 0/6 phases.

## Planning validation

The final validation receipt is [verification.json](verification.json). It records the task/phase parser, local links, resource/model-map checks, Markdown hygiene, mandatory final-template preservation and comparison/plan co-location. No implementation suite, upstream executable, live model benchmark, commit or remote publication ran for this planning task.

Workflow coverage limitation: the installed plan dispatcher names the unavailable generate-plan delegate. That delegate was not run. The available implementation-plan skill supplied the retained planning procedure, and plan-review plus its seeded design-interview pass were applied as recorded above.
