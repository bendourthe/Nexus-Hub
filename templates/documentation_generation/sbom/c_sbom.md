---
template_id: c_sbom
template_name: Sbom - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: documentation
phase: sbom
difficulty: beginner
estimated_time_hours: 2-3
prerequisites: []
tools:

  - unity

  - cmocka

  - check
tags:

  - documentation

  - documentation

  - c
---
# C SBOM Generation

## Objective
Generate comprehensive, standards-compliant Software Bill of Materials (SBOM) documentation that meets regulatory requirements (NTIA minimum elements, EU Cyber Resilience Act) for security, compliance, and supply chain management in C projects with manual dependency tracking and package managers (Conan, vcpkg).

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

- [ ] System libraries documented

- [ ] Static vs dynamic linking tracked

- [ ] Build-time vs runtime dependencies

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
# C SBOM Generation Request

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

Please generate a comprehensive Software Bill of Materials (SBOM) for this C project following this protocol:

## Phase 1: Dependency Discovery & Analysis

### Option A: Using Conan Package Manager

1. **Inventory Direct Dependencies**

   Analyze `conanfile.txt` or `conanfile.py`:

   ```bash
   # List all dependencies
   conan info . > ${OUTPUT_DIR}/exports/dependencies.txt

   # Generate dependency graph
   conan info . --graph=graph.html

   # JSON output
   conan info . --json=dependencies.json

   # List with full details
   conan info . --only requires
   ```

2. **Map Transitive Dependencies**

   ```bash
   # Full dependency tree
   conan info . --graph-depth=10

   # Visualize dependencies
   conan info . --graph=graph.dot
   dot -Tpng graph.dot -o dependencies.png

   # Get package info
   conan search zlib/1.2.13@ --remote=all
   ```

### Option B: Using vcpkg Package Manager

1. **Inventory Direct Dependencies**

   Analyze `vcpkg.json`:

   ```bash
   # List installed packages
   vcpkg list > ${OUTPUT_DIR}/exports/dependencies.txt

   # Get package information
   vcpkg search zlib

   # Export installed packages
   vcpkg export --output=packages.zip

   # Show dependencies for a package
   vcpkg depend-info zlib
   ```

2. **Map Transitive Dependencies**

   ```bash
   # Show full dependency tree
   vcpkg depend-info zlib --depth=10

   # List all dependencies recursively
   vcpkg list --x-full-desc
   ```

### Option C: Manual Dependency Tracking

1. **Inventory Dependencies**

   For projects without package managers:

   ```markdown
   ## Manual Dependency Inventory

   ### Direct Dependencies

   | Library | Version | Source | License | Purpose |
   |---------|---------|--------|---------|---------|
   | zlib | 1.2.13 | https://zlib.net/ | Zlib | Compression |
   | OpenSSL | 3.0.12 | https://www.openssl.org/ | Apache-2.0 | Cryptography |
   | libcurl | 8.5.0 | https://curl.se/ | curl | HTTP client |
   | SQLite | 3.44.2 | https://www.sqlite.org/ | Public Domain | Database |

   ### System Libraries

   | Library | Version | Purpose |
   |---------|---------|---------|
   | glibc | 2.35 | C standard library |
   | libpthread | - | POSIX threads |
   | libm | - | Math library |

   ### Build Dependencies

   | Tool | Version | Purpose |
   |------|---------|---------|
   | GCC | 11.4.0 | Compiler |
   | CMake | 3.25.0 | Build system |
   | Make | 4.3 | Build tool |
   ```

2. **Identify Dependency Metadata**

   For each dependency, collect:

   - Library name

   - Version

   - License

   - Source URL/repository

   - Download URL

   - Checksum (SHA-256)

   - Installation location

   - Linking type (static/dynamic)

   - Dependencies (for transitive mapping)

## Phase 2: SBOM Format Selection

Choose SBOM format based on requirements:

### Option 1: SPDX (Software Package Data Exchange)

- **Standard**: ISO/IEC 5962:2021

