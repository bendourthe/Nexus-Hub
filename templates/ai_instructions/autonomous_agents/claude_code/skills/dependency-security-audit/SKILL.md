---
name: dependency-security-audit
description: Systematically audit project dependencies for known vulnerabilities (CVEs), license compliance issues, and outdated packages - generate SBOM and provide remediation strategies
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Security
tags: [security, dependencies, vulnerabilities, CVE, SBOM, audit, compliance]
priority: HIGH
based_on: OWASP Dependency-Check, Snyk Security Best Practices, NIST Software Supply Chain Guidelines
---

# Dependency Security Audit

Systematically audit all project dependencies for known security vulnerabilities (CVEs), license compliance issues, and outdated packages. Generate comprehensive Software Bill of Materials (SBOM) and provide actionable remediation strategies across all supported languages.

## When to Use This Skill

Use this skill whenever you need to:

- ✅ Audit dependencies before production deployment

- ✅ Comply with security requirements (SOC 2, ISO 27001)

- ✅ Respond to newly disclosed vulnerabilities

- ✅ Onboard third-party or legacy code

- ✅ Prepare for security certification

- ✅ Establish supply chain security baseline

- ✅ Generate SBOM for compliance reporting

- ✅ Verify open-source license compatibility

- ✅ Quarterly or monthly security reviews

**This skill is critical when**:

- New CVEs are disclosed affecting your stack

- Preparing for security audits or penetration testing

- Onboarding acquired or inherited codebases

- Implementing DevSecOps practices

- Meeting regulatory compliance requirements

## What This Skill Does

This skill provides comprehensive dependency security analysis:

### Core Capabilities
- **Vulnerability Scanning**: Detect known CVEs in all dependencies

- **License Auditing**: Identify license compliance issues

- **Outdated Package Detection**: Find dependencies with security patches

- **Transitive Dependency Analysis**: Audit indirect dependencies

- **SBOM Generation**: Create complete software bill of materials

- **Risk Prioritization**: CVSS scoring and exploitability assessment

- **Remediation Guidance**: Actionable fix recommendations

### Language Support
- Python (pip, poetry, pipenv)

- JavaScript/TypeScript (npm, yarn, pnpm)

- Java (Maven, Gradle)

- C# (.NET, NuGet)

- Go (go.mod)

- C/C++ (Conan, vcpkg, CMake)

## Why Dependency Security Audits Matter

**Without Dependency Audits**:
```
Team: *deploys with vulnerable dependencies*
Application: *runs with known exploitable CVEs*
Attackers: *exploit public vulnerabilities*
Result:

- ❌ Remote code execution via vulnerable library

- ❌ Data breach through dependency exploit

- ❌ Supply chain compromise

- ❌ Legal liability for known vulnerabilities

- ❌ Compliance violations and audit failures

- ❌ Reputation damage from preventable breach
```

**With Dependency Audits**:
```
Team: *performs regular dependency audits*
Application: *runs with patched, secure libraries*
Attackers: *find no known vulnerable dependencies*
Result:

- ✅ Vulnerabilities identified and patched proactively

- ✅ Clean security audit reports

- ✅ Compliance requirements met

- ✅ Supply chain risk minimized

- ✅ Security posture documented

- ✅ Confidence in production deployments
```

## Benefits of Dependency Security Audits

### Risk Mitigation
- **Prevent Exploits**: Fix vulnerabilities before attackers discover them

- **Supply Chain Security**: Verify all third-party code

- **Reduce Attack Surface**: Remove unnecessary dependencies

- **Stay Current**: Keep pace with security patches

### Compliance
- **Meet Standards**: Satisfy SOC 2, ISO 27001, PCI-DSS requirements

- **SBOM Requirements**: Comply with executive orders and regulations

- **License Compliance**: Avoid legal issues with incompatible licenses

- **Audit Readiness**: Provide complete dependency documentation

### Operational Excellence
- **Technical Debt**: Identify outdated dependencies

- **Maintenance Planning**: Prioritize upgrade efforts

- **Security Culture**: Build awareness of supply chain risks

- **Automation**: Integrate into CI/CD pipelines

## Prerequisites

### Required
- Package manager configuration files accessible

- Network access to vulnerability databases

- Command-line tool installation permissions

### Recommended
- CI/CD pipeline access for automation

- Version control system (Git)

- API keys for enhanced scanning (Snyk, GitHub, etc.)

- Security dashboard or tracking system

### Knowledge
- Dependency management for target language

- CVE severity scoring (CVSS)

- Software licensing basics

- Semantic versioning principles

## Instructions

### Step 1: Install Security Scanning Tools

**Install appropriate tools for each language in your project:**

#### Python

```bash
# Install pip-audit (official Python auditing tool)
pip install pip-audit

# Install safety (alternative scanner)
pip install safety

# Install bandit (SAST tool with dependency checks)
pip install bandit[toml]

# Install pip-licenses (license scanner)
pip install pip-licenses

# Install cyclonedx-bom (SBOM generator)
pip install cyclonedx-bom
```

#### JavaScript/TypeScript

