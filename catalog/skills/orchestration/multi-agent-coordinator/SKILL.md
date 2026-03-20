---
name: multi-agent-coordinator
description: Coordinate concurrent subagent execution with clear role separation, dependency tracking, and result integration. Use when a task benefits from parallel delegation to specialized agents, needs explicit write-scope ownership to prevent conflicts, or requires structured reconciliation of multiple agent outputs.
---

# Multi-Agent Coordinator

Specialized expertise in decomposing complex tasks into parallel and sequential work streams, delegating each stream to a purpose-built subagent with an explicit write scope, and reconciling the outputs into a verified, integrated result. This skill operationalizes Claude Code's Agent tool for real multi-agent coordination rather than simple serial delegation.

## When to Use This Skill

Use this skill for:

- Tasks where two or more independent work streams can execute in parallel (e.g., backend API + frontend UI + test scaffolding)
- Situations where context isolation is required because total context exceeds a single agent's effective window
- Work that benefits from specialized reviewers running concurrently with implementers (security review, code review, documentation)
- Large refactors or migrations where disjoint file sets can be modified simultaneously without merge conflicts
- Any scenario where you need to prevent two agents from editing the same file at the same time

**Do NOT use this skill when**:

- The task is small enough for a single agent to hold all context (multi-agent adds 5-15x token overhead)
- All subtasks are strictly sequential with no parallelism opportunity
- The codebase has tight coupling that makes disjoint write scopes impossible

**Trigger phrases**: "multi-agent", "parallel agents", "delegate to agents", "concurrent execution", "agent coordination", "split across agents", "subagent", "write scope", "agent conflict", "parallel delegation"

## What This Skill Does

Provides a complete coordination framework including:

- **Task Graph Analysis**: Mapping critical-path work vs parallel sidecar opportunities
- **Role Assignment**: Matching subtasks to specialized agent types with explicit capabilities
- **Write-Scope Ownership**: Ensuring each agent owns a disjoint set of files to prevent conflicts
- **Dependency Tracking**: Defining wait points and integration edges between agent outputs
- **Parallel Execution**: Launching independent agents concurrently via Claude Code's Agent tool
- **Result Reconciliation**: Merging outputs, resolving overlapping concerns, and validating the integrated result
- **Failure Handling**: Fallback strategies for partial results, agent failures, and escalation

## Instructions

### Step 1: Analyze and Decompose the Task Graph

Before launching any agents, map the full task into a dependency graph. The goal is to identify the critical path (the longest sequential chain) and all opportunities for parallel sidecar work.

**Discovery Questions**:

1. What are the distinct deliverables?
2. Which deliverables share files or state?
3. What is the minimum sequential chain (critical path)?
4. Which work items have zero dependencies on each other?
5. What is the total context size, and does it exceed a single agent's effective window?

**Decision Matrix: Delegate vs Handle Locally**:

| Factor | Handle Locally | Delegate to Subagent |
|--------|---------------|---------------------|
| Context fits in current window | Yes | Overkill |
| Work is on the critical path with tight coupling | Yes | Risk of stale context |
| Work is independent with disjoint files | Possible but slow | Ideal for parallel execution |
| Work requires specialized review (security, perf) | If you have expertise | Better to delegate to focused reviewer |
| Total remaining work exceeds 30 minutes of sequential effort | Consider splitting | Strong candidate for delegation |

**Task Graph Template**:

```markdown
## Task Graph: [Feature/Task Name]

### Critical Path (sequential, blocking)
1. [Task A] - Foundation work, must complete first
2. [Task D] - Depends on A, blocks final integration
3. [Task F] - Final integration, depends on all parallel streams

### Parallel Stream 1 (after Task A completes)
- [Task B] - Backend implementation
- Files: src/api/, src/models/

### Parallel Stream 2 (after Task A completes)
- [Task C] - Frontend implementation
- Files: src/components/, src/hooks/

### Parallel Stream 3 (independent, can start immediately)
- [Task E] - Test scaffolding and documentation
- Files: tests/, docs/

### Dependency Edges
- Task B depends on: Task A
- Task C depends on: Task A
- Task D depends on: Task B, Task C
- Task E depends on: nothing (fully independent)
- Task F depends on: Task D, Task E
```

