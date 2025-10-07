# Phase 1: Context & Architecture Review

## Objective
Understand the project structure, architecture decisions, and overall design before diving into code-level details.

## Review Checklist

### Project Structure Compliance
- [ ] Follows standard Python application structure
- [ ] Virtual environment (`.venv/`) properly configured
- [ ] Source code organized under `src/` directory
- [ ] Entry point (`main.py`) clearly defined
- [ ] Core logic properly separated in `src/core/`
- [ ] Tests organized in `tests/` directory
- [ ] GUI components (if applicable) in `gui/` directory

### Essential Documentation Files
- [ ] `README.md` present and complete
  - Version number in header
  - "What's New" section
  - Clear overview (2-3 sentences)
  - Features list
  - Installation instructions
  - Usage examples
  - Testing instructions
- [ ] `CHANGELOG.md` follows Keep a Changelog format
  - Unreleased section present
  - Semantic versioning used correctly
  - Changes categorized (Added/Changed/Fixed/Removed)
- [ ] `DEVLOG.md` tracks development history
  - Current task list (High/Medium/Low priority)
  - Project architecture decisions
  - Implementation challenges documented
  - Technical decisions recorded
- [ ] `pyproject.toml` configured correctly
  - Version matches CHANGELOG
  - Author information complete
  - Dependencies listed
  - Development dependencies in optional-dependencies
  - Black, isort, mypy configurations present
- [ ] `requirements.txt` up to date
- [ ] `.gitignore` properly configured
  - Virtual environments ignored
  - Cache files ignored
  - OS-specific files ignored
  - IDE configs ignored

### Architecture Assessment
- [ ] Clear separation of concerns
- [ ] Component boundaries well-defined
- [ ] Data flow patterns documented
- [ ] External dependencies identified
- [ ] Integration points clear
- [ ] Design patterns appropriately applied

### Version Consistency
- [ ] Version in `pyproject.toml` matches `CHANGELOG.md`
- [ ] Version in `README.md` matches other files
- [ ] Semantic versioning correctly applied

## Detailed Review Prompt

```
Please perform a comprehensive context and architecture review of this Python project:

**Project Structure Analysis:**
1. Verify the directory structure follows the standard Python application layout:
   - .venv/ for virtual environment
   - src/ for application source code
   - src/main.py as entry point
   - src/core/ for core logic
   - gui/ for GUI components (if applicable)
   - tests/ for testing suite
   - docs/ for documentation

2. Check for essential files and their completeness:
   - README.md (with version, overview, features, installation, usage)
   - CHANGELOG.md (Keep a Changelog format, semantic versioning)
   - DEVLOG.md (task lists, architecture decisions, challenges)
   - pyproject.toml (correct configuration, version consistency)
   - requirements.txt (up to date with actual dependencies)
   - .gitignore (comprehensive ignore patterns)

3. Analyze version consistency:
   - Compare versions across pyproject.toml, CHANGELOG.md, and README.md
   - Verify semantic versioning is correctly applied
   - Check that CHANGELOG entries match the current version

**Architecture Evaluation:**
1. Assess overall system design:
   - Are components clearly separated with defined boundaries?
   - Is there clear separation between core logic, utilities, and interfaces?
   - Are design patterns appropriately applied?

2. Evaluate data flow:
   - How does data move through the system?
   - Are dependencies clearly identified?
   - Are integration points well-defined?

3. Review architectural decisions:
   - Check DEVLOG.md for documented architecture rationale
   - Verify decisions align with project requirements
   - Identify any architectural technical debt

**Deliverables:**
Provide a structured report covering:
- Project structure compliance score (pass/needs improvement)
- Documentation completeness assessment
- Version consistency verification
- Architecture strengths and concerns
- Recommended improvements with priority levels
```

## Expected Outcomes

### Pass Criteria
- All essential files present and complete
- Version consistency across all files
- Clear architectural documentation
- Proper project structure following standards

### Common Issues to Flag
- Missing or incomplete documentation files
- Version mismatches between files
- Unclear architectural decisions
- Non-standard project structure
- Missing .gitignore or incomplete ignore patterns
- Outdated requirements.txt

## Next Steps
After completing this phase, proceed to Phase 2: Code Quality & Standards Review.
