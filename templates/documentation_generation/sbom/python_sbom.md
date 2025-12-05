---
template_id: python_sbom
template_name: Sbom - Python
version: 1.0.0
last_updated: 2025-12-03
language: Python
category: documentation
phase: sbom
difficulty: beginner
estimated_time_hours: 2-3
prerequisites: []
tools:

  - pytest (8.3.4+)
  - black (24.12.0)
  - mypy (1.13.0)
  - ruff
tags:

  - documentation
  - documentation
  - python
---
# Python SBOM Generation

## Objective
Generate comprehensive, standards-compliant Software Bill of Materials (SBOM) documentation that meets regulatory requirements (NTIA minimum elements, EU Cyber Resilience Act) for security, compliance, and supply chain management.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/sbom/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/sbom/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### NTIA Minimum Elements

- [ ] Supplier name documented

- [ ] Component name documented

- [ ] Version of component documented

- [ ] Other unique identifiers (PURL, CPE)

- [ ] Dependency relationships mapped

- [ ] Author of SBOM data documented

- [ ] Timestamp of SBOM generation

### EU Cyber Resilience Act Requirements

- [ ] Complete dependency tree with versions

- [ ] Known vulnerabilities (CVEs) identified

- [ ] Security advisories tracked

- [ ] License information documented

- [ ] Component provenance documented

- [ ] Update and patch status

### Dependency Analysis

- [ ] Direct dependencies listed with versions

- [ ] Transitive dependencies mapped

- [ ] Dependency tree visualized

- [ ] Circular dependencies identified

- [ ] Outdated dependencies flagged

### License Compliance

- [ ] All licenses identified

- [ ] License compatibility checked

- [ ] Copyleft obligations documented

- [ ] License conflicts identified

- [ ] Attribution requirements tracked

### Vulnerability Tracking

- [ ] Known CVEs for each component

- [ ] CVSS scores documented

- [ ] Patch availability status

- [ ] Mitigation strategies documented

- [ ] False positive handling

### Supply Chain Security

- [ ] Component source/repository documented

- [ ] Package integrity (hashes) verified

- [ ] Digital signatures checked

- [ ] Build provenance tracked

- [ ] Supply chain risks assessed

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python SBOM Generation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/sbom"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please generate a comprehensive Software Bill of Materials (SBOM) for this Python project following this protocol:

## Phase 1: Dependency Discovery & Analysis

1. **Inventory Direct Dependencies**

   Analyze `requirements.txt`, `pyproject.toml`, or `setup.py`:

   ```bash
   # For pip
   pip list --format=json > ${OUTPUT_DIR}/exports/dependencies.json

   # For poetry
   poetry show --tree --format=json > ${OUTPUT_DIR}/exports/dependencies.json

   # For pipenv
   pipenv graph --json > ${OUTPUT_DIR}/exports/dependencies.json
   ```

2. **Map Transitive Dependencies**

   Create complete dependency tree:

   ```bash
   # Using pipdeptree
   pip install pipdeptree
   pipdeptree --json > ${OUTPUT_DIR}/exports/dependency_tree.json

   # Using poetry
   poetry show --tree
   ```

3. **Identify Dependency Metadata**

   For each dependency, collect:
   - Package name
   - Version
   - License
   - Repository URL
   - Maintainer/supplier
   - Dependencies (for transitive mapping)

## Phase 2: SBOM Format Selection

Choose SBOM format based on requirements:

### Option 1: SPDX (Software Package Data Exchange)

- **Standard**: ISO/IEC 5962:2021

- **Format**: JSON, YAML, RDF, Tag-Value

- **Best for**: License compliance, legal requirements

- **Tools**: spdx-tools, scancode-toolkit

### Option 2: CycloneDX

- **Standard**: OWASP CycloneDX

- **Format**: JSON, XML

- **Best for**: Security analysis, vulnerability management

- **Tools**: cyclonedx-python, syft

### Option 3: SWID (Software Identification Tags)

- **Standard**: ISO/IEC 19770-2:2015

- **Format**: XML

- **Best for**: IT asset management

