# Template Selection Decision Trees

Interactive decision trees to help you find the right template for your needs. Follow the branches based on your situation.

---

## Decision Tree 1: What Do You Need Help With?

```
START: What do you need help with?
│
├─→ [Improving Existing Code]
│   │
│   ├─→ Code is messy/has dead code → CODE CLEANUP
│   │   ├─→ Choose your language:
│   │   │   ├─→ Python: code_cleanup/python_cleanup.md
│   │   │   ├─→ JavaScript: code_cleanup/javascript_cleanup.md
│   │   │   ├─→ Java: code_cleanup/java_cleanup.md
│   │   │   ├─→ C#: code_cleanup/csharp_cleanup.md
│   │   │   ├─→ Go: code_cleanup/go_cleanup.md
│   │   │   ├─→ C: code_cleanup/c_cleanup.md
│   │   │   └─→ C++: code_cleanup/cpp_cleanup.md
│   │   └─→ Time: 4-8 hours | Difficulty: Intermediate
│   │
│   ├─→ Want quality/security feedback → CODE REVIEW
│   │   ├─→ Quick review (< 4 hours) → Phases 1-2
│   │   │   ├─→ Phase 1: code_review/context_analysis/{language}_context_analysis.md
│   │   │   └─→ Phase 2: code_review/code_quality/{language}_code_quality.md
│   │   │
│   │   ├─→ Comprehensive review (10-12 hours) → All 6 phases
│   │   │   ├─→ Phase 1: Context Analysis (2 hours)
│   │   │   ├─→ Phase 2: Code Quality (2-3 hours)
│   │   │   ├─→ Phase 3: Security Review (2-3 hours)
│   │   │   ├─→ Phase 4: Performance Review (2-3 hours)
│   │   │   ├─→ Phase 5: Testing Review (2 hours)
│   │   │   └─→ Phase 6: Final Report (1 hour)
│   │   │
│   │   └─→ See "Decision Tree 2: Which Code Review Phase?" for guidance
│   │
│   └─→ Missing tests → TEST DEVELOPMENT
│       ├─→ No test infrastructure → Phase 1: test_development/test_structure/{language}_test_structure.md
│       ├─→ Need unit tests → Phase 2: test_development/unit_tests/{language}_unit_tests.md
│       ├─→ Need integration tests → Phase 3: test_development/test_cases/{language}_test_cases.md
│       └─→ See "Decision Tree 3: Which Test Phase?" for complete guidance
│
├─→ [Starting New Project]
│   │
│   ├─→ Using Claude Code (Autonomous Agent)?
│   │   ├─→ Step 1: Install skills
│   │   │   └─→ python tools/install_skill.py --priority CRITICAL --destination /path/to/project
│   │   ├─→ Step 2: Install project init skill
│   │   │   ├─→ Python: --skill init-python-project
│   │   │   ├─→ JavaScript: --skill init-javascript-project
│   │   │   ├─→ Java: --skill init-java-project
│   │   │   └─→ C#: --skill init-csharp-project
│   │   ├─→ Step 3: Configure system prompt
│   │   │   └─→ Use skill: create-claude-md
│   │   └─→ See QUICKSTART.md for detailed instructions
│   │
│   └─→ Using GitHub Copilot/Cursor/Windsurf (Interactive Assistant)?
│       ├─→ Step 1: Choose system prompt version
│       │   └─→ See "Decision Tree 4: Comprehensive vs Condensed?" for guidance
│       ├─→ Step 2: Configure your platform
│       │   ├─→ Copilot: Create .github/copilot-instructions.md
│       │   ├─→ Cursor: Settings > Rules & Memories > User Rules
│       │   └─→ Windsurf: Cascade > Customizations > global_windsurf.md
│       └─→ Step 3: Start developing with AI assistance
│
├─→ [Generating Documentation]
│   │
│   ├─→ Code-level docs (docstrings) → documentation/docstrings/{language}_docstrings.md
│   │   └─→ Time: 2-3 hours | Difficulty: Beginner
│   │
│   ├─→ Strategic comments (inline explanations) → documentation/comments/{language}_comments.md
│   │   └─→ Time: 1-2 hours | Difficulty: Beginner
│   │
│   ├─→ User-facing docs (README, guides) → documentation/user_docs/{language}_user_docs.md
│   │   └─→ Time: 3-4 hours | Difficulty: Beginner
│   │
│   ├─→ API reference (complete API docs) → documentation/api_docs/{language}_api_docs.md
│   │   └─→ Time: 4-8 hours | Difficulty: Beginner
│   │   └─→ Or use skill: generate-api-docs
│   │
│   ├─→ Architecture docs (technical design) → documentation/technical_docs/{language}_technical_docs.md
│   │   └─→ Time: 4-6 hours | Difficulty: Intermediate
│   │
│   └─→ SBOM (compliance, dependencies) → documentation/sbom/{language}_sbom.md
│       └─→ Time: 2-3 hours | Difficulty: Intermediate
│
└─→ [Setting Up AI Assistant]
    │
    ├─→ Claude Code (Autonomous) → agent_prompts/autonomous_agents/claude_code/{language}/
    │   ├─→ Create CLAUDE.md in project root
    │   ├─→ Choose version: See "Decision Tree 4" below
    │   └─→ Or use skill: create-claude-md
    │
    ├─→ GitHub Copilot → agent_prompts/coding_assistants/{language}/
    │   ├─→ Create .github/copilot-instructions.md
    │   └─→ Paste content from GLOBAL_comprehensive_35k.md or GLOBAL_condensed_15k.md
    │
    ├─→ Cursor → agent_prompts/coding_assistants/{language}/
    │   ├─→ File > Preferences > Cursor Settings
    │   ├─→ Rules & Memories > User Rules
    │   └─→ Paste content from GLOBAL template
    │
    └─→ Windsurf → agent_prompts/coding_assistants/{language}/
        ├─→ Cascade chat > Customizations icon
        ├─→ Customizations > Rules > Edit global_windsurf.md
        └─→ Paste content from GLOBAL template
```

