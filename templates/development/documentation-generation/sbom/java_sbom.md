---
template_id: java_sbom
template_name: Sbom - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: documentation
phase: sbom
difficulty: beginner
estimated_time_hours: 2-3
prerequisites: []
tools:

  - junit (5.11.3)

  - maven

  - gradle
tags:

  - documentation

  - documentation

  - java
---
# Java SBOM Generation

## Objective
Generate comprehensive, standards-compliant Software Bill of Materials (SBOM) documentation that meets regulatory requirements (NTIA minimum elements, EU Cyber Resilience Act) for security, compliance, and supply chain management in Java projects using Maven or Gradle.

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

- [ ] Scope-specific dependencies tracked

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
# Java SBOM Generation Request

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

Please generate a comprehensive Software Bill of Materials (SBOM) for this Java project following this protocol:

## Phase 1: Dependency Discovery & Analysis

1. **Inventory Direct Dependencies (Maven)**

   Analyze `pom.xml`:

   ```bash
   # List all dependencies
   mvn dependency:list -DoutputFile=dependencies.txt

   # Generate dependency tree
   mvn dependency:tree -DoutputFile=dependency_tree.txt

   # Generate JSON report
   mvn dependency:tree -DoutputType=json -DoutputFile=dependencies.json

   # List with details
   mvn dependency:list -DincludeScope=compile
   ```

2. **Inventory Direct Dependencies (Gradle)**

   Analyze `build.gradle` or `build.gradle.kts`:

   ```bash
   # List all dependencies
   gradle dependencies > ${OUTPUT_DIR}/exports/dependencies.txt

   # Generate dependency report
   gradle dependencies --configuration runtimeClasspath

   # Generate HTML report
   gradle htmlDependencyReport

   # JSON format (with plugin)
   gradle generateBom --output-file sbom.json
   ```

3. **Map Transitive Dependencies**

   Create complete dependency tree:

   ```bash
   # Maven - full tree
   mvn dependency:tree -Dverbose

   # Maven - resolve conflicts
   mvn dependency:tree -Dverbose -DoutputFile=tree_verbose.txt

   # Gradle - all configurations
   gradle dependencies --configuration compileClasspath
   gradle dependencies --configuration runtimeClasspath

   # Gradle - dependency insight
   gradle dependencyInsight --dependency jackson-databind
   ```

4. **Identify Dependency Metadata**

   For each dependency, collect:

   - Group ID

   - Artifact ID

   - Version

   - License

   - Repository URL

   - Type (JAR, WAR, POM)

   - Scope/configuration

   - Dependencies (for transitive mapping)

## Phase 2: SBOM Format Selection

Choose SBOM format based on requirements:

### Option 1: SPDX (Software Package Data Exchange)

- **Standard**: ISO/IEC 5962:2021

- **Format**: JSON, YAML, RDF, Tag-Value

- **Best for**: License compliance, legal requirements

- **Tools**: spdx-maven-plugin, spdx-gradle-plugin

### Option 2: CycloneDX

- **Standard**: OWASP CycloneDX

- **Format**: JSON, XML

- **Best for**: Security analysis, vulnerability management

- **Tools**: cyclonedx-maven-plugin, cyclonedx-gradle-plugin

### Option 3: SWID (Software Identification Tags)

- **Standard**: ISO/IEC 19770-2:2015

- **Format**: XML

- **Best for**: IT asset management

**Recommendation**: Use CycloneDX for security focus, SPDX for license focus.

## Phase 3: Generate SBOM (CycloneDX Format)

### Using cyclonedx-maven-plugin

Add to `pom.xml`:

```xml
<project>
  <build>
    <plugins>
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
          <projectType>application</projectType>
          <schemaVersion>1.4</schemaVersion>
          <includeBomSerialNumber>true</includeBomSerialNumber>
          <includeCompileScope>true</includeCompileScope>
          <includeProvidedScope>true</includeProvidedScope>
          <includeRuntimeScope>true</includeRuntimeScope>
          <includeSystemScope>true</includeSystemScope>
          <includeTestScope>false</includeTestScope>
          <includeLicenseText>false</includeLicenseText>
          <outputFormat>json</outputFormat>
          <outputName>sbom</outputName>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
```

