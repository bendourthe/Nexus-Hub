---
name: competitive-generation
description: Run multiple AI agents in parallel on the same task, collect their outputs, and select the best implementation using an objective scoring rubric (test passage rate, diff size, dependency count, lint score, complexity). Use for high-stakes or high-value changes where the cost of multiple attempts is justified.
summary_l0: "Run parallel agents on the same task and select the best output by scoring rubric"
overview_l1: "This skill runs multiple AI agents in parallel on the same task, collects their outputs, and selects the best implementation using an objective scoring rubric. Use it for high-stakes or high-value changes where the cost of multiple attempts is justified, when comparing outputs from different models or prompts, or when maximum code quality is required. Key capabilities include parallel agent execution coordination, objective scoring rubric application (test passage rate, diff size, dependency count, lint score, complexity), output comparison and ranking, best-implementation selection with evidence, cost-benefit analysis of competitive generation, and winner explanation with scoring breakdown. The expected output is the best implementation selected from multiple candidates with a comparative scoring report. Trigger phrases: competitive generation, parallel agents, best-of-N, compare implementations, scoring rubric, multi-attempt, high-stakes change, best output."
---

# Competitive Multi-Agent Generation

Run N agents in parallel on the same implementation task, then select the best result using objective criteria. Instead of relying on a single agent's output, competitive generation produces multiple candidates and picks the winner based on measurable quality signals. This approach trades token cost for implementation quality and is recommended for high-stakes changes where getting it right the first time matters.

## When to Use This Skill

Use this skill when:

- The change is high-stakes (security, payments, data integrity) and the cost of a bug exceeds the cost of multiple agent runs
- You want to compare different implementation approaches objectively
- A single agent's output has been inconsistent or unreliable for this type of task
- The task has a clear, testable specification that can serve as an objective evaluation criterion
- You are using a multi-model workflow and want to leverage model diversity

Do NOT use this skill when:

- The task is routine or low-risk (the token cost is not justified)
- No tests or acceptance criteria exist to evaluate candidates objectively
- The change is purely cosmetic (formatting, renaming, comments)
- You are on a limited API budget and cannot afford N times the token cost

**Trigger phrases**: "competitive generation", "compare implementations", "run multiple agents", "best-of-N", "parallel implementations", "select best implementation", "agent competition"

## What This Skill Does

- **Parallel Task Setup**: Configures N independent agent sessions with the same task specification
- **Candidate Collection**: Gathers implementation outputs from each agent as separate branches or directories
- **Objective Scoring**: Evaluates each candidate against a scoring rubric with measurable criteria
- **Winner Selection**: Selects the highest-scoring candidate with full justification
- **Comparison Artifact**: Produces COMPARISON.md documenting all candidates, scores, and the selection rationale

## Instructions

### Step 1: Define the Task Specification

Create a task specification that all agents will receive. The specification must be precise enough that different agents produce comparable outputs.

**Required specification elements:**

```markdown
## Task Specification

### Objective
[One-sentence description of what to implement]

### Acceptance Criteria
| # | Criterion | How to Verify |
|---|-----------|---------------|
| AC-1 | [testable statement] | [test command or manual check] |
| AC-2 | [testable statement] | [test command or manual check] |

### Constraints
- [Files that may be modified]
- [Files that must NOT be modified]
- [Performance requirements, if any]
- [Dependency restrictions, if any]

### Evaluation Criteria
Candidates will be scored on: test passage, diff size, dependency count, lint score, complexity.
```

### Step 2: Launch Parallel Agent Sessions

Run N agents (recommended: 2-3) with the same specification. Use different models or different prompting strategies for diversity.

**Option A: Different models (recommended for diversity)**

```
Agent 1: Claude Opus   + task specification
Agent 2: Claude Sonnet + task specification
Agent 3: Codex CLI     + task specification
```

**Option B: Same model, different strategies**

```
Agent 1: "Implement with minimal changes to existing code"
Agent 2: "Implement using the cleanest architecture possible"
Agent 3: "Implement with maximum test coverage"
```

**Option C: Git worktrees for isolation**

```bash
# Create isolated worktrees for each agent
git worktree add ../candidate-1 -b candidate/approach-1
git worktree add ../candidate-2 -b candidate/approach-2
git worktree add ../candidate-3 -b candidate/approach-3

# Launch agents in their respective worktrees
# (Each agent works in isolation without affecting others)
```

### Step 3: Collect Candidate Outputs

After all agents complete, collect their outputs. Each candidate should include:

