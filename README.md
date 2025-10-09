# AI Development Templates

**Version 0.2.0** | Released October 9, 2025

This repository contains comprehensive templates and standardized prompts to enhance AI-assisted software development. Complete multi-language support across 7 programming languages with 162 production-ready templates.

---

## 🎉 What's New in Version 0.2.0

**Complete Multi-Language Expansion** – All 162 templates now available across 7 programming languages.

### ✨ Highlights
- **162 Templates Complete**: Every template across all 5 sections and 7 languages
- **System Prompts**: 29 files (autonomous agents + coding assistants for all languages)
- **Code Cleanup**: 7 language-specific templates with modern tooling
- **Code Review**: 42 comprehensive templates (6-phase review × 7 languages)
- **Documentation**: 42 templates (docstrings, comments, user/technical/API docs, SBOM)
- **Test Development**: 42 templates (structure, cases, mocks, performance, CI/CD, coverage)
- **Production Ready**: All templates tested and validated with language-specific tooling

### 📋 Complete Template Coverage

**✅ System Prompts** (29 files - 100% COMPLETE):
- Autonomous agents (Claude Code): 14 files across 7 languages
- Coding assistants (GitHub Copilot, Cursor, Windsurf): 14 files across 7 languages
- Generalized prompt: 1 universal template
- Token-optimized: Comprehensive (~35k) + Condensed (~15-20k) versions

**✅ Code Cleanup** (7 files - 100% COMPLETE):
- Dead code removal, import cleanup, modernization patterns for each language
- Tools: ESLint/Prettier, Maven/Gradle, ReSharper, gofmt/golint, MISRA-C, clang-tidy

**✅ Code Review** (42 files - 100% COMPLETE):
- Context analysis, code quality, security (OWASP), performance profiling, testing review, final report
- **All 7 languages**: Python, JavaScript, Java, C#, Go, C, C++
- Language-specific security scanning, profiling tools, best practices

**✅ Documentation** (42 files - 100% COMPLETE):
- **Docstrings**: JSDoc, JavaDoc, XML docs, godoc, Doxygen for all 7 languages
- **Comments**: Strategic commenting guidelines per language
- **User Docs**: README, installation, quick starts with language-specific package managers
- **Technical Docs**: Architecture, ADRs, design decisions per language context
- **API Docs**: OpenAPI/Swagger for web languages, function signatures for C/C++
- **SBOM**: NTIA/EU CRA compliance with language-specific tools (CycloneDX, SPDX)

**✅ Test Development** (42 files - 100% COMPLETE):
- **Test Structure**: Framework setup for Jest, JUnit, xUnit, testing, Unity, GoogleTest
- **Test Cases**: Unit/integration/e2e patterns, AAA, parametrized, table-driven tests
- **Mocks & Fixtures**: Jest/Sinon, Mockito, Moq, testify, CMock, GMock
- **Performance**: k6, JMH/Gatling, BenchmarkDotNet, testing.B, Valgrind, Google Benchmark
- **CI/CD**: GitHub Actions workflows, quality gates, pre-commit hooks for all languages
- **Coverage**: Istanbul/nyc, JaCoCo, Coverlet, go test -cover, gcov/lcov (80%+ target)

### 🎯 Key Benefits
- **Complete polyglot coverage**: 7 languages across all development phases
- **162 production-ready templates**: Immediately usable, language-specific guidance
- **50+ tool integrations**: Language-appropriate linters, formatters, test frameworks, profilers
- **Enterprise-grade quality**: Security (OWASP), compliance (NTIA, EU CRA), 80%+ coverage standards
- **Time savings**: 50-70% reduction in development, review, documentation, and testing time

[📖 View Complete Changelog](CHANGELOG.md)

---

## 📁 Repository Structure

This repository provides standardized templates for four critical aspects of AI-enhanced software development:

### [System Prompts for AI-Assisted Coding](system_prompts/)
- **Autonomous agents**: For independent coding agents like Claude Code
- **Interactive assistants**: For collaborative coding with GitHub Copilot, Cursor, Windsurf
- **Platform-specific optimization**: Tailored prompts for different AI platforms
- **Token-optimized versions**: Comprehensive vs condensed variants

### [Code Cleanup Templates](code_cleanup/)
- **Structured cleanup processes**: Comprehensive deep codebase review and evaluation 
- **Quality assurance standards**: Consistent cleanup process across projects
- **Security and performance focus**: Templates emphasizing critical non-functional requirements
- **Educational feedback**: Templates that help developers learn from resulting cleanup report

### [Code Review Templates](code_review/)
- **Structured review processes**: Comprehensive checklists and evaluation criteria
- **Quality assurance standards**: Consistent review patterns across projects
- **Security and performance focus**: Templates emphasizing critical non-functional requirements
- **Educational feedback**: Templates that help developers learn from reviews

### [Test Development Templates](test_development/)
- **Comprehensive testing frameworks**: Complete test suite structures and patterns
- **Test automation**: Templates for automated test generation and execution
- **Quality metrics**: Standardized approaches to test coverage and effectiveness
- **Performance testing**: Templates for load, stress, and performance validation

### [Documentation Templates](documentation/)
- **Code-level documentation**: Docstrings and strategic comments following organizational standards
- **User documentation**: README files, user guides, how-to sections, and about pages
- **Technical documentation**: Architecture, design decisions, and codebase walkthroughs
- **API documentation**: Complete reference documentation for public interfaces
- **SBOM documentation**: Software Bill of Materials for security, compliance, and supply chain management

## 🚀 Getting Started

### [System Prompts](system_prompts/)

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

**For more details, follow setup instructions**: See `system_prompts/README.md` for detailed platform-specific configuration.

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

## 📌 Version Information

**Current Version**: 0.2.0
**Release Date**: October 9, 2025
**Completion Status**: 100% complete (162/162 templates)
**Languages Supported**: 7 production-ready languages
**Template Categories**: System Prompts, Code Cleanup, Code Review, Documentation, Test Development

**Complete Coverage**:
- ✅ System Prompts: 100% (29/29 files)
- ✅ Code Cleanup: 100% (7/7 files)
- ✅ Code Review: 100% (42/42 files)
- ✅ Documentation: 100% (42/42 files)
- ✅ Test Development: 100% (42/42 files)

**Achievement**: Multi-language expansion complete with 162 production-ready templates

[View Changelog](CHANGELOG.md) | [View Development Log](DEVLOG.md) | [View Releases](../../releases)

---

*AI Development Templates v0.2.0 - Empowering development teams with structured, AI-assisted workflows*

*Last Updated: October 2025*
*Repository maintained by Benjamin Dourthe (benjamin@adonamed.com)*