Generate SBOM:

```bash
# Generate SBOM
mvn cyclonedx:makeAggregateBom

# Output: target/sbom.json
```

### Using cyclonedx-gradle-plugin

Add to `build.gradle`:

```groovy
plugins {
    id 'org.cyclonedx.bom' version '1.7.4'
}

cyclonedxBom {
    includeConfigs = ["runtimeClasspath"]
    skipConfigs = ["testRuntimeClasspath"]
    projectType = "application"
    schemaVersion = "1.4"
    destination = file("build/reports")
    outputName = "sbom"
    outputFormat = "json"
    includeBomSerialNumber = true
    includeLicenseText = false
}
```

Generate SBOM:

```bash
# Generate SBOM
gradle cyclonedxBom

# Output: build/reports/sbom.json
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
        "name": "cyclonedx-maven-plugin",
        "version": "2.7.9"
      }
    ],
    "authors": [
      {
        "name": "Benjamin Dourthe",
        "email": "benjamin.dourthe@gmail.com"
      }
    ],
    "component": {
      "type": "application",
      "bom-ref": "pkg:maven/com.example/project-name@1.0.0",
      "group": "com.example",
      "name": "project-name",
      "version": "1.0.0",
      "description": "Project description",
      "licenses": [
        {
          "license": {
            "id": "Apache-2.0"
          }
        }
      ],
      "purl": "pkg:maven/com.example/project-name@1.0.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://github.com/username/project"
        },
        {
          "type": "vcs",
          "url": "https://github.com/username/project.git"
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
      "bom-ref": "pkg:maven/org.springframework.boot/spring-boot-starter-web@3.2.0",
      "group": "org.springframework.boot",
      "name": "spring-boot-starter-web",
      "version": "3.2.0",
      "description": "Starter for building web, including RESTful, applications using Spring MVC",
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
        }
      ],
      "licenses": [
        {
          "license": {
            "id": "Apache-2.0"
          }
        }
      ],
      "purl": "pkg:maven/org.springframework.boot/spring-boot-starter-web@3.2.0",
      "externalReferences": [
        {
          "type": "website",
          "url": "https://spring.io/projects/spring-boot"
        },
        {
          "type": "vcs",
          "url": "https://github.com/spring-projects/spring-boot"
        },
        {
          "type": "distribution",
          "url": "https://repo1.maven.org/maven2/org/springframework/boot/spring-boot-starter-web/3.2.0/spring-boot-starter-web-3.2.0.jar"
        }
      ],
      "properties": [
        {
          "name": "maven:scope",
          "value": "compile"
        }
      ]
    },
    {
      "type": "library",
      "bom-ref": "pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.15.3",
      "group": "com.fasterxml.jackson.core",
      "name": "jackson-databind",
      "version": "2.15.3",
      "description": "General data-binding functionality for Jackson",
      "licenses": [
        {
          "license": {
            "id": "Apache-2.0"
          }
        }
      ],
      "purl": "pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.15.3"
    },
    {
      "type": "library",
      "bom-ref": "pkg:maven/org.apache.commons/commons-lang3@3.13.0",
      "group": "org.apache.commons",
      "name": "commons-lang3",
      "version": "3.13.0",
      "description": "Apache Commons Lang",
      "licenses": [
        {
          "license": {
            "id": "Apache-2.0"
          }
        }
      ],
      "purl": "pkg:maven/org.apache.commons/commons-lang3@3.13.0"
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:maven/com.example/project-name@1.0.0",
      "dependsOn": [
        "pkg:maven/org.springframework.boot/spring-boot-starter-web@3.2.0",
        "pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.15.3",
        "pkg:maven/org.apache.commons/commons-lang3@3.13.0"
      ]
    },
    {
      "ref": "pkg:maven/org.springframework.boot/spring-boot-starter-web@3.2.0",
      "dependsOn": [
        "pkg:maven/org.springframework.boot/spring-boot-starter@3.2.0",
        "pkg:maven/org.springframework.boot/spring-boot-starter-json@3.2.0",
        "pkg:maven/org.springframework/spring-web@6.1.1",
        "pkg:maven/org.springframework/spring-webmvc@6.1.1"
      ]
    }
  ],
  "vulnerabilities": [
    {
      "bom-ref": "vuln:maven/com.fasterxml.jackson.core/jackson-databind@2.14.0:CVE-2023-35116",
      "id": "CVE-2023-35116",
      "source": {
        "name": "NVD",
        "url": "https://nvd.nist.gov/vuln/detail/CVE-2023-35116"
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
      "cwes": [502],
      "description": "Deserialization of Untrusted Data in jackson-databind",
      "recommendation": "Update to version 2.15.0 or higher",
      "affects": [
        {
          "ref": "pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.14.0",
          "versions": [
            {
              "version": "2.14.0",
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

### Using spdx-maven-plugin

Add to `pom.xml`:

```xml
<plugin>
  <groupId>org.spdx</groupId>
  <artifactId>spdx-maven-plugin</artifactId>
  <version>0.7.1</version>
  <executions>
    <execution>
      <goals>
        <goal>createSPDX</goal>
      </goals>
    </execution>
  </executions>
  <configuration>
    <spdxDocumentNamespace>https://example.com/spdx/project-name-1.0.0</spdxDocumentNamespace>
    <defaultFileCopyright>Copyright (c) 2024 Benjamin Dourthe</defaultFileCopyright>
    <defaultFileContributors>
      <param>Benjamin Dourthe</param>
    </defaultFileContributors>
    <defaultLicenseInformationInFile>Apache-2.0</defaultLicenseInformationInFile>
    <defaultFileConcludedLicense>Apache-2.0</defaultFileConcludedLicense>
    <defaultFileNotice>SPDX-License-Identifier: Apache-2.0</defaultFileNotice>
  </configuration>