```bash
# NPM audit (built-in)
# No installation needed

# Install Snyk CLI
npm install -g snyk

# Install npm-check-updates
npm install -g npm-check-updates

# Install license-checker
npm install -g license-checker

# Install CycloneDX for Node.js
npm install -g @cyclonedx/cyclonedx-npm
```

#### Java

```bash
# OWASP Dependency-Check (Maven plugin)
# Add to pom.xml:
<plugin>
    <groupId>org.owasp</groupId>
    <artifactId>dependency-check-maven</artifactId>
    <version>8.4.0</version>
</plugin>

# Or standalone CLI
wget https://github.com/jeremylong/DependencyCheck/releases/download/v8.4.0/dependency-check-8.4.0-release.zip

# Maven versions plugin (for updates)
mvn versions:display-dependency-updates

# License Maven Plugin
# Add to pom.xml
```

#### C#

```bash
# dotnet CLI tools (built-in vulnerability scanning)
dotnet list package --vulnerable

# Install dotnet-outdated
dotnet tool install -g dotnet-outdated-tool

# Install CycloneDX for .NET
dotnet tool install -g CycloneDX
```

#### Go

```bash
# Install govulncheck (official Go vulnerability scanner)
go install golang.org/x/vuln/cmd/govulncheck@latest

# Install Nancy (Sonatype vulnerability scanner)
go install github.com/sonatype-nexus-community/nancy@latest

# Install go-licenses
go install github.com/google/go-licenses@latest

# Install cyclonedx-gomod
go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest
```

#### C/C++

```bash
# Install Conan (if using Conan package manager)
pip install conan

# Install vcpkg (if using vcpkg)
# Follow: https://github.com/microsoft/vcpkg

# For CVE scanning, use general tools:
pip install safety  # Can scan requirements
```

### Step 2: Run Vulnerability Scans

**Execute comprehensive vulnerability scanning for each language:**

#### Python - Comprehensive Scan

```bash
# 1. Scan with pip-audit (recommended primary tool)
pip-audit --desc --format json --output pip-audit-report.json
pip-audit --desc  # Human-readable output

# 2. Scan with safety
safety check --json --output safety-report.json
safety check --full-report

# 3. Check for outdated packages with security fixes
pip list --outdated --format json > outdated-packages.json

# 4. Detailed vulnerability information
pip-audit --vulnerability-service osv --format cyclonedx-json --output sbom.json

# 5. Fix available vulnerabilities (dry run first)
pip-audit --fix --dry-run
```

**Example Output Analysis**:
```
Found 3 known vulnerabilities in 2 packages

Name      Version  Vulnerability  CVSS  Fix Available
────────────────────────────────────────────────────
requests  2.25.0   CVE-2023-32681  6.1   2.31.0
urllib3   1.26.0   CVE-2023-43804  8.6   1.26.17
urllib3   1.26.0   CVE-2023-45803  4.2   1.26.17
```

#### JavaScript/TypeScript - Comprehensive Scan

```bash
# 1. NPM audit (built-in, fast)
npm audit --json > npm-audit.json
npm audit

# 2. Yarn audit (if using Yarn)
yarn audit --json > yarn-audit.json
yarn audit

# 3. Snyk comprehensive scan (requires account)
snyk auth  # First time only
snyk test --json > snyk-report.json
snyk test --severity-threshold=medium

# 4. Check for updates
npm-check-updates
ncu --doctor  # Test updates safely

# 5. Monitor for future vulnerabilities
snyk monitor  # Continuous monitoring

# 6. Fix vulnerabilities automatically
npm audit fix --dry-run  # Preview changes
npm audit fix  # Apply fixes
npm audit fix --force  # Force major version updates (risky)
```

**Example Output**:
```
found 8 vulnerabilities (2 low, 3 moderate, 2 high, 1 critical)

# Critical
  ┌───────────────┬──────────────────────────────────────────────┐
  │ Severity      │ Critical                                      │
  │ Package       │ lodash                                        │
  │ Current       │ 4.17.15                                       │
  │ Patched       │ 4.17.21                                       │
  │ CVE           │ CVE-2021-23337                                │
  │ CVSS          │ 9.8                                           │
  └───────────────┴──────────────────────────────────────────────┘
```

#### Java - Comprehensive Scan

```bash
# Maven Projects

# 1. OWASP Dependency-Check (comprehensive)
mvn dependency-check:check
mvn dependency-check:check -DfailBuildOnCVSS=7

# Output location: target/dependency-check-report.html

# 2. Check for dependency updates
mvn versions:display-dependency-updates

# 3. Analyze dependency tree
mvn dependency:tree > dependency-tree.txt
mvn dependency:analyze

# 4. Generate SBOM
mvn org.cyclonedx:cyclonedx-maven-plugin:makeAggregateBom

# Gradle Projects

# 1. OWASP Dependency-Check
gradle dependencyCheckAnalyze

# 2. Check for updates
gradle dependencyUpdates

# 3. Analyze dependencies
gradle dependencies > dependencies.txt

# 4. Generate SBOM
gradle cyclonedxBom
```