**Recommendation**: Use CycloneDX for security focus, SPDX for license focus.

## Phase 3: Generate SBOM (CycloneDX Format)

### Using cyclonedx-bom

```bash
# Install tool
pip install cyclonedx-bom

# Generate SBOM from requirements.txt
cyclonedx-py requirements requirements.txt -o ${OUTPUT_DIR}/exports/sbom.json

# Generate from poetry
cyclonedx-py poetry -o ${OUTPUT_DIR}/exports/sbom.json

# Generate from pipenv
cyclonedx-py pipenv -o ${OUTPUT_DIR}/exports/sbom.json

# Generate with all details
cyclonedx-py requirements requirements.txt \
  --format json \
  --output ${OUTPUT_DIR}/exports/sbom.json \
  --sv 1.4 \
  --reproducible
```

### CycloneDX SBOM Template (JSON)

```json
{
  "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json",
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
  "version": 1,
  "metadata": {
    "timestamp": "2024-01-16T10:00:00Z",
    "tools": [
      {
        "vendor": "CycloneDX",
        "name": "cyclonedx-python",
        "version": "3.11.0"
      }
    ],
    "authors": [
      {
        "name": "Benjamin Dourthe",
        "email": "benjamin@adonamed.com"
      }
    ],
    "component": {
      "type": "application",
      "bom-ref": "pkg:pypi/project-name@1.0.0",
      "name": "project-name",
      "version": "1.0.0",
      "description": "Project description",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:pypi/project-name@1.0.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://github.com/username/project"
        },
        {
          "type": "vcs",
          "url": "https://github.com/username/project.git"
        }
      ]
    }
  },
  "components": [
    {
      "type": "library",
      "bom-ref": "pkg:pypi/requests@2.31.0",
      "name": "requests",
      "version": "2.31.0",
      "description": "Python HTTP for Humans.",
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "942c5a758f98d8d7c5c5e4f2c9c1c9e3b1b7a7e4c4d4e4f4g4h4i4j4k4l4"
        }
      ],
      "licenses": [
        {
          "license": {
            "id": "Apache-2.0"
          }
        }
      ],
      "purl": "pkg:pypi/requests@2.31.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://requests.readthedocs.io"
        },
        {
          "type": "vcs",
          "url": "https://github.com/psf/requests"
        }
      ],
      "properties": [
        {
          "name": "pypi:package:type",
          "value": "library"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:pypi/fastapi@0.104.1",
      "name": "fastapi",
      "version": "0.104.1",
      "description": "FastAPI framework, high performance, easy to learn",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:pypi/fastapi@0.104.1",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://fastapi.tiangolo.com"
        }
      ]
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:pypi/project-name@1.0.0",
      "dependsOn": [
        "pkg:pypi/requests@2.31.0",
        "pkg:pypi/fastapi@0.104.1"
      ]
    },
    {
      "ref": "pkg:pypi/requests@2.31.0",
      "dependsOn": [
        "pkg:pypi/charset-normalizer@3.3.2",
        "pkg:pypi/idna@3.6",
        "pkg:pypi/urllib3@2.1.0",
        "pkg:pypi/certifi@2023.11.17"
      ]
    },
    {
      "ref": "pkg:pypi/fastapi@0.104.1",
      "dependsOn": [
        "pkg:pypi/starlette@0.27.0",
        "pkg:pypi/pydantic@2.5.0"
      ]
    }
  ],
  "vulnerabilities": [
    {
      "bom-ref": "vuln:pypi/requests@2.31.0:CVE-2023-XXXXX",
      "id": "CVE-2023-XXXXX",
      "source": {
        "name": "NVD",
        "url": "https://nvd.nist.gov/vuln/detail/CVE-2023-XXXXX"
      },
      "ratings": [
        {
          "source": {
            "name": "NVD"
          },
          "score": 7.5,
          "severity": "high",
          "method": "CVSSv3",
          "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"
        }
      ],
      "cwes": [79],
      "description": "Description of the vulnerability",
      "recommendation": "Update to version 2.31.1 or higher",
      "affects": [
        {
          "ref": "pkg:pypi/requests@2.31.0",
          "versions": [
            {
              "version": "2.31.0",
              "status": "affected"
            }
          ]
        }
      ]
    }
  ]
}
```

