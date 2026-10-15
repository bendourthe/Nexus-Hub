### Step 1: Collect Change History

Gather all changes between two references (typically the previous release tag and the current HEAD or new tag).

**Git Log Collection Script** (`scripts/collect-changes.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

FROM_REF="${1:?Usage: collect-changes.sh <from_ref> <to_ref>}"
TO_REF="${2:-HEAD}"
OUTPUT="${3:-changes.json}"

echo "Collecting changes from $FROM_REF to $TO_REF"

# Collect commits with structured output
git log "${FROM_REF}..${TO_REF}" \
  --pretty=format:'{%n  "hash": "%H",%n  "short_hash": "%h",%n  "author": "%an",%n  "email": "%ae",%n  "date": "%aI",%n  "subject": "%s",%n  "body": "%b"%n},' \
  > /tmp/commits_raw.txt

# Wrap in JSON array (remove trailing comma, add brackets)
echo "[" > "$OUTPUT"
sed '$ s/,$//' /tmp/commits_raw.txt >> "$OUTPUT"
echo "]" >> "$OUTPUT"

COMMIT_COUNT=$(git rev-list --count "${FROM_REF}..${TO_REF}")
echo "Collected $COMMIT_COUNT commits -> $OUTPUT"

# Collect merge commits (PRs) separately
echo ""
echo "Merge commits (PRs):"
git log "${FROM_REF}..${TO_REF}" --merges --oneline
```

**GitHub PR Collection** (using `gh` CLI):

```bash
#!/usr/bin/env bash
set -euo pipefail

FROM_DATE="${1:?Usage: collect-prs.sh <from_date> <to_date>}"
TO_DATE="${2:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
OUTPUT="${3:-prs.json}"

echo "Collecting merged PRs from $FROM_DATE to $TO_DATE"

gh pr list \
  --state merged \
  --search "merged:${FROM_DATE}..${TO_DATE}" \
  --json number,title,labels,author,body,mergedAt,headRefName \
  --limit 500 \
  > "$OUTPUT"

PR_COUNT=$(jq length "$OUTPUT")
echo "Collected $PR_COUNT merged PRs -> $OUTPUT"
```