</plugin>
```

Generate SBOM:

```bash
# Generate SPDX SBOM
mvn spdx:createSPDX

# Output: target/site/project-name-1.0.0.spdx.rdf.xml
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
      "Tool: spdx-maven-plugin-0.7.1",
      "Person: Benjamin Dourthe (benjamin.dourthe@gmail.com)"
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
      "licenseConcluded": "Apache-2.0",
      "licenseDeclared": "Apache-2.0",
      "copyrightText": "Copyright (c) 2024 Benjamin Dourthe",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:maven/com.example/project-name@1.0.0"
        }
      ]
    },
    {
      "SPDXID": "SPDXRef-Package-spring-boot-starter-web",
      "name": "spring-boot-starter-web",
      "versionInfo": "3.2.0",
      "downloadLocation": "https://repo1.maven.org/maven2/org/springframework/boot/spring-boot-starter-web/3.2.0/",
      "filesAnalyzed": false,
      "homepage": "https://spring.io/projects/spring-boot",
      "licenseConcluded": "Apache-2.0",
      "licenseDeclared": "Apache-2.0",
      "copyrightText": "Copyright (c) Pivotal Software, Inc.",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:maven/org.springframework.boot/spring-boot-starter-web@3.2.0"
        },
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:vmware:spring_boot:3.2.0:*:*:*:*:*:*:*"
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
      "relatedSpdxElement": "SPDXRef-Package-spring-boot-starter-web"
    }
  ]
}
```

## Phase 5: Vulnerability Scanning

Scan for known vulnerabilities in dependencies:

### Using OWASP Dependency-Check (Maven)

Add to `pom.xml`:

```xml
<plugin>
  <groupId>org.owasp</groupId>
  <artifactId>dependency-check-maven</artifactId>
  <version>9.0.7</version>
  <executions>
    <execution>
      <goals>
        <goal>check</goal>
      </goals>
    </execution>
  </executions>
  <configuration>
    <format>JSON</format>
    <format>HTML</format>
    <outputDirectory>target/dependency-check</outputDirectory>
  </configuration>
</plugin>
```

Run scan:

```bash
# Run OWASP Dependency-Check
mvn dependency-check:check

# Update vulnerability database
mvn dependency-check:update-only

# Suppress false positives
mvn dependency-check:check -DsuppressionFile=dependency-check-suppressions.xml

