# Phase 6: SBOM Generation & Dependency Documentation

Generate comprehensive Software Bill of Materials (SBOM) and dependency documentation for security, compliance, and supply chain management.

---

## Overview

This phase focuses on creating detailed Software Bill of Materials (SBOM) documentation that catalogs all software components, dependencies, licenses, and security information. SBOMs are increasingly required for regulatory compliance, security auditing, and supply chain risk management.

### Time Estimate
- **Dependency Analysis**: 30 minutes
- **SBOM Generation**: 30-60 minutes
- **Documentation**: 30 minutes
- **Total**: 1-2 hours

---

## Copy-Paste Prompt

```
Please help me generate comprehensive SBOM (Software Bill of Materials) and dependency documentation for my Python project.

**Project Context:**
- Project name: [YOUR_PROJECT_NAME]
- Version: [X.Y.Z]
- Package manager: [pip / poetry / conda]
- Deployment target: [Production / Open Source / Enterprise]
- Compliance requirements: [NIST / EU Cyber Resilience Act / NTIA / etc.]

---

## SBOM Requirements

### 1. Generate SBOM Files

Create SBOM files in multiple standard formats:

#### CycloneDX Format (Recommended)

```bash
# Install CycloneDX generator
pip install cyclonedx-bom

# Generate SBOM in JSON format
cyclonedx-py -o sbom.json -F json

# Generate SBOM in XML format
cyclonedx-py -o sbom.xml -F xml
```

**Generated file location**: `sbom.json` or `sbom.xml` in project root

#### SPDX Format

```bash
# Install SPDX tools
pip install spdx-tools

# Generate SPDX SBOM
# Manual generation or use tools like syft
```

#### Syft (Multi-format)

```bash
# Install Syft
# Windows: scoop install syft
# Linux/Mac: brew install syft

# Generate SBOM
syft packages . -o cyclonedx-json > sbom.json
syft packages . -o spdx-json > sbom-spdx.json
syft packages . -o table
```

---

### 2. SBOM Documentation (docs/SBOM.md)

Create comprehensive SBOM documentation:

```markdown
# Software Bill of Materials (SBOM)

## Overview

This document provides a comprehensive inventory of all software components, dependencies, and licenses used in [Project Name].

**Document Information**:
- **Project**: [Project Name]
- **Version**: [X.Y.Z]
- **Generated**: [YYYY-MM-DD]
- **SBOM Format**: CycloneDX 1.5 / SPDX 2.3
- **SBOM Location**: `sbom.json`, `sbom.xml`

## Purpose

This SBOM serves multiple purposes:
- **Security**: Identify vulnerable components for patching
- **Compliance**: Meet regulatory requirements (NTIA, EU CRA, etc.)
- **License Management**: Track and manage open source licenses
- **Supply Chain Risk**: Understand dependency provenance
- **Incident Response**: Rapid identification of affected components

## Summary Statistics

- **Total Components**: [X] packages
- **Direct Dependencies**: [Y] packages
- **Transitive Dependencies**: [Z] packages
- **Unique Licenses**: [N] different licenses
- **Known Vulnerabilities**: [M] (see Security section)

## Direct Dependencies

### Production Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| pandas | >=1.5.0 | BSD-3-Clause | Data manipulation and analysis |
| requests | >=2.28.0 | Apache-2.0 | HTTP client library |
| pydantic | >=2.0.0 | MIT | Data validation and parsing |
| [package] | [version] | [license] | [purpose] |

### Development Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| pytest | >=7.0.0 | MIT | Testing framework |
| black | >=22.0.0 | MIT | Code formatter |
| mypy | >=0.950 | MIT | Static type checker |
| [package] | [version] | [license] | [purpose] |

## Transitive Dependencies

Complete list of all indirect dependencies:

| Package | Version | Required By | License |
|---------|---------|-------------|---------|
| numpy | 1.24.3 | pandas | BSD-3-Clause |
| python-dateutil | 2.8.2 | pandas | Apache-2.0/BSD-3 |
| [package] | [version] | [parent] | [license] |

## License Analysis

### License Distribution

- **Permissive Licenses** (MIT, BSD, Apache): [X]% of dependencies
- **Copyleft Licenses** (GPL, LGPL): [Y]% of dependencies
- **Proprietary/Other**: [Z]% of dependencies

### License Compatibility

**Project License**: [Your License]

**Compatibility Assessment**:
- ✅ All dependencies compatible with project license
- ⚠️ [Package] has [license] - requires attribution
- ❌ No incompatible licenses detected

### License Details

#### Permissive Licenses

