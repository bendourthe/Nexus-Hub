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
    *   **Body**: Paragraphs and/or bullet points explaining *what* changed and *why*. Group by component.
    *   **No hard-wrapping (CRITICAL)**: Every paragraph and every bullet point in the body and footer MUST be written as a single continuous line in the source, regardless of length. Do NOT insert line breaks at any column width (50, 72, 80, 100, etc.). Let the user's editor or terminal handle visual wrapping. Blank lines still separate paragraphs, bullets, and section headings; the rule applies *within* each paragraph or bullet, never *between* them. The subject line is the only exception (its 50-character limit is a hard cap, not a wrap).
    *   **Encoding**: Use ASCII characters only. No em-dashes, en-dashes, curly quotes, ellipsis characters, or other Unicode punctuation. Use hyphens, straight quotes, and `...` instead. This prevents encoding corruption on Windows.
    *   **Footer**: Note any breaking changes or issue references.
        - **DO NOT** add `Co-Authored-By` lines or AI attribution footers

## Output
Provide the commit message in a code block for easy copying.

Example (note that every paragraph and bullet is a single continuous line in the source — there are no mid-paragraph or mid-bullet line breaks):

```text
feat(installer): add overwrite-all support to workspace phase

Extend the workspace install phase so users can answer "overwrite all" once at the first prompt instead of being asked per file. The flag now propagates through every nested Install-Workspace call so Copilot, Cursor, and Codex configs share the same answer.

Highlights:

- Added [A]ll option to overwrite prompts for Copilot/Cursor config so a single keystroke covers the entire phase instead of one per file.
- Updated Install-Workspace to respect a global overwrite flag passed down from the parent phase, including the Codex sub-phase that previously re-prompted.
- Standardized logging format across phases so the workspace, hooks, and skills phases all emit the same `[phase] action: target` shape, making the install transcript greppable.

Tests: 84 pass, 0 skips, 92.4% coverage.
```

Counter-example — DO NOT produce this (note the mid-paragraph and mid-bullet line breaks at ~72 columns):

```text
feat(installer): add overwrite-all support to workspace phase

Extend the workspace install phase so users can answer "overwrite all"
once at the first prompt instead of being asked per file. The flag
now propagates through every nested Install-Workspace call.

- Added [A]ll option to overwrite prompts for Copilot/Cursor config
  so a single keystroke covers the entire phase.
- Updated Install-Workspace to respect a global overwrite flag passed
  down from the parent phase.
```

The counter-example wraps both a paragraph and a bullet at a fixed column width. The agent must never produce output in that shape, even when the resulting line exceeds 100 characters.

**Important**: The generated commit message must never include `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures. The commit message represents the developer's work, not the tool that helped write it.

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
