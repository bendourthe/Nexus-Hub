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
