# Python Docu4. [Phase 3: User Documentation](#phase-3-user-documentation)
5. [Phase 4: Technical Documentation](#phase-4-technical-documentation)
6. [Phase 5: API & Reference Documentation](#phase-5-api--reference-documentation)
7. [Phase 6: SBOM Generation](#phase-6-sbom-generation)
8. [Quick Reference](#quick-reference)ation - Comprehensive Protocol

A systematic approach to generating complete, professional documentation for Python applications following organizational standards.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Protocol Philosophy](#protocol-philosophy)
3. [How to Use This Protocol](#how-to-use-this-protocol)
4. [Phase 1: Docstrings & Code Documentation](#phase-1-docstrings--code-documentation)
5. [Phase 2: Code Comments & Inline Documentation](#phase-2-code-comments--inline-documentation)
6. [Phase 3: User Documentation](#phase-3-user-documentation)
7. [Phase 4: Technical Documentation](#phase-4-technical-documentation)
8. [Phase 5: API & Reference Documentation](#phase-5-api--reference-documentation)
9. [Quick Reference](#quick-reference)

---

## Overview

This protocol provides a structured, six-phase approach to creating comprehensive documentation for Python applications. Each phase addresses a specific documentation need, from code-level docstrings through SBOM generation.

### What This Protocol Covers

- **Docstrings**: Function, class, and module documentation following organizational templates
- **Code Comments**: Strategic commenting that explains reasoning and non-obvious logic
- **User Documentation**: README files, user guides, how-to sections, about pages
- **Technical Documentation**: Architecture, design decisions, codebase walkthroughs
- **API Documentation**: Reference documentation for public interfaces
- **SBOM**: Software Bill of Materials for security, compliance, and supply chain management

### Target Audience

- **Python Developers**: Documenting new projects or improving existing documentation
- **Technical Writers**: Establishing documentation standards for development teams
- **Team Leads**: Ensuring consistent documentation across projects
- **Open Source Maintainers**: Creating comprehensive project documentation

---

## Protocol Philosophy

### Core Principles

1. **Clarity Over Brevity**: Documentation should be clear and complete, not minimal
2. **Purpose-Driven**: Every piece of documentation serves a specific purpose
3. **Maintainability**: Documentation evolves with code and remains accurate
4. **Accessibility**: Written for appropriate audience skill levels
5. **Standards Compliance**: Follows organizational documentation guidelines

### Organizational Standards Alignment

This protocol implements documentation standards defined in organizational coding guidelines:

- **Docstring Templates**: Simple vs. complex function templates
- **Comment Guidelines**: No inline comments, focus on "why" not "what"
- **Comment Placement**: Above code blocks, not same-line
- **No Meta-Commentary**: No editing history or revision comments in code
- **Structured Documentation**: README, CHANGELOG, DEVLOG patterns

---

## How to Use This Protocol

### For New Projects

**Follow phases sequentially:**

1. **Phase 1** (1-2 hours): Generate docstrings for all functions, classes, and modules
2. **Phase 2** (1-2 hours): Add strategic code comments explaining logic and decisions
3. **Phase 3** (2-3 hours): Create user-facing documentation (README, guides)
4. **Phase 4** (2-4 hours): Generate technical documentation for developers
5. **Phase 5** (1-2 hours): Build API reference documentation
6. **Phase 6** (1-2 hours): Generate SBOM and dependency documentation

**Total Time Investment**: 8-15 hours for complete documentation

### For Existing Projects

**Selective application:**

- **Missing Docstrings**: Start with Phase 1
- **Poor Comments**: Focus on Phase 2
- **No User Guide**: Jump to Phase 3
- **Unclear Architecture**: Implement Phase 4
- **No API Docs**: Add Phase 5

### For Quick Documentation

**Minimal viable documentation:**

1. Phase 1: Core function docstrings (1 hour)
2. Phase 3: Basic README (30 min)
3. Phase 4: Architecture overview (30 min)

**Total Time**: ~2 hours for essential documentation

---

## Phase 1: Docstrings & Code Documentation

### Objective
Generate comprehensive docstrings for all functions, classes, and modules following organizational templates.

### Key Deliverables

**Docstring Coverage:**
- Module-level docstrings
- Class docstrings with purpose and usage
- Function/method docstrings (simple and complex templates)
- Parameter and return value documentation
- Exception documentation
- Author attribution

**Templates:**

**Simple Functions:**
```python
def calculate_total(items: List[float]) -> float:
    """Calculate total including tax."""
    pass
```

**Complex Functions:**
```python
def process_user_data(
    records: List[Dict], 
    rules: Dict[str, Any]
) -> List[Dict]:
    """
    Process and validate records according to rules.

    Parameters:
        - records: Raw data records
        - rules: Validation rules

    Returns:
        - Processed records

    Raises:
        - ValueError: Invalid rules
        - DataError: Processing failed

    Authors:
        - Benjamin Dourthe (benjamin@adonamed.com)
    """
    pass
```

**Classes:**
```python
class DataProcessor:
    """
    Process and validate data with caching.
    
    This class provides efficient data processing with built-in
    caching and validation capabilities.
    
    Attributes:
        config: Configuration dictionary
        cache: Internal result cache
        validator: Schema validator instance
    
    Authors:
        - Benjamin Dourthe (benjamin@adonamed.com)
    """
    pass
```

**Modules:**
```python
"""
Core data processing module.

This module provides the primary data processing functionality
including validation, transformation, and caching.

Key Components:
    - DataProcessor: Main processing class
    - ValidationError: Custom exception for validation failures
    - process_batch: Batch processing utility

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
```

[🔗 View detailed Phase 1 template](phase1_docstrings.md)

### Expected Time
- **Generation**: 1-2 hours
- **Review**: 30 minutes
- **Total**: 1-2 hours

### Success Criteria
- ✅ All public functions documented
- ✅ All classes documented
- ✅ Module-level documentation present
- ✅ Parameters and returns described
- ✅ Exceptions documented

---

## Phase 2: Code Comments & Inline Documentation

### Objective
Add strategic code comments that explain reasoning, non-obvious logic, and important decisions.

### Key Deliverables

**Comment Guidelines:**
- Comments above code blocks (never inline)
- Explain "why" not "what"
- Focus on non-obvious behavior
- Document performance considerations
- Explain algorithm choices
- Note security implications

**Comment Examples:**

**Algorithm Choice:**
```python
# Use binary search for O(log n) performance on sorted data
# This is critical for large datasets (>10k items)
result = binary_search(sorted_list, target)
```

**Performance Optimization:**
```python
# Cache results to avoid expensive API calls during batch processing
# API rate limit is 100 calls/minute, caching prevents exceeding it
if key not in self.cache:
    self.cache[key] = expensive_api_call(key)
```

**Implementation Decision:**
```python
# Implement exponential backoff for rate-limited APIs
# Start with 1 second, double each retry up to 32 seconds max
for attempt in range(max_retries):
    wait_time = min(2 ** attempt, 32)
    time.sleep(wait_time)
```

**Avoid:**
```python
# Bad: Obvious comment
x = x + 1  # Increment x

# Bad: Meta-commentary
# Updated 2024-10-05: Changed algorithm

# Bad: Inline comment
result = process(data)  # Process the data
```

[🔗 View detailed Phase 2 template](phase2_comments.md)

### Expected Time
- **Analysis**: 30-60 minutes
- **Writing**: 30-60 minutes
- **Total**: 1-2 hours

### Success Criteria
- ✅ Complex logic explained
- ✅ No inline comments
- ✅ Performance considerations noted
- ✅ Security implications documented
- ✅ Algorithm choices justified

---

## Phase 3: User Documentation

### Objective
Create comprehensive user-facing documentation including README, user guides, how-to sections, and about pages.

### Key Deliverables

**Documentation Files:**
- README.md with project overview
- User guide with installation and usage
- How-to sections for common tasks
- About page with project information
- CHANGELOG for version history
- DEVLOG for development tracking

**README.md Structure:**
```markdown
# [Project Name] - v[X.Y.Z]

## What's New
- [Key features/changes]

## Overview
[2-3 sentence description]

## Features
- [Core capabilities]

## Installation

### Prerequisites
- Python 3.9+
- [Other requirements]

### Setup
```bash
git clone [repo-url]
cd [project-name]
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .[dev]
```

## Usage
```python
from src.core import MainModule
result = MainModule.process("input")
```

## Configuration
[Configuration options]

## Testing
```bash
python tests/run_all_tests.py
```

## Contributing
[Contribution guidelines]

## License
[License information]

## Authors
- Benjamin Dourthe (benjamin@adonamed.com)
```

**User Guide Structure:**
- Getting Started
- Installation Instructions
- Basic Usage Examples
- Common Workflows
- Troubleshooting
- FAQ

**How-To Sections:**
- How to install and configure
- How to use core features
- How to customize behavior
- How to troubleshoot issues
- How to contribute

[🔗 View detailed Phase 3 template](phase3_user_docs.md)

### Expected Time
- **Writing**: 2-3 hours
- **Review**: 30 minutes
- **Total**: 2-3 hours

### Success Criteria
- ✅ Complete README with all sections
- ✅ Clear installation instructions
- ✅ Usage examples included
- ✅ Troubleshooting guide present
- ✅ CHANGELOG and DEVLOG current

---

## Phase 4: Technical Documentation

### Objective
Generate detailed technical documentation explaining architecture, design decisions, and codebase structure for developers.

### Key Deliverables

**Technical Documentation Components:**
- Architecture overview with diagrams
- Design decisions and rationale
- Module and component descriptions
- Data flow documentation
- Code organization explanation
- Dependencies and integrations
- Development environment setup
- Troubleshooting for developers

**Architecture Documentation:**
```markdown
# Technical Architecture

## System Overview
[High-level description of system architecture]

## Components

### Core Components
- **Component A**: [Purpose and responsibilities]
- **Component B**: [Purpose and responsibilities]

### Supporting Components
- **Utilities**: [Helper functions and utilities]
- **Configuration**: [Configuration management]

## Data Flow
[Diagram and explanation of data flow]

## Design Decisions

### Decision 1: [Title]
**Context**: [What problem needed solving]
**Decision**: [What was chosen]
**Rationale**: [Why this approach]
**Trade-offs**: [Pros and cons]
**Alternatives Considered**: [Other options]

## Module Structure
```
project/
├── src/
│   ├── core/          # Core business logic
│   ├── utils/         # Utility functions
│   └── config/        # Configuration
├── tests/             # Test suites
└── docs/              # Documentation
```

## Dependencies
- **External**: [Third-party libraries]
- **Internal**: [Inter-module dependencies]

## Development Guide
[Setup for developers]
```

**Codebase Walkthrough:**
```markdown
# Codebase Walkthrough

## Entry Points
- `src/main.py`: Application entry point
- `src/core/processor.py`: Main processing logic

## Core Modules

### src/core/processor.py
**Purpose**: Primary data processing
**Key Classes**:
- `DataProcessor`: Main processing class
  - `process()`: Entry point for processing
  - `validate()`: Data validation
  - `transform()`: Data transformation

**Key Functions**:
- `batch_process()`: Batch processing utility

### src/core/validators.py
**Purpose**: Data validation logic
**Key Classes**:
- `SchemaValidator`: Schema validation
- `BusinessRuleValidator`: Business rule validation

## Integration Points
[How modules integrate]

## Extension Points
[How to extend functionality]
```

[🔗 View detailed Phase 4 template](phase4_technical_docs.md)

### Expected Time
- **Analysis**: 1-2 hours
- **Writing**: 1-2 hours
- **Diagrams**: 30 minutes
- **Total**: 2-4 hours

### Success Criteria
- ✅ Architecture clearly explained
- ✅ Design decisions documented
- ✅ Module structure described
- ✅ Data flow illustrated
- ✅ Development guide complete

---

## Phase 5: API & Reference Documentation

### Objective
Build comprehensive API reference documentation for all public interfaces.

### Key Deliverables

**API Documentation Components:**
- Module API reference
- Class API reference
- Function API reference
- Parameter specifications
- Return value specifications
- Exception documentation
- Usage examples
- Code samples

**API Reference Format:**
```markdown
# API Reference

## Module: src.core.processor

### Classes

#### DataProcessor
Process and validate data with caching.

**Constructor**:
```python
DataProcessor(config: Dict[str, Any])
```

**Parameters**:
- `config`: Configuration dictionary
  - `timeout`: Request timeout in seconds (default: 30)
  - `cache_size`: Maximum cache entries (default: 1000)

**Methods**:

##### process(data: List[Dict]) -> List[Dict]
Process input data with validation and transformation.

**Parameters**:
- `data`: List of data records to process

**Returns**:
- List of processed and validated records

**Raises**:
- `ValueError`: If data format is invalid
- `ValidationError`: If validation fails

**Example**:
```python
processor = DataProcessor({'timeout': 60})
result = processor.process(input_data)
```

### Functions

#### batch_process(items: List[Any], batch_size: int = 100) -> List[Any]
Process items in batches for efficiency.

**Parameters**:
- `items`: Items to process
- `batch_size`: Number of items per batch (default: 100)

**Returns**:
- List of processed items

**Example**:
```python
results = batch_process(large_dataset, batch_size=50)
```
```

[🔗 View detailed Phase 5 template](phase5_api_docs.md)

### Expected Time
- **Generation**: 1-2 hours
- **Examples**: 30 minutes
- **Total**: 1-2 hours

### Success Criteria
- ✅ All public APIs documented
- ✅ Parameters fully specified
- ✅ Return values described
- ✅ Exceptions listed
- ✅ Usage examples included

---

## Phase 6: SBOM Generation

### Objective
Generate comprehensive Software Bill of Materials (SBOM) and dependency documentation for security, compliance, and supply chain management.

### Key Deliverables

**SBOM Files:**
- CycloneDX format (JSON/XML)
- SPDX format (optional)
- Machine-readable for automated processing

**Documentation:**
- Complete SBOM documentation (docs/SBOM.md)
- Third-party attribution notices
- License analysis and compliance
- Vulnerability scanning results
- Dependency provenance tracking

**Automation:**
- SBOM generation scripts
- Vulnerability monitoring setup
- Automated dependency updates (Dependabot)
- CI/CD integration

**SBOM Content:**
```markdown
# Software Bill of Materials

## Summary Statistics
- Total Components: [X] packages
- Direct Dependencies: [Y] packages
- Transitive Dependencies: [Z] packages
- Unique Licenses: [N] licenses
- Known Vulnerabilities: [M] issues

## Direct Dependencies
| Package | Version | License | Purpose |
|---------|---------|---------|----------|
| pandas | >=1.5.0 | BSD-3 | Data analysis |
| requests | >=2.28.0 | Apache-2.0 | HTTP client |

## Security Analysis
- Vulnerability scanning configured
- Known CVEs documented
- Remediation plans included

## Compliance
- NTIA minimum elements met
- EU Cyber Resilience Act compliant
- Export control classification
```

[🔗 View detailed Phase 6 template](phase6_sbom.md)

### Expected Time
- **Analysis**: 30 minutes
- **Generation**: 30-60 minutes
- **Documentation**: 30 minutes
- **Total**: 1-2 hours

### Success Criteria
- ✅ SBOM files generated (CycloneDX/SPDX)
- ✅ All dependencies cataloged
- ✅ All licenses documented
- ✅ Vulnerability scanning configured
- ✅ Attribution notices complete
- ✅ Compliance requirements met
- ✅ Automation configured

---

## Quick Reference

### Documentation Commands

```powershell
# Generate API documentation with Sphinx
sphinx-apidoc -o docs/api src/
sphinx-build -b html docs/ docs/_build

# Generate documentation with pdoc
pdoc --html --output-dir docs/ src/

# Check docstring coverage
interrogate src/ -v

# Validate markdown
markdownlint docs/**/*.md
```

### Docstring Templates

**Simple Function:**
```python
def function_name(param: Type) -> ReturnType:
    """Brief description of what function does."""
```

**Complex Function:**
```python
def function_name(
    param1: Type1,
    param2: Type2
) -> ReturnType:
    """
    Detailed description of function purpose.

    Parameters:
        - param1: Description of param1
        - param2: Description of param2

    Returns:
        - Description of return value

    Raises:
        - ExceptionType: When this exception occurs

    Authors:
        - Name (email@example.com)
    """
```

### Comment Guidelines

**Good Comments:**
```python
# Use binary search for O(log n) performance
# Cache to avoid expensive API calls
# Implement exponential backoff for rate limits
```

**Avoid:**
```python
# Bad: x = x + 1  # Increment x
# Bad: # Updated 2024-10-05
# Bad: result = func()  # Call function
```

### README Checklist

- [ ] Project name and version
- [ ] What's new section
- [ ] Overview (2-3 sentences)
- [ ] Features list
- [ ] Installation instructions
- [ ] Prerequisites
- [ ] Usage examples
- [ ] Configuration options
- [ ] Testing instructions
- [ ] Contributing guidelines
- [ ] License information
- [ ] Author information

### CHANGELOG Format

```markdown
# Changelog

## [Unreleased]
### Added
### Changed
### Fixed
### Removed

## [X.Y.Z] - YYYY-MM-DD
### Added
- New features
### Changed
- Improvements
### Fixed
- Bug fixes
```

---

## Summary

This comprehensive protocol provides everything needed to create professional, complete documentation that aligns with organizational standards. By following the six phases sequentially, you'll establish:

1. **Code-Level Documentation** (Phase 1): Comprehensive docstrings for all code elements
2. **Strategic Comments** (Phase 2): Explaining complex logic and important decisions
3. **User-Facing Docs** (Phase 3): README, guides, how-tos for end users
4. **Technical Documentation** (Phase 4): Architecture, design, and codebase explanations
5. **API Reference** (Phase 5): Complete reference documentation for developers
6. **SBOM & Dependencies** (Phase 6): Security, compliance, and supply chain documentation

**Total Investment**: 8-15 hours for complete documentation

**Long-term Value**: Easier onboarding, reduced support burden, better collaboration, professional presentation, regulatory compliance, improved security posture

---

*For detailed guidance on each phase, see the individual phase template files.*
