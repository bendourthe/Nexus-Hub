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
