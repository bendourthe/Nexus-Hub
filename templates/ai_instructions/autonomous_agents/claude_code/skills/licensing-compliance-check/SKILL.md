---
template_id: SKILL
template_name: Licensing-Compliance-Check - Generic
version: 1.0.0
last_updated: 2025-12-03
language: Generic
category: skills
phase: licensing-compliance-check
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tags:

  - skills
  - generic
---
# licensing-compliance-check

---
category: security-quality
priority: MEDIUM
languages: [python, javascript, typescript, java, csharp, go, rust]
requires_user_input: true
estimated_duration: 1-3 hours
---

## Overview

Audit project dependencies for license compliance, identify potential legal issues, ensure compatibility between licenses, and generate compliance reports for legal review.

## When to Use This Skill

- Before releasing open-source software
- Corporate compliance requirements
- Adding new dependencies to project
- Legal review needed for distribution
- Mergers and acquisitions due diligence
- Contributing to projects with strict license policies

## Prerequisites

- Access to project dependency manifests
- Understanding of common open-source licenses
- Company license policy (if applicable)
- Legal team contact (for complex cases)

## Step-by-Step Instructions

### Phase 1: License Inventory

#### Step 1: Install License Scanning Tools

**Python:**

```bash
# Install license checking tools
pip install pip-licenses          # Generate license list
pip install licensecheck          # Verify licenses
pip install license-expression    # Parse license expressions
pip install python-license-check  # Compliance checking

# Install enhanced tools
pip install pip-audit             # Security + license audit
pip install pipdeptree            # Dependency tree with licenses
```

**JavaScript/TypeScript:**

```bash
# Install license checking tools
npm install -g license-checker    # Check licenses
npm install -g nlf                # Node License Finder
npm install -g legally            # Generate license reports
npm install -g license-report     # Detailed reports

# Install CI-friendly tools
npm install --save-dev license-checker-webpack-plugin
```

**Java:**

```bash
# Maven license plugin
# Add to pom.xml:
# <plugin>
#   <groupId>org.codehaus.mojo</groupId>
#   <artifactId>license-maven-plugin</artifactId>
# </plugin>

# Generate license report
mvn license:third-party-report
```

#### Step 2: Generate License Inventory

**Python:**

```bash
# Basic license list
pip-licenses --format=markdown --output-file=licenses.md

# Detailed JSON report
pip-licenses --format=json --with-urls --with-description > licenses.json

# Check specific formats
pip-licenses --format=csv --output-file=licenses.csv

# Example output:
# | Name          | Version | License                |
# |---------------|---------|------------------------|
# | requests      | 2.31.0  | Apache-2.0             |
# | numpy         | 1.24.0  | BSD-3-Clause           |
# | flask         | 3.0.0   | BSD-3-Clause           |
# | cryptography  | 41.0.0  | Apache-2.0 OR BSD-3-Clause |
```

**JavaScript:**

```bash
# Generate license report
license-checker --json --out licenses.json

# Summary format
license-checker --summary

# CSV export
license-checker --csv --out licenses.csv

# Example output:
# ├─ express@4.18.2
# │  ├─ licenses: MIT
# │  ├─ repository: https://github.com/expressjs/express
# │  ├─ publisher: TJ Holowaychuk
# │  └─ licenseFile: node_modules/express/LICENSE
```

**Cross-language with FOSSology:**

```bash
# Run FOSSology in Docker
docker run -p 8081:80 fossology/fossology

# Or use tern for container images
pip install tern
tern report -i myimage:latest -o license-report.json
```

#### Step 3: Categorize Licenses by Risk

