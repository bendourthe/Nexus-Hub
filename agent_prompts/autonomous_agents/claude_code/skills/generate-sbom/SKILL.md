---
name: generate-sbom
description: Generate Software Bill of Materials (SBOM) documenting all components, dependencies, licenses, and vulnerabilities for compliance and security
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language (Python, JavaScript, Java, C#, Go, C, C++)
category: Documentation
priority: MEDIUM
tags: [sbom, compliance, security, dependencies, licenses, vulnerabilities, cyclonedx, spdx, supply-chain]
template_sources:
  - documentation/sbom/python_sbom.md
  - documentation/sbom/javascript_sbom.md
  - documentation/sbom/java_sbom.md
  - documentation/sbom/csharp_sbom.md
  - documentation/sbom/go_sbom.md
  - documentation/sbom/c_sbom.md
  - documentation/sbom/cpp_sbom.md
---

# Generate Software Bill of Materials (SBOM)

Generate comprehensive, standards-compliant SBOM documentation that inventories all software components, dependencies, versions, licenses, and known vulnerabilities for security, compliance, and supply chain management.

## When to Use This Skill

Use this skill when you need to:
- Meet regulatory compliance (NTIA, EU Cyber Resilience Act)
- Document software supply chain
- Track dependencies and versions
- Identify license compliance issues
- Audit security vulnerabilities
- Prepare for security assessments
- Support procurement processes
- Enable vulnerability management
- Satisfy customer security requirements
- Maintain software inventory

## What This Skill Does

This skill generates comprehensive SBOM documentation:

### For All Languages
1. **SBOM Generation**
   - Complete dependency tree
   - Component identification (name, version, supplier)
   - License information
   - Checksums and hashes
   - PURL (Package URL) identifiers
   - CPE (Common Platform Enumeration)
   - Relationship mapping

2. **Compliance Standards**
   - **NTIA Minimum Elements**: Required baseline fields
   - **EU Cyber Resilience Act**: CRA-specific requirements
   - **SPDX Format**: Software Package Data Exchange
   - **CycloneDX Format**: Lightweight SBOM standard
   - **SWID Tags**: Software Identification Tags

3. **Security Analysis**
   - CVE (Common Vulnerabilities and Exposures) tracking
   - CVSS scores and severity ratings
   - Known vulnerability identification
   - Security advisory references
   - Patch availability information
   - Exploit maturity assessment

4. **License Compliance**
   - License identification (SPDX identifiers)
   - License compatibility analysis
   - Copyleft obligations
   - Attribution requirements
   - Commercial use restrictions
   - License conflict detection

5. **Supply Chain Security**
   - Component provenance
   - Supplier information
   - Repository sources
   - Build tool information
   - Dependency integrity verification
   - Transitive dependency tracking

6. **SBOM Maintenance**
   - Automated generation in CI/CD
   - Version tracking over time
   - Change detection and reporting
   - SBOM comparison tools
   - Continuous monitoring integration

### Language-Specific Features

#### Python
- **Tools**: CycloneDX Python, pip-licenses, pip-audit
- **Formats**: CycloneDX, SPDX, JSON
- **Package Managers**: pip, poetry, conda
- **Examples**:
  ```bash
  # Install tools
  pip install cyclonedx-bom pip-licenses pip-audit

  # Generate CycloneDX SBOM
  cyclonedx-py -r -o sbom.xml

  # Generate SPDX SBOM
  pip install spdx-tools
  pip-licenses --format=json --output-file=licenses.json

  # Audit for vulnerabilities
  pip-audit --format=json --output=vulnerabilities.json

  # Generate comprehensive SBOM
  cyclonedx-py -r --format=json -o sbom.json \
    --license-file-location . \
    --package-version $(python setup.py --version)
  ```

  **CycloneDX Output Structure:**
  ```json
  {
    "bomFormat": "CycloneDX",
    "specVersion": "1.4",
    "version": 1,
    "metadata": {
      "timestamp": "2024-10-21T10:00:00Z",
      "tools": [{
        "vendor": "CycloneDX",
        "name": "cyclonedx-python",
        "version": "3.11.0"
      }],
      "component": {
        "type": "application",
        "name": "myproject",
        "version": "1.0.0"
      }
    },
    "components": [
      {
        "type": "library",
        "name": "requests",
        "version": "2.31.0",
        "purl": "pkg:pypi/requests@2.31.0",
        "licenses": [{"license": {"id": "Apache-2.0"}}],
        "hashes": [{
          "alg": "SHA-256",
          "content": "..."
        }]
      }
    ]
  }
  ```

#### JavaScript/TypeScript
- **Tools**: CycloneDX Node.js, npm-audit, snyk
- **Formats**: CycloneDX, SPDX, JSON
- **Package Managers**: npm, yarn, pnpm
- **Examples**:
  ```bash
  # Install tools
  npm install -g @cyclonedx/cyclonedx-npm

  # Generate CycloneDX SBOM
  cyclonedx-npm --output-file sbom.xml

  # Generate JSON format
  cyclonedx-npm --output-format json --output-file sbom.json

  # Audit for vulnerabilities
  npm audit --json > npm-audit.json

  # Using Yarn
  yarn audit --json > yarn-audit.json

  # Generate with metadata
  cyclonedx-npm \
    --output-format json \
    --output-file sbom.json \
    --include-dev false \
    --include-optional false \
    --validate
  ```

  **Package.json Integration:**
  ```json
  {
    "scripts": {
      "sbom:generate": "cyclonedx-npm --output-file sbom.xml",
      "sbom:audit": "npm audit --json > audit.json",
      "sbom:validate": "cyclonedx validate --input-file sbom.xml"
    }
  }
  ```

#### Java
- **Tools**: CycloneDX Maven/Gradle, OWASP Dependency-Check
- **Formats**: CycloneDX, SPDX, XML/JSON
- **Build Tools**: Maven, Gradle
- **Examples**:

  **Maven Configuration (pom.xml):**
  ```xml
  <plugin>
    <groupId>org.cyclonedx</groupId>
    <artifactId>cyclonedx-maven-plugin</artifactId>
    <version>2.7.9</version>
    <executions>
      <execution>
        <phase>package</phase>
        <goals>
          <goal>makeAggregateBom</goal>
        </goals>
      </execution>
    </executions>
    <configuration>
      <outputFormat>json</outputFormat>
      <outputName>sbom</outputName>
      <includeBomSerialNumber>true</includeBomSerialNumber>
      <includeCompileScope>true</includeCompileScope>
      <includeProvidedScope>true</includeProvidedScope>
      <includeRuntimeScope>true</includeRuntimeScope>
      <includeSystemScope>true</includeSystemScope>
      <includeTestScope>false</includeTestScope>
      <includeLicenseText>false</includeLicenseText>
    </configuration>
  </plugin>
  ```

  ```bash
  # Generate SBOM
  mvn cyclonedx:makeAggregateBom

  # Output: target/sbom.json
  ```

  **Gradle Configuration (build.gradle):**
  ```gradle
  plugins {
      id 'org.cyclonedx.bom' version '1.7.4'
  }

  cyclonedxBom {
      includeConfigs = ['runtimeClasspath']
      skipConfigs = ['testRuntimeClasspath']
      outputFormat = 'json'
      outputName = 'sbom'
      includeBomSerialNumber = true
  }
  ```

  ```bash
  # Generate SBOM
  gradle cyclonedxBom

  # Output: build/reports/sbom.json
  ```

#### C#
- **Tools**: CycloneDX .NET, dotnet list package
- **Formats**: CycloneDX, SPDX, XML/JSON
- **Build Tools**: dotnet CLI, NuGet
- **Examples**:
  ```bash
  # Install tool
  dotnet tool install --global CycloneDX

  # Generate SBOM
  dotnet CycloneDX <path-to-solution.sln> \
    -o sbom.xml \
    -f xml

  # Generate JSON format
  dotnet CycloneDX <path-to-solution.sln> \
    -o sbom.json \
    -f json

  # List all packages with versions
  dotnet list package --include-transitive > packages.txt

  # Check for vulnerabilities
  dotnet list package --vulnerable --include-transitive
  ```

  **Project File Integration (.csproj):**
  ```xml
  <Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
      <GenerateSBOM>true</GenerateSBOM>
      <SBOMOutputPath>$(OutputPath)sbom.json</SBOMOutputPath>
    </PropertyGroup>
  </Project>
  ```

  **CI/CD Integration:**
  ```yaml
  - name: Generate SBOM
    run: dotnet CycloneDX MyApp.sln -o sbom.json -f json
  - name: Upload SBOM
    uses: actions/upload-artifact@v3
    with:
      name: sbom
      path: sbom.json
  ```

#### Go
- **Tools**: CycloneDX Go, go-licenses, govulncheck
- **Formats**: CycloneDX, SPDX, JSON
- **Package Manager**: go modules
- **Examples**:
  ```bash
  # Install tools
  go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest

  # Generate SBOM
  cyclonedx-gomod app -json -output sbom.json

  # Include module graph
  cyclonedx-gomod app -json -output sbom.json -module-graph

  # License information
  go install github.com/google/go-licenses@latest
  go-licenses report ./... --template licenses.tpl > licenses.md

  # Vulnerability check
  go install golang.org/x/vuln/cmd/govulncheck@latest
  govulncheck ./...

  # Generate with version info
  VERSION=$(git describe --tags --always)
  cyclonedx-gomod app \
    -json \
    -output sbom.json \
    -version $VERSION \
    -main-component-name myapp \
    -main-component-version $VERSION
  ```

  **Makefile Integration:**
  ```makefile
  .PHONY: sbom
  sbom:
  	cyclonedx-gomod app -json -output sbom.json
  	govulncheck -json ./... > vulnerabilities.json
  	go-licenses report ./... > licenses.md
  ```

#### C
- **Tools**: syft, SPDX tools, scancode-toolkit
- **Formats**: SPDX, CycloneDX
- **Build Systems**: Make, CMake, Autotools
- **Examples**:
  ```bash
  # Install syft (multi-language SBOM tool)
  curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh

  # Generate SBOM from source
  syft dir:. -o spdx-json=sbom.spdx.json

  # Generate CycloneDX format
  syft dir:. -o cyclonedx-json=sbom.cyclonedx.json

  # Scan with ScanCode for licenses
  pip install scancode-toolkit
  scancode --license --copyright --json-pp sbom-scan.json .

  # Manual SBOM creation for C library
  cat > sbom.spdx << 'EOF'
  SPDXVersion: SPDX-2.3
  DataLicense: CC0-1.0
  SPDXID: SPDXRef-DOCUMENT
  DocumentName: mylib
  DocumentNamespace: https://example.com/mylib/1.0.0
  Creator: Tool: manual

  PackageName: mylib
  SPDXID: SPDXRef-Package
  PackageVersion: 1.0.0
  PackageDownloadLocation: https://github.com/user/mylib
  FilesAnalyzed: false
  PackageLicenseConcluded: MIT
  PackageLicenseDeclared: MIT
  PackageCopyrightText: Copyright 2024 Author Name

  PackageName: openssl
  SPDXID: SPDXRef-openssl
  PackageVersion: 3.0.0
  ExternalRef: SECURITY cpe23Type cpe:2.3:a:openssl:openssl:3.0.0:*
  PackageLicenseConcluded: Apache-2.0
  EOF
  ```

  **CMake Integration:**
  ```cmake
  # Generate SBOM as part of build
  add_custom_target(sbom
      COMMAND syft dir:${CMAKE_SOURCE_DIR} -o cyclonedx-json=sbom.json
      WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
      COMMENT "Generating SBOM"
  )
  ```

#### C++
- **Tools**: syft, conan sbom, vcpkg export
- **Formats**: SPDX, CycloneDX
- **Build Systems**: CMake, Conan, vcpkg
- **Examples**:
  ```bash
  # Using syft
  syft dir:. -o spdx-json=sbom.spdx.json
  syft dir:. -o cyclonedx-json=sbom.cyclonedx.json

  # Using Conan
  conan install . --install-folder=build
  conan info . --json > conan-dependencies.json

  # Using vcpkg
  vcpkg export --raw --output=dependencies/ pkg1 pkg2
  vcpkg list --x-json > vcpkg-dependencies.json

  # Manual dependency tracking
  cat > dependencies.txt << 'EOF'
  boost@1.81.0 (BSL-1.0)
  openssl@3.0.0 (Apache-2.0)
  zlib@1.2.13 (Zlib)
  fmt@9.1.0 (MIT)
  EOF

  # Generate comprehensive SBOM
  syft packages dir:. \
    -o spdx-json=sbom.spdx.json \
    --source-name myproject \
    --source-version 1.0.0
  ```

  **CMake + Conan Integration:**
  ```cmake
  # CMakeLists.txt
  set(CONAN_SBOM_OUTPUT ${CMAKE_BINARY_DIR}/sbom.json)

  add_custom_target(generate-sbom
      COMMAND ${CONAN_COMMAND} info ${CMAKE_SOURCE_DIR} --json > ${CONAN_SBOM_OUTPUT}
      COMMAND syft dir:${CMAKE_SOURCE_DIR} -o cyclonedx-json=${CMAKE_BINARY_DIR}/sbom-full.json
      COMMENT "Generating SBOM from dependencies"
  )
  ```

## Prerequisites

- Completed or stable software project
- Dependency manifest files (requirements.txt, package.json, pom.xml, etc.)
- Build environment configured
- Understanding of license requirements
- Access to vulnerability databases (optional)
- CI/CD integration capability (optional)

## Instructions

### Step 1: Understand SBOM Requirements

1. **Regulatory Compliance**:
   - **NTIA Minimum Elements**: Baseline SBOM requirements
   - **EU Cyber Resilience Act**: CRA compliance
   - **NIST SP 800-161**: Supply chain risk management
   - **Executive Order 14028**: US federal requirements

2. **SBOM Format Selection**:
   - **CycloneDX**: Lightweight, security-focused, widely supported
   - **SPDX**: Comprehensive, license-focused, Linux Foundation standard
   - **SWID**: Software identification, ISO/IEC 19770-2 standard

3. **NTIA Minimum Elements**:
   - Supplier name
   - Component name
   - Version of component
   - Other unique identifiers (PURL, CPE)
   - Dependency relationship
   - Author of SBOM data
   - Timestamp

### Step 2: Invoke the Generate SBOM Skill

For **Python** projects:
```
"Use the generate-sbom skill to create comprehensive SBOM for Python project.

Language: Python
Package Manager: pip / poetry / conda
Format: CycloneDX / SPDX
Compliance: NTIA minimum elements / EU CRA
Include:
- All dependencies (direct and transitive)
- License information
- CVE vulnerability scanning
- Component hashes
- PURL identifiers
Output: sbom.json, vulnerabilities.json, licenses.txt
Automation: GitHub Actions workflow"
```

For **JavaScript/TypeScript** projects:
```
"Use the generate-sbom skill for JavaScript/TypeScript SBOM.

Language: JavaScript / TypeScript
Package Manager: npm / yarn / pnpm
Format: CycloneDX / SPDX
Compliance: NTIA minimum elements
Include:
- Production dependencies only
- License compatibility check
- npm audit results
- Package integrity hashes
- Security advisories
Output: sbom.json, audit.json
Automation: npm script + CI/CD"
```

For **Java** projects:
```
"Use the generate-sbom skill for Java project SBOM.

Language: Java
Build Tool: Maven / Gradle
Format: CycloneDX / SPDX
Compliance: NTIA + EU CRA
Include:
- Compile and runtime dependencies
- License information
- OWASP dependency check
- CVE tracking
- Component metadata
Output: target/sbom.json, dependency-check-report.html
Automation: Maven/Gradle plugin"
```

For **C#** projects:
```
"Use the generate-sbom skill for .NET SBOM generation.

Language: C#
Build Tool: dotnet CLI
Framework: .NET 6+ / .NET Framework
Format: CycloneDX / SPDX
Compliance: NTIA minimum elements
Include:
- NuGet dependencies (direct + transitive)
- License information
- Vulnerability check
- Package signatures
- Framework dependencies
Output: sbom.json, vulnerabilities.txt
Automation: dotnet tool + Azure DevOps"
```

For **Go** projects:
```
"Use the generate-sbom skill for Go module SBOM.

Language: Go
Package Manager: go modules
Format: CycloneDX / SPDX
Compliance: NTIA requirements
Include:
- go.mod dependencies
- Indirect dependencies
- License information
- govulncheck results
- Module checksums
Output: sbom.json, vulnerabilities.json, licenses.md
Automation: Makefile + CI/CD"
```

For **C/C++** projects:
```
"Use the generate-sbom skill for C/C++ project SBOM.

Language: C / C++
Build System: CMake / Make / Conan / vcpkg
Format: SPDX / CycloneDX
Compliance: NTIA minimum elements
Include:
- System libraries
- Third-party dependencies
- Build tool versions
- License information
- Manual component entries
Output: sbom.spdx.json, dependencies.txt
Automation: Build system integration"
```

### Step 3: Set Up SBOM Generation Tools

#### Install Tools by Language

**Python:**
```bash
pip install cyclonedx-bom pip-licenses pip-audit
```

**JavaScript:**
```bash
npm install -g @cyclonedx/cyclonedx-npm
```

**Java (Maven):**
```xml
<!-- Add to pom.xml -->
<plugin>
  <groupId>org.cyclonedx</groupId>
  <artifactId>cyclonedx-maven-plugin</artifactId>
  <version>2.7.9</version>
</plugin>
```

**C# (.NET):**
```bash
dotnet tool install --global CycloneDX
```

**Go:**
```bash
go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest
```

**C/C++ (Universal):**
```bash
# Install syft (works for all languages)
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh
```

### Step 4: Generate SBOM

#### Automated Generation

**Python:**
```bash
# Generate CycloneDX SBOM
cyclonedx-py -r --format json -o sbom.json

# Check vulnerabilities
pip-audit --format json --output vulnerabilities.json

# Extract licenses
pip-licenses --format json --output-file licenses.json
```

**JavaScript:**
```bash
# Generate SBOM
cyclonedx-npm --output-format json --output-file sbom.json

# Audit vulnerabilities
npm audit --json > audit.json
```

**Java (Maven):**
```bash
mvn cyclonedx:makeAggregateBom
# Output: target/sbom.json
```

**C# (.NET):**
```bash
dotnet CycloneDX MySolution.sln -o sbom.json -f json
dotnet list package --vulnerable --include-transitive
```

**Go:**
```bash
cyclonedx-gomod app -json -output sbom.json
govulncheck -json ./... > vulnerabilities.json
```

**C/C++ (syft):**
```bash
syft dir:. -o cyclonedx-json=sbom.json
syft dir:. -o spdx-json=sbom.spdx.json
```

### Step 5: Validate and Enrich SBOM

#### Validate SBOM Format

```bash
# Install CycloneDX CLI
npm install -g @cyclonedx/cyclonedx-cli

# Validate SBOM
cyclonedx validate --input-file sbom.xml
cyclonedx validate --input-file sbom.json --input-format json
```

#### Enrich SBOM with Additional Data

**Add Vulnerability Data:**
```bash
# Using grype (vulnerability scanner)
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh
grype sbom:sbom.json -o json > vulnerabilities-grype.json
```

**Add License Analysis:**
```bash
# Using licensee (GitHub's license detection)
gem install licensee
licensee detect --json > license-analysis.json
```

**Add Component Metadata:**
```bash
# Merge multiple SBOM sources
cyclonedx merge --input-files sbom1.json sbom2.json --output-file merged-sbom.json
```

### Step 6: Integrate SBOM Generation in CI/CD

#### GitHub Actions Example

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
          pip install cyclonedx-bom pip-audit

      - name: Generate SBOM
        run: |
          cyclonedx-py -r --format json -o sbom.json
          pip-audit --format json --output vulnerabilities.json

      - name: Validate SBOM
        run: |
          npm install -g @cyclonedx/cyclonedx-cli
          cyclonedx validate --input-file sbom.json --input-format json

      - name: Upload SBOM
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: |
            sbom.json
            vulnerabilities.json

      - name: Publish SBOM to Release
        if: github.event_name == 'release'
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ github.event.release.upload_url }}
          asset_path: ./sbom.json
          asset_name: sbom.json
          asset_content_type: application/json
