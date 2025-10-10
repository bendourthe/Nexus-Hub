# C# SBOM Generation

## Objective
Generate comprehensive, standards-compliant Software Bill of Materials (SBOM) documentation that meets regulatory requirements (NTIA minimum elements, EU Cyber Resilience Act) for security, compliance, and supply chain management in C# .NET projects.

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
- [ ] Framework and runtime dependencies tracked

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
# C# SBOM Generation Request

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

Please generate a comprehensive Software Bill of Materials (SBOM) for this C# .NET project following this protocol:

## Phase 1: Dependency Discovery & Analysis

1. **Inventory Direct Dependencies**

   Analyze `.csproj` files:

   ```bash
   # List all dependencies
   dotnet list package > ${OUTPUT_DIR}/exports/dependencies.txt

   # List with transitive dependencies
   dotnet list package --include-transitive > ${OUTPUT_DIR}/exports/dependencies_full.txt

   # List outdated packages
   dotnet list package --outdated

   # List vulnerable packages
   dotnet list package --vulnerable

   # JSON format (using PowerShell)
   dotnet list package --format json > ${OUTPUT_DIR}/exports/dependencies.json
   ```

2. **Map Transitive Dependencies**

   Create complete dependency tree:

   ```bash
   # Generate dependency graph
   dotnet list package --include-transitive

   # Per project in solution
   dotnet list MySolution.sln package --include-transitive

   # Using NuGet command
   nuget list -Source https://api.nuget.org/v3/index.json

   # Export project assets (detailed)
   dotnet restore --force
   # Check obj/project.assets.json for full dependency tree
   ```

3. **Identify Dependency Metadata**

   For each dependency, collect:
   - Package name
   - Version (semver)
   - License
   - Repository URL
   - Authors/owners
   - Dependencies (for transitive mapping)
   - Package hash (SHA-512)
   - Target framework

## Phase 2: SBOM Format Selection

Choose SBOM format based on requirements:

### Option 1: SPDX (Software Package Data Exchange)
- **Standard**: ISO/IEC 5962:2021
- **Format**: JSON, YAML, RDF, Tag-Value
- **Best for**: License compliance, legal requirements
- **Tools**: Microsoft SBOM Tool, spdx-dotnet

### Option 2: CycloneDX
- **Standard**: OWASP CycloneDX
- **Format**: JSON, XML
- **Best for**: Security analysis, vulnerability management
- **Tools**: CycloneDX .NET module, Microsoft SBOM Tool

### Option 3: SWID (Software Identification Tags)
- **Standard**: ISO/IEC 19770-2:2015
- **Format**: XML
- **Best for**: IT asset management

**Recommendation**: Use CycloneDX for security focus, SPDX for license focus, or Microsoft SBOM Tool for both.

## Phase 3: Generate SBOM (CycloneDX Format)

### Using CycloneDX .NET Global Tool

```bash
# Install CycloneDX tool
dotnet tool install --global CycloneDX

# Generate SBOM for project
dotnet CycloneDX MyProject.csproj -o . -f sbom.json -j

# Generate for solution
dotnet CycloneDX MySolution.sln -o . -f sbom.json -j

# With specific options
dotnet CycloneDX MyProject.csproj \
  -o ./sbom \
  -f sbom \
  -j \
  --include-license-text false \
  --set-type application
```

### Using Microsoft SBOM Tool