```python
# license_analyzer.py
"""
Categorize licenses by compliance risk level.
"""
from typing import Dict, List, Set
import json

class LicenseAnalyzer:
    """Analyze and categorize software licenses."""

    # License categories
    PERMISSIVE = {
        'MIT', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0',
        'ISC', 'Unlicense', 'WTFPL', 'CC0-1.0'
    }

    WEAK_COPYLEFT = {
        'LGPL-2.1', 'LGPL-3.0', 'MPL-2.0', 'EPL-1.0', 'EPL-2.0',
        'CDDL-1.0', 'CDDL-1.1', 'CPL-1.0'
    }

    STRONG_COPYLEFT = {
        'GPL-2.0', 'GPL-3.0', 'AGPL-3.0', 'CC-BY-SA-4.0'
    }

    PROPRIETARY = {
        'Commercial', 'Proprietary', 'Custom', 'UNLICENSED'
    }

    def __init__(self, inventory_file: str):
        """Initialize with license inventory."""
        with open(inventory_file, 'r') as f:
            self.inventory = json.load(f)

    def categorize_licenses(self) -> Dict[str, List]:
        """Categorize all licenses by type."""
        categories = {
            'permissive': [],
            'weak_copyleft': [],
            'strong_copyleft': [],
            'proprietary': [],
            'unknown': [],
            'multiple': []
        }

        for package, info in self.inventory.items():
            license_str = info.get('licenses', 'UNKNOWN')

            # Handle multiple licenses (e.g., "Apache-2.0 OR MIT")
            if ' OR ' in license_str or ' AND ' in license_str:
                categories['multiple'].append({
                    'package': package,
                    'licenses': license_str,
                    'version': info.get('version')
                })
                continue

            # Categorize single license
            if license_str in self.PERMISSIVE:
                categories['permissive'].append(package)
            elif license_str in self.WEAK_COPYLEFT:
                categories['weak_copyleft'].append(package)
            elif license_str in self.STRONG_COPYLEFT:
                categories['strong_copyleft'].append(package)
            elif license_str in self.PROPRIETARY:
                categories['proprietary'].append(package)
            else:
                categories['unknown'].append({
                    'package': package,
                    'license': license_str
                })

        return categories

    def check_compatibility(self, project_license: str) -> Dict:
        """
        Check if dependencies are compatible with project license.

        Compatibility rules:
        - Permissive (MIT, BSD, Apache) can use anything except strong copyleft
        - Weak copyleft (LGPL, MPL) can use permissive and weak copyleft
        - Strong copyleft (GPL) can use everything (but makes project GPL)
        """
        categories = self.categorize_licenses()
        issues = []

        if project_license in self.PERMISSIVE:
            # Check for strong copyleft dependencies
            if categories['strong_copyleft']:
                issues.append({
                    'severity': 'HIGH',
                    'issue': 'Strong copyleft dependencies incompatible with permissive license',
                    'packages': categories['strong_copyleft'],
                    'recommendation': 'Remove GPL/AGPL dependencies or change project license'
                })

        elif project_license in self.WEAK_COPYLEFT:
            # Can use permissive and weak copyleft, not strong copyleft
            if categories['strong_copyleft']:
                issues.append({
                    'severity': 'HIGH',
                    'issue': 'Strong copyleft dependencies force GPL licensing',
                    'packages': categories['strong_copyleft'],
                    'recommendation': 'Remove or replace with LGPL alternatives'
                })

        elif project_license in self.STRONG_COPYLEFT:
            # GPL can use anything, but entire project becomes GPL
            issues.append({
                'severity': 'INFO',
                'issue': 'Project is strong copyleft - all code must be GPL-compatible',
                'recommendation': 'Ensure all contributors understand GPL obligations'
            })

        # Check for unknown licenses
        if categories['unknown']:
            issues.append({
                'severity': 'MEDIUM',
                'issue': 'Dependencies with unknown licenses',
                'packages': categories['unknown'],
                'recommendation': 'Manually verify these licenses'
            })

        # Check multiple license packages
        if categories['multiple']:
            issues.append({
                'severity': 'LOW',
                'issue': 'Dependencies with multiple license options',
                'packages': categories['multiple'],
                'recommendation': 'Choose compatible license option for each'
            })

        return {
            'compatible': len(issues) == 0 or all(i['severity'] == 'INFO' for i in issues),
            'issues': issues,
            'summary': {
                'permissive': len(categories['permissive']),
                'weak_copyleft': len(categories['weak_copyleft']),
                'strong_copyleft': len(categories['strong_copyleft']),
                'unknown': len(categories['unknown'])
            }
        }

    def generate_compliance_report(self, project_license: str, output_file: str):
        """Generate comprehensive compliance report."""
        categories = self.categorize_licenses()
        compatibility = self.check_compatibility(project_license)

        report = {
            'project_license': project_license,
            'date': '2025-10-21',
            'total_dependencies': len(self.inventory),
            'categories': categories,
            'compatibility_check': compatibility,
            'high_risk_packages': []
        }

        # Identify high-risk packages
        for pkg in categories.get('strong_copyleft', []):
            report['high_risk_packages'].append({
                'package': pkg,
                'risk': 'Strong copyleft - may require source code disclosure'
            })

        for item in categories.get('unknown', []):
            report['high_risk_packages'].append({
                'package': item['package'],
                'risk': 'Unknown license - legal review required'
            })

        # Write report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Print summary
        self._print_summary(report)

    def _print_summary(self, report: Dict):
        """Print report summary to console."""
        print("\n" + "="*60)
        print("LICENSE COMPLIANCE REPORT")
        print("="*60)
        print(f"\nProject License: {report['project_license']}")
        print(f"Total Dependencies: {report['total_dependencies']}")
        print("\nLicense Distribution:")
        print(f"  Permissive: {report['compatibility_check']['summary']['permissive']}")
        print(f"  Weak Copyleft: {report['compatibility_check']['summary']['weak_copyleft']}")
        print(f"  Strong Copyleft: {report['compatibility_check']['summary']['strong_copyleft']}")
        print(f"  Unknown: {report['compatibility_check']['summary']['unknown']}")

        if report['compatibility_check']['issues']:
            print("\n⚠️  COMPLIANCE ISSUES:")
            for issue in report['compatibility_check']['issues']:
                print(f"\n[{issue['severity']}] {issue['issue']}")
                if 'packages' in issue:
                    print(f"  Affected packages: {', '.join(str(p) for p in issue['packages'][:5])}")
                print(f"  Recommendation: {issue['recommendation']}")

        if report['high_risk_packages']:
            print("\n🚨 HIGH RISK PACKAGES:")
            for pkg in report['high_risk_packages'][:10]:
                print(f"  - {pkg['package']}: {pkg['risk']}")

        print("\n" + "="*60)

# Usage
if __name__ == '__main__':
    analyzer = LicenseAnalyzer('licenses.json')
    analyzer.generate_compliance_report('MIT', 'compliance_report.json')
```