# Output: target/dependency-check/dependency-check-report.json
```

### Using OWASP Dependency-Check (Gradle)

Add to `build.gradle`:

```groovy
plugins {
    id 'org.owasp.dependencycheck' version '9.0.7'
}

dependencyCheck {
    formats = ['JSON', 'HTML']
    outputDirectory = 'build/reports/dependency-check'
}
```

Run scan:

```bash
# Run OWASP Dependency-Check
gradle dependencyCheckAnalyze

# Output: build/reports/dependency-check/dependency-check-report.json
```

### Using Snyk

```bash
# Install Snyk CLI
npm install -g snyk

# Authenticate
snyk auth

# Test Maven project
snyk test --file=pom.xml --json > ${OUTPUT_DIR}/exports/snyk_report.json

# Test Gradle project
snyk test --file=build.gradle --json > ${OUTPUT_DIR}/exports/snyk_report.json

# Monitor project
snyk monitor
```

### Using Trivy

```bash
# Install Trivy
# See: https://aquasecurity.github.io/trivy/

# Scan Java project
trivy fs --format json --output ${OUTPUT_DIR}/exports/trivy_report.json .

# Scan specific JAR file
trivy fs --scanners vuln target/project-name-1.0.0.jar
```

## Phase 6: License Analysis

### Using license-maven-plugin

Add to `pom.xml`:

```xml
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>license-maven-plugin</artifactId>
  <version>2.3.0</version>
  <executions>
    <execution>
      <goals>
        <goal>aggregate-add-third-party</goal>
      </goals>
    </execution>
  </executions>
  <configuration>
    <outputDirectory>target/generated-sources/license</outputDirectory>
    <thirdPartyFilename>THIRD-PARTY.txt</thirdPartyFilename>
    <fileTemplate>/org/codehaus/mojo/license/third-party-file-groupByLicense.ftl</fileTemplate>
  </configuration>
</plugin>
```

Generate report:

```bash
# Generate license report
mvn license:aggregate-add-third-party

# Output: target/generated-sources/license/THIRD-PARTY.txt

# Download licenses
mvn license:download-licenses

# Output: target/generated-resources/licenses.xml
```

### Using Gradle License Plugin

Add to `build.gradle`:

```groovy
plugins {
    id 'com.github.jk1.dependency-license-report' version '2.5'
}

licenseReport {
    renderers = [new com.github.jk1.license.render.JsonReportRenderer()]
    outputDir = "$projectDir/build/reports/licenses"
}
```

Generate report:

```bash
# Generate license report
gradle generateLicenseReport

# Output: build/reports/licenses/licenses.json
```

### License Compatibility Matrix

Document license compatibility:

```markdown
## License Compatibility

| License | Can Include | Cannot Include | Notes |
|---------|-------------|----------------|-------|
| Apache-2.0 | MIT, BSD, Apache | - | Patent grant included |
| MIT | Any | - | Very permissive |
| BSD-3-Clause | Any | - | Very permissive |
| GPL-3.0 | MIT, BSD | Proprietary | Copyleft - requires source |
| LGPL-3.0 | MIT, BSD | - | Lesser copyleft |
| EPL-2.0 | MIT, BSD | GPL | Eclipse Public License |
| CDDL-1.1 | MIT, BSD | GPL | Common Development License |
| Proprietary | ? | GPL, AGPL | Check license terms |

**Current Project License**: Apache-2.0

**Compatibility Status**:

- ✅ Compatible: Spring Boot (Apache-2.0), Jackson (Apache-2.0), Commons (Apache-2.0)

- ⚠️ Review Required: [list needing review]

- ❌ Incompatible: [list of incompatible]
```

## Phase 7: Supply Chain Security Assessment

### Package Provenance

```bash
# Maven - verify checksums
mvn verify

# Maven - verify signatures
mvn verify -Dgpg.verify=true

# Gradle - verify checksums
gradle build --warning-mode all

# Generate dependency verification metadata (Gradle)
gradle --write-verification-metadata sha256
```

### Repository Security

For each dependency, document:

```markdown
## Dependency: spring-boot-starter-web