- The code changes (as a diff or branch)
- Test results (all tests must have been run)
- Any artifacts produced (PLAN.md, etc.)

### Step 4: Score Each Candidate

Evaluate each candidate against the scoring rubric. All criteria are objective and measurable.

**Scoring Rubric:**

| Criterion | Weight | Measurement | Scoring |
|-----------|--------|------------|---------|
| **Test passage rate** | 30% | `(passing tests) / (total tests)` | 100% = 10pts, 90-99% = 7pts, <90% = 0pts |
| **Acceptance criteria met** | 25% | `(criteria passing) / (total criteria)` | 100% = 10pts, per-criterion proportional |
| **Diff size** | 15% | Lines added + lines removed | Smallest = 10pts, others proportional |
| **New dependencies** | 10% | Count of new packages added | 0 = 10pts, 1 = 7pts, 2 = 4pts, 3+ = 0pts |
| **Lint score** | 10% | Lint errors + warnings in changed files | 0 = 10pts, 1-5 = 7pts, 6+ = 0pts |
| **Cyclomatic complexity** | 10% | Max complexity in changed functions | <5 = 10pts, 5-10 = 7pts, >10 = 3pts |

**Scoring commands:**

```bash
# Test passage rate
pytest --tb=no -q | tail -1              # Python
npm test 2>&1 | grep -E "Tests:|passing" # JavaScript

# Diff size
git diff --stat main...candidate-1 | tail -1

# New dependencies
diff <(git show main:requirements.txt) requirements.txt | grep "^>" | wc -l  # Python
diff <(git show main:package.json | jq '.dependencies') <(jq '.dependencies' package.json) # JS

# Lint score
ruff check . --statistics | tail -1      # Python
eslint src/ --format compact | wc -l     # JavaScript

# Cyclomatic complexity
radon cc . -a -nb -s | grep "Average"    # Python
npx es-complexity src/ --threshold 10    # JavaScript (if available)
```

### Step 5: Select the Winner

Calculate the weighted score for each candidate and select the highest.

**Comparison Table:**

```markdown
## Candidate Comparison

| Criterion (Weight) | Candidate 1 | Candidate 2 | Candidate 3 |
|--------------------|-------------|-------------|-------------|
| Test passage (30%) | 100% = 10 | 95% = 7 | 100% = 10 |
| Acceptance criteria (25%) | 5/5 = 10 | 5/5 = 10 | 4/5 = 8 |
| Diff size (15%) | 47 lines = 10 | 112 lines = 4 | 63 lines = 7 |
| New deps (10%) | 0 = 10 | 1 = 7 | 0 = 10 |
| Lint score (10%) | 0 = 10 | 3 = 7 | 0 = 10 |
| Complexity (10%) | 4 = 10 | 8 = 7 | 6 = 7 |
| **Weighted Total** | **10.0** | **7.3** | **8.8** |

**Winner**: Candidate 1 (score: 10.0)
```

**Tie-breaking rules** (in order):
1. Higher acceptance criteria score wins
2. Higher test passage rate wins
3. Smaller diff size wins
4. Fewer new dependencies wins

### Step 6: Produce the Comparison Report

Generate COMPARISON.md:

```markdown
# Competitive Generation Report

**Task**: [description]
**Date**: [timestamp]
**Candidates**: [count]
**Models Used**: [list]

## Task Specification
[copy of the specification from Step 1]

## Candidate Summaries

### Candidate 1: [Model / Strategy]
- **Approach**: [1-2 sentence summary]
- **Files changed**: [count]
- **Tests added**: [count]
- **Notable decisions**: [key choices]

### Candidate 2: [Model / Strategy]
...

## Scoring

[Comparison table from Step 5]

## Winner Selection

**Selected**: Candidate [N]
**Score**: [weighted total]
**Rationale**: [1-2 sentences explaining why this candidate won beyond just the numbers]

## Runner-Up Notes
[Any valuable ideas from non-winning candidates that should be preserved for future reference]

## Cost Analysis
| Candidate | Input Tokens | Output Tokens | Estimated Cost |
|-----------|-------------|---------------|---------------|
| 1 | [count] | [count] | $[amount] |
| 2 | [count] | [count] | $[amount] |
| Total | | | $[total] |
```

## Iterative Competition (Multi-Round)

The base pattern (Steps 1-6) runs N agents in parallel for a single round and picks the winner from that one draw. When the best candidate of a single round still falls short of the rubric ceiling, or when the candidates cluster closely and none clearly dominates, extend the competition across multiple rounds: each round is seeded by the previous round's winner, so quality climbs round over round instead of being fixed by a single draw.

