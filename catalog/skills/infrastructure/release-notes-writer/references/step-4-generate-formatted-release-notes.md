### Step 4: Generate Formatted Release Notes

**Release Notes Generator** (`scripts/generate_release_notes.py`):

```python
"""Generate formatted release notes from categorized changes."""
import json
import sys
from datetime import datetime, timezone
from typing import Optional


# Category display order (user-facing categories first)
CATEGORY_ORDER = [
    "Breaking Changes",
    "Features",
    "Bug Fixes",
    "Performance",
    "Security",
    "Documentation",
    "Dependencies",
    "CI/CD",
    "Build System",
    "Internal Changes",
    "Reverts",
    "Other",
]


def generate_markdown(
    parsed_data: dict,
    version: str,
    date: Optional[str] = None,
    repo_url: Optional[str] = None,
    audience: str = "all",
) -> str:
    """Generate Markdown release notes.

    Args:
        parsed_data: Output from parse_commits.py or categorize_prs.py.
        version: Version string (e.g., "v2.5.0").
        date: Release date (defaults to today).
        repo_url: Repository URL for linking commits and PRs.
        audience: "user" (features/fixes only), "developer" (all technical),
                  or "all" (everything).
    """
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = []
    lines.append(f"# {version}")
    lines.append("")
    lines.append(f"**Release Date**: {date}")
    lines.append("")

    # Breaking changes section (always first if present)
    breaking = parsed_data.get("breaking_changes", [])
    if breaking:
        lines.append("## Breaking Changes")
        lines.append("")
        for change in breaking:
            desc = change.get("description", change.get("title", ""))
            breaking_detail = change.get("breaking_description", "")
            if "number" in change:
                if repo_url:
                    lines.append(f"- {desc} ([#{change['number']}]({repo_url}/pull/{change['number']}))")
                else:
                    lines.append(f"- {desc} (#{change['number']})")
            else:
                short_hash = change.get("short_hash", "")
                if repo_url and short_hash:
                    lines.append(f"- {desc} ([{short_hash}]({repo_url}/commit/{change.get('hash', '')}))")
                else:
                    lines.append(f"- {desc}")
            if breaking_detail:
                lines.append(f"  - Migration: {breaking_detail}")
        lines.append("")

    # Filter categories by audience
    user_categories = {"Features", "Bug Fixes", "Performance", "Security"}
    developer_categories = user_categories | {"Documentation", "Dependencies", "CI/CD", "Build System", "Reverts"}
    all_categories = developer_categories | {"Internal Changes", "Other"}

    if audience == "user":
        visible_categories = user_categories
    elif audience == "developer":
        visible_categories = developer_categories
    else:
        visible_categories = all_categories

    # Render each category
    categories = parsed_data.get("categories", {})
    for category in CATEGORY_ORDER:
        if category == "Breaking Changes":
            continue  # Already rendered above
        if category not in categories:
            continue
        if category not in visible_categories:
            continue

        items = categories[category]
        if not items:
            continue

        lines.append(f"## {category}")
        lines.append("")

        for item in items:
            desc = item.get("description", item.get("title", ""))
            scope = item.get("scope")
            author = item.get("author", "")

            prefix = f"**{scope}**: " if scope else ""

            if "number" in item:
                # PR-based entry
                ref = f"#{item['number']}"
                if repo_url:
                    ref = f"[#{item['number']}]({repo_url}/pull/{item['number']})"
                attribution = f" (@{author})" if author else ""
                lines.append(f"- {prefix}{desc} ({ref}){attribution}")
            else:
                # Commit-based entry
                short_hash = item.get("short_hash", "")
                if repo_url and short_hash:
                    ref = f"[{short_hash}]({repo_url}/commit/{item.get('hash', '')})"
                else:
                    ref = short_hash
                attribution = f" (@{author})" if author else ""
                lines.append(f"- {prefix}{desc} ({ref}){attribution}")

        lines.append("")

    # Summary statistics
    total = parsed_data.get("total_commits", parsed_data.get("total_prs", 0))
    lines.append("---")
    lines.append("")
    lines.append(f"**Full Changelog**: {total} changes from {len(categories)} categories")
    if repo_url:
        lines.append(f"**Compare**: [{repo_url}/compare/...{version}]({repo_url}/compare/...{version})")
    lines.append("")

    return "\n".join(lines)


def generate_keepachangelog(
    parsed_data: dict,
    version: str,
    date: Optional[str] = None,
) -> str:
    """Generate a CHANGELOG.md entry in Keep a Changelog format.

    See: https://keepachangelog.com/
    """
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Map internal categories to Keep a Changelog categories
    keepachangelog_map = {
        "Features": "Added",
        "Bug Fixes": "Fixed",
        "Performance": "Changed",
        "Security": "Security",
        "Documentation": "Changed",
        "Dependencies": "Changed",
        "Internal Changes": "Changed",
        "Reverts": "Removed",
        "Breaking Changes": "Changed",
    }

    # Regroup by Keep a Changelog categories
    regrouped: dict[str, list] = {}
    categories = parsed_data.get("categories", {})
    for category, items in categories.items():
        kac_category = keepachangelog_map.get(category, "Changed")
        regrouped.setdefault(kac_category, []).extend(items)

    kac_order = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]

    lines = []
    lines.append(f"## [{version}] - {date}")
    lines.append("")

    for kac_cat in kac_order:
        if kac_cat not in regrouped:
            continue
        items = regrouped[kac_cat]
        if not items:
            continue

        lines.append(f"### {kac_cat}")
        lines.append("")
        for item in items:
            desc = item.get("description", item.get("title", ""))
            lines.append(f"- {desc}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "parsed_commits.json"
    version = sys.argv[2] if len(sys.argv) > 2 else "v0.0.0"
    audience = sys.argv[3] if len(sys.argv) > 3 else "all"
    repo_url = sys.argv[4] if len(sys.argv) > 4 else None

    with open(input_file) as f:
        data = json.load(f)

    notes = generate_markdown(data, version, repo_url=repo_url, audience=audience)
    print(notes)

    # Also generate Keep a Changelog format
    kac = generate_keepachangelog(data, version)
    kac_path = "CHANGELOG_entry.md"
    with open(kac_path, "w") as f:
        f.write(kac)
    print(f"\nKeep a Changelog entry written to {kac_path}", file=sys.stderr)
```