```bash
# Install Microsoft SBOM Tool
dotnet tool install --global Microsoft.Sbom.DotNetTool

# Generate SBOM (SPDX format)
sbom-tool generate \
  -b ./bin/Release/net8.0 \
  -bc . \
  -pn "ProjectName" \
  -pv "1.0.0" \
  -ps "YourOrganization" \
  -nsb "https://example.com/sbom" \
  -m ./

# Generate SBOM (CycloneDX format)
sbom-tool generate \
  -b ./bin/Release/net8.0 \
  -bc . \
  -pn "ProjectName" \
  -pv "1.0.0" \
  -ps "YourOrganization" \
  -nsb "https://example.com/sbom" \
  -m ./ \
  -ManifestInfo Format=cyclonedx

# Output: _manifest/spdx_2.2/*.spdx.json
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
        "name": "CycloneDX .NET",
        "version": "3.0.0"
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
      "bom-ref": "pkg:nuget/ProjectName@1.0.0",
      "name": "ProjectName",
      "version": "1.0.0",
      "description": "Project description",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:nuget/ProjectName@1.0.0",
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
      "bom-ref": "pkg:nuget/Newtonsoft.Json@13.0.3",
      "name": "Newtonsoft.Json",
      "version": "13.0.3",
      "description": "Json.NET is a popular high-performance JSON framework for .NET",
      "hashes": [
        {
          "alg": "SHA-512",
          "content": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
        }
      ],
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:nuget/Newtonsoft.Json@13.0.3",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://www.newtonsoft.com/json"
        },
        {
          "type": "vcs",
          "url": "https://github.com/JamesNK/Newtonsoft.Json"
        },
        {
          "type": "distribution",
          "url": "https://api.nuget.org/v3-flatcontainer/newtonsoft.json/13.0.3/newtonsoft.json.13.0.3.nupkg"
        }
      ],
      "properties": [
        {
          "name": "nuget:package:type",
          "value": "Dependency"
        },
        {
          "name": "nuget:package:framework",
          "value": "net8.0"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:nuget/Microsoft.EntityFrameworkCore@8.0.0",
      "name": "Microsoft.EntityFrameworkCore",
      "version": "8.0.0",
      "description": "Entity Framework Core is a modern object-database mapper for .NET",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "purl": "pkg:nuget/Microsoft.EntityFrameworkCore@8.0.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://docs.microsoft.com/ef/core/"
        },
        {
          "type": "vcs",
          "url": "https://github.com/dotnet/efcore"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:nuget/Serilog@3.1.1",
      "name": "Serilog",
      "version": "3.1.1",
      "description": "Simple .NET logging with fully-structured events",
      "licenses": [
        {
          "license": {
            "id": "Apache-2.0"
          }
        }
      ],
      "purl": "pkg:nuget/Serilog@3.1.1"
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:nuget/ProjectName@1.0.0",
      "dependsOn": [
        "pkg:nuget/Newtonsoft.Json@13.0.3",
        "pkg:nuget/Microsoft.EntityFrameworkCore@8.0.0",
        "pkg:nuget/Serilog@3.1.1"
      ]
    },
    {
      "ref": "pkg:nuget/Microsoft.EntityFrameworkCore@8.0.0",
      "dependsOn": [
        "pkg:nuget/Microsoft.EntityFrameworkCore.Abstractions@8.0.0",
        "pkg:nuget/Microsoft.EntityFrameworkCore.Analyzers@8.0.0",
        "pkg:nuget/Microsoft.Extensions.Caching.Memory@8.0.0",
        "pkg:nuget/Microsoft.Extensions.Logging@8.0.0"
      ]
    }
  ],
  "vulnerabilities": [
    {
      "bom-ref": "vuln:nuget/Newtonsoft.Json@13.0.1:CVE-2024-21907",
      "id": "CVE-2024-21907",
      "source": {
        "name": "NVD",
        "url": "https://nvd.nist.gov/vuln/detail/CVE-2024-21907"
      },
      "ratings": [
        {
          "source": {
            "name": "NVD"
          },
          "score": 7.1,
          "severity": "high",
          "method": "CVSSv3",
          "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:H"
        }
      ],
      "cwes": [502],
      "description": "Improper Handling of Exceptional Conditions in Newtonsoft.Json",
      "recommendation": "Update to version 13.0.3 or higher",
      "affects": [
        {
          "ref": "pkg:nuget/Newtonsoft.Json@13.0.1",
          "versions": [
            {
              "version": "13.0.1",
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

### Using Microsoft SBOM Tool

```bash
# Generate SPDX 2.2 SBOM
sbom-tool generate \
  -b ./bin/Release/net8.0 \
  -bc . \
  -pn "ProjectName" \
  -pv "1.0.0" \
  -ps "YourOrganization" \
  -nsb "https://example.com/sbom/ProjectName-1.0.0" \
  -m ./