```

#### GitLab CI Example

```yaml
generate-sbom:
  stage: build
  image: python:3.11
  script:
    - pip install cyclonedx-bom pip-audit
    - cyclonedx-py -r --format json -o sbom.json
    - pip-audit --format json --output vulnerabilities.json
  artifacts:
    paths:
      - sbom.json
      - vulnerabilities.json
    expire_in: 1 year
  only:
    - main
    - tags
```

#### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    stages {
        stage('Generate SBOM') {
            steps {
                sh '''
                    pip install cyclonedx-bom pip-audit
                    cyclonedx-py -r --format json -o sbom.json
                    pip-audit --format json --output vulnerabilities.json
                '''
            }
        }
        stage('Archive SBOM') {
            steps {
                archiveArtifacts artifacts: 'sbom.json,vulnerabilities.json', fingerprint: true
            }
        }
    }
}
```

### Step 7: Monitor and Update SBOM

#### Continuous Monitoring

**Set up automated vulnerability scanning:**
```bash
# Schedule regular vulnerability checks
# Crontab entry for daily scan
0 2 * * * cd /path/to/project && pip-audit --format json > vulnerabilities.json && mail -s "Vulnerability Report" team@example.com < vulnerabilities.json
```

**Track SBOM changes:**
```bash
# Compare SBOMs between versions
cyclonedx diff --from sbom-v1.0.0.json --to sbom-v1.1.0.json
```

