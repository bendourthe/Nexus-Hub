---
description: Interactive wizard to help the user create new Skills or Commands.
---
# Create Skill or Command Wizard

Interactive wizard to help the user create new **Skills** or **Commands**.

## Process

### 1. Identify Resource Type
Ask the user: "Do you want to create a **Skill** (passive capability) or a **Command** (interactive /slash-command)?"

### 2. Structured Interview
Depending on the choice, gather requirements:

**For a Command:**
*   **Goal**: What should this command do?
*   **Trigger**: What user intent triggers this?
*   **Process**: What steps should the AI follow?
*   **Output**: What should the final result look like?

**For a Skill:**
*   **Domain**: What category does this fall under? (e.g., Testing, Security, Refactoring)
*   **Capability**: What specific task does it enable?
*   **Activation**: When should this skill automaticall activate?

### 3. Drafting Phase
Generate a draft of the new file:
*   **Propose a Name**: (e.g., `commands/analyze-db.md` or `skills/security/sql-injection.md`)
*   **Draft Content**: structured markdown with clear instructions.

### 4. Feedback Loop
Show the draft to the user.
*   "Does this name work for you?"
*   "Are the steps accurate?"
*   Refine based on feedback.

### 5. Finalization
Once approved:
1.  Create the file in the appropriate directory:
    *   Commands: `.claude/commands/` (or `.gemini/commands/`)
    *   Skills: `.claude/skills/<category>/`
2.  Confirm creation.