# Output: _manifest/spdx_2.2/manifest.spdx.json
```

### SPDX SBOM Template (JSON)

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "ProjectName-1.0.0",
  "documentNamespace": "https://example.com/spdxdocs/ProjectName-1.0.0-uuid",
  "creationInfo": {
    "created": "2024-01-16T10:00:00Z",
    "creators": [
      "Tool: Microsoft.Sbom.DotNetTool-1.0.0",
      "Person: Benjamin Dourthe (benjamin@adonamed.com)"
    ],
    "licenseListVersion": "3.21"
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-ProjectName",
      "name": "ProjectName",
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
          "referenceLocator": "pkg:nuget/ProjectName@1.0.0"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-Newtonsoft.Json",
      "name": "Newtonsoft.Json",
      "versionInfo": "13.0.3",
      "downloadLocation": "https://api.nuget.org/v3-flatcontainer/newtonsoft.json/13.0.3/newtonsoft.json.13.0.3.nupkg",
      "filesAnalyzed": false,
      "homepage": "https://www.newtonsoft.com/json",
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright (c) James Newton-King",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:nuget/Newtonsoft.Json@13.0.3"
        },
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:newtonsoft:json.net:13.0.3:*:*:*:*:*:*:*"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-EntityFrameworkCore",
      "name": "Microsoft.EntityFrameworkCore",
      "versionInfo": "8.0.0",
      "downloadLocation": "https://api.nuget.org/v3-flatcontainer/microsoft.entityframeworkcore/8.0.0/",
      "filesAnalyzed": false,
      "homepage": "https://docs.microsoft.com/ef/core/",
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright (c) Microsoft Corporation",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:nuget/Microsoft.EntityFrameworkCore@8.0.0"
        }
      ]
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-DOCUMENT",
      "relationshipType": "DESCRIBES",
      "relatedSpdxElement": "SPDXRef-Package-ProjectName"
    },
    {
      "spdxElementId": "SPDXRef-Package-ProjectName",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-Newtonsoft.Json"
    },
    {
      "spdxElementId": "SPDXRef-Package-ProjectName",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-EntityFrameworkCore"
    }
  ]
}
```

## Phase 5: Vulnerability Scanning

Scan for known vulnerabilities in dependencies:

### Using dotnet list package --vulnerable

```bash
# Check for vulnerable packages
dotnet list package --vulnerable

# Include transitive dependencies
dotnet list package --vulnerable --include-transitive

# Example output
Project 'MyProject' has the following vulnerable packages
   [net8.0]:
   Top-level Package      Requested   Resolved   Severity   Advisory URL
   > Newtonsoft.Json      13.0.1      13.0.1     High       https://github.com/advisories/GHSA-5crp-9r3c-p9vr

   Transitive Package     Resolved   Severity   Advisory URL
   > System.Text.Json     6.0.0      High       https://github.com/advisories/GHSA-hh2w-p6rv-4g7w
```

### Using NuGet Package Vulnerabilities

```bash
# Enable vulnerability warnings in .csproj
<PropertyGroup>
  <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  <WarningsAsErrors>NU1900;NU1901;NU1902;NU1903;NU1904</WarningsAsErrors>
</PropertyGroup>

# Restore with vulnerability check
dotnet restore --force

# Build with vulnerability check
dotnet build /p:TreatWarningsAsErrors=true
```

### Using OWASP Dependency-Check

```bash
# Install Dependency-Check
# Download from: https://github.com/jeremylong/DependencyCheck

# Run scan
dependency-check --project "ProjectName" \
  --scan "./bin/Release/net8.0" \
  --format JSON \
  --out ./dependency-check-report

# PowerShell
.\dependency-check.bat `
  --project "ProjectName" `
  --scan ".\bin\Release\net8.0" `
  --format JSON `
  --out .\dependency-check-report
```

### Using Snyk

```bash
# Install Snyk CLI
npm install -g snyk

# Authenticate
snyk auth

# Test .NET project
snyk test --file=MyProject.csproj --json > ${OUTPUT_DIR}/exports/snyk_report.json

# Monitor project
snyk monitor --file=MyProject.csproj
```

### Using Trivy

```bash
# Install Trivy
# See: https://aquasecurity.github.io/trivy/

# Scan .NET project
trivy fs --format json --output ${OUTPUT_DIR}/exports/trivy_report.json .

# Scan specific DLL
trivy fs --scanners vuln bin/Release/net8.0/MyProject.dll
```

## Phase 6: License Analysis

### Using dotnet-project-licenses

