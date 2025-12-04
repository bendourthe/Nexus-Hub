# Template Finder - Quick Reference Matrix

Quick reference guide to find the right template for your task. Filter by task type, language, time available, or difficulty level.

---

## By Task Type

| Task | Category | Languages | Time | Difficulty | Templates |
|------|----------|-----------|------|------------|-----------|
| Remove dead code & duplication | Code Cleanup | All 7 | 4-8h | Intermediate | [7 templates](code_cleanup/) |
| Review code quality & style | Code Review | All 7 | 2-3h | Intermediate | [7 templates](code_review/code_quality/) |
| Security vulnerability audit | Code Review | All 7 | 2-3h | Advanced | [7 templates](code_review/security_review/) |
| Performance optimization review | Code Review | All 7 | 2-3h | Advanced | [7 templates](code_review/performance_review/) |
| Generate unit tests | Testing | All 7 | 3-6h | Intermediate | [7 templates](test_development/unit_tests/) |
| Setup test infrastructure | Testing | All 7 | 2-4h | Intermediate | [7 templates](test_development/test_structure/) |
| Create integration/E2E tests | Testing | All 7 | 4-8h | Intermediate | [7 templates](test_development/test_cases/) |
| Setup mocks & fixtures | Testing | All 7 | 2-4h | Intermediate | [7 templates](test_development/mocks_fixtures/) |
| Performance & load testing | Testing | All 7 | 4-6h | Advanced | [7 templates](test_development/performance_testing/) |
| Code coverage analysis | Testing | All 7 | 2-3h | Intermediate | [7 templates](test_development/code_coverage/) |
| CI/CD & test automation | Testing | All 7 | 3-5h | Intermediate | [7 templates](test_development/maintenance_cicd/) |
| Test quality validation | Testing | All 7 | 3-5h | Advanced | [7 templates](test_development/reward_hacking/) |
| Generate API documentation | Documentation | All 7 | 4-8h | Beginner | [7 templates](documentation/api_docs/) |
| Write docstrings | Documentation | All 7 | 2-3h | Beginner | [7 templates](documentation/docstrings/) |
| Add strategic code comments | Documentation | All 7 | 1-2h | Beginner | [7 templates](documentation/comments/) |
| Create user documentation | Documentation | All 7 | 3-4h | Beginner | [7 templates](documentation/user_docs/) |
| Technical architecture docs | Documentation | All 7 | 4-6h | Intermediate | [7 templates](documentation/technical_docs/) |
| SBOM & compliance docs | Documentation | All 7 | 2-3h | Intermediate | [7 templates](documentation/sbom/) |

---

## By Language

### Python
**System Prompts:**
- [CLAUDE.md Comprehensive (40k tokens)](agent_prompts/autonomous_agents/claude_code/python/CLAUDE_comprehensive_40k.md) - For complex projects, mentoring
- [CLAUDE.md Condensed (20k tokens)](agent_prompts/autonomous_agents/claude_code/python/CLAUDE_condensed_20k.md) - For quick tasks, efficiency
- [Copilot/Cursor Comprehensive (35k tokens)](agent_prompts/coding_assistants/python/GLOBAL_comprehensive_35k.md)
- [Copilot/Cursor Condensed (15k tokens)](agent_prompts/coding_assistants/python/GLOBAL_condensed_15k.md)

**Templates:**
- [Code Cleanup](code_cleanup/python_cleanup.md) - Dead code removal, modernization
- **Code Review** (6 phases):
  - [Context Analysis](code_review/context_analysis/python_context_analysis.md)
  - [Code Quality](code_review/code_quality/python_code_quality.md)
  - [Security Review](code_review/security_review/python_security_review.md)
  - [Performance Review](code_review/performance_review/python_performance_review.md)
  - [Testing Review](code_review/testing_review/python_testing_review.md)
  - [Final Report](code_review/final_report/python_final_report.md)
- **Testing** (8 phases):
  - [Test Structure](test_development/test_structure/python_test_structure.md)
  - [Unit Tests](test_development/unit_tests/python_unit_tests.md)
  - [Test Cases](test_development/test_cases/python_test_cases.md)
  - [Mocks & Fixtures](test_development/mocks_fixtures/python_mocks_fixtures.md)
  - [Performance Testing](test_development/performance_testing/python_performance_testing.md)
  - [Code Coverage](test_development/code_coverage/python_code_coverage.md)
  - [Maintenance & CI/CD](test_development/maintenance_cicd/python_maintenance_cicd.md)
  - [Reward Hacking](test_development/reward_hacking/python_reward_hacking.md)
