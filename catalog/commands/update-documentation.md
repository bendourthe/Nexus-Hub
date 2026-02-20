---
description: Discover, audit, and update all documentation files (READMEs, guides, manuals) to match the current state of the codebase.
---

# Update Documentation Command

Discover all documentation files in the codebase, compare their content against the actual implementation, and update them to reflect reality.

**Scope**: READMEs, user guides, API docs, infrastructure docs, and other reference documentation.
**Out of scope**: CHANGELOG.md (use `/generate-changelog`), DEVLOG.md (use `/update-devlog`), version strings (use `/updated-version`).

## Phase 1: Discover and Classify Documentation Files

Find all `.md` files in the project and classify each as documentation or non-documentation.

### Include (Documentation)

These file types should be analyzed and updated:

- `README.md` files (root and all subdirectories)
- `CATALOG.md`, `GUIDE.md`, `MANUAL.md`, or similar reference files
- Files in `docs/`, `guides/`, `documentation/` directories
- Infrastructure documentation (`infrastructure/**/README.md`)
- Extension documentation (`extensions/**/README.md`)
- Skills overview files (`catalog/skills/README.md`, `catalog/skills/CATALOG.md`)
- API documentation files
- Configuration guides

### Exclude (Not Documentation)

These are managed by other commands or are not user-facing documentation:

- `CHANGELOG.md` (managed by `/generate-changelog`)
- `DEVLOG.md` (managed by `/update-devlog`)
- `CLAUDE.md`, `GEMINI.md` (AI system instructions, not user docs)
- Command definitions (`catalog/commands/*.md`)
- Skill definitions (`catalog/skills/**/SKILL.md`)
- Template files (`templates/**/*.md`)
- Context and memory files (`catalog/context/*.md`, `catalog/memory/*.md`)
- Compliance framework templates

### Output

Present a labeled inventory to the user:

```markdown
## Documentation Files Found

### Will Analyze (X files)
| # | File | Type | Last Modified |
|---|------|------|--------------|
| 1 | README.md | Root README | YYYY-MM-DD |
| 2 | extensions/claude-usage-monitor/README.md | Extension Docs | YYYY-MM-DD |
| ... | ... | ... | ... |

### Excluded (Y files)
- CHANGELOG.md (managed by /generate-changelog)
- DEVLOG.md (managed by /update-devlog)
- [N] command definitions
- [N] skill definitions
- [N] templates
```

Ask the user to confirm the list before proceeding. If they want to include or exclude specific files, adjust accordingly.

## Phase 2: Analyze the Codebase (Build Ground Truth)

Before checking documentation, build a comprehensive understanding of what the codebase actually contains. This is the "ground truth" that documentation should reflect.

### 2a. Project Structure

```bash
# Map directory structure (top 3 levels)
find . -maxdepth 3 -type d | head -60

# List key files in root
ls -la
```

- Identify all major directories and their purposes
- Note any directories that exist but are not documented

### 2b. Dependencies and Configuration

- Read `package.json`, `pyproject.toml`, `requirements.txt`, or equivalent
- Note installed dependencies, scripts, build commands
- Read configuration files (`.eslintrc`, `tsconfig.json`, etc.)

### 2c. Features and Functionality

- Identify entry points (main scripts, CLI commands, extension activation)
- Map the feature set: what does the project actually do today?
- Identify recent additions (files modified in the last 30 days via `git log --since="30 days ago" --name-only --diff-filter=A`)
- Note any features that were removed or significantly changed recently

### 2d. Architecture

- Identify patterns: hooks system, installer phases, extension architecture, skills catalog, etc.
- Map relationships between components
- Note integration points (APIs, file formats, configuration)

## Phase 3: Compare Documentation vs. Reality

For each documentation file from Phase 1, read its content and compare against the ground truth from Phase 2. Check for:

### 3a. Structure Accuracy
- Do directory trees or project structure descriptions match the actual filesystem?
- Are all documented modules, folders, and files still present?
- Are new directories or modules missing from the documentation?

### 3b. Feature Accuracy
- Do feature lists and descriptions match what is actually implemented?
- Are there new features not mentioned in any documentation?
- Are there documented features that no longer exist or work differently?

