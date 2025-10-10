# Go SBOM Generation

## Objective
Generate comprehensive, standards-compliant Software Bill of Materials (SBOM) documentation that meets regulatory requirements (NTIA minimum elements, EU Cyber Resilience Act) for security, compliance, and supply chain management in Go projects.

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

- [ ] Module replacement tracking

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
# Go SBOM Generation Request

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

Please generate a comprehensive Software Bill of Materials (SBOM) for this Go project following this protocol:

## Phase 1: Dependency Discovery & Analysis

1. **Inventory Direct Dependencies**

   Analyze `go.mod` and `go.sum`:

   ```bash
   # List all dependencies
   go list -m all > ${OUTPUT_DIR}/exports/dependencies.txt

   # List with JSON format
   go list -m -json all > ${OUTPUT_DIR}/exports/dependencies.json

   # List direct dependencies only
   go list -m -f '{{if not .Indirect}}{{.Path}} {{.Version}}{{end}}' all

   # List with module info
   go list -m -u all

   # Generate dependency graph
   go mod graph > ${OUTPUT_DIR}/exports/dependency_graph.txt
   ```

2. **Map Transitive Dependencies**

   Create complete dependency tree:

   ```bash
   # Full dependency graph
   go mod graph

   # Why a dependency is needed
   go mod why -m github.com/gin-gonic/gin

   # Visualize dependencies
   go mod graph | modgraphviz | dot -Tpng -o dependencies.png

   # Vendor dependencies (optional)
   go mod vendor
   ```

3. **Identify Dependency Metadata**

   For each dependency, collect:
   - Module path
   - Version (semantic versioning)
   - License
   - Repository URL
   - Maintainer/authors
   - Dependencies (for transitive mapping)
   - Checksum (from go.sum)

## Phase 2: SBOM Format Selection

Choose SBOM format based on requirements:

### Option 1: SPDX (Software Package Data Exchange)

- **Standard**: ISO/IEC 5962:2021

- **Format**: JSON, YAML, RDF, Tag-Value

- **Best for**: License compliance, legal requirements

- **Tools**: spdx-sbom-generator, syft

### Option 2: CycloneDX

- **Standard**: OWASP CycloneDX

- **Format**: JSON, XML

- **Best for**: Security analysis, vulnerability management

- **Tools**: cyclonedx-gomod, syft

### Option 3: SWID (Software Identification Tags)

- **Standard**: ISO/IEC 19770-2:2015

- **Format**: XML

- **Best for**: IT asset management

**Recommendation**: Use CycloneDX for security focus, SPDX for license focus.

## Phase 3: Generate SBOM (CycloneDX Format)

### Using cyclonedx-gomod

```bash
# Install cyclonedx-gomod
go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest

# Generate SBOM
cyclonedx-gomod mod -json -output sbom.json

# With all options
cyclonedx-gomod mod \
  -json \
  -output sbom.json \
  -licenses \
  -assert-licenses \
  -std \
  -version \
  -type application

# From go.mod in specific directory
cyclonedx-gomod mod -json -output sbom.json -module-path ./myproject
```

### Using Syft

