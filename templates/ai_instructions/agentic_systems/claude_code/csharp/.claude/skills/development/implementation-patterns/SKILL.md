---
name: implementation-patterns
description: Common interaction patterns and response structures for code fix requests, project planning, and code reviews. Includes decision trees for import organization, error handling, function structure, and testing strategy. Use when responding to coding requests or making implementation decisions.
---

# Implementation Patterns

## Common Interaction Patterns

### Standard Code Fix Request

**User Request:**
```
"Can you fix this function?"
[Code paste]
```

**Response Structure:**

1. **Analysis and Clarification** (if needed)
   ```
   I can see the function has [specific issues]. Before fixing it,
   I need to clarify [specific questions about requirements/context].
   ```

2. **Solution Implementation**
   ```python
   # Fixed version with improvements
   def improved_function(parameters):
       """Clear docstring explaining functionality."""
       # Implementation with best practices
       return result
   ```

3. **Explanation and Teaching**
   ```
   **Key Improvements Made:**
   - [Specific improvement 1 with reasoning]
   - [Specific improvement 2 with reasoning]

   **Why These Changes Work:**
   - [Educational explanation of concepts]
   - [References to Python best practices]
   ```

4. **Integration Instructions**
   ```
   **To Apply This Fix:**
   - Replace lines X-Y in your original function
   - Add the import statement at the top of your file
   - Test with [suggested test cases]
   ```

### Project Planning Request

**User Request:**
```
"I want to build a [complex application]"
```

**Response Structure:**

1. **Project Analysis**
   - Break down into main components
   - Identify technical challenges
   - Estimate complexity and timeline

2. **Architecture Recommendation**
   - Suggest standard project structure
   - Recommend technology stack
   - Propose development approach

3. **Subtask Breakdown**
   - Sequential, manageable tasks
   - Clear deliverables for each phase
   - Copy-pasteable prompts for execution

4. **Implementation Guidance**
   - Specific next steps
   - Quality checkpoints
   - Testing and validation approach

### Code Review and Enhancement

**User Request:**
```
"Please review this code for improvements"
[Code paste]
```

**Response Structure:**

1. **Current Code Assessment**
   - Identify strengths and positive aspects
   - Note areas needing improvement
   - Assess adherence to best practices

2. **Specific Improvement Recommendations**
   - Performance optimizations
   - Readability enhancements
   - Security considerations
   - Error handling improvements

3. **Enhanced Implementation**
   - Refactored code with improvements
   - Preserved original functionality
   - Added proper documentation

4. **Educational Context**
   - Explain why changes improve the code
   - Reference relevant Python concepts
   - Provide additional learning resources

## Decision Trees for Complex Scenarios

### Import Organization Decision Matrix

```
Question: Where should this import go?

Standard Library? → Section 1 (alphabetically)
│
├─ Third-Party? → Section 2 (grouped by function)
│  │
│  ├─ Data Science? → Group with numpy, pandas
│  ├─ Web Framework? → Group with flask, django
│  └─ Testing? → Group with pytest, unittest
│
└─ Local Module? → Section 3 (alphabetically)
   │
   ├─ Core Module? → from src.core import...
   ├─ Utilities? → from src.utils import...
   └─ Tests? → from tests import...
```

### Error Handling Strategy Selection

```
Question: How should I handle this error?

Recoverable Error?
├─ Yes → Use try/except with specific exception
│  │
│  ├─ Log and continue? → Use logging with continue
│  ├─ Retry possible? → Implement retry logic
│  └─ Default value? → Return safe default
│
└─ No → Let exception propagate
   │
   ├─ Add context? → Raise new exception with context
   ├─ Clean up needed? → Use try/finally
   └─ Critical error? → Log error and exit gracefully
```

### Function Structure Decision Guide

```
Question: How should I structure this function?

Single Responsibility?
├─ No → Break into smaller functions
│
├─ Yes → Check complexity
   │
   ├─ Simple (<10 lines)? → Keep as single function
   │
   └─ Complex (>10 lines)? → Consider helper functions
       │
       ├─ Repeated logic? → Extract to helper
       ├─ Multiple steps? → Extract each step
       └─ Complex algorithm? → Extract to private method
```

### Testing Strategy Decision Tree

```
Question: What testing approach should I use?

Unit Testing?
├─ Pure functions? → Simple assertions
├─ Dependencies? → Mock objects
├─ Database? → Test database
└─ API? → Mock responses

Integration Testing?
├─ Multiple components? → End-to-end
├─ Workflows? → Scenario tests
└─ Performance? → Load tests

Edge Cases?
├─ Boundaries? → Test limits
├─ Errors? → Test exceptions
└─ Concurrent? → Thread safety
```

### Code Style Decision Matrix

```
Question: Should I add a comment here?

Is the code self-explanatory?
├─ Yes → No comment needed
│
└─ No → What needs explanation?
       │
       ├─ Why this approach? → Add reasoning comment
       ├─ Complex algorithm? → Add algorithm explanation
       ├─ Non-obvious behavior? → Add behavior note
       └─ External dependency? → Add reference comment
```

### Refactoring Decision Guide

```
Question: Should I refactor this code?

Is there a bug to fix?
├─ Yes → Fix bug first, then consider refactoring
│
└─ No → Is refactoring requested?
       │
       ├─ Yes → Apply improvements
       │
       └─ No → Only refactor if:
              │
              ├─ Code is duplicated → Extract common logic
              ├─ Function is too long → Split into helpers
              ├─ Naming is unclear → Rename for clarity
              └─ Performance issue → Optimize critical path
```

## Response Templates

### Bug Fix Response
```markdown
## Analysis
[What's causing the issue]

## Solution
```python
[Fixed code]
```

## Changes Made
- [Change 1]: [Why]
- [Change 2]: [Why]

## Testing
```python
# Test this with:
[Test code]
```
```

### New Feature Response
```markdown
## Understanding
[Confirm understanding of requirements]

## Implementation Plan
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Code
```python
[Implementation]
```

## Next Steps
- [What user should do next]
```

### Code Review Response
```markdown
## Strengths
- [Positive aspect 1]
- [Positive aspect 2]

## Improvements Needed
- [Issue 1]: [Suggestion]
- [Issue 2]: [Suggestion]

## Refactored Code
```python
[Improved code]
```

## Key Learnings
- [Educational point 1]
- [Educational point 2]
```
