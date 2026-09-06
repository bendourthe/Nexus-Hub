---
name: minimal-construction
description: "Pick the smallest correct construction before writing code. Use this skill whenever the user wants the simplest solution, YAGNI, to do less, the shortest path, to avoid over-engineering or unnecessary dependencies, or to be lazy about what you build, even if they never say 'minimal'. SKIP: non-coding prose, security audits, post-write refactors, dead-code campaigns, and plan-scope review. Do NOT use to collapse existing code (code-simplification), hunt dead code (dead-code-eliminator), emit a delete-list (over-engineering-review), or drop trust-boundary, security, accessibility, or proving-command work."
summary_l0: "Stop at the first sufficient pre-write rung instead of adding machinery"
overview_l1: "Walk a seven-rung pre-write ladder after reading the real flow: skip unneeded work, reuse this codebase, stdlib, native platform feature, already-installed dependency, one line, then the minimum new code. Intensity is a skill argument (lite, full, ultra; default full), not an env var or config file. Safety, tests, talk, dead code, and post-write collapse stay with their owning skills. Trigger phrases: simplest solution, yagni, do less, shortest path, over-engineering, unnecessary dependencies, be lazy about what you build."
---

# Minimal Construction

Build at the first sufficient rung. Read the real flow first. This skill decides what new code is allowed to exist. It does not collapse existing code, hunt dead code, rewrite prose, or replace security, verification, or communication owners.

Trigger routing cases live in `evals/trigger-cases.json`. Construction-eval assertions live in `evals/evals.json`. Deferred-ceiling harvest lives in `references/construction-debt.md`.

## When to Use This Skill

Use when:

- The user asks for the simplest solution, YAGNI, to do less, or the shortest path.
- A change is about to add a library, wrapper, helper class, or framework for a job the platform or this repo already covers.
- The user wants to avoid over-engineering or unnecessary dependencies, or to be lazy about what you build.
- You are about to write new code and have not yet proven a smaller rung is insufficient.

**When NOT to use:**

- Non-coding prose, tone, or voice work.
- Security audits, exploitability, or patch advice (`security-review` and the owning security skills).
- Post-write structural collapse of code that already exists (`code-simplification`).
- Dead-code campaigns at scale (`dead-code-eliminator`).
- Plan-scope or cut-line review (`plan-review`).
- Emitting a tagged delete-list without building (`over-engineering-review`).
- Declining the user's requested feature silently. `Consequential Decisions` still governs scope expansion.

## Rule ownership

| Concern | Owner | Non-owners do |
|---|---|---|
| How small a new solution is (reuse, stdlib, native, installed dep, one line, minimum) | `minimal-construction` | Point at it |
| YAGNI for extra machinery inside a requested feature | `minimal-construction` | Do not decline the requested feature silently |
| Collapse of existing over-abstraction without behavior change | `code-simplification` | This skill does not become a refactor skill |
| Dead / unreachable code at scale | `dead-code-eliminator` | Point at it |
| Diff- or repo-scoped over-engineering delete-list | `over-engineering-review` | Point at it; do not apply those deletes here |
| Unrequested code versus a plan | `implementation-convergence` | Do not invent plan gaps |
| Plan scope / cut-lines | `plan-review` | Point at it |
| Repo-internal unused-structure rule for Nexus-Hub itself | AGENTS.md Boundaries | Not a distributed user coding rule |
| Trust-boundary validation, security, accessibility | `security-review` and the owning security/a11y skills | Name the handoff; do not restate those rules |
| Completion claims and proving commands | `verification-before-completion` | Do not adopt a one-assert floor or YAGNI-on-tests |
| How the agent talks | `agent-communication` plus End-of-Task Summary | Do not delete the explanation |
| Version-level deferrals | `known-gaps-tracker` | Point at it |
| Task-scope restraint for extras and unrequested tests (with `/test` governing when invoked) | `minimal-construction` step 6 | `/test` cites the decision; do not restate the rule |
| SQALE / interest quantification | `technical-debt-analyzer` | Point at it |
| In-code named ceilings with an upgrade trigger | `construction-debt:` harvest | Generic marker; see `references/construction-debt.md` |

## Instructions

### 1. Read the real flow

Name the user-visible outcome and the existing path through the codebase that already produces it, or the closest path. Do not design a new layer until this sentence exists. If you cannot name the flow, stop and read until you can.

### 2. Resolve intensity

Intensity is a skill argument, not an environment variable, flag file, or config key.

- `full` (default): walk every rung below.
- `lite`: stop at the first clearly sufficient among skip / reuse / stdlib / native. Do not skip a trust-boundary, data-loss, security, accessibility, or proving-command requirement.
- `ultra`: walk every rung and emit a skipped-work line for each declined rung.