When to escalate from a single round to multiple rounds:

- The single-round winner passes the rubric but leaves one dimension visibly weak (for example, it wins on tests but carries the largest diff).
- The top two or three candidates score within a narrow band, so the "winner" is close to a coin flip.
- The change is high-value enough that climbing from an 8.8 to a 9.6 is worth the additional rounds.

The mechanics:

- **Hill-climbing**: keep the current best candidate as the incumbent. Each round, generate challengers that vary the incumbent (a different approach to one weak dimension, a tighter diff, an added test). Replace the incumbent only when a challenger scores strictly higher on the same rubric, so the running score is monotonic and never regresses across rounds.
- **Co-evolution**: when the runners-up each carry a distinct strong idea (one has the cleanest abstraction, another the best test coverage), synthesize a new challenger that combines them rather than discarding the losers. The next incumbent can be a deliberate graft of the best parts, not just whichever single candidate survived the round.
- **Stopping rule**: stop when a round produces no rubric improvement over the incumbent for K consecutive rounds (a no-progress signature; K of 2 is a reasonable default), or when a pre-set round budget is hit, whichever comes first. Do not run "one more round" against a flat curve hoping for a lucky draw.
- **Token caution**: each round multiplies the per-round fan-out cost, so a 3-candidate, 4-round competition is up to 12 agent runs. Calibrate the round count and the fan-out width up front, treat the budget as fixed, and stop the moment the rubric converges.

Score challengers with an independent skeptic, not the generator that produced them, so the incumbent earns its place against adversarial scrutiny rather than self-assessment (see [[adversarial-verifier]]). Treat the round budget as a hard cost control, not a target to exhaust (see [[ai-billing-safeguards]]). Before committing to a multi-round competition at all, confirm that a fan-out is warranted for the task in the first place (see [[agent-orchestration-primitives]]).

## Best Practices

- **Use 2-3 candidates, not more**: diminishing returns set in quickly; 3 candidates provide sufficient diversity without excessive cost
- **Use different models for maximum diversity**: agents using the same model tend to produce similar code; cross-model competition yields more distinct approaches
- **Include cost analysis**: track the token cost of competitive generation so you can make informed decisions about when it is worth the investment
- **Reserve for high-value changes**: competitive generation costs N times a single run; use it for security-critical, performance-critical, or architecturally significant changes, not routine tasks
- **Keep the scoring rubric objective**: every criterion must be measurable by a command or tool; subjective criteria ("code readability") are not reliable for automated comparison
- **Preserve runner-up insights**: non-winning candidates may contain good ideas (a clever test, a useful abstraction) worth extracting even if the overall implementation was not selected

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "One good agent run is enough; running N is just burning tokens." | For a routine task, yes -- and this skill says NOT to use it then. But for a payments or data-integrity change, one undetected bug costs far more than N agent runs. Competitive generation buys insurance precisely where the failure cost is high. |
| "I will pick the winner by reading the diffs and choosing the one that looks cleanest." | "Looks cleanest" is the subjective judgement competitive generation exists to eliminate. The whole point is an objective rubric (test passage, diff size, lint score) so the selection survives a "why did you pick that one?" challenge. |
| "I can run this without tests; I will judge correctness by inspection." | With no tests or acceptance criteria there is no objective signal to rank candidates, so the comparison degenerates into a coin flip. The Do NOT list explicitly fences off this case. |

## Verification

- [ ] A single task specification was given identically to every agent
- [ ] Each candidate's output is captured as a separate branch or directory
- [ ] `COMPARISON.md` records the score of every candidate against the rubric
- [ ] The selected winner is the highest-scoring candidate, with the scoring breakdown shown
- [ ] The cost analysis (token cost of N runs vs. the value of the change) is documented

## Related Skills

- [[cross-model-orchestrator]] - Multi-model workflow (role-based, not competitive)
- [[quality-gate-definitions]] - Reusable criteria that can be adapted for scoring
- [[intent-based-review]] - Review the winning candidate by acceptance criteria
- [[adversarial-verifier]] - Stress-test the winning candidate after selection
- [[agent-orchestration-primitives]] - distinguishes best-of-N (this skill: one task, N attempts, pick a winner) from ranking/sorting many items by pairwise tournament (a distinct shape documented in its `references/five-patterns.md`)

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Best-of-N selection, multi-agent comparison patterns, objective code quality metrics
