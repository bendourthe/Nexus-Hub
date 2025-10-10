# Python Context Analysis

## Objective
Establish comprehensive understanding of the project before conducting detailed code review. This phase gathers context about purpose, architecture, dependencies, and current state to inform all subsequent review activities.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/context_analysis/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/context_analysis/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Analysis Checklist

### Project Understanding

- [ ] Project purpose and target audience identified

- [ ] Core features and use cases documented

- [ ] Development stage assessed (prototype, production, legacy)

- [ ] Key stakeholders and maintainers identified

- [ ] Project documentation reviewed (README, CONTRIBUTING, docs/)

### Architecture & Structure

- [ ] Entry points and main modules mapped

- [ ] Package/module organization evaluated

- [ ] Design patterns identified (MVC, repository, factory, etc.)

- [ ] Configuration management approach documented

- [ ] Environment-specific settings catalogued

### Dependency Analysis

- [ ] Direct dependencies listed with versions (requirements.txt, pyproject.toml)

- [ ] Development dependencies separated from production

- [ ] Outdated packages identified

- [ ] Security vulnerabilities in dependencies checked

- [ ] License compatibility verified

### Build & Deployment

- [ ] Build process documented (setup.py, pyproject.toml, Makefile)

- [ ] Test execution approach understood

- [ ] CI/CD pipelines identified (GitHub Actions, GitLab CI, Jenkins)

- [ ] Deployment targets documented (containers, serverless, traditional)

- [ ] Environment variables and secrets management reviewed

### Codebase Metrics

- [ ] Lines of code measured (total, per module)

- [ ] Cyclomatic complexity assessed

- [ ] Module coupling and cohesion evaluated

- [ ] Code duplication percentage calculated

- [ ] Comment density analyzed

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Project Context Analysis

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/context_analysis"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Analysis Protocol

Please perform a comprehensive context analysis of this Python project following this protocol:

## Phase 1: Project Discovery

1. **Identify Project Fundamentals**
   - Read and summarize README.md and primary documentation
   - Determine project purpose, target audience, and key features
   - Identify development stage (prototype/production/legacy)
   - List primary maintainers and stakeholders

2. **Map Repository Structure**
   - Identify all source directories (src/, app/, lib/, etc.)
   - Locate test directories and test frameworks used
   - Find configuration files (pyproject.toml, setup.py, setup.cfg, etc.)
   - Document documentation locations (docs/, wiki, external)

## Phase 2: Architecture Understanding

1. **Entry Points & Core Modules**
   - Identify main entry points (__main__.py, cli.py, app.py, etc.)
   - Map core business logic modules
   - Document public API surface
   - Identify internal vs external interfaces

2. **Design Patterns & Architecture**
   - Identify architectural style (monolithic, modular, microservices)
   - Document design patterns in use (factory, singleton, strategy, etc.)
   - Map data flow through the application
   - Identify configuration and settings management approach

3. **Module Dependencies**
   - Create dependency graph between internal modules
   - Identify circular dependencies
   - Assess module coupling (tight/loose)
   - Evaluate separation of concerns

## Phase 3: Dependency Analysis

1. **Dependency Inventory**
   - List all dependencies from requirements.txt, pyproject.toml, Pipfile
   - Separate production vs development dependencies
   - Document Python version requirements
   - Identify platform-specific dependencies

2. **Dependency Health Check**
   ```bash
   # Check for outdated packages
   pip list --outdated

   # Check for security vulnerabilities
   pip-audit
   # or
   safety check
   ```

3. **License & Compatibility**
   - List licenses for all dependencies
   - Flag potential license conflicts
   - Identify deprecated or unmaintained packages

## Phase 4: Build & Deployment

1. **Build System**
   - Document build configuration (setup.py, pyproject.toml)
   - Identify build tools (setuptools, poetry, flit, hatch)
   - Review packaging metadata (name, version, author, etc.)
   - Check for build scripts or Makefiles

2. **Test Infrastructure**
   - Identify testing frameworks (pytest, unittest, nose)
   - Document test execution commands
   - Review test configuration files (pytest.ini, tox.ini)
   - Assess test organization and structure

