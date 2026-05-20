---
description: Help the user import skills from the Hub catalog into their project.
---
# Import Skills from Catalog

Help the user import skills from the Hub catalog into their project.

## Instructions

You are helping the user import Claude Code skills from the Hub catalog into their project. Follow these steps:

### Step 1: Locate the Skills Catalog

Ask the user: "Where is your Nexus-Hub catalog located? Please provide the path to the `catalog/skills/` directory."

**Common locations:**
- `~/Nexus-Hub/catalog/skills/`
- `../Nexus-Hub/catalog/skills/`
- A custom path the user specifies

Wait for the user's response before proceeding.

### Step 2: Verify the Path

Once the user provides the path, verify it exists and contains skills by looking for SKILL.md files in subdirectories.

If the path is invalid, ask the user to provide a correct path.

### Step 3: Present Available Skills by Category

Display the available skills organized by category (Tests Generation, Code Review, Code Cleanup, Documentation, Compliance, Project Setup, Workflow, Security).

### Step 4: Ask User Selection

Ask the user: "Which skills would you like to import? You can:
1. Type **all** to import all skills
2. Type a **category name** to import all skills in that category
3. Type **specific skill names** separated by commas
4. Type **recommended** for a curated selection"

### Step 5: Execute Import

For each selected skill, copy the skill directory from the catalog to the project's `.claude/skills/` directory, organizing by category:

```
.claude/skills/
├── tests-generation/
│   ├── unit-tests/SKILL.md
...
```

### Step 6: Report Results

Confirm successful import and list loaded skills.


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