**Visualization**:

```
         ┌──────────┐
         │  Task A   │  (Foundation, critical path)
         └─────┬─────┘
       ┌───────┼───────────────┐
       │       │               │
  ┌────▼────┐ ┌▼──────────┐ ┌─▼───────┐
  │ Task B  │ │  Task C    │ │ Task E  │  (Parallel streams)
  │ Backend │ │  Frontend  │ │ Tests   │
  └────┬────┘ └─────┬──────┘ └────┬────┘
       │            │              │
       └──────┬─────┘              │
         ┌────▼────┐               │
         │ Task D  │  (Integration)│
         └────┬────┘               │
              └──────────┬─────────┘
                    ┌────▼────┐
                    │ Task F  │  (Final verification)
                    └─────────┘
```

### Step 2: Design Role Assignments and Write Scopes

Each subagent must have a clear role, a defined set of files it is allowed to modify, and a contract specifying what it must return.

**Agent Role Catalog**:

| Role | Purpose | Typical Write Scope | Output Contract |
|------|---------|-------------------|-----------------|
| **Explore** | Read-only investigation, gather context | None (read-only) | Structured findings document |
| **Implement** | Write code for a specific module | Specific source directories | Modified files + summary of changes |
| **Loop-Operator** | Run tests iteratively until passing | Test files + source files in scope | All tests green + iteration count |
| **Code-Reviewer** | Review changes for quality | None (read-only) | List of issues with severity and line numbers |
| **Security-Reviewer** | Audit for vulnerabilities | None (read-only) | Security findings with risk ratings |
| **Doc-Writer** | Create or update documentation | docs/, README files | Updated documentation files |
| **Test-Writer** | Write test cases | tests/ directory only | New test files + coverage report |

**Write-Scope Rules** (critical for conflict prevention):

1. **Disjoint ownership**: No two agents may have overlapping write scopes. If Agent A owns `src/api/`, no other agent may modify files in `src/api/`.
2. **Read access is universal**: Any agent can read any file. Only writes are scoped.
3. **Shared files require sequencing**: If two agents must modify the same file (e.g., `package.json`), they must run sequentially, not in parallel.
4. **Scope declaration is mandatory**: Every agent prompt must explicitly list the files or directories the agent is allowed to modify.

**Role Assignment Template**:

```markdown
## Agent Assignments

### Agent 1: Backend Implementer
- **Role**: Implement
- **Write scope**: src/api/, src/models/, src/services/
- **Read access**: Entire codebase
- **Output contract**: All API endpoints implemented, passing type checks
- **Dependencies**: Waits for Task A (schema design)

### Agent 2: Frontend Implementer
- **Role**: Implement
- **Write scope**: src/components/, src/hooks/, src/pages/
- **Read access**: Entire codebase + Agent 1's API contracts
- **Output contract**: All UI components rendering, connected to API types
- **Dependencies**: Waits for Task A (schema design)

### Agent 3: Test Writer
- **Role**: Test-Writer
- **Write scope**: tests/unit/, tests/integration/
- **Read access**: Entire codebase
- **Output contract**: Test scaffolding with mocks, ready for implementation details
- **Dependencies**: None (can start immediately with interface contracts)

### Agent 4: Security Reviewer
- **Role**: Security-Reviewer
- **Write scope**: None (read-only)
- **Read access**: Entire codebase
- **Output contract**: Security findings document with risk ratings
- **Dependencies**: Runs after Agents 1 and 2 complete
```

### Step 3: Define Dependency and Integration Points

Map the edges between agent tasks to determine launch order and wait points.

**Dependency Types in Multi-Agent Context**:

