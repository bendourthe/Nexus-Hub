### Step 3: Categorize Pull Requests

When conventional commits are not used consistently, fall back to PR labels and file paths for categorization.

**PR Categorization Script** (`scripts/categorize_prs.py`):

```python
"""Categorize pull requests by labels, title patterns, and file paths."""
import json
import re
import sys
from typing import Optional


# Label-to-category mapping (checked first)
LABEL_CATEGORY_MAP = {
    "feature": "Features",
    "enhancement": "Features",
    "bug": "Bug Fixes",
    "bugfix": "Bug Fixes",
    "fix": "Bug Fixes",
    "performance": "Performance",
    "perf": "Performance",
    "documentation": "Documentation",
    "docs": "Documentation",
    "security": "Security",
    "breaking-change": "Breaking Changes",
    "breaking": "Breaking Changes",
    "dependencies": "Dependencies",
    "deps": "Dependencies",
    "internal": "Internal Changes",
    "chore": "Internal Changes",
    "ci": "CI/CD",
}

# File path patterns for fallback categorization
PATH_CATEGORY_MAP = [
    (r"^docs/", "Documentation"),
    (r"^\.github/", "CI/CD"),
    (r"^\.gitlab-ci", "CI/CD"),
    (r"^Jenkinsfile", "CI/CD"),
    (r"^tests?/", "Internal Changes"),
    (r"^benchmark", "Performance"),
]

# Title patterns for fallback categorization
TITLE_CATEGORY_MAP = [
    (r"^feat(\(.+\))?:", "Features"),
    (r"^fix(\(.+\))?:", "Bug Fixes"),
    (r"^perf(\(.+\))?:", "Performance"),
    (r"^docs(\(.+\))?:", "Documentation"),
    (r"^chore(\(.+\))?:", "Internal Changes"),
    (r"^ci(\(.+\))?:", "CI/CD"),
    (r"^refactor(\(.+\))?:", "Internal Changes"),
]


def categorize_pr(pr: dict) -> str:
    """Determine the category for a single PR."""
    labels = [label.get("name", "").lower() for label in pr.get("labels", [])]

    # Check labels first (highest priority)
    for label in labels:
        if label in LABEL_CATEGORY_MAP:
            return LABEL_CATEGORY_MAP[label]

    # Check title patterns
    title = pr.get("title", "")
    for pattern, category in TITLE_CATEGORY_MAP:
        if re.match(pattern, title, re.IGNORECASE):
            return category

    # Default category
    return "Other"


def is_breaking(pr: dict) -> bool:
    """Check if a PR contains breaking changes."""
    labels = [label.get("name", "").lower() for label in pr.get("labels", [])]
    if "breaking-change" in labels or "breaking" in labels:
        return True

    title = pr.get("title", "")
    if "!" in title.split(":")[0] if ":" in title else False:
        return True

    body = pr.get("body", "") or ""
    if "BREAKING CHANGE" in body:
        return True

    return False


def categorize_all(input_path: str, output_path: str):
    """Categorize all PRs and write grouped output."""
    with open(input_path) as f:
        prs = json.load(f)

    categorized = {}
    breaking = []

    for pr in prs:
        category = categorize_pr(pr)
        entry = {
            "number": pr["number"],
            "title": pr["title"],
            "author": pr.get("author", {}).get("login", "unknown"),
            "merged_at": pr.get("mergedAt", ""),
            "category": category,
            "breaking": is_breaking(pr),
        }

        categorized.setdefault(category, []).append(entry)
        if entry["breaking"]:
            breaking.append(entry)

    output = {
        "total_prs": len(prs),
        "breaking_changes": breaking,
        "categories": categorized,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Categorized {len(prs)} PRs")
    for cat, items in categorized.items():
        print(f"  {cat}: {len(items)}")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "prs.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "categorized_prs.json"
    categorize_all(input_file, output_file)
```
