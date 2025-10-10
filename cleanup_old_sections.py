"""
Script to remove old 'File Output Instructions' sections and move content properly.

This script:
1. Removes old '## File Output Instructions' sections
2. Moves '## Output Format Specifications' inside the prompt template
3. Ensures content is before the closing ~~~

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
import re
from pathlib import Path
from typing import List


def find_template_files() -> List[Path]:
    """Find all template Markdown files."""
    base_dir = Path(__file__).parent
    categories = ["documentation", "code_review", "code_cleanup", "test_development"]

    template_files = []
    for category in categories:
        category_path = base_dir / category
        if category_path.exists():
            template_files.extend(category_path.rglob("*.md"))

    # Exclude README files
    return [f for f in template_files if f.name != "README.md" or "README" not in str(f.parent.parent)]


def remove_old_file_output_section(content: str) -> str:
    """Remove the old '## File Output Instructions' section completely."""
    # Pattern to match the entire old section
    pattern = r'---\s*\n\s*## File Output Instructions.*?(?=~~~\s*\n|## Output Format Specifications|## Verify Directory Structure|\Z)'

    content = re.sub(pattern, '', content, flags=re.DOTALL)
    return content


def move_output_format_inside_template(content: str) -> str:
    """Move 'Output Format Specifications' section inside the prompt template (before ~~~)."""

    # Find the Output Format Specifications section that's outside
    outside_pattern = r'~~~\s*\n\s*(## Output Format Specifications.*?)(?=---\s*\n\s*## Verify Directory Structure|\Z)'

    match = re.search(outside_pattern, content, flags=re.DOTALL)

    if match:
        output_format_section = match.group(1).strip()

        # Remove the section from outside
        content = re.sub(outside_pattern, '~~~\n', content, flags=re.DOTALL)

        # Find where to insert it (before the closing ~~~)
        # Look for the last section before ~~~
        insert_pattern = r'(## Best Practices.*?)\n\s*~~~'

        if re.search(insert_pattern, content, flags=re.DOTALL):
            # Insert after Best Practices
            content = re.sub(
                insert_pattern,
                r'\1\n\n---\n\n' + output_format_section + '\n\n~~~',
                content,
                flags=re.DOTALL
            )

    return content


def fix_bullet_formatting(content: str) -> str:
    """Add blank lines before bullet lists for better Bitbucket rendering."""
    # Add blank line before bullet lists if not already present
    content = re.sub(r'([^\n])\n(-\s+)', r'\1\n\n\2', content)
    return content


def process_file(file_path: Path) -> tuple[bool, str]:
    """Process a single file and return (changed, message)."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content

        # Apply transformations
        content = remove_old_file_output_section(content)
        content = move_output_format_inside_template(content)
        content = fix_bullet_formatting(content)

        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True, f"[+] Updated: {file_path.name}"
        else:
            return False, f"[ ] No changes: {file_path.name}"

    except Exception as e:
        return False, f"[X] Error: {file_path.name} - {str(e)}"


def main():
    """Main execution function."""
    print("Finding template files...")
    files = find_template_files()
    print(f"Found {len(files)} files\n")

    updated_count = 0
    results = []

    for file_path in files:
        changed, message = process_file(file_path)
        results.append(message)
        if changed:
            updated_count += 1
        print(message)

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Files updated: {updated_count}/{len(files)}")
    print(f"{'='*60}")

    # Save report
    report_path = Path(__file__).parent / "cleanup_report.md"
    report = f"""# Cleanup Report

## Summary
- Files processed: {len(files)}
- Files updated: {updated_count}
- Files unchanged: {len(files) - updated_count}

## Changes Applied
1. Removed old '## File Output Instructions' sections
2. Moved '## Output Format Specifications' inside prompt template
3. Fixed bullet point formatting for Bitbucket

## Results
{chr(10).join(results)}
"""
    report_path.write_text(report, encoding='utf-8')
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
