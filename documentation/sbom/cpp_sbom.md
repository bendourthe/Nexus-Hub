# C++ SBOM Generation

## Objective
Generate comprehensive, standards-compliant Software Bill of Materials (SBOM) documentation that meets regulatory requirements (NTIA minimum elements, EU Cyber Resilience Act) for security, compliance, and supply chain management in C++ projects using CMake, Conan, and vcpkg.

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

- Create `documentation/sbom/` directory in repository root if it doesn't exist

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
- [ ] Header-only libraries tracked
- [ ] System libraries documented
- [ ] Static vs dynamic linking tracked

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
# C++ SBOM Generation Request

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please generate a comprehensive Software Bill of Materials (SBOM) for this C++ project following this protocol:

## Phase 1: Dependency Discovery & Analysis

### Option A: Using Conan Package Manager

1. **Inventory Direct Dependencies**

   Analyze `conanfile.txt` or `conanfile.py`:

   ```bash
   # List all dependencies
   conan info . > dependencies.txt

   # Generate dependency graph
   conan info . --graph=graph.html

   # JSON output
   conan info . --json=dependencies.json

   # List with full details
   conan info . --only requires

   # Show package information
   conan search boost/1.81.0@ --remote=all
   ```

2. **Map Transitive Dependencies**

   ```bash
   # Full dependency tree
   conan info . --graph-depth=10

   # Visualize dependencies
   conan info . --graph=graph.dot
   dot -Tpng graph.dot -o dependencies.png

   # Get detailed package info
   conan inspect boost/1.81.0@
   ```

### Option B: Using vcpkg Package Manager

1. **Inventory Direct Dependencies**

   Analyze `vcpkg.json`:

   ```bash
   # List installed packages
   vcpkg list > dependencies.txt

   # Get package information
   vcpkg search boost

   # Export installed packages
   vcpkg export --output=packages.zip --output-type=zip

   # Show dependencies for a package
   vcpkg depend-info boost
   ```

2. **Map Transitive Dependencies**

   ```bash
   # Show full dependency tree
   vcpkg depend-info boost --depth=10

   # List all dependencies with descriptions
   vcpkg list --x-full-desc

   # Check installed features
   vcpkg list boost
   ```

### Option C: Using CMake with FetchContent/find_package

1. **Extract Dependencies from CMakeLists.txt**

   ```bash
   # Generate build files
   cmake -B build -S .

   # List linked libraries
   cmake --build build --target help

   # Export compile commands
   cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

   # Analyze compile_commands.json for dependencies
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
   - Linking type (static/dynamic/header-only)
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
- **Tools**: syft, grype, cyclonedx-conan

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
syft packages file:./myapp -o cyclonedx-json > sbom.json

# Scan directory
syft packages dir:. -o cyclonedx-json > sbom.json

# Scan with all catalogers
syft packages . -o cyclonedx-json --catalogers all --file sbom.json

# Include C++ libraries
syft packages dir:./build -o cyclonedx-json
```

### Using Conan with CycloneDX Plugin