```bash
# Install Syft
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Generate CycloneDX SBOM
syft packages dir:. -o cyclonedx-json > ${OUTPUT_DIR}/exports/sbom.json

# Generate from specific go.mod
syft packages file:go.mod -o cyclonedx-json > ${OUTPUT_DIR}/exports/sbom.json

# Generate with all details
syft packages . -o cyclonedx-json --file sbom.json
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
        "name": "cyclonedx-gomod",
        "version": "1.4.0"
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
      "bom-ref": "pkg:golang/github.com/username/project@v1.0.0",
      "name": "project",
      "version": "1.0.0",
      "description": "Project description",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:golang/github.com/username/project@v1.0.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://github.com/username/project"
        },
        {
          "type": "vcs",
          "url": "https://github.com/username/project"
        }
      ]
    }
  },
  "components": [
    {
      "type": "library",
      "bom-ref": "pkg:golang/github.com/gin-gonic/gin@v1.9.1",
      "name": "gin",
      "version": "v1.9.1",
      "description": "Gin is a HTTP web framework written in Go",
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "h1:4idEAncQnU5cB7BeOkPtxjfCSye0AAm1R0RVIqJ+Jmg="
        }
      ],
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:golang/github.com/gin-gonic/gin@v1.9.1",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://github.com/gin-gonic/gin"
        },
        {
          "type": "vcs",
          "url": "https://github.com/gin-gonic/gin"
        },
        {
          "type": "distribution",
          "url": "https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.9.1.zip"
        }
      ],
      "properties": [
        {
          "name": "go:module:indirect",
          "value": "false"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:golang/github.com/gorilla/mux@v1.8.1",
      "name": "mux",
      "version": "v1.8.1",
      "description": "A powerful HTTP router and URL matcher for building Go web servers",
      "licenses": [
        {
          "license": {
            "id": "BSD-3-Clause"
          }
        }
      ],
      "purl": "pkg:golang/github.com/gorilla/mux@v1.8.1"
    },
    {
      "type": "library",
      "bom-ref": "pkg:golang/golang.org/x/crypto@v0.17.0",
      "name": "crypto",
      "version": "v0.17.0",
      "description": "Go supplementary cryptography libraries",
      "licenses": [
        {
          "license": {
            "id": "BSD-3-Clause"
          }
        }
      ],
      "purl": "pkg:golang/golang.org/x/crypto@v0.17.0"
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:golang/github.com/username/project@v1.0.0",
      "dependsOn": [
        "pkg:golang/github.com/gin-gonic/gin@v1.9.1",
        "pkg:golang/github.com/gorilla/mux@v1.8.1",
        "pkg:golang/golang.org/x/crypto@v0.17.0"
      ]
    },
    {
      "ref": "pkg:golang/github.com/gin-gonic/gin@v1.9.1",
      "dependsOn": [
        "pkg:golang/github.com/gin-contrib/sse@v0.1.0",
        "pkg:golang/github.com/go-playground/validator/v10@v10.14.0",
        "pkg:golang/github.com/mattn/go-isatty@v0.0.19",
        "pkg:golang/golang.org/x/net@v0.17.0"
      ]
    }
  ],
  "vulnerabilities": [
    {
      "bom-ref": "vuln:golang/golang.org/x/crypto@v0.14.0:CVE-2023-48795",
      "id": "CVE-2023-48795",
      "source": {
        "name": "NVD",
        "url": "https://nvd.nist.gov/vuln/detail/CVE-2023-48795"
      },
      "ratings": [
        {
          "source": {
            "name": "NVD"
          },
          "score": 5.9,
          "severity": "medium",
          "method": "CVSSv3",
          "vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:N"
        }
      ],
      "cwes": [222],
      "description": "Prefix truncation attack in SSH protocol",
      "recommendation": "Update to version v0.17.0 or higher",
      "affects": [
        {
          "ref": "pkg:golang/golang.org/x/crypto@v0.14.0",
          "versions": [
            {
              "version": "v0.14.0",
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
curl -Lo spdx-sbom-generator.tar.gz \
  https://github.com/opensbom-generator/spdx-sbom-generator/releases/latest/download/spdx-sbom-generator-linux-amd64.tar.gz
tar -xzf spdx-sbom-generator.tar.gz
sudo mv spdx-sbom-generator /usr/local/bin/

# Generate SPDX SBOM
spdx-sbom-generator -o . -f json

# Output: bom-go-mod.json (SPDX format)
```

### Using Syft

```bash
# Generate SPDX SBOM
syft packages dir:. -o spdx-json > ${OUTPUT_DIR}/exports/sbom.spdx.json

# Generate SPDX 2.3
syft packages . -o spdx-json@2.3 --file sbom.spdx.json
```

