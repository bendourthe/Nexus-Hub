---
description: Perform a comprehensive documentation consistency check across the project.
---
# Documentation Consistency Audit

Perform a comprehensive documentation consistency check across the project.

## Instructions

You are performing a documentation audit to ensure all docs are accurate, consistent, and up-to-date. Follow these steps systematically:

### Step 1: Identify Documentation Files

First, find all documentation files in the project:

```
Look for:
- README.md (root and subdirectories)
- CHANGELOG.md
- DEVLOG.md
- docs/ directory contents
- API documentation
- Configuration guides
- Any .md files in the project
```

Tell the user what documentation files you found.

### Step 2: Check Internal Links

Verify all internal links and references:

```
For each documentation file:
- [ ] Check relative links to other docs
- [ ] Verify code file references exist
- [ ] Check anchor links within documents
- [ ] Verify image/asset references
```

Report any broken links found.

### Step 3: Version Consistency

Check version numbers are consistent across:

```
Files to check:
- README.md (version badge/header)
- CHANGELOG.md (latest version)
- pyproject.toml / package.json (version field)
- __version__ in source code
- Any hardcoded version references
```

Report any version mismatches.

### Step 4: Project Structure Accuracy

Verify documented structure matches reality:

```
Compare:
- Directory trees in README match actual structure
- Module descriptions match actual modules
- Feature lists match implemented features
- Installation steps are accurate
```

Report any discrepancies.

### Step 5: Deprecated References

Search for outdated content:

```
Look for:
- References to removed files/functions
- Deprecated API usage in examples
- Old configuration formats
- Outdated dependency versions in examples
```

List any deprecated references found.

### Step 6: External Links (Optional)

If the user wants, check external URLs:

```
Verify:
- Documentation links are accessible
- Package registry links work
- Reference links are valid
```

Ask the user if they want external link verification.

### Step 7: Stale Content Detection

Identify potentially outdated sections:

```
Flag sections that may need review:
- "Coming soon" or "TODO" markers
- Date references older than 6 months
- Version-specific instructions for old versions
- Placeholder content
```

### Step 8: Generate Consistency Report

Present findings to the user:

```markdown
## Documentation Consistency Report

### Summary
- Files Checked: X
- Issues Found: Y
- Critical: Z

### Broken Links
| File | Line | Broken Link | Suggested Fix |
|------|------|-------------|---------------|

### Version Mismatches
| Location | Found | Expected |
|----------|-------|----------|

### Structure Discrepancies
- [List of mismatches]

### Deprecated References
- [List with locations]

### Stale Content
- [Sections needing review]

### Recommendations
1. [Priority fixes]
2. [Suggested improvements]
```

## After the Audit

Ask the user:
1. "Would you like me to fix the broken links automatically?"
2. "Should I update the version references to be consistent?"
3. "Would you like me to update the project structure documentation?"

Only make changes after user approval.

## Guidelines

- Be thorough but don't overwhelm with minor issues
- Prioritize critical issues (broken links, version mismatches)
- Suggest fixes, don't just report problems
- Group related issues together
- Provide actionable recommendations


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
