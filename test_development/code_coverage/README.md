# Code Coverage Analysis

## Purpose
Measure, analyze, and improve test coverage to ensure comprehensive testing of the codebase. This includes line, branch, and function coverage measurement, gap identification, coverage reporting, and strategies for systematic improvement.

## What This Review Covers

### Coverage Measurement
- Line coverage (statement execution)
- Branch coverage (conditional paths)
- Function coverage (function execution)
- Missing coverage identification
- Coverage trends over time

### Coverage Tools
- coverage.py for measurement
- pytest-cov integration
- HTML coverage reports
- XML coverage for CI/CD
- Coverage badges and dashboards

### Coverage Analysis
- Critical path coverage
- Edge case coverage
- Error handling coverage
- Coverage gap prioritization
- Untested code identification

### Coverage Improvement
- Systematic gap closure
- Target setting (80%+ goal)
- Coverage thresholds in CI/CD
- Coverage regression prevention
- Balanced coverage strategy

## When to Use This Template
- Establishing coverage baselines
- Identifying untested code
- Setting coverage goals
- Improving test completeness
- Integrating coverage into CI/CD
- Preventing coverage regression

## Related Templates
- **Test Cases**: Filling coverage gaps
- **Test Structure**: Organizing coverage
- **CI/CD Integration**: Enforcing thresholds
- **Code Quality**: Quality metrics

## Expected Outcomes
- Comprehensive coverage measurement
- Identified coverage gaps
- Coverage improvement plan
- Automated coverage reporting
- Coverage thresholds enforced
- Sustainable coverage practices

## Available Templates

| Language | Template File | Status |
|----------|--------------|---------|
| Python | `python_code_coverage.md` | Available |
| JavaScript | `javascript_code_coverage.md` | Coming Soon |
| Java | `java_code_coverage.md` | Coming Soon |
| C# | `csharp_code_coverage.md` | Coming Soon |
| Go | `go_code_coverage.md` | Coming Soon |
| C | `c_code_coverage.md` | Coming Soon |
| C++ | `cpp_code_coverage.md` | Coming Soon |

## Quick Start
Use the appropriate template file with your AI assistant to:
1. Set up coverage measurement infrastructure
2. Analyze current coverage and identify gaps
3. Establish coverage goals and thresholds
4. Implement strategies to improve coverage
5. Integrate coverage into CI/CD pipeline
6. Create coverage reports and dashboards
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
