---
description: Perform a deep, thorough, and comprehensive analysis of the entire codebase.
---
# Run Deep Review Command

Perform a deep, thorough, and comprehensive analysis of the entire codebase.

## Objective
Analyze the code for logical correctness, architectural integrity, performance optimization, and edge case handling.

## Analysis Steps

1.  **Architecture & Flow**: Map out how components interact.
2.  **Error Detection**: Scan for potential runtime errors, unhandled exceptions, and race conditions.
3.  **Optimization**: Identify inefficient algorithms, redundant computations, or resource leaks.
4.  **Edge Cases**: specifically look for missing boundary checks or invalid state handling.

## Output Report Structure

Please provide a detailed report in the following format:

### 1. Executive Summary
A high-level overview of the health of the codebase.

### 2. Codebase Functionality
An organized block indicating what the codebase does (feature by feature).

### 3. Issues & Troubleshooting
*   **Potential Errors**: List of identified risks.
*   **Troubleshooting Needs**: Areas that seem fragile.

### 4. Optimization Opportunities
Suggestions for performance improvements or refactoring.

### 5. Missed Edge Cases
Scenarios that are currently not handled.

---

## Next Steps
(End the response by asking:)
> "Would you like me to now run the `/generate-tests` command to verify these findings and ensure robustness?"


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