**Example Output**:
```
Dependency-Check Report

Project: myapp
Scan Date: 2025-10-21

Vulnerabilities Found: 5

CVE-2023-xxxxx (CVSS: 9.8 - CRITICAL)
  Package: log4j-core:2.14.1
  Description: Remote code execution vulnerability
  Fix: Upgrade to 2.17.1 or higher
```

#### C# - Comprehensive Scan

```bash
# 1. Built-in vulnerability scanning
dotnet list package --vulnerable
dotnet list package --vulnerable --include-transitive

# 2. Check for outdated packages
dotnet-outdated

# 3. Check for deprecated packages
dotnet list package --deprecated

# 4. Restore and audit
dotnet restore
dotnet list package --vulnerable --source https://api.nuget.org/v3/index.json

# 5. Generate SBOM
CycloneDX -o sbom.xml -s solution.sln
```

**Example Output**:
```
Project `WebApp` has the following vulnerable packages:

   [net6.0]:
   Top-level Package      Requested   Resolved   Severity   Advisory URL
   > System.Text.Json     5.0.0       5.0.0      High       https://github.com/advisories/GHSA-xxxx
```

#### Go - Comprehensive Scan

```bash
# 1. govulncheck (official Go vulnerability scanner)
govulncheck ./...
govulncheck -json ./... > govulncheck-report.json

# 2. Nancy scanner
go list -json -deps ./... | nancy sleuth
nancy sleuth -p go.sum

# 3. Check module updates
go list -u -m all

# 4. Module verification
go mod verify
go mod tidy

# 5. Generate SBOM
cyclonedx-gomod app -json=true -output sbom.json
```

**Example Output**:
```
govulncheck is an experimental tool. Share feedback at https://go.dev/s/govulncheck-feedback.

Scanning for dependencies with known vulnerabilities...
Found 1 known vulnerability.

Vulnerability #1: GO-2023-1234
  Package: golang.org/x/net
  Module:  golang.org/x/net
  Introduced: v0.0.0-20220101000000
  Fixed:      v0.7.0
  CVSS:       7.5 (HIGH)
  Description: HTTP/2 rapid reset attack

Recommendation: Upgrade to golang.org/x/net v0.7.0 or later
```

#### C/C++ - Comprehensive Scan

```bash
# Conan-based projects

# 1. Update Conan repository
conan search "*" -r=all --update

# 2. Check for vulnerabilities (limited native support)
# Use dependency list with external scanners
conan info . --json > conan-deps.json

# 3. Check for updates
conan search package_name -r=conancenter

# vcpkg-based projects

# 1. Update vcpkg
git -C vcpkg pull

# 2. Check for updates
vcpkg upgrade

# 3. List installed packages
vcpkg list

# General C/C++ scanning

# 4. Static analysis with security focus
cppcheck --enable=all --inconclusive --xml src/ 2> cppcheck-report.xml

# 5. Flawfinder for security issues
flawfinder --html src/ > flawfinder-report.html
```

**Note**: C/C++ dependency vulnerability scanning is less mature than other ecosystems. Consider:

- Manually tracking dependencies and CVEs

- Using container scanning if deploying in containers

- Implementing SBOM practices for visibility

### Step 3: License Compliance Audit

**Verify all dependencies have compatible licenses:**

#### Python - License Audit

```bash
# 1. Generate license report
pip-licenses --format=markdown --output-file=licenses.md
pip-licenses --format=json --output-file=licenses.json

# 2. Check for specific license types
pip-licenses --summary

# 3. Identify packages with unknown licenses
pip-licenses | grep "UNKNOWN"

# 4. Detailed license information
pip-licenses --with-urls --with-description > licenses-detailed.txt
```

**Example Output**:
```
Name          Version  License
────────────────────────────────
requests      2.31.0   Apache 2.0
urllib3       2.0.4    MIT
certifi       2023.7.22 MPL-2.0
```

#### JavaScript/TypeScript - License Audit

```bash
# 1. Generate license report
license-checker --json > licenses.json
license-checker --csv > licenses.csv

# 2. Check for specific licenses
license-checker --onlyAllow "MIT;Apache-2.0;BSD-3-Clause"

# 3. Exclude licenses
license-checker --exclude "GPL;AGPL"

# 4. Detailed package information
license-checker --summary
```

#### Java - License Audit

```bash
# Maven - License Plugin
mvn license:aggregate-third-party-report

# Output: target/site/aggregate-third-party-report.html
```

#### C# - License Audit

```bash
# Using dotnet-project-licenses
dotnet tool install --global dotnet-project-licenses

dotnet-project-licenses -i . -o -u -f markdown > licenses.md
```

#### Go - License Audit

```bash
# 1. Generate license report
go-licenses report ./... --template=licenses.tpl > licenses.md

# 2. Check specific license
go-licenses check ./...

# 3. Save license files
go-licenses save ./... --save_path=licenses/
```

**Common License Compatibility Issues**:

| Your License | Compatible Dependency Licenses | Incompatible |
|--------------|-------------------------------|--------------|
| MIT | MIT, Apache 2.0, BSD, ISC | GPL*, AGPL* |
| Apache 2.0 | MIT, Apache 2.0, BSD | GPL 2.0, AGPL |
| GPL 3.0 | MIT, BSD, Apache 2.0, GPL | Proprietary |
| Proprietary | MIT, BSD, Apache 2.0 | GPL*, AGPL* |