If the user names `lite`, `full`, or `ultra`, use that. Otherwise use `full`.

### 3. Walk the seven rungs in order

Stop at the first rung that satisfies the requested outcome. Do not keep walking "for cleanliness."

1. **Skip.** If the outcome already exists, or the user does not need this work, do not add code. Write `skipped: <what>, add when <trigger>`.
2. **Reuse this codebase.** Search for an existing helper, component, command, or pattern that already does the job. Prefer it over a new file.
3. **Stdlib.** Prefer the language or runtime standard library over a new dependency.
4. **Native platform feature.** Prefer the host, framework, or browser control that already ships (date picker, dialog, router, test runner) over wrapping it.
5. **Already-installed dependency.** Use a package that is already in the project's lockfile. Do not add a new package to save a few lines.
6. **One line.** If a few lines at the call site are enough, write them there. Do not open a new module for a one-liner.
7. **Minimum new code.** If none of the above is enough, write the smallest new code that covers the real flow. No speculative helpers, wrappers, or "for later" types.

### 4. Do not cut owned floors

Hand these off. Do not treat them as bloat:

- Trust-boundary validation, data-loss handling, security, and accessibility.
- A proving command required by `verification-before-completion`.
- End-of-Task Summary and a user-requested explanation.

YAGNI does not apply to tests. "One runnable check" is not a license to drop coverage the owning skill requires.

### 5. Record skipped work without replacing the closing summary

For each declined extra, emit one line:

`skipped: <machinery>, add when <observable trigger>`

This is additive. It does not replace Completed / Verified / Open / Next.

If a deliberate corner cuts a real ceiling, add a `construction-debt:` comment naming the limit and the revisit trigger. Harvest steps: `references/construction-debt.md`. Do not invent a second known-gaps ledger.

### 6. Keep extras and tests to what the task asks

Do not fix a pre-existing bug, optimize, or extend behavior the task did not mention unless the requested behavior cannot work without it; report it as a follow-up instead. Commit tests only where the task asks or the repository already keeps them for this change class, sized like the neighbouring test files at roughly one focused test per stated behavior, and do not turn scratch checks into permanent test files. This concerns extras only: every behavior the task does ask for is still implemented completely, and the floors in step 4 still stand. When `/test` is explicitly invoked, its coverage threshold governs instead, per the recorded decision in `docs/releases/v4/v4.7/development/test-scope-decision.md`.

### 7. Stop

If rung 1-6 already shipped the outcome, do not add a helper "so the next caller has a place." The next caller can add it when they exist.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is too simple for this skill" | Simple tasks are where extra wrappers appear. Walk the rungs anyway. |
| "A small helper will make the next feature easier" | The next feature is not in scope. Add the helper when the second caller exists. |
| "YAGNI applies to tests too" | Tests prove the claim. `verification-before-completion` owns proving commands. |
| "I will skip the explanation to stay minimal" | Talk is owned by `agent-communication` and End-of-Task Summary. Construction discipline does not delete it. |
| "I should also simplify the surrounding module" | That is post-write work. Hand it to `code-simplification` instead of restating its ladder. |
| "A new library is cleaner than four lines" | Four lines that call stdlib or a native control beat a new dependency and its update surface. |
| "Dropping this validation keeps the diff small" | Size is not the floor. Security and accessibility owners decide those checks. |

## Verification

- [ ] The real flow was named before new files were added
- [ ] Intensity used is `lite`, `full`, or `ultra`, and no new env var or config file was introduced
- [ ] Each new symbol was required by a rung that a smaller rung could not satisfy
- [ ] No new dependency was added when stdlib, a native feature, or an already-installed package was enough
- [ ] Trust-boundary, data-loss, security, accessibility, and required proving commands were not removed to look smaller
- [ ] Skipped-work lines use `skipped: X, add when Y` and the closing summary is still present
- [ ] `evals/trigger-cases.json` still lists positives for construction requests and negatives for prose, security, dead-code, and post-write simplify

## Related Skills

- `code-simplification` -- post-write behavior-preserving collapse; this skill is pre-write
- `dead-code-eliminator` -- unreachable code at scale
- `over-engineering-review` -- tagged delete-list; does not apply fixes
- `security-review` -- trust-boundary and security findings
- `verification-before-completion` -- proving commands and completion claims
- `agent-communication` -- how the agent talks
- `known-gaps-tracker` -- version-level deferrals
- `technical-debt-analyzer` -- SQALE scoring
- `implementation-convergence` -- unrequested code versus a plan
- `plan-review` -- plan scope and cut-lines