- **Documentation** (6 types):
  - [Docstrings](documentation/docstrings/python_docstrings.md)
  - [Comments](documentation/comments/python_comments.md)
  - [User Docs](documentation/user_docs/python_user_docs.md)
  - [Technical Docs](documentation/technical_docs/python_technical_docs.md)
  - [API Docs](documentation/api_docs/python_api_docs.md)
  - [SBOM](documentation/sbom/python_sbom.md)

**Skills:** All [48 Claude Code skills](agent_prompts/autonomous_agents/claude_code/skills/) are language-agnostic

---

### JavaScript
**System Prompts:**
- [CLAUDE.md Comprehensive (40k tokens)](agent_prompts/autonomous_agents/claude_code/javascript/CLAUDE_comprehensive_40k.md)
- [CLAUDE.md Condensed (20k tokens)](agent_prompts/autonomous_agents/claude_code/javascript/CLAUDE_condensed_20k.md)
- [Copilot/Cursor Comprehensive (35k tokens)](agent_prompts/coding_assistants/javascript/GLOBAL_comprehensive_35k.md)
- [Copilot/Cursor Condensed (15k tokens)](agent_prompts/coding_assistants/javascript/GLOBAL_condensed_15k.md)

**Templates:** Same structure as Python (21 templates: 1 cleanup + 6 code review + 8 testing + 6 documentation)

---

### Java
**System Prompts:**
- [CLAUDE.md Comprehensive (40k tokens)](agent_prompts/autonomous_agents/claude_code/java/CLAUDE_comprehensive_40k.md)
- [CLAUDE.md Condensed (20k tokens)](agent_prompts/autonomous_agents/claude_code/java/CLAUDE_condensed_20k.md)
- [Copilot/Cursor Comprehensive (35k tokens)](agent_prompts/coding_assistants/java/GLOBAL_comprehensive_35k.md)
- [Copilot/Cursor Condensed (15k tokens)](agent_prompts/coding_assistants/java/GLOBAL_condensed_15k.md)

**Templates:** Same structure as Python (21 templates)

---

### C#
**System Prompts:**
- [CLAUDE.md Comprehensive (40k tokens)](agent_prompts/autonomous_agents/claude_code/csharp/CLAUDE_comprehensive_40k.md)
- [CLAUDE.md Condensed (20k tokens)](agent_prompts/autonomous_agents/claude_code/csharp/CLAUDE_condensed_20k.md)
- [Copilot/Cursor Comprehensive (35k tokens)](agent_prompts/coding_assistants/csharp/GLOBAL_comprehensive_35k.md)
- [Copilot/Cursor Condensed (15k tokens)](agent_prompts/coding_assistants/csharp/GLOBAL_condensed_15k.md)

**Templates:** Same structure as Python (21 templates)

---

### Go
**System Prompts:**
- [CLAUDE.md Comprehensive (40k tokens)](agent_prompts/autonomous_agents/claude_code/go/CLAUDE_comprehensive_40k.md)
- [CLAUDE.md Condensed (20k tokens)](agent_prompts/autonomous_agents/claude_code/go/CLAUDE_condensed_20k.md)
- [Copilot/Cursor Comprehensive (35k tokens)](agent_prompts/coding_assistants/go/GLOBAL_comprehensive_35k.md)
- [Copilot/Cursor Condensed (15k tokens)](agent_prompts/coding_assistants/go/GLOBAL_condensed_15k.md)

**Templates:** Same structure as Python (21 templates)

---

### C
**System Prompts:**
- [CLAUDE.md Comprehensive (40k tokens)](agent_prompts/autonomous_agents/claude_code/c/CLAUDE_comprehensive_40k.md)
- [CLAUDE.md Condensed (20k tokens)](agent_prompts/autonomous_agents/claude_code/c/CLAUDE_condensed_20k.md)
- [Copilot/Cursor Comprehensive (35k tokens)](agent_prompts/coding_assistants/c/GLOBAL_comprehensive_35k.md)
- [Copilot/Cursor Condensed (15k tokens)](agent_prompts/coding_assistants/c/GLOBAL_condensed_15k.md)

**Templates:** Same structure as Python (21 templates)

---

### C++
**System Prompts:**
- [CLAUDE.md Comprehensive (40k tokens)](agent_prompts/autonomous_agents/claude_code/cpp/CLAUDE_comprehensive_40k.md)
- [CLAUDE.md Condensed (20k tokens)](agent_prompts/autonomous_agents/claude_code/cpp/CLAUDE_condensed_20k.md)
- [Copilot/Cursor Comprehensive (35k tokens)](agent_prompts/coding_assistants/cpp/GLOBAL_comprehensive_35k.md)
- [Copilot/Cursor Condensed (15k tokens)](agent_prompts/coding_assistants/cpp/GLOBAL_condensed_15k.md)

**Templates:** Same structure as Python (21 templates)

---

## By Time Available

### Quick Tasks (<2 hours)
Perfect for addressing specific issues or adding targeted improvements.