**MIT License** (X packages):
- pandas, requests, pydantic, [others]
- **Obligations**: Include copyright notice and license text
- **Restrictions**: None

**Apache License 2.0** (Y packages):
- [list packages]
- **Obligations**: Include copyright, license, and NOTICE file
- **Restrictions**: Trademark restrictions

**BSD-3-Clause** (Z packages):
- [list packages]
- **Obligations**: Include copyright notice
- **Restrictions**: Cannot use names for endorsement

#### Copyleft Licenses

**LGPL** (if any):
- [list packages]
- **Obligations**: Provide source code for modifications
- **Restrictions**: Dynamic linking allowed

## Security Analysis

### Vulnerability Scanning

Last scanned: [YYYY-MM-DD]

**Scan Results**:
- **Critical**: [N] vulnerabilities
- **High**: [N] vulnerabilities
- **Medium**: [N] vulnerabilities
- **Low**: [N] vulnerabilities

### Known Vulnerabilities

#### Critical Vulnerabilities

**CVE-YYYY-XXXXX** - [Package Name] [Version]
- **Severity**: Critical (CVSS 9.8)
- **Description**: [Brief description]
- **Affected Versions**: [version range]
- **Fixed In**: [version]
- **Remediation**: Update to [version] or higher
- **Status**: [Open / Patched / Mitigated]

### Vulnerability Mitigation

```bash
# Update vulnerable packages
pip install --upgrade [package]

# Or specify exact version
pip install [package]==[fixed-version]
```

### Security Scanning Tools

**Recommended Tools**:
```bash
# pip-audit - Check for known vulnerabilities
pip install pip-audit
pip-audit

# Safety - Database of known security vulnerabilities
pip install safety
safety check

# Bandit - Code security analysis
pip install bandit
bandit -r src/

# Snyk - Comprehensive security scanning
snyk test
```

## Component Provenance

### Package Sources

| Package | Source Repository | Integrity Check |
|---------|-------------------|-----------------|
| pandas | https://github.com/pandas-dev/pandas | SHA256 verified |
| requests | https://github.com/psf/requests | SHA256 verified |
| [package] | [repository URL] | [verification method] |

### Dependency Resolution

