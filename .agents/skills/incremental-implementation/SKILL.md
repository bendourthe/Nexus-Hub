---
name: incremental-implementation
description: "Implements features one small, tested step at a time -- never more than one task per cycle. Use when executing any implementation plan, to prevent scope expansion, half-built states, and undebuggable large diffs. Trigger phrases: implement this step by step, one task at a time, don't do everything at once, incremental changes, implement incrementally."
summary_l0: "Implement features one tested step at a time to prevent scope creep and undebuggable diffs"
overview_l1: "This skill enforces a disciplined one-task-at-a-time implementation discipline with a test-after-each-step cycle. Use it when executing any implementation plan -- especially for multi-file changes, refactoring, or features with multiple interacting components. Key capabilities include task scoping, checkpoint verification, scope containment, and rollback-ready commits. The expected output is a working, tested, committed state after each task -- never a half-built state spanning multiple incomplete tasks. Without this discipline, implementations accumulate debt through scope creep, interleaved changes become undebuggable, and rollback is impossible. Trigger phrases: implement step by step, one task at a time, incremental changes, don't do everything at once, implement incrementally, task-by-task execution."
---

# Incremental Implementation

Implement one task at a time. Verify it works. Commit. Move to the next. Never leave the codebase in a half-built state between tasks.

## When to Use This Skill

Use when:
- Executing any multi-step implementation plan
- Making changes that touch more than one file
- Refactoring existing code
- Working on a feature with multiple interacting components
- The change is large enough that rolling it back would be costly

**When NOT to use:** Single-file, single-function changes that are complete in one edit. For those, just make the change and verify.

## The Cycle

Each task follows exactly this cycle:

```
1. SCOPE  → Define the single task to complete right now
2. BUILD  → Implement only that task; nothing beyond it
3. VERIFY → Run the relevant tests / build / check
4. COMMIT → Commit the working state before moving on
5. REPEAT → Pick the next task
```

The cycle must complete before the next task begins. There is no skipping steps.

## Instructions

### Step 1: Define the Current Task

Before touching any file, write out in one sentence what you are about to implement and what "done" looks like for this task. This prevents scope creep at the moment you are writing code.

```
CURRENT TASK: Add input validation to the createUser endpoint
DONE WHEN: POST /users with missing email returns 422 with {"error": "email required"}
SCOPE: Only src/handlers/users.ts -- no other files
```

If you find yourself writing "and also..." -- stop. That's a new task.

### Step 2: Implement Only That Task

Rules during implementation:
- Change only the files listed in the task scope
- If you discover a necessary change in a different file, add it to the task list for later -- do not implement it now
- If you find a bug in a nearby function while implementing, note it -- do not fix it now
- Stop when the task's acceptance criterion is met, not when all related things are also improved

### Step 3: Verify Before Committing

Run the verification step defined for this task:

```bash
# Minimum: the relevant test(s) pass
npm test -- --testPathPattern=users

# If the change touches shared code: full test suite
npm test

# If the change touches configuration or build: ensure it still builds
npm run build
```

Do not commit until verification passes. If verification fails, fix the current task -- do not start the next task.

### Step 4: Commit the Working State

Each task gets its own commit with a message describing what changed:

```bash
git add src/handlers/users.ts tests/handlers/users.test.ts
git commit -m "feat(users): add email validation on POST /users"
```

This creates a clean rollback point. If the next task goes wrong, you can return to this state.

### Step 5: Update the Task List

Mark the completed task as done. Review whether the next task is still correct given what you just learned during implementation. Adjust if needed.

## Scope Containment Rules

These are the most common ways incremental discipline breaks down:

**Rule 1 -- One task at a time.** If the current task reveals another problem, add it to the list. Implement it after this task is committed.

**Rule 2 -- No "while I'm here" improvements.** Seeing messy code while implementing an unrelated change does not make cleanup part of this task. Log it, commit the task, then create a cleanup task.

**Rule 3 -- No half-built states in commits.** A commit where "the first half works but the second half is in progress" is not a commit -- it is a savepoint. Only commit when the task's acceptance criterion is met.

**Rule 4 -- Small tasks over large tasks.** If a task will change more than ~5 files, it can be split into smaller tasks. Smaller tasks have smaller diffs and simpler verification.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just do these two things together, they're related" | Related tasks still interact in unexpected ways. Two-task diffs double the debug surface. One task at a time. |
| "The test suite is slow, I'll verify at the end" | Failing tests at the end mean you cannot tell which task broke what. Verify after each task. |
| "This improvement is obvious and small" | Every "obvious and small" deviation is scope creep. Note it, finish the current task first, implement it as a separate task. |
| "I'll commit when the whole feature is done" | A single commit for a whole feature is untraceable, unreviewable, and unrollbackable. Commit each task separately. |
| "Fixing this bug I found will make my feature easier" | It will also expand the blast radius of this change. Log the bug, finish the current task, fix the bug separately. |

## Verification

- [ ] Each task was implemented independently (no mixed changes from multiple tasks in a single diff)
- [ ] Tests were run and passed after each task before moving to the next
- [ ] Each completed task has its own commit with a descriptive message
- [ ] No "while I'm here" changes are mixed into task commits
- [ ] The codebase is in a working, buildable state at the end of every commit

## Related Skills

- [[spec-driven-development]] -- produces the task list that this skill executes
- [[plan-before-code]] -- produces the implementation plan; this skill executes it
- [[test-driven-development]] -- pairs naturally with incremental implementation (write test first, then implement)
- [[code-commit-workflow]] -- commit message conventions and atomic change patterns
