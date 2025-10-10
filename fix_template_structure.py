"""
Automated script to fix directory structure and formatting in all template files.

This script:
1. Removes 'generated_docs/' subdirectory references
2. Updates directory structure to 3 subdirectories (templates/, assets/, exports/)
3. Adds directory setup instructions at the beginning
4. Updates all file path references to include ${OUTPUT_DIR}/ prefix
5. Fixes Markdown bullet point formatting
6. Adds verification section at the end

Authors:
    - Benjamin Dourthe (benjamin@adonamed.com)
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


class TemplateUpdater:
    """Handles template file updates with directory structure corrections."""

    def __init__(self, base_dir: str):
        """Initialize with base directory."""
        self.base_dir = Path(base_dir)
        self.changes_log = []
        self.files_processed = 0
        self.errors = []

    def find_template_files(self) -> List[Path]:
        """Find all template Markdown files."""
        categories = [
            "documentation",
            "code_review",
            "code_cleanup",
            "test_development"
        ]

        template_files = []
        for category in categories:
            category_path = self.base_dir / category
            if category_path.exists():
                template_files.extend(category_path.rglob("*.md"))

        # Exclude README files from root directories
        return [f for f in template_files if f.name != "README.md" or "README" not in str(f.parent.parent)]

    def determine_output_dir(self, file_path: Path) -> Tuple[str, str]:
        """Determine OUTPUT_DIR and phase name based on file path."""
        parts = file_path.parts

        if "documentation" in parts:
            idx = parts.index("documentation")
            if idx + 1 < len(parts):
                phase = parts[idx + 1]
                return f"documentation/{phase}", phase

        elif "code_review" in parts:
            idx = parts.index("code_review")
            if idx + 1 < len(parts):
                phase = parts[idx + 1]
                return f"review/{phase}", phase

        elif "code_cleanup" in parts:
            return "cleanup", "cleanup"

        elif "test_development" in parts:
            idx = parts.index("test_development")
            if idx + 1 < len(parts):
                phase = parts[idx + 1]
                return f"tests/{phase}", phase

        return "output", "output"

    def create_directory_setup_section(self, output_dir: str, phase: str) -> str:
        """Create the directory setup section to add at the beginning."""
        return f"""## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="{output_dir}"
```

Create the required subdirectories:
```bash
mkdir -p ${{OUTPUT_DIR}}/templates
mkdir -p ${{OUTPUT_DIR}}/assets
mkdir -p ${{OUTPUT_DIR}}/exports
```

**Directory Structure:**
```
${{OUTPUT_DIR}}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**
- All generated files should be saved with the `${{OUTPUT_DIR}}/` prefix
- Examples:
  - Reports and documentation → `${{OUTPUT_DIR}}/exports/report.md`
  - Template files → `${{OUTPUT_DIR}}/templates/template.yaml`
  - Diagrams and images → `${{OUTPUT_DIR}}/assets/diagram.png`

