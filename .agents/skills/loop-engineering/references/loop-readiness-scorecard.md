# Loop Readiness Scorecard

A loop is admitted by evidence, not by enthusiasm. Score the candidate work on the seven dimensions below before assembling a loop definition, and record the total in the loop's instance state so a later reader can see what the loop was admitted on.

This scorecard is a practical heuristic for local use. It is not an industry standard, it carries no external validation, and a total is a conversation starter rather than an authorization.

## The seven dimensions

Score each dimension 0, 1, or 2.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Objective clarity | The goal is vague and could be declared met by argument. | Partially stated; the end state needs interpretation. | A falsifiable end state one sentence long. |
| Verification | Subjective judgement only. | A rubric exists but a human must apply it. | A strong external or deterministic check (exit code, metric, compiler, test suite). |
| Convergence | A failed check rarely points to a meaningful next action. | Sometimes points to a next action. | A failed check usually names the next action. |
| Reversibility | The actions are costly or irreversible. | Partly reversible, or reversible at a cost. | A safe sandbox, or every action is cheaply reversible. |
| State | Progress is hard to represent between iterations. | Partially representable. | A clear, compact state model survives a cold start. |
| Permissions | Broad access is required. | Partial narrowing is possible. | Least privilege is feasible and expressible. |
| Economics | Low task value against iterative compute. | Uncertain. | High task value against iterative compute. |

## Interpreting the total

- **11 to 14** is a strong loop candidate. Assemble the loop.
- **7 to 10** is a pilot under close supervision while the verifier is improved. The weak dimension is usually verification or convergence, and improving it raises the total more cheaply than running the loop harder.
- **0 to 6** means prefer chat, a deterministic workflow, or a human-led process. A low total is not a reason to loop more carefully; it is a reason not to loop.

## When not to loop

Five anti-fits. Any one of them is sufficient on its own, whatever the total says.

- **Short tasks.** Work completable in one or two turns pays the loop's setup and trace cost for nothing.
- **Purely subjective work.** With no calibratable rubric and no human gate, there is nothing for a checker to evaluate.
- **Irreversible high-risk actions.** Production data, money, external communications, and regulated decisions are gated or human-led, not looped.
- **No independent evidence.** If the producer would also be the only approver, the loop cannot terminate honestly.
- **Non-convergent exploration.** Open-ended ideation and strategy work have no failing check that points anywhere.

## Worked scoring: ship-pr-until-green

Scored using only the definition in [loop-library.md](loop-library.md), with the justifying field quoted for each dimension.

| Dimension | Score | Justifying field |
|---|---|---|
| Objective clarity | 2 | `goal: The pull request has no failing required checks.` -- falsifiable, one sentence, no interpretation needed. |
| Verification | 2 | `check_command: gh pr checks` with `exit_condition: check_command exits 0 and reports no failing required checks.` -- an external deterministic check the loop does not produce. |
| Convergence | 2 | The same `check_command` output names which required check failed, so a failure points at the job to fix. |
| Reversibility | 1 | The `gates` entry declares one step (`Approve a force-push that rewrites this PR's history?`) whose blast radius exceeds the loop's authority. Ordinary fix-and-push is reversible; history rewriting is not, so this is partial rather than free. |
| State | 2 | `iteration_cap: 10` plus the check output is the whole state model: which required checks are red this iteration. It survives a cold start. |
| Permissions | 1 | The definition declares `agents` but no `permissions` field, so least privilege is feasible (a repository-scoped `gh` token) but undeclared. Adding `permissions` per [loop-schema.md](loop-schema.md) raises this to 2. |
| Economics | 2 | The `tags` list (`ci`, `pr`, `checks`) against `iteration_cap: 10`: each iteration is one cheap check plus a narrow fix, and an unblocked pull request is high value. |

Total: **12** -- a strong loop candidate, with the two 1s naming exactly what to improve. Declaring `permissions` closes one; the other is inherent to a loop that touches shared history and is correctly handled by a gate rather than by a higher score.
