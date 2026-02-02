---
description: Analyze all units and generate a detailed plan to generate every single unit test possible for the entire codebase.
---

# Generate Unit Tests Command

This command performs a deep, comprehensive analysis of the codebase to generate an exhaustive suite of unit tests. It focuses on isolating units of code and covering all logic paths and edge cases.

## Process

1.  **Codebase Discovery & Analysis**
    *   Identify the project language (e.g., Python, JavaScript, C++).
    *   Identify the testing framework (e.g., pytest, Jest, JUnit).
    *   List all source files and identify the core logic files vs. infrastructure/config.
    *   Review existing tests to understand established patterns and helpers.

2.  **Comprehensive Unit Test Planning**
    *   Create a `unit_test_plan.md` artifact.
    *   For each source file:
        *   Identify every class, method, and function.
        *   Determine the **Happy Path**: Expected behavior with valid inputs.
        *   Determine **Edge Cases**:
            *   Null/Undefined/Empty inputs.
            *   Boundary values (0, -1, max_int, etc.).
            *   Invalid formats or types.
        *   Determine **Error States**: Exceptions that should be thrown or handled.
    *   Plan specific test cases for each scenario.

3.  **Test Implementation**
    *   Generate test files mirroring the source structure (e.g., `src/utils.ts` -> `tests/utils.test.ts`).
    *   **Strict Isolation**: Mock all external dependencies (DB, Network, File System) to ensure tests rely only on the unit itself.
    *   **Quality Standards**:
        *   Use descriptive test names (e.g., `should_return_error_when_input_is_negative`).
        *   Follow the Arrange-Act-Assert pattern.
        *   Include comments explaining complex test logic.

4.  **Verification (Optional)**
    *   If the environment allows, run the newly generated tests.
    *   Report on any failures or compilation errors.

## Output

1.  **`unit_test_plan.md`**: A detailed document outlining the strategy and coverage for each file.
2.  **Test Code**: High-quality, runnable unit test files.
3.  **Summary**: A final report on what was generated and any manual steps required.

## Phase 5: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated `unit_test_plan.md` and the Test Code.
    *   Did you cover all edge cases listed in the plan?
    *   Are there any obvious compilation errors or syntax issues?
    *   Did you mock all external dependencies?
2.  **Refine**:
    *   If you missed edge cases, add them now.
    *   If code looks incorrect, fix it.
3.  **Stop**:
    *   If you are confident the tests are excellent and comprehensive.
    *   OR if you have reached the maximum iteration count.
