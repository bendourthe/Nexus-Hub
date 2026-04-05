---
description: Bootstrap a new project with CLAUDE.md configuration, directory scaffolding, .gitignore, README, DEVLOG, and CHANGELOG generation.
---
# Project Setup Assistant

Bootstrap a new project with CLAUDE.md configuration, directory scaffolding, a comprehensive .gitignore, and generated README, DEVLOG, and CHANGELOG.

## Phase 1: Project Information Gathering

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

## Phase 2: CLAUDE.md Configuration

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

### Example Output Format

```markdown
# Project: [Project Name]

## Overview
[Generated 2-4 sentence description that clearly explains what the project does,
its primary purpose, and who it's for. Written in a professional, concise style.]
```

## Phase 3: Directory Scaffolding

Create the following project directories if they do not already exist. Add a `.gitkeep` file inside each empty directory so git tracks them.

### Core directories (always created)

| Directory | Purpose |
|-----------|---------|
| `src/` | Primary source code |
| `tests/` | Test suites (unit, integration, e2e) |
| `docs/` | Documentation and guides |
| `configs/` | Project configuration files (linter configs, CI templates, environment configs) |
| `scripts/` | Build, deploy, and utility scripts |

### Supporting directories (always created)

| Directory | Purpose |
|-----------|---------|
| `assets/` | Static assets (images, fonts, icons) |
| `examples/` | Usage examples and sample code |
| `lib/` | Shared libraries and internal packages |

### Reporting

After creating directories, report a summary to the user:
- List which directories were **created** (new)
- List which directories **already existed** (skipped)

## Phase 4: Generate .gitignore

Generate a comprehensive `.gitignore` file organized into clearly commented sections.

### Pre-check

- If a `.gitignore` already exists, ask the user: **Merge** (append missing patterns), **Overwrite** (replace entirely), or **Skip**
- If no `.gitignore` exists, create one from scratch

### Tech stack detection

Auto-detect the project's tech stack by checking:
1. The Tech Stack section of CLAUDE.md (just updated in Phase 2)
2. Presence of package files: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `*.csproj`, `pom.xml`, `build.gradle`

Include **all universal sections** plus **only the language-specific sections** that match the detected stack.

### Universal sections (always included)

```gitignore
# OS metadata
.DS_Store
Thumbs.db
Desktop.ini
._*

# IDE and editor
.idea/
.vscode/
*.swp
*.swo
*~
.project
.classpath
.settings/

# Logs and temp
*.log
logs/
temp/
tmp/

# Secrets and environment
.env
.env.*
!.env.example
*.pem
*.key
*.p12
credentials.json
secrets.json

# Coverage and test output
coverage/
.nyc_output/
htmlcov/
TEST*.xml

# Build artifacts
dist/
build/
out/

# Archives
*.zip
*.tar.gz
*.rar

# Large media
*.mp4
*.avi
*.mov
*.wmv
*.flv
*.tiff

# Claude Code settings
/.claude/
settings.local.json
```

### Language-specific sections (include only if detected)

**Node.js / TypeScript** (detected via `package.json`):
```gitignore
# Node.js
node_modules/
.next/
.nuxt/
*.tsbuildinfo
.npm
.yarn/
.pnp.*
```

**Python** (detected via `pyproject.toml`, `setup.py`, `requirements.txt`, or `*.py` files):
```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
*.egg-info/
.mypy_cache/
.ruff_cache/
.pytest_cache/
```

**Go** (detected via `go.mod`):
```gitignore
# Go
vendor/
```

**Rust** (detected via `Cargo.toml`):
```gitignore
# Rust
target/
```

**Java** (detected via `pom.xml`, `build.gradle`):
```gitignore
# Java
*.class
*.jar
*.war
target/
```

**C# / .NET** (detected via `*.csproj`, `*.sln`):
```gitignore
# .NET
bin/
obj/
*.suo
*.user
```

## Phase 5: Generate README

1. Check if `README.md` already exists
   - If yes, ask the user: **Regenerate** or **Skip**
   - If no, proceed
2. Invoke the `/generate-readme` workflow to produce a production-quality README from codebase analysis
3. Note to the user that this is running as part of project setup

## Phase 6: Generate DEVLOG

1. Check if `docs/DEVLOG.md` already exists
   - If yes, ask the user: **Regenerate** or **Skip**
   - If no, proceed
2. Invoke the `/generate-devlog` workflow to produce a development log from git history
3. Note to the user that this is running as part of project setup

## Phase 7: Generate CHANGELOG

1. Check if `CHANGELOG.md` already exists
   - If yes, ask the user: **Regenerate** or **Skip**
   - If no, proceed
2. Invoke the `/generate-changelog` workflow to produce a changelog from git tags and commits
3. Note to the user that this is running as part of project setup

## Phase 8: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1. **Analyze**: Review all generated artifacts:
   - Is the CLAUDE.md complete and accurate?
   - Were all directories created successfully?
   - Is the .gitignore comprehensive for the detected tech stack?
   - Does the README accurately reflect the project?
   - Are the DEVLOG and CHANGELOG properly formatted?
2. **Refine**:
   - Fix any issues found
   - Add missing components
3. **Stop**:
   - If you are confident all artifacts are excellent
   - OR if you have reached the maximum iteration count

## Phase 9: Generate Implementation Plan (Optional)

After all prior phases are complete, ask the user:

> "Would you like to generate a v0.1.0 implementation plan for this project?
> This will guide you through a short discovery interview and produce
> `docs/v0.1.0/implementation-plan.md` — a phased build roadmap where every
> sub-task includes a ready-to-use prompt for a future Claude Code session.
> [Y]es / [N]o"

- If the user answers **Yes** (or Y): invoke `/generate-implementation-plan`
- If the user answers **No** (or N): skip this phase and conclude setup

## Guidelines

- Keep all descriptions factual and clear
- Focus on WHAT it does and WHY it's useful
- Avoid buzzwords and excessive adjectives
- Match the technical level to the target users
- If the project already has content in CLAUDE.md, preserve other sections
- Never overwrite existing files without explicit user approval
- Report progress to the user after each phase completes
