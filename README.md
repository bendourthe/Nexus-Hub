# AI Development Templates

**Version 0.1.0** | Released October 7, 2025

This repository contains comprehensive templates and standardized prompts to enhance AI-assisted software development across multiple domains. These templates ensure consistent, high-quality outputs while maintaining organizational software development standards.

---

## 🎉 What's New in Version 0.1.0

**Initial Release** - Complete Python template suite with phase-based organization!

### 🚀 Major Features
- **18 Comprehensive Templates** across Code Review (6), Test Development (6), and Documentation (6)
- **Phase-Based Organization** with individual directories for each phase
- **Fully Clickable Navigation** - Direct links to every template from any README
- **22 README Files** providing guidance at repository, section, and phase levels
- **System Prompts** for GitHub Copilot, Cursor, Windsurf, and Claude Code

### 📋 Template Coverage
- **Code Review**: Context analysis, code quality, security, performance, testing, and final reporting
- **Test Development**: Infrastructure, test cases, mocking, performance testing, CI/CD, and coverage (80%+ target)
- **Documentation**: Docstrings, comments, user guides, technical docs, API reference, and SBOM generation

### ⏱️ Time Investment
- **Code Review**: 1-16 hours (depending on depth)
- **Test Development**: 8-15 hours (complete implementation)
- **Documentation**: 8-15 hours (including SBOM)

### 🎯 Key Benefits
- Copy-paste ready prompts for AI assistants
- Organizational standards integration
- CI/CD workflow templates
- Security and compliance focus (SBOM, NTIA, EU CRA)
- Educational approach with "why" explanations

[📖 View Complete Changelog](CHANGELOG.md)

---

## 📁 Repository Structure

