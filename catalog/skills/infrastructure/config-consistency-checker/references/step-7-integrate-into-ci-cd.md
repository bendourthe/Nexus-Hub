### Step 7: Integrate into CI/CD

**GitHub Actions Configuration Check** (`.github/workflows/config-check.yml`):

```yaml
name: Configuration Consistency Check

on:
  pull_request:
    paths:
      - "config/**"
      - ".env.*"
      - "k8s/**/configmap*.yaml"
  push:
    branches: [main]
    paths:
      - "config/**"
      - ".env.*"
  schedule:
    - cron: "0 8 * * 1"  # Weekly Monday at 08:00 UTC

jobs:
  check-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install pyyaml jsonschema

      - name: Run configuration comparison
        run: |
          python scripts/config_compare.py config-inventory.yaml config_findings.json
        continue-on-error: true

      - name: Run schema validation
        run: |
          python scripts/config_validate_schema.py config-inventory.yaml
        continue-on-error: true

      - name: Generate drift report
        run: |
          python scripts/generate_drift_report.py config_findings.json markdown drift_report.md

      - name: Post report as PR comment
        if: github.event_name == 'pull_request'
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          path: drift_report.md

      - name: Check for critical findings
        run: |
          CRITICAL=$(python -c "
          import json
          with open('config_findings.json') as f:
              findings = json.load(f)
          critical = [f for f in findings if f['severity'] == 'critical']
          print(len(critical))
          ")

          if [ "$CRITICAL" -gt 0 ]; then
            echo "CRITICAL configuration issues detected: $CRITICAL"
            echo "Review drift_report.md for details"
            exit 1
          fi

          echo "No critical configuration issues found"

      - name: Upload drift report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: config-drift-report
          path: drift_report.md
          retention-days: 30
```

**Complete Pipeline Script** (`scripts/check-config-consistency.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

INVENTORY="${1:-config-inventory.yaml}"
OUTPUT_DIR="${2:-.config-check}"

echo "=== Configuration Consistency Check ==="
echo "Inventory: $INVENTORY"
echo ""

mkdir -p "$OUTPUT_DIR"

# Step 1: Compare environments
echo "--- Step 1: Cross-Environment Comparison ---"
python scripts/config_compare.py "$INVENTORY" "$OUTPUT_DIR/findings.json" || true

# Step 2: Schema validation
echo ""
echo "--- Step 2: Schema Validation ---"
python scripts/config_validate_schema.py "$INVENTORY" || true

# Step 3: Generate report
echo ""
echo "--- Step 3: Drift Report ---"
python scripts/generate_drift_report.py "$OUTPUT_DIR/findings.json" markdown "$OUTPUT_DIR/drift_report.md"

# Step 4: Summary
echo ""
echo "=== Results ==="
CRITICAL=$(python -c "
import json
with open('$OUTPUT_DIR/findings.json') as f:
    findings = json.load(f)
critical = [f for f in findings if f['severity'] == 'critical']
print(len(critical))
")

echo "Report: $OUTPUT_DIR/drift_report.md"
echo "Critical findings: $CRITICAL"

if [ "$CRITICAL" -gt 0 ]; then
  echo ""
  echo "FAIL: Critical configuration drift detected"
  exit 1
fi

echo "PASS: No critical configuration drift"
```
