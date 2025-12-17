# AI Development Templates

**Version 0.3.2**

> **277 production-ready templates** for AI-assisted software development across 7 languages
>
> Copy prompts → Paste into AI assistant → Get production-quality code

---

## 🎉 What's New in v0.3.2

### Simplified AI Instructions Templates

- **Consolidated Coding Assistant Templates** - One optimized template per language (~20k characters) replacing comprehensive/condensed split

- **GitHub Copilot Format** - Templates renamed to `copilot-instructions.md` matching expected VS Code format

- **Streamlined Setup** - Clear 3-step instructions for GitHub Copilot and Claude Code

- **Removed Complexity** - Focused documentation on GitHub Copilot and Claude Code only

[View Complete Changelog](CHANGELOG.md)

---

## 🎯 Quick Navigation

**I want to...**

- **[Configure my AI Assistant](#ai-instructions-configuration)** → Claude Code, GitHub Copilot, Cursor

- **[Use Pre-built Claude Skills](#claude-skills)** → 47 automated skills for testing, review, compliance

- **[Generate Code Documentation](#code-documentation-generation)** → API docs, README, docstrings

- **[Generate Tests](#tests-generation)** → Unit tests, code coverage, CI/CD integration

- **[Review My Code](#code-review)** → Security, performance, quality

- **[Establish Compliance & Governance](#compliance-governance)** → SOC 2, ISO 27001, GDPR, AI governance

- **[Clean Up My Codebase](#codebase-cleanup)** → Remove dead code, duplication, legacy patterns

---

## 📖 What is This Repository?

This repository provides **ready-to-use prompt templates** for AI coding assistants that generate production-quality code across the entire development lifecycle.

**How it works:**

1. Find your template below (e.g., "Python Unit Tests")

2. Click the link to open the template file

3. Copy the "Prompt Template" section from that file

4. Paste it into GitHub Copilot, ChatGPT, Claude, or Cursor

5. Get comprehensive, production-ready results in minutes

**Supported languages:** Python | JavaScript | Java | C# | Go | C | C++

---

<a name="ai-instructions-configuration"></a>

## ⚙️ AI Instructions Configuration

**Configure your AI coding assistant with language-specific system prompts**

### Coding Assistants (GitHub Copilot)

| Language | Instructions |
|----------|-------------|
| **Python** | [copilot-instructions.md](templates/ai_instructions/coding_assistants/python/copilot-instructions.md) |
| **JavaScript** | [copilot-instructions.md](templates/ai_instructions/coding_assistants/javascript/copilot-instructions.md) |
| **Java** | [copilot-instructions.md](templates/ai_instructions/coding_assistants/java/copilot-instructions.md) |
| **C#** | [copilot-instructions.md](templates/ai_instructions/coding_assistants/csharp/copilot-instructions.md) |
| **Go** | [copilot-instructions.md](templates/ai_instructions/coding_assistants/go/copilot-instructions.md) |
| **C** | [copilot-instructions.md](templates/ai_instructions/coding_assistants/c/copilot-instructions.md) |
| **C++** | [copilot-instructions.md](templates/ai_instructions/coding_assistants/cpp/copilot-instructions.md) |

**Setup in VS Code (3 steps):**

1. Create `.github` folder in your project root

2. Create `copilot-instructions.md` file inside `.github`

3. Copy the content from your language template above into the file


### Agentic Systems (Claude Code)

**Quick Setup (3 steps):**

1. **Copy template** to your project:
   ```bash
   cp -r templates/ai_instructions/agentic_systems/claude_code/python/* your-project/
   ```

2. **Start Claude Code** and run the setup wizard:
   ```
   /setup-project
   ```

3. **Import skills** from the catalog:
   ```
   /import-skills
   ```

| Language | Template |
|----------|----------|
| **Python** | [python/](templates/ai_instructions/agentic_systems/claude_code/python/) |
| **JavaScript** | [javascript/](templates/ai_instructions/agentic_systems/claude_code/javascript/) |
| **Java** | [java/](templates/ai_instructions/agentic_systems/claude_code/java/) |
| **C#** | [csharp/](templates/ai_instructions/agentic_systems/claude_code/csharp/) |
| **Go** | [go/](templates/ai_instructions/agentic_systems/claude_code/go/) |
| **C** | [c/](templates/ai_instructions/agentic_systems/claude_code/c/) |
| **C++** | [cpp/](templates/ai_instructions/agentic_systems/claude_code/cpp/) |

> **Modular skills-based templates** with ~80% token reduction. **47+ skills available** in the [Skills Catalog](catalogs/claude_skills/).
>
> **[→ Full Claude Code Setup Guide](guides/CLAUDE_CODE_PROJECT_SETUP.md)**

---

<a name="claude-skills"></a>

## 🧠 Claude Skills

**47 production-ready skills for automated development workflows with Claude Code**

Claude Skills are modular instruction sets that automatically activate when you describe a task. Instead of writing prompts, simply tell Claude what you need and the appropriate skill takes over.

### What Are Skills?

Skills are self-contained `SKILL.md` files that:
- **Auto-activate** based on natural language triggers ("write unit tests", "security review")
- **Provide step-by-step guidance** with language-specific code examples
- **Chain together** for complete workflows (test → review → document → commit)

### Quick Setup

```bash
# Copy a single skill to your project
cp -r catalogs/claude_skills/tests-generation/unit-tests/ your-project/.claude/skills/

# Or copy an entire category
cp -r catalogs/claude_skills/workflow/ your-project/.claude/skills/
```

Once installed, skills activate automatically when you describe related tasks.

### Pre-Built Skill Categories

| Category | Skills | What They Do |
|----------|--------|--------------|
| **[Tests Generation](catalogs/claude_skills/tests-generation/)** | 8 | FIRST principles, AAA pattern, mocks, coverage, CI/CD |
| **[Code Review](catalogs/claude_skills/code-review/)** | 6 | 6-phase review: context → quality → security → performance → testing → report |
| **[Code Cleanup](catalogs/claude_skills/code-cleanup/)** | 7 | Dead code removal, modernization per language |
| **[Documentation](catalogs/claude_skills/documentation/)** | 6 | Docstrings, comments, README, API docs, SBOM |
| **[Compliance](catalogs/claude_skills/compliance/)** | 8 | SOC 2, ISO 27001, GDPR, NIST AI RMF, AI governance |
| **[Project Setup](catalogs/claude_skills/project-setup/)** | 4 | Initialize projects with best practices |
| **[Workflow](catalogs/claude_skills/workflow/)** | 5 | Plan-before-code, TDD, commit workflow |
| **[Security](catalogs/claude_skills/security/)** | 3 | Dependency audit, pre-commit checks, licensing |

### Pre-Built Slash Commands

The Claude Code templates include 6 ready-to-use slash commands:

| Command | What It Does |
|---------|--------------|
| `/setup-project` | Initialize project structure with best practices |
| `/test` | Run tests and fix failures |
| `/review` | Comprehensive code review |
| `/update-documentation` | Sync docs with code changes |
| `/import-skills` | Import skills from the catalog |
| `/upgrade-version` | Manage semantic versioning |

**Creating custom commands**: Add `.md` files to `.claude/commands/` in your project. See the [create-custom-command](catalogs/claude_skills/workflow/create-custom-command/) skill for guidance.

> **Full Documentation**: [Skills README](catalogs/claude_skills/README.md) | [Skills Catalog](catalogs/claude_skills/CATALOG.md)

---

<a name="code-documentation-generation"></a>

## 📚 Code Documentation Generation

**Generate comprehensive documentation from docstrings to SBOM**

### Quick Links by Type

| Type | What It Generates | Click to Open |
|------|-------------------|---------------|
| **Docstrings** | Function/class docs | [Python](templates/documentation_generation/docstrings/python_docstrings.md) \| [JavaScript](templates/documentation_generation/docstrings/javascript_docstrings.md) \| [Java](templates/documentation_generation/docstrings/java_docstrings.md) \| [C#](templates/documentation_generation/docstrings/csharp_docstrings.md) \| [Go](templates/documentation_generation/docstrings/go_docstrings.md) \| [C](templates/documentation_generation/docstrings/c_docstrings.md) \| [C++](templates/documentation_generation/docstrings/cpp_docstrings.md) |
| **Comments** | Strategic inline explanations | [Python](templates/documentation_generation/comments/python_comments.md) \| [JavaScript](templates/documentation_generation/comments/javascript_comments.md) \| [Java](templates/documentation_generation/comments/java_comments.md) \| [C#](templates/documentation_generation/comments/csharp_comments.md) \| [Go](templates/documentation_generation/comments/go_comments.md) \| [C](templates/documentation_generation/comments/c_comments.md) \| [C++](templates/documentation_generation/comments/cpp_comments.md) |
| **User Docs** | README, guides, tutorials | [Python](templates/documentation_generation/user_docs/python_user_docs.md) \| [JavaScript](templates/documentation_generation/user_docs/javascript_user_docs.md) \| [Java](templates/documentation_generation/user_docs/java_user_docs.md) \| [C#](templates/documentation_generation/user_docs/csharp_user_docs.md) \| [Go](templates/documentation_generation/user_docs/go_user_docs.md) \| [C](templates/documentation_generation/user_docs/c_user_docs.md) \| [C++](templates/documentation_generation/user_docs/cpp_user_docs.md) |
| **Technical Docs** | Architecture, design | [Python](templates/documentation_generation/technical_docs/python_technical_docs.md) \| [JavaScript](templates/documentation_generation/technical_docs/javascript_technical_docs.md) \| [Java](templates/documentation_generation/technical_docs/java_technical_docs.md) \| [C#](templates/documentation_generation/technical_docs/csharp_technical_docs.md) \| [Go](templates/documentation_generation/technical_docs/go_technical_docs.md) \| [C](templates/documentation_generation/technical_docs/c_technical_docs.md) \| [C++](templates/documentation_generation/technical_docs/cpp_technical_docs.md) |
| **API Docs** | Complete API reference | [Python](templates/documentation_generation/api_docs/python_api_docs.md) \| [JavaScript](templates/documentation_generation/api_docs/javascript_api_docs.md) \| [Java](templates/documentation_generation/api_docs/java_api_docs.md) \| [C#](templates/documentation_generation/api_docs/csharp_api_docs.md) \| [Go](templates/documentation_generation/api_docs/go_api_docs.md) \| [C](templates/documentation_generation/api_docs/c_api_docs.md) \| [C++](templates/documentation_generation/api_docs/cpp_api_docs.md) |
| **SBOM** | Software Bill of Materials | [Python](templates/documentation_generation/sbom/python_sbom.md) \| [JavaScript](templates/documentation_generation/sbom/javascript_sbom.md) \| [Java](templates/documentation_generation/sbom/java_sbom.md) \| [C#](templates/documentation_generation/sbom/csharp_sbom.md) \| [Go](templates/documentation_generation/sbom/go_sbom.md) \| [C](templates/documentation_generation/sbom/c_sbom.md) \| [C++](templates/documentation_generation/sbom/cpp_sbom.md) |

---

<a name="tests-generation"></a>

## 🧪 Tests Generation

**Generate comprehensive test suites with FIRST principles and AAA pattern**

### Quick Links by Phase

| Phase | What It Does | Click to Open |
|-------|--------------|---------------|
| **1. Test Structure** | Set up testing framework | [Python](templates/tests_generation/test_structure/python_test_structure.md) \| [JavaScript](templates/tests_generation/test_structure/javascript_test_structure.md) \| [Java](templates/tests_generation/test_structure/java_test_structure.md) \| [C#](templates/tests_generation/test_structure/csharp_test_structure.md) \| [Go](templates/tests_generation/test_structure/go_test_structure.md) \| [C](templates/tests_generation/test_structure/c_test_structure.md) \| [C++](templates/tests_generation/test_structure/cpp_test_structure.md) |
| **2. Unit Tests** | Generate unit tests | [Python](templates/tests_generation/unit_tests/python_unit_tests.md) \| [JavaScript](templates/tests_generation/unit_tests/javascript_unit_tests.md) \| [Java](templates/tests_generation/unit_tests/java_unit_tests.md) \| [C#](templates/tests_generation/unit_tests/csharp_unit_tests.md) \| [Go](templates/tests_generation/unit_tests/go_unit_tests.md) \| [C](templates/tests_generation/unit_tests/c_unit_tests.md) \| [C++](templates/tests_generation/unit_tests/cpp_unit_tests.md) |
| **3. Integration Tests** | E2E and integration | [Python](templates/tests_generation/test_cases/python_test_cases.md) \| [JavaScript](templates/tests_generation/test_cases/javascript_test_cases.md) \| [Java](templates/tests_generation/test_cases/java_test_cases.md) \| [C#](templates/tests_generation/test_cases/csharp_test_cases.md) \| [Go](templates/tests_generation/test_cases/go_test_cases.md) \| [C](templates/tests_generation/test_cases/c_test_cases.md) \| [C++](templates/tests_generation/test_cases/cpp_test_cases.md) |
| **4. Mocks & Fixtures** | Test isolation | [Python](templates/tests_generation/mocks_fixtures/python_mocks_fixtures.md) \| [JavaScript](templates/tests_generation/mocks_fixtures/javascript_mocks_fixtures.md) \| [Java](templates/tests_generation/mocks_fixtures/java_mocks_fixtures.md) \| [C#](templates/tests_generation/mocks_fixtures/csharp_mocks_fixtures.md) \| [Go](templates/tests_generation/mocks_fixtures/go_mocks_fixtures.md) \| [C](templates/tests_generation/mocks_fixtures/c_mocks_fixtures.md) \| [C++](templates/tests_generation/mocks_fixtures/cpp_mocks_fixtures.md) |
| **5. Performance Tests** | Load and stress | [Python](templates/tests_generation/performance_testing/python_performance_testing.md) \| [JavaScript](templates/tests_generation/performance_testing/javascript_performance_testing.md) \| [Java](templates/tests_generation/performance_testing/java_performance_testing.md) \| [C#](templates/tests_generation/performance_testing/csharp_performance_testing.md) \| [Go](templates/tests_generation/performance_testing/go_performance_testing.md) \| [C](templates/tests_generation/performance_testing/c_performance_testing.md) \| [C++](templates/tests_generation/performance_testing/cpp_performance_testing.md) |
| **6. Code Coverage** | Achieve 80%+ | [Python](templates/tests_generation/code_coverage/python_code_coverage.md) \| [JavaScript](templates/tests_generation/code_coverage/javascript_code_coverage.md) \| [Java](templates/tests_generation/code_coverage/java_code_coverage.md) \| [C#](templates/tests_generation/code_coverage/csharp_code_coverage.md) \| [Go](templates/tests_generation/code_coverage/go_code_coverage.md) \| [C](templates/tests_generation/code_coverage/c_code_coverage.md) \| [C++](templates/tests_generation/code_coverage/cpp_code_coverage.md) |
| **7. CI/CD Integration** | Automate testing | [Python](templates/tests_generation/maintenance_cicd/python_maintenance_cicd.md) \| [JavaScript](templates/tests_generation/maintenance_cicd/javascript_maintenance_cicd.md) \| [Java](templates/tests_generation/maintenance_cicd/java_maintenance_cicd.md) \| [C#](templates/tests_generation/maintenance_cicd/csharp_maintenance_cicd.md) \| [Go](templates/tests_generation/maintenance_cicd/go_maintenance_cicd.md) \| [C](templates/tests_generation/maintenance_cicd/c_maintenance_cicd.md) \| [C++](templates/tests_generation/maintenance_cicd/cpp_maintenance_cicd.md) |
| **8. Test Validation** | Mutation testing | [Python](templates/tests_generation/reward_hacking/python_reward_hacking.md) \| [JavaScript](templates/tests_generation/reward_hacking/javascript_reward_hacking.md) \| [Java](templates/tests_generation/reward_hacking/java_reward_hacking.md) \| [C#](templates/tests_generation/reward_hacking/csharp_reward_hacking.md) \| [Go](templates/tests_generation/reward_hacking/go_reward_hacking.md) \| [C](templates/tests_generation/reward_hacking/c_reward_hacking.md) \| [C++](templates/tests_generation/reward_hacking/cpp_reward_hacking.md) |

> **🆕 NEW: C++ Google Test + VS Code + Copilot**
> 
> - **10-minute setup** from clone to running tests
> 
> - **[Complete Workflow Guide](templates/tests_generation/GOOGLE_TEST_VSCODE_WORKFLOW.md)** - Step-by-step setup
> 
> - **[Copilot Quick Reference](templates/tests_generation/unit_tests/COPILOT_QUICK_REFERENCE.md)** - 50+ AI prompts
> 
> - **[VS Code Configuration](templates/tests_generation/vscode_config/README.md)** - Ready-to-use configs

---

<a name="code-review"></a>

## 🔍 Code Review

**Comprehensive 6-phase code review methodology with severity classification**

### Quick Links by Phase

| Phase | What It Does | Click to Open |
|-------|--------------|---------------|
| **1. Context Analysis** | Understand project | [Python](templates/code_review/context_analysis/python_context_analysis.md) \| [JavaScript](templates/code_review/context_analysis/javascript_context_analysis.md) \| [Java](templates/code_review/context_analysis/java_context_analysis.md) \| [C#](templates/code_review/context_analysis/csharp_context_analysis.md) \| [Go](templates/code_review/context_analysis/go_context_analysis.md) \| [C](templates/code_review/context_analysis/c_context_analysis.md) \| [C++](templates/code_review/context_analysis/cpp_context_analysis.md) |
| **2. Code Quality** | Style & maintainability | [Python](templates/code_review/code_quality/python_code_quality.md) \| [JavaScript](templates/code_review/code_quality/javascript_code_quality.md) \| [Java](templates/code_review/code_quality/java_code_quality.md) \| [C#](templates/code_review/code_quality/csharp_code_quality.md) \| [Go](templates/code_review/code_quality/go_code_quality.md) \| [C](templates/code_review/code_quality/c_code_quality.md) \| [C++](templates/code_review/code_quality/cpp_code_quality.md) |
| **3. Security Review** | Vulnerability assessment | [Python](templates/code_review/security_review/python_security_review.md) \| [JavaScript](templates/code_review/security_review/javascript_security_review.md) \| [Java](templates/code_review/security_review/java_security_review.md) \| [C#](templates/code_review/security_review/csharp_security_review.md) \| [Go](templates/code_review/security_review/go_security_review.md) \| [C](templates/code_review/security_review/c_security_review.md) \| [C++](templates/code_review/security_review/cpp_security_review.md) |
| **4. Performance Review** | Optimization opportunities | [Python](templates/code_review/performance_review/python_performance_review.md) \| [JavaScript](templates/code_review/performance_review/javascript_performance_review.md) \| [Java](templates/code_review/performance_review/java_performance_review.md) \| [C#](templates/code_review/performance_review/csharp_performance_review.md) \| [Go](templates/code_review/performance_review/go_performance_review.md) \| [C](templates/code_review/performance_review/c_performance_review.md) \| [C++](templates/code_review/performance_review/cpp_performance_review.md) |
| **5. Testing Review** | Test quality & coverage | [Python](templates/code_review/testing_review/python_testing_review.md) \| [JavaScript](templates/code_review/testing_review/javascript_testing_review.md) \| [Java](templates/code_review/testing_review/java_testing_review.md) \| [C#](templates/code_review/testing_review/csharp_testing_review.md) \| [Go](templates/code_review/testing_review/go_testing_review.md) \| [C](templates/code_review/testing_review/c_testing_review.md) \| [C++](templates/code_review/testing_review/cpp_testing_review.md) |
| **6. Final Report** | Consolidated findings | [Python](templates/code_review/final_report/python_final_report.md) \| [JavaScript](templates/code_review/final_report/javascript_final_report.md) \| [Java](templates/code_review/final_report/java_final_report.md) \| [C#](templates/code_review/final_report/csharp_final_report.md) \| [Go](templates/code_review/final_report/go_final_report.md) \| [C](templates/code_review/final_report/c_final_report.md) \| [C++](templates/code_review/final_report/cpp_final_report.md) |

---

<a name="compliance-governance"></a>

## 🔒 Compliance & Governance

**Build organization-wide security posture with strategic governance frameworks and AI agent governance**

### Quick Links by Framework

| Framework | What It Does | Click to Open |
|-----------|--------------|---------------|
| **SOC 2 Type II** | Enterprise trust & security compliance | [Python](templates/compliance_governance/compliance_frameworks/python_soc2_compliance.md) \| [JavaScript](templates/compliance_governance/compliance_frameworks/javascript_soc2_compliance.md) \| [Java](templates/compliance_governance/compliance_frameworks/java_soc2_compliance.md) \| [C#](templates/compliance_governance/compliance_frameworks/csharp_soc2_compliance.md) \| [Go](templates/compliance_governance/compliance_frameworks/go_soc2_compliance.md) \| [C](templates/compliance_governance/compliance_frameworks/c_soc2_compliance.md) \| [C++](templates/compliance_governance/compliance_frameworks/cpp_soc2_compliance.md) |
| **ISO 27001** | Information security management (114 controls) | [Python](templates/compliance_governance/compliance_frameworks/python_iso27001_implementation.md) \| [JavaScript](templates/compliance_governance/compliance_frameworks/javascript_iso27001_implementation.md) \| [Java](templates/compliance_governance/compliance_frameworks/java_iso27001_implementation.md) \| [C#](templates/compliance_governance/compliance_frameworks/csharp_iso27001_implementation.md) \| [Go](templates/compliance_governance/compliance_frameworks/go_iso27001_implementation.md) \| [C](templates/compliance_governance/compliance_frameworks/c_iso27001_implementation.md) \| [C++](templates/compliance_governance/compliance_frameworks/cpp_iso27001_implementation.md) |
| **NIST AI RMF** | AI risk management framework | [Python](templates/compliance_governance/compliance_frameworks/python_nist_ai_rmf.md) \| [JavaScript](templates/compliance_governance/compliance_frameworks/javascript_nist_ai_rmf.md) \| [Java](templates/compliance_governance/compliance_frameworks/java_nist_ai_rmf.md) \| [C#](templates/compliance_governance/compliance_frameworks/csharp_nist_ai_rmf.md) \| [Go](templates/compliance_governance/compliance_frameworks/go_nist_ai_rmf.md) \| [C](templates/compliance_governance/compliance_frameworks/c_nist_ai_rmf.md) \| [C++](templates/compliance_governance/compliance_frameworks/cpp_nist_ai_rmf.md) |
| **PCI-DSS v4.0** | Payment card data security | [Python](templates/compliance_governance/compliance_frameworks/python_pci_dss_compliance.md) \| [JavaScript](templates/compliance_governance/compliance_frameworks/javascript_pci_dss_compliance.md) \| [Java](templates/compliance_governance/compliance_frameworks/java_pci_dss_compliance.md) \| [C#](templates/compliance_governance/compliance_frameworks/csharp_pci_dss_compliance.md) \| [Go](templates/compliance_governance/compliance_frameworks/go_pci_dss_compliance.md) \| [C](templates/compliance_governance/compliance_frameworks/c_pci_dss_compliance.md) \| [C++](templates/compliance_governance/compliance_frameworks/cpp_pci_dss_compliance.md) |
| **GDPR** | EU data protection & privacy | [Python](templates/compliance_governance/privacy_protection/python_gdpr_compliance.md) \| [JavaScript](templates/compliance_governance/privacy_protection/javascript_gdpr_compliance.md) \| [Java](templates/compliance_governance/privacy_protection/java_gdpr_compliance.md) \| [C#](templates/compliance_governance/privacy_protection/csharp_gdpr_compliance.md) \| [Go](templates/compliance_governance/privacy_protection/go_gdpr_compliance.md) \| [C](templates/compliance_governance/privacy_protection/c_gdpr_compliance.md) \| [C++](templates/compliance_governance/privacy_protection/cpp_gdpr_compliance.md) |
| **CCPA** | California consumer privacy | [Python](templates/compliance_governance/privacy_protection/python_ccpa_compliance.md) \| [JavaScript](templates/compliance_governance/privacy_protection/javascript_ccpa_compliance.md) \| [Java](templates/compliance_governance/privacy_protection/java_ccpa_compliance.md) \| [C#](templates/compliance_governance/privacy_protection/csharp_ccpa_compliance.md) \| [Go](templates/compliance_governance/privacy_protection/go_ccpa_compliance.md) \| [C](templates/compliance_governance/privacy_protection/c_ccpa_compliance.md) \| [C++](templates/compliance_governance/privacy_protection/cpp_ccpa_compliance.md) |
| **Risk Assessment** | Threat modeling & risk management | [Python](templates/compliance_governance/risk_management/python_risk_assessment.md) \| [JavaScript](templates/compliance_governance/risk_management/javascript_risk_assessment.md) \| [Java](templates/compliance_governance/risk_management/java_risk_assessment.md) \| [C#](templates/compliance_governance/risk_management/csharp_risk_assessment.md) \| [Go](templates/compliance_governance/risk_management/go_risk_assessment.md) \| [C](templates/compliance_governance/risk_management/c_risk_assessment.md) \| [C++](templates/compliance_governance/risk_management/cpp_risk_assessment.md) |
| **Security Policies** | Organization-wide governance policies | [Python](templates/compliance_governance/governance_policies/python_security_policies.md) \| [JavaScript](templates/compliance_governance/governance_policies/javascript_security_policies.md) \| [Java](templates/compliance_governance/governance_policies/java_security_policies.md) \| [C#](templates/compliance_governance/governance_policies/csharp_security_policies.md) \| [Go](templates/compliance_governance/governance_policies/go_security_policies.md) \| [C](templates/compliance_governance/governance_policies/c_security_policies.md) \| [C++](templates/compliance_governance/governance_policies/cpp_security_policies.md) |
| **Incident Response** | Breach protocols & recovery procedures | [Python](templates/compliance_governance/incident_response/python_incident_response_plan.md) \| [JavaScript](templates/compliance_governance/incident_response/javascript_incident_response_plan.md) \| [Java](templates/compliance_governance/incident_response/java_incident_response_plan.md) \| [C#](templates/compliance_governance/incident_response/csharp_incident_response_plan.md) \| [Go](templates/compliance_governance/incident_response/go_incident_response_plan.md) \| [C](templates/compliance_governance/incident_response/c_incident_response_plan.md) \| [C++](templates/compliance_governance/incident_response/cpp_incident_response_plan.md) |
| **AI Agent Governance** | 4 Pillars: Lifecycle, Risk, Security, Observability | [Python](templates/compliance_governance/ai_agent_governance/python_agent_lifecycle.md) \| [JavaScript](templates/compliance_governance/ai_agent_governance/javascript_agent_lifecycle.md) \| [Java](templates/compliance_governance/ai_agent_governance/java_agent_lifecycle.md) \| [C#](templates/compliance_governance/ai_agent_governance/csharp_agent_lifecycle.md) \| [Go](templates/compliance_governance/ai_agent_governance/go_agent_lifecycle.md) \| [C](templates/compliance_governance/ai_agent_governance/c_agent_lifecycle.md) \| [C++](templates/compliance_governance/ai_agent_governance/cpp_agent_lifecycle.md) |

> **What you get:**
>
> - Comprehensive compliance frameworks (SOC 2, ISO 27001, PCI-DSS, GDPR, CCPA)
>
> - AI-specific governance (ISO 42001, NIST AI RMF, 4 Pillars Framework)
>
> - Production-ready code examples for all security controls
>
> - Audit preparation and evidence collection guidance
>
> - Integration with [Security Review](#code-review) templates

> **New for 2025:**
>
> - **4 Pillars AI Agent Governance**: Lifecycle Management, Risk Management, Security, Observability
>
> - **ISO 42001**: First international standard for AI Management Systems
>
> - **AI-enhanced SOC 2**: Model security, bias testing, inference logging
>
> - Research-backed best practices from [McKinsey](https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/deploying-agentic-ai-with-safety-and-security-a-playbook-for-technology-leaders), [Bain](https://www.bain.com/insights/building-the-foundation-for-agentic-ai-technology-report-2025/), [AWS](https://aws.amazon.com/blogs/machine-learning/advancing-ai-agent-governance-with-boomi-and-aws-a-unified-approach-to-observability-and-compliance/), [NIST](https://www.nist.gov/itl/ai-risk-management-framework)

**[→ View Complete Compliance & Governance Documentation](templates/compliance_governance/README.md)**

---

<a name="codebase-cleanup"></a>

## 🧹 Codebase Cleanup

**Remove dead code, duplication, and legacy patterns with multi-pass validation**

### Quick Links by Language

| Language | Click to Open |
|----------|---------------|
| **Python** | [Python Cleanup Template](templates/code_cleanup/python_cleanup.md) |
| **JavaScript** | [JavaScript Cleanup Template](templates/code_cleanup/javascript_cleanup.md) |
| **Java** | [Java Cleanup Template](templates/code_cleanup/java_cleanup.md) |
| **C#** | [C# Cleanup Template](templates/code_cleanup/csharp_cleanup.md) |
| **Go** | [Go Cleanup Template](templates/code_cleanup/go_cleanup.md) |
| **C** | [C Cleanup Template](templates/code_cleanup/c_cleanup.md) |
| **C++** | [C++ Cleanup Template](templates/code_cleanup/cpp_cleanup.md) |

> **What you get:**
> 
> - Dead code removal
> 
> - Duplication elimination
> 
> - Legacy pattern modernization
> 
> - Stopping criteria to prevent over-cleaning

---

## 📊 Repository Statistics

| Metric | Count |
|--------|-------|
| **Templates** | 277 production-ready templates |
| **Languages** | 7 (Python, JavaScript, Java, C#, Go, C, C++) |
| **Claude Code Skills** | 47 autonomous development skills |
| **Compliance Frameworks** | 8 frameworks (SOC 2, ISO 27001, NIST AI RMF, PCI-DSS, GDPR, CCPA) |
| **AI Agent Governance** | 4 Pillars (Lifecycle, Risk, Security, Observability) |
| **Test Phases** | 8-phase testing methodology |
| **Review Phases** | 6-phase review methodology |
| **Doc Types** | 6 documentation types |

---

## 📚 Guides

Comprehensive guides for getting started and mastering AI-assisted development:

- **[Coding Assistant Guide](guides/CODING_ASSISTANT_GUIDE.md)** - Setup and usage for GitHub Copilot, Cursor, Windsurf, ChatGPT, and Claude
- **[Claude Code Guide](guides/CLAUDE_CODE_GUIDE.md)** - Setup and autonomous workflows with Claude Code
- **[Contributing Guide](guides/CONTRIBUTING.md)** - How to contribute to this repository

---

## 🤝 Contributing

See [Contributing Guide](guides/CONTRIBUTING.md) for guidelines on:

- Adding new templates

- Improving existing templates

- Reporting issues

- Submitting pull requests

---

**Made with ❤️ for developers using AI coding assistants**