3. **CI/CD Pipeline**
   - Locate CI/CD configuration (.github/workflows, .gitlab-ci.yml, etc.)
   - Document automated checks (linting, testing, security scans)
   - Review deployment automation
   - Identify quality gates and merge requirements

4. **Environment Management**
   - Document environment variables and configuration
   - Review secrets management approach
   - Identify environment-specific settings (dev/staging/prod)
   - Check for .env files or environment documentation

## Phase 5: Codebase Metrics

1. **Size & Complexity Metrics**
   ```bash
   # Lines of code
   find . -name "*.py" | xargs wc -l

   # Cyclomatic complexity
   radon cc . -a -nb

   # Maintainability index
   radon mi . -nb
   ```

2. **Quality Indicators**
   - Calculate code-to-comment ratio
   - Measure average function/method length
   - Identify large files (>500 lines)
   - Count TODO/FIXME/HACK comments

3. **Duplication Analysis**
   ```bash
   # Check for code duplication
   pylint --disable=all --enable=duplicate-code .
   ```

## Phase 6: Documentation Review

1. **Code Documentation**
   - Assess docstring coverage (modules, classes, functions)
   - Review docstring format (Google, NumPy, reStructuredText)
   - Check type hints coverage
   - Evaluate inline comment quality

2. **Project Documentation**
   - Review README completeness
   - Check for CONTRIBUTING.md
   - Assess CHANGELOG.md or release notes
   - Review architecture documentation

## Output Format

Please provide a comprehensive context report with the following structure:

### Executive Summary

- **Project Name**: [name]

- **Purpose**: [1-2 sentence description]

- **Stage**: [prototype/production/legacy]

- **Python Version**: [version requirements]

- **Architecture**: [architectural style]

### Project Structure
```
project/
├── [key directories and their purposes]
├── [entry points]
└── [configuration files]
```

### Architecture Overview

- **Design Patterns**: [patterns identified]

- **Module Organization**: [brief description]

- **Key Dependencies**: [critical external packages]

- **Configuration Approach**: [how settings are managed]

### Dependency Summary
| Package | Version | Purpose | Status | Security |
|---------|---------|---------|--------|----------|
| [name] | [version] | [usage] | [current/outdated] | [safe/vulnerable] |

### Build & Deployment

- **Build System**: [tool and configuration]

- **Test Framework**: [framework and execution]

- **CI/CD**: [platform and key workflows]

- **Deployment**: [target environments]

### Codebase Metrics

- **Total Lines**: [number] (excluding tests)

- **Average Complexity**: [cyclomatic complexity score]

- **Maintainability**: [index score]

- **Duplication**: [percentage]

- **Documentation**: [docstring coverage %]

### Key Findings
1. **Strengths**: [positive observations]
2. **Concerns**: [potential issues to investigate]
3. **Dependencies**: [outdated or vulnerable packages]
4. **Documentation**: [gaps or areas needing improvement]

### Recommendations for Review Focus
Based on this context, the following review areas should be prioritized:
1. [Area 1] - [reason]
2. [Area 2] - [reason]
3. [Area 3] - [reason]

### Next Steps

- [ ] Proceed with code quality review

- [ ] Conduct security audit (especially if vulnerable dependencies found)

- [ ] Perform performance analysis

- [ ] Review test coverage and quality

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/context_analysis/analysis_scripts
mkdir -p ${OUTPUT_DIR}/context_analysis/supporting_data
```

**Save files as follows**:

- Main report → `review/context_analysis/context_analysis_report.md`

- Findings data → `review/context_analysis/context_analysis_findings.json`

- Analysis scripts → `review/context_analysis/analysis_scripts/`

- Supporting data → `review/context_analysis/supporting_data/`

## Notes

- Save this context report - it will inform all subsequent review phases

- Flag any critical issues discovered during context gathering

- Update dependency vulnerabilities before detailed code review

- Use this as baseline for measuring improvement over time
~~~
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