- **Format**: JSON, YAML, RDF, Tag-Value

- **Best for**: License compliance, legal requirements

- **Tools**: spdx-sbom-generator, syft, scancode

### Option 2: CycloneDX

- **Standard**: OWASP CycloneDX

- **Format**: JSON, XML

- **Best for**: Security analysis, vulnerability management

- **Tools**: syft, grype, cdxgen

### Option 3: SWID (Software Identification Tags)

- **Standard**: ISO/IEC 19770-2:2015

- **Format**: XML

- **Best for**: IT asset management

**Recommendation**: Use CycloneDX for security focus, SPDX for license focus.

## Phase 3: Generate SBOM (CycloneDX Format)

### Using Syft

```bash
# Install Syft
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Scan binary for dependencies
syft packages file:./myapp -o cyclonedx-json > ${OUTPUT_DIR}/exports/sbom.json

# Scan directory
syft packages dir:. -o cyclonedx-json > ${OUTPUT_DIR}/exports/sbom.json

# Scan with all catalogers
syft packages . -o cyclonedx-json --catalogers all --file sbom.json

# Include system packages
syft packages . -o cyclonedx-json --scope all-layers
```

### Using Conan to Generate CycloneDX

```bash
# Install CycloneDX Conan plugin
pip install cyclonedx-conan

# Generate SBOM from Conan
cyclonedx-conan --output ${OUTPUT_DIR}/exports/sbom.json

# With specific conanfile
cyclonedx-conan --conanfile conanfile.txt --output ${OUTPUT_DIR}/exports/sbom.json
```