| Type | Description | Handling Strategy |
|------|-------------|-------------------|
| **Data dependency** | Agent B needs Agent A's output | Launch B after A completes; pass A's output in B's prompt |
| **Interface dependency** | Agent B needs to know A's API shape | Define interface up front; both agents code to the contract |
| **File dependency** | Both agents need to modify the same file | Sequence the agents; second agent reads first agent's changes |
| **Verification dependency** | Reviewer agent needs implementer output | Launch reviewer after implementer; pass diff as context |

**Wait Point Design**:

```markdown
## Integration Points

### Wait Point 1: Schema Complete
- **Trigger**: Agent handling Task A reports completion
- **Unblocks**: Agent 1 (Backend), Agent 2 (Frontend)
- **Data passed**: Schema definitions, API contracts

### Wait Point 2: Implementation Complete
- **Trigger**: Both Agent 1 and Agent 2 report completion
- **Unblocks**: Agent 4 (Security Review), Integration testing
- **Data passed**: File change summaries, new file paths

### Wait Point 3: All Reviews Complete
- **Trigger**: Agent 4 reports completion
- **Unblocks**: Final integration and verification
- **Data passed**: Review findings, required fixes
```

**Handling Partial or Uncertain Results**:

When an agent returns incomplete work, apply this decision framework:

| Situation | Action |
|-----------|--------|
| Agent completed 80%+ of its scope | Accept output, handle remaining items locally |
| Agent completed <80% but identified clear blockers | Re-delegate with refined prompt addressing blockers |
| Agent returned conflicting or incorrect results | Discard output, investigate root cause, re-delegate or handle locally |
| Agent timed out with no output | Check if the task was too large; decompose further and retry |

### Step 4: Execute the Multi-Agent Plan

Use Claude Code's Agent tool to launch subagents. The key patterns are parallel launch for independent work and sequential launch for dependent work.

**Pattern A: Parallel Launch for Independent Agents**

When agents have no dependencies on each other, launch them in the same tool-call block so they execute concurrently:

```markdown
## Execution Plan: Parallel Phase

Launch the following agents simultaneously (no dependencies between them):

[Agent Tool Call 1 - Backend Implementer]
Prompt: "You are a backend implementer. Your write scope is limited to:
- src/api/
- src/models/
- src/services/

DO NOT modify any files outside this scope.

Task: Implement the REST API endpoints for the user management feature.
Schema contract: [paste schema definitions here]
Existing patterns: Read src/api/existing-endpoint.ts for the established pattern.

Return: A summary of all files created or modified, and confirmation that type checks pass."

[Agent Tool Call 2 - Frontend Implementer]
Prompt: "You are a frontend implementer. Your write scope is limited to:
- src/components/
- src/hooks/
- src/pages/

DO NOT modify any files outside this scope.

Task: Implement the UI components for the user management feature.
API contract: [paste API type definitions here]
Design spec: [paste or reference design requirements]

Return: A summary of all files created or modified, and confirmation that components render without errors."

[Agent Tool Call 3 - Test Scaffolding]
Prompt: "You are a test writer. Your write scope is limited to:
- tests/unit/
- tests/integration/

DO NOT modify any files outside this scope.

Task: Create test scaffolding for the user management feature.
Interfaces: [paste interface contracts]

Return: A summary of all test files created, with placeholder test cases ready for implementation details."
```

**Pattern B: Sequential Launch for Dependent Agents**

When Agent B depends on Agent A's output, launch them in sequence:

```markdown
## Execution Plan: Sequential Phase

Step 1: Launch foundation agent and wait for completion.

[Agent Tool Call - Schema Designer]
Prompt: "Design the database schema and API contracts for the user management feature.
Requirements: [paste requirements]
Return: Schema SQL, TypeScript type definitions, and API route contracts."

Step 2: Read the schema agent's output, then launch parallel implementers (Pattern A above).

Step 3: After implementers complete, launch reviewer.

[Agent Tool Call - Security Reviewer]
Prompt: "You are a security reviewer. You have READ-ONLY access. Do not modify any files.

Review the following changes for security vulnerabilities:
- Files changed: [list from implementer outputs]
- Feature: User management with authentication

Check for: SQL injection, XSS, CSRF, authentication bypass, authorization flaws,
sensitive data exposure, and insecure defaults.

Return: A structured findings document with severity ratings (Critical/High/Medium/Low)
and specific line references for each issue."
```

