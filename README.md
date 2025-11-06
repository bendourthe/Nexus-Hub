# AI Development Templates

**Version 0.2.8** | Released November 6, 2025

This repository contains comprehensive templates and standardized prompts to enhance AI-assisted software development. Complete multi-language support across 7 programming languages with 178 production-ready templates, **48 Claude Code Skills**, comprehensive 8-phase testing methodology, one-command installation, web-based discovery, and comprehensive automation.

---

## 🎯 New to This Repository? Start Here!

**→ [📖 Quick Start Guide: Set Up a New Project in 5 Minutes](QUICKSTART.md) ←**

Learn how to:
- Create a new project with Claude Code superpowers
- Install skills with one command
- Generate project structure, CLAUDE.md, and documentation automatically
- Start developing with 48 production-ready skills at your fingertips

---

## 🎉 What's New in Version 0.2.8

### 🧪 NEW: Complete 8-Phase Testing Methodology
- **Unit Tests Phase** ([test_development/unit_tests/](test_development/unit_tests/)): Foundational unit testing with FIRST principles
  - 7 language templates (Python, JavaScript, Java, C#, Go, C, C++)
  - FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)
  - AAA pattern (Arrange-Act-Assert) with 20-30+ examples per language
  - Testing all component types: functions, classes, async, decorators, generators, context managers
  - Anti-patterns guide with remediation strategies
  - Speed requirements: <1 second per test (target: <100ms)

- **Reward Hacking Phase** ([test_development/reward_hacking/](test_development/reward_hacking/)): Test quality validation through mutation testing
  - 7 language templates with mutation testing setup
  - Detects "reward hacking" where tests pass without validating functionality
  - 7-phase validation covering ALL previous test phases
  - Mutation testing tools: mutmut, Stryker, PITest, Stryker.NET, go-mutesting, mull
  - 15-20 weak vs. strong test examples per language
  - Quality metrics: >80% mutation score, 100% test independence
  - Remediation action plans with continuous monitoring

### 🔬 Testing Framework Enhancements
- **Complete 8-Phase Workflow**: From infrastructure to quality validation
- **Updated all phase READMEs** with cross-references to new phases
- **Quality Targets**: Mutation score >80%, test speed <1s, error coverage >80%
- **Detection Patterns**: Tautological tests, weak assertions, over-mocking, happy-path-only testing

### 📊 Stats
- **178 Production-Ready Templates** (up from 162)
- **16 New Testing Files**: 8 Unit Tests + 8 Reward Hacking
- **~25,800 Lines**: Of comprehensive testing guidance
- **150+ Code Examples**: Across all 7 languages
- **8-Phase Testing**: Complete methodology from setup to validation
- **48 Claude Code Skills** across 12 categories
- **7 Languages Supported**: Python, JavaScript, Java, C#, Go, C, C++

