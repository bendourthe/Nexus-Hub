# Docstring Generation

## 📋 Overview

This template provides a systematic approach to generating comprehensive, standards-compliant docstrings for Python code. It covers module-level documentation, class descriptions, function signatures with parameter types, and examples.

## 🎯 Objective

Generate clear, complete docstrings that document all public interfaces, explain purpose and behavior, include type information, and provide usage examples following industry standards (Google, NumPy, or reStructuredText style).

## 📂 Available Templates

| Language | Template File |
|----------|---------------|
| **Python** | [python_docstrings.md](python_docstrings.md) |
| **JavaScript/TypeScript** | [javascript_docstrings.md](javascript_docstrings.md) |
| **Java** | [java_docstrings.md](java_docstrings.md) |
| **C#** | [csharp_docstrings.md](csharp_docstrings.md) |
| **Go** | [go_docstrings.md](go_docstrings.md) |
| **C** | [c_docstrings.md](c_docstrings.md) |
| **C++** | [cpp_docstrings.md](cpp_docstrings.md) |

## ✅ Key Areas Covered

- **Module Docstrings**: Package and module-level documentation
- **Class Docstrings**: Class purpose, attributes, and usage
- **Function Docstrings**: Parameters, returns, exceptions, and examples
- **Type Hints Integration**: Coordinating docstrings with type annotations
- **Docstring Styles**: Support for Google, NumPy, and reStructuredText formats
- **Examples and Usage**: Practical code examples in docstrings

## 🚀 Quick Start

1. Choose your preferred docstring style (Google recommended for readability)
2. Use the comprehensive prompt template in `python_docstrings.md`
3. Request docstring generation for specific modules, classes, or entire codebase
4. Review and validate generated docstrings align with your standards

## 📊 Success Criteria

- [ ] All public modules, classes, and functions have docstrings
- [ ] Docstrings follow consistent style guide
- [ ] Parameter types and return values clearly documented
- [ ] Exceptions and edge cases explained
- [ ] Usage examples provided for complex interfaces
- [ ] Docstrings integrate properly with type hints

---

[← Back to Documentation](../README.md)
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
