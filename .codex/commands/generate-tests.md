---
description: Perform a deep, comprehensive analysis of the entire codebase to generate extensive test coverage.
---
# Generate Tests Command

Perform a deep, comprehensive analysis of the entire codebase to generate extensive test coverage.

## Process

1.  **Deep Codebase Analysis**
    *   Scan the entire project structure to understand architecture and dependencies.
    *   Identify critical paths, complex algorithms, and data flow.
    *   Detect potential edge cases, race conditions, and error states.

2.  **Strategic Thinking Plan**
    *   Develop a testing strategy covering:
        *   **Unit Tests**: Isolated logic verification.
        *   **Feature Tests**: End-to-end user flows.
        *   **Optimization Tests**: Performance benchmarks and stress testing.
        *   **Edge Case Tests**: Boundary conditions, null inputs, network failures.

3.  **Test Generation**
    *   Generate test files using the project's native framework (pytest, Jest, JUnit, etc.).
    *   Ensure tests are self-contained and mocked where appropriate.
    *   Add comments explaining *why* a specific test case was chosen.

## Output

1.  **Test Suite**: The actual test code files.
2.  **Coverage Report**: An overview of what was covered and what issues were found during analysis.
3.  **Performance/Issue Insights**: A summary of potential bottlenecks or bugs discovered while writing tests.


## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Is it complete?
    *   Are there any obvious errors?
    *   Does it meet the user's requirements?
2.  **Refine**:
    *   Fix any issues found.
    *   Add missing components.
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.
