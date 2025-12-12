# Import Skills from Catalog

Help the user import skills from the ai-templates skills catalog into their project.

## Instructions

You are helping the user import Claude Code skills from the ai-templates repository into their project. Follow these steps:

### Step 1: Locate the Skills Catalog

Ask the user: "Where is your ai-templates skills catalog located? Please provide the path to the `catalogs/claude_skills/` directory."

**Common locations:**
- `~/ai-templates/catalogs/claude_skills/`
- `../ai-templates/catalogs/claude_skills/`
- A custom path the user specifies

Wait for the user's response before proceeding.

### Step 2: Verify the Path

Once the user provides the path, verify it exists and contains skills by looking for SKILL.md files in subdirectories.

If the path is invalid, ask the user to provide a correct path.

### Step 3: Present Available Skills by Category

Display the available skills organized by category:

```markdown
## Available Skills

### Tests Generation (8 skills)
- [ ] `test-structure` - Set up testing infrastructure and framework
- [ ] `unit-tests` - Generate comprehensive unit tests (FIRST principles, AAA pattern)
- [ ] `test-cases` - Create integration and end-to-end test scenarios
- [ ] `mocks-fixtures` - Build test doubles, data factories, and fixtures
- [ ] `performance-testing` - Implement load testing and benchmarking
- [ ] `cicd-integration` - Configure test automation in CI/CD pipelines
- [ ] `code-coverage` - Analyze and improve test coverage
- [ ] `mutation-testing` - Validate test quality through mutation testing

### Code Review (6 skills)
- [ ] `context-analysis` - First phase: understand project structure and architecture
- [ ] `code-quality` - Evaluate style, maintainability, and best practices
- [ ] `security-review` - Identify vulnerabilities and OWASP Top 10 issues
- [ ] `performance-review` - Profile performance and detect bottlenecks
- [ ] `testing-review` - Assess test coverage and testing strategy
- [ ] `final-report` - Consolidate findings into prioritized report

### Code Cleanup (7 skills)
- [ ] `python-cleanup` - Remove dead code, fix PEP 8, add type hints
- [ ] `javascript-cleanup` - Remove unused exports, modernize to ES6+
- [ ] `java-cleanup` - Update deprecated APIs, apply modern patterns
- [ ] `csharp-cleanup` - Modernize async, optimize LINQ
- [ ] `go-cleanup` - Apply gofmt, improve error handling
- [ ] `c-cleanup` - Fix memory leaks, apply MISRA guidelines
- [ ] `cpp-cleanup` - Modernize to C++17/20, use smart pointers

### Documentation (6 skills)
- [ ] `docstrings` - Generate function/class docstrings (JSDoc, PyDoc, etc.)
- [ ] `strategic-comments` - Add high-value comments for complex logic
- [ ] `user-documentation` - Create README, guides, and tutorials
- [ ] `technical-documentation` - Generate architecture docs and ADRs
- [ ] `api-documentation` - Create OpenAPI/Swagger specifications
- [ ] `sbom-generation` - Generate Software Bill of Materials

### Compliance (8 skills)
- [ ] `soc2-compliance` - Implement SOC 2 Type II controls
- [ ] `iso27001-compliance` - Implement ISO 27001:2022 ISMS controls
- [ ] `iso42001-ai-governance` - Implement ISO 42001:2023 AI Management
- [ ] `nist-ai-rmf` - Implement NIST AI Risk Management Framework
- [ ] `pci-dss-compliance` - Implement PCI-DSS v4.0 requirements
- [ ] `gdpr-compliance` - Implement GDPR data protection requirements
- [ ] `ccpa-compliance` - Implement CCPA/CPRA privacy requirements
- [ ] `ai-agent-governance` - Implement 4 Pillars Framework for AI agents

### Project Setup (4 skills)
- [ ] `init-python-project` - Initialize Python project with pyproject.toml
- [ ] `init-javascript-project` - Initialize JS/TS project with package.json
- [ ] `init-java-project` - Initialize Java project with Maven/Gradle
- [ ] `init-csharp-project` - Initialize C#/.NET project

### Workflow (5 skills)
- [ ] `plan-before-code` - Structured planning before coding
- [ ] `test-driven-development` - TDD with red-green-refactor cycle
- [ ] `code-commit-workflow` - Structured Git commit workflow
- [ ] `debug-with-logs` - Strategic debugging with logging
- [ ] `create-custom-command` - Create custom slash commands

### Security (3 skills)
- [ ] `dependency-security-audit` - Scan dependencies for CVEs
- [ ] `pre-commit-checklist` - Validate code before committing
- [ ] `licensing-compliance` - Check dependency licenses
```

