"""
Fix consistency issues across all templates.

This script fixes:
1. OUTPUT_DIR pattern: {OUTPUT_DIR} → ${OUTPUT_DIR}
2. Reports all files that need updates

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


def fix_output_dir_pattern(content: str) -> Tuple[str, int]:
    """
    Fix OUTPUT_DIR pattern from {OUTPUT_DIR} to ${OUTPUT_DIR}.

    Returns:
        Tuple of (fixed_content, number_of_replacements)
    """
    # Find all occurrences of {OUTPUT_DIR} that don't have $ prefix
    # Use negative lookbehind to avoid replacing ${OUTPUT_DIR}
    pattern = r'(?<!\$)\{OUTPUT_DIR\}'

    # Count occurrences
    matches = re.findall(pattern, content)
    count = len(matches)

    if count == 0:
        return content, 0

    # Replace with ${OUTPUT_DIR}
    fixed_content = re.sub(pattern, '${OUTPUT_DIR}', content)

    return fixed_content, count


def process_file(filepath: Path) -> Dict:
    """
    Process a single file and fix consistency issues.

    Returns:
        Dictionary with results
    """
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        fixes = []

        # Fix OUTPUT_DIR pattern
        content, output_dir_fixes = fix_output_dir_pattern(content)
        if output_dir_fixes > 0:
            fixes.append(f"OUTPUT_DIR pattern ({output_dir_fixes} replacements)")

        # If any fixes were made, write back
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                'status': 'updated',
                'fixes': fixes,
                'file': str(filepath.relative_to(filepath.parents[1]))
            }
        else:
            return {
                'status': 'no_changes',
                'file': str(filepath.relative_to(filepath.parents[1]))
            }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'file': str(filepath.relative_to(filepath.parents[1]))
        }


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
                if md_file.name not in ['README.md', 'CHANGELOG.md', 'DEVLOG.md']:
                    templates.append(md_file)

    return sorted(templates)


def main():
    """Fix consistency issues across all templates."""
    base_path = Path(__file__).parent.parent

    print("=" * 80)
    print("Fixing Consistency Issues Across All Templates")
    print("=" * 80)
    print()

    # Find all templates
    print("Scanning for template files...")
    templates = find_all_templates(base_path)
    print(f"Found {len(templates)} template files to process")
    print()

    # Process each file
    updated = []
    no_changes = []
    errors = []

    print("Processing files...")
    print("-" * 80)

    for filepath in templates:
        result = process_file(filepath)

        if result['status'] == 'updated':
            updated.append(result)
            print(f"UPDATED: {result['file']}")
            for fix in result['fixes']:
                print(f"  - {fix}")
        elif result['status'] == 'no_changes':
            no_changes.append(result)
        elif result['status'] == 'error':
            errors.append(result)
            print(f"ERROR: {result['file']} - {result['error']}")

    # Print summary
    print()
    print("=" * 80)
    print("Summary:")
    print("-" * 80)
    print(f"  Total files scanned: {len(templates)}")
    print(f"  Files updated: {len(updated)}")
    print(f"  Files with no changes needed: {len(no_changes)}")
    print(f"  Files with errors: {len(errors)}")
    print("=" * 80)

    if updated:
        print()
        print("Updated files:")
        print("-" * 80)
        for result in updated:
            print(f"  {result['file']}")

    if errors:
        print()
        print("Files with errors:")
        print("-" * 80)
        for result in errors:
            print(f"  {result['file']}: {result['error']}")

    print()
    print("Consistency fixes complete!")


if __name__ == '__main__':
    main()
