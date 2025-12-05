---
name: plan-before-code
description: Guide Claude through exploration and planning phases before implementation (Anthropic best practice)
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Workflow
tags: [workflow, planning, best-practice, anthropic, methodology]
priority: CRITICAL
based_on: Anthropic Claude Code Best Practices 2025
---

# Plan Before Code

Guide Claude Code through systematic exploration and planning before jumping into implementation. This Anthropic-recommended workflow significantly improves code quality and reduces iterations.

## When to Use This Skill

Use this skill for:

- ✅ Any non-trivial implementation (>30 minutes estimated)

- ✅ Features requiring multiple files or components

- ✅ Bug fixes that need root cause analysis

- ✅ Refactoring existing code

- ✅ New features in unfamiliar codebases

- ✅ Architecture decisions

- ✅ Performance optimizations

- ✅ Security-sensitive changes

**Do NOT skip this for "quick fixes"** - the planning often reveals the "quick fix" is more complex than expected.

## What This Skill Does

This skill implements Anthropic's **#1 recommended best practice** for Claude Code: **Plan-Then-Execute**.

### Phase 1: Exploration (Gather Context)
- Read relevant files without modifying

- Understand existing architecture and patterns

- Identify dependencies and constraints

- Map affected components

- Research similar implementations

### Phase 2: Planning (Design Before Code)
- Break down the task into steps

- Identify potential challenges

- Consider alternative approaches

- Plan testing strategy

- Estimate effort and complexity

- Get approval before proceeding

### Phase 3: Execution (Implement the Plan)
- Follow the approved plan

- Make small, incremental changes

- Test continuously

- Document as you go

## Why This Works

**Without Planning** (Common Anti-Pattern):
```
User: "Add user authentication to the API"
Claude: *immediately starts writing code*
Result:

- ❌ Missed existing auth patterns

- ❌ Incompatible with current architecture

- ❌ Missing edge cases

- ❌ No test strategy

- ❌ Multiple iterations needed
```

**With Planning** (Best Practice):
```
User: "Add user authentication to the API"
Claude: *explores codebase, analyzes patterns, creates plan*
User: *reviews and approves plan*
Claude: *implements according to plan*
Result:

- ✅ Consistent with existing patterns

- ✅ Comprehensive implementation

- ✅ Edge cases covered

- ✅ Tests included

- ✅ Done right first time
```

## Prerequisites

- Claude Code installed and active

- Project context (CLAUDE.md recommended)

- Clear understanding of the goal

