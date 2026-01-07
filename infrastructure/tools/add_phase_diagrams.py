"""
Add phase diagrams to all testing templates.

This script adds visual phase diagrams to all test development templates
to help users understand where they are in the 8-phase methodology.

Authors:
    - Benjamin Dourthe (benjamin.dourthe@gmail.com)
"""
import os
import re
from pathlib import Path
from typing import Dict, List

# Phase mapping
PHASES = {
    'test_structure': {
        'number': 1,
        'name': 'Test Structure Setup',
        'next': 'Phase 2 (Unit Tests)'
    },
    'unit_tests': {
        'number': 2,
        'name': 'Unit Tests',
        'next': 'Phase 3 (Test Cases Development)'
    },
    'test_cases': {
        'number': 3,
        'name': 'Test Cases Development',
        'next': 'Phase 4 (Mocks & Fixtures)'
    },
    'mocks_fixtures': {
        'number': 4,
        'name': 'Mocks & Fixtures',
        'next': 'Phase 5 (Performance Testing)'
    },
    'performance_testing': {
        'number': 5,
        'name': 'Performance Testing',
        'next': 'Phase 6 (Code Coverage)'
    },
    'code_coverage': {
        'number': 6,
        'name': 'Code Coverage',
        'next': 'Phase 7 (Maintenance & CI/CD)'
    },
    'maintenance_cicd': {
        'number': 7,
        'name': 'Maintenance & CI/CD',
        'next': 'Phase 8 (Reward Hacking Validation)'
    },
    'reward_hacking': {
        'number': 8,
        'name': 'Reward Hacking Validation',
        'next': 'Testing complete!'
    }
}

PHASE_NAMES = [
    'Test Structure Setup',
    'Unit Tests',
    'Test Cases Development',
    'Mocks & Fixtures',
    'Performance Testing',
    'Code Coverage',
    'Maintenance & CI/CD',
    'Reward Hacking Validation'
]


def generate_phase_diagram(phase_dir: str) -> str:
    """Generate phase diagram for a specific phase."""
    phase_info = PHASES.get(phase_dir)
    if not phase_info:
        return ""

    current_phase = phase_info['number']

    # Build diagram
    lines = [
        "## Your Position in the 8-Phase Testing Methodology",
        "",
        "```",
        "┌─────────────────────────────────────────────────────────┐"
    ]

    for i, phase_name in enumerate(PHASE_NAMES, 1):
        if i < current_phase:
            status = "[COMPLETE]"
        elif i == current_phase:
            status = "● CURRENT"
        elif i == current_phase + 1:
            status = "[NEXT]"
        else:
            status = ""

        # Format line
        line = f"│ Phase {i}: {phase_name}"
        padding = 59 - len(line) - len(status)
        line += " " * padding + "► │ " + status
        lines.append(line)

    lines.extend([
        "└─────────────────────────────────────────────────────────┘",
        "```",
        ""
    ])

    # Add prerequisites and next steps
    if current_phase == 1:
        lines.append("**Prerequisites:** None - This is the starting phase")
    else:
        prev_phase = current_phase - 1
        lines.append(f"**Prerequisites:** Phase {prev_phase} ({PHASE_NAMES[prev_phase - 1]}) should be completed first")

    lines.append(f"**Next Step:** {phase_info['next']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def add_diagram_to_file(filepath: Path) -> bool:
    """Add phase diagram to a template file."""
    # Determine phase from directory
    phase_dir = filepath.parent.name
    if phase_dir not in PHASES:
        print(f"WARNING: Unknown phase: {phase_dir}")
        return False

    # Read file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if diagram already exists
    if "Your Position in the 8-Phase Testing Methodology" in content:
        print(f"SKIP: Already has diagram: {filepath.name}")
        return False

    # Find title (first line starting with #)
    title_match = re.match(r'^(# .+?)$', content, re.MULTILINE)
    if not title_match:
        print(f"WARNING: No title found: {filepath.name}")
        return False

    title_end = title_match.end()

    # Generate diagram
    diagram = generate_phase_diagram(phase_dir)

    # Insert diagram after title
    new_content = content[:title_end] + "\n\n" + diagram + content[title_end:]

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"SUCCESS: Added diagram: {filepath.name}")
    return True


def main():
    """Add phase diagrams to all testing templates."""
    base_path = Path(__file__).parent.parent.parent / 'templates' / 'development' / 'tests-generation'

    if not base_path.exists():
        print(f"❌ Test development directory not found: {base_path}")
        return

    # Languages to process
    languages = ['python', 'javascript', 'java', 'csharp', 'go', 'c', 'cpp']

    total = 0
    updated = 0

    for phase_dir in PHASES.keys():
        phase_path = base_path / phase_dir
        if not phase_path.exists():
            continue

        for lang in languages:
            filepath = phase_path / f"{lang}_{phase_dir}.md"
            if filepath.exists():
                total += 1
                if add_diagram_to_file(filepath):
                    updated += 1

    print(f"\n{'='*60}")
    print(f"Processed {total} files, updated {updated} files")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