```bash
# Install tool
dotnet tool install --global dotnet-project-licenses

# Generate license report
dotnet-project-licenses -i . -o -f json > ${OUTPUT_DIR}/exports/licenses.json

# Generate markdown report
dotnet-project-licenses -i . -o -f markdown > ${OUTPUT_DIR}/exports/LICENSES.md

# Generate HTML report
dotnet-project-licenses -i . -o -f html > ${OUTPUT_DIR}/exports/licenses.html

# Example JSON output
[
  {
    "PackageName": "Newtonsoft.Json",
    "PackageVersion": "13.0.3",
    "PackageUrl": "https://www.newtonsoft.com/json",
    "License": "MIT",
    "LicenseUrl": "https://licenses.nuget.org/MIT"
  },
  {
    "PackageName": "Microsoft.EntityFrameworkCore",
    "PackageVersion": "8.0.0",
    "PackageUrl": "https://docs.microsoft.com/ef/core/",
    "License": "MIT",
    "LicenseUrl": "https://licenses.nuget.org/MIT"
  }
]
```

### Using NuGet License Analysis

```bash
# Query package license from NuGet
nuget list Newtonsoft.Json -Verbosity detailed

# Using dotnet CLI
dotnet add package Newtonsoft.Json
# Check .nuspec file in packages folder for license info
```

### License Compatibility Matrix

Document license compatibility:

```markdown
## License Compatibility

| License | Can Include | Cannot Include | Notes |
|---------|-------------|----------------|-------|
| MIT | Any | - | Very permissive |
| Apache-2.0 | MIT, BSD, Apache | - | Patent grant included |
| BSD-3-Clause | Any | - | Very permissive |
| MS-PL | MIT, BSD | GPL | Microsoft Public License |
| GPL-3.0 | MIT, BSD | Proprietary | Copyleft - requires source |
| LGPL-3.0 | MIT, BSD | - | Lesser copyleft |
| Proprietary | ? | GPL, AGPL | Check license terms |

**Current Project License**: MIT

**Compatibility Status**:
- ✅ Compatible: Newtonsoft.Json (MIT), EF Core (MIT), Serilog (Apache-2.0)
- ⚠️ Review Required: [list needing review]
- ❌ Incompatible: [list of incompatible]
```

## Phase 7: Supply Chain Security Assessment

### Package Provenance

```bash
# Verify package signatures
dotnet nuget verify MyPackage.1.0.0.nupkg

# Enable package signature verification in nuget.config
<configuration>
  <config>
    <add key="signatureValidationMode" value="require" />
  </config>
  <trustedSigners>
    <repository name="nuget.org" serviceIndex="https://api.nuget.org/v3/index.json">
      <certificate fingerprint="0E5F38F57DC1BCC806D8494F4F90FBCEDD988B46760709CBEEC6F4219AA6157D"
                   hashAlgorithm="SHA256"
                   allowUntrustedRoot="false" />
    </repository>
  </trustedSigners>
</configuration>

# Lock file for reproducible builds
dotnet restore --use-lock-file
# This generates packages.lock.json
```

### Repository Security

For each dependency, document:

```markdown
## Dependency: Newtonsoft.Json

**Repository**: https://github.com/JamesNK/Newtonsoft.Json
**Package Registry**: NuGet.org
**Maintainer**: James Newton-King

**Security Posture**:
- ✅ Active maintenance (last commit: [date])
- ✅ Security policy present
- ✅ Vulnerability disclosure process
- ✅ Package signing enabled
- ✅ Recent security audit
- ✅ Large, active community (10k+ stars)
- ✅ Trusted by Microsoft ecosystem

**Risk Assessment**: LOW
- Well-maintained, widely-used library
- Active security response
- Regular updates and patches
- Strong community oversight

**Alternative Options**:
- System.Text.Json (built-in .NET)
- Utf8Json (high performance)
- Jil (fast serializer)
```

## Phase 8: Compliance Documentation

### NTIA Minimum Elements Compliance

```markdown
# NTIA SBOM Compliance Checklist

## Minimum Elements

- [x] **Supplier Name**: All suppliers identified in SBOM
- [x] **Component Name**: All components named (NuGet package names)
- [x] **Version**: All versions specified (semver)
- [x] **Other Unique Identifiers**: PURL and CPE provided for all
- [x] **Dependency Relationships**: Complete dependency tree
- [x] **Author of SBOM Data**: [Benjamin Dourthe]
- [x] **Timestamp**: [2024-01-16T10:00:00Z]

## Automation Supportability

- [x] SBOM in machine-readable format (CycloneDX/SPDX JSON)
- [x] Consistent data format across components
- [x] Unique identifiers (PURL) for all components
- [x] Dependency relationships machine-parseable

## Practices and Processes

- [x] SBOM generation automated in CI/CD
- [x] SBOM updated with each release
- [x] SBOM published alongside releases
- [x] Vulnerability scanning integrated (dotnet list package --vulnerable)

**Compliance Status**: ✅ COMPLIANT
```