### SPDX SBOM Template (JSON)

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "project-1.0.0",
  "documentNamespace": "https://example.com/spdxdocs/project-1.0.0-uuid",
  "creationInfo": {
    "created": "2024-01-16T10:00:00Z",
    "creators": [
      "Tool: spdx-sbom-generator-0.0.13",
      "Person: Benjamin Dourthe (benjamin@adonamed.com)"
    ],
    "licenseListVersion": "3.21"
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-project",
      "name": "project",
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
          "referenceLocator": "pkg:golang/github.com/username/project@v1.0.0"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-gin",
      "name": "gin",
      "versionInfo": "v1.9.1",
      "downloadLocation": "https://github.com/gin-gonic/gin",
      "filesAnalyzed": false,
      "homepage": "https://github.com/gin-gonic/gin",
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright (c) 2014 Manuel Martínez-Almeida",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:golang/github.com/gin-gonic/gin@v1.9.1"
        },
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:gin-gonic:gin:1.9.1:*:*:*:*:go:*:*"
        }
      ]
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-DOCUMENT",
      "relationshipType": "DESCRIBES",
      "relatedSpdxElement": "SPDXRef-Package-project"
    },
    {
      "spdxElementId": "SPDXRef-Package-project",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-gin"
    }
  ]
}
```

## Phase 5: Vulnerability Scanning

Scan for known vulnerabilities in dependencies:

### Using govulncheck

```bash
# Install govulncheck
go install golang.org/x/vuln/cmd/govulncheck@latest

# Scan for vulnerabilities
govulncheck ./...

# JSON output
govulncheck -json ./... > ${OUTPUT_DIR}/exports/vulnerabilities.json

# Example output
{
  "Vulns": [
    {
      "OSV": {
        "id": "GO-2023-2375",
        "published": "2023-12-18T20:03:31Z",
        "modified": "2024-01-05T09:45:12Z",
        "aliases": ["CVE-2023-48795"],
        "summary": "Prefix truncation attack in SSH protocol",
        "details": "An attacker can compromise the integrity of an SSH channel...",
        "affected": [
          {
            "package": {
              "name": "golang.org/x/crypto",
              "ecosystem": "Go"
            },
            "ranges": [
              {
                "type": "SEMVER",
                "events": [
                  {
                    "introduced": "0"
                  },
                  {
                    "fixed": "0.17.0"
                  }
                ]
              }
            ]
          }
        ]
      }
    }
  ]
}

# Scan specific module
govulncheck -mode module ./...

# Scan source code (default)
govulncheck -mode source ./...
```

### Using Nancy (Sonatype OSS Index)

```bash
# Install Nancy
go install github.com/sonatype-nexus-community/nancy@latest

# Scan go.sum
nancy sleuth --path go.sum

# JSON output
nancy sleuth --path go.sum --output json > ${OUTPUT_DIR}/exports/nancy_report.json
```

### Using Trivy

```bash
# Install Trivy
# See: https://aquasecurity.github.io/trivy/

# Scan Go project
trivy fs --format json --output ${OUTPUT_DIR}/exports/trivy_report.json .

# Scan go.mod
trivy fs --scanners vuln go.mod

# Include indirect dependencies
trivy fs --scanners vuln --include-non-failures .
```

### Using Snyk

```bash
# Install Snyk CLI
npm install -g snyk

# Authenticate
snyk auth

# Test Go project
snyk test --json > ${OUTPUT_DIR}/exports/snyk_report.json

# Monitor project
snyk monitor
```

## Phase 6: License Analysis

### Using go-licenses

```bash
# Install go-licenses
go install github.com/google/go-licenses@latest

# List all licenses
go-licenses csv ./... > ${OUTPUT_DIR}/exports/licenses.csv

# Generate license report
go-licenses report ./... > ${OUTPUT_DIR}/exports/LICENSES.md

# Save license files
go-licenses save ./... --save_path=./third_party_licenses

# Check for restricted licenses
go-licenses check ./... --disallowed_types=restricted,forbidden

# Example CSV output
# Package,License,URL
github.com/gin-gonic/gin,MIT,https://github.com/gin-gonic/gin
github.com/gorilla/mux,BSD-3-Clause,https://github.com/gorilla/mux
golang.org/x/crypto,BSD-3-Clause,https://cs.opensource.google/go/x/crypto
```

### Using go-license-detector

```bash
# Install go-license-detector
go install go.elastic.co/go-license-detector@latest

