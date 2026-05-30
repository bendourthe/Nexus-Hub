# TDD for Skills: Author Discipline Skills Against a Failing Baseline First

This reference documents a test-first methodology for authoring discipline-enforcing skills and commands. It adapts the "no behavior change without a failing test first" discipline from software TDD to the problem of writing a skill that must resist rationalization. It complements Nexus-Hub's empirical `skill-eval-loop` (which measures trigger rate and grades output against assertions) by telling you what the skill body must contain before you ever run an eval.

A discipline skill is one whose job is to make the agent do the harder, correct thing under pressure (verify before claiming done, investigate root cause before patching, get a design approved before coding). Capability skills teach the agent how to do something it could not otherwise do; discipline skills stop the agent from talking itself out of something it already knows it should do. The failure mode for a discipline skill is not "the agent could not follow the steps" but "the agent found a plausible-sounding reason to skip them". You cannot write an effective counter to a rationalization you have not seen, so the methodology is built around surfacing the real rationalizations first.

## The Iron Law

> No skill without a failing baseline first.

Before you write a single line of a discipline skill, run the target scenario WITHOUT the skill loaded and watch the agent fail (or rationalize its way to the wrong answer). If you cannot produce a baseline failure, you have no evidence the skill is needed, and no catalogue of the specific rationalizations the skill must rebut. Writing the skill first and then constructing a scenario it happens to pass is the skill-authoring equivalent of writing a test after the code and asserting whatever the code already returns: it proves nothing and it bakes in your assumptions instead of the agent's actual behavior.

This law has one practical consequence worth stating plainly: the baseline-failure transcript is an authoring artifact, not throwaway output. Capture it. The verbatim rationalizations it contains become rows in the skill's `## Common Rationalizations` table, and the wrong turns it takes become the `## Red Flags` and the binary items in `## Verification`.

## RED - GREEN - REFACTOR for skills

The three TDD phases map cleanly onto skill authoring.

### RED: run the pressure scenario without the skill, capture rationalizations verbatim

1. Write a realistic scenario that should trigger the discipline (see `pressure-testing.md` for how to construct one that actually applies pressure rather than a softball).
2. Run it against the agent with NO skill loaded. The `skill-eval-loop` "without_skill" / baseline run is exactly this control.
3. Read the full transcript and copy the rationalizations the agent used, word for word. Do not paraphrase. "It should work now, so I will report it as done" is a different failure surface than "the change is trivial, so verification is unnecessary", and a paraphrase collapses the two.
4. Record the observable wrong action, not just the wrong reasoning: did the agent claim success, skip a command, edit a test to make it pass, scaffold code before a design existed? The observable action is what `## Verification` will check for.

If the baseline run passes (the agent does the right thing unprompted), stop. Either the scenario applied no real pressure, or the skill is not needed. Ratchet the pressure (combine time + sunk-cost + authority pressures) and re-run before concluding the skill is unnecessary.

### GREEN: write the skill to counter the captured rationalizations

Write the smallest skill body that turns every captured rationalization into a rebutted, named failure mode.

- Each verbatim rationalization from RED becomes one row in `## Common Rationalizations`, with a rebuttal that cites the concrete failure the rationalization causes (not a generic principle). "Even simple changes break" is weak; "the last three 'too trivial to test' changes each shipped a regression that a 5-second test command would have caught" is a rebuttal.
- Each observable wrong action becomes a binary `## Verification` item and, where appropriate, a `## Red Flags` entry the agent can pattern-match on mid-task.
- State the gate as a hard, first-person-imperative rule near the top of the body so it is impossible to miss. Discipline skills earn the right to be blunt here in a way capability skills do not.
- Keep the `description` frontmatter trigger-focused (when to fire, with explicit trigger phrases and a `SKIP:` clause) and push "what the skill does" into `summary_l0` / `overview_l1`. This is the reconciliation of the two description philosophies discussed in the Nexus-Hub vs. superpowers comparison (Section 4): a workflow summary in the `description` field gives the agent a shortcut it follows instead of reading the body, which is precisely what undermines a discipline gate.

Then re-run the same scenario WITH the skill loaded. It should now pass. If it does not, you have not yet countered the rationalization the agent is actually using; read the new transcript and add the missing rebuttal. This is the red-to-green transition, and it is empirical: the `skill-eval-loop` paired run gives you the before/after on the identical prompt.

