# AI Development Templates

This repository contains comprehensive templates and standardized prompts to enhance AI-assisted software development across multiple domains. These templates ensure consistent, high-quality outputs while maintaining organizational software development standards.

## 📁 Repository Structure

```
ai_templates/
├── system_prompts/                             # System prompts for AI-assisted coding
│   ├── autonomous_agents/                      # Prompts for autonomous coding agents
│   │   └── claude_code/                        # Claude-specific autonomous coding
│   │       └── python/                         # Python language prompts
│   │           ├── CLAUDE_comprehensive_35k.md # Full system prompt (~35k tokens)
│   │           └── CLAUDE_condensed_20k.md     # Optimized prompt (~20k tokens)
│   ├── coding_assistants/                      # Prompts for interactive coding assistants
│   │   └── python/                             # General interactive coding assistance
│   │       ├── GLOBAL_comprehensive_35k.md     # Full system prompt (~35k tokens)
│   │       └── GLOBAL_condensed_15k.md         # Optimized prompt (~15k tokens)
│   └── README.md                               # Platform setup instructions
├── code_review/                                # Templates for comprehensive code reviews
│   ├── python/                                 # Python code review templates
│   │   ├── README.md                           # 6-phase review protocol
│   │   ├── phase1_context.md                   # Context gathering
│   │   ├── phase2_code_quality.md              # Quality assessment
│   │   ├── phase3_security.md                  # Security review
│   │   ├── phase4_performance.md               # Performance analysis
│   │   ├── phase5_testing.md                   # Test coverage review
│   │   └── phase6_final.md                     # Final report generation
│   └── README.md                               # Code review overview
├── test_development/                           # Templates for comprehensive test development
│   ├── python/                                 # Python test development templates
│   │   ├── README.md                           # 5-phase test protocol
│   │   ├── phase1_structure.md                 # Test infrastructure
│   │   ├── phase2_test_cases.md                # Test case development
│   │   ├── phase3_mocks_fixtures.md            # Mocking & fixtures
│   │   ├── phase4_performance.md               # Performance testing
│   │   └── phase5_maintenance_cicd.md          # CI/CD integration
│   └── README.md                               # Test development overview
├── documentation/                              # Templates for comprehensive documentation
│   ├── python/                                 # Python documentation templates
│   │   ├── README.md                           # 5-phase documentation protocol
│   │   ├── phase1_docstrings.md                # Docstrings & code documentation
│   │   ├── phase2_comments.md                  # Strategic code comments
│   │   ├── phase3_user_docs.md                 # User-facing documentation
│   │   ├── phase4_technical_docs.md            # Technical documentation
│   │   └── phase5_api_docs.md                  # API reference documentation
│   └── README.md                               # Documentation overview
├── .github/
│   └── copilot-instructions.md                 # GitHub Copilot configuration for this repo
└── README.md                                   # This file
```

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
   - Quick (30 min): Phases 1-2 for basic quality assessment
   - Standard (1-2 hours): Phases 1-4 for thorough review
   - Comprehensive (3+ hours): All 6 phases for complete analysis
2. **Navigate to template**: `code_review/python/README.md` for complete protocol
3. **Copy phase prompts**: Each phase has copy-paste ready prompts for AI assistants
4. **Review systematically**: Follow sequential phases for comprehensive coverage
5. **Generate report**: Phase 6 consolidates findings into actionable recommendations

### For [Test Development](test_development/)
1. **Choose implementation approach**:
   - Quick (2 hours): Phases 1, 2 (core tests), and 5 (basic CI)
   - Standard (7-10 hours): Phases 1-4 for production-ready tests
   - Comprehensive (10-13 hours): All 5 phases for enterprise-grade testing
2. **Navigate to template**: `test_development/python/README.md` for complete protocol
3. **Follow phase sequence**: Each phase builds on previous infrastructure
4. **Use copy-paste prompts**: Detailed implementation prompts with code examples
5. **Integrate with CI/CD**: Phase 5 provides GitHub Actions and Jenkins configurations

### For [Documentation](documentation/)
1. **Choose documentation scope**:
   - Quick (2 hours): Phases 1 (docstrings), 3 (basic README), 4 (architecture overview)
   - Standard (7-10 hours): Phases 1-4 for comprehensive documentation
   - Complete (10-13 hours): All 5 phases for professional documentation