**Action Required for Incompatible Licenses**:

1. Replace with compatible alternative library

2. Negotiate license exception (rarely possible)

3. Change project license (if feasible)

4. Remove functionality that requires incompatible dependency

### Step 4: Generate Software Bill of Materials (SBOM)

**Create comprehensive SBOM for supply chain transparency:**

#### Python - SBOM Generation

```bash
# CycloneDX format (recommended for security)
cyclonedx-py --format json --output sbom.json
cyclonedx-py --format xml --output sbom.xml

# SPDX format (alternative standard)
pip install spdx-tools
# Manual SPDX generation or use commercial tools
```

#### JavaScript - SBOM Generation

```bash
# CycloneDX for NPM
cyclonedx-npm --output-file sbom.json

# With all dependencies (including dev)
cyclonedx-npm --output-file sbom-full.json --omit none
```

#### Java - SBOM Generation

```bash
# Maven
mvn org.cyclonedx:cyclonedx-maven-plugin:makeAggregateBom

# Gradle
gradle cyclonedxBom
```

#### C# - SBOM Generation

```bash
# CycloneDX for .NET
CycloneDX -o sbom.json -f JSON -s solution.sln
```

#### Go - SBOM Generation

```bash
# CycloneDX for Go
cyclonedx-gomod app -json=true -output sbom.json
```

**SBOM Use Cases**:

- Compliance reporting (FDA, NTIA, Executive Orders)

- Vulnerability management (track affected components)

- License compliance documentation

- Supply chain risk assessment

- Incident response (identify affected systems)

### Step 5: Analyze and Prioritize Vulnerabilities

**Assess discovered vulnerabilities for risk and impact:**

#### Severity Classification

**CVSS Score Ranges**:

- **Critical (9.0-10.0)**: Immediate action required

- **High (7.0-8.9)**: Urgent attention needed

- **Medium (4.0-6.9)**: Plan remediation

- **Low (0.1-3.9)**: Address when possible

**Prioritization Matrix**:

```
High Exploitability + High Impact = P0 (Fix immediately)
High Exploitability + Low Impact  = P1 (Fix this sprint)
Low Exploitability + High Impact  = P1 (Fix this sprint)
Low Exploitability + Low Impact   = P2 (Plan for future)
```

**Exploitability Factors**:

- [ ] Public exploit code available

- [ ] Vulnerability in internet-facing component

- [ ] No authentication required

- [ ] Easy to exploit (low complexity)

- [ ] Actively being exploited in the wild

**Impact Factors**:

- [ ] Affects production systems

- [ ] Handles sensitive data

- [ ] Critical business function

- [ ] Regulatory compliance requirement

- [ ] Customer-facing component

#### Vulnerability Assessment Template

```markdown
## Vulnerability Assessment

### CVE-2023-XXXXX

**Package**: lodash@4.17.15
**Severity**: Critical (CVSS 9.8)
**Category**: Prototype Pollution

**Description**:
Remote code execution via prototype pollution in lodash template function.

**Affected Code**:

- `src/api/users.js:45` - Uses lodash.template with user input

- `src/utils/formatter.js:120` - Calls vulnerable function

**Exploitability**: HIGH

- [x] Public exploit available (exploit-db.com/exploits/12345)

- [x] Internet-facing endpoint

- [x] No authentication required

- [x] Low complexity

**Impact**: HIGH

- [x] Production system affected

- [x] Handles PII data

- [x] Critical user authentication flow

**Priority**: P0 - Fix Immediately

**Remediation**:

1. Upgrade lodash to 4.17.21 or higher

2. Review all uses of lodash.template

3. Sanitize user input before template processing

4. Deploy fix within 24 hours

**Estimated Effort**: 2 hours
**Testing Required**: Unit tests + manual security testing
```

### Step 6: Plan Remediation Strategy

**Develop actionable plan to fix identified vulnerabilities:**

#### Remediation Approaches

**1. Direct Upgrade (Preferred)**
```bash
# Python
pip install --upgrade package_name==secure_version

# JavaScript
npm update package_name@secure_version

# Java (in pom.xml)
<dependency>
    <groupId>com.example</groupId>
    <artifactId>package</artifactId>
    <version>secure_version</version>
</dependency>

# C#
dotnet add package PackageName --version secure_version

# Go
go get package@secure_version
```

**2. Transitive Dependency Override**

When vulnerable package is an indirect dependency:

**Python** (requirements.txt):
```
# Force secure version of transitive dependency
urllib3>=2.0.0  # Even if another package requires older version
```

**JavaScript** (package.json):
```json
{
  "overrides": {
    "vulnerable-package": "^secure-version"
  }
}
```

**Java** (pom.xml):
```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>com.example</groupId>
      <artifactId>vulnerable-package</artifactId>
      <version>secure-version</version>
    </dependency>
  </dependencies>
</dependencyManagement>
```

**3. Find Alternative Package**

When no secure version exists:

- Search for actively maintained alternatives

- Compare features and migration effort