---

## Decision Tree 2: Which Code Review Phase?

```
START: What aspect concerns you most?
│
├─→ [I don't understand the project yet]
│   └─→ PHASE 1: Context Analysis (2 hours)
│       ├─→ Understand project structure & architecture
│       ├─→ Map dependencies & data flows
│       ├─→ Identify core vs auxiliary components
│       └─→ Template: code_review/context_analysis/{language}_context_analysis.md
│       └─→ NEXT: Phase 2 (Code Quality)
│
├─→ [Code Quality Issues]
│   └─→ PHASE 2: Code Quality (2-3 hours)
│       ├─→ Style consistency (naming, formatting)
│       ├─→ Code complexity & maintainability
│       ├─→ DRY violations & duplication
│       ├─→ Error handling patterns
│       └─→ Template: code_review/code_quality/{language}_code_quality.md
│       └─→ NEXT: Phase 3 (Security) or Phase 4 (Performance)
│
├─→ [Security Vulnerabilities]
│   └─→ PHASE 3: Security Review (2-3 hours)
│       ├─→ Input validation & sanitization
│       ├─→ Authentication & authorization
│       ├─→ Data exposure & encryption
│       ├─→ Dependency vulnerabilities
│       ├─→ Supply chain security (2025)
│       └─→ Template: code_review/security_review/{language}_security_review.md
│       └─→ NEXT: Phase 4 (Performance) or Phase 6 (Final Report)
│
├─→ [Performance Problems]
│   └─→ PHASE 4: Performance Review (2-3 hours)
│       ├─→ Algorithm efficiency & complexity
│       ├─→ Database query optimization
│       ├─→ Memory usage & leaks
│       ├─→ Caching opportunities
│       ├─→ Async/parallel processing
│       └─→ Template: code_review/performance_review/{language}_performance_review.md
│       └─→ NEXT: Phase 5 (Testing) or Phase 6 (Final Report)
│
├─→ [Testing Coverage Concerns]
│   └─→ PHASE 5: Testing Review (2 hours)
│       ├─→ Test coverage analysis (>80% target)
│       ├─→ Test quality assessment
│       ├─→ Missing edge cases
│       ├─→ Test maintainability
│       └─→ Template: code_review/testing_review/{language}_testing_review.md
│       └─→ NEXT: Phase 6 (Final Report)
│
├─→ [Need Complete Assessment]
│   └─→ ALL PHASES (10-12 hours)
│       ├─→ Run all 6 phases sequentially
│       ├─→ Comprehensive quality, security, performance analysis
│       └─→ End with: code_review/final_report/{language}_final_report.md
│
└─→ [Just want a quick check before merging]
    └─→ QUICK REVIEW (4 hours)
        ├─→ Phase 1: Context Analysis (2 hours)
        └─→ Phase 2: Code Quality (2 hours)
        └─→ Skip remaining phases for quick PRs
```

**Recommended Phase Order:**

1. **Context Analysis** (always first - understand before reviewing)

2. **Code Quality** (foundational issues)

3. **Security** (critical vulnerabilities)

4. **Performance** (optimization opportunities)

