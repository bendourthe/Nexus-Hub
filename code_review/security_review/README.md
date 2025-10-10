# Security Review

## 📋 Overview

Security review identifies vulnerabilities, insecure coding practices, and compliance gaps that could expose the application to attacks or data breaches. This phase examines authentication, authorization, data protection, dependency vulnerabilities, and adherence to security best practices.

## 🎯 Objectives

- Identify common vulnerabilities (OWASP Top 10)
- Audit dependencies for known security issues
- Detect hardcoded secrets and credentials
- Evaluate authentication and authorization mechanisms
- Assess data protection and encryption practices
- Review compliance with security standards

## 📂 Available Templates

| Language | Template File |
|----------|---------------|
| **Python** | [python_security_review.md](python_security_review.md) |
| **JavaScript/TypeScript** | [javascript_security_review.md](javascript_security_review.md) |
| **Java** | [java_security_review.md](java_security_review.md) |
| **C#** | [csharp_security_review.md](csharp_security_review.md) |
| **Go** | [go_security_review.md](go_security_review.md) |
| **C** | [c_security_review.md](c_security_review.md) |
| **C++** | [cpp_security_review.md](cpp_security_review.md) |

## ✅ Success Criteria

- [ ] Vulnerability scan completed with findings categorized
- [ ] Dependency security audit performed
- [ ] Secrets and credentials detection completed
- [ ] Authentication/authorization mechanisms evaluated
- [ ] Data protection practices assessed
- [ ] Compliance gaps identified with remediation plan

---

[← Back to Code Review](../README.md)
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