- Verify alternative doesn't have same issues

**4. Patch or Fork**

Last resort for abandoned packages:

- Fork repository

- Apply security patch

- Use forked version (document thoroughly)

**5. Remove Dependency**

If not critical:

- Implement functionality yourself

- Use standard library alternative

- Reconsider if feature is necessary

#### Remediation Roadmap Template

```markdown
# Dependency Vulnerability Remediation Roadmap

**Project**: [Name]
**Audit Date**: [Date]
**Total Vulnerabilities**: [Count]

## Immediate (This Week) - P0

### 1. CVE-2023-XXXXX - lodash (Critical, CVSS 9.8)
- **Action**: Upgrade lodash 4.17.15 → 4.17.21

- **Impact**: No breaking changes expected

- **Testing**: Unit tests + security regression test

- **Effort**: 2 hours

- **Owner**: Security Team

- **Status**: 🔴 Not Started

### 2. CVE-2023-YYYYY - requests (High, CVSS 8.1)
- **Action**: Upgrade requests 2.25.0 → 2.31.0

- **Impact**: Minor API changes in edge cases

- **Testing**: Integration test suite

- **Effort**: 4 hours

- **Owner**: Backend Team

- **Status**: 🔴 Not Started

## Urgent (This Sprint) - P1

### 3. CVE-2023-ZZZZZ - jackson-databind (High, CVSS 7.5)
- **Action**: Upgrade jackson-databind 2.12.0 → 2.15.2

- **Impact**: Review deserialization patterns

- **Testing**: Full API test suite

- **Effort**: 8 hours

- **Owner**: API Team

- **Status**: 🔴 Not Started

## Planned (Next Sprint) - P2

### 4. Multiple outdated packages (Medium risk)
- **Action**: Upgrade 12 outdated packages

- **Impact**: Minimal, mostly security patches

- **Testing**: Automated test suite

- **Effort**: 1 day

- **Owner**: DevOps Team

- **Status**: 🔴 Not Started

## Monitoring (Continuous)

### 5. Enable automated dependency scanning
- **Action**: Integrate Snyk/Dependabot into CI/CD

- **Impact**: Early detection of new vulnerabilities

- **Effort**: 4 hours setup

- **Owner**: DevOps Team

- **Status**: 🔴 Not Started

## Testing Protocol for Upgrades

**For Each Remediation**:

1. Create feature branch

2. Update dependency version

3. Run full test suite locally

4. Manual testing of affected features

5. Security regression test (verify fix)

6. Code review

7. Deploy to staging

8. Run production-like tests

9. Monitor for 24 hours

10. Deploy to production

11. Post-deployment monitoring

## Rollback Plan

**If Issues Arise**:

1. Immediately rollback to previous version

2. Document issue in ticket

3. Investigate root cause

4. Consider alternative remediation

5. Update roadmap with new approach
```

### Step 7: Automate Dependency Scanning in CI/CD

**Integrate security scanning into continuous integration:**

#### GitHub Actions Integration

```yaml
# .github/workflows/dependency-scan.yml
name: Dependency Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:

    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  security-scan:
    runs-on: ubuntu-latest

    steps:

      - uses: actions/checkout@v3

      # Python Projects
      - name: Set up Python
        if: hashFiles('requirements.txt') != ''
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install pip-audit
        if: hashFiles('requirements.txt') != ''
        run: pip install pip-audit

      - name: Run pip-audit
        if: hashFiles('requirements.txt') != ''
        run: |
          pip-audit --desc --format json --output pip-audit-report.json
          pip-audit
        continue-on-error: true

      # JavaScript Projects
      - name: Set up Node.js
        if: hashFiles('package.json') != ''
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Run npm audit
        if: hashFiles('package.json') != ''
        run: |
          npm audit --json > npm-audit.json
          npm audit
        continue-on-error: true

      # Snyk Scan (Multi-language)
      - name: Run Snyk
        uses: snyk/actions@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          command: test
          args: --severity-threshold=high --json-file-output=snyk-report.json
        continue-on-error: true

      # Upload Results
      - name: Upload Security Reports
        uses: actions/upload-artifact@v3
        with:
          name: security-scan-reports
          path: |
            *-audit-report.json
            snyk-report.json

      # Fail Build on Critical Issues
      - name: Check for Critical Vulnerabilities
        run: |
          # Parse JSON reports and fail if critical issues found
          python scripts/check_critical_vulns.py
```

#### GitLab CI Integration

```yaml
# .gitlab-ci.yml
stages:

  - security

dependency-scan:
  stage: security
  image: python:3.11
  script:

    - pip install pip-audit safety

    - pip-audit --desc --format json --output pip-audit-report.json || true

    - safety check --json --output safety-report.json || true
  artifacts:
    reports:
      dependency_scanning: pip-audit-report.json
    paths:

      - pip-audit-report.json

      - safety-report.json
    expire_in: 30 days
  only:

    - merge_requests

    - main

npm-security-scan:
  stage: security
  image: node:18
  script:

    - npm audit --json > npm-audit-report.json || true
  artifacts:
    paths:

      - npm-audit-report.json
    expire_in: 30 days
  only:

    - merge_requests

    - main
```

