# Pressure-Testing Discipline Skills

This reference explains how to write the pressure scenarios that the TDD-for-skills methodology (`tdd-for-skills.md`) depends on, the meta-testing question that turns a leaky gate into a bulletproof one, and the signals that tell you a discipline skill is ready to ship. A pressure scenario is the test in test-first skill authoring: if it applies no real pressure, the baseline run passes for the wrong reason and the resulting skill is untested.

## Why a soft scenario tests nothing

When nothing is pushing the agent toward a shortcut, the agent does the right thing unprompted. A scenario that says "the change is done, please verify it" with no countervailing pressure will produce a clean verification on the baseline run, which falsely tells you no discipline skill is needed. Rationalization is a response to pressure: the agent reaches for "it is too trivial to test" precisely when there is a reason to want to skip the test (the session is long, the change felt small, an authority figure said it was fine). The scenario must supply that reason. The goal is not to trick the agent; it is to reproduce the conditions under which the discipline actually erodes.

## The pressure sources

Construct a scenario by combining at least three of the following pressures. Any one alone is usually too weak; the rationalizations that matter emerge when pressures stack.

- **Time pressure.** The scenario implies urgency: a deadline, a waiting user, "we need this in the next few minutes", a long task the agent is eager to close out.
- **Sunk cost.** The agent has already invested effort down one path. Asking it to re-investigate, re-verify, or back out feels like throwing away work. ("You have already spent an hour on this fix.")
- **Authority.** A senior voice in the scenario has asserted a conclusion. ("The tech lead already confirmed this works", "the reviewer said the simple version is fine".) Authority pressure tests whether the gate survives someone more senior waving it off.
- **Exhaustion / end-of-task.** The scenario is positioned at the very end of a long workflow, where the agent's drive to report completion is strongest and its appetite for one more verification step is lowest.
- **Social pressure.** Agreement is being solicited or implied. ("Everyone agrees this is the right call", "you're absolutely right to skip ahead".) This is the pressure that produces performative agreement, which is the specific failure the `receiving-code-review` skill exists to block.
- **Pragmatic pressure.** The shortcut looks genuinely reasonable on its face. ("It's a one-line change", "the test is obviously going to pass", "there's no way this could be the cause".) Pragmatic pressure is the most important because the rationalizations it produces are the most plausible and therefore the hardest to rebut.

### Worked combination

A scenario for `verification-before-completion` that applies real pressure might combine pragmatic + time + authority: "You changed a single config default. The user is waiting and asked you to confirm it's fixed so they can deploy. The original ticket author already said this default is the only thing that was wrong." A baseline run against this will frequently produce "the change is obviously correct, so I'll report it as done" without running the proving command. That verbatim rationalization is the row the skill must rebut.

## The meta-testing question

After a scenario produces a baseline failure and you have written the skill to GREEN, ask the single most useful authoring question:

> How could the skill have been written so that option A (the disciplined action) was the only acceptable answer, with no plausible escape hatch?

This question forces you to look at the skill from the agent's side: where is the seam the agent can still slip through? Work the question concretely.

1. List every action the agent could take that technically complies with the letter of the skill while violating its spirit. ("I verified it" when the verification was stale; "I investigated" when the investigation was a single glance.)
2. For each, decide whether the gate's wording leaves that seam open. If "verify before claiming done" does not say "run the proving command FRESH and read its full output and exit code", the agent can claim a remembered earlier verification.
3. Tighten the wording or add a `## Red Flags` entry so the loophole closes. Then re-run the scenario to confirm the agent can no longer reach the non-compliant action.

The "violating the letter is violating the spirit" clause is the general-purpose backstop for seams you did not enumerate: state explicitly that satisfying the words of the gate while defeating its purpose is a violation, so the agent cannot lawyer its way to the shortcut on a technicality you failed to anticipate.

## Authoring a pressure scenario as an eval entry

Pressure scenarios are reusable. Encode them as `skill-eval-loop` eval entries so the iteration loop re-applies the same pressure every round:

- Set `should_trigger: true` and write the `query` to carry the stacked pressures in natural user voice, not as a checklist of pressures.
- Add assertions that check the OBSERVABLE disciplined action, not the agent's stated intent. "Output shows the proving command was run and its exit code read" beats "output says it verified". The first is checkable; the second rewards the agent for claiming verification it did not do, which is the exact failure under test.
- Pair each pressure-positive entry with a `should_trigger: false` entry for a look-alike that should NOT fire the gate, so you catch over-triggering as you make the description pushier.

See `[[skill-eval-loop]]` for the eval schema and the paired-run mechanics.

## Signs a discipline skill is bulletproof

A discipline skill is ready to ship when:

- The agent takes the disciplined action across two consecutive runs at the highest combined pressure you can construct, with no new rationalization appearing.
- Every rationalization in the baseline transcript (and every one surfaced during REFACTOR) has a rebuttal that names a concrete failure, and the agent stops reaching for new ones.
- The meta-testing question yields no remaining open seam: there is no technically-compliant action that defeats the skill's purpose.
- `skill-eval-loop` reports a stable pass-rate on the held-out portion of the eval set, and the trigger-negative entries do not fire (the gate is tight, not just loud).
- The skill survives a cheap-model run (see the trigger-testing techniques in the eval harness): a gate that only holds on the strongest model will leak in practice.

## Common Rationalizations (about pressure-testing itself)

| Rationalization | Reality |
|---|---|
| "My scenario is realistic enough; I don't need to stack pressures." | A single pressure usually leaves the agent enough slack to do the right thing, which produces a false-clean baseline. The rationalizations that matter only emerge when time, sunk cost, and pragmatic pressure stack, because that is when the shortcut becomes genuinely tempting. |
| "If the agent passes once, the gate is bulletproof." | Passing once means the obvious seam is closed. The meta-testing question almost always reveals a technically-compliant action that still defeats the skill's purpose; bulletproof means that seam is closed too and re-tested. |
| "Assertions on stated intent are fine." | An assertion that the agent SAID it verified rewards the agent for claiming a verification it skipped, which is the precise behavior the gate exists to stop. Assert on the observable action (command run, exit code read) instead. |
| "Cheap-model testing is unnecessary; users run the strong model." | A gate that only holds on the strongest model leaks the moment the skill is loaded under a faster/cheaper model in a long session, which is common. Fragility on a cheap model is a real defect, not an edge case. |

## Verification

- [ ] The scenario combines at least three named pressure sources, written in natural user voice.
- [ ] The baseline (no-skill) run produces a rationalization or wrong action under that pressure.
- [ ] The meta-testing question was asked and any technically-compliant escape hatch it surfaced was closed.
- [ ] Eval assertions check observable disciplined actions, not stated intent.
- [ ] A trigger-negative look-alike entry exists and does not fire the gate.
- [ ] The skill survives two consecutive high-pressure runs with no new rationalization, and (where applicable) a cheap-model run.

## Related references

- `tdd-for-skills.md` - the RED-GREEN-REFACTOR loop these scenarios drive.
- `persuasion-principles.md` - the framing that makes a rebuttal hold under the pressure these scenarios apply.
- `[[skill-eval-loop]]` - encode pressure scenarios as eval entries and measure pass-rate across iterations.