**Automate SBOM updates:**
```yaml
# Dependabot configuration (.github/dependabot.yml)
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    # Automatically regenerate SBOM on dependency updates
```

## SBOM Format Examples

### CycloneDX Format (JSON)

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
  "version": 1,
  "metadata": {
    "timestamp": "2024-10-21T10:00:00Z",
    "tools": [
      {
        "vendor": "CycloneDX",
        "name": "cyclonedx-python-lib",
        "version": "3.1.5"
      }
    ],
    "component": {
      "type": "application",
      "bom-ref": "myproject@1.0.0",
      "name": "myproject",
      "version": "1.0.0",
      "description": "My awesome project",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
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
      "description": "Python HTTP library",
      "purl": "pkg:pypi/requests@2.31.0",
      "licenses": [
        {
          "license": {
            "id": "Apache-2.0"
          }
        }
      ],
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "942c5a758f98d790eaed1a29cb6eefc7ffb0d1cf7af05c3d2791656dbd6ad1e1"
        }
      ],
      "externalReferences": [
        {
          "type": "website",
          "url": "https://requests.readthedocs.io"
        },
        {
          "type": "vcs",
          "url": "https://github.com/psf/requests"
        }
      ]
    }
  ],
  "dependencies": [
    {
      "ref": "myproject@1.0.0",
      "dependsOn": [
        "pkg:pypi/requests@2.31.0"
      ]
    }
  ],
  "vulnerabilities": [
    {
      "bom-ref": "vuln-requests-CVE-2023-32681",
      "id": "CVE-2023-32681",
      "source": {
        "name": "NVD",
        "url": "https://nvd.nist.gov/vuln/detail/CVE-2023-32681"
      },
      "ratings": [
        {
          "score": 6.1,
          "severity": "medium",
          "method": "CVSSv3",
          "vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:C/C:N/I:H/A:N"
        }
      ],
      "cwes": [113],
      "description": "Unintended proxy behavior in requests",
      "recommendation": "Update to requests 2.31.0 or later",
      "affects": [
        {
          "ref": "pkg:pypi/requests@2.30.0"
        }
      ]
    }
  ]
}
```

### SPDX Format (JSON)

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "myproject-1.0.0",
  "documentNamespace": "https://example.com/myproject/1.0.0/sbom.spdx.json",
  "creationInfo": {
    "created": "2024-10-21T10:00:00Z",
    "creators": [
      "Tool: cyclonedx-python-3.1.5"
    ],
    "licenseListVersion": "3.21"
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-myproject",
      "name": "myproject",
      "versionInfo": "1.0.0",
      "downloadLocation": "https://github.com/user/myproject",
      "filesAnalyzed": false,
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright 2024 Author Name"
    },
    {
      "SPDXID": "SPDXRef-Package-requests",
      "name": "requests",
      "versionInfo": "2.31.0",
      "downloadLocation": "https://pypi.org/project/requests/2.31.0",
      "filesAnalyzed": false,
      "licenseConcluded": "Apache-2.0",
      "licenseDeclared": "Apache-2.0",
      "copyrightText": "NOASSERTION",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:pypi/requests@2.31.0"
        },
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:python:requests:2.31.0:*:*:*:*:*:*:*"
        }
      ],
      "checksums": [
        {
          "algorithm": "SHA256",
          "checksumValue": "942c5a758f98d790eaed1a29cb6eefc7ffb0d1cf7af05c3d2791656dbd6ad1e1"
        }
      ]
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-Package-myproject",
      "relationshipType": "DEPENDS_ON",
      "relatedSpdxElement": "SPDXRef-Package-requests"
    }
  ]
}
```