### Step 4: Ask User Selection

Ask the user: "Which skills would you like to import? You can:
1. Type **all** to import all 47 skills
2. Type a **category name** (e.g., 'workflow', 'security') to import all skills in that category
3. Type **specific skill names** separated by commas (e.g., 'unit-tests, security-review, plan-before-code')
4. Type **recommended** for a curated selection of essential skills"

**Recommended Skills (13 essential skills):**
- `plan-before-code` - Planning methodology
- `test-driven-development` - TDD workflow
- `code-commit-workflow` - Git best practices
- `unit-tests` - Test generation
- `code-quality` - Code review
- `security-review` - Security assessment
- `java-cleanup` - Code cleanup for Java
- `docstrings` - Documentation
- `user-documentation` - README/guides
- `dependency-security-audit` - Security scanning
- `pre-commit-checklist` - Pre-commit validation
- `debug-with-logs` - Debugging practices
- `test-structure` - Test infrastructure

Wait for the user's response.

### Step 5: Confirm Selection

Before importing, show the user:
```markdown
## Import Summary

**Skills to import:** X skills
**Categories:** [list categories]
**Estimated size:** ~Y KB

Skills:
1. skill-name-1 (category)
2. skill-name-2 (category)
...

**Target directory:** .claude/skills/

Proceed with import? (yes/no)
```

Wait for confirmation.

### Step 6: Execute Import

For each selected skill, copy the skill directory from the catalog to the project's `.claude/skills/` directory, organizing by category:

```
.claude/skills/
├── tests-generation/
│   ├── unit-tests/SKILL.md
│   └── test-structure/SKILL.md
├── code-review/
│   └── security-review/SKILL.md
├── workflow/
│   ├── plan-before-code/SKILL.md
│   └── code-commit-workflow/SKILL.md
...
```

### Step 7: Report Results

After import, display:
```markdown
## Import Complete

**Successfully imported:** X skills
**Location:** .claude/skills/

### Imported Skills by Category
- **workflow/** (3 skills): plan-before-code, code-commit-workflow, debug-with-logs
- **security/** (2 skills): dependency-security-audit, pre-commit-checklist
...

### How to Use
Skills are automatically activated based on task context. You can also reference them:
- "Use the security-review skill to check this code"
- "Apply the plan-before-code skill before implementing"

### Next Steps
1. Run `/update-documentation` to verify documentation consistency
2. Start using skills by mentioning them in your requests
```

## Skill Category Paths

Reference for copying:
```
tests-generation/     → .claude/skills/tests-generation/
code-review/          → .claude/skills/code-review/
code-cleanup/         → .claude/skills/code-cleanup/
documentation/        → .claude/skills/documentation/
compliance/           → .claude/skills/compliance/
project-setup/        → .claude/skills/project-setup/
workflow/             → .claude/skills/workflow/
security/             → .claude/skills/security/
```

## Guidelines

- Preserve the directory structure (category/skill-name/SKILL.md)
- Don't overwrite existing skills unless the user confirms
- If a skill already exists, ask if the user wants to update it
- Validate each SKILL.md file has proper YAML frontmatter
- Report any errors during import clearly
