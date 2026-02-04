---
description: Analyze recent changes and generate a comprehensive entry for the DEVLOG.md file.
---
# Update DEVLOG Command

Analyze recent changes and generate a comprehensive entry for the `DEVLOG.md` file.

## Objective
Maintain a detailed history of development to aid future AI agents in troubleshooting and context retrieval. This log serves as a persistent "memory" of challenges, failures, and solutions.

## Process

1.  **Analyze Context**:
    *   Read the existing `DEVLOG.md` (if present) to identify the last recorded state.
    *   Analyze git history/diffs since the last entry.
    *   Recall (or infer from code comments/commit messages) specific errors encountered.

2.  **Synthesize Entry**:
    Create a new Markdown entry with the following structure:

    ### [YYYY-MM-DD HH:MM] - [Short Title of Task]
    
    *   **Goal**: What was the primary objective?
    *   **Attempted Solutions**:
        *   *Approach 1*: Description of what was tried.
            *   *Result*: Failed/Partially Worked.
            *   *Error*: `[Quote specific error logs or messages]`
            *   *Analysis*: Why did this fail? (e.g., "Syntax error in Powershell 5.1", "API misuse").
        *   *Approach 2* (The Solution): Description of the successful fix.
    *   **Changes**:
        *   Modified `[file_path]`: [Brief desc of change]
    *   **Lessons Learned**: Critical context for future agents (e.g., "Always use `Safe-Copy` for this file type to avoid locks").
    *   **Current Status**: Verified/Pending/Broken.

3.  **Action**:
    *   Append this entry to the top (or chronological bottom, depending on existing file style) of `DEVLOG.md`.
    *   If `DEVLOG.md` does not exist, create it.


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