### Quick Navigation
- [System Prompts](#system-prompts-for-ai-assisted-coding) - AI coding agent configurations
- [Code Review](#code-review-templates) - Comprehensive review methodology
- [Test Development](#test-development-templates) - Complete testing frameworks
- [Documentation](#documentation-templates) - Professional documentation system
- [Changelog](CHANGELOG.md) - Version history

---

## 🎯 Purpose

This repository provides standardized templates for four critical aspects of AI-enhanced software development:

### System Prompts for AI-Assisted Coding
- **Autonomous agents**: For independent coding agents like Claude Code
- **Interactive assistants**: For collaborative coding with GitHub Copilot, Cursor, Windsurf
- **Platform-specific optimization**: Tailored prompts for different AI platforms
- **Token-optimized versions**: Comprehensive vs condensed variants

### Code Review Templates
- **Structured review processes**: Comprehensive checklists and evaluation criteria
- **Quality assurance standards**: Consistent review patterns across projects
- **Security and performance focus**: Templates emphasizing critical non-functional requirements
- **Educational feedback**: Templates that help developers learn from reviews

### Test Development Templates
- **Comprehensive testing frameworks**: Complete test suite structures and patterns
- **Test automation**: Templates for automated test generation and execution
- **Quality metrics**: Standardized approaches to test coverage and effectiveness
- **Performance testing**: Templates for load, stress, and performance validation

### Documentation Templates
- **Code-level documentation**: Docstrings and strategic comments following organizational standards
- **User documentation**: README files, user guides, how-to sections, and about pages
- **Technical documentation**: Architecture, design decisions, and codebase walkthroughs
- **API documentation**: Complete reference documentation for public interfaces
- **SBOM documentation**: Software Bill of Materials for security, compliance, and supply chain management

## 🚀 Getting Started

### For [System Prompts](system_prompts/)
1. **Choose platform tier**: 

   - `autonomous_agents/` for Claude Code and Codex CLI

   - `coding_assistants/` for GitHub Copilot, Cursor, and Windsurf

2. **Select platform and coding language**: Navigate to appropriate language folder (currently `python/`)

3. **Choose version**: 

   - Comprehensive (~35k tokens) for complex projects

   - Condensed (15k-20k tokens) for efficiency and speed

4. **Configure your AI platform**:

   - **GitHub Copilot**: Create `.github/copilot-instructions.md` in your workspace and replace content with condensed or comprehensive template.

   - **Cursor**: Go to File > Preferences > Cursor Settings > Rules & Memories (tab on the left panel) > User Rules, then paste content of condensed or comprehensive template.

   - **Windsurf**: Open Cascade chat on the right > Customizations icon (top right corner) > Customizations > Rules > Edit global_windsurf.md, then paste content of condensed or comprehensive template.

   - **Claude Code**: Create `CLAUDE.md` in your workspace root and replace content with condensed or comprehensive template.

5. **Follow setup instructions**: See `system_prompts/README.md` for detailed platform-specific configuration

### For [Code Reviews](code_review/)

1. **Choose review depth**: 

   - Quick (30 min): [Phase 1](code_review/context_analysis/) + [Phase 2](code_review/code_quality/) for basic assessment

   - Standard (1-2 hours): Phases [1](code_review/context_analysis/)-[4](code_review/performance_review/) for thorough review

   - Comprehensive (3+ hours): All 6 phases for complete analysis

2. **Select review phase**:

   - [Context Analysis](code_review/context_analysis/) - Project understanding

   - [Code Quality](code_review/code_quality/) - Style and maintainability

   - [Security](code_review/security_review/) - Vulnerability assessment

   - [Performance](code_review/performance_review/) - Optimization opportunities

   - [Testing](code_review/testing_review/) - Test coverage and quality

   - [Final Report](code_review/final_report/) - Consolidated findings

3. **Copy phase prompts**: Each phase has copy-paste ready prompts for AI assistants

4. **Review systematically**: Follow sequential phases for comprehensive coverage

### For [Test Development](test_development/)

1. **Choose implementation approach**:

   - Quick (2.25 hours): [Phase 1](test_development/test_structure/), [2](test_development/test_cases/) (core), [5](test_development/maintenance_cicd/), [6](test_development/code_coverage/) (basic)

   - Standard (8-11 hours): Phases [1](test_development/test_structure/)-[5](test_development/maintenance_cicd/) for production-ready tests

   - Comprehensive (11-15 hours): All 6 phases for enterprise-grade testing

2. **Select test phase**:

   - [Test Structure](test_development/test_structure/) - Infrastructure setup

   - [Test Cases](test_development/test_cases/) - Comprehensive test development

   - [Mocks & Fixtures](test_development/mocks_fixtures/) - Test isolation

   - [Performance Testing](test_development/performance_testing/) - Load and stress tests

   - [Maintenance & CI/CD](test_development/maintenance_cicd/) - Automation and quality gates

   - [Code Coverage](test_development/code_coverage/) - Coverage analysis (80%+ target)

3. **Follow phase sequence**: Each phase builds on previous infrastructure

4. **Use copy-paste prompts**: Detailed implementation prompts with code examples

### For [Documentation](documentation/)

1. **Choose documentation scope**:

   - Quick (2 hours): [Phase 1](documentation/docstrings/) (docstrings), [3](documentation/user_docs/) (README), [4](documentation/technical_docs/) (architecture)

   - Standard (7-10 hours): Phases [1](documentation/docstrings/)-[4](documentation/technical_docs/) for comprehensive docs

   - Complete (11-15 hours): All 6 phases for professional documentation with SBOM

2. **Select documentation phase**:

   - [Docstrings](documentation/docstrings/) - Code-level documentation
   
   - [Comments](documentation/comments/) - Strategic code comments
   
   - [User Docs](documentation/user_docs/) - README, guides, and tutorials
   
   - [Technical Docs](documentation/technical_docs/) - Architecture and design
   
   - [API Docs](documentation/api_docs/) - Complete API reference
   
   - [SBOM](documentation/sbom/) - Software Bill of Materials and compliance3. **Follow phase sequence**: Docstrings → Comments → User Docs → Technical Docs → API Reference → SBOM

4. **Use copy-paste prompts**: Detailed prompts with examples and templates

## 🛠 Template Categories

### System Prompts
- **Comprehensive versions (~35k tokens)**
  - Complete architectural guidance
  - Extensive best practices and error handling
  - Detailed documentation standards
  - Full testing frameworks

- **Condensed versions (15k-20k tokens)**
  - Essential guidelines and core practices
  - Streamlined for token efficiency
  - Quick development and prototyping focus

### Code Review Templates

#### Python Code Review (6-Phase Methodology)
- **Context Gathering** - Project understanding, architecture analysis, dependency review
- **Code Quality** - Style compliance, design patterns, error handling, documentation
- **Security Review** - Vulnerability assessment, input validation, authentication, encryption
- **Performance** - Algorithm efficiency, resource management, scalability analysis
- **Testing** - Test coverage, quality assessment, edge cases, integration tests
- **Final Report** - Comprehensive findings, prioritized recommendations, action items

**Time Investment**: 30 minutes (quick) to 3+ hours (comprehensive)

**Features**:
- Copy-paste ready prompts for AI-assisted reviews
- Comprehensive checklists (150+ evaluation points)
- Severity-based issue classification (Critical/High/Medium/Low)
- Security-focused analysis (OWASP Top 10, injection attacks, auth vulnerabilities)
- Performance profiling recommendations
- Actionable remediation guidance

### Test Development Templates

#### Python Test Development (6-Phase Methodology)
- **Phase 1: Test Structure** - Infrastructure setup, master runner, utilities, configuration (1-2 hours)
- **Phase 2: Test Cases** - Functional, edge cases, error handling, integration, performance (2-4 hours)
- **Phase 3: Mocks & Fixtures** - Database mocking, API mocking, test data, isolation (1-2 hours)
- **Phase 4: Performance Testing** - Response time, throughput, load, stress, memory profiling (2-4 hours)
- **Phase 5: CI/CD Integration** - GitHub Actions, Jenkins, flaky test detection, quality gates (1-2 hours)
- **Phase 6: Code Coverage** - Coverage analysis, gap identification, targeted tests, enforcement (1-2 hours)

**Time Investment**: 8-15 hours for complete implementation, 2.25 hours for quick setup

**Features**:
- Copy-paste ready implementation prompts
- TestResultAggregator and PerformanceTimer utilities
- Exact output formatting (100-char separators, box-drawing tables)
- Mock patterns for databases, APIs, file systems
- Performance testing with percentile analysis (p95, p99)
- Concurrent load testing (ThreadPoolExecutor)
- CI/CD workflow templates (GitHub Actions, Jenkins)
- Code coverage analysis with coverage.py
- Coverage gap identification and targeted testing
- Coverage threshold enforcement (80%+ standards)
- Flaky test detection and resolution strategies

### Documentation Templates

#### Python Documentation (6-Phase Methodology)
- **Phase 1: Docstrings** - Comprehensive docstrings for functions, classes, modules (1-2 hours)
- **Phase 2: Comments** - Strategic comments explaining logic, decisions, non-obvious behavior (1-2 hours)
- **Phase 3: User Documentation** - README, user guides, how-to sections, CHANGELOG, DEVLOG (2-3 hours)
- **Phase 4: Technical Documentation** - Architecture, design decisions, codebase walkthroughs (2-4 hours)
- **Phase 5: API Reference** - Complete API documentation with examples and specifications (1-2 hours)
- **Phase 6: SBOM Generation** - Software Bill of Materials, dependency documentation, security (1-2 hours)

**Time Investment**: 8-15 hours for complete documentation, 2 hours for essential docs

**Features**:
- Copy-paste ready prompts for each phase
- Simple vs. complex docstring templates
- Comment guidelines (no inline, explain "why" not "what")
- README, CHANGELOG, DEVLOG structures
- Architecture documentation with diagrams
- Complete API reference format
- CycloneDX/SPDX SBOM generation
- Vulnerability scanning and license tracking
- Compliance documentation (NTIA, EU CRA)
- Usage examples and code samples

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

## 🔄 Version Control & Updates

- **Track changes**: All template modifications are version controlled for accountability
- **Team synchronization**: Ensure all team members use same template versions
- **Continuous improvement**: Regular updates based on evolving best practices and feedback
- **Impact assessment**: Evaluate template changes for effectiveness and adoption

### Version 0.1.0 Highlights (October 7, 2025)
- ✅ **Phase-Based Organization**: Individual directories for each of 18 phases with dedicated READMEs
- ✅ **Clickable Navigation**: Direct links to all templates from any README
- ✅ **Python Code Review Templates**: Complete 6-phase methodology with 150+ evaluation points
- ✅ **Python Test Development Templates**: Complete 6-phase methodology with coverage analysis (80%+ target)
- ✅ **Python Documentation Templates**: Complete 6-phase methodology including SBOM generation
- ✅ **SBOM Compliance**: CycloneDX/SPDX formats with NTIA and EU CRA compliance
- ✅ **System Prompts**: Comprehensive and condensed versions for 4 AI platforms
- 🔄 **Language Expansion**: JavaScript, TypeScript, Java, C# templates (planned for v0.2.0)
- 🔄 **Additional Review Types**: API design reviews, database schema reviews (planned for v0.2.0)

## 📝 Contributing

To contribute improvements:
1. **Test changes thoroughly** with your AI platform and development workflows
2. **Document the reasoning** for modifications and expected benefits
3. **Ensure compatibility** across different use cases and technology stacks
4. **Maintain phase structure**: Keep sequential phase-based methodology where applicable
5. **Include examples**: Provide copy-paste ready prompts and code examples
6. **Submit changes** with clear commit messages and impact descriptions

### Contribution Areas
- **New language templates**: Extend code review and test templates to other languages
- **Additional review types**: API design, database schema, infrastructure reviews
- **Platform optimizations**: Improve templates for specific AI platforms
- **Best practice updates**: Incorporate emerging patterns and techniques
- **Tooling integration**: Add support for new testing frameworks, CI/CD platforms

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

## 📄 License

These templates are designed for organizational use and can be customized according to your specific needs and licensing requirements.

---

## 📌 Version Information

**Current Version**: 0.1.0  
**Release Date**: October 7, 2025  
**Template Coverage**: Python (Complete - 18 phases)  
**Next Planned**: JavaScript/TypeScript templates

[View Changelog](CHANGELOG.md) | [View Releases](../../releases)

---

*AI Development Templates v0.1.0 - Empowering developers with structured, AI-assisted workflows*

*Last Updated: October 2025*
*Repository maintained by Benjamin Dourthe (benjamin@adonamed.com)*