# Optional Authoring Self-Check Rubric

Optional pattern for a content-producing skill that grades its own output before returning it. It generalizes the runtime self-check loop that `anti-slop-editing` already ships. Read this file only when step 4.1 of `skill-create` applies; a skill that produces no prose or structured content does not need it.

This is guidance and a template, not a runtime. Nothing here is executed, scored, or enforced by a tool, and no rubric engine exists.

## Rule ownership

| Concern | Owner | This file does |
|---|---|---|
| Prose-quality checks (point, voice, proportional cutting, ASCII punctuation, named patterns) | `anti-slop-editing`, in `catalog/skills/developer-experience/anti-slop-editing/references/self-check.md` | Links to it; never restates its checks |
| Completion evidence and the fresh-evidence rule | `verification-before-completion` | Hands off to it after the loop |
| Behavioral benchmarking of a skill (with-skill versus baseline runs) | `skill-eval-loop` | Points to it for routing and outcome evaluation |
| The bounded evaluate/fix/recheck loop and the rubric template below | `skill-create` (this file) | Owns |

## When to add a rubric

Add one when the new skill returns content a reader consumes (a report, a document, a message, a structured artifact) and at least one quality property can be stated as a PASS/FAIL check on that content. Skip it when every quality property is already an observable artifact the skill's Verification section checks.

## Template

Copy this shape into the new skill's `references/self-check.md` and link it from the skill body (the orphan audit fails an unlinked file).

```markdown
# Self-Check Rubric

Grade the output against every applicable check before returning it.

## Delegated checks

- Prose quality: apply `anti-slop-editing` `references/self-check.md` shared checks 1-4.

## Skill-specific checks

1. **<Check name>.** <One observable property of the output>. PASS/FAIL.
2. **<Check name>.** <One observable property of the output>. PASS/FAIL.

## Budget

At most <N> evaluate/fix/recheck rounds (default 3).
```

Each check names one property a second reader could confirm from the output alone. "The output is good" is not a check.

## Bounded evaluate/fix/recheck

1. **Evaluate.** Grade every applicable check, including the delegated prose checks. Record each as PASS, FAIL, or INCONCLUSIVE.
2. **Fix.** Change only what a FAIL names.
3. **Recheck.** Re-grade the whole applicable set, because a fix can regress another check.
4. **Stop** when every check is PASS, or when the round budget is spent, whichever comes first.

The budget is a hard ceiling. When it is spent with a check still FAIL, return the output with an owned finding: the check name, the last failing evidence, and the owner who must resolve it. Do not report the rubric as passed.

## What is not covered

- **Missing delegate.** If `anti-slop-editing` or its `references/self-check.md` is unavailable, mark the prose-quality checks as not covered, name the missing skill, and continue with the skill-specific checks. Do not reconstruct its checks from memory.
- **Inconclusive result.** A check the agent cannot decide from the output alone is INCONCLUSIVE, which is reported as not covered, never as PASS.

## Self-check is not independent verification

The loop is the author grading its own work, so it cannot satisfy a completion claim on its own. After the loop, the skill's Verification section still runs on observable artifacts under `verification-before-completion`, and a skill whose behavior needs measuring uses `skill-eval-loop` for paired runs. A rubric pass, an exhausted budget, or a not-covered check is reported as exactly that.
