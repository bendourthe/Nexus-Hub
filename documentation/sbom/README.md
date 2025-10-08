# SBOM Generation

## 📋 Overview

This template provides comprehensive guidance for generating Software Bill of Materials (SBOM) documents that meet regulatory requirements including NTIA minimum elements and EU Cyber Resilience Act standards.

## 🎯 Objective

Generate complete, standards-compliant SBOM documentation that inventories all software components, dependencies, versions, licenses, and known vulnerabilities for security, compliance, and supply chain management.

## 📂 Template

- **[Python SBOM](python_sbom.md)**: Complete SBOM generation prompt

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