5. **Testing** (coverage & quality)

6. **Final Report** (consolidate findings)

---

## Decision Tree 3: Which Test Phase?

```
START: Where are you in your testing journey?
│
├─→ [No Tests Yet / Starting Fresh]
│   └─→ PHASE 1: Test Structure Setup (2-4 hours)
│       ├─→ Setup testing framework (pytest, Jest, JUnit, etc.)
│       ├─→ Configure test runners & CI/CD
│       ├─→ Establish directory structure
│       ├─→ Create test utilities & helpers
│       └─→ Template: test_development/test_structure/{language}_test_structure.md
│       └─→ NEXT: Phase 2 (Unit Tests)
│
├─→ [Have Test Infrastructure, Need Tests]
│   └─→ PHASE 2: Unit Tests (3-6 hours)
│       ├─→ FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)
│       ├─→ AAA pattern (Arrange-Act-Assert)
│       ├─→ Test functions, classes, async code
│       ├─→ 20-30 examples per language
│       ├─→ Speed target: <1 second per test
│       └─→ Template: test_development/unit_tests/{language}_unit_tests.md
│       └─→ NEXT: Phase 3 (Test Cases / Integration)
│
├─→ [Have Unit Tests, Need Integration/E2E]
│   └─→ PHASE 3: Test Cases (Integration/E2E) (4-8 hours)
│       ├─→ Integration tests (component interactions)
│       ├─→ End-to-end tests (full user workflows)
│       ├─→ API endpoint testing
│       ├─→ Database integration testing
│       └─→ Template: test_development/test_cases/{language}_test_cases.md
│       └─→ NEXT: Phase 4 (Mocks & Fixtures)
│
├─→ [Tests Are Slow or Coupled]
│   └─→ PHASE 4: Mocks & Fixtures (2-4 hours)
│       ├─→ Mock external dependencies (APIs, databases)
│       ├─→ Create test fixtures & factories
│       ├─→ Isolation strategies
│       ├─→ Reduce test coupling
│       └─→ Template: test_development/mocks_fixtures/{language}_mocks_fixtures.md
│       └─→ NEXT: Phase 5 (Performance Testing) or Phase 6 (Coverage)
│
├─→ [Need Performance/Load Testing]
│   └─→ PHASE 5: Performance Testing (4-6 hours)
│       ├─→ Load testing (expected traffic)
│       ├─→ Stress testing (breaking point)
│       ├─→ Endurance testing (sustained load)
│       ├─→ Spike testing (sudden traffic)
│       └─→ Template: test_development/performance_testing/{language}_performance_testing.md
│       └─→ NEXT: Phase 6 (Coverage) or Phase 7 (CI/CD)
│
├─→ [Want Coverage Metrics]
│   └─→ PHASE 6: Code Coverage (2-3 hours)
│       ├─→ Coverage analysis (>80% target)
│       ├─→ Identify untested code
│       ├─→ Coverage reports & visualization
│       ├─→ Critical path coverage (100% target)
│       └─→ Template: test_development/code_coverage/{language}_code_coverage.md
│       └─→ NEXT: Phase 7 (CI/CD) or Phase 8 (Validation)
│
├─→ [Ready for CI/CD Automation]
│   └─→ PHASE 7: Maintenance & CI/CD (3-5 hours)
│       ├─→ CI/CD pipeline setup (GitHub Actions, GitLab CI)
│       ├─→ Automated test execution
│       ├─→ Quality gates & thresholds
│       ├─→ Test result reporting
│       ├─→ Flaky test detection
│       └─→ Template: test_development/maintenance_cicd/{language}_maintenance_cicd.md
│       └─→ NEXT: Phase 8 (Validation)
│
├─→ [Tests Pass But Don't Catch Bugs]
│   └─→ PHASE 8: Reward Hacking Validation (3-5 hours)
│       ├─→ Mutation testing (>80% mutation score target)
│       ├─→ Detect weak tests (tautological, over-mocked)
│       ├─→ Validate test quality across ALL phases
│       ├─→ Tools: mutmut, Stryker, PITest, go-mutesting
│       └─→ Template: test_development/reward_hacking/{language}_reward_hacking.md
│       └─→ DONE: High-quality test suite complete!
│
└─→ [Want Complete Testing Setup]
    └─→ ALL 8 PHASES (20-30 hours)
        └─→ Follow phases 1→2→3→4→5→6→7→8 sequentially
        └─→ Comprehensive testing from infrastructure to validation
```

