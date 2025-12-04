"""
Lint all templates for consistency and completeness.

Validates:
1. YAML frontmatter present and valid
2. OUTPUT_DIR uses ${OUTPUT_DIR} (not {OUTPUT_DIR})
3. Tool versions are current (2025)
4. Required sections present
5. Language-specific requirements met

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
import re
from pathlib import Path
from typing import List, Dict, Tuple


# Current tool versions (2025)
CURRENT_VERSIONS = {
    'black': '24.12.0',
    'flake8': '7.1.1',
    'mypy': '1.13.0',
    'pytest': '8.3.4',
    'jest': '29.7.0',
    'eslint': '9.15.0',
    'junit': '5.11.3',
    'nunit': '4.2.2',
    'go': '1.23'
}

# Outdated versions to flag
OUTDATED_PATTERNS = [
    r'black.*24\.1\.1',
    r'flake8.*7\.0\.0',
    r'mypy.*v?1\.8\.0',
    r'pytest.*7\.',
    r'jest.*28\.',
    r'eslint.*8\.',
    r'junit.*5\.9',
    r'nunit.*3\.13',
    r'Go 1\.20',
    r'go 1\.20'
]


class TemplateLinter:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.errors = []
        self.warnings = []
        self.info = []

    def lint_all_templates(self) -> Dict:
        """Lint all templates and return results."""
        templates = self._find_all_templates()

        print(f"Linting {len(templates)} templates...")
        print()

        for template in templates:
            self.lint_template(template)

        return {
            'total_templates': len(templates),
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'success': len(self.errors) == 0
        }

    def lint_template(self, filepath: Path):
        """Lint a single template file."""
        rel_path = filepath.relative_to(self.base_path)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"{rel_path}: Cannot read file - {e}")
            return

        # Check 1: YAML frontmatter
        self._check_yaml_frontmatter(filepath, rel_path, content)

        # Check 2: OUTPUT_DIR pattern
        self._check_output_dir_pattern(rel_path, content)

        # Check 3: Outdated tool versions
        self._check_tool_versions(rel_path, content)

        # Check 4: Required sections (based on category)
        self._check_required_sections(filepath, rel_path, content)

        # Check 5: Language-specific checks
        self._check_language_specifics(filepath, rel_path, content)

    def _check_yaml_frontmatter(self, filepath: Path, rel_path: Path, content: str):
        """Check YAML frontmatter presence and validity."""
        if not content.startswith('---'):
            self.errors.append(f"{rel_path}: Missing YAML frontmatter")
            return

        # Extract frontmatter
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            self.errors.append(f"{rel_path}: Invalid YAML frontmatter format")
            return

        frontmatter = match.group(1)

        # Check required fields
        required_fields = [
            'template_id',
            'template_name',
            'version',
            'last_updated',
            'language',
            'category',
            'difficulty',
            'estimated_time_hours'
        ]

        for field in required_fields:
            if f"{field}:" not in frontmatter:
                self.warnings.append(f"{rel_path}: Missing frontmatter field '{field}'")

        # Check version format
        if 'version:' in frontmatter:
            version_match = re.search(r'version:\s*(\S+)', frontmatter)
            if version_match:
                version = version_match.group(1)
                if not re.match(r'\d+\.\d+\.\d+', version):
                    self.warnings.append(f"{rel_path}: Invalid version format '{version}' (use semver)")

        # Check date format
        if 'last_updated:' in frontmatter:
            date_match = re.search(r'last_updated:\s*(\S+)', frontmatter)
            if date_match:
                date = date_match.group(1)
                if not re.match(r'\d{4}-\d{2}-\d{2}', date):
                    self.warnings.append(f"{rel_path}: Invalid date format '{date}' (use YYYY-MM-DD)")

    def _check_output_dir_pattern(self, rel_path: Path, content: str):
        """Check OUTPUT_DIR uses correct bash syntax."""
        # Find {OUTPUT_DIR} without $ prefix
        if re.search(r'(?<!\$)\{OUTPUT_DIR\}', content):
            self.warnings.append(f"{rel_path}: Use ${{OUTPUT_DIR}} not {{OUTPUT_DIR}}")

    def _check_tool_versions(self, rel_path: Path, content: str):
        """Check for outdated tool versions."""
        for pattern in OUTDATED_PATTERNS:
            if re.search(pattern, content):
                self.warnings.append(f"{rel_path}: Outdated tool version detected: {pattern}")

    def _check_required_sections(self, filepath: Path, rel_path: Path, content: str):
        """Check for required sections based on template type."""
        category = filepath.parents[1].name if len(filepath.parents) > 1 else ''

        # Common required sections
        common_sections = ['##']  # At least one section header

        # Category-specific requirements
        if category == 'code_review':
            required = ['## Objective', '## Review Checklist', '## Prompt Template']
            for section in required:
                if section not in content:
                    self.warnings.append(f"{rel_path}: Missing required section '{section}'")

        elif category == 'test_development':
            required = ['## Objective', '## Prompt Template', '## Success Criteria']
            for section in required:
                if section not in content:
                    self.warnings.append(f"{rel_path}: Missing required section '{section}'")

        elif category == 'code_cleanup':
            required = ['## Objective', '## Review Checklist', '## Prompt Template']
            for section in required:
                if section not in content:
                    self.warnings.append(f"{rel_path}: Missing required section '{section}'")

        elif category == 'documentation':
            required = ['## Objective', '## Prompt Template']
            for section in required:
                if section not in content:
                    self.warnings.append(f"{rel_path}: Missing required section '{section}'")

        # Check for at least one section
        if '##' not in content:
            self.errors.append(f"{rel_path}: No section headers found (must have ## headers)")

    def _check_language_specifics(self, filepath: Path, rel_path: Path, content: str):
        """Check language-specific requirements."""
        filename = filepath.name.lower()

        # Python templates
        if filename.startswith('python'):
            # Should mention pytest, black, or mypy
            tools = ['pytest', 'black', 'mypy', 'ruff']
            if not any(tool in content.lower() for tool in tools):
                self.info.append(f"{rel_path}: Python template doesn't mention common tools")

        # JavaScript templates
        elif filename.startswith('javascript'):
            tools = ['jest', 'eslint', 'npm', 'node']
            if not any(tool in content.lower() for tool in tools):
                self.info.append(f"{rel_path}: JavaScript template doesn't mention common tools")

        # Java templates
        elif filename.startswith('java'):
            tools = ['junit', 'maven', 'gradle']
            if not any(tool in content.lower() for tool in tools):
                self.info.append(f"{rel_path}: Java template doesn't mention common tools")

    def _find_all_templates(self) -> List[Path]:
        """Find all template markdown files."""
        templates = []
        scan_dirs = [
            'code_cleanup',
            'code_review',
            'test_development',
            'documentation',
            'agent_prompts'
        ]

        for dir_name in scan_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                for md_file in dir_path.rglob('*.md'):
                    if md_file.name not in ['README.md', 'CHANGELOG.md', 'DEVLOG.md',
                                             'TEMPLATE_FINDER.md', 'DECISION_TREES.md']:
                        templates.append(md_file)

        return sorted(templates)


def main():
    """Run template linter."""
    base_path = Path(__file__).parent.parent
    linter = TemplateLinter(base_path)

    print("=" * 80)
    print("Template Linter - Validating All Templates")
    print("=" * 80)
    print()

    results = linter.lint_all_templates()

    # Print results
    print("=" * 80)
    print("Linting Results")
    print("=" * 80)
    print(f"Templates scanned: {results['total_templates']}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")
    print(f"Info: {len(results['info'])}")
    print()

    if results['errors']:
        print("=" * 80)
        print("ERRORS (Must Fix)")
        print("=" * 80)
        for error in results['errors'][:20]:  # Show first 20
            print(f"  {error}")
        if len(results['errors']) > 20:
            print(f"  ... and {len(results['errors']) - 20} more")
        print()

    if results['warnings']:
        print("=" * 80)
        print("WARNINGS (Should Fix)")
        print("=" * 80)
        for warning in results['warnings'][:20]:  # Show first 20
            print(f"  {warning}")
        if len(results['warnings']) > 20:
            print(f"  ... and {len(results['warnings']) - 20} more")
        print()

    if results['info']:
        print("=" * 80)
        print("INFO (Nice to Have)")
        print("=" * 80)
        for info in results['info'][:10]:  # Show first 10
            print(f"  {info}")
        if len(results['info']) > 10:
            print(f"  ... and {len(results['info']) - 10} more")
        print()

    print("=" * 80)
    if results['success']:
        print("SUCCESS: All templates passed linting (no errors)")
    else:
        print("FAILED: Templates have errors that must be fixed")
    print("=" * 80)

    return 0 if results['success'] else 1


if __name__ == '__main__':
    exit(main())