- Patience (don't skip planning!)

## Instructions

### Step 1: Request Exploration (DO NOT CODE YET)

Use this exact pattern:

```
"I need to [implement feature/fix bug/refactor code].

IMPORTANT: Do NOT write any code yet.

First, please explore and understand:

1. Read [relevant files/directories]

2. Identify existing patterns for [similar functionality]

3. Map out all files that will need changes

4. List any dependencies or constraints

5. Research any unfamiliar concepts or libraries

Provide a summary of your findings."
```

**Example**:
```
"I need to add rate limiting to our REST API endpoints.

IMPORTANT: Do NOT write any code yet.

First, please explore:

1. Read the current API route handlers

2. Identify existing middleware patterns

3. Check if any rate limiting exists elsewhere

4. Review our Redis/cache setup

5. Understand our authentication flow

Provide a summary of what you find."
```

### Step 2: Review Exploration Results

Claude will respond with findings like:
```
I've explored the codebase. Here's what I found:

1. **Current API Structure**

   - Express.js with route handlers in src/routes/

   - Middleware applied in src/middleware/

   - 15 API endpoints total

2. **Existing Patterns**

   - Authentication middleware already exists (auth.js)

   - Logging middleware for all requests

   - Error handling middleware

3. **Dependencies**

   - Express 4.18.2 installed

   - Redis client configured but underutilized

   - No rate limiting library currently

4. **Constraints**

   - Must work with existing auth system

   - Need to preserve current error handling

   - Redis available for state storage

5. **Similar Implementations**

   - Found commented-out rate limit code in old commits

   - Team previously used express-rate-limit library
```

**Review these findings carefully** - correct any misunderstandings before proceeding.

### Step 3: Request Detailed Plan

Now ask for a plan:

```
"Based on your exploration, please create a detailed implementation plan.

Include:

1. Approach and architecture decisions

2. Step-by-step implementation sequence

3. Files to create/modify (in order)

4. Testing strategy

5. Potential challenges and mitigations

6. Estimated complexity

Do NOT implement yet - just the plan."
```

### Step 4: Review and Approve Plan

Claude will provide a structured plan:

```
## Implementation Plan for Rate Limiting

### Approach
Use express-rate-limit with Redis store for distributed rate limiting
across multiple server instances.

### Implementation Steps

**Step 1: Install Dependencies**

- express-rate-limit (4.0.4)

- rate-limit-redis (3.0.2)
Files: package.json

**Step 2: Create Rate Limit Middleware**
Create: src/middleware/rateLimit.js

- Initialize Redis client

- Configure rate limit rules (100 req/15min per IP)

- Export middleware function

**Step 3: Apply to Routes**
Modify: src/routes/index.js

- Import rate limit middleware

- Apply globally or per-route basis

- Add custom messages for rate limit errors

**Step 4: Error Handling**
Modify: src/middleware/errorHandler.js

- Add specific handling for rate limit errors (429)

- Return user-friendly messages

**Step 5: Testing**
Create: tests/rateLimit.test.js

- Test rate limit enforcement

- Test Redis connection handling

- Test error responses

### Testing Strategy
- Unit tests for middleware logic

- Integration tests for API endpoints

- Load testing to verify limits work under pressure

### Potential Challenges
1. **Redis connection failures**: Add fallback to in-memory store

2. **Testing with Redis**: Use Redis mock or test container

3. **Rate limit bypass**: Ensure applied to all routes

### Estimated Complexity
Medium - 2-3 hours with testing
```

**Critical: Review and approve this plan before proceeding!**

Ask questions if anything is unclear:
```
"The plan looks good, but I have questions:

1. Why Redis over in-memory store?

2. Should we have different limits for authenticated users?

3. What about rate limiting by API key vs IP?"
```

### Step 5: Authorize Implementation

Once satisfied with the plan:

```
"Plan approved. Please proceed with implementation following the steps exactly as outlined."
```

**OR** request modifications:

```
"Please modify the plan:

- Use different rate limit (50 req/10min)

- Add separate limits for auth vs non-auth endpoints

- Include rate limit headers in responses

Then proceed with the updated plan."
```

### Step 6: Incremental Implementation

Claude will now implement step-by-step:

- ✅ Complete one step at a time

- ✅ Show progress after each step

- ✅ Test incrementally

- ✅ Pause if issues arise

### Step 7: Final Verification

After implementation:

```
"Please verify the implementation:

1. Run all tests

2. Check all files modified match the plan

3. Confirm no TODO items left

4. List any deviations from the plan"
```

## Complete Example Workflow

### 🎯 Example: Add Pagination to API Endpoints

#### Exploration Phase
```
User: "I need to add pagination support to our user listing API endpoint.

IMPORTANT: Do NOT write code yet.

Please explore:

1. Read src/routes/users.js and the user controller

2. Check if pagination exists elsewhere in the codebase

3. Review our database query patterns (we use PostgreSQL)

4. Understand current response format

5. Check API documentation standards

Report your findings."
```

```
Claude: "I've explored the codebase:

1. **Current Implementation**

   - GET /api/users returns all users (no limit)

   - Query in src/controllers/userController.js

   - Currently 50 users, but table growing

2. **Existing Pagination**

   - Found pagination in /api/posts endpoint

   - Uses ?page=1&limit=20 query params

   - Returns metadata: {page, limit, total, totalPages}

3. **Database Setup**

   - PostgreSQL with Sequelize ORM

   - User model in src/models/User.js

   - Supports OFFSET and LIMIT

4. **Response Format**

   - Current: {users: [...]}

   - Posts endpoint: {data: [...], pagination: {...}}

5. **Standards**

   - API docs use OpenAPI 3.0

   - Query params documented in docs/api.md"
```

#### Planning Phase
```
User: "Good findings. Now create a detailed implementation plan following the existing pagination pattern from the posts endpoint."
```

```
Claude: "## Pagination Implementation Plan

### Approach
Mirror existing posts pagination for consistency:

- Query params: page (default 1), limit (default 20, max 100)

- Response format: {data: users[], pagination: {page, limit, total, totalPages}}

### Implementation Steps

**Step 1: Update Controller**
File: src/controllers/userController.js

- Extract page/limit from query params

- Add validation (page >= 1, limit between 1-100)

- Modify Sequelize query to use offset/limit

- Calculate total, totalPages

- Format response with pagination metadata

**Step 2: Update Route**
File: src/routes/users.js

- Add query param documentation in comments

- No code changes needed (controller handles it)

**Step 3: Update Tests**
File: tests/controllers/userController.test.js

- Test default pagination (page=1, limit=20)

- Test custom page/limit

- Test invalid params (page=0, limit=1000)

- Test pagination metadata accuracy

- Test empty results

**Step 4: Update API Documentation**
File: docs/api.md

- Document query parameters

- Add example requests/responses

- Note max limit of 100

**Step 5: Database Optimization** (Optional)
File: src/models/User.js

- Consider adding index on commonly sorted fields

- Test query performance with LIMIT/OFFSET

### Testing Strategy
- Unit tests for controller logic

- Integration tests for full endpoint

- Performance test with large dataset

- Edge cases (page beyond total, invalid params)

### Potential Challenges
1. **Large offsets slow**: Use cursor-based pagination later if needed

2. **Backward compatibility**: Keep old response format optional with ?paginated=false

3. **Inconsistent data**: Total count may change between requests

### Estimated Complexity
Low-Medium - 1-2 hours including tests"
```

#### Approval & Implementation
```
User: "Plan approved with one change: make default limit 50 instead of 20. Proceed with implementation."
```

```
Claude: "Updated plan with limit=50 default. Starting implementation...

✅ Step 1 Complete: Updated userController.js

- Added pagination logic

- Default page=1, limit=50, max=100

- Response includes pagination metadata

✅ Step 2 Complete: Updated route documentation

✅ Step 3 Complete: Added comprehensive tests

- All tests passing (12/12)

✅ Step 4 Complete: Updated API documentation

Ready for your review."
```

## Advanced: Using Subagents for Research

For complex tasks, ask Claude to use subagents:

```
"Please explore the codebase. For any unfamiliar patterns or libraries, use a subagent to research best practices. Report your findings before creating a plan."
```

## Common Mistakes to Avoid

### ❌ Mistake 1: Skipping Exploration
```
"Add feature X"  → Claude immediately codes → Wrong patterns used
```

**✅ Correct**:
```
"Add feature X. First explore [relevant areas], then plan, then code."
```

### ❌ Mistake 2: Vague Exploration Request
```
"Look around and figure out how to add feature X"
```

**✅ Correct**:
```
"Explore:

1. Read src/module.js

2. Find similar features

3. Check dependencies
Report findings before planning."
```

### ❌ Mistake 3: Planning Without Exploration
```
"Create a plan for feature X" → Claude guesses architecture
```

**✅ Correct**:
```
"First explore [areas], THEN create plan based on findings."
```

### ❌ Mistake 4: Approving Incomplete Plans
```
Claude: "Plan: 1. Add code 2. Test"
User: "Approved"  → Too vague
```

**✅ Correct**:
```
"Please expand the plan:

- Exact files to modify

- Step-by-step sequence

- Testing strategy

- Edge cases to handle"
```

## Success Criteria

After using this skill, you should have:

- [ ] Completed exploration phase (no code written yet)

- [ ] Reviewed Claude's findings for accuracy

- [ ] Received detailed implementation plan

- [ ] Reviewed and approved (or modified) the plan

- [ ] Authorized implementation to proceed

- [ ] Verified final implementation matches plan

- [ ] All tests passing

- [ ] Documentation updated

## Workflow Templates

### Template 1: Feature Addition
```
"I need to add [feature].

Do NOT code yet. First:

1. Explore: [relevant files/areas]

2. Identify: existing patterns

3. Map: affected components

4. Report: findings

Then create detailed plan."
```

### Template 2: Bug Fix
```
"I need to fix [bug description].

Do NOT fix yet. First:

1. Reproduce: the bug

2. Investigate: root cause

3. Analyze: affected areas

4. Report: findings

Then create fix plan with testing strategy."
```

### Template 3: Refactoring
```
"I want to refactor [code area] to [goal].

Do NOT refactor yet. First:

1. Analyze: current implementation

2. Identify: dependencies and usage

3. Research: best practices for [goal]

4. Report: findings

Then create refactoring plan with safety measures."
```

## Integration with Other Skills

**Combine with**:

- `test-driven-development`: Plan includes tests-first approach

- `code-review-quality`: Review plan before implementation

- `create-claude-md`: Document planning requirements in CLAUDE.md

**Before Using**:

- `create-claude-md`: Establish project standards

- `setup-[language]-system-prompt`: Configure environment

**After Using**:

- `code-review-quality`: Review implemented code

- `generate-test-cases`: Add comprehensive tests

## Measuring Success

Track these metrics to validate the workflow:

**Before Plan-Before-Code**:

- Average iterations to complete task: 3-5

- Code review issues: High

- Bugs in implementation: Medium-High

- Time to first working version: Longer

- Context thrashing: High

**After Plan-Before-Code**:

- Average iterations to complete task: 1-2 ✅

- Code review issues: Low ✅

- Bugs in implementation: Low ✅

- Time to first working version: Shorter ✅

- Context thrashing: Low ✅

## Why Anthropic Recommends This

From Anthropic's research:

> "Asking Claude to research and plan first significantly improves performance for problems requiring deeper thinking upfront. Without explicit planning instructions, Claude tends to jump straight to coding a solution."

**Key Finding**: The planning step takes 5-10 minutes but saves 30-60 minutes of iteration and debugging.

## Additional Resources

- [Claude Code Best Practices - Anthropic](https://www.anthropic.com/engineering/claude-code-best-practices)

- [Plan-Then-Execute Pattern](https://docs.claude.com/en/docs/claude-code/common-workflows)

- [Research on AI Planning Performance](https://www.anthropic.com/research/planning-in-ai-systems)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: Anthropic Claude Code Best Practices 2025
**Priority**: 🔥 CRITICAL - Use for all non-trivial implementations