### REFACTOR: close the new loopholes the agent finds

A discipline skill is never done after one green run, because closing one rationalization often reveals the next. The agent that can no longer claim "it is too trivial to verify" will try "I already verified this earlier in the session". REFACTOR is the loop that hunts those down.

1. Re-run the scenario (and variants at higher pressure) with the green skill loaded.
2. Capture any NEW rationalization the agent reaches for now that the obvious ones are blocked.
3. Add a rebuttal row for each, re-run, repeat.
4. Stop when the agent stops finding new escape hatches across two consecutive runs at the highest pressure you can construct, OR when `skill-eval-loop` reports a stable pass-rate on the held-out portion of the eval set (see the loop's stop condition).

Refactoring also covers the usual structural cleanup: if the body grows past the 500-line target while accumulating rebuttals, move worked examples into a `references/` file and keep the gate, the rationalization table, and the verification checklist in the body where they fire.

## How this complements skill-eval-loop

The two are not redundant; they answer different questions and run at different times.

| Concern | TDD-for-skills (this reference) | skill-eval-loop |
|---|---|---|
| Phase | Authoring (cold start, before stable evals exist) | Iteration (after 2-3 stable test prompts exist) |
| Primary question | What must the skill body CONTAIN to counter real rationalizations? | Does the skill measurably outperform baseline, and is the pass-rate stable? |
| Evidence produced | A verbatim rationalization catalogue feeding the body's tables | A graded benchmark with trigger rate, token/time deltas, held-out test split |
| Baseline control | The RED no-skill run | The "without_skill" paired run |
| Output | The first green draft of the skill | A measured pass-rate trajectory across iterations |

Run TDD-for-skills to produce the draft, then hand that draft to `skill-eval-loop` to measure and harden it across iterations. The baseline run is the shared artifact: TDD-for-skills uses it to mine rationalizations during authoring; `skill-eval-loop` uses it as the marginal-value control during iteration. See `[[skill-eval-loop]]` and `pressure-testing.md` for the scenario-construction techniques that make both passes meaningful.

## Common Rationalizations (about the methodology itself)

| Rationalization | Reality |
|---|---|
| "I know what rationalizations the agent will use; I can skip the baseline run." | The rationalizations you predict are the obvious ones. The baseline run surfaces the specific phrasing and the non-obvious escape hatches (for example, "I verified this earlier") that you would not have thought to rebut. Skipping it means shipping a skill that blocks the rationalizations you imagined, not the ones that actually occur. |
| "The skill reads well, so it will work." | Reading well is not the bar. A discipline skill is judged by whether the agent follows it under pressure, which is an empirical fact you discover by running the scenario, not by reviewing the prose. |
| "One green run means the skill is done." | One green run means the obvious loophole is closed. REFACTOR exists because closing one rationalization reveals the next; a skill that has only survived one run has not been pressure-tested against the agent's second and third escape hatches. |
| "Pressure scenarios are contrived; real tasks are not this adversarial." | Real tasks combine time pressure, sunk cost, and the agent's own drive to report progress, which is exactly the combination that produces rationalization. A scenario that applies no pressure tests nothing, because the agent does the right thing unprompted when nothing is pushing it toward the shortcut. |

## Verification

- [ ] A baseline (no-skill) transcript exists for the target scenario and shows the failure or rationalization the skill is meant to prevent.
- [ ] Every rationalization captured verbatim in the baseline run has a corresponding row in the skill's `## Common Rationalizations` table.
- [ ] Each rebuttal cites a concrete failure mode, not a generic principle.
- [ ] A with-skill run on the same scenario passes (the red-to-green transition is demonstrated, not assumed).
- [ ] At least one REFACTOR pass was run, and any new rationalization it surfaced was added and re-tested.
- [ ] The skill's `description` is trigger-focused; "what it does" lives in `summary_l0` / `overview_l1`, not in `description`.

## Related references

- `pressure-testing.md` - how to construct scenarios that apply real, combined pressure and the meta-testing question that hardens a gate.
- `persuasion-principles.md` - the research-backed framing (authority, commitment, social proof) that makes rebuttals stick, and which principles to avoid.
- `[[skill-eval-loop]]` - the empirical iteration loop that consumes the draft this methodology produces.