## Quality Checklist

Before finalizing SBOM, verify:

- [ ] All NTIA minimum elements present
- [ ] EU CRA requirements met (if applicable)
- [ ] All dependencies included (direct + transitive)
- [ ] License information complete
- [ ] Version numbers accurate
- [ ] Component hashes/checksums included
- [ ] PURL identifiers for all components
- [ ] Vulnerability data included
- [ ] Supplier information present
- [ ] Timestamp and tool information
- [ ] Dependency relationships mapped
- [ ] SBOM validates against schema
- [ ] Format is standards-compliant
- [ ] CI/CD integration working
- [ ] SBOM versioned with software releases

## Common Issues and Solutions

### Issue: Missing Transitive Dependencies
**Solution**:
- Use tools that automatically detect transitive deps
- For Python: `cyclonedx-py -r` (recursive)
- For JavaScript: ensure dev dependencies excluded if needed
- For Java: use aggregate BOM in Maven
- Manually verify dependency tree

### Issue: License Information Incomplete
**Solution**:
- Use dedicated license detection tools
- Check project metadata files (LICENSE, README)
- Manual review for ambiguous licenses
- Use SPDX license identifiers
- Document license conflicts

### Issue: SBOM Too Large
**Solution**:
- Exclude test/dev dependencies
- Use compression (gzip)
- Split into multiple SBOMs (layers)
- Remove redundant metadata
- Focus on production dependencies