## Phase 4: Generate SBOM (SPDX Format)

### Using spdx-tools

```bash
# Install tools
pip install spdx-tools

# Generate SPDX SBOM
# (Requires manual construction or tooling)
```

### SPDX SBOM Template (JSON)

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "project-name-1.0.0",
  "documentNamespace": "https://example.com/spdxdocs/project-name-1.0.0-uuid",
  "creationInfo": {
    "created": "2024-01-16T10:00:00Z",
    "creators": [
      "Tool: spdx-tools-0.8.0",
      "Person: Benjamin Dourthe (benjamin@adonamed.com)"
    ],
    "licenseListVersion": "3.21"
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-project-name",
      "name": "project-name",
      "versionInfo": "1.0.0",
      "downloadLocation": "https://github.com/username/project",
      "filesAnalyzed": false,
      "homepage": "https://github.com/username/project",
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright (c) 2024 Benjamin Dourthe",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:pypi/project-name@1.0.0"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-requests",
      "name": "requests",
      "versionInfo": "2.31.0",
      "downloadLocation": "https://pypi.org/project/requests/2.31.0/",
      "filesAnalyzed": false,
      "homepage": "https://requests.readthedocs.io",
      "licenseConcluded": "Apache-2.0",
      "licenseDeclared": "Apache-2.0",
      "copyrightText": "Copyright (c) Kenneth Reitz",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:pypi/requests@2.31.0"
        },
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:python-requests:requests:2.31.0:*:*:*:*:*:*:*"
        }
      ]
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-DOCUMENT",
      "relationshipType": "DESCRIBES",
      "relatedSpdxElement": "SPDXRef-Package-project-name"
    },
    {
      "spdxElementId": "SPDXRef-Package-project-name",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-requests"
    }
  ]
}
```

## Phase 5: Vulnerability Scanning

Scan for known vulnerabilities in dependencies:

### Using pip-audit

```bash
# Install pip-audit
pip install pip-audit

# Scan for vulnerabilities
pip-audit --format json --output ${OUTPUT_DIR}/exports/vulnerabilities.json

# Scan with specific requirement file
pip-audit -r requirements.txt --format json

# Example output
{
  "dependencies": [
    {
      "name": "requests",
      "version": "2.25.0",
      "vulns": [
        {
          "id": "PYSEC-2023-74",
          "fix_versions": ["2.31.0"],
          "description": "Requests Proxy-Authorization header leak",
          "aliases": ["CVE-2023-32681"]
        }
      ]
    }
  ]
}
```

### Using safety

```bash
# Install safety
pip install safety

# Scan dependencies
safety check --json > ${OUTPUT_DIR}/exports/safety_report.json

# Scan specific requirements file
safety check -r requirements.txt --json
```

### Using Trivy

```bash
# Install Trivy
# See: https://aquasecurity.github.io/trivy/

# Scan Python project
trivy fs --format json --output ${OUTPUT_DIR}/exports/trivy_report.json .

# Scan specific requirements file
trivy fs --format json -f requirements.txt .
```

## Phase 6: License Analysis

### Using pip-licenses

```bash
# Install pip-licenses
pip install pip-licenses

# List all licenses
pip-licenses --format=json --with-urls > ${OUTPUT_DIR}/exports/licenses.json

# Check for specific license types
pip-licenses --format=markdown --with-urls

# Example output format
[
  {
    "Name": "requests",
    "Version": "2.31.0",
    "License": "Apache 2.0",
    "URL": "https://requests.readthedocs.io"
  },
  {
    "Name": "fastapi",
    "Version": "0.104.1",
    "License": "MIT",
    "URL": "https://fastapi.tiangolo.com"
  }
]
```

### Using licensecheck

```bash
# Install licensecheck
pip install licensecheck

# Check licenses
licensecheck --format json > ${OUTPUT_DIR}/exports/license_report.json
```

### License Compatibility Matrix

Document license compatibility:

```markdown
## License Compatibility