2. **Navigate to template**: `documentation/python/README.md` for complete protocol
3. **Follow phase sequence**: Docstrings → Comments → User Docs → Technical Docs → API Reference
4. **Use copy-paste prompts**: Detailed prompts with examples and templates
5. **Maintain documentation**: Keep docs current with code changes

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
- **Phase 1: Context Gathering** - Project understanding, architecture analysis, dependency review
- **Phase 2: Code Quality** - Style compliance, design patterns, error handling, documentation
- **Phase 3: Security Review** - Vulnerability assessment, input validation, authentication, encryption
- **Phase 4: Performance** - Algorithm efficiency, resource management, scalability analysis
- **Phase 5: Testing** - Test coverage, quality assessment, edge cases, integration tests
- **Phase 6: Final Report** - Comprehensive findings, prioritized recommendations, action items

**Time Investment**: 30 minutes (quick) to 3+ hours (comprehensive)

**Features**:
- Copy-paste ready prompts for AI-assisted reviews
- Comprehensive checklists (150+ evaluation points)
- Severity-based issue classification (Critical/High/Medium/Low)
- Security-focused analysis (OWASP Top 10, injection attacks, auth vulnerabilities)
- Performance profiling recommendations
- Actionable remediation guidance

### Test Development Templates

#### Python Test Development (5-Phase Methodology)
- **Phase 1: Test Structure** - Infrastructure setup, master runner, utilities, configuration (1-2 hours)
- **Phase 2: Test Cases** - Functional, edge cases, error handling, integration, performance (2-4 hours)
- **Phase 3: Mocks & Fixtures** - Database mocking, API mocking, test data, isolation (1-2 hours)
- **Phase 4: Performance Testing** - Response time, throughput, load, stress, memory profiling (2-4 hours)
- **Phase 5: CI/CD Integration** - GitHub Actions, Jenkins, flaky test detection, quality gates (1-2 hours)

**Time Investment**: 7-13 hours for complete implementation, 2 hours for quick setup

**Features**:
- Copy-paste ready implementation prompts
- TestResultAggregator and PerformanceTimer utilities
- Exact output formatting (100-char separators, box-drawing tables)
- Mock patterns for databases, APIs, file systems
- Performance testing with percentile analysis (p95, p99)
- Concurrent load testing (ThreadPoolExecutor)
- CI/CD workflow templates (GitHub Actions, Jenkins)
- Flaky test detection and resolution strategies

### Documentation Templates

#### Python Documentation (5-Phase Methodology)
- **Phase 1: Docstrings** - Comprehensive docstrings for functions, classes, modules (1-2 hours)
- **Phase 2: Comments** - Strategic comments explaining logic, decisions, non-obvious behavior (1-2 hours)
- **Phase 3: User Documentation** - README, user guides, how-to sections, CHANGELOG, DEVLOG (2-3 hours)
- **Phase 4: Technical Documentation** - Architecture, design decisions, codebase walkthroughs (2-4 hours)
- **Phase 5: API Reference** - Complete API documentation with examples and specifications (1-2 hours)

**Time Investment**: 7-13 hours for complete documentation, 2 hours for essential docs

**Features**:
- Copy-paste ready prompts for each phase
- Simple vs. complex docstring templates
- Comment guidelines (no inline, explain "why" not "what")
- README, CHANGELOG, DEVLOG structures
- Architecture documentation with diagrams
- Complete API reference format
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

### Recent Updates (October 2025)
- ✅ **Python Code Review Templates**: Complete 6-phase methodology with 150+ evaluation points
- ✅ **Python Test Development Templates**: Complete 5-phase methodology with CI/CD integration
- ✅ **Python Documentation Templates**: Complete 5-phase methodology for comprehensive documentation
- ✅ **System Prompts**: Comprehensive and condensed versions for autonomous agents and coding assistants
- 🔄 **Language Expansion**: JavaScript, TypeScript, Java, C# templates (planned)
- 🔄 **Additional Review Types**: API design reviews, database schema reviews (planned)

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

*Last Updated: October 2025*
*Repository maintained by Benjamin Dourthe (benjamin@adonamed.com)*