**Pattern C: Background Agents for Truly Independent Work**

For work that does not block anything else and whose results are needed only at the end:

```markdown
## Execution Plan: Background Work

Launch documentation agent in the background while critical-path work proceeds:

[Agent Tool Call - Doc Writer (background)]
Prompt: "You are a documentation writer. Your write scope is limited to:
- docs/api/
- docs/guides/

Task: Write API documentation for the user management feature based on these contracts:
[paste API contracts]

Return: Updated documentation files with endpoint descriptions, request/response examples,
and error code tables."
```

**Context Provision Checklist**:

Every agent starts with a fresh context. You must provide:

- [ ] Clear role statement ("You are a...")
- [ ] Explicit write scope with DO NOT MODIFY warning
- [ ] All necessary context (schemas, contracts, patterns) pasted directly into the prompt
- [ ] File paths to read for additional context
- [ ] Expected output format and contract
- [ ] Any project conventions (naming, error handling patterns, test frameworks)

### Step 5: Reconcile and Integrate Results

After parallel agents complete, their outputs must be merged and validated.

**Reconciliation Checklist**:

```markdown
## Result Reconciliation

### Agent Outputs Received
- [ ] Agent 1 (Backend): [Status: Complete/Partial] - [Summary]
- [ ] Agent 2 (Frontend): [Status: Complete/Partial] - [Summary]
- [ ] Agent 3 (Tests): [Status: Complete/Partial] - [Summary]

### Conflict Detection
- [ ] No two agents modified the same file
- [ ] Import paths are consistent across agent outputs
- [ ] Shared type definitions match between backend and frontend
- [ ] API contracts implemented by backend match what frontend consumes
- [ ] No duplicate function or variable names introduced across scopes

### Integration Actions
1. [ ] Verify all agent-created files are present and syntactically valid
2. [ ] Run the full type checker across the combined codebase
3. [ ] Run the test suite to catch integration issues
4. [ ] Resolve any type mismatches between agent outputs
5. [ ] Update shared configuration files (package.json, tsconfig.json) if needed

### Conflict Resolution Strategies
| Conflict Type | Resolution |
|---------------|------------|
| Type mismatch between agents | Use the API contract as source of truth; fix the divergent agent's output |
| Duplicate utility functions | Keep the more complete version; update imports in the other agent's files |
| Inconsistent naming | Apply project conventions; rename to match established patterns |
| Overlapping test coverage | Merge non-redundant tests; remove duplicates |
```

**Integration Merge Template**:

```markdown
## Integration Summary

### Files Created (total: N)
- Agent 1: [list files]
- Agent 2: [list files]
- Agent 3: [list files]

### Files Modified (total: N)
- Agent 1: [list files with change summary]
- Agent 2: [list files with change summary]

### Integration Fixes Applied
1. [Fix description] - Reason: [type mismatch / naming inconsistency / etc.]
2. [Fix description] - Reason: [...]

### Validation Results
- Type checker: [Pass/Fail with details]
- Test suite: [X passed, Y failed, Z skipped]
- Lint: [Pass/Fail with details]
```

### Step 6: Handle Failures and Contingencies

Agents can fail, return partial results, or produce incorrect output. Plan for these scenarios.

**Failure Classification and Response**:

| Failure Mode | Symptoms | Response |
|--------------|----------|----------|
| **Agent timeout** | No output returned | Task was too large; decompose into smaller pieces and re-delegate |
| **Partial completion** | Output covers 50-80% of scope | Accept partial output; complete remaining work locally or re-delegate the gap |
| **Incorrect output** | Code does not compile, fails tests, or violates conventions | Analyze root cause; refine prompt with explicit corrections and re-delegate |
| **Scope violation** | Agent modified files outside its write scope | Revert out-of-scope changes; re-delegate with stronger scope warnings |
| **Conflicting outputs** | Two agents produced incompatible implementations | Use the API contract as arbiter; fix the divergent output |

