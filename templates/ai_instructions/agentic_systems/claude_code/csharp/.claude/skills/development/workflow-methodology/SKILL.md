---
name: workflow-methodology
description: Development workflow including task breakdown methodology for complex projects and the CRITICAL iterative testing protocol using tests/temp/. Includes analysis phase, subtask principles, quality gates, and the full test-driven problem solving workflow. Use when planning complex tasks, breaking down projects, implementing features that need testing, or troubleshooting issues.
---

# Development Workflow Methodology

## Task Breakdown Methodology

### When to Use Task Breakdown

**Apply systematic breakdown for:**
- Projects estimated >30 minutes
- Multi-component applications
- Complex feature implementations
- Integration tasks with dependencies
- Refactoring projects
- Any task with unclear scope

### Analysis Phase

**Always start with:**

1. **Requirements Gathering**
   - Identify all components needed
   - Map dependencies between components
   - Clarify acceptance criteria

2. **Complexity Assessment**
   - Determine scope and boundaries
   - Identify technical challenges
   - Estimate effort for each component

3. **Prerequisites Check**
   - List required setup and tools
   - Verify environment readiness
   - Identify knowledge gaps

4. **Risk Analysis**
   - Identify potential blockers
   - Plan mitigation strategies
   - Note assumptions being made

5. **Success Metrics**
   - Define measurable outcomes
   - Establish verification criteria
   - Set quality thresholds

### Task Template

```markdown
## Project: [Name]

### Overview
[2-3 sentence scope description]

### Prerequisites
- [Requirement 1]
- [Requirement 2]

### Subtask X: [Title]
**Objective**: [Clear, specific goal]
**Deliverables**: [Expected outputs]
**Time Estimate**: [15-45 minutes]
**Dependencies**: [Previous tasks that must be complete]

**Prompt**:
```
[Step-by-step instructions]
[Expected structure/format]
[Standards to follow]
[Success criteria]

Complete this subtask and pause for review.
Confirm completion before proceeding to next subtask.
```
```

### Subtask Principles

Each subtask should be:

- **Self-Contained**: Can be completed independently
- **Clearly Defined**: Unambiguous objectives and deliverables
- **Appropriately Scoped**: 15-45 minutes of focused work
- **Logically Sequenced**: Builds on previous tasks
- **Verifiable**: Has testable/observable results
- **Well Documented**: Clear criteria for completion

### Quality Gates

Before proceeding to the next subtask, verify:

- [ ] **Functionality**: Subtask objective achieved
- [ ] **Style Compliance**: Code follows project standards
- [ ] **Documentation**: Appropriate comments/docstrings added
- [ ] **Tests**: Relevant tests written or updated
- [ ] **Performance**: No obvious performance issues
- [ ] **Security**: No security vulnerabilities introduced
- [ ] **Dependencies**: All imports/dependencies resolved
- [ ] **Error Handling**: Appropriate exceptions handled

---

## Iterative Testing Protocol

**CRITICAL: Test-Driven Problem Solving**

When implementing new features, fixing bugs, or troubleshooting issues, follow this iterative protocol to ensure solutions actually work before claiming completion.

### Protocol Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 ITERATIVE TESTING PROTOCOL                   │
├─────────────────────────────────────────────────────────────┤
│  1. Create temporary test script in tests/temp/              │
│  2. Write challenging tests for the feature/fix              │
│  3. Implement solution                                       │
│  4. Run tests                                                │
│     ├─ FAIL → Document in DEVLOG, modify, repeat step 4     │
│     └─ PASS → Proceed to step 5                             │
│  5. Clean up: Delete temp tests, move valuable ones         │
│  6. Document final solution in DEVLOG                       │
└─────────────────────────────────────────────────────────────┘
```

### Step 1: Create Temporary Test Scripts

**Location:** `tests/temp/` directory

**Naming Convention:**
- `test_feature_validation.py` - For new features
- `test_bug_reproduction.py` - For bug fixes
- `test_[specific_issue].py` - For specific issues

**Test Design Principles:**
- Write **challenging** tests that thoroughly validate the solution
- Include **edge cases** and boundary conditions
- Include **error conditions** and exception handling
- Test **integration points** with other components
- Make tests **fail first** to verify they catch issues

### Step 2: Implement Solution

- Write or modify code to address the issue
- Follow all code standards and best practices
- Document your approach in DEVLOG.md as you work
- Keep changes focused and minimal

### Step 3: Run Tests and Iterate

**If tests FAIL:**
```markdown
## DEVLOG Entry

### Feature/Bug: [Name]

**Iteration 1**:
- Tests failed: [Describe failure]
- Root cause: [Analysis]
- Solution attempt: [What was tried]

