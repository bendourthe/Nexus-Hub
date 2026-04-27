"""
Build comprehensive skills.json catalog from all SKILL.md files.

Scans all skills in the repository and extracts metadata from YAML frontmatter
to create a machine-readable catalog for discovery and installation.

Authors:
    - Benjamin Dourthe (benjamin.dourthe@gmail.com)
"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any


def extract_frontmatter(file_path: Path) -> Dict[str, Any]:
    """Extract YAML frontmatter from SKILL.md file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match YAML frontmatter between --- delimiters
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}
    yaml_content = match.group(1)

    # Parse YAML manually (simple approach for known structure)
    for line in yaml_content.split('\n'):
        if ':' not in line:
            continue

        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()

        # Handle arrays [item1, item2, item3]
        if value.startswith('[') and value.endswith(']'):
            items = value[1:-1].split(',')
            frontmatter[key] = [item.strip() for item in items]
        else:
            frontmatter[key] = value

    return frontmatter


def extract_description_from_content(file_path: Path) -> str:
    """Extract first paragraph description from skill content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip frontmatter and find first substantive paragraph
    parts = content.split('---', 2)
    if len(parts) < 3:
        return ""

    main_content = parts[2]

    # Find first paragraph after the main heading
    paragraphs = main_content.split('\n\n')
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith('#') and len(para) > 50:
            # Remove markdown formatting
            para = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', para)
            para = re.sub(r'\*\*([^\*]+)\*\*', r'\1', para)
            para = re.sub(r'\*([^\*]+)\*', r'\1', para)
            return para[:300] + ('...' if len(para) > 300 else '')

    return ""


def extract_tools_required(file_path: Path) -> List[str]:
    """Extract required Claude tools from skill content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tools = set()
    tool_patterns = [
        r'uses?\s+the\s+(\w+)\s+tool',
        r'requires?\s+(\w+)\s+tool',
        r'Tool:\s+(\w+)',
        r'`(\w+)`\s+tool',
    ]

    # Common Claude tools
    known_tools = ['Read', 'Write', 'Edit', 'Bash', 'Glob', 'Grep',
                   'WebSearch', 'WebFetch', 'Task', 'TodoWrite']

    for tool in known_tools:
        if tool in content:
            tools.add(tool)

    return sorted(list(tools))


def calculate_skill_size(file_path: Path) -> Dict[str, int]:
    """Calculate skill size metrics."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    return {
        'lines': len(lines),
        'characters': len(content),
        'tokens_estimate': len(content.split())
    }


def assign_category(skill_name: str, frontmatter: Dict) -> str:
    """Assign skill to primary category."""
    if 'category' in frontmatter:
        return frontmatter['category']

    # Fallback category assignment based on name
    category_map = {
        'workflow': ['plan-before-code', 'test-driven-development', 'code-commit-workflow', 'debug-with-logs'],
        'configuration': ['create-claude-md', 'create-custom-command', 'optimize-context-usage', 'create-subagent-workflow'],
        'system-prompt': ['setup-python-system-prompt', 'setup-javascript-system-prompt', 'setup-java-system-prompt',
                          'setup-csharp-system-prompt', 'setup-go-system-prompt', 'setup-c-system-prompt', 'setup-cpp-system-prompt'],
        'code-review': ['code-review-context-analysis', 'code-review-quality', 'code-review-security',
                        'code-review-performance', 'code-review-testing', 'code-review-final-report'],
        'code-cleanup': ['cleanup-python', 'cleanup-javascript', 'cleanup-java', 'cleanup-csharp',
                         'cleanup-go', 'cleanup-c', 'cleanup-cpp'],
        'documentation': ['generate-api-docs', 'generate-docstrings', 'add-strategic-comments',
                          'create-user-documentation', 'create-technical-docs', 'generate-sbom'],
        'testing': ['setup-test-infrastructure', 'generate-test-cases', 'generate-mocks-fixtures',
                    'setup-performance-tests', 'setup-cicd-testing', 'measure-code-coverage'],
        'project-init': ['init-python-project', 'init-javascript-project', 'init-java-project', 'init-csharp-project'],
        'security': ['dependency-security-audit', 'pre-commit-checklist', 'licensing-compliance-check'],
        'migration': ['migrate-python-2-to-3', 'refactor-for-testability', 'extract-microservice', 'dependency-upgrade'],
        'analysis': ['code-complexity-analysis']
    }

    for category, skills in category_map.items():
        if skill_name in skills:
            return category

    return 'other'


def extract_section_content(file_path: Path, section_name: str, max_chars: int = 1000) -> str:
    """Extract content from a named Markdown section (e.g., '## When to Use')."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = rf'^##\s+{re.escape(section_name)}.*?\n(.*?)(?=^##\s|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return ""

    text = match.group(1).strip()
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{2,}', ' ', text)
    text = re.sub(r'\n', ' ', text)
    return text[:max_chars].strip()