### Phase 2: Compliance Rules

#### Step 4: Define Company License Policy

```yaml
# license-policy.yml
# Company license compliance policy

project_license: MIT

allowed_licenses:
  # Permissive licenses - always allowed
  permissive:

    - MIT
    - BSD-2-Clause
    - BSD-3-Clause
    - Apache-2.0
    - ISC
    - Unlicense
    - CC0-1.0

  # Weak copyleft - allowed with conditions
  weak_copyleft:

    - LGPL-2.1
    - LGPL-3.0
    - MPL-2.0
    - EPL-2.0
    conditions: "Dynamic linking only, no modification of LGPL code"

denied_licenses:
  # Strong copyleft - not compatible with MIT
  - GPL-2.0
  - GPL-3.0
  - AGPL-3.0
  - CC-BY-SA-4.0

  # Proprietary/unclear licenses
  - Commercial
  - Proprietary
  - Custom
  - UNLICENSED

requires_review:
  # Licenses requiring legal review
  - Artistic-2.0
  - OFL-1.1
  - CC-BY-4.0
  - Zlib

exceptions:
  # Approved exceptions (with justification)
  - package: readline
    license: GPL-3.0
    justification: "Used only in development, not distributed"
    approved_by: "legal-team"
    approved_date: "2025-01-15"

notifications:
  # Who to notify for license issues
  legal_team: legal@company.com
  engineering: eng-leads@company.com
  compliance_officer: compliance@company.com
```

#### Step 5: Automated Compliance Checking