#### Jenkins Pipeline Integration

```groovy
// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('Dependency Security Scan') {
            parallel {
                stage('Python Dependencies') {
                    when {
                        expression { fileExists('requirements.txt') }
                    }
                    steps {
                        sh '''
                            pip install pip-audit
                            pip-audit --desc --format json --output pip-audit-report.json
                        '''
                    }
                }

                stage('JavaScript Dependencies') {
                    when {
                        expression { fileExists('package.json') }
                    }
                    steps {
                        sh '''
                            npm audit --json > npm-audit-report.json
                        '''
                    }
                }

                stage('Java Dependencies') {
                    when {
                        expression { fileExists('pom.xml') }
                    }
                    steps {
                        sh '''
                            mvn dependency-check:check
                        '''
                    }
                }
            }
        }

        stage('Evaluate Results') {
            steps {
                script {
                    def criticalCount = sh(
                        script: "python scripts/count_critical.py",
                        returnStdout: true
                    ).trim().toInteger()

                    if (criticalCount > 0) {
                        error("Found ${criticalCount} critical vulnerabilities!")
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '*-report.json', allowEmptyArchive: true
            publishHTML([
                reportName: 'Dependency Security Report',
                reportDir: 'target',
                reportFiles: 'dependency-check-report.html'
            ])
        }
    }
}
```

#### Dependabot/Renovate Configuration

**Dependabot** (GitHub):
```yaml
# .github/dependabot.yml
version: 2
updates:
  # Python
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:

      - "security-team"
    labels:

      - "dependencies"

      - "security"

  # JavaScript
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  # Java
  - package-ecosystem: "maven"
    directory: "/"
    schedule:
      interval: "weekly"
```

**Renovate** (Multi-platform):
```json
{
  "extends": ["config:base"],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"]
  },
  "packageRules": [
    {
      "matchUpdateTypes": ["major"],
      "automerge": false
    },
    {
      "matchUpdateTypes": ["minor", "patch"],
      "matchCurrentVersion": "!/^0/",
      "automerge": true
    }
  ],
  "schedule": ["before 6am on monday"],
  "timezone": "UTC"
}
```

### Step 8: Generate Comprehensive Audit Report

**Create detailed report documenting findings and recommendations:**

