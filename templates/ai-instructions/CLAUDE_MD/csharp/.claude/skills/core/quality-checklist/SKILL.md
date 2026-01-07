---
name: quality-checklist
description: Pre-delivery quality assurance checklist for code and projects. Use before completing any coding task, finishing a feature, preparing for code review, or delivering a project milestone.
---

# Quality Assurance Checklist

Use this checklist before delivering code or completing tasks to ensure quality standards are met.

## Before Delivering Code

### Functionality
- [ ] **Solves the Problem**: Code addresses the stated requirement
- [ ] **Works Correctly**: Tested manually or with automated tests
- [ ] **Edge Cases**: Common edge cases handled
- [ ] **Error Handling**: Appropriate error handling in place

### Code Quality
- [ ] **Follows Standards**: Adheres to project coding standards
- [ ] **Clean Code**: Readable, well-organized, no dead code
- [ ] **Naming**: Variables, functions, classes have clear names
- [ ] **DRY**: No unnecessary duplication

### Documentation
- [ ] **Comments**: Complex logic has explanatory comments
- [ ] **Docstrings**: Public functions/methods documented
- [ ] **README Updates**: If applicable, documentation updated

### Type Safety (if applicable)
- [ ] **Type Hints**: Added for function parameters and returns
- [ ] **Type Checker**: Passes mypy/TypeScript/etc. without errors

### Testing
- [ ] **Unit Tests**: Core logic has test coverage
- [ ] **Tests Pass**: All existing tests still pass
- [ ] **Test Quality**: Tests are meaningful, not just for coverage

### Security
- [ ] **No Secrets**: No hardcoded credentials or API keys
- [ ] **Input Validation**: User inputs validated/sanitized
- [ ] **SQL Injection**: Parameterized queries used
- [ ] **XSS Prevention**: Output properly escaped (if web)

### Performance
- [ ] **Efficiency**: No obvious performance issues
- [ ] **Resource Usage**: Memory/CPU usage reasonable
- [ ] **Scalability**: Considered for expected load

## Before Delivering Project/Feature

### Completeness
- [ ] **All Requirements**: Every requirement addressed
- [ ] **Integration**: Components work together correctly
- [ ] **Configuration**: Environment configs documented

### Architecture
- [ ] **Standard Structure**: Follows project architecture
- [ ] **Dependencies**: All dependencies declared
- [ ] **No Circular Deps**: Clean dependency graph

### Documentation
- [ ] **README**: Setup and usage documented
- [ ] **API Docs**: Endpoints/interfaces documented
- [ ] **CHANGELOG**: Changes recorded

### DevOps
- [ ] **Builds**: Project builds without errors
- [ ] **CI/CD**: Pipeline passes
- [ ] **Environment**: Works in target environment

### Version Control
- [ ] **Clean History**: Commits are logical units
- [ ] **Branch Updated**: Rebased/merged with main
- [ ] **No Conflicts**: Merge conflicts resolved

## Quick Verification Commands

```bash
# Run linter
[project-specific lint command]

# Run type checker
[project-specific type check command]

# Run tests
[project-specific test command]

# Build project
[project-specific build command]
```

## Common Issues to Check

### Python
- [ ] Virtual environment activated
- [ ] Requirements.txt / pyproject.toml updated
- [ ] `__init__.py` files present where needed
- [ ] No relative import issues

### JavaScript/TypeScript
- [ ] package.json dependencies updated
- [ ] No `any` types without justification
- [ ] ESLint errors resolved
- [ ] Build output is correct

### Database
- [ ] Migrations created and tested
- [ ] Indexes added for query patterns
- [ ] No N+1 query problems

## When to Skip Items

Some checklist items may not apply:

- **Prototype/POC**: Focus on functionality over polish
- **Hotfix**: Focus on the fix, document for follow-up
- **Refactoring**: Focus on existing test coverage
- **Documentation-only**: Skip code-related items

Always note what was intentionally skipped and why.
