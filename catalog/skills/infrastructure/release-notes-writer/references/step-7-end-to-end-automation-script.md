### Step 7: End-to-End Automation Script

**Complete Release Notes Pipeline** (`scripts/release-notes-pipeline.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: release-notes-pipeline.sh <version> [previous_version] [audience]}"
PREV_VERSION="${2:-}"
AUDIENCE="${3:-all}"
REPO_URL="${REPO_URL:-$(git remote get-url origin | sed 's/\.git$//' | sed 's|git@github.com:|https://github.com/|')}"

echo "=== Release Notes Pipeline ==="
echo "Version:  $VERSION"
echo "Audience: $AUDIENCE"
echo "Repo:     $REPO_URL"

# Auto-detect previous version if not specified
if [ -z "$PREV_VERSION" ]; then
  PREV_VERSION=$(git tag --sort=-version:refname | grep -v "^${VERSION}$" | head -1)
  if [ -z "$PREV_VERSION" ]; then
    echo "ERROR: Could not detect previous version. Specify it explicitly."
    exit 1
  fi
fi
echo "Previous: $PREV_VERSION"
echo ""

# Step 1: Collect data
echo "--- Collecting changes ---"
bash scripts/collect-changes.sh "$PREV_VERSION" "$VERSION"

# Step 2: Parse commits
echo ""
echo "--- Parsing commits ---"
python scripts/parse_commits.py changes.json parsed_commits.json

# Step 3: Generate release notes
echo ""
echo "--- Generating release notes ---"
python scripts/generate_release_notes.py \
  parsed_commits.json \
  "$VERSION" \
  "$AUDIENCE" \
  "$REPO_URL" \
  > "release_notes_${VERSION}.md"

echo ""
echo "Release notes written to: release_notes_${VERSION}.md"
echo ""
echo "--- Preview ---"
head -40 "release_notes_${VERSION}.md"
```