# Detect licenses
go-license-detector -includeIndirect ./... > ${OUTPUT_DIR}/exports/licenses.json

# Example JSON output
{
  "github.com/gin-gonic/gin": "MIT",
  "github.com/gorilla/mux": "BSD-3-Clause",
  "golang.org/x/crypto": "BSD-3-Clause"
}
```

### License Compatibility Matrix

Document license compatibility:

```markdown
## License Compatibility

| License | Can Include | Cannot Include | Notes |
|---------|-------------|----------------|-------|
| MIT | Any | - | Very permissive |
| BSD-3-Clause | Any | - | Very permissive |
| BSD-2-Clause | Any | - | Very permissive |
| Apache-2.0 | MIT, BSD, Apache | - | Patent grant included |
| GPL-3.0 | MIT, BSD | Proprietary | Copyleft - requires source |
| LGPL-3.0 | MIT, BSD | - | Lesser copyleft |
| MPL-2.0 | MIT, BSD | - | Mozilla Public License |
| Proprietary | ? | GPL, AGPL | Check license terms |

**Current Project License**: MIT

**Compatibility Status**:

- ✅ Compatible: gin (MIT), mux (BSD-3-Clause), crypto (BSD-3-Clause)

- ⚠️ Review Required: [list needing review]

- ❌ Incompatible: [list of incompatible]
```

## Phase 7: Supply Chain Security Assessment

### Package Provenance

```bash
# Verify module checksums
go mod verify

# Download and verify all dependencies
go mod download -json

# Check module provenance with go.sum
cat go.sum

# Example go.sum entry
github.com/gin-gonic/gin v1.9.1 h1:4idEAncQnU5cB7BeOkPtxjfCSye0AAm1R0RVIqJ+Jmg=
github.com/gin-gonic/gin v1.9.1/go.mod h1:hPrL7YrpYKXt5YId3A/Tnip5kqbEAP+KLuI3SUcPTeU=
```

### Repository Security

For each dependency, document:

```markdown
## Dependency: github.com/gin-gonic/gin

**Repository**: https://github.com/gin-gonic/gin
**Package Registry**: Go Module Proxy (proxy.golang.org)
**Maintainer**: Gin Community

**Security Posture**:

- ✅ Active maintenance (last commit: [date])

- ✅ Security policy present

- ✅ Vulnerability disclosure process

- ✅ Module checksum verification (go.sum)

- ✅ Recent security audit

- ✅ Large, active community (75k+ stars)

- ✅ Transparent development

**Risk Assessment**: LOW

- Well-maintained, widely-used library

- Active security response

- Regular updates and patches

- Strong community oversight

**Alternative Options**:

- Echo (high performance alternative)

- Fiber (Express-inspired framework)

- Chi (lightweight router)
```

## Phase 8: Compliance Documentation

### NTIA Minimum Elements Compliance

```markdown
# NTIA SBOM Compliance Checklist

## Minimum Elements

- [x] **Supplier Name**: All suppliers identified in SBOM

- [x] **Component Name**: All components named (module paths)

- [x] **Version**: All versions specified (semantic versioning)

- [x] **Other Unique Identifiers**: PURL and CPE provided for all

- [x] **Dependency Relationships**: Complete dependency graph

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

- [x] Vulnerability scanning integrated (govulncheck)

**Compliance Status**: ✅ COMPLIANT
```

### EU Cyber Resilience Act Compliance

```markdown
# EU CRA Compliance Checklist

## Essential Requirements

- [x] Complete SBOM with all components

- [x] Known vulnerabilities identified (CVE tracking via govulncheck)

- [x] Security updates and patches tracked

- [x] Vulnerability disclosure timeline documented

- [x] Supply chain security assessed (go.sum verification)

## Documentation Requirements

- [x] SBOM in standardized format (CycloneDX/SPDX)