**Repository**: https://github.com/spring-projects/spring-boot
**Package Registry**: Maven Central
**Maintainer**: VMware (Pivotal)

**Security Posture**:

- ✅ Active maintenance (last commit: [date])

- ✅ Security policy present

- ✅ Vulnerability disclosure process

- ✅ Package signing (GPG)

- ✅ Recent security audit

- ✅ Large, active community (70k+ stars)

- ✅ Corporate backing (VMware)

**Risk Assessment**: LOW

- Well-maintained, enterprise-grade library

- Active security response

- Regular updates and patches

- Strong community and corporate oversight

**Alternative Options**:

- Quarkus (cloud-native alternative)

- Micronaut (microservices framework)

- Helidon (Oracle's microservices framework)
```

## Phase 8: Compliance Documentation

### NTIA Minimum Elements Compliance

```markdown
# NTIA SBOM Compliance Checklist

## Minimum Elements

- [x] **Supplier Name**: All suppliers identified in SBOM

- [x] **Component Name**: All components named (groupId:artifactId)

- [x] **Version**: All versions specified

- [x] **Other Unique Identifiers**: PURL and CPE provided for all

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

- [x] Vulnerability scanning integrated (OWASP Dependency-Check)

**Compliance Status**: ✅ COMPLIANT
```

### EU Cyber Resilience Act Compliance

```markdown
# EU CRA Compliance Checklist

## Essential Requirements

- [x] Complete SBOM with all components

- [x] Known vulnerabilities identified (CVE tracking via OWASP)

- [x] Security updates and patches tracked

- [x] Vulnerability disclosure timeline documented

- [x] Supply chain security assessed

## Documentation Requirements

- [x] SBOM in standardized format (CycloneDX/SPDX)

- [x] Vulnerability report attached (OWASP Dependency-Check)

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

   - All known CVEs (from OWASP Dependency-Check)

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

   - Scope-specific dependencies

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
**Build Tool**: Maven/Gradle

**Components**:

- Total components: [count]

- Direct dependencies: [count]

- Transitive dependencies: [count]

- Unique licenses: [count]

**Vulnerabilities** (OWASP Dependency-Check):

- Critical: [count]

- High: [count]

- Medium: [count]

- Low: [count]

- Total: [count]

**License Distribution**:

- Apache-2.0: [count]

- MIT: [count]

- EPL-2.0: [count]

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
  sbom-maven:
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3

      - name: Set up JDK 17
        uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Generate CycloneDX SBOM
        run: mvn cyclonedx:makeAggregateBom

      - name: Run OWASP Dependency-Check
        run: mvn dependency-check:check

      - name: Generate license report
        run: mvn license:aggregate-add-third-party

      - name: Upload SBOM artifacts
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: |
            target/sbom.json
            target/dependency-check/dependency-check-report.json
            target/generated-sources/license/THIRD-PARTY.txt

      - name: Attach to release
        if: github.event_name == 'release'
        uses: softprops/action-gh-release@v1
        with:
          files: target/sbom.json
```

### GitLab CI/CD

```yaml
sbom:
  stage: build
  image: maven:3.9-eclipse-temurin-17
  script:

    - mvn clean package

    - mvn cyclonedx:makeAggregateBom

    - mvn dependency-check:check
  artifacts:
    paths:

      - target/sbom.json

      - target/dependency-check/dependency-check-report.json
    expire_in: 1 year
```

---

## Best Practices

1. **Automate SBOM Generation**

   - Integrate into Maven/Gradle build

   - Generate in CI/CD pipeline

   - Update with every release

   - Include in release artifacts

2. **Keep SBOMs Current**

   - Regenerate on dependency updates

   - Track vulnerability fixes

   - Document changes between versions

   - Run OWASP Dependency-Check regularly

3. **Use Multiple Formats**

   - CycloneDX for security

   - SPDX for license compliance

   - Both for comprehensive coverage

4. **Continuous Monitoring**

   - Monitor for new vulnerabilities (OWASP, Snyk)

   - Track dependency updates (Dependabot, Renovate)

   - Assess supply chain risks

   - Enable Maven Central security scanning

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
