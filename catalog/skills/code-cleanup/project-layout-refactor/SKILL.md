---
name: project-layout-refactor
description: Audit and refactor repository root directories to follow standard layout rules. Moves misplaced files, fixes all path references, and verifies nothing breaks. Use when a repo has too many files in root, after adopting new layout conventions, or when preparing a project for public release.
summary_l0: "Refactor repository layout to follow standard conventions with full reference repair"
overview_l1: "This skill systematically reorganizes a repository's file layout to follow declared conventions, with full impact analysis and reference repair before any file is moved. Use it when cleaning up a cluttered project root, applying a standard layout ruleset to an existing project, migrating a repo after adopting new conventions, preparing a project for public release, enforcing layout consistency across a team, or auditing whether a repo matches its declared layout rules. Key capabilities include layout rule auditing, misplaced file detection, impact analysis before moves, path reference repair across all file types (imports, configs, CI pipelines, documentation links), and post-move verification to ensure nothing breaks. The expected output is a reorganized repository with all files in their correct directories, updated path references, and passing tests. Trigger phrases: refactor project layout, refactor repo layout, clean up root directory, too many files in root, organize project structure, apply layout rules, move files to correct directories, root is cluttered, layout conventions, project structure refactor."
---

# Project Layout Refactor

Systematically reorganize a repository's file layout to follow declared conventions, with full impact analysis and reference repair before any file is moved.

## When to Use This Skill

Use this skill when you need to:

- Clean up a cluttered project root with too many loose files
- Apply a standard layout ruleset to an existing project
- Migrate a repo after adopting new conventions (e.g., moving DEVLOG.md to `docs/`)
- Prepare a project for public release with a clean, navigable structure
- Enforce layout consistency across a team or organization
- Audit whether a repo's current layout matches its declared rules

**Trigger phrases**: "refactor project layout", "refactor repo layout", "clean up root directory", "too many files in root", "organize project structure", "apply layout rules", "move files to correct directories", "root is cluttered", "layout conventions", "project structure refactor"

## How to Invoke

### Claude Code

Use the slash command for an interactive guided experience:

```
/refactor-project-layout
```

Or activate this skill directly by using any of the trigger phrases above in your message.

### Codex (OpenAI CLI)

Activate by using any trigger phrase in your prompt. To explicitly invoke the skill, reference it by name:

```
Using the project-layout-refactor skill, audit and refactor the root directory of this project.
```

### Gemini CLI

Use any trigger phrase in your prompt. If you have imported the skill into `.gemini/skills/`, Gemini will auto-activate it. To invoke explicitly:

```
Apply the project-layout-refactor skill to clean up this project's root directory.
```

### GitHub Copilot (Chat)

Reference the skill file directly or use any trigger phrase:

```
#file:.claude/skills/project-layout-refactor/SKILL.md
Audit and refactor the root directory of this project according to the layout rules.
```

Note: Copilot cannot move files directly. This skill will generate a shell script for you to run.

## What This Skill Does

1. **Rule Loading** — reads layout rules from CLAUDE.md, GEMINI.md, or project config; falls back to DevAI-Hub defaults
2. **Root Inventory** — classifies every root file as Stay / Move / Ambiguous against the loaded rules
3. **Impact Analysis** — finds every reference to each file that will move, across all file types, before touching anything
4. **Safe Move Protocol** — copy → verify → delete (never deletes without confirming the copy succeeded)
5. **Reference Repair** — updates all auto-fixable path references in `.md`, `.py`, `.sh`, `.ps1`, `.bat`, `.json`, `.yaml`, `.toml`, and other text files
6. **Verification** — re-scans for stale references and confirms structural compliance after the refactor

## Standard Layout Rules Reference

These are the DevAI-Hub canonical defaults. Use these when no project-specific rules are declared, or as the baseline when customizing.

