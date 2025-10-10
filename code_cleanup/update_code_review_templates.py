#!/usr/bin/env python3
"""
Script to update code review template files with required changes:
1. Fix bullet point formatting (add blank lines)
2. Add repository information section
3. Add file output instructions
"""

import os
import re
from pathlib import Path

def update_template_file(filepath, phase_name):
    """Update a single template file with all required changes."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Change 1: Fix bullet point formatting in Directory Setup section
    old_directory_setup = f"""**Directory Setup**:
- Create `review/` directory in repository root if it doesn't exist
- Create `review/{phase_name}/` subdirectory for this review phase
- All reports, scripts, and data files go in the phase-specific directory

**Expected Outputs**:
- `{phase_name}_report.md` - Main findings and recommendations
- `{phase_name}_findings.json` - Structured data for tooling integration
- `analysis_scripts/` - Any scripts generated during analysis
- `supporting_data/` - Raw data, logs, profiling results, scan outputs"""

    new_directory_setup = f"""**Directory Setup**:

- Create `review/{phase_name}/` directory in repository root if it doesn't exist

- All review outputs (reports, findings, scripts, data) go in the phase-specific directory

**Expected Outputs**:

- `{phase_name}_report.md` - Main findings and recommendations

- `{phase_name}_findings.json` - Structured data for tooling integration

- `analysis_scripts/` - Any scripts generated during analysis

- `supporting_data/` - Raw data, logs, profiling results, scan outputs"""

    if old_directory_setup in content:
        content = content.replace(old_directory_setup, new_directory_setup)
        print(f"[OK] Updated directory setup in {filepath.name}")
    else:
        print(f"[SKIP] Directory setup pattern not found in {filepath.name}")

    # Change 2: Add repository information after prompt template header
    # Find patterns like "# Python Context Analysis\n\nPlease perform"
    pattern = r'(~~~markdown\n# .*?\n)\n(Please perform|## Phase)'

    repo_info = """
## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Analysis Protocol
"""  if 'context_analysis' in str(filepath) or 'Context Analysis' in content else """
## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Review Protocol
"""

    def replacer(match):
        if '## Repository Information' not in match.group(0):
            return match.group(1) + repo_info + '\n' + match.group(2)
        return match.group(0)

    new_content = re.sub(pattern, replacer, content)
    if new_content != content:
        content = new_content
        print(f"[OK] Added repository information in {filepath.name}")
    else:
        if '## Repository Information' not in content:
            print(f"[SKIP] Could not add repository information in {filepath.name}")

    # Change 3: Add file output instructions before ~~~
    file_output = f"""
## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p review/{phase_name}/analysis_scripts
mkdir -p review/{phase_name}/supporting_data
```

**Save files as follows**:

- Main report → `review/{phase_name}/{phase_name}_report.md`

- Findings data → `review/{phase_name}/{phase_name}_findings.json`

- Analysis scripts → `review/{phase_name}/analysis_scripts/`

- Supporting data → `review/{phase_name}/supporting_data/`
~~~"""

    # Find the last ~~~ and add before it
    if content.endswith('~~~\n'):
        if '## File Output Instructions' not in content:
            content = content[:-4] + file_output + '\n'
            print(f"[OK] Added file output instructions in {filepath.name}")
    elif content.endswith('~~~'):
        if '## File Output Instructions' not in content:
            content = content[:-3] + file_output
            print(f"[OK] Added file output instructions in {filepath.name}")
    else:
        if '## File Output Instructions' not in content:
            print(f"[SKIP] Could not add file output instructions in {filepath.name}")

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def main():
    """Update all code review template files."""
    base_path = Path(__file__).parent.parent / 'code_review'

    phases = [
        'context_analysis',
        'code_quality',
        'security_review',
        'performance_review',
        'testing_review',
        'final_report'
    ]

    languages = [
        'python', 'javascript', 'java', 'csharp', 'go', 'c', 'cpp'
    ]

    total_files = 0
    updated_files = 0

    for phase in phases:
        phase_dir = base_path / phase
        if not phase_dir.exists():
            print(f"Phase directory not found: {phase_dir}")
            continue

        for lang in languages:
            # Find the template file
            template_file = phase_dir / f"{lang}_{phase}.md"
            if template_file.exists():
                total_files += 1
                print(f"\nProcessing: {template_file.relative_to(base_path)}")
                try:
                    update_template_file(template_file, phase)
                    updated_files += 1
                except Exception as e:
                    print(f"ERROR updating {template_file.name}: {e}")
            else:
                print(f"File not found: {template_file.relative_to(base_path)}")

    print(f"\n{'='*60}")
    print(f"Summary: Updated {updated_files} of {total_files} files")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