### Manual CycloneDX SBOM Template (JSON)

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
        "vendor": "Manual",
        "name": "SBOM Generator",
        "version": "1.0.0"
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
      "bom-ref": "pkg:generic/myapp@1.0.0",
      "name": "myapp",
      "version": "1.0.0",
      "description": "My C application",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:generic/myapp@1.0.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://github.com/username/myapp"
        },
        {
          "type": "vcs",
          "url": "https://github.com/username/myapp.git"
        }
      ]
    }
  },
  "components": [
    {
      "type": "library",
      "bom-ref": "pkg:generic/zlib@1.2.13",
      "name": "zlib",
      "version": "1.2.13",
      "description": "A massively spiffy yet delicately unobtrusive compression library",
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "b3a24de97a8fdbc835b9833169501030b8977031bcb54b3b3ac13740f846ab30"
        }
      ],
      "licenses": [
        {
          "license": {
            "id": "Zlib"
          }
        }
      ],
      "purl": "pkg:generic/zlib@1.2.13",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://zlib.net/"
        },
        {
          "type": "vcs",
          "url": "https://github.com/madler/zlib"
        },
        {
          "type": "distribution",
          "url": "https://zlib.net/zlib-1.2.13.tar.gz"
        }
      ],
      "properties": [
        {
          "name": "linking:type",
          "value": "dynamic"
        },
        {
          "name": "library:type",
          "value": "system"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:generic/openssl@3.0.12",
      "name": "openssl",
      "version": "3.0.12",
      "description": "TLS/SSL and crypto library",
      "licenses": [
        {
          "license": {
            "id": "Apache-2.0"
          }
        }
      ],
      "purl": "pkg:generic/openssl@3.0.12",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://www.openssl.org/"
        },
        {
          "type": "vcs",
          "url": "https://github.com/openssl/openssl"
        }
      ],
      "properties": [
        {
          "name": "linking:type",
          "value": "dynamic"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:generic/libcurl@8.5.0",
      "name": "libcurl",
      "version": "8.5.0",
      "description": "The multiprotocol file transfer library",
      "licenses": [
        {
          "license": {
            "id": "curl"
          }
        }
      ],
      "purl": "pkg:generic/libcurl@8.5.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://curl.se/libcurl/"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:generic/sqlite@3.44.2",
      "name": "sqlite",
      "version": "3.44.2",
      "description": "Self-contained SQL database engine",
      "licenses": [
        {
          "license": {
            "name": "Public Domain"
          }
        }
      ],
      "purl": "pkg:generic/sqlite@3.44.2"
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:generic/myapp@1.0.0",
      "dependsOn": [
        "pkg:generic/zlib@1.2.13",
        "pkg:generic/openssl@3.0.12",
        "pkg:generic/libcurl@8.5.0",
        "pkg:generic/sqlite@3.44.2"
      ]
    },
    {
      "ref": "pkg:generic/libcurl@8.5.0",
      "dependsOn": [
        "pkg:generic/openssl@3.0.12",
        "pkg:generic/zlib@1.2.13"
      ]
    }
  ],
  "vulnerabilities": [
    {
      "bom-ref": "vuln:generic/zlib@1.2.12:CVE-2022-37434",
      "id": "CVE-2022-37434",
      "source": {
        "name": "NVD",
        "url": "https://nvd.nist.gov/vuln/detail/CVE-2022-37434"
      },
      "ratings": [
        {
          "source": {
            "name": "NVD"
          },
          "score": 9.8,
          "severity": "critical",
          "method": "CVSSv3",
          "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        }
      ],
      "cwes": [787],
      "description": "Heap-based buffer over-read in inflate.c",
      "recommendation": "Update to version 1.2.13 or higher",
      "affects": [
        {
          "ref": "pkg:generic/zlib@1.2.12",
          "versions": [
            {
              "version": "1.2.12",
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

# Generate SPDX SBOM (requires CMakeLists.txt or similar)
spdx-sbom-generator -o . -f json

# Output: bom-cmake.json (SPDX format)
```

### Using Syft

```bash
# Generate SPDX SBOM
syft packages file:./myapp -o spdx-json > ${OUTPUT_DIR}/exports/sbom.spdx.json

# SPDX 2.3 format
syft packages . -o spdx-json@2.3 --file sbom.spdx.json
```

### Using ScanCode

```bash
# Install ScanCode Toolkit
pip install scancode-toolkit

# Generate SPDX SBOM
scancode -clpieu --spdx-rdf sbom.spdx.rdf .

# JSON format
scancode -clpieu --json-pp sbom.json .
```

### Manual SPDX SBOM Template (JSON)

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "myapp-1.0.0",
  "documentNamespace": "https://example.com/spdxdocs/myapp-1.0.0-uuid",
  "creationInfo": {
    "created": "2024-01-16T10:00:00Z",
    "creators": [
      "Tool: Manual-1.0.0",
      "Person: Benjamin Dourthe (benjamin@adonamed.com)"
    ],
    "licenseListVersion": "3.21"
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-myapp",
      "name": "myapp",
      "versionInfo": "1.0.0",
      "downloadLocation": "https://github.com/username/myapp",
      "filesAnalyzed": true,
      "homepage": "https://github.com/username/myapp",
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright (c) 2024 Benjamin Dourthe",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:generic/myapp@1.0.0"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-zlib",
      "name": "zlib",
      "versionInfo": "1.2.13",
      "downloadLocation": "https://zlib.net/zlib-1.2.13.tar.gz",
      "filesAnalyzed": false,
      "homepage": "https://zlib.net/",
      "licenseConcluded": "Zlib",
      "licenseDeclared": "Zlib",
      "copyrightText": "Copyright (c) 1995-2022 Jean-loup Gailly and Mark Adler",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:generic/zlib@1.2.13"
        },
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:zlib:zlib:1.2.13:*:*:*:*:*:*:*"
        }
      ],
      "checksums": [
        {
          "algorithm": "SHA256",
          "checksumValue": "b3a24de97a8fdbc835b9833169501030b8977031bcb54b3b3ac13740f846ab30"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-openssl",
      "name": "openssl",
      "versionInfo": "3.0.12",
      "downloadLocation": "https://www.openssl.org/source/openssl-3.0.12.tar.gz",
      "filesAnalyzed": false,
      "homepage": "https://www.openssl.org/",
      "licenseConcluded": "Apache-2.0",
      "licenseDeclared": "Apache-2.0",
      "copyrightText": "Copyright (c) The OpenSSL Project",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:generic/openssl@3.0.12"
        },
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:openssl:openssl:3.0.12:*:*:*:*:*:*:*"
        }
      ]
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-DOCUMENT",
      "relationshipType": "DESCRIBES",
      "relatedSpdxElement": "SPDXRef-Package-myapp"
    },
    {
      "spdxElementId": "SPDXRef-Package-myapp",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-zlib"
    },
    {
      "spdxElementId": "SPDXRef-Package-myapp",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-openssl"
    }
  ]
}
```

## Phase 5: Vulnerability Scanning

Scan for known vulnerabilities in dependencies:

### Using Grype

```bash
# Install Grype
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# Scan binary
grype file:./myapp -o json > ${OUTPUT_DIR}/exports/vulnerabilities.json

# Scan directory
grype dir:. -o json > ${OUTPUT_DIR}/exports/vulnerabilities.json

# Use SBOM as input
grype sbom:./sbom.json -o json

# Example JSON output
{
  "matches": [
    {
      "vulnerability": {
        "id": "CVE-2022-37434",
        "dataSource": "https://nvd.nist.gov/vuln/detail/CVE-2022-37434",
        "namespace": "nvd:cpe",
        "severity": "Critical",
        "cvss": [
          {
            "version": "3.1",
            "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            "metrics": {
              "baseScore": 9.8
            }
          }
        ]
      },
      "artifact": {
        "name": "zlib",
        "version": "1.2.12",
        "type": "c-library",
        "purl": "pkg:generic/zlib@1.2.12"
      }
    }
  ]
}
```

### Using Trivy

```bash
# Install Trivy
# See: https://aquasecurity.github.io/trivy/

# Scan binary
trivy fs --format json --output ${OUTPUT_DIR}/exports/trivy_report.json ./myapp

# Scan directory
trivy fs --scanners vuln .

# Use SBOM as input
trivy sbom sbom.json
```

### Using OSS Index (for Conan/vcpkg)

```bash
# For Conan packages
# Install jake
pip install jake

# Scan Conan packages
jake iq --conan conanfile.txt

# For vcpkg (manual check via CVE databases)
# Check each package against:
# - https://nvd.nist.gov/
# - https://www.cvedetails.com/
# - https://github.com/advisories
```

### Manual CVE Checking

```bash
# Check each library against CVE databases
# Example for zlib
curl -s "https://services.nvd.nist.gov/rest/json/cves/1.0?keyword=zlib" | jq .

# Or use cve-search
git clone https://github.com/cve-search/cve-search.git
cd cve-search
./sbin/db_mgmt_cpe_dictionary.py -p
./sbin/db_mgmt_cve.py -p
./bin/search.py -p zlib
```

## Phase 6: License Analysis

### Using ScanCode

```bash
# Install ScanCode
pip install scancode-toolkit

# Scan for licenses
scancode -l --json-pp licenses.json .

# Generate license report
scancode -l --html licenses.html .

# Full scan (licenses, copyrights, packages)
scancode -clpieu --json-pp full_scan.json .

# Example output
{
  "files": [
    {
      "path": "src/main.c",
      "licenses": [
        {
          "key": "mit",
          "name": "MIT License",
          "category": "Permissive"
        }
      ]
    }
  ]
}
```

### Using FOSSology

```bash
# Install FOSSology (via Docker)
docker run -p 8081:80 fossology/fossology

# Upload source for analysis
# Access web interface at http://localhost:8081
# Generates comprehensive license report
```

### Manual License Documentation

```markdown
## License Analysis

### Direct Dependencies

| Library | Version | License | Source |
|---------|---------|---------|--------|
| zlib | 1.2.13 | Zlib | https://zlib.net/zlib_license.html |
| OpenSSL | 3.0.12 | Apache-2.0 | https://www.openssl.org/source/license-openssl-ssleay.txt |
| libcurl | 8.5.0 | curl | https://curl.se/docs/copyright.html |
| SQLite | 3.44.2 | Public Domain | https://www.sqlite.org/copyright.html |

### License Texts

Include full license text for each dependency in `LICENSES/` directory:

- LICENSES/zlib.txt

- LICENSES/Apache-2.0.txt

- LICENSES/curl.txt

- LICENSES/sqlite-public-domain.txt
```

### License Compatibility Matrix

```markdown
## License Compatibility

| License | Can Include | Cannot Include | Notes |
|---------|-------------|----------------|-------|
| MIT | Any | - | Very permissive |
| Apache-2.0 | MIT, BSD, Apache | - | Patent grant included |
| BSD-3-Clause | Any | - | Very permissive |
| Zlib | Any | - | Very permissive |
| GPL-3.0 | MIT, BSD, LGPL | Proprietary | Copyleft - requires source |
| LGPL-3.0 | MIT, BSD | - | Lesser copyleft (dynamic linking OK) |
| Public Domain | Any | - | No restrictions |

**Current Project License**: MIT

**Compatibility Status**:

- ✅ Compatible: zlib (Zlib), OpenSSL (Apache-2.0), libcurl (curl), SQLite (Public Domain)

- ⚠️ Review Required: [list needing review]

- ❌ Incompatible: [list of incompatible]
```

## Phase 7: Supply Chain Security Assessment

### Package Provenance

```bash
# Verify checksums
sha256sum downloaded_library.tar.gz
# Compare with official checksum

# Example for zlib
curl -s https://zlib.net/zlib-1.2.13.tar.gz | sha256sum
# Should match: b3a24de97a8fdbc835b9833169501030b8977031bcb54b3b3ac13740f846ab30

# Verify GPG signatures
wget https://zlib.net/zlib-1.2.13.tar.gz.asc
gpg --verify zlib-1.2.13.tar.gz.asc zlib-1.2.13.tar.gz

# For Conan
conan config set general.revisions_enabled=1
# Enables package revision tracking

# For vcpkg
vcpkg install zlib --triplet x64-linux
# Check vcpkg\ports\zlib\portfile.cmake for source URLs and hashes
```

### Repository Security

For each dependency, document:

```markdown
## Dependency: zlib

**Repository**: https://github.com/madler/zlib
**Official Website**: https://zlib.net/
**Maintainer**: Mark Adler, Jean-loup Gailly

**Security Posture**:

- ✅ Active maintenance (last commit: [date])

- ✅ Security policy present

- ✅ Vulnerability disclosure process

- ✅ GPG signed releases

- ✅ Widely used and audited (core system library)

- ✅ Transparent development

- ⚠️ Minimal recent activity (mature project)

**Risk Assessment**: LOW

- Extremely well-established library

- Core system component

- Extensive real-world testing

- Regular security audits

**Verification Steps**:

1. Download from official source

2. Verify SHA-256 checksum

3. Verify GPG signature

4. Build from source with known-good compiler

**Alternative Options**:

- zlib-ng (optimized fork)

- miniz (single-file alternative)
```

## Phase 8: Compliance Documentation

### NTIA Minimum Elements Compliance

```markdown
# NTIA SBOM Compliance Checklist

## Minimum Elements

- [x] **Supplier Name**: All suppliers identified in SBOM

- [x] **Component Name**: All components named (library names)

- [x] **Version**: All versions specified

- [x] **Other Unique Identifiers**: PURL and CPE provided for all

- [x] **Dependency Relationships**: Complete dependency tree

- [x] **Author of SBOM Data**: [Benjamin Dourthe]

- [x] **Timestamp**: [2024-01-16T10:00:00Z]

## Automation Supportability

- [x] SBOM in machine-readable format (CycloneDX JSON)

- [x] Consistent data format across components

- [x] Unique identifiers (PURL/CPE) for all components

- [x] Dependency relationships machine-parseable

## Practices and Processes

- [x] SBOM generation process documented

- [x] SBOM updated with each release

- [x] SBOM published alongside releases

- [x] Vulnerability scanning integrated (Grype/Trivy)

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

- [x] Supply chain security assessed (checksums, signatures)

## Documentation Requirements

- [x] SBOM in standardized format (CycloneDX/SPDX)

- [x] Vulnerability report attached (Grype/Trivy)

- [x] License compliance documented (ScanCode)

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

   - Complete dependency list

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
```

### Supporting Documentation

```markdown
## Supporting Files

1. **VULNERABILITIES.md**

   - All known CVEs (from Grype/Trivy)

   - Severity ratings

   - Remediation status

   - Mitigation strategies

2. **LICENSES.md**

   - All component licenses

   - License compatibility analysis

   - Attribution requirements

   - Compliance status

3. **LICENSES/** (directory)

   - Full license texts for all dependencies

4. **DEPENDENCIES.md**

   - Dependency tree visualization

   - Direct dependencies

   - Transitive dependencies

   - System libraries

   - Build dependencies

   - Update recommendations

5. **SUPPLY_CHAIN.md**

   - Component provenance

   - Security assessment

   - Checksum verification

   - Risk analysis

   - Alternative options
```

### Summary Report

```markdown
## SBOM Generation Summary

**Generated**: [timestamp]
**Project**: [name] v[version]
**License**: [license]
**Compiler**: GCC 11.4.0
**Build System**: CMake 3.25.0

**Components**:

- Total libraries: [count]

- Direct dependencies: [count]

- System libraries: [count]

- Build dependencies: [count]

- Unique licenses: [count]

**Vulnerabilities** (Grype/Trivy):

- Critical: [count]

- High: [count]

- Medium: [count]

- Low: [count]

- Total: [count]

**License Distribution**:

- MIT: [count]

- Apache-2.0: [count]

- BSD-3-Clause: [count]

- Zlib: [count]

- Public Domain: [count]

- Other: [count]

**Compliance**:

- NTIA Minimum Elements: ✅/❌

- EU CRA Requirements: ✅/❌

- SPDX 2.3 Compliant: ✅/❌

- CycloneDX 1.4 Compliant: ✅/❌

**Supply Chain Risk**: [LOW/MEDIUM/HIGH]

**Actions Required**:

- [ ] Update [X] libraries with known vulnerabilities

- [ ] Review [Y] libraries with license concerns

- [ ] Verify checksums for [Z] dependencies
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

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y cmake build-essential

      - name: Build project
        run: |
          mkdir build && cd build
          cmake ..
          make

      - name: Install SBOM tools
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
          pip install scancode-toolkit

      - name: Generate SBOM with Syft
        run: syft packages dir:. -o cyclonedx-json > ${OUTPUT_DIR}/exports/sbom.json

      - name: Scan for vulnerabilities
        run: grype sbom:./sbom.json -o json > ${OUTPUT_DIR}/exports/vulnerabilities.json

      - name: Scan for licenses
        run: scancode -l --json-pp licenses.json .

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

---

## Best Practices

1. **Manual Tracking for C Projects**

   - Maintain comprehensive dependency inventory

   - Document all system libraries

   - Track both build-time and runtime dependencies

   - Use package managers when possible (Conan, vcpkg)

2. **Keep SBOMs Current**

   - Regenerate on dependency updates

   - Track vulnerability fixes

   - Document changes between versions

   - Verify checksums regularly

3. **Use Multiple Formats**

   - CycloneDX for security

   - SPDX for license compliance

   - Both for comprehensive coverage

4. **Continuous Monitoring**

   - Monitor for new vulnerabilities (Grype, Trivy)

   - Track dependency updates manually

   - Assess supply chain risks (checksums, signatures)

   - Subscribe to security mailing lists

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

- Include complete dependency inventory

- Document all known vulnerabilities with CVE IDs

- Provide license information for all components

- Assess supply chain security risks (checksums, signatures)

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