| Rule | What | Where | Rationale |
|------|------|-------|-----------|
| Community files | `README.md`, `CHANGELOG.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.gitignore`, `.gitattributes`, `llms.txt` | Project root | GitHub and tooling scan the root for these; moving them breaks discovery |
| AI instruction files | `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.copilot-instructions.md` | Project root | AI assistants read these from root by convention |
| Installer entry points | `install.bat`, `install.sh`, `install.exe`, `*.msi`, `setup.exe` | Project root | Users expect to find and run installers at root |
| Development log | `DEVLOG.md` | `docs/DEVLOG.md` | Project-specific artifact, not a root convention; belongs with other project docs |
| Machine-readable catalogs | `skills.json`, `bundles.json`, `templates.json`, `workflows.json`, `report_data.json` | `data/` | Data files are not source or docs; `data/` makes their purpose clear |
| Scripts and automation | `installer.ps1`, `installer.sh`, `generate_report.py`, build scripts | `scripts/` | Separates runnable tools from project metadata |
| Source code | application code, libraries | `src/` | Industry-standard separation of source from project files |
| Skills catalog source | skill directories (`SKILL.md` files) | `catalog/skills/` | Distinguishes human-readable catalog source from compiled JSON in `data/` |

## File Classification Heuristics

When a file does not match a named rule, use these heuristics to decide where it belongs:

### By Extension

| Extension | Default Destination | Notes |
|-----------|--------------------|-|
| `.json` | `data/` | Unless it is `package.json`, `tsconfig.json`, or other tooling config — those stay at root |
| `.yaml`, `.yml` | `config/` or root | CI/CD configs (`.github/`, `azure-pipelines.yml`) stay at root; app config goes to `config/` |
| `.py`, `.sh`, `.ps1`, `.bat` | `scripts/` | Unless it is a project entry point (`main.py`, `app.py`) — those go to `src/` |
| `.md` | `docs/` | Unless it is a community file (README, CHANGELOG, SECURITY, CODE_OF_CONDUCT) |
| `.toml`, `.cfg`, `.ini` | Root | Build and tool configuration files are conventionally at root |
| `.exe`, `.msi`, `.bat` (named `install*`) | Root | Installer binaries must stay at root |

### By Name Pattern

| Pattern | Default Destination |
|---------|---------------------|
| `DEVLOG*`, `devlog*` | `docs/` |
| `*_catalog.json`, `*_data.json` | `data/` |
| `*report*`, `*output*` | `data/` or `output/` |
| `Makefile`, `Dockerfile`, `docker-compose*.yml` | Root |
| `*.lock` | Root (alongside their package manager config) |

### By Content Type

- **Log files** (entries with dates, status notes) → `docs/`
- **Schema files** (JSON Schema, OpenAPI specs) → `schemas/` or `data/`
- **Generated files** (output of a build step) → `data/` or `output/` (and usually `.gitignore`d)
- **Template files** → `templates/`

## Reference Detection Patterns

Use these grep patterns to find all references to a file that is about to move. Run against the full codebase (not just the root). Replace `DEVLOG\.md` with the escaped filename you are searching for.

### Markdown

```bash
grep -rn "DEVLOG\.md" --include="*.md" .
```

### Python

```bash
grep -rn "DEVLOG\.md" --include="*.py" .
```

### Shell Scripts

```bash
grep -rn "DEVLOG\.md" --include="*.sh" --include="*.bash" .
```

### PowerShell

```bash
grep -rn "DEVLOG\.md" --include="*.ps1" --include="*.psm1" .
```

### JSON / YAML / TOML

```bash
grep -rn "DEVLOG\.md" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.toml" .
```

### All text files at once

```bash
grep -rn "DEVLOG\.md" --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir=".venv" .
```

**Tip**: Use `\.` to escape the dot in regex patterns so it matches a literal period, not any character.

## Safe Move Protocol

Never move a file without following these steps in order. Skipping any step risks data loss.

