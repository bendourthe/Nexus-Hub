
# Analysis of Changes
- **Catalog Update**: 63+ skill files and 13 command files were modified.
- **Nature of Change**: Appended "Iterative Refinement Strategy" to skills and "Iterative Refinement (Loop)" to commands.
- **Reason**: To enable the agent to self-correct and iterate on tasks.
- **Affected Components**: `catalog/skills`, `catalog/commands`.

# Draft Commit Message
type: feat
scope: workflow
description: add iterative refinement strategy to all skills and commands

body:
- Updated 13 command workflows (e.g., generate-unit-tests) to include a 3-step iterative refinement loop.
- Updated 63+ skills in the catalog to include a standardized "Iterative Refinement Strategy" section.
- This enables the agent to self-critique and improve outputs (coverage, quality) before completion.
- Added `scripts/apply_iterative_workflow.py` automation script.

# Iterative Refinement
1. **Analyze**: Does this cover everything? Yes, the script addition and the mass file updates.
2. **Refine**: The description is concise. The scope is correct. The body explains *why* (self-critique).
3. **Verdict**: The message is high quality.