- [Strategic Comments](documentation/comments/) - 1-2 hours - Add explanatory comments to complex code
- [Pre-commit Checklist Setup](agent_prompts/autonomous_agents/claude_code/skills/pre-commit-checklist/) - 1 hour - Setup quality gates

### Half-Day Tasks (2-4 hours)
Substantial improvements that can be completed in a single session.

- [Code Quality Review](code_review/code_quality/) - 2-3 hours - Style & maintainability review
- [Test Structure Setup](test_development/test_structure/) - 2-4 hours - Test infrastructure foundation
- [User Documentation](documentation/user_docs/) - 3-4 hours - README, guides, tutorials
- [Docstrings](documentation/docstrings/) - 2-3 hours - Code-level documentation
- [SBOM Documentation](documentation/sbom/) - 2-3 hours - Software Bill of Materials
- [Code Coverage Analysis](test_development/code_coverage/) - 2-3 hours - Coverage reports & gaps
- [Security Review](code_review/security_review/) - 2-3 hours - Vulnerability assessment
- [Performance Review](code_review/performance_review/) - 2-3 hours - Optimization opportunities
- [Mocks & Fixtures](test_development/mocks_fixtures/) - 2-4 hours - Test isolation setup

### Full-Day Tasks (6-8 hours)
Major improvements requiring focused effort over a full workday.

- [Complete Code Cleanup](code_cleanup/) - 4-8 hours - Dead code removal, duplication elimination
- [Unit Test Generation](test_development/unit_tests/) - 3-6 hours - Comprehensive unit test suite
- [API Documentation](documentation/api_docs/) - 4-8 hours - Complete API reference
- [Technical Documentation](documentation/technical_docs/) - 4-6 hours - Architecture & design docs
- [Test Cases (Integration/E2E)](test_development/test_cases/) - 4-8 hours - Integration & E2E tests
- [Performance Testing](test_development/performance_testing/) - 4-6 hours - Load & stress tests
- [CI/CD & Maintenance](test_development/maintenance_cicd/) - 3-5 hours - Automation setup
- [Reward Hacking Validation](test_development/reward_hacking/) - 3-5 hours - Test quality validation

### Multi-Day Projects (10+ hours)
Comprehensive initiatives that transform code quality across multiple dimensions.

- **[Complete Code Review](code_review/)** (all 6 phases) - 10-12 hours
  - Context Analysis (2h) → Code Quality (2-3h) → Security (2-3h) → Performance (2-3h) → Testing (2h) → Final Report (1h)

- **[Complete Testing Setup](test_development/)** (all 8 phases) - 20-30 hours
  - Test Structure (2-4h) → Unit Tests (3-6h) → Test Cases (4-8h) → Mocks (2-4h) → Performance (4-6h) → Coverage (2-3h) → CI/CD (3-5h) → Validation (3-5h)

- **[Complete Documentation](documentation/)** (all 6 types) - 15-25 hours
  - Docstrings (2-3h) → Comments (1-2h) → User Docs (3-4h) → Technical Docs (4-6h) → API Docs (4-8h) → SBOM (2-3h)

---

## By Difficulty Level

### Beginner
Perfect for getting started with AI-assisted development or onboarding new team members.

**Documentation:**
- [Docstrings](documentation/docstrings/) - Code-level documentation with examples
- [Strategic Comments](documentation/comments/) - When and how to comment code
- [User Documentation](documentation/user_docs/) - README files, guides, tutorials
- [API Documentation](documentation/api_docs/) - Comprehensive API reference (structured approach)

**Skills:**
- [Create CLAUDE.md](agent_prompts/autonomous_agents/claude_code/skills/create-claude-md/) - Generate project configuration
- [Generate API Docs](agent_prompts/autonomous_agents/claude_code/skills/generate-api-docs/) - Automated API documentation

---

### Intermediate
For developers comfortable with testing, code review, and project structure.

**Code Management:**
- [Code Cleanup](code_cleanup/) - Dead code removal, duplication elimination
- [Code Quality Review](code_review/code_quality/) - Style & maintainability assessment
- [Context Analysis](code_review/context_analysis/) - Project understanding & mapping

**Testing:**
- [Test Structure Setup](test_development/test_structure/) - Testing infrastructure foundation
- [Unit Tests](test_development/unit_tests/) - FIRST principles, AAA pattern
- [Test Cases](test_development/test_cases/) - Integration & E2E test development
- [Mocks & Fixtures](test_development/mocks_fixtures/) - Test isolation strategies
- [Code Coverage](test_development/code_coverage/) - Coverage analysis & gap identification
- [CI/CD & Maintenance](test_development/maintenance_cicd/) - Test automation setup

**Documentation:**
- [Technical Documentation](documentation/technical_docs/) - Architecture & design docs
- [SBOM](documentation/sbom/) - Software Bill of Materials & compliance