**8-Phase Testing Methodology Progress:**
```
Phase 1: Test Structure ──────────────────────► Foundation
Phase 2: Unit Tests ──────────────────────────► Core Testing
Phase 3: Test Cases ──────────────────────────► Integration
Phase 4: Mocks & Fixtures ────────────────────► Isolation
Phase 5: Performance Testing ─────────────────► Load/Stress
Phase 6: Code Coverage ───────────────────────► Metrics
Phase 7: Maintenance & CI/CD ─────────────────► Automation
Phase 8: Reward Hacking ──────────────────────► Validation
```

---

## Decision Tree 4: Comprehensive vs Condensed System Prompts?

```
START: Which system prompt version should I use?
│
├─→ [Comprehensive: 35-40k tokens]
│   │
│   CHOOSE IF:
│   ✅ New team member onboarding
│   ✅ Complex/legacy codebase (>10k LOC)
│   ✅ Teaching and mentoring focus
│   ✅ Establishing new patterns/standards
│   ✅ Token budget allows (Claude Sonnet 4.5)
│   ✅ Need detailed explanations & examples
│   ✅ Want extensive "why" explanations
│   │
│   Templates:
│   ├─→ Claude Code: autonomous_agents/claude_code/{language}/CLAUDE_comprehensive_40k.md
│   └─→ Copilot/Cursor: coding_assistants/{language}/GLOBAL_comprehensive_35k.md
│   │
│   Includes:
│   ├─→ 3-5 examples per pattern
│   ├─→ Detailed "why" explanations
│   ├─→ Historical context for decisions
│   ├─→ Extended troubleshooting sections
│   └─→ Comprehensive best practices
│
└─→ [Condensed: 15-20k tokens]
    │
    CHOOSE IF:
    ✅ Experienced development team
    ✅ Well-established patterns & conventions
    ✅ Quick tasks (<30 minutes per session)
    ✅ Token optimization needed
    ✅ Claude Haiku usage (cost optimization)
    ✅ Need speed over depth
    ✅ Focus on "how" rather than "why"
    │
    Templates:
    ├─→ Claude Code: autonomous_agents/claude_code/{language}/CLAUDE_condensed_20k.md
    └─→ Copilot/Cursor: coding_assistants/{language}/GLOBAL_condensed_15k.md
    │
    Includes:
    ├─→ Single example per pattern
    ├─→ Concise explanations
    ├─→ Focus on "how" (action-oriented)
    ├─→ Quick reference format
    └─→ Essential best practices only
```

**Comparison Chart:**

| Aspect | Comprehensive (40k) | Condensed (20k) |
|--------|-------------------|-----------------|
| **Tokens** | 35,000-40,000 | 15,000-20,000 |
| **Use Case** | Complex projects, onboarding | Quick tasks, experienced teams |
| **Examples** | 3-5 per pattern | 1 per pattern |
| **Explanations** | Detailed "why" + "how" | Concise "how" |
| **Best For** | Claude Sonnet | Claude Haiku |
| **Learning** | High (teaching focus) | Low (reference focus) |
| **Speed** | Slower (thorough) | Faster (efficient) |

**When Unsure:** Start with **Comprehensive** → Switch to **Condensed** once team is familiar with patterns

---

## Decision Tree 5: Single Template vs Complete Workflow?

```
START: How much time can you invest?
│
├─→ [Limited Time: <4 hours]
│   └─→ SINGLE TEMPLATE APPROACH
│       ├─→ Pick highest-priority template
│       ├─→ Examples:
│       │   ├─→ Security Review (2-3h) - Critical vulnerabilities
│       │   ├─→ Code Quality Review (2-3h) - Style issues
│       │   ├─→ Unit Tests (3-6h) - Core functionality
│       │   └─→ API Documentation (4-8h) - Public interface
│       └─→ See TEMPLATE_FINDER.md "By Time Available"
│
├─→ [Half Day: 4-8 hours]
│   └─→ QUICK WORKFLOW (2-3 templates)
│       ├─→ Code Quality Workflow:
│       │   ├─→ 1. Context Analysis (2h)
│       │   ├─→ 2. Code Quality Review (2-3h)
│       │   └─→ 3. Docstrings (2-3h)
│       │
│       ├─→ Testing Starter Workflow:
│       │   ├─→ 1. Test Structure (2-4h)
│       │   └─→ 2. Unit Tests (3-6h)
│       │
│       └─→ Documentation Workflow:
│           ├─→ 1. Docstrings (2-3h)
│           ├─→ 2. User Docs (3-4h)
│           └─→ 3. API Docs (4-8h)
│
├─→ [Full Day: 8-12 hours]
│   └─→ COMPREHENSIVE WORKFLOW (4-6 templates)
│       ├─→ Quality Improvement:
│       │   ├─→ 1. Code Cleanup (4-8h)
│       │   ├─→ 2. Code Quality Review (2-3h)
│       │   └─→ 3. Unit Tests (3-6h)
│       │
│       └─→ Complete Code Review:
│           └─→ All 6 review phases (10-12h total)
│
└─→ [Multi-Day Project: 20+ hours]
    └─→ COMPLETE METHODOLOGY
        ├─→ Complete Testing (all 8 phases): 20-30 hours
        ├─→ Complete Documentation (all 6 types): 15-25 hours
        └─→ Complete Quality Overhaul: 30-40 hours
            ├─→ Code Cleanup (4-8h)
            ├─→ Complete Code Review (10-12h)
            ├─→ Complete Testing (20-30h)
            └─→ Complete Documentation (15-25h)
```