```bash
# Install CycloneDX Conan plugin
pip install cyclonedx-conan

# Generate SBOM from Conan
cyclonedx-conan --output sbom.json

# With specific conanfile
cyclonedx-conan --conanfile conanfile.txt --output sbom.json

# Include all transitive dependencies
cyclonedx-conan --conanfile conanfile.txt --output sbom.json --include-transitive
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
        "name": "cyclonedx-conan",
        "version": "2.0.0"
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
      "description": "My C++ application",
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
        },
        {
          "type": "build-system",
          "url": "https://github.com/username/myapp/blob/main/CMakeLists.txt"
        }
      ]
    }
  },
  "components": [
    {
      "type": "library",
      "bom-ref": "pkg:conan/boost@1.81.0",
      "name": "boost",
      "version": "1.81.0",
      "description": "Peer-reviewed portable C++ source libraries",
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "71feeed900fbccca04a3b4f2f84a7c217186f28a940ed8b7ed4725986baf99fa"
        }
      ],
      "licenses": [
        {
          "license": {
            "id": "BSL-1.0"
          }
        }
      ],
      "purl": "pkg:conan/boost@1.81.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://www.boost.org/"
        },
        {
          "type": "vcs",
          "url": "https://github.com/boostorg/boost"
        },
        {
          "type": "distribution",
          "url": "https://boostorg.jfrog.io/artifactory/main/release/1.81.0/source/boost_1_81_0.tar.gz"
        }
      ],
      "properties": [
        {
          "name": "conan:package_id",
          "value": "abc123def456"
        },
        {
          "name": "cpp:library_type",
          "value": "header-only"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:conan/fmt@9.1.0",
      "name": "fmt",
      "version": "9.1.0",
      "description": "A modern formatting library",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:conan/fmt@9.1.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://fmt.dev/"
        },
        {
          "type": "vcs",
          "url": "https://github.com/fmtlib/fmt"
        }
      ],
      "properties": [
        {
          "name": "cpp:library_type",
          "value": "static"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:conan/spdlog@1.11.0",
      "name": "spdlog",
      "version": "1.11.0",
      "description": "Fast C++ logging library",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:conan/spdlog@1.11.0",
      "externalReferences": [
        {
          "type": "vcs",
          "url": "https://github.com/gabime/spdlog"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:vcpkg/nlohmann-json@3.11.2",
      "name": "nlohmann-json",
      "version": "3.11.2",
      "description": "JSON for Modern C++",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:vcpkg/nlohmann-json@3.11.2",
      "externalReferences": [
        {
          "type": "vcs",
          "url": "https://github.com/nlohmann/json"
        }
      ],
      "properties": [
        {
          "name": "cpp:library_type",
          "value": "header-only"
        }
      ]
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:generic/myapp@1.0.0",
      "dependsOn": [
        "pkg:conan/boost@1.81.0",
        "pkg:conan/fmt@9.1.0",
        "pkg:conan/spdlog@1.11.0",
        "pkg:vcpkg/nlohmann-json@3.11.2"
      ]
    },
    {
      "ref": "pkg:conan/spdlog@1.11.0",
      "dependsOn": [
        "pkg:conan/fmt@9.1.0"
      ]
    }
  ],
  "vulnerabilities": [
    {
      "bom-ref": "vuln:conan/boost@1.78.0:CVE-2022-21854",
      "id": "CVE-2022-21854",
      "source": {
        "name": "NVD",
        "url": "https://nvd.nist.gov/vuln/detail/CVE-2022-21854"
      },
      "ratings": [
        {
          "source": {
            "name": "NVD"
          },
          "score": 7.5,
          "severity": "high",
          "method": "CVSSv3",
          "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H"
        }
      ],
      "cwes": [190],
      "description": "Integer overflow in Boost.Filesystem",
      "recommendation": "Update to version 1.79.0 or higher",
      "affects": [
        {
          "ref": "pkg:conan/boost@1.78.0",
          "versions": [
            {
              "version": "1.78.0",
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

# Generate SPDX SBOM (for CMake projects)
spdx-sbom-generator -o . -f json

# Output: bom-cmake.json (SPDX format)
```

### Using Syft

```bash
# Generate SPDX SBOM
syft packages file:./myapp -o spdx-json > sbom.spdx.json

# SPDX 2.3 format
syft packages dir:. -o spdx-json@2.3 --file sbom.spdx.json

# From build directory
syft packages dir:./build -o spdx-json > sbom.spdx.json
```