**Re-delegation Strategy**:

When re-delegating after a failure, always include:

1. The original task description
2. What the previous agent attempted and where it went wrong
3. Specific corrections or constraints to prevent the same failure
4. A narrower scope if the original was too broad

```markdown
## Re-delegation Prompt Template

"You are a [role]. A previous agent attempted this task but [describe failure].

Your corrected task:
- [Refined task description]
- [Specific constraints addressing the previous failure]

Previous agent's output (for context, do not build on this):
- [Summary of what was produced]
- [Specific errors or issues]

Your write scope: [explicit file list]
Expected output: [contract]"
```

**Escalation Criteria**:

Escalate to the user (do not attempt further re-delegation) when:

- The same agent has failed 2+ times on the same task
- The failure indicates an ambiguous requirement that needs human clarification
- The task requires access to systems or credentials the agent cannot reach
- The risk of further automated attempts outweighs the cost of human intervention
- File conflicts cannot be resolved without architectural decisions

### Step 7: Quality Gates and Verification

After all agents complete and outputs are reconciled, run a structured verification pass.

**Post-Integration Verification Checklist**:

```markdown
## Post-Integration Quality Gate

### Build Verification
- [ ] Project compiles without errors
- [ ] No new type errors introduced
- [ ] No new lint warnings introduced

### Test Verification
- [ ] All existing tests still pass (no regressions)
- [ ] New tests written by test agent pass
- [ ] Integration tests pass with real (not mocked) connections where applicable
- [ ] Test coverage meets project threshold

### Functional Verification
- [ ] Each acceptance criterion from the original requirements is met
- [ ] Edge cases identified during planning are handled
- [ ] Error paths return appropriate messages

### Security Verification (if security reviewer was used)
- [ ] All Critical and High findings from security review are addressed
- [ ] Medium findings are documented with planned remediation dates
- [ ] No secrets, tokens, or credentials in committed code

### Documentation Verification
- [ ] API documentation matches actual implementation
- [ ] Code comments explain non-obvious decisions
- [ ] Architecture decisions are documented

### Delegation Audit Trail
- [ ] Record which agent handled each subtask
- [ ] Note any re-delegations and their causes
- [ ] Document residual items that were completed locally vs by agents
- [ ] Calculate total agent invocations for cost awareness
```

**Delegation Audit Template**:

```markdown
## Delegation Audit: [Feature/Task Name]

### Agent Invocations
| # | Agent Role | Task | Status | Re-delegated? | Notes |
|---|-----------|------|--------|---------------|-------|
| 1 | Schema Designer | Design DB schema | Complete | No | |
| 2 | Backend Implementer | REST API endpoints | Complete | No | |
| 3 | Frontend Implementer | UI components | Partial | Yes (1x) | Initial prompt lacked design spec |
| 4 | Test Writer | Test scaffolding | Complete | No | |
| 5 | Security Reviewer | Security audit | Complete | No | Found 1 Medium issue |
| 6 | Frontend Implementer (retry) | UI components | Complete | No | Added design spec to prompt |

### Cost Summary
- Total agent invocations: 6
- Re-delegations: 1
- Parallel phases: 2 (Agents 2+3+4 ran concurrently; Agent 5 ran after)
- Estimated token multiplier: ~8x single-agent baseline

### Residual Risk
- [ ] Medium security finding (input sanitization on search endpoint) tracked in issue #NNN
- [ ] Frontend accessibility testing not yet performed (out of scope for this delegation)
```

## Risk Assessment Matrix

Use this matrix to evaluate whether multi-agent coordination is appropriate for a given task:

| Risk Factor | Low Risk | Medium Risk | High Risk |
|-------------|----------|-------------|-----------|
| **File overlap** | Agents touch completely disjoint files | Agents share config files (package.json) | Agents need to modify the same source files |
| **Interface coupling** | Well-defined API contracts exist | Contracts exist but may change during implementation | No contracts; agents must discover interfaces |
| **Task clarity** | Requirements are unambiguous | Some requirements need interpretation | Requirements are vague or contradictory |
| **Codebase familiarity** | Established patterns, agents can read examples | Some patterns exist, some new ground | Greenfield with no established patterns |
| **Rollback cost** | Git makes reverting easy | Partial rollback is complex (DB migrations) | Changes are irreversible (data mutations, external APIs) |

