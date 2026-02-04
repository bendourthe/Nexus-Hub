---
description: Analyze git changes and generate a structured commit message
---

1. Run `git status` to check the current state of the repository.
2. Run `git diff` to view changes not staged for commit.
3. Run `git diff --cached` to view changes staged for commit.
4. Analyze the output from the above commands to understand the scope and nature of the changes.
5. Generate a comprehensive commit message following the Conventional Commits specification:
   - **Header**: `<type>(<scope>): <description>`
     - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
     - Scope: Optional, e.g., `(auth)`, `(api)`.
     - Description: Concise summary in imperative mood.
   - **Body**: Detailed explanation of changes. Use bullet points if necessary.
   - **Footer**: References to issues or breaking changes.
6. Present the generated commit message in a code block for easy copying.


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
