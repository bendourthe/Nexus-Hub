# SBOM Generation

## 📋 Overview

This template provides comprehensive guidance for generating Software Bill of Materials (SBOM) documents that meet regulatory requirements including NTIA minimum elements and EU Cyber Resilience Act standards.

## 🎯 Objective

Generate complete, standards-compliant SBOM documentation that inventories all software components, dependencies, versions, licenses, and known vulnerabilities for security, compliance, and supply chain management.

## 📂 Available Templates

| Language | Template File |
|----------|---------------|
| **Python** | [python_sbom.md](python_sbom.md) |
| **JavaScript/TypeScript** | [javascript_sbom.md](javascript_sbom.md) |
| **Java** | [java_sbom.md](java_sbom.md) |
| **C#** | [csharp_sbom.md](csharp_sbom.md) |
| **Go** | [go_sbom.md](go_sbom.md) |
| **C** | [c_sbom.md](c_sbom.md) |
| **C++** | [cpp_sbom.md](cpp_sbom.md) |

## ✅ Key Areas Covered

- **NTIA Minimum Elements**: Required components for SBOM compliance
- **EU Cyber Resilience Act**: CRA-specific requirements
- **Dependency Tree**: Complete dependency graph with versions
- **License Information**: License identification and compliance
- **Known Vulnerabilities**: CVE tracking and security advisories
- **Supply Chain Security**: Component provenance and integrity

## 🚀 Quick Start

1. Determine compliance requirements (NTIA, EU CRA, etc.)
2. Use the comprehensive prompt in `python_sbom.md`
3. Generate SBOM in required format (SPDX, CycloneDX)
4. Review for completeness and accuracy
5. Integrate SBOM generation into CI/CD pipeline

## 📊 Success Criteria

- [ ] SBOM includes all NTIA minimum elements
- [ ] EU Cyber Resilience Act requirements met (if applicable)
- [ ] Complete dependency tree with versions documented
- [ ] All licenses identified and documented
- [ ] Known vulnerabilities tracked and documented
- [ ] SBOM format standard-compliant (SPDX or CycloneDX)
- [ ] Automated SBOM generation integrated in build process
- [ ] SBOM updated with each release

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