```
1. Determine destination path
   └─ Create destination directory if it does not exist

2. Copy source → destination
   └─ Verify: file exists at destination AND byte size matches source

3. If verification passes:
   └─ Delete source
   └─ Log: ✓ Moved: source → destination

4. If verification fails:
   └─ Do NOT delete source
   └─ Log error and stop this file's move
   └─ Continue with next file (do not abort entire refactor)
```

**Never use a rename/move operation as an atomic action** when operating across directories — on networked drives or certain filesystems, a move can fail silently. Copy + verify + delete is always safe.

## Reference Fix Patterns

How to update path references in each file type after a file moves.

### Markdown Links

```markdown
# Before
[Development Log](DEVLOG.md)
[DEVLOG](./DEVLOG.md)

# After
[Development Log](docs/DEVLOG.md)
[DEVLOG](./docs/DEVLOG.md)
```

**Rule**: If the link had a `./` prefix, keep it. Replace only the path portion.

### Python String Literals

```python
# Before
path = "DEVLOG.md"
devlog = root / "DEVLOG.md"

# After
path = "docs/DEVLOG.md"
devlog = root / "docs" / "DEVLOG.md"
```

**Rule**: For `pathlib` chains (`root / "X"`), split into multiple segments if the destination has multiple components.

### Shell Variable Assignments

```bash
# Before
DEVLOG="$GIT_ROOT/DEVLOG.md"

# After
DEVLOG="$GIT_ROOT/docs/DEVLOG.md"
```

### JSON Path Strings

```json
{ "devlog": "DEVLOG.md" }
→
{ "devlog": "docs/DEVLOG.md" }
```

### PowerShell

```powershell
# Before
$devlog = Join-Path $root "DEVLOG.md"

# After
$devlog = Join-Path $root "docs\DEVLOG.md"
```

## Platform-Specific Tool Usage

### Claude Code

- Use `Glob` to list root files (do not use Bash `ls`)
- Use `Grep` for reference scanning (do not use Bash `grep`)
- Use `Read` before any `Edit`; use `Edit` for targeted fixes (not `Write`)
- Use `Bash` only for the copy+verify+delete sequence and `git status`

### Codex (OpenAI CLI)

- Use the `computer` tool for file reads and writes
- Run grep via shell for reference scanning
- Prefer shell `cp` + `test -s` for copy+verify, then `rm` for delete

### Gemini CLI

- Use `read_file` / `write_file` for file operations
- Use `run_shell_command` for grep-based reference scanning
- Apply targeted edits with `replace_in_file` rather than full rewrites

### GitHub Copilot (Chat / Workspace)

- Use `#file:` to reference specific files for reading
- Use `@workspace /search` for codebase-wide reference scanning
- Copilot cannot move files directly: generate a shell script (`move-files.sh` or `move-files.ps1`) for the user to run, then repair references in the files you can edit

## Quality Checklist

Before marking the refactor complete:

- [ ] Layout rules loaded and confirmed by user
- [ ] Every root file classified (no Ambiguous items left unresolved)
- [ ] Impact analysis run for all files that will move
- [ ] User explicitly approved the plan before any changes were made
- [ ] All file moves completed with copy → verify → delete protocol
- [ ] All auto-fixable references updated
- [ ] Stale reference scan returns zero hits
- [ ] Root directory matches the declared layout rules
- [ ] `git status` shows no unintended deletions or modifications
- [ ] Manual-review items documented and handed off to user

## Related Skills

- `documentation-consistency` — audit documentation accuracy after a layout change
- `version-upgrade` — update version references and CHANGELOG as part of a release that includes layout changes
- `code-commit-workflow` — commit the layout refactor with a clear, structured commit message

---

**Version**: 1.0.0
**Last Updated**: March 2026


### Iterative Refinement Strategy

This skill is optimized for an iterative approach:
1. **Execute**: Classify files, run impact analysis, execute approved moves and reference fixes.
2. **Review**: Re-scan for stale references; check structural compliance.
3. **Refine**: If stale references remain, apply targeted fixes and re-scan.
4. **Loop**: Continue until the stale-reference scan is clean (up to 3 iterations).