- [x] Vulnerability report attached (govulncheck)

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
   - Complete dependency graph
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
   - All known CVEs (from govulncheck)
   - Severity ratings
   - Remediation status
   - Mitigation strategies

2. **LICENSES.md**
   - All component licenses
   - License compatibility analysis
   - Attribution requirements
   - Compliance status

3. **DEPENDENCIES.md**
   - Dependency graph visualization
   - Direct dependencies
   - Indirect dependencies
   - Module replacements
   - Update recommendations

4. **SUPPLY_CHAIN.md**
   - Component provenance
   - Security assessment (go.sum verification)
   - Risk analysis
   - Alternative options
```

### Summary Report

```markdown
## SBOM Generation Summary

**Generated**: [timestamp]
**Project**: [name] v[version]
**License**: [license]
**Go Version**: 1.21

**Components**:

- Total modules: [count]

- Direct dependencies: [count]

- Indirect dependencies: [count]

- Unique licenses: [count]

**Vulnerabilities** (govulncheck):

- Critical: [count]

- High: [count]

- Moderate: [count]

- Low: [count]

- Total: [count]

**License Distribution**:

- MIT: [count]

- BSD-3-Clause: [count]

- Apache-2.0: [count]

- MPL-2.0: [count]

- Other: [count]

**Compliance**:

- NTIA Minimum Elements: ✅/❌

- EU CRA Requirements: ✅/❌

- SPDX 2.3 Compliant: ✅/❌

- CycloneDX 1.4 Compliant: ✅/❌

**Supply Chain Risk**: [LOW/MEDIUM/HIGH]

**Actions Required**:

- [ ] Update [X] modules with known vulnerabilities

- [ ] Review [Y] modules with license concerns

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

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Install SBOM tools
        run: |
          go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest
          go install golang.org/x/vuln/cmd/govulncheck@latest
          go install github.com/google/go-licenses@latest

      - name: Generate CycloneDX SBOM
        run: cyclonedx-gomod mod -json -output sbom.json -licenses

      - name: Run govulncheck
        run: govulncheck -json ./... > ${OUTPUT_DIR}/exports/vulnerabilities.json || true

      - name: Generate license report
        run: go-licenses csv ./... > ${OUTPUT_DIR}/exports/licenses.csv

      - name: Upload SBOM artifacts
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: |
            sbom.json
            vulnerabilities.json
            licenses.csv

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
  image: golang:1.21
  script:
    - go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest
    - go install golang.org/x/vuln/cmd/govulncheck@latest
    - cyclonedx-gomod mod -json -output sbom.json -licenses
    - govulncheck -json ./... > ${OUTPUT_DIR}/exports/vulnerabilities.json || true
  artifacts:
    paths:
      - sbom.json
      - vulnerabilities.json
    expire_in: 1 year
```

---

## Best Practices

1. **Automate SBOM Generation**
   - Integrate into build process
   - Generate in CI/CD pipeline
   - Update with every release
   - Include in release artifacts

2. **Keep SBOMs Current**
   - Regenerate on dependency updates
   - Track vulnerability fixes (govulncheck)
   - Document changes between versions
   - Run go mod verify regularly

3. **Use Multiple Formats**
   - CycloneDX for security
   - SPDX for license compliance
   - Both for comprehensive coverage

4. **Continuous Monitoring**
   - Monitor for new vulnerabilities (govulncheck)
   - Track dependency updates (Dependabot)
   - Assess supply chain risks (go.sum)
   - Enable Go Module Proxy verification

5. **Publish Transparently**
   - Include SBOM in releases
   - Make publicly available
   - Provide easy access
   - Document update process

---

## Output Format Specifications

The SBOM should:

- Comply with NTIA minimum elements requirements

- Meet EU Cyber Resilience Act standards

- Use standard formats (CycloneDX 1.4+ or SPDX 2.3+)

- Include complete dependency graph with versions

- Document all known vulnerabilities with CVE IDs

- Provide license information for all components

- Assess supply chain security risks (go.sum)

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
