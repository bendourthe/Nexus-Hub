"""
Add YAML frontmatter to all templates.

This script adds comprehensive YAML frontmatter to all templates for searchability,
filtering, and automated catalog generation.

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# Template metadata mappings
DIFFICULTY_MAP = {
    'code_cleanup': 'intermediate',
    'code_review': {
        'context_analysis': 'intermediate',
        'code_quality': 'intermediate',
        'security_review': 'advanced',
        'performance_review': 'advanced',
        'testing_review': 'intermediate',
        'final_report': 'intermediate'
    },
    'test_development': {
        'test_structure': 'intermediate',
        'unit_tests': 'intermediate',
        'test_cases': 'intermediate',
        'mocks_fixtures': 'intermediate',
        'performance_testing': 'advanced',
        'code_coverage': 'intermediate',
        'maintenance_cicd': 'intermediate',
        'reward_hacking': 'advanced'
    },
    'documentation': 'beginner',
    'agent_prompts': 'intermediate'
}

TIME_ESTIMATES = {
    'code_cleanup': '4-8',
    'code_review': {
        'context_analysis': '2-3',
        'code_quality': '2-3',
        'security_review': '2-3',
        'performance_review': '2-3',
        'testing_review': '2',
        'final_report': '1'
    },
    'test_development': {
        'test_structure': '2-4',
        'unit_tests': '3-6',
        'test_cases': '4-8',
        'mocks_fixtures': '3-5',
        'performance_testing': '4-6',
        'code_coverage': '2-3',
        'maintenance_cicd': '3-5',
        'reward_hacking': '4-6'
    },
    'documentation': {
        'docstrings': '2-3',
        'comments': '1-2',
        'user_docs': '3-4',
        'technical_docs': '4-6',
        'api_docs': '4-8',
        'sbom': '2-3'
    },
    'agent_prompts': 'varies'
}

TOOL_VERSIONS = {
    'python': ['pytest (8.3.4+)', 'black (24.12.0)', 'mypy (1.13.0)', 'ruff'],
    'javascript': ['jest (29.7.0)', 'eslint (9.15.0)', 'prettier'],
    'java': ['junit (5.11.3)', 'maven', 'gradle'],
    'csharp': ['NUnit (4.2.2)', 'xUnit', 'MSTest'],
    'go': ['go test (1.23+)', 'testify'],
    'c': ['unity', 'cmocka', 'check'],
    'cpp': ['google test', 'catch2', 'boost.test']
}


def extract_language(filepath: Path) -> str:
    """Extract language from filename."""
    filename = filepath.stem.lower()

    for lang in ['python', 'javascript', 'java', 'csharp', 'go', 'cpp', 'c']:
        if filename.startswith(lang):
            return lang.capitalize() if lang != 'csharp' else 'C#'

    return 'Generic'


def extract_phase_info(filepath: Path) -> Tuple[str, Optional[int]]:
    """Extract phase name and number from filepath."""
    phase_map = {
        'test_structure': (1, 'Test Structure Setup'),
        'unit_tests': (2, 'Unit Tests'),
        'test_cases': (3, 'Test Cases Development'),
        'mocks_fixtures': (4, 'Mocks & Fixtures'),
        'performance_testing': (5, 'Performance Testing'),
        'code_coverage': (6, 'Code Coverage'),
        'maintenance_cicd': (7, 'Maintenance & CI/CD'),
        'reward_hacking': (8, 'Reward Hacking Validation'),
        'context_analysis': (1, 'Context Analysis'),
        'code_quality': (2, 'Code Quality'),
        'security_review': (3, 'Security Review'),
        'performance_review': (4, 'Performance Review'),
        'testing_review': (5, 'Testing Review'),
        'final_report': (6, 'Final Report')
    }

    parent_dir = filepath.parent.name
    if parent_dir in phase_map:
        num, name = phase_map[parent_dir]
        return name, num

    return filepath.parent.name.replace('_', ' ').title(), None


def get_difficulty(category: str, phase: Optional[str] = None) -> str:
    """Get difficulty level based on category and phase."""
    if isinstance(DIFFICULTY_MAP.get(category), dict) and phase:
        return DIFFICULTY_MAP[category].get(phase, 'intermediate')
    return DIFFICULTY_MAP.get(category, 'intermediate')


def get_time_estimate(category: str, phase: Optional[str] = None) -> str:
    """Get time estimate based on category and phase."""
    if isinstance(TIME_ESTIMATES.get(category), dict) and phase:
        return TIME_ESTIMATES[category].get(phase, '2-4')
    return TIME_ESTIMATES.get(category, '2-4')


def extract_prerequisites(filepath: Path, phase_number: Optional[int]) -> List[str]:
    """Determine prerequisites based on phase."""
    if not phase_number or phase_number == 1:
        return []

    category = filepath.parents[1].name
    parent_phase = filepath.parent.name

    # For testing phases
    if category == 'test_development':
        phases = ['test_structure', 'unit_tests', 'test_cases', 'mocks_fixtures',
                  'performance_testing', 'code_coverage', 'maintenance_cicd', 'reward_hacking']
        if phase_number > 1 and phase_number <= len(phases):
            prev_phase = phases[phase_number - 2]
            lang = extract_language(filepath).lower()
            if lang == 'c#':
                lang = 'csharp'
            return [f"test_development/{prev_phase}/{lang}_{prev_phase}.md"]

    # For code review phases
    if category == 'code_review' and phase_number > 1:
        phases = ['context_analysis', 'code_quality', 'security_review',
                  'performance_review', 'testing_review', 'final_report']
        if phase_number <= len(phases):
            prev_phase = phases[phase_number - 2]
            lang = extract_language(filepath).lower()
            if lang == 'c#':
                lang = 'csharp'
            return [f"code_review/{prev_phase}/{lang}_{prev_phase}.md"]

    return []


def extract_related_templates(filepath: Path, phase_number: Optional[int]) -> List[str]:
    """Determine related templates."""
    category = filepath.parents[1].name
    lang = extract_language(filepath).lower()
    if lang == 'c#':
        lang = 'csharp'

    related = []

    # For testing phases, suggest next phase
    if category == 'test_development' and phase_number and phase_number < 8:
        phases = ['test_structure', 'unit_tests', 'test_cases', 'mocks_fixtures',
                  'performance_testing', 'code_coverage', 'maintenance_cicd', 'reward_hacking']
        next_phase = phases[phase_number]
        related.append(f"test_development/{next_phase}/{lang}_{next_phase}.md")

    # For code review, suggest related review types
    if category == 'code_review':
        current_phase = filepath.parent.name
        review_phases = ['code_quality', 'security_review', 'performance_review', 'testing_review']
        for phase in review_phases:
            if phase != current_phase:
                related.append(f"code_review/{phase}/{lang}_{phase}.md")
                break

    return related


def generate_tags(filepath: Path, category: str, phase_name: str) -> List[str]:
    """Generate relevant tags for the template."""
    tags = [category.replace('_', '-')]

    # Add phase-specific tags
    if 'test' in phase_name.lower():
        tags.append('testing')
    if 'security' in phase_name.lower():
        tags.append('security')
    if 'performance' in phase_name.lower():
        tags.append('performance')
    if 'review' in phase_name.lower():
        tags.append('code-review')
    if 'cleanup' in filepath.name.lower():
        tags.append('refactoring')
    if 'documentation' in category:
        tags.append('documentation')

    # Add language
    lang = extract_language(filepath).lower()
    tags.append(lang)

    return tags


def generate_yaml_frontmatter(filepath: Path) -> str:
    """Generate YAML frontmatter for a template file."""
    # Extract metadata
    filename = filepath.stem
    language = extract_language(filepath)
    category = filepath.parents[1].name
    phase_name, phase_number = extract_phase_info(filepath)
    parent_phase = filepath.parent.name

    # Get computed values
    difficulty = get_difficulty(category, parent_phase)
    time_estimate = get_time_estimate(category, parent_phase)
    prerequisites = extract_prerequisites(filepath, phase_number)
    related = extract_related_templates(filepath, phase_number)
    tags = generate_tags(filepath, category, phase_name)

    # Get tools
    lang_key = language.lower()
    if lang_key == 'c#':
        lang_key = 'csharp'
    tools = TOOL_VERSIONS.get(lang_key, [])

    # Build YAML
    yaml_lines = [
        "---",
        f"template_id: {filename}",
        f"template_name: {phase_name} - {language}",
        "version: 1.0.0",
        f"last_updated: {datetime.now().strftime('%Y-%m-%d')}",
        f"language: {language}",
        f"category: {category}",
        f"phase: {parent_phase}"
    ]

    if phase_number:
        yaml_lines.append(f"phase_number: {phase_number}")

    yaml_lines.extend([
        f"difficulty: {difficulty}",
        f"estimated_time_hours: {time_estimate}"
    ])

    # Add prerequisites
    if prerequisites:
        yaml_lines.append("prerequisites:")
        for prereq in prerequisites:
            yaml_lines.append(f"  - {prereq}")
    else:
        yaml_lines.append("prerequisites: []")

    # Add related templates
    if related:
        yaml_lines.append("related_templates:")
        for rel in related:
            yaml_lines.append(f"  - {rel}")

    # Add tools
    if tools:
        yaml_lines.append("tools:")
        for tool in tools:
            yaml_lines.append(f"  - {tool}")

    # Add tags
    yaml_lines.append("tags:")
    for tag in tags:
        yaml_lines.append(f"  - {tag}")

    yaml_lines.append("---")
    yaml_lines.append("")

    return "\n".join(yaml_lines)


def add_frontmatter_to_file(filepath: Path) -> bool:
    """Add YAML frontmatter to a template file."""
    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if frontmatter already exists
    if content.startswith('---'):
        print(f"SKIP: Already has frontmatter: {filepath.name}")
        return False

    # Generate frontmatter
    frontmatter = generate_yaml_frontmatter(filepath)

    # Prepend frontmatter
    new_content = frontmatter + content

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"SUCCESS: Added frontmatter: {filepath.name}")
    return True


def find_all_templates(base_path: Path) -> List[Path]:
    """Find all markdown template files."""
    templates = []

    # Directories to scan
    scan_dirs = [
        'code_cleanup',
        'code_review',
        'test_development',
        'documentation',
        'agent_prompts'
    ]

    for dir_name in scan_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            # Find all .md files recursively
            for md_file in dir_path.rglob('*.md'):
                # Skip READMEs, CHANGELOGs, etc.
                if md_file.name not in ['README.md', 'CHANGELOG.md', 'DEVLOG.md',
                                         'TEMPLATE_FINDER.md', 'DECISION_TREES.md']:
                    templates.append(md_file)

    return sorted(templates)


def main():
    """Add YAML frontmatter to all templates."""
    base_path = Path(__file__).parent.parent

    print("=" * 80)
    print("Adding YAML Frontmatter to All Templates")
    print("=" * 80)
    print()

    # Find all templates
    print("Scanning for template files...")
    templates = find_all_templates(base_path)
    print(f"Found {len(templates)} template files to process")
    print()

    # Process each file
    updated = []
    skipped = []
    errors = []

    print("Processing files...")
    print("-" * 80)

    for filepath in templates:
        try:
            result = add_frontmatter_to_file(filepath)
            if result:
                updated.append(filepath)
            else:
                skipped.append(filepath)
        except Exception as e:
            errors.append((filepath, str(e)))
            print(f"ERROR: {filepath.name} - {str(e)}")

    # Print summary
    print()
    print("=" * 80)
    print("Summary:")
    print("-" * 80)
    print(f"  Total files scanned: {len(templates)}")
    print(f"  Files updated: {len(updated)}")
    print(f"  Files skipped (already have frontmatter): {len(skipped)}")
    print(f"  Files with errors: {len(errors)}")
    print("=" * 80)

    if updated:
        print()
        print("Updated files:")
        print("-" * 80)
        for filepath in updated[:10]:  # Show first 10
            print(f"  {filepath.relative_to(base_path)}")
        if len(updated) > 10:
            print(f"  ... and {len(updated) - 10} more")

    if errors:
        print()
        print("Files with errors:")
        print("-" * 80)
        for filepath, error in errors:
            print(f"  {filepath.name}: {error}")

    print()
    print("YAML frontmatter addition complete!")


if __name__ == '__main__':
    main()
