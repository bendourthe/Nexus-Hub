---
description: Analyze the current git changes and generate a comprehensive, structured commit message.
---
# Generate Commit Message Command

Analyze the current git changes and generate a comprehensive, structured commit message.

## Steps

1.  **Analyze Changes**:
    *   Run `git diff --name-status` to see which files changed.
    *   Run `git diff` to see the actual code changes (limit output if huge).
    *   Run `git diff --cached` to see staged changes.

2.  **Categorize**:
    *   Determine the type of change: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.
    *   Identify the scope (e.g., `installer`, `catalog`, `api`).

3.  **Draft Message**:
    *   **Title**: Conventional Commit format (`<type>(<scope>): <short summary>`). Limits to 50 chars.
        - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
        - Scope: Optional, e.g., `(auth)`, `(api)`, `(installer)`.
        - Description: Concise summary in imperative mood (e.g., "add feature" not "added feature").
    *   **Body**: Bullet points explaining *what* changed and *why*. Group by component.
    *   **Footer**: Note any breaking changes or issue references.

## Output
Provide the commit message in a code block for easy copying.

Example:
```text
feat(installer): add overwrite-all support to workspace phase

- Added [A]ll option to overwrite prompts for Copilot/Cursor config
- Updated Install-Workspace to respect global overwrite flag
- Standardized logging format across phases
```


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
