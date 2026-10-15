---
name: code-simplification
description: "Reduces code complexity by removing unnecessary abstraction, dead code, and over-engineering -- without changing behavior. Use when code has grown hard to understand, when a component is over-abstracted for its actual use cases, or when simplification is the goal rather than feature addition. Different from language-specific cleanup skills (python-cleanup, javascript-cleanup) -- this skill addresses structural complexity across any codebase. Trigger phrases: simplify this, this is too complex, over-engineered, reduce complexity, make it simpler, clean up the design."
summary_l0: "Reduce structural complexity by eliminating over-abstraction and dead code without changing behavior"
overview_l1: "This skill provides a systematic process for reducing code complexity -- removing unnecessary abstraction layers, dead code, premature generalization, and over-engineering without changing observable behavior. Use it when code has accumulated complexity through growth, when abstractions exist for use cases that never materialized, or when simplicity is explicitly the goal. Key capabilities include complexity assessment (cyclomatic, cognitive), abstraction necessity analysis, dead code detection, and safe refactoring sequences. The expected output is code that is functionally equivalent but shorter, clearer, and easier to change. Trigger phrases: simplify this code, too much abstraction, over-engineered, reduce complexity, clean up the design, this is too complicated."
---

# Code Simplification

Make code do the same thing with less. The best code is the code that does not exist.

## When to Use This Skill

Use when:
- Code is hard to understand on first reading
- A component has abstraction layers that serve no current use case
- Functions or classes do more than their name implies
- Dead code exists but has never been removed
- The architecture was designed for scale that never arrived

**When NOT to use:** When simplification would remove future-needed flexibility (verify this is actually needed, not hypothetical). For language-specific style issues, use `python-cleanup`, `javascript-cleanup`, etc. For dead code detection at scale, use `dead-code-eliminator`. For pre-write construction (should this exist, stdlib, native, one line), use `minimal-construction`; this skill remains post-write behavior-preserving collapse.

## Complexity Assessment First

Before simplifying anything, measure the current complexity to know what you are improving:

**Cyclomatic complexity** (number of independent paths through code):
- 1-5: Simple, easy to test
- 6-10: Moderate, consider simplification
- 11+: Complex, actively simplify

**Cognitive complexity** (how hard it is to understand):
- Deeply nested conditionals
- Multiple return points with complex conditions
- State spread across many variables
- Long function chains where each step requires knowing the previous

**Abstraction audit** (how many layers between intent and implementation):
```
Is this layer doing something the layers above and below it cannot?
If not, it can be removed.
```

**Simplicity heuristic** (human-readable gut check):
- Would a senior engineer reading this code immediately see it as unnecessarily complex?
- Could this be rewritten in half the lines without losing clarity? If yes, it should be.
- If you needed to explain what this code does to a new team member, would the explanation be shorter than the code itself? If not, the code is too complex.

## Instructions

### Step 1: Understand Before Changing

Read the code end-to-end before changing anything. Write down in one sentence what the code does. If you cannot do this, the code is too complex to simplify safely -- document what you do understand first.

Write a characterization test if one does not exist:
```python
def test_current_behavior():
    """Documents current behavior before simplification."""
    result = complex_function(known_input)
    assert result == known_output
```

This test will catch any behavior change introduced during simplification.

### Step 2: Remove Dead Code

Dead code is safer to delete than to simplify. Check for:

- Functions that are never called (grep for usages; check git log for last call date)
- Conditional branches that can never be true
- Parameters that are always passed the same value
- Commented-out code blocks
- Feature flags for features that shipped and are now always-on

Delete dead code before attempting any other simplification -- it removes noise.

### Step 3: Flatten Unnecessary Abstraction

Ask for each abstraction layer:
1. Does this layer have more than one caller?
2. Does this layer have meaningful logic beyond delegation?
3. Does this layer exist for a use case that actually materialized?

If all answers are no, collapse it:

```python
# Before: 3 layers of abstraction for one use case
class UserRepository:
    def get(self, id): return self.store.fetch('users', id)

class UserStore:
    def fetch(self, table, id): return self.db.query(table, id)

class Database:
    def query(self, table, id): return db.execute(f"SELECT * FROM {table} WHERE id = {id}")

# After: direct, when there's only one caller and no polymorphism
def get_user(id: int) -> User:
    return db.execute("SELECT * FROM users WHERE id = ?", [id])
```

### Step 4: Reduce Nesting

Each level of nesting multiplies cognitive load. Flatten using early returns and guard clauses:

```python
# Before: nested conditionals
def process(user, order):
    if user is not None:
        if user.is_active:
            if order is not None:
                if order.total > 0:
                    return charge(user, order)
    return None

# After: guard clauses
def process(user, order):
    if user is None or not user.is_active: return None
    if order is None or order.total <= 0: return None
    return charge(user, order)
```

### Step 5: Consolidate Duplicate Logic

Three similar functions that diverge in small ways are candidates for consolidation -- but only if the consolidation is genuinely simpler, not just more abstract:

```python
# Before: three functions with 90% overlap
def notify_by_email(user, message): ...
def notify_by_sms(user, message): ...
def notify_by_push(user, message): ...

# After: one function if the variation is regular and the callers are identical
def notify(user, message, channel: Literal["email", "sms", "push"]): ...

# Only consolidate if all call sites use the same pattern. Don't consolidate if
# the three functions have genuinely different error handling, retry logic, or side effects.
```

### Step 6: Verify Behavior is Unchanged

Run the full test suite. The characterization test from Step 1 must still pass. If any behavior changed, that was not simplification -- it was modification. Revert and re-approach.

## The Rule of Three Similarity

- 1 occurrence: just write it
- 2 occurrences: tolerate duplication
- 3 occurrences: consider a shared abstraction (but only if the abstraction is genuinely simpler)

Abstraction for 2 callers is premature. Abstraction that is harder to understand than the duplication it replaces is wrong.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We might need this abstraction later" | You might. Build it then, not now. YAGNI -- You Aren't Gonna Need It. |
| "Removing this layer will break the tests" | Tests that break during behavior-preserving simplification are testing implementation, not behavior. Fix the tests, then simplify. |
| "This is complex because the domain is complex" | Domain complexity does not require implementation complexity. Simplify the code; the domain remains. |
| "I'll understand it once I'm familiar with it" | New team members, your future self at 2am, and AI agents working in the codebase will not have that luxury. |
| "The original author intended this for future use" | The original author is not here. The code you have is the code that matters. |

## Verification

- [ ] All existing tests pass after simplification (behavior is unchanged)
- [ ] Cyclomatic complexity of changed functions is lower than before (measure and compare)
- [ ] No abstraction layer remains that has only one caller and no meaningful logic
- [ ] No dead code remains (functions with zero callers, branches that can never execute)
- [ ] The code can be read and understood by a developer unfamiliar with it in under 5 minutes

## Related Skills

- [[dead-code-eliminator]] -- systematic dead code removal at codebase scale
- [[minimal-construction]] -- pre-write ladder (should this exist, stdlib, native, one line); this skill does not restate that ladder
- [[refactoring-expert]] -- behavior-preserving refactoring using Fowler's catalog
- [[python-cleanup]] -- Python-specific style and pattern cleanup
- [[javascript-cleanup]] -- JavaScript/TypeScript-specific cleanup
- [[code-smell-detector]] -- identify structural code quality issues before simplification
