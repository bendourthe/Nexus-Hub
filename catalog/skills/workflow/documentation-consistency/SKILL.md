---
name: documentation-consistency
description: Verify documentation is up-to-date and consistent across all files. Check for broken links, outdated references, deprecated content, and mismatched information. Use when auditing documentation, checking for stale content, verifying links, ensuring docs match current codebase state, running a link audit, detecting cross-file mismatches, or reviewing deprecated documentation. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/.
summary_l0: "Verify documentation links, lifespan placement, staleness, and cross-file consistency"
overview_l1: "This skill verifies documentation is up-to-date and consistent across all files, checking for broken links, outdated references, deprecated content, and mismatched information. Use it when auditing documentation, checking for stale content, verifying links, or ensuring docs match current codebase state. Key capabilities include broken link detection (internal and external), outdated reference identification, deprecated content flagging, cross-file information consistency checking, code-to-documentation synchronization verification, version number consistency checking, and documentation freshness scoring. The expected output is a documentation consistency report with broken links, outdated references, mismatches, and recommended fixes. Trigger phrases: documentation audit, broken links, stale docs, outdated documentation, doc consistency, verify documentation, documentation sync, docs match code. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Documentation Consistency Check

Systematically audit all documentation to ensure consistency, accuracy, and alignment with the current state of the codebase.

## When to Use This Skill

Use this skill when you need to:

- Audit documentation for accuracy
- Check for broken or outdated links
- Find references to non-existent files or functions
- Verify version numbers are consistent
- Remove deprecated or stale content
- Ensure documentation matches codebase structure
- Prepare for a release

**Trigger phrases**: "check documentation", "audit docs", "find broken links", "update documentation", "docs consistency", "stale documentation", "outdated references"

## What This Skill Does

### Consistency Audit Process

1. **Cross-Reference Validation** - Verify all references point to existing files
2. **Version Consistency** - Check version numbers match across files
3. **Structure Alignment** - Ensure documented structure matches actual files
4. **Link Verification** - Test all internal and external links
5. **Content Freshness** - Identify potentially outdated content
6. **Deprecation Cleanup** - Remove references to deleted/renamed items
7. **Comparison / Adoption-Plan Co-location** - Verify each comparison and the adoption plan it seeds live in the same version directory

## Instructions

### Step 1: Identify All Documentation Files

```bash
# Find all markdown documentation files
find . -name "*.md" -type f | grep -v node_modules | grep -v .venv | grep -v __pycache__

# Common documentation files to check:
# - README.md
# - CHANGELOG.md
# - docs/DEVLOG.md
# - docs/*.md
# - .claude/context/*.md
# - guides/*.md
```

### Step 2: Check Internal Links

Verify all markdown links point to existing files:

```bash
# Find all markdown links in a file
grep -oE '\[.*?\]\([^)]+\)' README.md

# Extract just the paths
grep -oE '\[.*?\]\([^)]+\)' README.md | sed 's/.*(\([^)]*\))/\1/' | grep -v "^http"

# For each path, verify the file exists
for link in $(grep -oE '\[.*?\]\([^)]+\)' README.md | sed 's/.*(\([^)]*\))/\1/' | grep -v "^http"); do
  if [ ! -f "$link" ] && [ ! -d "$link" ]; then
    echo "BROKEN: $link"
  fi
done
```

### Step 3: Verify Version Consistency

Check that version numbers match across all files:

```bash
# Search for version patterns
grep -rn "version" --include="*.md" --include="*.toml" --include="*.json" --include="*.yaml" .

# Common version locations:
# - pyproject.toml: version = "X.Y.Z"
# - package.json: "version": "X.Y.Z"
# - README.md: badges, headers
# - CHANGELOG.md: ## [X.Y.Z]
# - __version__.py or __init__.py
```

### Step 4: Validate Project Structure References

Compare documented structure to actual file system:

```bash
# Get actual project structure
find . -type f -name "*.py" -o -name "*.js" -o -name "*.ts" | head -50

# Compare with documented structure in README.md
# Look for:
# - Directories mentioned that don't exist
# - Files mentioned that have been removed
# - Missing documentation for new files/directories
```

### Step 5: Check for Deprecated References

Look for references to items that no longer exist:

#### Functions and Classes
```bash
# Find function/class references in docs
grep -rE "(def |class |function )\w+" docs/ README.md

# Verify each referenced function/class exists in codebase
# Flag any that can't be found
```

#### File References
```bash
# Find file path references
grep -rE "(`[^`]+\.(py|js|ts|go|java|cs|cpp|c|h)`)" --include="*.md" .

# Check each referenced file exists
```

#### Configuration Options
```bash
# Find configuration references
grep -rE "(config\.|settings\.|options\.)" --include="*.md" .

# Verify documented options match actual config files
```

### Step 6: Audit External Links

```bash
# Find all external links
grep -rEoh "https?://[^)\"' >]+" --include="*.md" . | sort -u

# Test each link (optional - may take time)
# curl -s -o /dev/null -w "%{http_code}" URL

# Common issues:
# - 404 (page not found)
# - 301/302 (redirects - may need updating)
# - SSL errors
```

### Step 7: Check for Stale Content

Look for indicators of outdated documentation:

#### Date Markers
```bash
# Find date references
grep -rE "(January|February|March|April|May|June|July|August|September|October|November|December) 20[0-9]{2}" --include="*.md" .
grep -rE "202[0-3]-[0-9]{2}" --include="*.md" .  # Old dates

# Flag anything older than 6-12 months for review
```

#### TODO/FIXME Comments
```bash
# Find outstanding documentation TODOs
grep -rn "TODO\|FIXME\|XXX\|HACK" --include="*.md" .
```

#### Placeholder Text
```bash
# Find unfilled placeholders
grep -rE "\[.*?\]|\{.*?\}|<.*?>" --include="*.md" . | grep -v "http"
grep -rE "TBD|TBA|Coming soon|TODO" --include="*.md" .
```

### Step 7.5: Comparison / Adoption-Plan Co-location

A `/compare` report and the `/plan from-comparison` plan it seeds must live in the SAME version directory (`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`). A comparison is versioned and placed by its `Adoption target: vX.Y.Z` header field (`cross-project-comparison` Step 6.5), and `/plan from-comparison` co-locates the generated plan in that same tree (`implementation-plan` From-comparison mode). This check flags any drift between the two so the misplacement class cannot silently recur.

Two directions catch all drift without false positives:

- **plan -> comparison** (authoritative): for each plan carrying a `**Seeded from**:` line, the referenced comparison must live in the plan's own version directory.
- **comparison -> adoption target**: for each comparison carrying an `Adoption target: vX.Y.Z`, the comparison must sit under that target's version directory. A comparison with no `Adoption target:` field is a legacy report (noted, not failed - give it the field so it can be enforced).

**Grandfathering**: only the CURRENT major's active version directories are enforced. `docs/archives/**` and prior-major trees (`docs/v1/**`, `docs/v2/**`, ...) are intentionally excluded, mirroring the `[[docs-layout-refactor]]` grandfathering norm - the check achieves this simply by scoping its search to `docs/releases/v<CURRENT_MAJOR>/`.

```bash
# Comparison / adoption-plan co-location check (assumes the canonical
# docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/ layout; legacy flat layouts are grandfathered).

# Current major = highest docs/v<N> directory.
CURRENT_MAJOR=$(ls -d docs/v[0-9]* 2>/dev/null | sed -E 's|docs/v([0-9]+).*|\1|' | sort -n | tail -1)
echo "Enforcing co-location under docs/releases/v${CURRENT_MAJOR}/ (docs/archives/** and prior majors grandfathered)"

# version_dir of a path: docs/releases/v3/v3.15/comparisons/x.md -> docs/releases/v3/v3.15
verdir() { echo "$1" | sed -E 's|(docs/v[0-9]+/v[0-9]+\.[0-9]+)/.*|\1|'; }

mismatches=0

# Direction 1: plan -> comparison (anchored on the plan's `**Seeded from**:` line).
find "docs/releases/v${CURRENT_MAJOR}" -type f -path "*/plans/*.md" 2>/dev/null | while read -r plan; do
  seeded=$(grep -E '\*\*Seeded from\*\*:' "$plan" | grep -oE 'docs/v[0-9]+/[^`) ]+\.md' | head -1)
  [ -z "$seeded" ] && continue
  pdir=$(verdir "$plan"); cdir=$(verdir "$seeded")
  if [ "$pdir" != "$cdir" ]; then
    echo "MISMATCH (plan/comparison): $plan (in $pdir) is seeded from $seeded (in $cdir); expected the comparison under $pdir/comparisons/"
    mismatches=$((mismatches+1))
  fi
done

# Direction 2: comparison -> its declared adoption target.
find "docs/releases/v${CURRENT_MAJOR}" -type f -path "*/comparisons/*.md" 2>/dev/null | while read -r cmp; do
  tgt=$(grep -iE 'Adoption target' "$cmp" | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  if [ -z "$tgt" ]; then
    echo "NOTE (legacy): $cmp has no 'Adoption target:' field - give it one so co-location can be enforced"
    continue
  fi
  major=$(echo "$tgt" | sed -E 's|v([0-9]+)\..*|\1|'); minor=$(echo "$tgt" | sed -E 's|v[0-9]+\.([0-9]+)\..*|\1|')
  expected="docs/v${major}/v${major}.${minor}"
  cdir=$(verdir "$cmp")
  if [ "$cdir" != "$expected" ]; then
    echo "MISMATCH (comparison placement): $cmp (in $cdir) declares Adoption target $tgt; expected under ${expected}/comparisons/"
    mismatches=$((mismatches+1))
  fi
done

echo "Co-location check complete (MISMATCH lines above, if any, must be reconciled via [[docs-layout-refactor]])."
```

Report every `MISMATCH` line in the consistency report with both paths and the expected location, and reconcile it by moving the misplaced file and repairing references via `[[docs-layout-refactor]]` (propose-then-apply, with confirmation). Treat each `NOTE (legacy)` as a low-priority recommendation, not a failure.

### Step 7.6: Lifespan Contradictions

Run the standalone frozen-bucket edit-history check defined once in [`docs-layout-refactor`'s link-integrity reference](../../code-cleanup/docs-layout-refactor/references/link-integrity.md). Invoke `audit-docs.py lifespan-contradictions --root ./docs --repo-root .`, copy every returned record into a `## Lifespan contradictions` report section, and fail the audit when the command exits 1 or 2. Findings require human intent review; this skill never moves the file automatically.

### Step 8: Generate Consistency Report

Create a summary of all issues found:

```markdown
# Documentation Consistency Report

## Generated: YYYY-MM-DD

### Summary
- **Files Audited**: X
- **Issues Found**: Y
- **Critical**: Z
- **Warnings**: W

### Broken Links
| File | Line | Broken Link | Suggested Fix |
|------|------|-------------|---------------|
| README.md | 45 | [link](old/path.md) | Update to new/path.md |

### Version Mismatches
| File | Current | Expected |
|------|---------|----------|
| README.md | 1.0.0 | 1.2.0 |

### Deprecated References
| File | Line | Reference | Issue |
|------|------|-----------|-------|
| docs/api.md | 23 | `old_function()` | Function removed in v1.1.0 |

### Stale Content
| File | Section | Last Updated | Notes |
|------|---------|--------------|-------|
| docs/setup.md | Installation | 2023-06 | May need update |

### Missing Documentation
| Item | Type | Notes |
|------|------|-------|
| new_module.py | Module | No documentation found |

### Recommendations
1. **High Priority**: Fix broken links in README.md
2. **Medium Priority**: Update version references
3. **Low Priority**: Review stale content in docs/
```

### Step 9: Check Doc-Header Summaries (System Docs)

Verify that every SYSTEM doc (architecture, policy, reference, runbook - not point-in-time artifacts like session histories, comparison reports, CHANGELOG, or plans) opens with a greppable summary header per `catalog/style-guides/doc-headers.md`: a title plus a 3-7 line summary (what it covers, who reads it and when, key topics) above the first `##`. Flag any system doc missing the header. Apply the SELF-HEALING rule: flag any doc whose header no longer matches the system it describes (drift), propose the corrected summary, and update the doc in the same change that alters the system.

## Common Documentation Issues

### Issue Categories

| Category | Examples | Severity |
|----------|----------|----------|
| Broken Links | 404s, wrong paths | High |
| Version Mismatch | Old versions in badges/text | High |
| Missing Files | Referenced files deleted | High |
| Deprecated APIs | Old function names | Medium |
| Stale Content | Outdated instructions | Medium |
| Unfilled Placeholders | [TODO], TBD | Low |
| Typos | Misspelled file names | Low |

### Fix Patterns

#### Broken Internal Link
```markdown
# Before (broken)
See [installation guide](docs/install.md)

# After (fixed - file moved)
See [installation guide](guides/installation.md)
```

#### Version Update
```markdown
# Before
![Version](https://img.shields.io/badge/version-1.0.0-blue)

# After
![Version](https://img.shields.io/badge/version-1.2.0-blue)
```

#### Deprecated Reference
```markdown
# Before
Use `old_api_call()` to fetch data.

# After
Use `new_api_call()` to fetch data. (Note: `old_api_call()` was deprecated in v1.1.0)
```

## Automation Script Template

```python
#!/usr/bin/env python3
"""Documentation consistency checker."""

import os
import re
from pathlib import Path

def find_markdown_files(root_dir: str) -> list[Path]:
    """Find all markdown files in project."""
    excludes = {'node_modules', '.venv', '__pycache__', '.git'}
    files = []
    for path in Path(root_dir).rglob('*.md'):
        if not any(ex in path.parts for ex in excludes):
            files.append(path)
    return files

def extract_internal_links(content: str) -> list[str]:
    """Extract internal links from markdown content."""
    pattern = r'\[.*?\]\(([^)]+)\)'
    links = re.findall(pattern, content)
    return [l for l in links if not l.startswith(('http', '#', 'mailto'))]

def check_link_exists(link: str, base_path: Path) -> bool:
    """Check if linked file exists."""
    target = base_path.parent / link
    return target.exists()

def audit_documentation(root_dir: str) -> dict:
    """Run full documentation audit."""
    results = {
        'broken_links': [],
        'version_mismatches': [],
        'stale_content': [],
        'todos': []
    }

    for md_file in find_markdown_files(root_dir):
        content = md_file.read_text(encoding='utf-8')

        # Check links
        for link in extract_internal_links(content):
            if not check_link_exists(link, md_file):
                results['broken_links'].append({
                    'file': str(md_file),
                    'link': link
                })

        # Check for TODOs
        if 'TODO' in content or 'FIXME' in content:
            results['todos'].append(str(md_file))

    return results

if __name__ == '__main__':
    results = audit_documentation('.')
    print(f"Broken links: {len(results['broken_links'])}")
    print(f"Files with TODOs: {len(results['todos'])}")
```

## Verification

Before completing documentation audit:

- [ ] All internal links verified and working
- [ ] Version numbers consistent across all files
- [ ] No references to non-existent files/functions
- [ ] External links tested (at least critical ones)
- [ ] Placeholder text filled or removed
- [ ] TODOs addressed or documented for follow-up
- [ ] Deprecated content removed or marked
- [ ] Documentation structure matches codebase
- [ ] Every comparison and the adoption plan it seeds live in the same version dir (Step 7.5); mismatches for the current major reconciled, `docs/archives/**` and prior-major trees grandfathered
- [ ] Frozen-bucket edit history checked through the shared lifespan-contradiction rule; every finding reports both dates and no file moved automatically
- [ ] Dates updated where applicable
- [ ] Consistency report generated

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The docs were correct when I wrote them, so they are still fine" | Code drifts away from prose silently; a renamed function or moved file leaves a dead link or a stale example that misleads the next reader who trusts the doc. |
| "Broken links are cosmetic, not worth an audit" | A broken install or API link in a README blocks a new user at the first step; the cost is a lost contributor, not a cosmetic blemish. |
| "Version numbers will be consistent because I bumped the main one" | Version strings live in many files (README, package manifest, docs headers); bumping one and missing the rest produces contradictory claims that erode trust in every number. |

## Related Skills

- [[version-upgrade]] -- the version bump workflow whose cross-file edits this audit verifies for consistency
- [[code-commit-workflow]] -- commit hygiene that keeps doc changes atomic with the code they describe
- [[technical-documentation]] -- authoring the docs whose freshness and link integrity this skill checks

---

**Version**: 1.2.0
**Last Updated**: July 2026


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