[View Changelog](CHANGELOG.md) | [View Development Log](DEVLOG.md) | [Browse Skills Online](https://bdourthe.github.io/ai_templates/)

---

## 📁 Repository Structure

This repository provides standardized templates for AI-enhanced software development:

### [Agent Prompts for AI-Assisted Coding](agent_prompts/)
- **Autonomous agents**: For independent coding agents like Claude Code
- **Interactive assistants**: For collaborative coding with GitHub Copilot, Cursor, Windsurf
- **Claude Code Skills**: 48 production-ready skills ([Browse Skills](https://bdourthe.github.io/ai_templates/))
- **Platform-specific optimization**: Tailored prompts for different AI platforms
- **Token-optimized versions**: Comprehensive vs condensed variants

### [Tools](tools/) - NEW!
- **[Skills Catalog Builder](tools/build_skills_catalog.py)**: Generate skills.json metadata
- **[Skill Installer](tools/install_skill.py)**: CLI tool for one-command skill installation
- **[Tool Documentation](tools/README.md)**: Complete usage guide

### [Integrations](integrations/) - NEW!
- **[MCP Configurations](integrations/)**: Connect Claude to external services
- **GitHub, GitLab**: Repository and CI/CD integration
- **Databases**: PostgreSQL, MySQL, MongoDB support
- **Cloud Services**: AWS, Azure, GCP configurations
- **AI Services**: OpenAI, Anthropic integration

### [Hooks](hooks/) - NEW!
- **[Automation Workflows](hooks/)**: Git hooks and quality gates
- **Pre-commit**: Quality checks before commits
- **Pre-push**: Comprehensive validation before push
- **Post-commit**: Auto-documentation updates
- **CI/CD Integration**: Hooks for build pipelines

### [Code Cleanup Templates](code_cleanup/)
- **Structured cleanup processes**: Comprehensive deep codebase review
- **Quality assurance standards**: Consistent cleanup process
- **Security and performance focus**: Critical non-functional requirements
- **Educational feedback**: Learn from cleanup reports

### [Code Review Templates](code_review/)
- **Structured review processes**: Comprehensive checklists
- **Quality assurance standards**: Consistent review patterns
- **Security and performance focus**: Critical analysis
- **Educational feedback**: Learn from reviews

### [Test Development Templates](test_development/)
- **Comprehensive testing frameworks**: Complete test structures
- **Test automation**: Automated test generation
- **Quality metrics**: Coverage and effectiveness
- **Performance testing**: Load and stress tests

### [Documentation Templates](documentation/)
- **Code-level documentation**: Docstrings and strategic comments
- **User documentation**: README files and guides
- **Technical documentation**: Architecture and design
- **API documentation**: Complete API reference
- **SBOM documentation**: Security and compliance

## 🚀 Getting Started

### Setting Up a New Project with Claude Code (Recommended)

**Complete setup in 5 minutes to supercharge your development with Claude Code!**

#### Step 1: Create Your Project Repository

```bash
# Create and clone your new project
mkdir my-awesome-project
cd my-awesome-project
git init
```

#### Step 2: Clone AI Templates Repository (Temporary)

```bash
# Clone ai_templates to a temporary location
cd ..
git clone https://github.com/bdourthe/ai_templates.git
```

#### Step 3: Install Skills into Your Project

```bash
# Install essential skills to your project
cd ai_templates

# Install critical workflow skills (RECOMMENDED START)
python tools/install_skill.py --priority CRITICAL --destination ../my-awesome-project

# Install project initialization skill for your language
python tools/install_skill.py --skill init-python-project --destination ../my-awesome-project
# Or: --skill init-javascript-project / init-java-project / init-csharp-project

# Install code review suite (HIGHLY RECOMMENDED)
python tools/install_skill.py --category "Code Review" --destination ../my-awesome-project

# Optional: Install all skills for complete power
python tools/install_skill.py --all --destination ../my-awesome-project
```

#### Step 4: Initialize Your Project with Claude Code

```bash
# Go back to your project
cd ../my-awesome-project

# Start Claude Code and use the skills you just installed!
claude

# Then in Claude Code, run:
"Use the init-python-project skill to create 'my-awesome-project'"
"Use the create-claude-md skill to configure this project"
```

#### Step 5: Verify Setup

Your project should now have:
```
my-awesome-project/
├── .claude/
│   └── skills/              # All installed skills
├── CLAUDE.md                # Project configuration (generated by skill)
├── src/                     # Source code (generated by init skill)
├── tests/                   # Test infrastructure
├── pyproject.toml           # Project configuration
├── README.md                # Documentation
└── .gitignore              # Git ignore rules
```

#### Step 6: Start Developing!

```bash
# In Claude Code, leverage your skills:
"Use the plan-before-code skill to design the authentication feature"
"Use the test-driven-development skill to implement user registration"
"Use the code-review-security skill to audit the code"
"Use the generate-api-docs skill to document the API"
```

#### Step 7: Clean Up (Optional)

```bash
# Remove the temporary ai_templates clone
cd ..
rm -rf ai_templates
```

---

### Quick Reference: Common Setup Scenarios

#### Scenario 1: Python Web Application
```bash
python tools/install_skill.py --priority CRITICAL --destination ../my-project
python tools/install_skill.py --skill init-python-project --destination ../my-project
python tools/install_skill.py --category "Code Review" --destination ../my-project
python tools/install_skill.py --category Documentation --destination ../my-project
```

#### Scenario 2: JavaScript/React Application
```bash
python tools/install_skill.py --priority CRITICAL --destination ../my-project
python tools/install_skill.py --skill init-javascript-project --destination ../my-project
python tools/install_skill.py --skill cleanup-javascript --destination ../my-project
python tools/install_skill.py --category Testing --destination ../my-project
```

#### Scenario 3: Existing Project (Add Claude Code Support)
```bash
# Navigate to your existing project
cd my-existing-project

# Install skills directly
python ../ai_templates/tools/install_skill.py --priority CRITICAL
python ../ai_templates/tools/install_skill.py --skill create-claude-md

# Then in Claude Code:
"Use the create-claude-md skill to configure this existing project"
```

#### Scenario 4: Team Project with Standardization
```bash
# Install comprehensive quality tooling
python tools/install_skill.py --category workflow --destination ../team-project
python tools/install_skill.py --category "Code Review" --destination ../team-project
python tools/install_skill.py --category security --destination ../team-project
python tools/install_skill.py --skill pre-commit-checklist --destination ../team-project

# Configure project standards
cd ../team-project
claude
"Use the create-claude-md skill with team coding standards"
```

---

### Alternative: Browse and Install from Web

**Don't want to use command line?**

1. Visit [AI Templates Skills Browser](https://bdourthe.github.io/ai_templates/)
2. Browse and search for skills you need
3. Copy installation commands for each skill
4. Run commands with `--destination` flag pointing to your project

---

### Installing Skills to Existing Projects

**Already have a project and want to add Claude Code skills?**

```bash
# Option 1: Install from cloned ai_templates
cd /path/to/ai_templates
python tools/install_skill.py --skill plan-before-code --destination /path/to/your-project

# Option 2: Install from anywhere using --repo flag
python install_skill.py --skill plan-before-code --destination /path/to/your-project --repo /path/to/ai_templates
```

---

### Exploring Available Skills

**Before installing, explore what's available:**

```bash
# List all skills with descriptions
python tools/install_skill.py --list

# Show all categories
python tools/install_skill.py --categories

# Get detailed info about a specific skill
python tools/install_skill.py --info plan-before-code

# Filter by priority
python tools/install_skill.py --list --priority CRITICAL
```

---

### [Agent Prompts](agent_prompts/)

#### Platform Tier Selection 
- `autonomous_agents/` for Claude Code and Codex CLI
- `coding_assistants/` for GitHub Copilot, Cursor, and Windsurf

#### Coding Language Selection
Navigate to appropriate language folder (currently `python/`)

#### Version Selection 
- Comprehensive (~35k tokens) for complex projects
- Condensed (15k-20k tokens) for efficiency and speed

#### AI platform Configuration

##### Coding Assistants
- **GitHub Copilot**: Create `.github/copilot-instructions.md` in your workspace and replace content with condensed or comprehensive template.
- **Cursor**: Go to File > Preferences > Cursor Settings > Rules & Memories (tab on the left panel) > User Rules, then paste content of condensed or comprehensive template.
- **Windsurf**: Open Cascade chat on the right > Customizations icon (top right corner) > Customizations > Rules > Edit global_windsurf.md, then paste content of condensed or comprehensive template.
##### Autonomous Agents
- **Claude Code**: Create `CLAUDE.md` in your workspace root and replace content with condensed or comprehensive template.

**For more details, follow setup instructions**: See `agent_prompts/README.md` for detailed platform-specific configuration.

### [Claude Code Skills](agent_prompts/autonomous_agents/claude_code/skills/)

**NEW**: Production-ready skills for Claude Code autonomous agent workflows

#### Quick Start with Skills
```
"Use the init-python-project skill to create 'my-app'"
"Use the plan-before-code skill to design the auth feature"
"Use the create-claude-md skill to configure this project"
```

#### Available Skills (52 production-ready - 100% complete!)
| Skill | Category | Description |
|-------|----------|-------------|
| [plan-before-code](agent_prompts/autonomous_agents/claude_code/skills/plan-before-code/) | 🔥 Workflow | Anthropic's #1 best practice - explore, plan, execute |
| [create-claude-md](agent_prompts/autonomous_agents/claude_code/skills/create-claude-md/) | 🔥 Config | Generate comprehensive CLAUDE.md files |
| [init-python-project](agent_prompts/autonomous_agents/claude_code/skills/init-python-project/) | Setup | Initialize complete Python projects |
| [setup-python-system-prompt](agent_prompts/autonomous_agents/claude_code/skills/setup-python-system-prompt/) | Config | Configure Python development standards |
| [cleanup-python](agent_prompts/autonomous_agents/claude_code/skills/cleanup-python/) | Cleanup | Modernize and clean Python code |
| [generate-api-docs](agent_prompts/autonomous_agents/claude_code/skills/generate-api-docs/) | Docs | Generate API documentation (multi-language) |

**[View All Skills Documentation →](agent_prompts/autonomous_agents/claude_code/skills/README.md)**

#### Skills Roadmap (52 total planned)
- ✅ 6 completed (12%)
- 🔥 18 high-priority remaining
- 📊 28 medium-priority remaining
- [View Complete Roadmap](agent_prompts/autonomous_agents/claude_code/skills/SKILLS_LIST.md)

### [Code Cleanup](code_cleanup/)

#### Review Selection
| Phase | Focus |
| --- | --- |
| [Code Cleanup](code_cleanup/) | Dead code and duplication removal |

### [Code Reviews](code_review/)

#### Review Selection
| Phase | Focus |
| --- | --- |
| [Context Analysis](code_review/context_analysis/) | Project understanding |
| [Code Quality](code_review/code_quality/) | Style and maintainability |
| [Security](code_review/security_review/) | Vulnerability assessment |
| [Performance](code_review/performance_review/) | Optimization opportunities |
| [Testing](code_review/testing_review/) | Test coverage and quality |
| [Final Report](code_review/final_report/) | Consolidated findings |

#### Prompt Execution
Each code review type has copy-paste ready prompts for AI assistants.

#### Comprehensive Review
Run each code review prompt template one at a time for comprehensive coverage.

### [Test Development](test_development/)

#### Test Selection
| Phase | Focus |
| --- | --- |
| [Test Structure](test_development/test_structure/) | Infrastructure setup |
| [Test Cases](test_development/test_cases/) | Comprehensive test development |
| [Mocks & Fixtures](test_development/mocks_fixtures/) | Test isolation |
| [Performance Testing](test_development/performance_testing/) | Load and stress tests |
| [Maintenance & CI/CD](test_development/maintenance_cicd/) | Automation and quality gates |
| [Code Coverage](test_development/code_coverage/) | Coverage analysis (80%+ target) |

#### Prompt Execution
Each test type has copy-paste ready prompts for AI assistants.

#### Comprehensive Testing
Run each test prompt template one at a time for comprehensive coverage.

### [Documentation](documentation/)

#### Documentation Selection
| Phase | Focus |
| --- | --- |
| [Docstrings](documentation/docstrings/) | Code-level documentation |
| [Comments](documentation/comments/) | Strategic code comments |
| [User Docs](documentation/user_docs/) | README, guides, and tutorials |
| [Technical Docs](documentation/technical_docs/) | Architecture and design |
| [API Docs](documentation/api_docs/) | Complete API reference |
| [SBOM](documentation/sbom/) | Software Bill of Materials and compliance |

#### Prompt Execution
Each documentation type has copy-paste ready prompts for AI assistants.

#### Comprehensive Documentation
Run each documentation prompt template one at a time for comprehensive coverage.

## 📈 Benefits

### Consistent Quality
- **Standardized outputs**: All AI-generated content follows same high standards
- **Reduced review time**: Content adheres to established patterns and practices
- **Cross-platform compatibility**: Templates work across different AI tools and platforms
- **Organizational alignment**: Built-in compliance with coding standards and best practices

### Enhanced Productivity
- **Faster development**: Pre-built templates accelerate common development tasks
- **Reduced cognitive load**: Templates provide structure, allowing focus on problem-solving
- **Knowledge transfer**: Templates capture and share organizational best practices
- **AI-assisted workflows**: Copy-paste prompts enable immediate AI collaboration
- **Time savings**: Comprehensive templates reduce implementation time by 50-70%

### Quality Assurance
- **Built-in standards**: Templates include security, performance, and maintainability considerations
- **Comprehensive coverage**: Templates address all aspects of software development lifecycle
- **Continuous improvement**: Templates evolve based on lessons learned and industry best practices
- **Automated testing**: Test templates establish robust quality gates
- **Security first**: Code review templates emphasize vulnerability detection
- **Performance monitoring**: Built-in performance testing and profiling

### Educational Value
- **Learning through templates**: Detailed explanations help teams understand best practices
- **Pattern recognition**: Templates demonstrate proven architectural and coding patterns
- **Progressive improvement**: Teams naturally adopt better practices through template use

## 🔧 Customization

These templates are designed to be:
- **Modular**: Easy to adapt sections for specific organizational needs
- **Extensible**: Add organization-specific guidelines without breaking core structure
- **Language-agnostic**: Core principles apply beyond specific programming languages (Python currently implemented)
- **Technology-flexible**: Adaptable to different frameworks, tools, and methodologies
- **AI-platform neutral**: Works with GitHub Copilot, Claude, ChatGPT, Cursor, Windsurf, and other AI assistants

### To customize:
1. **Fork or copy** relevant template files
2. **Modify sections** specific to your organization's standards and requirements
3. **Adjust criteria**: Update pass/fail thresholds, coverage requirements, performance targets
4. **Extend checklists**: Add organization-specific evaluation points
5. **Test thoroughly** with your typical development workflows and use cases
6. **Version control** your customizations to track changes and enable rollback
7. **Share learnings** by contributing improvements back to the community

### Language Expansion
Current templates focus on Python. To extend to other languages:
1. **Copy Python structure** as a starting point
2. **Adapt language-specific patterns**: Modify for language idioms and frameworks
3. **Update tool references**: Replace Python-specific tools (pytest, unittest) with language equivalents
4. **Maintain phase structure**: Keep proven phase-based methodology
5. **Test and validate**: Ensure templates work with target language ecosystem

## 🔧 Troubleshooting

### Common Issues

#### System Prompts
- **Token limits**: Use condensed versions for platforms with stricter token constraints
- **Platform compatibility**: Some features may need adjustment per AI platform or tool
- **Performance impact**: Monitor AI response quality and adjust template complexity as needed

#### Code Review Templates
- **Too detailed**: Use quick review (phases 1-2) for simple changes
- **Context gathering**: Ensure you have repository access for phase 1 analysis
- **Missing information**: Skip unavailable checks rather than making assumptions

#### Test Development Templates
- **Time constraints**: Use quick setup (2 hours) for rapid prototyping
- **Complex setup**: Start with phase 1 infrastructure before adding advanced features
- **CI/CD integration**: Test locally before configuring automated pipelines
- **Flaky tests**: Run flakiness detection script before deployment

### Best Practices
- **Start comprehensive, optimize later**: Begin with full-featured templates, then streamline if needed
- **Regular review and updates**: Keep templates current with evolving best practices and tools
- **Cross-functional feedback**: Gather input from development, QA, and security teams
- **Iterative improvement**: Make incremental changes and measure impact before major revisions
- **Measure effectiveness**: Track time savings, bug reduction, and quality improvements
- **Team training**: Ensure team understands template structure and intended usage
- **Progressive adoption**: Implement one template category at a time

---

*AI Development Templates v0.2.5 - Empowering development teams with structured, AI-assisted workflows*

*Last Updated: October 2025*
*Repository maintained by Benjamin Dourthe (benjamin@adonamed.com)*