### EU Cyber Resilience Act Compliance

```markdown
# EU CRA Compliance Checklist

## Essential Requirements

- [x] Complete SBOM with all components
- [x] Known vulnerabilities identified (CVE tracking via NuGet)
- [x] Security updates and patches tracked
- [x] Vulnerability disclosure timeline documented
- [x] Supply chain security assessed

## Documentation Requirements

- [x] SBOM in standardized format (CycloneDX/SPDX)
- [x] Vulnerability report attached (dotnet list package)
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
   - All known CVEs (from dotnet list package)
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
   - Framework dependencies
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
**Framework**: .NET 8.0

**Components**:
- Total components: [count]
- Direct dependencies: [count]
- Transitive dependencies: [count]
- Unique licenses: [count]

**Vulnerabilities** (dotnet list package):
- Critical: [count]
- High: [count]
- Moderate: [count]
- Low: [count]
- Total: [count]

**License Distribution**:
- MIT: [count]
- Apache-2.0: [count]
- MS-PL: [count]
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
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '8.0.x'

      - name: Restore dependencies
        run: dotnet restore

      - name: Build project
        run: dotnet build --configuration Release --no-restore

      - name: Install SBOM tools
        run: |
          dotnet tool install --global CycloneDX
          dotnet tool install --global Microsoft.Sbom.DotNetTool

      - name: Generate CycloneDX SBOM
        run: dotnet CycloneDX MyProject.csproj -o . -f sbom.json -j

      - name: Check for vulnerabilities
        run: dotnet list package --vulnerable --include-transitive > ${OUTPUT_DIR}/exports/vulnerabilities.txt

      - name: Upload SBOM artifacts
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: |
            sbom.json
            vulnerabilities.txt

      - name: Attach to release
        if: github.event_name == 'release'
        uses: softprops/action-gh-release@v1
        with:
          files: sbom.json
```

### Azure DevOps Pipeline

```yaml
trigger:
  - main

pool:
  vmImage: 'windows-latest'

steps:
- task: UseDotNet@2
  inputs:
    version: '8.0.x'

- task: DotNetCoreCLI@2
  displayName: 'Restore'
  inputs:
    command: 'restore'

- task: DotNetCoreCLI@2
  displayName: 'Build'
  inputs:
    command: 'build'
    arguments: '--configuration Release'

- task: PowerShell@2
  displayName: 'Install SBOM tools'
  inputs:
    targetType: 'inline'
    script: |
      dotnet tool install --global CycloneDX
      dotnet tool install --global Microsoft.Sbom.DotNetTool

- task: PowerShell@2
  displayName: 'Generate SBOM'
  inputs:
    targetType: 'inline'
    script: |
      dotnet CycloneDX MyProject.csproj -o $(Build.ArtifactStagingDirectory) -f sbom.json -j

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: '$(Build.ArtifactStagingDirectory)'
    artifactName: 'sbom'
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
   - Track vulnerability fixes
   - Document changes between versions
   - Run dotnet list package --vulnerable regularly

3. **Use Multiple Formats**
   - CycloneDX for security
   - SPDX for license compliance
   - Both for comprehensive coverage
   - Microsoft SBOM Tool supports both

4. **Continuous Monitoring**
   - Monitor for new vulnerabilities (dotnet list package)
   - Track dependency updates (Dependabot)
   - Assess supply chain risks
   - Enable NuGet package signing verification

5. **Publish Transparently**
   - Include SBOM in releases
   - Make publicly available
   - Provide easy access
   - Document update process

---

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/sbom/generated_docs
mkdir -p ${OUTPUT_DIR}/sbom/templates
mkdir -p ${OUTPUT_DIR}/sbom/assets
mkdir -p ${OUTPUT_DIR}/sbom/exports
```

**Save files as follows**:


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
- Assess supply chain security risks
- Be machine-readable and automatable
- Be versioned and timestamped
- Be published alongside software releases
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