**Risk-based approach**:

- **All Low**: Proceed with full parallel delegation
- **Any Medium**: Add explicit interface contracts before delegating; prefer sequential over parallel for coupled agents
- **Any High**: Reduce parallelism; consider handling the high-risk portion locally while delegating low-risk sidecars

## Best Practices

- **Start with contracts** - Define API types, schemas, and interface boundaries before delegating implementation to any agent
- **Scope narrowly** - Each agent should own 3-10 files, not entire subsystems
- **Paste, do not reference** - Agents start fresh; paste critical context directly into prompts rather than asking agents to "read the project structure"
- **One role per agent** - An agent that implements AND reviews its own code provides no quality benefit; separate the roles
- **Verify after every merge** - Run the type checker and test suite after integrating each agent's output, not just at the end
- **Track token cost** - Multi-agent coordination costs 5-15x a single agent; ensure the parallelism benefit justifies the cost
- **Fail fast** - If an agent's first output shows fundamental misunderstanding, refine the prompt immediately rather than hoping it improves
- **Keep the coordinator lean** - The coordinating agent (you) should focus on decomposition, delegation, and reconciliation, not implementation

## Common Anti-Patterns

| Anti-Pattern | Problem | Correction |
|-------------|---------|------------|
| Delegating everything | Token cost explodes; coordination overhead exceeds implementation effort | Handle simple tasks locally; delegate only when parallelism or specialization adds value |
| Overlapping write scopes | Two agents edit the same file, creating merge conflicts | Enforce disjoint write scopes; sequence agents that must share files |
| Vague agent prompts | Agents guess at requirements, producing incorrect output | Provide explicit contracts, file paths, and examples in every prompt |
| No verification between phases | Errors compound across agent handoffs | Run type checks and tests after each integration point |
| Re-delegating without refinement | Same failure repeats because the prompt did not change | Always add corrective context to re-delegation prompts |
| Ignoring token economics | 10 agents for a task one agent could handle | Apply the decision matrix from Step 1 honestly |

## Integration with Other Skills

Invoke related skills at the appropriate coordination phase:

| Phase | Related Skills |
|-------|---------------|
| Task decomposition | `task-coordinator`, `plan-before-code` |
| Agent prompt construction | `context-analysis`, `context-manager` |
| Implementation agents | Language-specific skills, `code-quality` |
| Review agents | `code-reviewer`, `security-review`, `dependency-security-audit` |
| Test agents | `unit-tests`, `test-cases`, `performance-testing` |
| Documentation agents | `technical-documentation`, `api-documentation` |
| Verification | `loop-operator` (iterative test fixing) |

## Quality Checklist

- [ ] Task graph identifies critical path and all parallel opportunities
- [ ] Every agent has a defined role, disjoint write scope, and output contract
- [ ] Dependencies between agents are explicitly mapped with wait points
- [ ] Agent prompts include all necessary context (not just file references)
- [ ] Reconciliation plan exists for merging parallel outputs
- [ ] Failure handling and re-delegation strategy is defined
- [ ] Post-integration verification covers build, tests, and security
- [ ] Delegation audit trail is documented for cost tracking

## Related Skills

- `task-coordinator` - General task decomposition and dependency management
- `plan-before-code` - Upfront planning methodology
- `context-manager` - Managing information across agent boundaries
- `workflow-orchestrator` - End-to-end workflow management
- `code-quality` - Quality standards for agent-produced implementations

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: awesome-codex-subagents multi-agent-coordinator, Claude Code Agent tool patterns
**Attribution**: Multi-agent patterns adapted from [awesome-codex-subagents](https://github.com/QuantGeekDev/awesome-codex-subagents) and [Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) (MIT License)


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets are not met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
