# Decision: Test instruction-file edits first in isolation, and ship ownership framing as an opt-in snippet

Status: implemented - behavioral edits to an instruction file are tested first as manifests on the v4.15.2 shared evaluator with frozen case sets, clarity is owned by `writing-editing`, and the codebase-ownership sentence ships only as an opt-in snippet under `minimal-construction`

## Problem

Nexus-Hub changes the instruction templates that every installed agent reads, and no change is measured for behavior before it lands. Three template rules were proposed from outside sources (clear sentences, working through ordinary obstacles, summaries free of self-coined terms), and an ownership sentence was found to change agent behavior sharply. A rule added without a test can lose a behavior that already worked, or raise cost with no gain. Separately, three owners already cover parts of the evaluation job (the test-first rule, the shared evaluator, the grader), so a new procedure risks restating them.

## Decision

- Instruction-file edits are tested first, in isolated sessions with an isolation canary. Trials run as manifests on the shared evaluator `scripts/evaluate_harness_pairings.py` from v4.15.2, and no second runner is built.
- Judge-style assertions are graded by `skill-eval-loop`'s grader over the final text and the tool-call path that the evaluator retains. The evaluator calls no judge.
- A case passes at 4 of 5 runs. A gain or a loss counts only when the pass count moves by 2 or more. The classes are gain, loss, no change, unstable, and not run.
- Case files are frozen before the first baseline run, with one sharpening allowed per set and the original case kept.
- Live runs are capped at USD 80 for the whole plan, and template edits run last, against a fresh baseline.
- The case sets live in `tests/verification/fixtures/instruction-templates/`, because that root is already collected by the governance shards and a folder under `templates/ai-instructions/` would sit beside the template roster.
- The generic procedure is `catalog/skills/workflow/skill-eval-loop/references/instruction-file-evals.md`. It links the test-first rule, the evaluator contract, the grader, and `ai-output-evaluation`, and it restates none of them.
- Clarity is owned by `writing-editing` (`references/clarity-faults.md`). `anti-slop-editing` Detect mode links it as a second output section and does not own it.
- Paired-run inference and receipts for this procedure are out of scope here (item A8b) and owned by the v4.21.2 plan.
- The ownership sentence ships only as an opt-in snippet, `catalog/skills/code-cleanup/minimal-construction/references/codebase-ownership-mode.md`, with a scope exception, the vendor-measured costs, an off switch, and a statement of what it does not grant. No template contains it.

Status of the work behind this record: the procedure, the case sets with their manifests, the clarity reference, and the opt-in snippet are in the repository. The live canary and the baseline and after runs, and therefore the three template edits, are waiting on a maintainer decision about live spend and on evaluator capabilities the merged v4.15.2 evaluator does not yet have (a live isolation backend, a per-trial throwaway configuration directory, a canary workload, and retained final text and tool path).

## Alternatives considered

- **Subagent runs without isolation.** Rejected: the operator's installed instruction files stay live in both arms, so the test measures the file against itself and returns a plausible number.
- **Pass at 2 of 3 runs.** Rejected: with so few runs a single unstable result flips the class, and 5 runs with a movement threshold of 2 separates noise from change at a cost the cap allows.
- **Report pass rates without a gate.** Rejected: a rate with no decision rule does not stop a bad edit.
- **A procedure only for this repository.** Rejected: any user who maintains a CLAUDE.md or AGENTS.md has the same problem, so the procedure sits in a distributed skill.
- **The ownership sentence as a default in the templates.** Rejected: the vendor measured 70 to 80 percent more output tokens, unrequested changes, and summaries that omit small changes, and a scope rule does not cancel it, so a default would change every user's repository.
- **The ownership sentence as documentation only.** Rejected: users who own their repository and want it would have to rebuild the scope exception without the measured costs beside it.
- **A separate template-case runner, or an extension of `skill-eval-loop`'s CLI adapter, beside the shared evaluator.** Rejected: it adds a second isolation, canary, and spend-cap engine to maintain, and the maintainer decided on 2026-11-12 to use the shared evaluator.
- **A `Stop` hook that requires a cold-reader pass after any turn that changed reader-facing prose.** Rejected: the project adds no hooks for this, and `Stop` fires at the end of every turn, so it would run constantly.
- **A structural reviewer that sends prose to a third-party model API.** Rejected: that is generation as a service, which the MCP registry policy refuses, and a subagent gives the same independent read.

## Consequences

- A template edit that changes behavior needs a committed case set, a failing baseline, and a per-case comparison before it ships, and a rule with no failing positive case is dropped.
- Until the evaluator gains the capabilities named above and the maintainer approves live spend, the three template rules stay unshipped and are recorded as known gaps rather than shipped on an unmeasured assumption.
- `writing-editing` loads at the start of any task whose deliverable is prose another person will read, which raises its trigger rate and its cost per task slightly.
- The ownership snippet adds one more reference file to maintain, and a Fable 5.2 claim in the model profile points to it, so a vendor change to the sentence needs a profile refresh.