---

## Quick Reference: Common Scenarios

### Scenario 1: "I inherited a messy codebase"
**Path:**

1. [Context Analysis](code_review/context_analysis/) (2h) - Understand what you're dealing with

2. [Code Cleanup](code_cleanup/) (4-8h) - Remove dead code, fix duplication

3. [Code Quality Review](code_review/code_quality/) (2-3h) - Identify remaining issues

4. [Unit Tests](test_development/unit_tests/) (3-6h) - Add safety net for future changes

**Total:** 11-19 hours | **Result:** Maintainable codebase with test coverage

---

### Scenario 2: "Preparing for production release"
**Path:**

1. [Security Review](code_review/security_review/) (2-3h) - Find vulnerabilities

2. [Performance Review](code_review/performance_review/) (2-3h) - Optimize bottlenecks

3. [Testing Review](code_review/testing_review/) (2h) - Validate test coverage

4. [API Documentation](documentation/api_docs/) (4-8h) - Document public interfaces

5. [SBOM](documentation/sbom/) (2-3h) - Compliance & dependencies

**Total:** 12-19 hours | **Result:** Production-ready, secure, documented code

---

### Scenario 3: "Code review flagged testing issues"
**Path:**

1. [Test Structure](test_development/test_structure/) (2-4h) - Setup infrastructure

2. [Unit Tests](test_development/unit_tests/) (3-6h) - Cover core functionality

3. [Test Cases](test_development/test_cases/) (4-8h) - Integration & E2E tests

4. [Code Coverage](test_development/code_coverage/) (2-3h) - Measure & report

5. [CI/CD](test_development/maintenance_cicd/) (3-5h) - Automate testing

**Total:** 14-26 hours | **Result:** Comprehensive test suite with automation

---

### Scenario 4: "Starting a new project from scratch"
**Path:**

1. **Use Skills** (if using Claude Code):

   - [init-{language}-project](agent_prompts/autonomous_agents/claude_code/skills/init-python-project/) (1h)

   - [create-claude-md](agent_prompts/autonomous_agents/claude_code/skills/create-claude-md/) (1h)

2. [Test Structure](test_development/test_structure/) (2-4h) - Setup from day 1

3. [User Documentation](documentation/user_docs/) (3-4h) - README, setup guide

4. [CI/CD](test_development/maintenance_cicd/) (3-5h) - Automation pipeline

**Total:** 10-15 hours | **Result:** Professional project setup with quality foundations

---

### Scenario 5: "Quick pre-merge code review"
**Path:**

1. [Context Analysis](code_review/context_analysis/) (2h) - Understand changes

2. [Code Quality Review](code_review/code_quality/) (2h) - Style & maintainability

3. **Optional:** [Security Review](code_review/security_review/) (2-3h) - If touching sensitive areas

**Total:** 4-7 hours | **Result:** Confident merge decision

---

## Navigation Tips

### Find Templates By:
- **Task Type:** See [TEMPLATE_FINDER.md](TEMPLATE_FINDER.md) "By Task Type"

- **Time Available:** See [TEMPLATE_FINDER.md](TEMPLATE_FINDER.md) "By Time Available"

- **Difficulty Level:** See [TEMPLATE_FINDER.md](TEMPLATE_FINDER.md) "By Difficulty"

- **Language:** See [TEMPLATE_FINDER.md](TEMPLATE_FINDER.md) "By Language"

### Other Resources:
- [Main README](README.md) - Repository overview

- [Quick Start Guide](QUICKSTART.md) - New project setup (5 minutes)

- [Skills Browser](https://bdourthe.github.io/ai_templates/) - Web-based skill discovery

- [Changelog](CHANGELOG.md) - Version history

---

*Last Updated: December 2025 | Version 0.2.8*
