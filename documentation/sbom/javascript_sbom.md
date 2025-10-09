# JavaScript SBOM Generation

## Objective
Generate comprehensive, standards-compliant Software Bill of Materials (SBOM) documentation that meets regulatory requirements (NTIA minimum elements, EU Cyber Resilience Act) for security, compliance, and supply chain management in JavaScript/Node.js projects.

## Output Directory Structure

All documentation outputs should be saved in organized directories:

```
documentation/
└── sbom/
    ├── generated_docs/
    ├── templates/
    ├── assets/
    └── exports/
```

**Directory Setup**:
- Create `documentation/` directory in repository root if it doesn't exist
- Create `documentation/sbom/` subdirectory for this documentation phase
- All documentation files, templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:
- `generated_docs/` - Generated documentation files (HTML, MD, PDF)
- `templates/` - Documentation templates and examples
- `assets/` - Images, diagrams, supplementary files
- `exports/` - Published documentation, release artifacts

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
- [ ] Peer dependencies tracked

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
# JavaScript SBOM Generation Request

Please generate a comprehensive Software Bill of Materials (SBOM) for this JavaScript/Node.js project following this protocol:

## Phase 1: Dependency Discovery & Analysis

1. **Inventory Direct Dependencies**

   Analyze `package.json` and `package-lock.json`:

   ```bash
   # List all dependencies
   npm list --all --json > dependencies.json

   # List only production dependencies
   npm list --prod --json > prod-dependencies.json

   # List development dependencies
   npm list --dev --json > dev-dependencies.json

   # Using yarn
   yarn list --json > dependencies.json
   ```

2. **Map Transitive Dependencies**

   Create complete dependency tree:

   ```bash
   # Using npm
   npm ls --all --depth=10 > dependency_tree.txt

   # Using yarn
   yarn list --depth=10 > dependency_tree.txt

   # Generate detailed JSON tree
   npm list --all --json --depth=99 > dependency_tree.json
   ```

3. **Identify Dependency Metadata**

   For each dependency, collect:
   - Package name
   - Version (semver)
   - License
   - Repository URL
   - Maintainer/author
   - Dependencies (for transitive mapping)
   - Package integrity (shasum)

## Phase 2: SBOM Format Selection

Choose SBOM format based on requirements:

### Option 1: SPDX (Software Package Data Exchange)
- **Standard**: ISO/IEC 5962:2021
- **Format**: JSON, YAML, RDF, Tag-Value
- **Best for**: License compliance, legal requirements
- **Tools**: spdx-sbom-generator, scancode-toolkit

### Option 2: CycloneDX
- **Standard**: OWASP CycloneDX
- **Format**: JSON, XML
- **Best for**: Security analysis, vulnerability management
- **Tools**: @cyclonedx/bom, syft, cdxgen

### Option 3: SWID (Software Identification Tags)
- **Standard**: ISO/IEC 19770-2:2015
- **Format**: XML
- **Best for**: IT asset management

**Recommendation**: Use CycloneDX for security focus, SPDX for license focus.

## Phase 3: Generate SBOM (CycloneDX Format)

### Using @cyclonedx/bom