**Iteration 2**:
- Tests failed: [Describe failure]
- Root cause: [Analysis]
- Solution attempt: [What was tried]

**Iteration N**:
- Tests PASSED
- Final solution: [Summary]
```

**Continue iterating until:**
- All tests pass
- Solution is verified complete
- No regressions introduced

**If tests PASS:**
- Verify solution completeness
- Check for any missed edge cases
- Proceed to cleanup

### Step 4: Clean Up Temporary Tests

**IMPORTANT:** After successful implementation:

1. **Delete all files** in `tests/temp/` directory
2. **Move valuable test cases** to permanent test suites:
   - Unit tests → `tests/unit/`
   - Integration tests → `tests/integration/`
   - Feature tests → `tests/[feature]/`
3. **Document** which tests were moved and why

### Step 5: Document Final Solution

**DEVLOG Entry Template:**
```markdown
### Feature/Bug: [Name] - COMPLETED

**Summary**: [What was implemented/fixed]

**Iterations**: [Number of attempts]

**Key Challenges**:
- [Challenge 1]: [How resolved]
- [Challenge 2]: [How resolved]

**Tests**:
- Temporary: Deleted from tests/temp/
- Permanent: [X] test cases moved to [location]

**Files Changed**:
- [file1.py]: [What changed]
- [file2.py]: [What changed]
```

### Example Workflow

```markdown
## DEVLOG.md Entry

### Feature: User Authentication - Password Validation

**Iteration 1**: Created tests/temp/test_password_validation.py
- 5 test cases for password strength
- Tests failed: Password validation too weak
- Solution: Enhanced regex pattern for complexity

**Iteration 2**: Re-ran tests
- Tests failed: Edge case with special characters not handled
- Solution: Added character escaping in validation

**Iteration 3**: Re-ran tests
- Tests failed: Unicode passwords causing errors
- Solution: Added unicode normalization

**Iteration 4**: Final run
- All 5 tests passed
- Added 3 additional edge case tests
- All 8 tests passed

**Cleanup**:
- Deleted tests/temp/test_password_validation.py
- Moved 5 core tests to tests/auth/test_authentication.py
- Kept 3 edge case tests as regression tests

**Files Changed**:
- src/auth/validators.py: Enhanced validate_password()
- tests/auth/test_authentication.py: Added 5 tests
```

### Benefits of Iterative Testing

1. **Ensures Quality**: Solutions actually work before claiming completion
2. **Documents Process**: Full history of problem-solving approach
3. **Prevents False Claims**: No premature declarations of success
4. **Creates Robust Code**: Multiple iterations catch edge cases
5. **Maintains Clean Repo**: No temporary test clutter in production
6. **Enables Learning**: Each iteration provides insights
7. **Supports Debugging**: Clear trail if issues resurface

---

## Integration with DEVLOG.md

**CRITICAL: All development activity should be documented in DEVLOG.md**

### What to Document

- Task list updates
- Iteration details for complex implementations
- Challenges encountered and solutions
- Technical decisions and rationale
- Test results and coverage
- Performance observations

### What NOT to Create

**NEVER create separate documentation files like:**
- `TROUBLESHOOTING_ISSUE.md`
- `FIX_SUMMARY.md`
- `IMPLEMENTATION_NOTES.md`
- `BUG_FIX_DETAILS.md`

**ALWAYS use DEVLOG.md** for all development documentation.

---

## Decision Tree: When to Use Task Breakdown

```
Is the task complex?
│
├─ Simple (< 30 min, single component)
│   └─ Proceed directly with implementation
│
└─ Complex (> 30 min OR multiple components)
    │
    ├─ New Feature?
    │   └─ Full task breakdown + iterative testing
    │
    ├─ Bug Fix?
    │   └─ Create temp test to reproduce, then iterative fix
    │
    ├─ Refactoring?
    │   └─ Task breakdown + comprehensive test coverage first
    │
    └─ Integration?
        └─ Full task breakdown with dependency mapping
```

---

## Quick Reference

### Task Breakdown Checklist
- [ ] Requirements gathered
- [ ] Complexity assessed
- [ ] Prerequisites verified
- [ ] Risks identified
- [ ] Success metrics defined
- [ ] Subtasks created (15-45 min each)
- [ ] Dependencies mapped

### Iterative Testing Checklist
- [ ] Temp test created in tests/temp/
- [ ] Challenging tests written
- [ ] Solution implemented
- [ ] Tests run and iterated until pass
- [ ] Temp tests deleted
- [ ] Valuable tests moved to permanent location
- [ ] DEVLOG updated with full history
