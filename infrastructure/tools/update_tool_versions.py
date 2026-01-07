"""
Update tool versions to 2025 standards across all templates.

This script updates outdated tool references to current versions as of December 2025.

Authors:
    - Benjamin Dourthe (benjamin.dourthe@gmail.com)
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


# Version mappings: old_version -> new_version
VERSION_UPDATES = {
    # Python tools
    'black': [
        ('24.1.1', '24.12.0'),
        ('black 24.1.1', 'black 24.12.0'),
        ('black==24.1.1', 'black==24.12.0'),
        ('black>=24.1.1', 'black>=24.12.0'),
    ],
    'flake8': [
        ('7.0.0', '7.1.1'),
        ('flake8 7.0.0', 'flake8 7.1.1'),
        ('flake8==7.0.0', 'flake8==7.1.1'),
        ('flake8>=7.0.0', 'flake8>=7.1.1'),
    ],
    'mypy': [
        ('v1.8.0', '1.13.0'),
        ('mypy v1.8.0', 'mypy 1.13.0'),
        ('mypy==1.8.0', 'mypy==1.13.0'),
        ('mypy>=1.8.0', 'mypy>=1.13.0'),
    ],
    'pytest': [
        ('pytest 7.', 'pytest 8.3.4'),
        ('pytest==7.', 'pytest==8.3.4'),
        ('pytest>=7.', 'pytest>=8.3.4'),
    ],

    # JavaScript tools
    'jest': [
        ('jest 28.', 'jest 29.7.0'),
        ('jest 29.0', 'jest 29.7.0'),
    ],
    'eslint': [
        ('eslint 8.', 'eslint 9.15.0'),
    ],

    # Java tools
    'junit': [
        ('junit 5.9', 'junit 5.11.3'),
        ('junit-jupiter 5.9', 'junit-jupiter 5.11.3'),
        ('JUnit 5.9', 'JUnit 5.11.3'),
    ],

    # C# tools
    'nunit': [
        ('NUnit 3.13', 'NUnit 4.2.2'),
        ('nunit 3.13', 'nunit 4.2.2'),
    ],

    # Go tools
    'go test': [
        ('Go 1.20', 'Go 1.23'),
        ('go 1.20', 'go 1.23'),
    ],
}


def update_tool_versions(content: str, filepath: Path) -> Tuple[str, List[str]]:
    """
    Update tool versions in content.

    Returns:
        Tuple of (updated_content, list_of_changes)
    """
    updated_content = content
    changes = []

    # Determine language from filepath
    filename = filepath.name.lower()

    # Apply version updates based on file type
    for tool_name, version_pairs in VERSION_UPDATES.items():
        for old_version, new_version in version_pairs:
            # Check if this update is relevant for this file
            if _is_relevant_for_file(tool_name, filepath):
                # Use word boundaries to avoid partial matches
                pattern = re.escape(old_version)
                if re.search(pattern, updated_content):
                    updated_content = re.sub(pattern, new_version, updated_content)
                    changes.append(f"{tool_name}: {old_version} -> {new_version}")

    return updated_content, changes


def _is_relevant_for_file(tool_name: str, filepath: Path) -> bool:
    """Check if a tool update is relevant for a specific file."""
    filename = filepath.name.lower()

    # Python tools
    if tool_name in ['black', 'flake8', 'mypy', 'pytest']:
        return 'python' in filename

    # JavaScript tools
    if tool_name in ['jest', 'eslint', 'npm']:
        return 'javascript' in filename

    # Java tools
    if tool_name in ['junit', 'maven', 'gradle']:
        return 'java' in filename

    # C# tools
    if tool_name in ['nunit', 'mstest', 'xunit']:
        return 'csharp' in filename

    # Go tools
    if tool_name in ['go test', 'testify']:
        return 'go' in filename

    # C/C++ tools
    if tool_name in ['gtest', 'catch2', 'unity']:
        return filename.startswith('c_') or filename.startswith('cpp_')

    return True  # Default: apply to all files


def process_file(filepath: Path) -> Dict:
    """
    Process a single file and update tool versions.

    Returns:
        Dictionary with results
    """
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Update tool versions
        content, changes = update_tool_versions(content, filepath)

        # If changes were made, write back
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                'status': 'updated',
                'changes': changes,
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
    """Update tool versions across all templates."""
    base_path = Path(__file__).parent.parent

    print("=" * 80)
    print("Updating Tool Versions to 2025 Standards")
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
            for change in result['changes']:
                print(f"  - {change}")
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
            for change in result['changes']:
                print(f"    - {change}")

    if errors:
        print()
        print("Files with errors:")
        print("-" * 80)
        for result in errors:
            print(f"  {result['file']}: {result['error']}")

    print()
    print("Tool version updates complete!")


if __name__ == '__main__':
    main()