```bash
# Install tool
npm install -g @cyclonedx/cyclonedx-npm

# Generate SBOM from package-lock.json
cyclonedx-npm --output-file sbom.json

# Generate with specific options
cyclonedx-npm \
  --output-format JSON \
  --output-file sbom.json \
  --spec-version 1.4 \
  --validate

# Using cdxgen (comprehensive tool)
npm install -g @cyclonedx/cdxgen
cdxgen -t js -o sbom.json .
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
        "name": "@cyclonedx/cyclonedx-npm",
        "version": "1.7.0"
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
      "bom-ref": "pkg:npm/project-name@1.0.0",
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
      "purl": "pkg:npm/project-name@1.0.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://github.com/username/project"
        },
        {
          "type": "vcs",
          "url": "git+https://github.com/username/project.git"
        },
        {
          "type": "issue-tracker",
          "url": "https://github.com/username/project/issues"
        }
      ]
    }
  },
  "components": [
    {
      "type": "library",
      "bom-ref": "pkg:npm/express@4.18.2",
      "name": "express",
      "version": "4.18.2",
      "description": "Fast, unopinionated, minimalist web framework",
      "hashes": [
        {
          "alg": "SHA-512",
          "content": "3c4b76b79d1c5e7e1a7f6d6e8f5f4f3f2f1f0f9f8f7f6f5f4f3f2f1f0f9f8f7f6"
        }
      ],
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:npm/express@4.18.2",
      "externalReferences": [
        {
          "type": "website",
          "url": "http://expressjs.com/"
        },
        {
          "type": "vcs",
          "url": "git+https://github.com/expressjs/express.git"
        },
        {
          "type": "distribution",
          "url": "https://registry.npmjs.org/express/-/express-4.18.2.tgz"
        }
      ],
      "properties": [
        {
          "name": "npm:package:type",
          "value": "library"
        },
        {
          "name": "npm:package:dev",
          "value": "false"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:npm/react@18.2.0",
      "name": "react",
      "version": "18.2.0",
      "description": "React is a JavaScript library for building user interfaces.",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:npm/react@18.2.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://reactjs.org/"
        },
        {
          "type": "vcs",
          "url": "git+https://github.com/facebook/react.git"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:npm/lodash@4.17.21",
      "name": "lodash",
      "version": "4.17.21",
      "description": "Lodash modular utilities.",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:npm/lodash@4.17.21"
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:npm/project-name@1.0.0",
      "dependsOn": [
        "pkg:npm/express@4.18.2",
        "pkg:npm/react@18.2.0",
        "pkg:npm/lodash@4.17.21"
      ]
    },
    {
      "ref": "pkg:npm/express@4.18.2",
      "dependsOn": [
        "pkg:npm/body-parser@1.20.1",
        "pkg:npm/cookie@0.5.0",
        "pkg:npm/debug@2.6.9",
        "pkg:npm/qs@6.11.0"
      ]
    },
    {
      "ref": "pkg:npm/react@18.2.0",
      "dependsOn": [
        "pkg:npm/loose-envify@1.4.0"
      ]
    }
  ],
  "vulnerabilities": [
    {
      "bom-ref": "vuln:npm/lodash@4.17.20:CVE-2021-23337",
      "id": "CVE-2021-23337",
      "source": {
        "name": "NVD",
        "url": "https://nvd.nist.gov/vuln/detail/CVE-2021-23337"
      },
      "ratings": [
        {
          "source": {
            "name": "NVD"
          },
          "score": 7.2,
          "severity": "high",
          "method": "CVSSv3",
          "vector": "CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H"
        }
      ],
      "cwes": [77, 94],
      "description": "Command injection in lodash",
      "recommendation": "Update to version 4.17.21 or higher",
      "affects": [
        {
          "ref": "pkg:npm/lodash@4.17.20",
          "versions": [
            {
              "version": "4.17.20",
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

### Using spdx-sbom-generator

```bash
# Install spdx-sbom-generator
npm install -g @spdx/spdx-sbom-generator

# Generate SPDX SBOM
spdx-sbom-generator -o sbom.spdx.json

# Specify format
spdx-sbom-generator -f json -o sbom.spdx.json
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
      "Tool: @spdx/spdx-sbom-generator-1.0.0",
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
          "referenceLocator": "pkg:npm/project-name@1.0.0"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-express",
      "name": "express",
      "versionInfo": "4.18.2",
      "downloadLocation": "https://registry.npmjs.org/express/-/express-4.18.2.tgz",
      "filesAnalyzed": false,
      "homepage": "http://expressjs.com/",
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright (c) 2009-2014 TJ Holowaychuk",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:npm/express@4.18.2"
        },
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:expressjs:express:4.18.2:*:*:*:*:node.js:*:*"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-react",
      "name": "react",
      "versionInfo": "18.2.0",
      "downloadLocation": "https://registry.npmjs.org/react/-/react-18.2.0.tgz",
      "filesAnalyzed": false,
      "homepage": "https://reactjs.org/",
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright (c) Meta Platforms, Inc. and affiliates.",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:npm/react@18.2.0"
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
      "relatedSpdxElement": "SPDXRef-Package-express"
    },
    {
      "spdxElementId": "SPDXRef-Package-project-name",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-react"
    }
  ]
}
```

## Phase 5: Vulnerability Scanning

Scan for known vulnerabilities in dependencies:

### Using npm audit

```bash
# Run npm audit
npm audit --json > vulnerabilities.json