### Issue: Vulnerability Data Outdated
**Solution**:
- Regenerate SBOM regularly (CI/CD)
- Use real-time vulnerability scanning
- Subscribe to security advisories
- Automate dependency updates (Dependabot)
- Monitor CVE databases

## Success Criteria

After using this skill, you should have:

- [ ] Complete SBOM in standard format (CycloneDX/SPDX)
- [ ] All NTIA minimum elements included
- [ ] EU CRA compliance (if required)
- [ ] Comprehensive dependency inventory
- [ ] License compliance documentation
- [ ] Vulnerability assessment
- [ ] SBOM validation passed
- [ ] CI/CD integration automated
- [ ] SBOM versioned with releases
- [ ] Monitoring and update process
- [ ] Team trained on SBOM maintenance
- [ ] Compliance requirements satisfied

## Related Skills

- `dependency-security-audit`: Audit dependencies for vulnerabilities
- `generate-api-docs`: Document APIs
- `create-technical-docs`: Architecture documentation
- `code-review-security`: Security code review

## Tools and Resources

### SBOM Generation Tools
- **CycloneDX**: Multi-language SBOM tools
- **Syft**: Universal SBOM generator (Anchore)
- **SPDX Tools**: Official SPDX utilities
- **Tern**: Container SBOM analysis
- **OSS Review Toolkit**: Comprehensive SBOM suite

### Vulnerability Scanners
- **Grype**: Vulnerability scanner (Anchore)
- **Trivy**: Container/filesystem scanner (Aqua)
- **OWASP Dependency-Check**: Multi-language vulnerability detection
- **Snyk**: Commercial vulnerability platform
- **GitHub Dependabot**: Automated dependency updates

### License Analysis
- **FOSSA**: License compliance platform
- **ScanCode**: Open source license scanner
- **licensee**: GitHub's license detection
- **FOSSology**: License compliance system

### SBOM Management
- **Dependency-Track**: SBOM analysis platform
- **sw360**: Software component catalog
- **Hoppr**: SBOM diffing and analysis
- **SBOM Tool**: Microsoft SBOM utility

## Additional Resources

- [NTIA SBOM Minimum Elements](https://www.ntia.gov/files/ntia/publications/sbom_minimum_elements_report.pdf)
- [EU Cyber Resilience Act](https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act)
- [CycloneDX Specification](https://cyclonedx.org/specification/overview/)
- [SPDX Specification](https://spdx.github.io/spdx-spec/)
- [CISA SBOM Resources](https://www.cisa.gov/sbom)
- [OpenSSF Security Scorecard](https://securityscorecards.dev/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - documentation/sbom/
