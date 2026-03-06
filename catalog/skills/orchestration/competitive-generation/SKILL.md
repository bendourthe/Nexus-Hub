---
name: competitive-generation
description: Run multiple AI agents in parallel on the same task, collect their outputs, and select the best implementation using an objective scoring rubric (test passage rate, diff size, dependency count, lint score, complexity). Use for high-stakes or high-value changes where the cost of multiple attempts is justified.
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

## Best Practices

- **Use 2-3 candidates, not more**: diminishing returns set in quickly; 3 candidates provide sufficient diversity without excessive cost
- **Use different models for maximum diversity**: agents using the same model tend to produce similar code; cross-model competition yields more distinct approaches
- **Include cost analysis**: track the token cost of competitive generation so you can make informed decisions about when it is worth the investment
- **Reserve for high-value changes**: competitive generation costs N times a single run; use it for security-critical, performance-critical, or architecturally significant changes, not routine tasks
- **Keep the scoring rubric objective**: every criterion must be measurable by a command or tool; subjective criteria ("code readability") are not reliable for automated comparison
- **Preserve runner-up insights**: non-winning candidates may contain good ideas (a clever test, a useful abstraction) worth extracting even if the overall implementation was not selected

## Related Skills

- `cross-model-orchestrator` - Multi-model workflow (role-based, not competitive)
- `quality-gate-definitions` - Reusable criteria that can be adapted for scoring
- `intent-based-review` - Review the winning candidate by acceptance criteria
- `adversarial-verifier` - Stress-test the winning candidate after selection

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Best-of-N selection, multi-agent comparison patterns, objective code quality metrics