```python
# check_compliance.py
"""
Automated license compliance checking against policy.
"""
import json
import yaml
from typing import Dict, List

class ComplianceChecker:
    """Check licenses against company policy."""

    def __init__(self, policy_file: str, inventory_file: str):
        """Initialize checker with policy and inventory."""
        with open(policy_file, 'r') as f:
            self.policy = yaml.safe_load(f)

        with open(inventory_file, 'r') as f:
            self.inventory = json.load(f)

    def check_all_packages(self) -> Dict:
        """Check all packages against policy."""
        results = {
            'compliant': [],
            'violations': [],
            'requires_review': [],
            'exceptions': []
        }

        allowed = set(
            self.policy['allowed_licenses']['permissive'] +
            self.policy['allowed_licenses']['weak_copyleft']
        )
        denied = set(self.policy['denied_licenses'])
        review_required = set(self.policy['requires_review'])

        # Check for approved exceptions
        exceptions_map = {
            exc['package']: exc
            for exc in self.policy.get('exceptions', [])
        }

        for package, info in self.inventory.items():
            license_str = info.get('licenses', 'UNKNOWN')

            # Check if package has approved exception
            if package in exceptions_map:
                results['exceptions'].append({
                    'package': package,
                    'license': license_str,
                    'exception': exceptions_map[package]
                })
                continue

            # Check compliance
            if license_str in denied:
                results['violations'].append({
                    'package': package,
                    'version': info.get('version'),
                    'license': license_str,
                    'severity': 'HIGH',
                    'reason': 'Denied license used'
                })
            elif license_str in review_required:
                results['requires_review'].append({
                    'package': package,
                    'version': info.get('version'),
                    'license': license_str
                })
            elif license_str in allowed:
                results['compliant'].append(package)
            elif license_str == 'UNKNOWN':
                results['violations'].append({
                    'package': package,
                    'version': info.get('version'),
                    'license': license_str,
                    'severity': 'MEDIUM',
                    'reason': 'License not identified'
                })
            else:
                results['requires_review'].append({
                    'package': package,
                    'version': info.get('version'),
                    'license': license_str
                })

        return results

    def generate_report(self) -> str:
        """Generate compliance report."""
        results = self.check_all_packages()

        report = []
        report.append("="*60)
        report.append("LICENSE COMPLIANCE CHECK")
        report.append("="*60)
        report.append(f"\nProject License: {self.policy['project_license']}")
        report.append(f"Total Packages: {len(self.inventory)}")
        report.append(f"Compliant: {len(results['compliant'])}")
        report.append(f"Violations: {len(results['violations'])}")
        report.append(f"Requires Review: {len(results['requires_review'])}")
        report.append(f"Approved Exceptions: {len(results['exceptions'])}")

        if results['violations']:
            report.append("\n🚨 LICENSE VIOLATIONS:")
            for violation in results['violations']:
                report.append(f"\n  [{violation['severity']}] {violation['package']} v{violation['version']}")
                report.append(f"    License: {violation['license']}")
                report.append(f"    Reason: {violation['reason']}")

        if results['requires_review']:
            report.append("\n⚠️  REQUIRES LEGAL REVIEW:")
            for item in results['requires_review']:
                report.append(f"  - {item['package']} v{item['version']} ({item['license']})")

        if results['exceptions']:
            report.append("\n✓ APPROVED EXCEPTIONS:")
            for exc in results['exceptions']:
                report.append(f"  - {exc['package']} ({exc['license']})")
                report.append(f"    Justification: {exc['exception']['justification']}")

        # Compliance status
        if results['violations']:
            report.append("\n❌ COMPLIANCE CHECK FAILED")
            report.append("\nAction Required:")
            report.append("1. Remove or replace packages with violations")
            report.append("2. Request exceptions from legal team")
            report.append(f"3. Contact: {self.policy['notifications']['legal_team']}")
        else:
            report.append("\n✅ COMPLIANCE CHECK PASSED")

        return "\n".join(report)

    def fail_on_violations(self) -> bool:
        """Return True if there are violations (for CI/CD)."""
        results = self.check_all_packages()
        return len(results['violations']) > 0

# Usage
if __name__ == '__main__':
    checker = ComplianceChecker('license-policy.yml', 'licenses.json')
    print(checker.generate_report())

    # Exit with error code if violations found (for CI)
    import sys
    if checker.fail_on_violations():
        sys.exit(1)
```

### Phase 3: CI/CD Integration

#### Step 6: Add License Checks to CI/CD

```yaml
# .github/workflows/license-check.yml
name: License Compliance

on:
  pull_request:
    paths:

      - 'requirements.txt'
      - 'package.json'
      - 'pom.xml'
  schedule:

    - cron: '0 0 * * 0'  # Weekly check

jobs:
  license-check:
    runs-on: ubuntu-latest
    steps:

    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install pip-licenses
        pip install -r requirements.txt

    - name: Generate license report
      run: |
        pip-licenses --format=json --with-urls > licenses.json

    - name: Check compliance
      run: |
        python check_compliance.py

    - name: Upload license report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: license-report
        path: |
          licenses.json
          compliance_report.json

    - name: Comment on PR
      if: failure() && github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: '❌ License compliance check failed. Please review the license report.'
          })
```

### Phase 4: Attribution and Notices

#### Step 7: Generate License Notices