| License | Can Include | Cannot Include | Notes |
|---------|-------------|----------------|-------|
| MIT | Any | - | Very permissive |
| Apache-2.0 | MIT, BSD, Apache | - | Patent grant included |
| GPL-3.0 | MIT, BSD | Proprietary | Copyleft - requires source |
| LGPL-3.0 | MIT, BSD | - | Lesser copyleft |
| BSD-3-Clause | Any | - | Very permissive |
| Proprietary | ? | GPL, AGPL | Check license terms |

**Current Project License**: MIT

**Compatibility Status**:

- ✅ Compatible: [list of dependencies]

- ⚠️ Review Required: [list needing review]

- ❌ Incompatible: [list of incompatible]
```

## Phase 7: Supply Chain Security Assessment

### Package Provenance

```bash
# Verify package signatures (if available)
pip install --require-hashes -r requirements_with_hashes.txt

# Generate requirements with hashes
pip freeze --all | pip-compile --generate-hashes -o ${OUTPUT_DIR}/exports/requirements_locked.txt
```

### Repository Security

For each dependency, document:

```markdown
## Dependency: requests

**Repository**: https://github.com/psf/requests
**Package Index**: https://pypi.org/project/requests/
**Maintainer**: Python Software Foundation

**Security Posture**:

- ✅ Active maintenance (last commit: [date])

- ✅ Security policy present

- ✅ Vulnerability disclosure process

- ✅ Code signing (where applicable)

- ⚠️ No recent security audit

- ✅ Large, active community (50k+ stars)

**Risk Assessment**: LOW

- Well-maintained, widely-used library

- Active security response

- Regular updates and patches

**Alternative Options**:

- httpx (modern alternative)

- urllib3 (lower-level, requests uses this)
```

## Phase 8: Compliance Documentation

### NTIA Minimum Elements Compliance

```markdown
# NTIA SBOM Compliance Checklist

## Minimum Elements

- [x] **Supplier Name**: All suppliers identified in SBOM

- [x] **Component Name**: All components named

- [x] **Version**: All versions specified

- [x] **Other Unique Identifiers**: PURL provided for all

- [x] **Dependency Relationships**: Complete dependency tree

- [x] **Author of SBOM Data**: [Benjamin Dourthe]

- [x] **Timestamp**: [2024-01-16T10:00:00Z]

## Automation Supportability

- [x] SBOM in machine-readable format (CycloneDX JSON)

- [x] Consistent data format across components

- [x] Unique identifiers (PURL) for all components

- [x] Dependency relationships machine-parseable

## Practices and Processes

- [x] SBOM generation automated in CI/CD

- [x] SBOM updated with each release

- [x] SBOM published alongside releases

- [x] Vulnerability scanning integrated

**Compliance Status**: ✅ COMPLIANT
```

### EU Cyber Resilience Act Compliance

```markdown
# EU CRA Compliance Checklist

## Essential Requirements

- [x] Complete SBOM with all components

- [x] Known vulnerabilities identified (CVE tracking)

- [x] Security updates and patches tracked

- [x] Vulnerability disclosure timeline documented

- [x] Supply chain security assessed

## Documentation Requirements

- [x] SBOM in standardized format (CycloneDX/SPDX)

- [x] Vulnerability report attached

- [x] License compliance documented

- [x] Security contact information provided

- [x] Update/patching process documented

## Ongoing Obligations

- [ ] SBOM updated with each release

- [ ] Vulnerability monitoring continuous

- [ ] Security updates issued promptly

- [ ] Users notified of security issues

**Compliance Status**: ✅ COMPLIANT
```

## Output Format

Please provide SBOM documentation in this format:

### Primary SBOM Files

```markdown
## SBOM Files Generated

1. **sbom.json** (CycloneDX format)
   - Complete dependency tree
   - Vulnerability information
   - License data
   - Component metadata

2. **sbom.spdx.json** (SPDX format)
   - License-focused SBOM
   - Compliance documentation
   - Relationship mapping

