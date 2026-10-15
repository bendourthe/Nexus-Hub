## Opus 4.7 Practices

Four prompting habits that matter specifically for Opus 4.7 (Claude 4.7 family). These are not generic best practices - they address concrete behavioral shifts vs Opus 4.6 and earlier models. Apply them alongside the Effort-Level Strategy above.

### Positive examples over negative instructions

Tell the model what *to* do, not what *not* to do. Negative instructions ("don't use X") force the model to represent X before rejecting it, which wastes reasoning budget and occasionally pattern-matches back to the forbidden option. Positive instructions give the model a concrete target.

| Bad (negative) | Good (positive) |
|----------------|-----------------|
| "Don't use class components." | "Use function components with hooks." |
| "Don't catch exceptions silently." | "Log every caught exception with the request ID and re-raise or return a structured error." |
| "Don't put logic in the view layer." | "Keep the view layer pure: it only reads props and emits events. Put logic in the hook / store layer." |

When a negative rule is unavoidable (e.g., "do not call the database"), pair it with the positive alternative ("use the repository layer instead").

### Explicit tool-invocation prompts

Opus 4.7 has a reasoning-first posture: it prefers thinking to tool invocation. That is usually the right default - but it means 4.7 no longer infers tool use as readily as 4.6. When you want a specific tool run, name it explicitly.

| Bad (implicit) | Good (explicit) |
|----------------|-----------------|
| "Check for issues in this file." | "Run `ruff check src/auth.py` and report the violations with file:line references." |
| "Look at the tests." | "Run `pytest tests/unit/test_auth.py -v` and report which tests passed or failed." |
| "See what's in the repo." | "Use the Glob tool to list `src/**/*.py` files." |

This is especially important when you want parallel tool calls. Opus 4.7 will usually batch them when asked explicitly ("make these three reads in a single message") but will sequentialize them under an ambiguous instruction.

### Adaptive thinking without fixed budgets

Do not set fixed thinking-budget tokens alongside `effortLevel`. Opus 4.7 scales its thinking budget adaptively per turn based on task difficulty; a fixed budget truncates reasoning on hard turns and wastes budget on easy ones. Set `effortLevel` and let the model manage the underlying budget.

**Prompt pattern**: "Think through this carefully." is the right shape.
**Anti-pattern**: "Use 20k thinking tokens." or `max_thinking_tokens=20000`.

If you *do* need to cap reasoning for cost reasons, drop one effort tier (e.g., `xhigh` to `high`) rather than clamping thinking tokens directly.

### First-turn specification checklists

The single largest quality gain comes from front-loading the specification. Opus 4.7 rewards a crisp first turn: it commits its reasoning to the goal you state, and rework is expensive. Put goal, constraints, acceptance criteria, and out-of-scope items all in the first message.

Related skills: [plan-before-code](../../workflow/plan-before-code/SKILL.md), [spec-driven-development](../../developer-experience/spec-driven-development/SKILL.md).

**First-turn template** (copy into your opening message):

```
Goal:              [One sentence - what "done" looks like]
Constraints:       [Language / runtime / library / perf / security constraints]
Acceptance:        [Observable checks - commands that prove it works]
Out of scope:      [What NOT to do - boundaries the model will otherwise cross]
Context pointers:  [File paths or links to the docs the model should read first]
```

Filling all five lines in the first turn prevents the "one-question-per-turn" ping-pong that wastes context and dilutes reasoning (see the batched-clarifying-questions rule in the platform templates).