```python
# generate_notices.py
"""
Generate license attribution notices for distribution.
"""
import json
from typing import Dict

class NoticeGenerator:
    """Generate third-party license notices."""

    def __init__(self, inventory_file: str):
        """Initialize with license inventory."""
        with open(inventory_file, 'r') as f:
            self.inventory = json.load(f)

    def generate_notice_file(self, output_file: str = 'NOTICE.txt'):
        """Generate NOTICE file for distribution."""
        lines = []

        lines.append("THIRD-PARTY SOFTWARE NOTICES AND INFORMATION")
        lines.append("=" * 60)
        lines.append("\nThis software incorporates components from the projects listed below.")
        lines.append("The original copyright notices and the licenses are provided below.\n")

        for package, info in sorted(self.inventory.items()):
            lines.append("\n" + "-" * 60)
            lines.append(f"Package: {package}")
            lines.append(f"Version: {info.get('version', 'unknown')}")
            lines.append(f"License: {info.get('licenses', 'UNKNOWN')}")

            if 'url' in info:
                lines.append(f"Homepage: {info['url']}")

            if 'licenseFile' in info:
                lines.append(f"\nLicense Text:")
                try:
                    with open(info['licenseFile'], 'r') as f:
                        license_text = f.read()
                        lines.append(license_text)
                except Exception as e:
                    lines.append(f"[License file could not be read: {e}]")

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✓ Generated {output_file}")
        print(f"  Included {len(self.inventory)} third-party components")

    def generate_html_attribution(self, output_file: str = 'licenses.html'):
        """Generate HTML page with license attributions."""
        html = [
            "<!DOCTYPE html>",
            "<html><head>",
            "<title>Third-Party Licenses</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; }",
            ".package { margin: 20px 0; padding: 15px; border-left: 3px solid #007bff; background: #f8f9fa; }",
            ".package-name { font-size: 1.2em; font-weight: bold; }",
            ".license { margin-top: 10px; font-family: monospace; white-space: pre-wrap; }",
            "</style>",
            "</head><body>",
            "<h1>Third-Party Software Licenses</h1>"
        ]

        for package, info in sorted(self.inventory.items()):
            html.append(f'<div class="package">')
            html.append(f'  <div class="package-name">{package}</div>')
            html.append(f'  <div>Version: {info.get("version", "unknown")}</div>')
            html.append(f'  <div>License: {info.get("licenses", "UNKNOWN")}</div>')

            if 'url' in info:
                html.append(f'  <div>Homepage: <a href="{info["url"]}">{info["url"]}</a></div>')

            html.append('</div>')

        html.append("</body></html>")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))

        print(f"✓ Generated {output_file}")

# Usage
if __name__ == '__main__':
    generator = NoticeGenerator('licenses.json')
    generator.generate_notice_file('NOTICE.txt')
    generator.generate_html_attribution('licenses.html')
```

## Expected Outcomes

After completing this compliance check:

1. **Complete license inventory**
   - All dependencies catalogued
   - License types identified
   - Risk levels assessed

2. **Compliance verification**
   - Compatible with project license
   - No legal issues identified
   - Proper attribution included

3. **Automated monitoring**
   - CI/CD checks in place
   - Policy enforcement automated
   - Regular audits scheduled

4. **Legal documentation**
   - NOTICE file generated
   - Attribution page created
   - Compliance report available

## Success Criteria

- [ ] All dependency licenses identified
- [ ] License compatibility verified
- [ ] No high-risk violations present
- [ ] Company policy compliance confirmed
- [ ] NOTICE file generated
- [ ] Attribution documentation complete
- [ ] CI/CD checks implemented
- [ ] Legal team review completed (if required)

## Common Pitfalls

1. **Ignoring transitive dependencies**
   - Check entire dependency tree, not just direct deps

2. **Assuming compatibility**
   - Verify each license combination carefully

3. **Missing attribution**
   - Include proper notices for all third-party code

4. **Not updating regularly**
   - Re-check when dependencies change

## Related Skills

- **dependency-upgrade**: Upgrade dependencies safely
- **setup-python-project**: Initialize projects with proper licensing
- **code-review**: Review license compliance in code reviews

## Additional Resources

### License Databases
- [SPDX License List](https://spdx.org/licenses/)
- [ChooseALicense.com](https://choosealicense.com/)
- [TLDRLegal](https://tldrlegal.com/)

### Tools
- **Python**: pip-licenses, licensecheck
- **JavaScript**: license-checker, licensee
- **Java**: license-maven-plugin
- **Multi-language**: FOSSology, ScanCode

### License Compatibility
- [GPL Compatibility Matrix](https://www.gnu.org/licenses/gpl-faq.html#AllCompatibility)
- [Apache-GPLv3 Compatibility](https://www.apache.org/licenses/GPL-compatibility.html)

---

**Note**: This skill provides guidance but does not constitute legal advice. Consult with legal counsel for specific compliance questions.
