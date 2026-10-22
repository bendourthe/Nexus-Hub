# Queue Reorganization - 2026-10-12

**Scope**: every queued plan from v4.14 onward (27 plans, 24 comparisons) plus the new v4.15.3 speed comparison. Plan content is unchanged except version identity and reference repair.
**Decision owner**: the maintainer, who approved the release map on 2026-10-12.
**Ranking rule**: `plan-queue-assessment` Step 5. Impact on the harness is a maintainer judgement recorded below, not a computed score. No delivery-speed claim is made for the reordering itself.

## Why

The queue had grown to 27 plans across four minors, with v4.17 alone holding thirteen patches. Work the maintainer ranked as most urgent (agent speed and token cost) formerly sat at v4.16.2 and v4.17.11-v4.17.12, behind documentation-class and evaluation-class plans. The reorganization groups plans into nine themed minors with at most four patches each, puts speed and cost first, and keeps documentation and visual-class plans last per the class rule.

## Release map

| New | Theme | Plan (slug) | Original version |
|---|---|---|---|
| v4.14.0 | Speed and cost | adoption-agent-tooling-and-subagent-cost | formerly v4.16.2 |
| v4.14.1 | Speed and cost | adoption-effort-allocation | formerly v4.17.11 |
| v4.14.2 | Speed and cost | adoption-harness-decisions-design-rules-and-cache-stability | formerly v4.17.12 |
| v4.15.0 | Context payload | instruction-necessity-review | formerly v4.16.0 |
| v4.15.1 | Context payload | adoption-model-adaptive-harness | formerly v4.16.1 |
| v4.15.2 | Context payload | adoption-harness-economics-and-portable-engineering-system | formerly v4.17.3 |
| v4.15.3 | Context payload | new comparison: agent speed, KV handoffs, mods delta, local search | new |
| v4.16.0 | Long sessions | adoption-pinned-rules-and-prune-compaction | formerly v4.17.9 |
| v4.16.1 | Long sessions | adoption-proactive-memory-intervention | formerly v4.17.2 |
| v4.16.2 | Long sessions | adoption-agent-experience-and-harness-economics | formerly v4.16.3 |
| v4.17.0 | Safety guards | push-size-guard | formerly v4.14.0 |
| v4.17.1 | Safety guards | adoption-process-safety-and-review-pipeline | formerly v4.17.4 |
| v4.17.2 | Safety guards | adoption-agent-working-agreement | formerly v4.17.5 |
| v4.18.0 | Working discipline | adoption-testing-discipline-headings-and-opus-5-5 | formerly v4.17.6 |
| v4.18.1 | Working discipline | adoption-local-hooks-and-single-item-install | formerly v4.17.7 |
| v4.18.2 | Working discipline | adoption-de-slop-repair-discipline | formerly v4.15.1 |
| v4.19.0 | Planning practice | adoption-frontier-agent-practice | formerly v4.17.0 |
| v4.19.1 | Planning practice | adoption-tracer-bullet-and-leading-words | formerly v4.17.8 |
| v4.20.0 | Alignment and reporting | adoption-alignment-readability-mods-routing | formerly v4.18.1 |
| v4.20.1 | Alignment and reporting | adoption-manager-context-signal-discipline | formerly v4.15.0 |
| v4.20.2 | Alignment and reporting | adoption-aika-modes | formerly v4.17.1 |
| v4.21.0 | Self-improvement and evals | adoption-self-improving-harness-loop | formerly v4.18.2 |
| v4.21.1 | Self-improvement and evals | adoption-html-plans-agent-verification-and-authorization-proofs | formerly v4.18.3 |
| v4.21.2 | Self-improvement and evals | adoption-evals-test-trust-and-visual-agent-communication | formerly v4.18.4 |
| v4.22.0 | Docs and visuals | adoption-structural-slop-signatures | formerly v4.17.10 |
| v4.22.1 | Docs and visuals | adoption-code-rendered-animation-and-illustration-quality | formerly v4.18.0 |
| v4.22.2 | Docs and visuals | adoption-dashboards-motion-evidence-ledger-and-reliable-automations | formerly v4.18.5 |
| v4.22.3 | Docs and visuals | adoption-claude-code-mods | formerly v4.15.2 |