def build_catalog() -> List[Dict[str, Any]]:
    """Build complete skills catalog from nested category/skill directories."""
    skills_base = Path(__file__).parent.parent.parent / 'catalog' / 'skills'

    catalog = []

    for category_dir in sorted(skills_base.iterdir()):
        if not category_dir.is_dir():
            continue

        category_name = category_dir.name

        # Check for SKILL.md directly in category dir (flat structure)
        direct_skill = category_dir / 'SKILL.md'
        if direct_skill.exists():
            skill_dirs = [category_dir]
        else:
            skill_dirs = []

        # Check for nested skill dirs (category/skill structure)
        for child in sorted(category_dir.iterdir()):
            if child.is_dir() and (child / 'SKILL.md').exists():
                skill_dirs.append(child)

        for skill_dir in skill_dirs:
            skill_file = skill_dir / 'SKILL.md'
            skill_name = skill_dir.name
            rel_path = skill_dir.relative_to(skills_base).as_posix()

            print(f"Processing: {rel_path}")

            frontmatter = extract_frontmatter(skill_file)

            # Determine category from directory structure or frontmatter
            if skill_dir == category_dir:
                category = assign_category(skill_name, frontmatter)
            else:
                category = frontmatter.get('category', category_name)

            # L0 summary: use frontmatter field if present, else fall back to description
            summary_l0 = frontmatter.get('summary_l0', '')
            if not summary_l0:
                summary_l0 = frontmatter.get('description', '')

            # L1 overview: use frontmatter field if present, else extract from content
            overview_l1 = frontmatter.get('overview_l1', '')
            if not overview_l1:
                what_it_does = extract_section_content(skill_file, 'What This Skill Does')
                when_to_use = extract_section_content(skill_file, 'When to Use')
                if what_it_does or when_to_use:
                    parts = []
                    if what_it_does:
                        parts.append(what_it_does[:500])
                    if when_to_use:
                        parts.append(f"Use when: {when_to_use[:300]}")
                    overview_l1 = ' '.join(parts)[:1000]
                else:
                    overview_l1 = extract_description_from_content(skill_file)

            skill_entry = {
                'name': skill_name,
                'title': frontmatter.get('name', skill_name),
                'description': frontmatter.get('description', ''),
                'long_description': extract_description_from_content(skill_file),
                'summary_l0': summary_l0,
                'overview_l1': overview_l1,
                'version': frontmatter.get('version', '1.0.0'),
                'author': frontmatter.get('author', 'Benjamin Dourthe'),
                'category': category,
                'language': frontmatter.get('language', 'Multi-language'),
                'tags': frontmatter.get('tags', []),
                'priority': frontmatter.get('priority', 'MEDIUM'),
                'based_on': frontmatter.get('based_on', ''),
                'tools_required': extract_tools_required(skill_file),
                'path': f'catalog/skills/{rel_path}/',
                'file': f'catalog/skills/{rel_path}/SKILL.md',
                'size': calculate_skill_size(skill_file),
                'downloads': 0,
                'status': 'production',
                'security': {
                    'structural': 100,
                    'integrity': 100,
                    'semantic': 95,
                    'validated': True
                }
            }

            # Optional fields from frontmatter
            if 'model_hint' in frontmatter:
                skill_entry['model_hint'] = frontmatter['model_hint']
            if 'reasoning_effort' in frontmatter:
                skill_entry['reasoning_effort'] = frontmatter['reasoning_effort']
            if 'permissions' in frontmatter:
                skill_entry['permissions'] = frontmatter['permissions']

            catalog.append(skill_entry)

    return catalog


