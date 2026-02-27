---
name: context-manager
description: Manage and maintain context across large codebases and complex multi-file changes. Covers context fundamentals (attention budget, progressive disclosure, compaction triggers) and practical techniques for navigating unfamiliar codebases and synthesizing information from multiple sources.
---

# Context Manager

Specialized expertise in managing information and maintaining context across large codebases, ensuring consistent understanding when working on changes that span multiple files, components, or systems.

## When to Use This Skill

Use this skill for:

- Working on changes that affect many files
- Navigating unfamiliar or large codebases
- Maintaining consistency across related changes
- Synthesizing information from multiple sources
- Tracking relationships between components
- Ensuring changes don't break existing functionality

**Trigger phrases**: "maintain context", "large codebase", "cross-file changes", "related files", "track dependencies", "understand codebase", "consistent changes", "attention budget", "context window", "progressive disclosure"

## What This Skill Does

Provides context management capabilities including:

- **Information Synthesis**: Combining knowledge from multiple files
- **Dependency Tracking**: Understanding component relationships
- **Change Impact Analysis**: Predicting ripple effects
- **Consistency Verification**: Ensuring related changes align
- **Knowledge Persistence**: Maintaining understanding across sessions
- **Navigation Optimization**: Efficiently exploring large codebases

## Instructions

### Step 0: Understand Context Fundamentals

Before managing context, understand what competes for an AI model's limited attention window. Every token loaded into context displaces something else; the goal is the **smallest possible set of high-signal tokens** for the task at hand.

**The Five Context Components**:

| Component | What It Contains | Typical Budget | Optimization Lever |
|-----------|-----------------|----------------|-------------------|
| **System Prompts** | Instructions, role definitions, CLAUDE.md | 5-15% | Keep concise; load rules on demand |
| **Tool Definitions** | MCP tool schemas, function signatures | 5-10% | Limit to 10-20 active tools; namespace larger sets |
| **Retrieved Documents** | Files, search results, RAG outputs | 20-40% | Retrieve only what the current step needs |
| **Message History** | Prior conversation turns | 20-40% | Summarize older turns; compress at thresholds |
| **Tool Outputs** | Command results, API responses, file reads | 10-30% | Mask verbose outputs; write large results to files |

**Key Principles**:

1. **Attention Budget**: Models develop attention patterns from training data where shorter sequences predominate. Information buried in the middle of long contexts receives 10-40% lower recall (the "Lost-in-Middle" effect). Place important information at the beginning or end.

2. **Progressive Disclosure**: Load information incrementally based on what the current step requires, not everything that might be useful. This keeps the attention budget focused on high-signal tokens.

3. **Compaction Trigger**: Monitor context utilization. At **70-80% capacity**, begin proactive summarization of older conversation history and tool outputs. Waiting until the context window is full leads to abrupt quality degradation.

4. **Quality Over Quantity**: Larger context windows do not solve context quality problems. A focused 50K-token context outperforms a cluttered 200K-token context for most tasks. Curate aggressively.

**When to Apply These Fundamentals**:
- Long-running sessions (>20 turns)
- Multi-file explorations that generate large tool outputs
- Tasks requiring synthesis across many sources
- Sessions where the agent starts "forgetting" earlier instructions

### Step 1: Build Initial Context Map

**Context Discovery Process**:

```markdown
## Context Map: [Feature/Area]

### Core Components
| Component | Purpose | Key Files | Dependencies |
|-----------|---------|-----------|--------------|
| [Name] | [Description] | [Paths] | [List] |

### Data Flow
```
[Source] → [Transform] → [Store] → [Display]
    │           │           │          │
    ▼           ▼           ▼          ▼
[File A]    [File B]    [File C]   [File D]
```

### Key Interfaces
- Interface 1: [Description]
  - Defined in: [file]
  - Implemented by: [files]
  - Used by: [files]

### Configuration Points
- [Config 1]: [file] - [purpose]
- [Config 2]: [file] - [purpose]

### External Dependencies
- [Dependency]: [version] - [usage]
```

### Step 2: Track File Relationships

**Relationship Types**:

| Relationship | Description | Example |
|--------------|-------------|---------|
| **Imports** | Direct code dependency | `import { fn } from './util'` |
| **Implements** | Interface realization | `class X implements IY` |
| **Extends** | Inheritance | `class Child extends Parent` |
| **Calls** | Runtime dependency | API calls, event handlers |
| **Configures** | Configuration dependency | Config files, env vars |
| **Tests** | Test coverage | Test files for source |

**File Relationship Template**:

```markdown
## File: [path/to/file.ts]

### Identity
- **Purpose**: [Brief description]
- **Type**: Component | Service | Utility | Config | Test
- **Domain**: [Business domain]

### Dependencies (What this file needs)
```
Imports:
├── ../services/api.ts (ApiService)
├── ../utils/helpers.ts (formatDate, parseData)
├── ../types/models.ts (User, Order)
└── react (useState, useEffect)
```

### Dependents (What needs this file)
```
Used by:
├── ../pages/Dashboard.tsx
├── ../components/OrderList.tsx
└── ../tests/OrderService.test.ts
```

### Interfaces Exposed
- `OrderService` class
- `OrderStatus` enum
- `createOrder()` function

### Side Effects
- Writes to localStorage
- Makes API calls to /api/orders
- Dispatches Redux actions

### Change Impact
If modified, verify:
- [ ] Dashboard.tsx still works
- [ ] OrderList.tsx displays correctly
- [ ] Tests pass
```

### Step 3: Maintain Change Context

**Change Tracking Template**:

```markdown
## Change Set: [Description]

### Motivation
[Why this change is being made]

### Files Modified

#### Primary Changes
| File | Change Type | Description |
|------|-------------|-------------|
| [path] | Add/Modify/Delete | [What changed] |

#### Cascading Changes (required for consistency)
| File | Reason | Change |
|------|--------|--------|
| [path] | [dependency reason] | [What needs to change] |

### Consistency Checks

#### Naming Consistency
- [ ] Function names follow pattern: [pattern]
- [ ] Variable names follow pattern: [pattern]
- [ ] File names follow pattern: [pattern]

#### Interface Consistency
- [ ] All implementations updated
- [ ] Type definitions match
- [ ] Default values consistent

#### Behavior Consistency
- [ ] Error handling consistent
- [ ] Logging consistent
- [ ] Null handling consistent

### Verification Plan
1. [ ] Run affected tests
2. [ ] Verify imports resolve
3. [ ] Check TypeScript compilation
4. [ ] Manual verification of [specific flows]
```

### Step 4: Synthesize Cross-File Information

**Pattern Recognition Template**:

```markdown
## Pattern Analysis: [Pattern Name]

### Observed Instances
| Location | Implementation | Notes |
|----------|----------------|-------|
| [file:line] | [code snippet] | [variations] |

### Canonical Pattern
```[language]
// The standard way this pattern should be implemented
[code example]
```

### Deviations
| Location | Deviation | Reason | Action |
|----------|-----------|--------|--------|
| [file] | [difference] | [why] | Keep/Update |

### Recommendations
- [Recommendation 1]
- [Recommendation 2]
```

### Step 5: Handle Context Handoffs

**Context Summary Template** (for session boundaries):

```markdown
## Context Summary: [Task/Feature]
**Date**: [timestamp]
**Status**: In Progress | Blocked | Complete

### Current State
[Brief description of where things stand]

### Key Decisions Made
1. [Decision 1]: [Rationale]
2. [Decision 2]: [Rationale]

### Important Files
| File | Status | Notes |
|------|--------|-------|
| [path] | Modified/Needs work | [details] |

### Open Questions
- [ ] [Question 1]
- [ ] [Question 2]

### Next Steps
1. [Immediate next action]
2. [Following action]

### Things to Remember
- [Important context that might be forgotten]
- [Non-obvious relationships discovered]
- [Gotchas encountered]
```

### Step 6: Navigate Efficiently

**Codebase Navigation Strategy**:

```markdown
## Navigation Guide: [Codebase/Feature Area]

### Entry Points
- **Main entry**: [file] - Start here for [use case]
- **Config entry**: [file] - Start here for configuration
- **API entry**: [file] - Start here for API exploration

### Key Landmarks
| What | Where | Why Important |
|------|-------|---------------|
| [Feature] | [path pattern] | [significance] |

### Search Patterns
| Looking for | Search strategy |
|-------------|-----------------|
| Component usage | Grep: `<ComponentName` |
| Function calls | Grep: `functionName(` |
| Type usage | Grep: `: TypeName` |
| Config values | Grep: `CONFIG.keyName` |

### Common Paths
```
Feature X workflow:
[entry] → [processing] → [storage] → [display]

Request lifecycle:
[route] → [controller] → [service] → [repository]
```

### Quick References
- Types/interfaces: `src/types/`
- Utilities: `src/utils/`
- Constants: `src/constants/`
- Tests: `**/*.test.ts`
```

## Best Practices

- **Map before modifying** - Understand relationships first
- **Document discoveries** - Record non-obvious findings
- **Track ripple effects** - Changes often cascade
- **Verify consistency** - Check related code matches
- **Use search effectively** - Grep/find for relationships
- **Build incrementally** - Start narrow, expand as needed
- **Note patterns** - Recognize and follow conventions
- **Summarize often** - Capture context before it fades

## Common Patterns

### Pattern 1: Feature Boundary Mapping

When starting on a feature, map its boundaries:

```markdown
## Feature: User Authentication

### Boundary Map
```
                    ┌─────────────────────────────────────┐
                    │         Authentication Feature       │
                    │                                     │
  Entry Points:     │  ┌─────────────┐                    │
  ─────────────►    │  │ LoginPage   │                    │
                    │  └──────┬──────┘                    │
                    │         │                           │
                    │  ┌──────▼──────┐   ┌─────────────┐  │
                    │  │ AuthService │───│ TokenStore  │  │
                    │  └──────┬──────┘   └─────────────┘  │
                    │         │                           │
  External:         │  ┌──────▼──────┐                    │
  ◄────────────     │  │  Auth API   │                    │
                    │  └─────────────┘                    │
                    │                                     │
                    └─────────────────────────────────────┘

Internal files: [list]
External dependencies: [list]
```

### Pattern 2: Change Impact Matrix

For significant changes, build an impact matrix:

```markdown
## Change Impact: Renaming `userId` to `accountId`

### Impact Matrix
| File | Direct Change | Indirect Impact | Test Impact |
|------|---------------|-----------------|-------------|
| User.ts | ✓ Property rename | - | Update mocks |
| UserService.ts | ✓ References | API contract | Update tests |
| UserController.ts | ✓ Parameters | Route handling | Integration tests |
| UserRepository.ts | ✓ Queries | DB compatibility | Update fixtures |
| user.test.ts | ✓ Test updates | - | - |

### Risk Assessment
- High: Database migration needed
- Medium: API backward compatibility
- Low: Internal code changes
```

### Pattern 3: Cross-Cutting Concern Tracking

For concerns that span multiple areas:

```markdown
## Cross-Cutting: Error Handling

### Implementations Inventory
| Layer | Implementation | File | Pattern |
|-------|----------------|------|---------|
| API | try/catch + response | api/*.ts | ErrorResponse |
| Service | throw custom errors | services/*.ts | AppError |
| UI | Error boundary | components/ErrorBoundary.tsx | React boundary |
| Logging | Winston logger | utils/logger.ts | Structured logs |

### Consistency Status
- [x] All API routes wrapped
- [x] Custom error classes used
- [ ] Error boundary covers all routes (3 missing)
- [ ] Logging consistent (varies by module)

### Recommended Actions
1. Add ErrorBoundary to routes: X, Y, Z
2. Standardize logging format
```

## Quality Checklist

- [ ] Initial context map created
- [ ] File relationships documented
- [ ] Change set tracked
- [ ] Consistency checks defined
- [ ] Impact analysis completed
- [ ] Context summary prepared
- [ ] Navigation paths documented
- [ ] Handoff notes ready

## Related Skills

- `task-coordinator` - Breaking down coordinated work
- `plan-before-code` - Initial exploration and planning
- `context-analysis` - Deep codebase analysis
- `workflow-orchestrator` - Managing complete workflows

---

**Version**: 1.1.0
**Last Updated**: February 2026
**Based on**: awesome-claude-code-subagents patterns, software architecture practices
**Attribution**: Context fundamentals adapted from [Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) (MIT License)


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
