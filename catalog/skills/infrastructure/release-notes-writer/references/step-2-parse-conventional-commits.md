### Step 2: Parse Conventional Commits

Conventional Commits follow the pattern: `type(scope): description`

**Python Parser** (`scripts/parse_commits.py`):

```python
"""Parse conventional commits into structured release note data."""
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


CONVENTIONAL_PATTERN = re.compile(
    r"^(?P<type>\w+)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*"
    r"(?P<description>.+)$"
)

BREAKING_CHANGE_PATTERN = re.compile(
    r"^BREAKING[ -]CHANGE:\s*(?P<description>.+)",
    re.MULTILINE,
)

ISSUE_REF_PATTERN = re.compile(
    r"(?:closes?|fixes?|resolves?)\s+#(\d+)",
    re.IGNORECASE,
)

# Map conventional commit types to release note categories
TYPE_CATEGORY_MAP = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "perf": "Performance",
    "docs": "Documentation",
    "refactor": "Internal Changes",
    "test": "Internal Changes",
    "chore": "Internal Changes",
    "build": "Build System",
    "ci": "CI/CD",
    "style": "Internal Changes",
    "revert": "Reverts",
}


@dataclass
class ParsedCommit:
    hash: str
    short_hash: str
    author: str
    date: str
    type: str = "other"
    scope: Optional[str] = None
    description: str = ""
    body: str = ""
    breaking: bool = False
    breaking_description: str = ""
    category: str = "Other"
    issues: list = field(default_factory=list)
    is_conventional: bool = False


def parse_commit(commit: dict) -> ParsedCommit:
    """Parse a single commit into structured data."""
    subject = commit.get("subject", "")
    body = commit.get("body", "")

    parsed = ParsedCommit(
        hash=commit["hash"],
        short_hash=commit["short_hash"],
        author=commit["author"],
        date=commit["date"],
        body=body,
    )

    match = CONVENTIONAL_PATTERN.match(subject)
    if match:
        parsed.is_conventional = True
        parsed.type = match.group("type")
        parsed.scope = match.group("scope")
        parsed.description = match.group("description")
        parsed.breaking = match.group("breaking") is not None
        parsed.category = TYPE_CATEGORY_MAP.get(parsed.type, "Other")
    else:
        parsed.description = subject

    # Check body for breaking change footer
    breaking_match = BREAKING_CHANGE_PATTERN.search(body)
    if breaking_match:
        parsed.breaking = True
        parsed.breaking_description = breaking_match.group("description").strip()

    # Extract issue references
    parsed.issues = ISSUE_REF_PATTERN.findall(subject + " " + body)

    return parsed


def parse_all(input_path: str) -> list[ParsedCommit]:
    """Parse all commits from a JSON file."""
    with open(input_path) as f:
        commits = json.load(f)

    return [parse_commit(c) for c in commits]


def group_by_category(commits: list[ParsedCommit]) -> dict[str, list[ParsedCommit]]:
    """Group parsed commits by their release note category."""
    groups: dict[str, list[ParsedCommit]] = {}
    for commit in commits:
        groups.setdefault(commit.category, []).append(commit)
    return groups


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "changes.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "parsed_commits.json"

    commits = parse_all(input_file)
    grouped = group_by_category(commits)

    output = {
        "total_commits": len(commits),
        "conventional_commits": sum(1 for c in commits if c.is_conventional),
        "breaking_changes": [asdict(c) for c in commits if c.breaking],
        "categories": {
            cat: [asdict(c) for c in items]
            for cat, items in grouped.items()
        },
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Parsed {len(commits)} commits ({output['conventional_commits']} conventional)")
    print(f"Breaking changes: {len(output['breaking_changes'])}")
    print(f"Categories: {', '.join(grouped.keys())}")
    print(f"Output: {output_file}")
```