# Audit only production dependencies
npm audit --production --json

# Get detailed report
npm audit

# Example JSON output
{
  "auditReportVersion": 2,
  "vulnerabilities": {
    "lodash": {
      "name": "lodash",
      "severity": "high",
      "via": [
        {
          "source": 1065,
          "name": "lodash",
          "dependency": "lodash",
          "title": "Command Injection in lodash",
          "url": "https://github.com/advisories/GHSA-35jh-r3h4-6jhm",
          "severity": "high",
          "cwe": ["CWE-94"],
          "cvss": {
            "score": 7.2,
            "vectorString": "CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H"
          },
          "range": "<4.17.21"
        }
      ],
      "effects": [],
      "range": "<4.17.21",
      "nodes": ["node_modules/lodash"],
      "fixAvailable": true
    }
  },
  "metadata": {
    "vulnerabilities": {
      "info": 0,
      "low": 2,
      "moderate": 5,
      "high": 3,
      "critical": 1,
      "total": 11
    }
  }
}

# Fix vulnerabilities automatically
npm audit fix

# Force fix with breaking changes
npm audit fix --force
```

### Using Snyk

```bash
# Install Snyk CLI
npm install -g snyk

# Authenticate
snyk auth

# Test for vulnerabilities
snyk test --json > snyk_report.json

# Monitor project
snyk monitor

# Test specific package.json
snyk test --file=package.json --json
```

### Using yarn audit

```bash
# Run yarn audit
yarn audit --json > vulnerabilities.json

# Get detailed report
yarn audit

# Example output
{
  "type": "auditSummary",
  "data": {
    "vulnerabilities": {
      "info": 0,
      "low": 2,
      "moderate": 5,
      "high": 3,
      "critical": 1
    },
    "dependencies": 1234,
    "devDependencies": 456,
    "optionalDependencies": 12,
    "totalDependencies": 1702
  }
}
```

### Using Trivy

```bash
# Install Trivy
# See: https://aquasecurity.github.io/trivy/

# Scan Node.js project
trivy fs --format json --output trivy_report.json .

# Scan package-lock.json
trivy fs --scanners vuln package-lock.json
```

## Phase 6: License Analysis

### Using license-checker

```bash
# Install license-checker
npm install -g license-checker

# List all licenses
license-checker --json > licenses.json

# List with URLs
license-checker --json --customPath customFormat.json

# Custom format (customFormat.json)
{
  "name": "",
  "version": "",
  "license": "",
  "repository": "",
  "url": ""
}

# Example output
{
  "express@4.18.2": {
    "licenses": "MIT",
    "repository": "https://github.com/expressjs/express",
    "publisher": "TJ Holowaychuk",
    "url": "http://expressjs.com/"
  },
  "react@18.2.0": {
    "licenses": "MIT",
    "repository": "https://github.com/facebook/react",
    "publisher": "Meta Platforms, Inc.",
    "url": "https://reactjs.org/"
  }
}

# CSV format
license-checker --csv --out licenses.csv

# Markdown format
license-checker --markdown --out LICENSES.md
```

### Using licensee

```bash
# Install licensee
npm install -g licensee

# Check licenses
licensee --json > license_report.json

# Check against allowed list
licensee --errors-only --licenses MIT Apache-2.0 ISC BSD-3-Clause
```

### License Compatibility Matrix

Document license compatibility:

```markdown
## License Compatibility

| License | Can Include | Cannot Include | Notes |
|---------|-------------|----------------|-------|
| MIT | Any | - | Very permissive |
| Apache-2.0 | MIT, BSD, Apache | - | Patent grant included |
| ISC | Any | - | Functionally equivalent to MIT |
| BSD-2-Clause | Any | - | Very permissive |
| BSD-3-Clause | Any | - | Very permissive |
| GPL-3.0 | MIT, BSD | Proprietary | Copyleft - requires source |
| LGPL-3.0 | MIT, BSD | - | Lesser copyleft |
| Proprietary | ? | GPL, AGPL | Check license terms |