**Skills:**
- [Plan Before Code](agent_prompts/autonomous_agents/claude_code/skills/plan-before-code/) - Systematic development workflow
- [Code Review Quality](agent_prompts/autonomous_agents/claude_code/skills/code-review-quality/) - Automated quality reviews
- [Test-Driven Development](agent_prompts/autonomous_agents/claude_code/skills/test-driven-development/) - TDD workflow

---

### Advanced
For experienced developers tackling complex optimization, security, and quality challenges.

**Advanced Review:**
- [Security Review](code_review/security_review/) - Vulnerability assessment & threat modeling
- [Performance Review](code_review/performance_review/) - Profiling & optimization opportunities
- [Testing Review](code_review/testing_review/) - Test suite quality assessment

**Advanced Testing:**
- [Performance Testing](test_development/performance_testing/) - Load, stress, endurance testing
- [Reward Hacking Validation](test_development/reward_hacking/) - Mutation testing for test quality

**Skills:**
- [Code Review Security](agent_prompts/autonomous_agents/claude_code/skills/code-review-security/) - Security audit workflows
- [Code Review Performance](agent_prompts/autonomous_agents/claude_code/skills/code-review-performance/) - Performance analysis
- [Dependency Security Audit](agent_prompts/autonomous_agents/claude_code/skills/dependency-security-audit/) - Vulnerability scanning

---

## Quick Selection Guide

### "I need to..."

**...clean up messy code**
→ [Code Cleanup](code_cleanup/) templates (4-8 hours, Intermediate)

**...review code before merging**
→ [Code Review](code_review/) - Start with [Context Analysis](code_review/context_analysis/) + [Code Quality](code_review/code_quality/) (4 hours total)

**...add tests to existing code**
→ [Test Structure](test_development/test_structure/) → [Unit Tests](test_development/unit_tests/) (5-10 hours total)

**...document an API**
→ [API Documentation](documentation/api_docs/) (4-8 hours, Beginner)

**...setup CI/CD for tests**
→ [Maintenance & CI/CD](test_development/maintenance_cicd/) (3-5 hours, Intermediate)

**...find security vulnerabilities**
→ [Security Review](code_review/security_review/) (2-3 hours, Advanced)

**...improve performance**
→ [Performance Review](code_review/performance_review/) (2-3 hours, Advanced)

**...validate test quality**
→ [Reward Hacking Validation](test_development/reward_hacking/) (3-5 hours, Advanced)

---

## Template Combinations (Recommended Workflows)

### New Project Setup (8-12 hours)
1. [Init Project Skill](agent_prompts/autonomous_agents/claude_code/skills/init-python-project/) - 1 hour
2. [Test Structure](test_development/test_structure/) - 2-4 hours
3. [User Documentation](documentation/user_docs/) - 3-4 hours
4. [CI/CD Setup](test_development/maintenance_cicd/) - 3-5 hours

### Quality Improvement Sprint (15-20 hours)
1. [Code Cleanup](code_cleanup/) - 4-8 hours
2. [Code Quality Review](code_review/code_quality/) - 2-3 hours
3. [Unit Tests](test_development/unit_tests/) - 3-6 hours
4. [Code Coverage](test_development/code_coverage/) - 2-3 hours
5. [Docstrings](documentation/docstrings/) - 2-3 hours

### Pre-Release Checklist (10-15 hours)
1. [Security Review](code_review/security_review/) - 2-3 hours
2. [Performance Review](code_review/performance_review/) - 2-3 hours
3. [Testing Review](code_review/testing_review/) - 2 hours
4. [API Documentation](documentation/api_docs/) - 4-8 hours
5. [SBOM](documentation/sbom/) - 2-3 hours

### Test Modernization (15-25 hours)
1. [Test Structure](test_development/test_structure/) - 2-4 hours
2. [Unit Tests](test_development/unit_tests/) - 3-6 hours
3. [Mocks & Fixtures](test_development/mocks_fixtures/) - 2-4 hours
4. [Performance Testing](test_development/performance_testing/) - 4-6 hours
5. [Code Coverage](test_development/code_coverage/) - 2-3 hours
6. [Reward Hacking Validation](test_development/reward_hacking/) - 3-5 hours

---

## Related Resources

- [Main README](README.md) - Repository overview and getting started
- [Decision Trees](DECISION_TREES.md) - Interactive template selection guide
- [Quick Start Guide](QUICKSTART.md) - Setup a new project in 5 minutes
- [Skills Browser](https://bdourthe.github.io/ai_templates/) - Web-based skill discovery
- [Changelog](CHANGELOG.md) - Version history and updates
- [Development Log](DEVLOG.md) - Implementation notes and decisions

---

*Last Updated: December 2025 | Version 0.2.8*
