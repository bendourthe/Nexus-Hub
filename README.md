# AI Development Templates

**Version 0.3.0**

> **178 production-ready templates** for AI-assisted software development across 7 languages
>
> Copy prompts → Paste into AI assistant → Get production-quality code

---

## 🎉 What's New in v0.3.0

### Google Test + VS Code + GitHub Copilot Integration

- ⚡ **10-minute setup** from clone to running tests (vs. 1-2 hours manual)
- 🤖 **AI-assisted testing** with GitHub Copilot generating 15+ comprehensive test suites
- ⌨️ **One-click build/test/debug** with keyboard shortcuts
- 📊 **Automated code coverage** with lcov/gcovr
- 🔄 **Cross-platform** support (Linux, macOS, Windows)

**New Files:**

- [Complete Workflow Guide](templates/test_development/GOOGLE_TEST_VSCODE_WORKFLOW.md) - 10-step setup

- [Copilot Quick Reference](templates/test_development/unit_tests/COPILOT_QUICK_REFERENCE.md) - 50+ AI prompts

- [VS Code Configuration](templates/test_development/vscode_config/README.md) - Ready-to-use configs

[View Complete Changelog](CHANGELOG.md)

---

## 🎯 Quick Navigation

**I want to...**

- **[Configure my AI Assistant](#%EF%B8%8F-ai-instructions)** → Claude Code, GitHub Copilot, Cursor
- **[Generate Code Documentation](#-documentation)** → API docs, README, docstrings
- **[Generate Tests](#-test-development)** → Unit tests, code coverage, CI/CD integration
- **[Review My Code](#-code-review)** → Security, performance, quality
- **[Clean Up My Codebase](#-code-cleanup)** → Remove dead code, duplication, legacy patterns

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

## ⚙️ AI Instructions Configuration

**Configure your AI coding assistant with language-specific system prompts**

### Coding Assistants
> GitHub Copilot / Cursor / Windsurf

| Language | Comprehensive | Condensed |
|----------|---------------|-----------|
| **Python** | [35k tokens](templates/ai_instructions/coding_assistants/python/GLOBAL_comprehensive_40k.md) | [15k tokens](templates/ai_instructions/coding_assistants/python/GLOBAL_condensed_15k.md) |
| **JavaScript** | [35k tokens](templates/ai_instructions/coding_assistants/javascript/GLOBAL_comprehensive_40k.md) | [15k tokens](templates/ai_instructions/coding_assistants/javascript/GLOBAL_condensed_15k.md) |
| **Java** | [35k tokens](templates/ai_instructions/coding_assistants/java/GLOBAL_comprehensive_40k.md) | [15k tokens](templates/ai_instructions/coding_assistants/java/GLOBAL_condensed_15k.md) |
| **C#** | [35k tokens](templates/ai_instructions/coding_assistants/csharp/GLOBAL_comprehensive_40k.md) | [15k tokens](templates/ai_instructions/coding_assistants/csharp/GLOBAL_condensed_15k.md) |
| **Go** | [35k tokens](templates/ai_instructions/coding_assistants/go/GLOBAL_comprehensive_40k.md) | [15k tokens](templates/ai_instructions/coding_assistants/go/GLOBAL_condensed_15k.md) |
| **C** | [35k tokens](templates/ai_instructions/coding_assistants/c/GLOBAL_comprehensive_40k.md) | [15k tokens](templates/ai_instructions/coding_assistants/c/GLOBAL_condensed_15k.md) |
| **C++** | [35k tokens](templates/ai_instructions/coding_assistants/cpp/GLOBAL_comprehensive_40k.md) | [15k tokens](templates/ai_instructions/coding_assistants/cpp/GLOBAL_condensed_15k.md) |

> **Comprehensive Instructions (35k characters):** Best for complex projects that require highly detailed rules.
>
> **Condensed (15k characters):** Best for quick and efficient tasks.

### Agentic Systems
> Claude Code, Codex CLI, Gemini CLI

| Language | Comprehensive | Condensed |
|----------|---------------|-----------|
| **Python** | [40k tokens](templates/ai_instructions/autonomous_agents/claude_code/python/CLAUDE_comprehensive_40k.md) | [20k tokens](templates/ai_instructions/autonomous_agents/claude_code/python/CLAUDE_condensed_20k.md) |
| **JavaScript** | [40k tokens](templates/ai_instructions/autonomous_agents/claude_code/javascript/CLAUDE_comprehensive_40k.md) | [20k tokens](templates/ai_instructions/autonomous_agents/claude_code/javascript/CLAUDE_condensed_20k.md) |
| **Java** | [40k tokens](templates/ai_instructions/autonomous_agents/claude_code/java/CLAUDE_comprehensive_40k.md) | [20k tokens](templates/ai_instructions/autonomous_agents/claude_code/java/CLAUDE_condensed_20k.md) |
| **C#** | [40k tokens](templates/ai_instructions/autonomous_agents/claude_code/csharp/CLAUDE_comprehensive_40k.md) | [20k tokens](templates/ai_instructions/autonomous_agents/claude_code/csharp/CLAUDE_condensed_20k.md) |
| **Go** | [40k tokens](templates/ai_instructions/autonomous_agents/claude_code/go/CLAUDE_comprehensive_40k.md) | [20k tokens](templates/ai_instructions/autonomous_agents/claude_code/go/CLAUDE_condensed_20k.md) |
| **C** | [40k tokens](templates/ai_instructions/autonomous_agents/claude_code/c/CLAUDE_comprehensive_40k.md) | [20k tokens](templates/ai_instructions/autonomous_agents/claude_code/c/CLAUDE_condensed_20k.md) |
| **C++** | [40k tokens](templates/ai_instructions/autonomous_agents/claude_code/cpp/CLAUDE_comprehensive_40k.md) | [20k tokens](templates/ai_instructions/autonomous_agents/claude_code/cpp/CLAUDE_condensed_20k.md) |

> **Comprehensive Instructions (40k characters):** Best for complex projects that require highly detailed rules.
>
> **Condensed (20k characters):** Best for quick and efficient tasks.
>
> **48 Claude Code Skills Available:** [View Skills Catalog](templates/ai_instructions/autonomous_agents/claude_code/skills/README.md)

### AI Instructions Setup

- **Copilot:** Create `.github/copilot-instructions.md` and paste content
- **Cursor:** File → Preferences → Cursor Settings → Rules & Memories → User Rules
- **Windsurf:** Cascade → Customizations → Rules → Edit global_windsurf.md
- **Claude Code:** Save selected markdown file as CLAUDE.md in the root directory of your project

---

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

## 🧪 Test Development

**Generate comprehensive test suites with FIRST principles and AAA pattern**

### Quick Links by Phase

| Phase | What It Does | Click to Open |
|-------|--------------|---------------|
| **1. Test Structure** | Set up testing framework | [Python](templates/test_development/test_structure/python_test_structure.md) \| [JavaScript](templates/test_development/test_structure/javascript_test_structure.md) \| [Java](templates/test_development/test_structure/java_test_structure.md) \| [C#](templates/test_development/test_structure/csharp_test_structure.md) \| [Go](templates/test_development/test_structure/go_test_structure.md) \| [C](templates/test_development/test_structure/c_test_structure.md) \| [C++](templates/test_development/test_structure/cpp_test_structure.md) |
| **2. Unit Tests** | Generate unit tests | [Python](templates/test_development/unit_tests/python_unit_tests.md) \| [JavaScript](templates/test_development/unit_tests/javascript_unit_tests.md) \| [Java](templates/test_development/unit_tests/java_unit_tests.md) \| [C#](templates/test_development/unit_tests/csharp_unit_tests.md) \| [Go](templates/test_development/unit_tests/go_unit_tests.md) \| [C](templates/test_development/unit_tests/c_unit_tests.md) \| [C++](templates/test_development/unit_tests/cpp_unit_tests.md) |
| **3. Integration Tests** | E2E and integration | [Python](templates/test_development/test_cases/python_test_cases.md) \| [JavaScript](templates/test_development/test_cases/javascript_test_cases.md) \| [Java](templates/test_development/test_cases/java_test_cases.md) \| [C#](templates/test_development/test_cases/csharp_test_cases.md) \| [Go](templates/test_development/test_cases/go_test_cases.md) \| [C](templates/test_development/test_cases/c_test_cases.md) \| [C++](templates/test_development/test_cases/cpp_test_cases.md) |
| **4. Mocks & Fixtures** | Test isolation | [Python](templates/test_development/mocks_fixtures/python_mocks_fixtures.md) \| [JavaScript](templates/test_development/mocks_fixtures/javascript_mocks_fixtures.md) \| [Java](templates/test_development/mocks_fixtures/java_mocks_fixtures.md) \| [C#](templates/test_development/mocks_fixtures/csharp_mocks_fixtures.md) \| [Go](templates/test_development/mocks_fixtures/go_mocks_fixtures.md) \| [C](templates/test_development/mocks_fixtures/c_mocks_fixtures.md) \| [C++](templates/test_development/mocks_fixtures/cpp_mocks_fixtures.md) |
| **5. Performance Tests** | Load and stress | [Python](templates/test_development/performance_testing/python_performance_testing.md) \| [JavaScript](templates/test_development/performance_testing/javascript_performance_testing.md) \| [Java](templates/test_development/performance_testing/java_performance_testing.md) \| [C#](templates/test_development/performance_testing/csharp_performance_testing.md) \| [Go](templates/test_development/performance_testing/go_performance_testing.md) \| [C](templates/test_development/performance_testing/c_performance_testing.md) \| [C++](templates/test_development/performance_testing/cpp_performance_testing.md) |
| **6. Code Coverage** | Achieve 80%+ | [Python](templates/test_development/code_coverage/python_code_coverage.md) \| [JavaScript](templates/test_development/code_coverage/javascript_code_coverage.md) \| [Java](templates/test_development/code_coverage/java_code_coverage.md) \| [C#](templates/test_development/code_coverage/csharp_code_coverage.md) \| [Go](templates/test_development/code_coverage/go_code_coverage.md) \| [C](templates/test_development/code_coverage/c_code_coverage.md) \| [C++](templates/test_development/code_coverage/cpp_code_coverage.md) |
| **7. CI/CD Integration** | Automate testing | [Python](templates/test_development/maintenance_cicd/python_maintenance_cicd.md) \| [JavaScript](templates/test_development/maintenance_cicd/javascript_maintenance_cicd.md) \| [Java](templates/test_development/maintenance_cicd/java_maintenance_cicd.md) \| [C#](templates/test_development/maintenance_cicd/csharp_maintenance_cicd.md) \| [Go](templates/test_development/maintenance_cicd/go_maintenance_cicd.md) \| [C](templates/test_development/maintenance_cicd/c_maintenance_cicd.md) \| [C++](templates/test_development/maintenance_cicd/cpp_maintenance_cicd.md) |
| **8. Test Validation** | Mutation testing | [Python](templates/test_development/reward_hacking/python_reward_hacking.md) \| [JavaScript](templates/test_development/reward_hacking/javascript_reward_hacking.md) \| [Java](templates/test_development/reward_hacking/java_reward_hacking.md) \| [C#](templates/test_development/reward_hacking/csharp_reward_hacking.md) \| [Go](templates/test_development/reward_hacking/go_reward_hacking.md) \| [C](templates/test_development/reward_hacking/c_reward_hacking.md) \| [C++](templates/test_development/reward_hacking/cpp_reward_hacking.md) |

> **🆕 NEW: C++ Google Test + VS Code + Copilot**
> 
> - **10-minute setup** from clone to running tests
> 
> - **[Complete Workflow Guide](templates/test_development/GOOGLE_TEST_VSCODE_WORKFLOW.md)** - Step-by-step setup
> 
> - **[Copilot Quick Reference](templates/test_development/unit_tests/COPILOT_QUICK_REFERENCE.md)** - 50+ AI prompts
> 
> - **[VS Code Configuration](templates/test_development/vscode_config/README.md)** - Ready-to-use configs

---

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
| **Templates** | 178 production-ready templates |
| **Languages** | 7 (Python, JavaScript, Java, C#, Go, C, C++) |
| **Claude Code Skills** | 48 autonomous development skills |
| **Test Phases** | 8-phase testing methodology |
| **Review Phases** | 6-phase review methodology |
| **Doc Types** | 6 documentation types |

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding new templates
- Improving existing templates
- Reporting issues
- Submitting pull requests

---

**Made with ❤️ for developers using AI coding assistants**

[Browse Skills](https://bdourthe.github.io/ai_templates/) | [Quick Start](QUICKSTART.md) | [Template Finder](TEMPLATE_FINDER.md) | [Decision Trees](DECISION_TREES.md)
