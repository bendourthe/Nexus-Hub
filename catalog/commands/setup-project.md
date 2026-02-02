---
description: Help the user configure their CLAUDE.md with a well-structured project description.
---
# Project Setup Assistant

Help the user configure their CLAUDE.md with a well-structured project description.

## Instructions

You are helping the user set up their project configuration. Ask the following questions ONE AT A TIME, waiting for each response before proceeding:

### Question 1: Project Name
Ask: "What's the name of your project?"

### Question 2: Project Purpose
Ask: "In one sentence, what does this project do? (e.g., 'A CLI tool that analyzes code complexity')"

### Question 3: Key Features
Ask: "What are the 3-5 main features or capabilities? (Brief bullet points are fine)"

### Question 4: Target Users
Ask: "Who will use this project? (e.g., developers, data scientists, end-users, internal team)"

### Question 5: Additional Context (Optional)
Ask: "Any specific frameworks, integrations, or constraints I should know about? (Press Enter to skip)"

## After Gathering Responses

1. **Generate a polished Overview section** that:
   - Uses professional, clear language
   - Is 2-4 sentences long
   - Captures the essence and value proposition
   - Avoids marketing fluff

2. **Update CLAUDE.md** with:
   - Project title in the header
   - The generated Overview section
   - Any relevant tech stack additions mentioned

3. **Show the user** the generated content and ask for approval before saving

## Example Output Format

```markdown
# Project: [Project Name]

## Overview
[Generated 2-4 sentence description that clearly explains what the project does,
its primary purpose, and who it's for. Written in a professional, concise style.]
```

## Guidelines

- Keep the description factual and clear
- Focus on WHAT it does and WHY it's useful
- Avoid buzzwords and excessive adjectives
- Match the technical level to the target users
- If the project already has content in CLAUDE.md, preserve other sections


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
