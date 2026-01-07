"""
Generate templates.json metadata catalog.

This script scans all templates with YAML frontmatter and generates a searchable
JSON catalog for use in web interfaces and CLI tools.

Authors:
    - Benjamin Dourthe (benjamin.dourthe@gmail.com)
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def extract_yaml_frontmatter(filepath: Path) -> Dict:
    """Extract YAML frontmatter from template file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match YAML frontmatter
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return {}

        # Parse YAML (basic parsing)
        frontmatter = {}
        current_list = None
        for line in match.group(1).split('\n'):
            line = line.strip()
            if not line:
                continue

            # Handle list items
            if line.startswith('- '):
                if current_list and current_list in frontmatter:
                    frontmatter[current_list].append(line[2:].strip())
                continue

            # Handle key-value pairs
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Check if this starts a list
                if not value:
                    current_list = key
                    frontmatter[key] = []
                else:
                    current_list = None
                    frontmatter[key] = value

        return frontmatter
    except Exception as e:
        print(f"Warning: Could not parse {filepath.name}: {e}")
        return {}


def scan_templates(base_path: Path) -> List[Dict]:
    """Scan all template directories and extract metadata."""
    templates = []
    categories = [
        'templates/development/codebase-cleanup',
        'templates/development/codebase-review',
        'templates/development/tests-generation',
        'templates/development/documentation-generation',
        'templates/development/compliance-review',
        'templates/ai-instructions'
    ]

    for category in categories:
        category_path = base_path / category
        if not category_path.exists():
            continue

        # Recursively find all .md files
        for md_file in category_path.rglob('*.md'):
            if md_file.name in ['README.md', 'CHANGELOG.md', 'DEVLOG.md',
                                 'TEMPLATE_FINDER.md', 'DECISION_TREES.md']:
                continue

            metadata = extract_yaml_frontmatter(md_file)
            if metadata:
                # Add file path and size
                metadata['file_path'] = str(md_file.relative_to(base_path)).replace('\\', '/')
                metadata['file_size_kb'] = round(md_file.stat().st_size / 1024, 1)

                # Extract description from file (first paragraph after frontmatter)
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Remove frontmatter
                        content = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
                        # Get first paragraph
                        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.startswith('#')]
                        if paragraphs:
                            description = paragraphs[0][:200]  # First 200 chars
                            if len(paragraphs[0]) > 200:
                                description += '...'
                            metadata['description'] = description
                except:
                    pass

                templates.append(metadata)

    return templates


def generate_catalog(templates: List[Dict]) -> Dict:
    """Generate comprehensive catalog with statistics."""
    catalog = {
        'version': '0.2.9',
        'generated_date': datetime.now().strftime('%Y-%m-%d'),
        'total_templates': len(templates),
        'templates': templates,
        'statistics': {
            'by_language': {},
            'by_category': {},
            'by_difficulty': {},
            'by_phase': {},
            'total_estimated_hours': 0
        },
        'categories': {
            'code_cleanup': 'Remove dead code, duplication, and legacy patterns',
            'code_review': '6-phase comprehensive code review methodology',
            'test_development': '8-phase testing methodology from structure to validation',
            'documentation': 'Generate docstrings, comments, API docs, and technical documentation',
            'agent_prompts': 'System prompts for AI coding assistants'
        },
        'languages': ['Python', 'JavaScript', 'Java', 'C#', 'Go', 'C', 'C++']
    }

    # Calculate statistics
    for template in templates:
        # Language stats
        lang = template.get('language', 'unknown')
        catalog['statistics']['by_language'][lang] = \
            catalog['statistics']['by_language'].get(lang, 0) + 1

        # Category stats
        cat = template.get('category', 'unknown')
        catalog['statistics']['by_category'][cat] = \
            catalog['statistics']['by_category'].get(cat, 0) + 1

        # Difficulty stats
        diff = template.get('difficulty', 'unknown')
        catalog['statistics']['by_difficulty'][diff] = \
            catalog['statistics']['by_difficulty'].get(diff, 0) + 1

        # Phase stats
        phase = template.get('phase', 'none')
        catalog['statistics']['by_phase'][phase] = \
            catalog['statistics']['by_phase'].get(phase, 0) + 1

        # Time estimation (parse "2-4" format)
        time_est = template.get('estimated_time_hours', '0')
        try:
            if '-' in str(time_est):
                low, high = map(float, str(time_est).split('-'))
                avg = (low + high) / 2
            elif str(time_est).replace('.', '').isdigit():
                avg = float(time_est)
            else:
                avg = 3.0  # Default
            catalog['statistics']['total_estimated_hours'] += avg
        except:
            pass

    # Round total hours
    catalog['statistics']['total_estimated_hours'] = round(
        catalog['statistics']['total_estimated_hours'], 1
    )

    return catalog


def main():
    """Generate templates.json catalog."""
    base_path = Path(__file__).parent.parent.parent

    print("=" * 80)
    print("Building Templates Catalog")
    print("=" * 80)
    print()

    print("Scanning templates...")
    templates = scan_templates(base_path)
    print(f"Found {len(templates)} templates with YAML frontmatter")
    print()

    print("Generating catalog with statistics...")
    catalog = generate_catalog(templates)

    # Save to repository root
    output_path = base_path / 'templates.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Catalog generated: {output_path}")
    print()

    # Print statistics
    print("=" * 80)
    print("Catalog Statistics")
    print("=" * 80)
    print(f"Total templates: {catalog['total_templates']}")
    print(f"Total estimated hours: {catalog['statistics']['total_estimated_hours']}")
    print()

    print("By Language:")
    for lang, count in sorted(catalog['statistics']['by_language'].items()):
        print(f"  {lang}: {count}")
    print()

    print("By Category:")
    for cat, count in sorted(catalog['statistics']['by_category'].items()):
        print(f"  {cat}: {count}")
    print()

    print("By Difficulty:")
    for diff, count in sorted(catalog['statistics']['by_difficulty'].items()):
        print(f"  {diff}: {count}")
    print()

    print("=" * 80)
    print("Success! templates.json created")
    print("=" * 80)


if __name__ == '__main__':
    main()