### 3c. Installation and Setup Accuracy
- Are installation steps correct and complete?
- Are prerequisites (Node.js version, dependencies, tools) accurate?
- Do documented commands actually work?

### 3d. API and Configuration Accuracy
- Do documented APIs, commands, or settings match the code?
- Are configuration options accurate (names, types, defaults)?
- Are code examples up-to-date?

### 3e. Internal Links
- Do relative links to other files resolve to existing files?
- Do anchor links within documents point to existing headings?
- Do image or asset references point to existing files?

### 3f. Stale References
- References to removed files, renamed modules, or deleted functions
- Outdated dependency versions in examples
- Old configuration formats or deprecated APIs

### 3g. Missing Documentation
- Significant modules or features with no README or documentation at all
- New components added since the documentation was last updated

### Severity Classification

| Severity | Description | Examples |
|----------|-------------|---------|
| **Critical** | Documentation is factually wrong or misleading | Wrong installation steps, incorrect API usage, broken examples |
| **High** | Significant content is missing or outdated | New major feature undocumented, removed feature still listed |
| **Medium** | Minor inaccuracies or stale content | Outdated directory tree, old dependency version in example |
| **Low** | Cosmetic or minor improvements | Broken internal link, placeholder text, minor wording |

## Phase 4: Generate Report

Present findings as a consolidated report:

```markdown
## Documentation Audit Report

### Summary
- Documentation files checked: X
- Files needing updates: Y
- Total findings: Z (Critical: _, High: _, Medium: _, Low: _)

### Per-File Findings

#### 1. README.md
| # | Severity | Finding | Proposed Fix |
|---|----------|---------|-------------|
| 1 | Critical | Installation step 3 references removed script | Update to current script name |
| 2 | High | Feature list missing "Usage Monitoring" section | Add section describing the 3 monitoring features |
| ... | ... | ... | ... |

#### 2. extensions/claude-usage-monitor/README.md
| # | Severity | Finding | Proposed Fix |
|---|----------|---------|-------------|
| ... | ... | ... | ... |

### Missing Documentation
- [List of undocumented modules/features that should have docs]

### Broken Links
| File | Link | Target | Status |
|------|------|--------|--------|
| ... | ... | ... | Not found / Wrong path |
```

Then ask:

```
How would you like to proceed?
1. **Fix all** - Update all documentation files with the proposed fixes
2. **Critical + High only** - Only fix Critical and High severity issues
3. **Specific files** - Tell me which files to update
4. **No changes** - Review complete, no updates needed
```

## Phase 5: Update Documentation

After user approval, update each file one by one:

1. Read the current content of the documentation file
2. Apply the approved changes using targeted edits (not full rewrites)
3. Preserve the existing structure, tone, and formatting
4. After each file, briefly report what changed:

```
Updated: extensions/claude-usage-monitor/README.md
- Added "Auto-fetch API" section (was missing)
- Fixed installation command (npm install → npm ci)
- Updated settings table with new refreshInterval default
```

### Update Guidelines

- **Preserve voice**: Match the existing writing style and tone of each document
- **Targeted edits**: Fix specific inaccuracies rather than rewriting entire sections
- **No scope creep**: Only fix what was identified in the report. Do not add commentary, opinions, or embellishments.
- **No formatting changes**: Do not reformat sections that are not being updated
- **Link fixes**: Update broken internal links to correct paths
- **New sections**: When adding content for undocumented features, place it in the logical location within the existing document structure

## Phase 6: Summary

After all updates are complete:

```markdown
## Documentation Update Summary

### Updated (X files)
| File | Changes Made |
|------|-------------|
| README.md | Fixed feature list, updated directory tree |
| extensions/.../README.md | Added new settings, fixed example |

### Skipped (Y files)
- [Files that were already accurate]

### New Documentation Created (if any)
- [New README.md files created for undocumented modules]

### Remaining Recommendations
- [Any items deferred or requiring manual review]
```


## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Did every documentation file get checked?
    *   Were all findings classified with correct severity?
    *   Are proposed fixes accurate and complete?
    *   Were updates applied cleanly without breaking formatting?
2.  **Refine**:
    *   Fix any issues found.
    *   Re-check files that had the most changes.
    *   Verify internal links in updated files still resolve.
3.  **Stop**:
    *   If you are confident the result is thorough.
    *   OR if you have reached the maximum iteration count.