```markdown
# Dependency Security Audit Report

**Project**: [Project Name]
**Audit Date**: [YYYY-MM-DD]
**Auditor**: [Name]
**Next Audit**: [YYYY-MM-DD]

## Executive Summary

- **Total Dependencies**: [Direct: X, Transitive: Y, Total: Z]

- **Vulnerabilities Found**: [Count]

  - Critical: [Count] (CVSS 9.0-10.0)

  - High: [Count] (CVSS 7.0-8.9)

  - Medium: [Count] (CVSS 4.0-6.9)

  - Low: [Count] (CVSS 0.1-3.9)

- **License Issues**: [Count]

- **Outdated Packages**: [Count with security patches]

- **Risk Rating**: [Critical / High / Medium / Low]

## Detailed Findings

### Critical Vulnerabilities (P0) - Immediate Action Required

#### 1. CVE-2023-XXXXX - Remote Code Execution in lodash

**Package**: lodash
**Current Version**: 4.17.15
**Fixed Version**: 4.17.21
**CVSS Score**: 9.8 (Critical)
**CWE**: CWE-1321 (Improperly Controlled Modification of Object Prototype)

**Description**:
Prototype pollution vulnerability allows remote code execution via template function.

**Exploit Status**: Public exploit available, actively exploited in the wild

**Affected Code Locations**:

- `src/api/users.js:45` - User input processed with lodash.template

- `src/utils/formatter.js:120` - Server-side template rendering

**Impact**:

- Remote attackers can execute arbitrary code

- Full system compromise possible

- Customer data exposure risk

**Remediation**:
```bash
npm update lodash@4.17.21
```

**Testing Requirements**:

- Verify all lodash.template uses

- Security regression test

- Full integration test suite

**Estimated Effort**: 2 hours
**Deadline**: Within 24 hours

---

### High Priority Vulnerabilities (P1) - Urgent

[Similar detailed entries for each high-priority vulnerability]

---

### Medium Priority Vulnerabilities (P2) - Plan Remediation

[Summarized list with key details]

---

### Low Priority Vulnerabilities (P3) - Address When Possible

[Brief list with minimal details]

---

## Dependency Inventory

### Direct Dependencies

| Package | Version | Latest | Vulnerabilities | License | Status |
|---------|---------|--------|-----------------|---------|--------|
| requests | 2.25.0 | 2.31.0 | 1 High | Apache-2.0 | ⚠️ Update |
| flask | 2.0.1 | 2.3.3 | 0 | BSD-3-Clause | ✅ OK |
| sqlalchemy | 1.4.20 | 2.0.21 | 0 | MIT | ⚠️ Major update available |

### Transitive Dependencies with Vulnerabilities

| Package | Via | Version | CVE | CVSS | Fix |
|---------|-----|---------|-----|------|-----|
| urllib3 | requests | 1.26.0 | CVE-2023-43804 | 8.6 | 1.26.17 |

## License Compliance

### License Distribution

- MIT: 45 packages (68%)

- Apache-2.0: 12 packages (18%)

- BSD-3-Clause: 8 packages (12%)

- ISC: 1 package (1.5%)

### License Issues

**None found** - All dependencies have compatible licenses for commercial use.

OR

**Issues Identified**:

1. **GPL-3.0 Dependency**: `package-name@1.0.0`

   - Incompatible with proprietary project license

   - **Recommendation**: Replace with MIT-licensed alternative

## Software Bill of Materials (SBOM)

**Format**: CycloneDX 1.5
**File**: `sbom.json`
**Generated**: [Date]

SBOM includes:

- All direct and transitive dependencies

- Version information

- License data

- Vulnerability mappings

- Component hashes

**SBOM Location**: Attached as `sbom.json`

## Outdated Dependencies

### Security Patches Available

| Package | Current | Latest | Security Fixes | Priority |
|---------|---------|--------|----------------|----------|
| requests | 2.25.0 | 2.31.0 | 3 CVEs fixed | High |
| urllib3 | 1.26.0 | 2.0.4 | 5 CVEs fixed | High |

### Major Version Updates Available

| Package | Current | Latest | Breaking Changes | Recommendation |
|---------|---------|--------|------------------|----------------|
| sqlalchemy | 1.4.20 | 2.0.21 | Yes (API changes) | Plan migration |

## Remediation Roadmap

### Phase 1: Critical (This Week)
- [ ] Fix CVE-2023-XXXXX (lodash) - 2 hours

- [ ] Fix CVE-2023-YYYYY (requests) - 4 hours

- [ ] **Total Effort**: 6 hours

- [ ] **Target Completion**: [Date]

### Phase 2: High Priority (This Sprint)
- [ ] Fix CVE-2023-ZZZZZ (urllib3) - 3 hours

- [ ] Replace GPL-licensed package - 8 hours

- [ ] **Total Effort**: 11 hours

- [ ] **Target Completion**: [Date]

### Phase 3: Medium Priority (Next Sprint)
- [ ] Update 12 outdated packages - 1 day

- [ ] Review and test all updates - 1 day

- [ ] **Total Effort**: 2 days

- [ ] **Target Completion**: [Date]

### Phase 4: Continuous Improvement
- [ ] Implement automated dependency scanning in CI/CD

- [ ] Enable Dependabot/Renovate

- [ ] Establish monthly audit cadence

- [ ] Create security dashboard

## Recommendations

### Immediate Actions
1. **Deploy Critical Fixes**: Address CVE-2023-XXXXX within 24 hours

2. **Block Vulnerable Versions**: Add policy to prevent deployment with critical CVEs

3. **Enable Monitoring**: Set up Snyk/Dependabot for continuous monitoring

### Short-Term Improvements
1. **Automate Scanning**: Integrate dependency checks into CI/CD pipeline

2. **Establish Policy**: Define acceptable risk levels and remediation SLAs

3. **Team Training**: Educate developers on secure dependency management

### Long-Term Strategy
1. **Supply Chain Security**: Implement comprehensive SBOM tracking

2. **Vendor Assessment**: Evaluate all third-party dependencies

3. **Dependency Minimization**: Regularly review and remove unnecessary dependencies

4. **Update Cadence**: Establish quarterly major update reviews

## Compliance Status

### SOC 2 Requirements
- ✅ Vulnerability scanning implemented

- ✅ SBOM available for all components

- ⚠️ Automated monitoring not yet enabled (in progress)

### ISO 27001 Requirements
- ✅ Asset inventory (dependency list) maintained

- ✅ Risk assessment completed

- ✅ Remediation plan documented

## Positive Findings

- Majority of dependencies use secure, well-maintained packages

- License compliance is generally good

- No malicious packages detected

- Development dependencies properly separated

## Appendix

### Tools Used
- pip-audit v2.6.1

- npm audit v9.8.1

- Snyk CLI v1.1200.0

- OWASP Dependency-Check v8.4.0

- govulncheck v1.0.1

### References
- [NVD - National Vulnerability Database](https://nvd.nist.gov/)

- [OSV - Open Source Vulnerabilities](https://osv.dev/)

- [Snyk Vulnerability Database](https://security.snyk.io/)

### Change Log
- [Date]: Initial audit completed

- [Date]: Remediation progress review

---

**Report Status**: Draft / Final
**Next Review**: [Date]
**Contact**: [Security Team Email]
```

## Multi-Language Support

This skill provides comprehensive dependency auditing for:

### Python Ecosystem
- **Package Managers**: pip, poetry, pipenv, conda

- **Scanning Tools**: pip-audit, safety, bandit

- **SBOM**: CycloneDX, SPDX

- **Automation**: GitHub Dependabot, Renovate

### JavaScript/TypeScript Ecosystem
- **Package Managers**: npm, yarn, pnpm

- **Scanning Tools**: npm audit, yarn audit, Snyk

- **SBOM**: CycloneDX for npm

- **Automation**: Dependabot, Renovate, Snyk

### Java Ecosystem
- **Build Tools**: Maven, Gradle

