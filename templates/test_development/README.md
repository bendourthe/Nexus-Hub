# Test Development Templates

**Complete 8-phase testing methodology from infrastructure setup to test quality validation**

[← Back to Main](../../README.md) | [Quick Start Guide](../../QUICKSTART.md) | [All Guides](../../guides/)

---

## 🚀 Quick Start

**New to testing?** Follow this path:

```
Your Testing Journey:
├─ Phase 1: Test Structure → Set up testing framework (2-4 hours)
├─ Phase 2: Unit Tests → Generate unit tests (3-6 hours) ⭐ START HERE if you already have a test framework
├─ Phase 3-8: Run as needed → Build on top of unit tests
```

**Most Popular:** Phase 2 (Unit Tests) - Jump straight here if you already have a testing framework!

**Copy & Paste Templates:**
1. Choose your language below
2. Click the phase you want
3. Scroll to "## Prompt Template" in that file
4. Copy the entire prompt
5. Paste into GitHub Copilot / ChatGPT / Claude

---

## 📋 Overview

This section provides comprehensive test development templates for creating robust, maintainable test suites through an 8-phase methodology.

**What You'll Get:**
- ✅ FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)
- ✅ AAA pattern (Arrange-Act-Assert)
- ✅ 20-30 test examples per language
- ✅ Anti-patterns guide
- ✅ CI/CD integration examples
- ✅ Mutation testing for test quality validation

## 🎯 Objectives

- Establish comprehensive test infrastructure and frameworks

- Implement effective unit testing following FIRST principles

- Develop thorough test cases covering all code paths

- Implement proper mocking and fixture strategies

- Create performance and load testing suites

- Integrate testing into CI/CD pipelines with quality gates

- Achieve and maintain 80%+ code coverage

- Validate test suite quality through mutation testing and reward hacking detection

## 📂 Available Templates

### Supported Languages

Templates are available for the following languages:

- **Python** - pytest, unittest, coverage.py

- **JavaScript/TypeScript** - Jest, Mocha, Cypress, Playwright

- **Java** - JUnit 5, Mockito, JaCoCo

- **C#** - xUnit, NUnit, Moq, Coverlet

- **Go** - testing package, testify, go test

- **C** - Unity, CUnit, gcov (embedded focus)

- **C++** - GoogleTest, Catch2, llvm-cov

### Testing Phases

Each language has templates for all 8 testing phases:

| Phase | Focus Areas | Available Languages |
|-------|-------------|---------------------|
| **[Test Structure](test_structure/)** | Framework setup, directory organization, configuration | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Unit Tests](unit_tests/)** | FIRST principles, AAA pattern, test isolation, fast execution | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Test Cases](test_cases/)** | Integration/e2e tests, workflow coverage, test scenarios | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Mocks & Fixtures](mocks_fixtures/)** | Test isolation, mocking strategies, test data factories | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Performance Testing](performance_testing/)** | Load testing, stress testing, benchmarking | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Maintenance & CI/CD](maintenance_cicd/)** | Test automation, quality gates, CI/CD integration | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Code Coverage](code_coverage/)** | Coverage analysis, gap identification, 80%+ target | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Reward Hacking](reward_hacking/)** | Test quality validation, mutation testing, weak test detection | Python, JavaScript, Java, C#, Go, C, C++ |

### Recommended Phase Order

For optimal results, follow this testing workflow:

1. **Test Structure** - Set up infrastructure
2. **Unit Tests** - Establish fast, isolated tests for individual components
3. **Test Cases** - Add integration and E2E tests for workflows
4. **Mocks & Fixtures** - Implement proper test isolation
5. **Performance Testing** - Validate performance requirements
6. **Maintenance & CI/CD** - Automate testing in pipelines
7. **Code Coverage** - Measure and improve coverage
8. **Reward Hacking** - Validate test quality and effectiveness (FINAL PHASE)

## ✅ Success Criteria

- [ ] Test infrastructure established with appropriate frameworks

- [ ] Unit tests follow FIRST principles with fast execution (<1s per test)

- [ ] Comprehensive test cases covering all critical paths

- [ ] Mocking and fixtures properly implemented for test isolation

- [ ] Performance tests validate application under load

- [ ] CI/CD pipeline includes automated testing with quality gates

- [ ] Code coverage reaches and maintains 80%+ threshold

- [ ] Mutation testing validates test effectiveness (>80% mutation score)

- [ ] No reward hacking patterns detected in test suite

---

[← Back to AI Templates](../../README.md)
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
