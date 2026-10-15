### Step 5: Implement Secret Reference Validation

Verify that all secret references in configuration actually point to existing secrets.

**Secret Reference Validator** (`scripts/validate_secrets.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:?Usage: validate_secrets.sh <environment> <config_file>}"
CONFIG_FILE="${2:?Missing config file path}"
SECRET_STORE="${3:-aws-secrets-manager}"

echo "=== Secret Reference Validation ==="
echo "Environment:  $ENVIRONMENT"
echo "Config file:  $CONFIG_FILE"
echo "Secret store: $SECRET_STORE"
echo ""

ERRORS=0
WARNINGS=0
CHECKED=0

# Extract secret references from config (values starting with arn:, vault:, ssm:)
while IFS='=' read -r KEY VALUE; do
  # Skip comments and empty lines
  [[ -z "$KEY" || "$KEY" =~ ^# ]] && continue

  # Remove quotes from value
  VALUE=$(echo "$VALUE" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

  case "$VALUE" in
    arn:aws:secretsmanager:*)
      CHECKED=$((CHECKED + 1))
      SECRET_ID=$(echo "$VALUE" | sed 's|arn:aws:secretsmanager:[^:]*:[^:]*:secret:||')
      echo -n "Checking AWS secret: $SECRET_ID ... "
      if aws secretsmanager describe-secret --secret-id "$SECRET_ID" > /dev/null 2>&1; then
        echo "OK"
      else
        echo "MISSING"
        ERRORS=$((ERRORS + 1))
        echo "  ERROR: Secret '$SECRET_ID' referenced by '$KEY' does not exist"
      fi
      ;;

    ssm:*)
      CHECKED=$((CHECKED + 1))
      PARAM_NAME="${VALUE#ssm:}"
      echo -n "Checking SSM parameter: $PARAM_NAME ... "
      if aws ssm get-parameter --name "$PARAM_NAME" > /dev/null 2>&1; then
        echo "OK"
      else
        echo "MISSING"
        ERRORS=$((ERRORS + 1))
        echo "  ERROR: SSM parameter '$PARAM_NAME' referenced by '$KEY' does not exist"
      fi
      ;;

    vault:*)
      CHECKED=$((CHECKED + 1))
      VAULT_PATH="${VALUE#vault:}"
      echo -n "Checking Vault path: $VAULT_PATH ... "
      if vault kv get "$VAULT_PATH" > /dev/null 2>&1; then
        echo "OK"
      else
        echo "MISSING"
        ERRORS=$((ERRORS + 1))
        echo "  ERROR: Vault secret '$VAULT_PATH' referenced by '$KEY' does not exist"
      fi
      ;;

    *PASSWORD*|*SECRET*|*API_KEY*|*TOKEN*)
      # Value looks like it might be a plaintext secret
      if [[ "$VALUE" != *"arn:"* && "$VALUE" != *"vault:"* && "$VALUE" != *"ssm:"* ]]; then
        WARNINGS=$((WARNINGS + 1))
        echo "  WARNING: '$KEY' may contain a plaintext secret (not a reference)"
      fi
      ;;
  esac
done < "$CONFIG_FILE"

echo ""
echo "=== Results ==="
echo "Checked:  $CHECKED secret references"
echo "Errors:   $ERRORS (missing secrets)"
echo "Warnings: $WARNINGS (potential plaintext secrets)"

if [ "$ERRORS" -gt 0 ]; then
  exit 1
fi
```
