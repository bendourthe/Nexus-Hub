# Mocks & Fixtures

## Purpose
Establish effective mocking strategies and fixture management to isolate components under test, manage test data efficiently, and create maintainable test dependencies. This covers pytest fixtures, unittest.mock usage, and strategies for handling external dependencies.

## What This Review Covers

### Fixture Management
- Pytest fixture patterns and scopes
- Fixture composition and dependencies
- Fixture factories for flexible test data
- Fixture organization and reusability
- Teardown and cleanup strategies

### Mocking Strategies
- When to mock vs use real objects
- unittest.mock library usage
- Mocking external APIs and services
- Database mocking strategies
- File system and I/O mocking

### Test Data Management
- Test data factories and builders
- Fixture data organization
- Realistic vs minimal test data
- Data generation strategies
- Test data versioning

### Dependency Isolation
- Isolating external dependencies
- Mocking third-party libraries
- Test doubles (mocks, stubs, fakes, spies)
- Dependency injection for testability
- Avoiding over-mocking

## When to Use This Template
- Setting up test data infrastructure
- Mocking external services or APIs
- Creating reusable test fixtures
- Improving test isolation
- Refactoring tests with heavy setup
- Establishing mocking standards

## Related Templates
- **Test Structure**: Infrastructure and organization
- **Test Cases**: Actual test implementation
- **Integration Testing**: When to minimize mocking
- **Performance Testing**: Realistic data patterns

## Expected Outcomes
- Well-organized fixture library
- Effective mocking strategies
- Isolated, fast unit tests
- Maintainable test data
- Clear separation of test concerns
- Reduced test setup complexity

## Available Templates

| Language | Template File | Status |
|----------|--------------|---------|
| Python | `python_mocks_fixtures.md` | Available |
| JavaScript | `javascript_mocks_fixtures.md` | Available |
| Java | `java_mocks_fixtures.md` | Available |
| C# | `csharp_mocks_fixtures.md` | Available |
| Go | `go_mocks_fixtures.md` | Available |
| C | `c_mocks_fixtures.md` | Available |
| C++ | `cpp_mocks_fixtures.md` | Available |

## Quick Start
Use the appropriate template file with your AI assistant to:
1. Design fixture architecture for your tests
2. Implement reusable fixtures with appropriate scopes
3. Create effective mocks for external dependencies
4. Build test data factories
5. Establish mocking conventions and best practices
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