### SPDX SBOM Template (JSON)

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
      "Tool: spdx-sbom-generator-0.0.13",
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
      "SPDXID": "SPDXRef-Package-boost",
      "name": "boost",
      "versionInfo": "1.81.0",
      "downloadLocation": "https://boostorg.jfrog.io/artifactory/main/release/1.81.0/source/boost_1_81_0.tar.gz",
      "filesAnalyzed": false,
      "homepage": "https://www.boost.org/",
      "licenseConcluded": "BSL-1.0",
      "licenseDeclared": "BSL-1.0",
      "copyrightText": "Copyright (c) Boost authors",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:conan/boost@1.81.0"
        },
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:boost:boost:1.81.0:*:*:*:*:*:*:*"
        }
      ],
      "checksums": [
        {
          "algorithm": "SHA256",
          "checksumValue": "71feeed900fbccca04a3b4f2f84a7c217186f28a940ed8b7ed4725986baf99fa"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-fmt",
      "name": "fmt",
      "versionInfo": "9.1.0",
      "downloadLocation": "https://github.com/fmtlib/fmt/archive/refs/tags/9.1.0.tar.gz",
      "filesAnalyzed": false,
      "homepage": "https://fmt.dev/",
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright (c) Victor Zverovich",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:conan/fmt@9.1.0"
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
      "relatedSpdxElement": "SPDXRef-Package-boost"
    },
    {
      "spdxElementId": "SPDXRef-Package-myapp",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-fmt"
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
grype file:./myapp -o json > vulnerabilities.json

# Scan directory
grype dir:. -o json > vulnerabilities.json

# Use SBOM as input
grype sbom:./sbom.json -o json

# Scan build directory
grype dir:./build -o json

# Example JSON output
{
  "matches": [
    {
      "vulnerability": {
        "id": "CVE-2022-21854",
        "dataSource": "https://nvd.nist.gov/vuln/detail/CVE-2022-21854",
        "namespace": "nvd:cpe",
        "severity": "High",
        "cvss": [
          {
            "version": "3.1",
            "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
            "metrics": {
              "baseScore": 7.5
            }
          }
        ]
      },
      "artifact": {
        "name": "boost",
        "version": "1.78.0",
        "type": "cpp-library",
        "purl": "pkg:conan/boost@1.78.0"
      }
    }
  ]
}
```

### Using Trivy

```bash
# Install Trivy
# See: https://aquasecurity.github.io/trivy/

# Scan C++ binary
trivy fs --format json --output trivy_report.json ./myapp

# Scan directory
trivy fs --scanners vuln .

# Scan build artifacts
trivy fs --scanners vuln ./build

# Use SBOM as input
trivy sbom sbom.json
```

### Using Conan with Vulnerability Database

```bash
# Check for known vulnerabilities in Conan packages
# Currently limited, but improving

# Check package details
conan inspect boost/1.81.0@

# Search for security advisories
# Check: https://github.com/conan-io/conan-center-index/security/advisories
```

### Using vcpkg with Vulnerability Scanning

```bash
# vcpkg has built-in baseline tracking
# Check for updates and security fixes

# Update vcpkg
git pull origin master

# Check for package updates
vcpkg upgrade --no-dry-run

# Verify package versions against known vulnerabilities
# Cross-reference with NVD or GitHub Advisories
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

# Scan specific directories
scancode -l --json-pp licenses.json ./src ./include

# Example output
{
  "files": [
    {
      "path": "include/myapp.hpp",
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

### Using Conan for License Information

```bash
# Get license info for packages
conan info . --json=conan_info.json

# Extract license from package recipe
conan inspect boost/1.81.0@ | grep license

# Example extraction script
conan info . --only requires | while read pkg; do
    conan inspect $pkg | grep -E "(license|License)"
done
```

### Using vcpkg for License Information

```bash
# Check package license
vcpkg install boost --dry-run
# Check: vcpkg\ports\boost\vcpkg.json for license field

# List all with licenses
vcpkg list --x-json | jq '.[] | {name, version, license}'

# View license file
cat vcpkg/ports/boost/copyright
```

### License Compatibility Matrix

```markdown
## License Compatibility

| License | Can Include | Cannot Include | Notes |
|---------|-------------|----------------|-------|
| MIT | Any | - | Very permissive |
| BSL-1.0 | Any | - | Boost Software License, permissive |
| Apache-2.0 | MIT, BSD, Apache | - | Patent grant included |
| BSD-3-Clause | Any | - | Very permissive |
| GPL-3.0 | MIT, BSD, LGPL | Proprietary | Copyleft - requires source |
| LGPL-3.0 | MIT, BSD | - | Lesser copyleft (dynamic linking OK) |
| MPL-2.0 | MIT, BSD | - | Mozilla Public License, file-level copyleft |

**Current Project License**: MIT

**Compatibility Status**:
- ✅ Compatible: boost (BSL-1.0), fmt (MIT), spdlog (MIT), nlohmann-json (MIT)
- ⚠️ Review Required: [list needing review]
- ❌ Incompatible: [list of incompatible]

**Header-Only Libraries**:
- boost (BSL-1.0) - Header-only portions
- nlohmann-json (MIT) - Header-only
- Note: Header-only libraries are compiled into your binary
```

## Phase 7: Supply Chain Security Assessment

### Package Provenance

```bash
# Conan: Verify package checksums
conan config set general.revisions_enabled=1
conan install . --verify

# vcpkg: Verify package checksums
# vcpkg automatically verifies checksums from portfile.cmake

# Example for Boost
# Check vcpkg\ports\boost\portfile.cmake:
vcpkg_download_distfile(ARCHIVE
    URLS "https://boostorg.jfrog.io/artifactory/main/release/1.81.0/source/boost_1_81_0.tar.gz"
    FILENAME "boost_1_81_0.tar.gz"
    SHA512 71feeed900fbccca04a3b4f2f84a7c217186f28a940ed8b7ed4725986baf99fa...
)

# Manual verification
sha256sum boost_1_81_0.tar.gz
# Compare with official checksum from https://www.boost.org/
```

### Repository Security

For each dependency, document:

```markdown
## Dependency: Boost

**Repository**: https://github.com/boostorg/boost
**Official Website**: https://www.boost.org/
**Maintainer**: Boost Community

**Security Posture**:
- ✅ Active maintenance (last commit: [date])
- ✅ Security policy present
- ✅ Vulnerability disclosure process
- ✅ Checksum verification (Conan/vcpkg)
- ✅ Widely used and audited (core C++ library)
- ✅ Large, active community (6k+ contributors)
- ✅ Transparent development

**Risk Assessment**: LOW
- Extremely well-established library
- Core C++ ecosystem component
- Extensive real-world testing
- Regular security reviews

**Verification Steps**:
1. Download from official Conan/vcpkg
2. Verify SHA-256 checksum
3. Compare with Boost.org checksums
4. Build from source with known-good compiler

**Alternative Options**:
- Standard Library (C++11/14/17/20/23) - Many Boost features now in STL
- Abseil (Google's C++ library)
- POCO (for networking/threading)
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

- [x] SBOM generation automated (Conan/vcpkg integration)
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
- [x] Supply chain security assessed (checksums via Conan/vcpkg)

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
   - Complete dependency tree
   - Vulnerability information
   - License data
   - Component metadata
   - Header-only library tracking

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
   - Header-only library considerations
   - Attribution requirements
   - Compliance status

3. **LICENSES/** (directory)
   - Full license texts for all dependencies

4. **DEPENDENCIES.md**
   - Dependency tree visualization
   - Direct dependencies
   - Transitive dependencies
   - Header-only libraries
   - System libraries
   - Build dependencies
   - Update recommendations

5. **SUPPLY_CHAIN.md**
   - Component provenance
   - Security assessment
   - Checksum verification (Conan/vcpkg)
   - Risk analysis
   - Alternative options
```

### Summary Report

```markdown
## SBOM Generation Summary

**Generated**: [timestamp]
**Project**: [name] v[version]
**License**: [license]
**Compiler**: GCC 11.4.0 / Clang 15.0 / MSVC 19.35
**Build System**: CMake 3.25.0
**Package Managers**: Conan 2.0 / vcpkg

**Components**:
- Total libraries: [count]
- Direct dependencies: [count]
- Header-only libraries: [count]
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
- BSL-1.0: [count]
- Apache-2.0: [count]
- BSD-3-Clause: [count]
- MPL-2.0: [count]
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

      - name: Install Conan
        run: |
          pip install conan
          conan profile detect

      - name: Install dependencies
        run: |
          conan install . --build=missing

      - name: Install CMake
        uses: jwlawson/actions-setup-cmake@v1.13
        with:
          cmake-version: '3.25.x'

      - name: Build project
        run: |
          cmake -B build -DCMAKE_BUILD_TYPE=Release
          cmake --build build

      - name: Install SBOM tools
        run: |
          pip install cyclonedx-conan
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
          pip install scancode-toolkit

      - name: Generate SBOM with CycloneDX-Conan
        run: cyclonedx-conan --output sbom.json

      - name: Scan for vulnerabilities
        run: grype sbom:./sbom.json -o json > vulnerabilities.json

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

### GitLab CI/CD

```yaml
sbom:
  stage: build
  image: conanio/gcc11
  before_script:
    - pip install cyclonedx-conan
    - curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
  script:
    - conan install . --build=missing
    - cmake -B build -DCMAKE_BUILD_TYPE=Release
    - cmake --build build
    - cyclonedx-conan --output sbom.json
    - syft packages dir:./build -o cyclonedx-json > sbom_syft.json
  artifacts:
    paths:
      - sbom.json
      - sbom_syft.json
    expire_in: 1 year
```

---

## Best Practices

1. **Use Package Managers**
   - Prefer Conan or vcpkg for dependency management
   - Automated checksum verification
   - Easier SBOM generation
   - Better version tracking

2. **Track Header-Only Libraries**
   - Document all header-only dependencies
   - Include in SBOM even though no linking occurs
   - Important for license compliance
   - Track versions carefully

3. **Keep SBOMs Current**
   - Regenerate on dependency updates
   - Track vulnerability fixes
   - Document changes between versions
   - Verify checksums regularly

4. **Use Multiple Formats**
   - CycloneDX for security
   - SPDX for license compliance
   - Both for comprehensive coverage

5. **Continuous Monitoring**
   - Monitor for new vulnerabilities (Grype, Trivy)
   - Track dependency updates (Conan/vcpkg)
   - Assess supply chain risks (checksums)
   - Subscribe to security advisories

6. **Publish Transparently**
   - Include SBOM in releases
   - Make publicly available
   - Provide easy access
   - Document update process

---

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p documentation/sbom/generated_docs
mkdir -p documentation/sbom/templates
mkdir -p documentation/sbom/assets
mkdir -p documentation/sbom/exports
```

**Save files as follows**:

- Generated docs → `documentation/sbom/generated_docs/`

- Templates → `documentation/sbom/templates/`

- Assets → `documentation/sbom/assets/`

- Exports → `documentation/sbom/exports/`

Replace `{phase_name}` with the specific phase (docstrings, comments, user_docs, technical_docs, api_docs, or sbom).

~~~

## Output Format Specifications

The SBOM should:
- Comply with NTIA minimum elements requirements
- Meet EU Cyber Resilience Act standards
- Use standard formats (CycloneDX 1.4+ or SPDX 2.3+)
- Include complete dependency tree with versions
- Document all known vulnerabilities with CVE IDs
- Provide license information for all components
- Track header-only libraries explicitly
- Assess supply chain security risks (checksums)
- Be machine-readable and automatable
- Be versioned and timestamped
- Be published alongside software releases