Each comparison moved with the plan it seeds. Two comparisons seed two plans each, so their plans share a minor: `working-agreement-typed-judgment-and-prod-gates` (v4.17.1 and v4.17.2), `testing-discipline-component-library-and-opus-5-5` (v4.18.0 and v4.18.1), and `model-adaptive-harness` (v4.15.0 and v4.15.1). The approved map was adjusted by these three placements on the same day, because `check_doc_colocation.py` requires a plan and its comparison to share a minor.

## Position reasons

- **v4.14 Speed and cost.** Cheaper subagents (pinned agents plus the subagent model lever), effort spent where it buys verification, and cache-correct model or effort changes. Effort precedes cache stability because the cache plan builds on the effort note in step-8.
- **v4.15 Context payload.** Instruction-necessity first, because harness-economics consumes its decision before flipping the skill-index default (v4.13 DF-1). Model-adaptive shares the necessity comparison. The v4.15.3 speed comparison follows the flip it complements.
- **v4.16 Long sessions.** Compaction, reactivation, and harness-economics routing cut re-reading in long sessions.
- **v4.17 Safety guards.** Push-size guard, process ownership, and the working agreement (co-located with its comparison).
- **v4.18 Working discipline.** Test-first and headings, single-item install and settings-merge safety, and repair discipline.
- **v4.19 to v4.21.** Planning practice, reporting contracts, the improvement loop, and evaluations.
- **v4.22 Docs and visuals, last.** Documentation, illustration, and visual-class plans describe what earlier plans build, so they carry a content refresh against everything ahead of them.

## Inverted predecessors

These plans now precede a plan their queued-predecessor table named as sharing files (computed from each plan's ordering-impact rows). They remain serial, and each must refresh its content at its admission phase, which `plan-queue-assessment` requires at every plan start anyway.

| Plan (new) | Now precedes (new) |
|---|---|
| v4.14.0 subagent-cost | v4.15.1 model-adaptive |
| v4.14.1 effort-allocation | v4.16.2 agent-experience, v4.18.0 testing-discipline |
| v4.16.0 pinned-rules | v4.17.1 process-safety, v4.18.1 local-hooks, v4.19.0 frontier, v4.19.1 tracer-bullet |
| v4.16.1 proactive-memory | v4.20.2 AiKA modes |
| v4.17.2 working-agreement | v4.19.0 frontier |
| v4.18.2 de-slop | v4.19.0 frontier |
| v4.19.1 tracer-bullet | v4.20.1 report contract |
| v4.21.0 self-improving loop | v4.22.0 structural-slop |
| v4.21.1 HTML plans | v4.22.0 structural-slop |

## Reference repair

- Moved files: 51 (27 plans, 24 comparisons), via `git mv` through temporary names in two passes.
- Living files rewritten with one simultaneous old-to-new mapping: the moved files, the open v4.13.11 plan, `docs/releases/v4/v4.13/known-gaps.md`, `docs/todos.md`, and `CONTEXT.md`.
- Released history (v4.13 evidence and shipped plans, archives, CHANGELOG, decisions, catalog prose): link paths only, so links resolve while recorded version claims stay as written.
- Kept verbatim: `docs/releases/v4/v4.17/known-gaps.md` (scoped to the v4.17 minor-scope run, not a plan), three completed tracker tasks naming PR #222 and #225, two authoring lines naming the branch `docs/v4.16.2-agent-tooling-and-subagent-cost`, and the runbook's `v4.17.0-<slug>` placeholder.
- Every moved file carries a `**Renumbered**:` line naming its original version.

## Verification

- Residual references were checked in a clean worktree on `origin/develop` with `python scripts/enumerate_plan_queue.py --root . --check-residual <old>` for each of the 14 retired versions (formerly v4.16.3, v4.17.3 to v4.17.12, v4.18.3 to v4.18.5), skipping `docs/archives`, released v4.13 history, `CHANGELOG.md`, `docs/DEVLOG.md`, `catalog`, and `docs/releases/v4/v4.17/known-gaps.md`. The remaining survivors are released v4.13 plans and evidence, one implemented decision record, and the original-version cells in this record. Reused version numbers cannot be checked this way; they are covered by the single-pass mapping and the link checks.
- Correction, 2026-10-12: a first residual pass reported zero survivors because the checker writes its findings to stderr and only stdout was read. The pass above reads both streams. It also found nine references in `docs/releases/v4/v4.13/known-gaps.md` that had not been remapped in the committed copy; they were remapped before commit.
- `python scripts/ci/run.py --profile full --only docs --quiet`: 10 of 10 checks passed, including co-location and link integrity.