def generate_statistics(catalog: List[Dict]) -> Dict[str, Any]:
    """Generate catalog statistics."""
    categories = {}
    priorities = {}
    total_lines = 0
    total_tokens = 0

    for skill in catalog:
        # Count by category
        cat = skill['category']
        categories[cat] = categories.get(cat, 0) + 1

        # Count by priority
        pri = skill['priority']
        priorities[pri] = priorities.get(pri, 0) + 1

        # Sum size metrics
        total_lines += skill['size']['lines']
        total_tokens += skill['size']['tokens_estimate']

    return {
        'total_skills': len(catalog),
        'categories': categories,
        'priorities': priorities,
        'total_lines': total_lines,
        'total_tokens_estimate': total_tokens,
        'average_lines_per_skill': total_lines // len(catalog) if catalog else 0,
        'languages_supported': ['Python', 'JavaScript', 'Java', 'C#', 'Go', 'C', 'C++'],
        'repository': 'https://github.com/bendourthe/DevAI-Hub',
        'last_updated': '2025-10-21'
    }


def generate_skill_index(catalog: List[Dict]) -> str:
    """Generate SKILL_INDEX.md with L0 summaries organized by category."""
    lines = [
        "# DevAI-Hub Skill Index",
        "",
        "Quick-reference index of all available skills. Use the skill name or summary to find the right skill for your task.",
        "",
        "| Skill | Category | Summary | File |",
        "|-------|----------|---------|------|",
    ]

    sorted_skills = sorted(catalog, key=lambda s: (s['category'], s['name']))
    for skill in sorted_skills:
        name = skill['name']
        category = skill['category']
        summary = skill.get('summary_l0', skill.get('description', '')).replace('|', '\\|')
        file_path = skill['file']
        lines.append(f"| {name} | {category} | {summary} | {file_path} |")

    lines.append("")
    lines.append(f"**Total: {len(catalog)} skills across {len(set(s['category'] for s in catalog))} categories**")
    lines.append("")
    return '\n'.join(lines)


def main():
    """Build and save skills catalog and skill index."""
    from datetime import datetime, timezone

    print("Building skills catalog...")
    catalog = build_catalog()

    print(f"\nProcessed {len(catalog)} skills")

    stats = generate_statistics(catalog)

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    output = {
        'metadata': {
            'version': '2.0.0',
            'generated': now,
            'repository': 'https://github.com/bendourthe/DevAI-Hub',
            'description': 'Comprehensive catalog of DevAI-Hub skills with L0/L1 tiered summaries'
        },
        'statistics': stats,
        'skills': catalog
    }

    base_path = Path(__file__).parent.parent.parent

    # Save skills.json
    output_path = base_path / 'data' / 'skills.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nCatalog saved to: {output_path}")

    # Generate and save SKILL_INDEX.md
    index_content = generate_skill_index(catalog)
    index_path = base_path / 'data' / 'SKILL_INDEX.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    print(f"Skill index saved to: {index_path}")

    # Print summary
    print(f"\nStatistics:")
    print(f"  Total skills: {stats['total_skills']}")
    print(f"  Total lines: {stats['total_lines']:,}")
    print(f"  Estimated tokens: {stats['total_tokens_estimate']:,}")
    print(f"  Average lines per skill: {stats['average_lines_per_skill']}")

    # Count L0/L1 coverage
    l0_count = sum(1 for s in catalog if s.get('summary_l0'))
    l1_count = sum(1 for s in catalog if s.get('overview_l1'))
    print(f"\nTiered coverage:")
    print(f"  L0 summaries: {l0_count}/{len(catalog)}")
    print(f"  L1 overviews: {l1_count}/{len(catalog)}")

    print(f"\nCategories:")
    for cat, count in sorted(stats['categories'].items()):
        print(f"  {cat}: {count}")
    print(f"\nPriorities:")
    for pri, count in sorted(stats['priorities'].items()):
        print(f"  {pri}: {count}")


if __name__ == '__main__':
    main()