**Current Project License**: MIT

**Compatibility Status**:
- ✅ Compatible: express (MIT), react (MIT), lodash (MIT)
- ⚠️ Review Required: [list needing review]
- ❌ Incompatible: [list of incompatible]
```

## Phase 7: Supply Chain Security Assessment

### Package Provenance

```bash
# Verify package integrity
npm install --integrity

# Generate package-lock.json with integrity hashes
npm install --package-lock-only

# Check package signatures (npm v7+)
npm audit signatures

# Verify specific package
npm view express dist.integrity
```

### Repository Security

For each dependency, document:

```markdown
## Dependency: express

**Repository**: https://github.com/expressjs/express
**Package Registry**: https://www.npmjs.com/package/express
**Maintainer**: TJ Holowaychuk & Express team

**Security Posture**:
- ✅ Active maintenance (last commit: [date])
- ✅ Security policy present
- ✅ Vulnerability disclosure process
- ✅ Package signing enabled
- ✅ Recent security audit (2023)
- ✅ Large, active community (60k+ stars)
- ✅ 2FA required for maintainers

**Risk Assessment**: LOW
- Well-maintained, widely-used library
- Active security response
- Regular updates and patches
- Strong community oversight

**Alternative Options**:
- fastify (modern, faster alternative)
- koa (next-gen from Express team)
- hapi (enterprise-focused)
```

## Phase 8: Compliance Documentation

### NTIA Minimum Elements Compliance

```markdown
# NTIA SBOM Compliance Checklist

## Minimum Elements

- [x] **Supplier Name**: All suppliers identified in SBOM
- [x] **Component Name**: All components named
- [x] **Version**: All versions specified (semver)
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
   - Severity ratings (npm audit)
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
   - Peer dependencies
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
- Dev dependencies: [count]
- Transitive dependencies: [count]
- Unique licenses: [count]

**Vulnerabilities**:
- Critical: [count]
- High: [count]
- Moderate: [count]
- Low: [count]
- Info: [count]
- Total: [count]

**License Distribution**:
- MIT: [count]
- Apache-2.0: [count]
- ISC: [count]
- BSD-3-Clause: [count]
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

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Install SBOM tools
        run: |
          npm install -g @cyclonedx/cyclonedx-npm
          npm install -g license-checker

      - name: Generate CycloneDX SBOM
        run: |
          cyclonedx-npm --output-file sbom.json

      - name: Run npm audit
        run: |
          npm audit --json > vulnerabilities.json || true

      - name: Generate license report
        run: |
          license-checker --json > licenses.json

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

### GitLab CI/CD

```yaml
sbom:
  stage: build
  image: node:18
  script:
    - npm ci
    - npm install -g @cyclonedx/cyclonedx-npm
    - cyclonedx-npm --output-file sbom.json
    - npm audit --json > vulnerabilities.json || true
  artifacts:
    paths:
      - sbom.json
      - vulnerabilities.json
    expire_in: 1 year
```

---

## Best Practices

1. **Automate SBOM Generation**
   - Generate in CI/CD pipeline
   - Update with every release
   - Include in release artifacts
   - Use package-lock.json for deterministic builds

2. **Keep SBOMs Current**
   - Regenerate on dependency updates
   - Track vulnerability fixes
   - Document changes between versions
   - Monitor npm audit regularly

3. **Use Multiple Formats**
   - CycloneDX for security
   - SPDX for license compliance
   - Both for comprehensive coverage

4. **Continuous Monitoring**
   - Monitor for new vulnerabilities (npm audit, Snyk)
   - Track dependency updates (Dependabot)
   - Assess supply chain risks
   - Enable npm audit signatures

5. **Publish Transparently**
   - Include SBOM in releases
   - Make publicly available
   - Provide easy access
   - Document update process

---
~~~

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