- **Scanning Tools**: OWASP Dependency-Check, Snyk

- **SBOM**: CycloneDX Maven/Gradle plugins

- **Automation**: Dependabot, Renovate

### C# / .NET Ecosystem
- **Package Manager**: NuGet

- **Scanning Tools**: dotnet CLI, dotnet-outdated

- **SBOM**: CycloneDX for .NET

- **Automation**: Dependabot, Renovate

### Go Ecosystem
- **Package Manager**: go modules

- **Scanning Tools**: govulncheck, Nancy

- **SBOM**: CycloneDX for Go

- **Automation**: Dependabot, Renovate

### C/C++ Ecosystem
- **Package Managers**: Conan, vcpkg, system packages

- **Scanning Tools**: cppcheck, flawfinder, Snyk

- **SBOM**: Manual SBOM generation

- **Automation**: Limited native support

## Common Pitfalls and Solutions

### Pitfall 1: Only Scanning Direct Dependencies

**Problem**: Transitive dependencies often contain vulnerabilities but are overlooked.

**Solution**: Always scan with `--include-transitive` or equivalent flag. Use dependency tree analysis.

```bash
# Python
pip-audit --desc  # Includes transitive by default

# JavaScript
npm audit  # Includes transitive by default

# C#
dotnet list package --vulnerable --include-transitive

# Java
mvn dependency:tree  # Analyze full tree
```

### Pitfall 2: Ignoring Low-Severity Vulnerabilities

**Problem**: Low-severity issues accumulate and may become critical in combination.

**Solution**: Address all vulnerabilities systematically. Low-severity issues are often easy fixes.

### Pitfall 3: Blocking on Unfixable Vulnerabilities

**Problem**: Some vulnerabilities have no fix available, blocking development.

**Solution**:

- Assess actual exploitability in your context

- Implement compensating controls (WAF, input validation)

- Consider alternative packages

- Document accepted risk with approval

```markdown
## Accepted Risk: CVE-2023-XXXXX

**Package**: legacy-library@1.0.0
**Vulnerability**: CVE-2023-XXXXX (CVSS 7.2)
**No Fix Available**: Package abandoned, no maintained alternatives

**Mitigations Implemented**:

- Library only used in isolated admin tool (not internet-facing)

- Input validation prevents exploit

- Network segmentation limits impact

- Monitoring alerts on suspicious activity

**Risk Acceptance**: Approved by Security Team
**Review Date**: [3 months from now]
**Owner**: [Name]
```

### Pitfall 4: Not Testing Dependency Updates

**Problem**: Updating dependencies breaks functionality without proper testing.

**Solution**: Always test dependency updates thoroughly before deploying.

```bash
# Create test branch
git checkout -b deps/security-updates

# Update dependencies
npm update package@version

# Run full test suite
npm test

# Manual testing
# Deploy to staging
# Monitor for 24 hours
# Deploy to production
```

### Pitfall 5: Manual-Only Auditing

**Problem**: Infrequent manual audits miss newly disclosed vulnerabilities.

**Solution**: Automate dependency scanning in CI/CD pipeline and enable continuous monitoring.

## Success Criteria

- [ ] All package managers identified and scanned

- [ ] Vulnerability scanning completed for all languages

- [ ] Transitive dependencies analyzed

- [ ] License compliance verified

- [ ] SBOM generated and stored

- [ ] Critical vulnerabilities prioritized with CVSS scores

- [ ] Remediation roadmap created with timelines

- [ ] Automated scanning integrated into CI/CD

- [ ] Continuous monitoring enabled (Dependabot/Snyk)

- [ ] Comprehensive audit report generated

- [ ] Team briefed on findings and remediation plan

- [ ] Follow-up audit scheduled

## Related Skills

### Security Skills
- [Code Review Security](../code-review-security/SKILL.md) - Application-level security audit

- [Pre-Commit Security Checklist](../pre-commit-checklist/SKILL.md) - Pre-commit security checks

### Code Quality Skills
- [Code Review Quality](../code-review-quality/SKILL.md) - Code maintainability review

## Additional Resources

### Vulnerability Databases
- [National Vulnerability Database (NVD)](https://nvd.nist.gov/)

- [OSV - Open Source Vulnerabilities](https://osv.dev/)

- [Snyk Vulnerability Database](https://security.snyk.io/)

- [GitHub Advisory Database](https://github.com/advisories)

### SBOM Standards
- [CycloneDX](https://cyclonedx.org/)

- [SPDX](https://spdx.dev/)

- [NTIA SBOM Guidelines](https://www.ntia.gov/sbom)

### Security Tools
- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)

- [Snyk](https://snyk.io/)

- [Dependabot](https://github.com/dependabot)

- [Renovate](https://renovatebot.com/)

### Compliance Frameworks
- [NIST Supply Chain Security](https://csrc.nist.gov/Projects/cyber-supply-chain-risk-management)

- [Executive Order 14028](https://www.nist.gov/itl/executive-order-14028-improving-nations-cybersecurity) (SBOM requirements)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: OWASP Dependency-Check, Snyk Security Best Practices, NIST Software Supply Chain Guidelines