3. **sbom-lite.json** (Simplified)
   - Essential information only
   - For quick reference
   - Human-readable summary
```

### Supporting Documentation

```markdown
## Supporting Files

1. **VULNERABILITIES.md**
   - All known CVEs
   - Severity ratings
   - Remediation status
   - Mitigation strategies

2. **LICENSES.md**
   - All component licenses
   - License compatibility analysis
   - Attribution requirements
   - Compliance status

3. **DEPENDENCIES.md**
   - Dependency tree visualization
   - Direct dependencies
   - Transitive dependencies
   - Update recommendations

4. **SUPPLY_CHAIN.md**
   - Component provenance
   - Security assessment
   - Risk analysis
   - Alternative options
```

### Summary Report

```markdown
## SBOM Generation Summary

**Generated**: [timestamp]
**Project**: [name] v[version]
**License**: [license]

**Components**:

- Total components: [count]

- Direct dependencies: [count]

- Transitive dependencies: [count]

- Unique licenses: [count]

**Vulnerabilities**:

- Critical: [count]

- High: [count]

- Medium: [count]

- Low: [count]

- Total: [count]

**License Distribution**:

- MIT: [count]

- Apache-2.0: [count]

- GPL-3.0: [count]

- Other: [count]

**Compliance**:

- NTIA Minimum Elements: ✅/❌

- EU CRA Requirements: ✅/❌

- SPDX 2.3 Compliant: ✅/❌

- CycloneDX 1.4 Compliant: ✅/❌

**Supply Chain Risk**: [LOW/MEDIUM/HIGH]

**Actions Required**:

- [ ] Update [X] components with known vulnerabilities

- [ ] Review [Y] components with license concerns

- [ ] Assess [Z] outdated dependencies
```

---

## Automation & CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Generate SBOM

on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  sbom:
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install cyclonedx-bom pip-audit pip-licenses

      - name: Generate SBOM
        run: |
          cyclonedx-py requirements requirements.txt -o ${OUTPUT_DIR}/exports/sbom.json

      - name: Scan vulnerabilities
        run: |
          pip-audit --format json --output ${OUTPUT_DIR}/exports/vulnerabilities.json
        continue-on-error: true

      - name: Generate license report
        run: |
          pip-licenses --format=json --with-urls > ${OUTPUT_DIR}/exports/licenses.json

      - name: Upload SBOM artifacts
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: |
            sbom.json
            vulnerabilities.json
            licenses.json

      - name: Attach to release
        if: github.event_name == 'release'
        uses: softprops/action-gh-release@v1
        with:
          files: sbom.json
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:

  - repo: local
    hooks:

      - id: generate-sbom
        name: Generate SBOM
        entry: cyclonedx-py requirements requirements.txt -o ${OUTPUT_DIR}/exports/sbom.json
        language: system
        pass_filenames: false

      - id: check-vulnerabilities
        name: Check Vulnerabilities
        entry: pip-audit
        language: system
        pass_filenames: false
```

---

## Best Practices

1. **Automate SBOM Generation**
   - Generate in CI/CD pipeline
   - Update with every release
   - Include in release artifacts

2. **Keep SBOMs Current**
   - Regenerate on dependency updates
   - Track vulnerability fixes
   - Document changes between versions

3. **Use Multiple Formats**
   - CycloneDX for security
   - SPDX for license compliance
   - Both for comprehensive coverage

4. **Continuous Monitoring**
   - Monitor for new vulnerabilities
   - Track dependency updates
   - Assess supply chain risks

5. **Publish Transparently**
   - Include SBOM in releases
   - Make publicly available
   - Provide easy access

---

## Output Format Specifications

The SBOM should:

- Comply with NTIA minimum elements requirements

- Meet EU Cyber Resilience Act standards

- Use standard formats (CycloneDX 1.4+ or SPDX 2.3+)

- Include complete dependency tree with versions

- Document all known vulnerabilities with CVE IDs

- Provide license information for all components

- Assess supply chain security risks

- Be machine-readable and automatable

- Be versioned and timestamped

- Be published alongside software releases

~~~
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
