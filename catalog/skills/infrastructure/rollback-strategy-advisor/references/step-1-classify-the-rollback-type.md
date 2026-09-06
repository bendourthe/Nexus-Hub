### Step 1: Classify the Rollback Type

Before designing a rollback procedure, classify the deployment change to determine which rollback approach applies:

```
Rollback Type Assessment Matrix:

Change Type              | Rollback Approach     | Complexity | Data Risk
-------------------------|-----------------------|------------|----------
Stateless code change    | Immediate             | Low        | None
Configuration change     | Immediate             | Low        | None
Additive schema change   | Immediate (code only) | Low        | None
Destructive schema change| Data-aware            | High       | High
Multi-service change     | Coordinated           | High       | Medium
Feature flag release     | Flag toggle           | Low        | None
Infrastructure change    | Terraform/IaC revert  | Medium     | Low
Blue-green deployment    | Traffic switchback    | Low        | None
Canary deployment        | Weight reduction      | Low        | None
```

**Decision Tree Script** (`scripts/classify-rollback.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Rollback Classification ==="
echo ""
echo "1. Does this deployment include database schema changes?"
read -r HAS_SCHEMA

if [ "$HAS_SCHEMA" = "yes" ]; then
  echo "2. Are the schema changes destructive (dropping columns, renaming tables, changing types)?"
  read -r IS_DESTRUCTIVE

  if [ "$IS_DESTRUCTIVE" = "yes" ]; then
    echo ""
    echo "CLASSIFICATION: Data-Aware Rollback"
    echo "RISK: HIGH - Requires data migration reversal"
    echo "APPROACH: Use expand-contract pattern; do NOT use immediate rollback"
    echo "SEE: Step 3 (Database Migration Rollbacks)"
    exit 0
  else
    echo ""
    echo "CLASSIFICATION: Immediate Rollback (code only)"
    echo "RISK: LOW - Additive schema changes are backward-compatible"
    echo "APPROACH: Roll back application code; leave schema changes in place"
    echo "NOTE: Clean up unused schema additions in a future migration"
    exit 0
  fi
fi

echo "2. Does this deployment span multiple services?"
read -r MULTI_SERVICE

if [ "$MULTI_SERVICE" = "yes" ]; then
  echo ""
  echo "CLASSIFICATION: Coordinated Rollback"
  echo "RISK: HIGH - Service interdependencies require ordered rollback"
  echo "APPROACH: Roll back in reverse deployment order; verify contracts at each step"
  echo "SEE: Step 6 (Multi-Service Rollback Coordination)"
  exit 0
fi

echo "2. Is this a feature flag release?"
read -r IS_FLAG

if [ "$IS_FLAG" = "yes" ]; then
  echo ""
  echo "CLASSIFICATION: Feature Flag Rollback"
  echo "RISK: LOW - No deployment needed; toggle flag"
  echo "APPROACH: Disable the feature flag; verify behavior"
  echo "SEE: Step 4 (Feature Flag Rollbacks)"
  exit 0
fi

echo ""
echo "CLASSIFICATION: Immediate Rollback"
echo "RISK: LOW - Stateless change can be reverted directly"
echo "APPROACH: kubectl rollout undo / redeploy previous version"
echo "SEE: Step 2 (Immediate Rollback)"
```
