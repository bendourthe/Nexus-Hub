### Step 5: Automate Release Note Generation in CI/CD

**GitHub Actions Workflow** (`.github/workflows/release-notes.yml`):

```yaml
name: Generate Release Notes

on:
  release:
    types: [created]
  workflow_dispatch:
    inputs:
      tag:
        description: "Release tag (e.g., v2.5.0)"
        required: true
        type: string
      previous_tag:
        description: "Previous tag for comparison (auto-detected if empty)"
        required: false
        type: string

jobs:
  generate-notes:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Determine version range
        id: range
        run: |
          TAG="${{ inputs.tag || github.event.release.tag_name }}"
          echo "tag=$TAG" >> "$GITHUB_OUTPUT"

          if [ -n "${{ inputs.previous_tag }}" ]; then
            PREV="${{ inputs.previous_tag }}"
          else
            # Find the previous tag automatically
            PREV=$(git tag --sort=-creatordate | grep -A1 "^${TAG}$" | tail -1)
            if [ -z "$PREV" ] || [ "$PREV" = "$TAG" ]; then
              # Fall back to the tag before this one by date
              PREV=$(git tag --sort=-creatordate | sed -n '2p')
            fi
          fi

          echo "previous_tag=$PREV" >> "$GITHUB_OUTPUT"
          echo "Generating notes for $PREV..$TAG"

      - name: Collect commits
        run: |
          bash scripts/collect-changes.sh \
            "${{ steps.range.outputs.previous_tag }}" \
            "${{ steps.range.outputs.tag }}"

      - name: Collect PRs
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          PREV_DATE=$(git log -1 --format=%aI "${{ steps.range.outputs.previous_tag }}")
          TAG_DATE=$(git log -1 --format=%aI "${{ steps.range.outputs.tag }}")
          bash scripts/collect-prs.sh "$PREV_DATE" "$TAG_DATE"

      - name: Parse and categorize
        run: |
          python scripts/parse_commits.py changes.json parsed_commits.json
          python scripts/categorize_prs.py prs.json categorized_prs.json

      - name: Generate release notes
        id: notes
        run: |
          REPO_URL="${{ github.server_url }}/${{ github.repository }}"
          python scripts/generate_release_notes.py \
            parsed_commits.json \
            "${{ steps.range.outputs.tag }}" \
            "all" \
            "$REPO_URL" \
            > release_notes.md

          echo "Generated release notes:"
          cat release_notes.md

      - name: Update GitHub Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release edit "${{ steps.range.outputs.tag }}" \
            --notes-file release_notes.md

      - name: Update CHANGELOG.md
        run: |
          if [ -f CHANGELOG.md ]; then
            # Insert new entry after the header
            python -c "
          import sys
          with open('CHANGELOG.md') as f:
              content = f.read()
          with open('CHANGELOG_entry.md') as f:
              entry = f.read()
          # Insert after the first '# Changelog' line
          marker = '# Changelog'
          if marker in content:
              idx = content.index(marker) + len(marker)
              # Find end of that line
              newline_idx = content.index('\n', idx)
              content = content[:newline_idx+1] + '\n' + entry + content[newline_idx+1:]
          else:
              content = '# Changelog\n\n' + entry + content
          with open('CHANGELOG.md', 'w') as f:
              f.write(content)
          "
            echo "CHANGELOG.md updated"
          fi
```

**GitLab CI Release Notes Job**:

```yaml
generate-release-notes:
  stage: release
  image: python:3.12-slim
  before_script:
    - apt-get update && apt-get install -y git jq
    - pip install --quiet requests
  script:
    - |
      PREV_TAG=$(git tag --sort=-creatordate | sed -n '2p')
      CURRENT_TAG=$CI_COMMIT_TAG
      echo "Generating notes for $PREV_TAG..$CURRENT_TAG"

      bash scripts/collect-changes.sh "$PREV_TAG" "$CURRENT_TAG"
      python scripts/parse_commits.py changes.json parsed_commits.json
      python scripts/generate_release_notes.py parsed_commits.json "$CURRENT_TAG" all > release_notes.md

      # Update GitLab Release description via API
      ENCODED_TAG=$(echo "$CURRENT_TAG" | jq -sRr @uri)
      curl --request PUT \
        --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
        --header "Content-Type: application/json" \
        --data "{\"description\": $(jq -Rs . release_notes.md)}" \
        "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/releases/${ENCODED_TAG}"
  rules:
    - if: $CI_COMMIT_TAG
```
