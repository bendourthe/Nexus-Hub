# Documentation

## 📋 Overview

This section provides comprehensive documentation templates that enable systematic creation of high-quality code and project documentation. Templates cover docstrings, strategic comments, user guides, technical documentation, API references, and Software Bill of Materials (SBOM) generation for compliance.

## 🎯 Objectives

- Generate clear, comprehensive docstrings for all public interfaces
- Add strategic comments that explain "why" not "what"
- Create user-friendly documentation (README, guides, tutorials)
- Develop technical documentation for architecture and design decisions
- Generate complete API reference documentation
- Produce SBOM for security, compliance, and supply chain management

## 📂 Available Templates

### Supported Languages

Templates are available for the following languages:
- **Python** - General-purpose, data science, web development
- **JavaScript/TypeScript** - Web, Node.js, React, Angular, Vue
- **Java** - Enterprise, Spring Boot, Android
- **C#** - .NET, ASP.NET Core, Unity
- **Go** - Microservices, cloud-native
- **C** - Embedded systems, firmware, RTOS
- **C++** - Performance-critical, embedded, modern C++

### Documentation Phases

Each language has templates for all 6 documentation phases:

| Phase | Focus Areas | Available Languages |
|-------|-------------|---------------------|
| **[Docstrings](docstrings/)** | Code-level documentation (JSDoc, JavaDoc, XML docs, godoc, Doxygen) | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Comments](comments/)** | Strategic commenting guidelines (explain "why" not "what") | Python, JavaScript, Java, C#, Go, C, C++ |
| **[User Documentation](user_docs/)** | README, installation guides, quick starts, tutorials | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Technical Documentation](technical_docs/)** | Architecture, ADRs, design decisions, codebase walkthroughs | Python, JavaScript, Java, C#, Go, C, C++ |
| **[API Documentation](api_docs/)** | Complete API reference with examples (OpenAPI, gRPC) | Python, JavaScript, Java, C#, Go, C, C++ |
| **[SBOM Generation](sbom/)** | Software Bill of Materials for compliance (NTIA, EU CRA) | Python, JavaScript, Java, C#, Go, C, C++ |

## ✅ Success Criteria

- [ ] All public interfaces documented with clear docstrings
- [ ] Strategic comments added explaining complex logic
- [ ] User documentation complete and accessible
- [ ] Technical documentation captures architecture and design decisions
- [ ] API reference generated with examples
- [ ] SBOM generated meeting compliance requirements

---

[← Back to AI Templates](../README.md)
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