**Package Manager**: pip [version]
**Lock File**: requirements.txt / poetry.lock / Pipfile.lock
**Registry**: PyPI (https://pypi.org)

### Supply Chain Security

**Measures Implemented**:
- ✅ Dependencies installed from official PyPI
- ✅ Package integrity verified via SHA256 hashes
- ✅ Dependency versions pinned for reproducibility
- ✅ Regular vulnerability scanning
- ✅ Automated dependency updates via Dependabot

## Dependency Graph

### Top-Level Dependencies

```
[project-name]
├── pandas (>=1.5.0)
│   ├── numpy (>=1.21.0)
│   ├── python-dateutil (>=2.8.1)
│   └── pytz (>=2020.1)
├── requests (>=2.28.0)
│   ├── charset-normalizer (<4,>=2)
│   ├── idna (<4,>=2.5)
│   ├── urllib3 (<3,>=1.21.1)
│   └── certifi (>=2017.4.17)
└── pydantic (>=2.0.0)
    ├── typing-extensions (>=4.6.1)
    └── pydantic-core (==2.x.x)
```

### Generate Full Dependency Tree

```bash
# Using pipdeptree
pip install pipdeptree
pipdeptree --graph-output png > dependency-graph.png

# Using poetry
poetry show --tree

# Text format
pip install pipdeptree
pipdeptree > dependency-tree.txt
```

## Compliance Information

### Regulatory Compliance

**NTIA Minimum Elements** (US Executive Order 14028):
- ✅ Supplier name
- ✅ Component name
- ✅ Version of component
- ✅ Other unique identifiers
- ✅ Dependency relationships
- ✅ Author of SBOM data
- ✅ Timestamp

**EU Cyber Resilience Act**:
- ✅ SBOM provided in machine-readable format
- ✅ Vulnerability disclosure process documented
- ✅ Security updates available

### Export Control

**Export Control Classification**: [EAR99 / Other]
**ECCN**: [If applicable]
**Notes**: [Any export restrictions]

## Maintenance

### Update Frequency

- **Regular Updates**: Monthly dependency review
- **Security Updates**: Within 24-48 hours of disclosure
- **SBOM Regeneration**: With each release

### Update Process

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade [package]

# Regenerate SBOM
cyclonedx-py -o sbom.json -F json

# Run security scan
pip-audit
safety check

# Update this documentation
# Update version, date, and statistics
```

### Dependency Update Policy

**Minor/Patch Updates**: 
- Reviewed and applied monthly
- Automated via Dependabot/Renovate

**Major Updates**: 
- Reviewed quarterly
- Tested before deployment
- Breaking changes assessed

**Security Updates**: 
- Applied immediately upon disclosure
- Emergency process for critical vulnerabilities

## Third-Party Notices

### Attribution Requirements

The following packages require attribution:

**Package Name** - [License]
```
[Copyright notice]
[License text or reference]
```

**Complete Notices**: See [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt)

## Verification

### SBOM Integrity

**SBOM Checksum** (SHA256):
```
[checksum of sbom.json]
```

**Verification**:
```bash
# Windows PowerShell
Get-FileHash sbom.json -Algorithm SHA256

# Linux/Mac
shasum -a 256 sbom.json
```

### Reproducibility

This SBOM can be regenerated using:
```bash
# Install exact versions from lock file
pip install -r requirements-lock.txt

# Regenerate SBOM
cyclonedx-py -o sbom-verify.json -F json

# Compare with original
diff sbom.json sbom-verify.json
```

## Contact Information

**SBOM Maintainer**: [Name/Team]
**Email**: [security@example.com]
**Security Issues**: [security reporting process]
**Last Updated**: [YYYY-MM-DD]

## References

- **CycloneDX Specification**: https://cyclonedx.org/specification/overview/
- **SPDX Specification**: https://spdx.dev/specifications/
- **NTIA SBOM Guidelines**: https://www.ntia.gov/SBOM
- **CISA SBOM Resources**: https://www.cisa.gov/sbom

---

*This SBOM should be updated with each release and when dependencies change.*
```

---

### 3. Third-Party Notices File

Create complete attribution file:

```markdown
# Third-Party Notices

This file contains the required notices for third-party components used in [Project Name].

---

## pandas (BSD-3-Clause License)

Copyright (c) 2008-2011, AQR Capital Management, LLC, Lambda Foundry, Inc. and PyData Development Team
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

[Full license text]

---

## requests (Apache License 2.0)

Copyright 2019 Kenneth Reitz

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.

[Full license text]

---

[Continue for all dependencies requiring attribution]
```

---

### 4. Dependency Lock Files

Ensure proper dependency locking:

**requirements-lock.txt** (pip):
```txt
# Generated with: pip freeze > requirements-lock.txt
pandas==2.1.0
numpy==1.24.3
python-dateutil==2.8.2
pytz==2023.3
requests==2.31.0
charset-normalizer==3.2.0
idna==3.4
urllib3==2.0.4
certifi==2023.7.22
[all dependencies with exact versions]
```

**poetry.lock** (if using Poetry):
```bash
# Generate lock file
poetry lock

# Install from lock file
poetry install
```

**Pipfile.lock** (if using Pipenv):
```bash
# Generate lock file
pipenv lock

# Install from lock file
pipenv sync
```

---

### 5. Vulnerability Monitoring Setup

Configure automated vulnerability monitoring:

#### GitHub Dependabot

Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "security"
```

#### Snyk Integration

```bash
# Install Snyk CLI
npm install -g snyk

# Authenticate
snyk auth

# Monitor project
snyk monitor

# Test for vulnerabilities
snyk test
```

#### Safety in CI/CD

Add to your CI pipeline:
```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install safety pip-audit
      - name: Run Safety check
        run: safety check
      - name: Run pip-audit
        run: pip-audit
```

---

### 6. SBOM Automation Scripts

Create automation scripts for SBOM generation:

**scripts/generate_sbom.py**:
```python
#!/usr/bin/env python3
"""
Generate SBOM and update documentation.
"""
import subprocess
import json
from datetime import datetime
from pathlib import Path

def generate_sbom():
    """Generate SBOM in multiple formats."""
    print("Generating SBOM files...")
    
    # CycloneDX JSON
    subprocess.run([
        "cyclonedx-py", "-o", "sbom.json", "-F", "json"
    ], check=True)
    
    # CycloneDX XML
    subprocess.run([
        "cyclonedx-py", "-o", "sbom.xml", "-F", "xml"
    ], check=True)
    
    print("✅ SBOM files generated")

def analyze_sbom():
    """Analyze SBOM and extract statistics."""
    with open("sbom.json", "r") as f:
        sbom = json.load(f)
    
    components = sbom.get("components", [])
    
    stats = {
        "total": len(components),
        "licenses": set(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    for component in components:
        if "licenses" in component:
            for lic in component["licenses"]:
                if "license" in lic:
                    stats["licenses"].add(lic["license"].get("id", "Unknown"))
    
    print(f"Total components: {stats['total']}")
    print(f"Unique licenses: {len(stats['licenses'])}")
    
    return stats

def run_security_scan():
    """Run security vulnerability scan."""
    print("Running security scan...")
    
    try:
        subprocess.run(["pip-audit"], check=True)
        print("✅ No vulnerabilities found")
    except subprocess.CalledProcessError:
        print("⚠️ Vulnerabilities detected - see output above")

if __name__ == "__main__":
    generate_sbom()
    analyze_sbom()
    run_security_scan()
```

**Make script executable and use**:
```bash
# Windows
python scripts/generate_sbom.py

# Unix/Mac
chmod +x scripts/generate_sbom.py
./scripts/generate_sbom.py
```

---

## Deliverables

Please create:

1. **sbom.json** - CycloneDX SBOM in JSON format
2. **sbom.xml** - CycloneDX SBOM in XML format (optional)
3. **docs/SBOM.md** - Human-readable SBOM documentation
4. **THIRD-PARTY-NOTICES.txt** - Complete attribution notices
5. **requirements-lock.txt** - Pinned dependency versions
6. **scripts/generate_sbom.py** - Automation script
7. **.github/dependabot.yml** - Automated dependency updates

**Quality Checks:**
- [ ] SBOM includes all dependencies (direct and transitive)
- [ ] All licenses documented
- [ ] Known vulnerabilities identified
- [ ] Attribution notices complete
- [ ] Dependency versions pinned
- [ ] Automation configured
- [ ] Compliance requirements met

Complete and confirm SBOM documentation is comprehensive and up-to-date.
```

---

## Success Criteria

- ✅ SBOM files generated in standard formats
- ✅ All dependencies cataloged (direct and transitive)
- ✅ All licenses identified and documented
- ✅ Vulnerability scanning configured
- ✅ Attribution notices complete
- ✅ Dependency versions pinned
- ✅ Automation scripts working
- ✅ Compliance requirements addressed

---

## Tools and Resources

### SBOM Generation Tools

**CycloneDX**:
```bash
pip install cyclonedx-bom
cyclonedx-py -o sbom.json -F json
```

**Syft**:
```bash
# Multi-format SBOM generation
syft packages . -o cyclonedx-json > sbom.json
syft packages . -o spdx-json > sbom-spdx.json
```

**SPDX Tools**:
```bash
pip install spdx-tools
```

### Vulnerability Scanning

**pip-audit** (Python-specific):
```bash
pip install pip-audit
pip-audit
```

**Safety**:
```bash
pip install safety
safety check
```

**Snyk** (Multi-language):
```bash
npm install -g snyk
snyk test
```

**Trivy** (Container and filesystem):
```bash
trivy fs .
```

### Dependency Analysis

**pipdeptree**:
```bash
pip install pipdeptree
pipdeptree
pipdeptree --graph-output png > deps.png
```

**pip-licenses**:
```bash
pip install pip-licenses
pip-licenses --format=markdown > licenses.md
```

---

## Compliance Standards

### NTIA Minimum Elements

Required by US Executive Order 14028:
- Supplier name
- Component name
- Version string
- Other unique identifiers
- Dependency relationships
- Author of SBOM data
- Timestamp

### EU Cyber Resilience Act

Requirements:
- SBOM in machine-readable format
- Continuous vulnerability disclosure
- Security update availability
- Supply chain transparency

### Industry Standards

- **CycloneDX**: OWASP standard for SBOM
- **SPDX**: Linux Foundation standard
- **SWID**: ISO/IEC 19770-2 standard

---

## Maintenance Schedule

### Regular Tasks

**Weekly**:
- Automated vulnerability scans
- Review Dependabot PRs

**Monthly**:
- Update dependencies (minor/patch)
- Regenerate SBOM
- Review security advisories

**Quarterly**:
- Major dependency updates
- License compliance review
- SBOM process audit

**Per Release**:
- Generate final SBOM
- Update documentation
- Security scan before deployment

---

## Common Issues

### Issue: SBOM generation fails
**Solution**: Ensure all dependencies installed and CycloneDX tools updated

### Issue: Missing transitive dependencies
**Solution**: Use `pip freeze` to capture all installed packages

### Issue: License information missing
**Solution**: Check package metadata, may need manual research

### Issue: Vulnerability scanner false positives
**Solution**: Review CVE details, check if applies to your usage

---

## Next Steps

After completing Phase 6:
- Integrate SBOM generation into CI/CD pipeline
- Set up automated vulnerability monitoring
- Establish security update process
- Train team on SBOM maintenance
- Document security incident response process