"""

    def create_verification_section(self) -> str:
        """Create the verification section to add at the end."""
        return """
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
"""

    def update_directory_structure_section(self, content: str, output_dir: str) -> str:
        """Update the Output Directory Structure section."""
        # Pattern to find the directory structure section
        pattern = r'## Output Directory Structure\s*\n\s*\n.*?```\s*\n.*?```\s*\n\s*\n\*\*Directory Setup\*\*:.*?(?=\n##|\Z)'

        replacement = f'''## Output Directory Structure

All outputs should be saved in organized directories:

```
{output_dir}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `{output_dir}/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts

'''

        return re.sub(pattern, replacement, content, flags=re.DOTALL)

    def fix_bullet_points(self, content: str) -> str:
        """Fix bullet point formatting for Bitbucket compatibility."""
        # Ensure proper spacing in checklist items
        content = re.sub(r'- \[\s*\]', '- [ ]', content)
        content = re.sub(r'-\[\s*\]', '- [ ]', content)
        content = re.sub(r'- \[x\]', '- [x]', content, flags=re.IGNORECASE)
        return content

    def update_file_paths(self, content: str, output_dir: str) -> str:
        """Update file paths to include ${OUTPUT_DIR}/ prefix."""
        # Pattern for common file generation commands
        patterns = [
            # Output redirects
            (r'> ([a-zA-Z0-9_\-\.]+\.(json|md|yaml|yml|txt|html|xml|csv))',
             r'> ${OUTPUT_DIR}/exports/\1'),

            # --output flag
            (r'--output ([a-zA-Z0-9_\-\.]+\.(json|md|yaml|yml|txt|html|xml|csv))',
             r'--output ${OUTPUT_DIR}/exports/\1'),

            # -o flag
            (r' -o ([a-zA-Z0-9_\-\.]+\.(json|md|yaml|yml|txt|html|xml|csv))',
             r' -o ${OUTPUT_DIR}/exports/\1'),

            # mkdir commands without OUTPUT_DIR
            (r'mkdir -p (documentation|review|tests|cleanup)/([a-zA-Z0-9_\-/]+)',
             r'mkdir -p ${OUTPUT_DIR}/\2'),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        return content

    def remove_generated_docs_references(self, content: str) -> str:
        """Remove all references to generated_docs/ subdirectory."""
        # Remove from directory listings
        content = re.sub(r'\s*├── generated_docs/.*\n', '', content)
        content = re.sub(r'\s*└── generated_docs/.*\n', '', content)

        # Remove from bullet points
        content = re.sub(r'- `generated_docs/`[^\n]*\n', '', content)
        content = re.sub(r'- Generated docs[^\n]*`[^`]*generated_docs/[^`]*`[^\n]*\n', '', content)

        # Replace paths that use generated_docs
        content = re.sub(r'generated_docs/', 'exports/', content)

        return content

    def insert_directory_setup_after_prompt_template(self, content: str, setup_section: str) -> str:
        """Insert directory setup section after '## Prompt Template' or similar marker."""
        # Look for the start of the prompt template section
        pattern = r'(## Prompt Template\s*\n\s*\n.*?~~~markdown\s*\n# [^\n]+\n\s*\n)'

        def replacer(match):
            return match.group(1) + setup_section

        return re.sub(pattern, replacer, content, count=1, flags=re.DOTALL)

    def process_file(self, file_path: Path) -> bool:
        """Process a single template file."""
        try:
            # Read file
            content = file_path.read_text(encoding='utf-8')
            original_content = content

            # Determine output directory
            output_dir, phase = self.determine_output_dir(file_path)

            # Create sections
            setup_section = self.create_directory_setup_section(output_dir, phase)
            verification_section = self.create_verification_section()

            # Apply transformations
            content = self.remove_generated_docs_references(content)
            content = self.update_directory_structure_section(content, output_dir)
            content = self.fix_bullet_points(content)
            content = self.update_file_paths(content, output_dir)
            content = self.insert_directory_setup_after_prompt_template(content, setup_section)

            # Add verification section at the end if not already present
            if "## Verify Directory Structure" not in content:
                content = content.rstrip() + verification_section

            # Write back only if changed
            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                self.changes_log.append(f"✓ Updated: {file_path.relative_to(self.base_dir)}")
                self.files_processed += 1
                return True
            else:
                self.changes_log.append(f"○ No changes: {file_path.relative_to(self.base_dir)}")
                return False

        except Exception as e:
            error_msg = f"✗ Error processing {file_path.relative_to(self.base_dir)}: {str(e)}"
            self.errors.append(error_msg)
            print(error_msg)
            return False

    def generate_report(self) -> str:
        """Generate a summary report of changes."""
        report = f"""
# Template Update Report

## Summary
- Total files processed: {self.files_processed}
- Total files scanned: {len(self.changes_log)}
- Errors encountered: {len(self.errors)}

## Changes Made
{chr(10).join(self.changes_log)}

## Errors
{chr(10).join(self.errors) if self.errors else "No errors"}

## Transformations Applied
1. Removed 'generated_docs/' subdirectory references
2. Updated directory structure to 3 subdirectories (templates/, assets/, exports/)
3. Added directory setup instructions at the beginning of templates
4. Updated file path references to include ${{OUTPUT_DIR}}/ prefix
5. Fixed Markdown bullet point formatting
6. Added verification section at the end

## Next Steps
- Review sample files to verify correctness
- Test templates with GitHub Copilot
- Commit changes to repository
"""
        return report

    def run(self):
        """Run the update process."""
        print("Finding template files...")
        template_files = self.find_template_files()
        print(f"Found {len(template_files)} template files")

        print("\nProcessing files...")
        for file_path in template_files:
            print(f"Processing: {file_path.relative_to(self.base_dir)}")
            self.process_file(file_path)

        print("\nGenerating report...")
        report = self.generate_report()

        # Save report
        report_path = self.base_dir / "template_update_report.md"
        report_path.write_text(report, encoding='utf-8')
        print(f"\nReport saved to: {report_path}")

        print(f"\n✓ Update complete!")
        print(f"Files processed: {self.files_processed}")
        print(f"Errors: {len(self.errors)}")


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    updater = TemplateUpdater(base_dir)
    updater.run()
