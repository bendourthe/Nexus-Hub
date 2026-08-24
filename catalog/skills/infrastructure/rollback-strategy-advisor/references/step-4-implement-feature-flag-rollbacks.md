### Step 4: Implement Feature Flag Rollbacks

Feature flags enable instant rollback without deployment by toggling the flag to disable the new behavior.

**Feature Flag Rollback Script** (`scripts/rollback-feature-flag.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

FLAG_NAME="${1:?Usage: rollback-feature-flag.sh <flag_name> <provider>}"
PROVIDER="${2:?Missing provider (launchdarkly|unleash|custom)}"

echo "=== Feature Flag Rollback ==="
echo "Flag:     $FLAG_NAME"
echo "Provider: $PROVIDER"
echo ""

case "$PROVIDER" in
  launchdarkly)
    # Use LaunchDarkly API to disable the flag
    LD_API_KEY="${LD_API_KEY:?Missing LD_API_KEY environment variable}"
    LD_PROJECT="${LD_PROJECT:-default}"
    LD_ENVIRONMENT="${LD_ENVIRONMENT:-production}"

    echo "Disabling flag via LaunchDarkly API..."
    RESPONSE=$(curl -s -w "\n%{http_code}" \
      -X PATCH \
      -H "Authorization: ${LD_API_KEY}" \
      -H "Content-Type: application/json; domain-model=launchdarkly.semanticpatch" \
      -d "{
        \"environmentKey\": \"${LD_ENVIRONMENT}\",
        \"instructions\": [
          { \"kind\": \"turnFlagOff\" }
        ]
      }" \
      "https://app.launchdarkly.com/api/v2/flags/${LD_PROJECT}/${FLAG_NAME}")

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    if [ "$HTTP_CODE" = "200" ]; then
      echo "Flag disabled successfully"
    else
      echo "Failed to disable flag (HTTP $HTTP_CODE)"
      echo "$RESPONSE" | head -n -1
      exit 1
    fi
    ;;

  unleash)
    UNLEASH_URL="${UNLEASH_URL:?Missing UNLEASH_URL}"
    UNLEASH_TOKEN="${UNLEASH_TOKEN:?Missing UNLEASH_TOKEN}"

    echo "Disabling flag via Unleash API..."
    curl -s -X POST \
      -H "Authorization: ${UNLEASH_TOKEN}" \
      "${UNLEASH_URL}/api/admin/projects/default/features/${FLAG_NAME}/environments/production/off"
    echo "Flag disabled"
    ;;

  custom)
    # For custom feature flag stores (Redis, database, config file)
    REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
    echo "Disabling flag in Redis..."
    redis-cli -u "$REDIS_URL" SET "feature:${FLAG_NAME}" "false"
    redis-cli -u "$REDIS_URL" SET "feature:${FLAG_NAME}:disabled_at" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    redis-cli -u "$REDIS_URL" SET "feature:${FLAG_NAME}:disabled_reason" "rollback"
    echo "Flag disabled in Redis"
    ;;
esac

echo ""
echo "=== Verification ==="
echo "Wait 30 seconds for flag propagation, then verify:"
echo "  1. Check application behavior reflects the disabled state"
echo "  2. Monitor error rates for improvement"
echo "  3. Confirm no users are receiving the disabled feature"
```

**Application-Level Feature Flag Pattern (Python)**:

```python
"""Feature flag wrapper with rollback-safe defaults."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class FlagState:
    enabled: bool
    rollback_reason: Optional[str] = None
    disabled_at: Optional[datetime] = None


class FeatureFlagManager:
    """Manages feature flags with safe defaults and rollback tracking."""

    def __init__(self, provider):
        self.provider = provider
        self._rollback_log = []

    def is_enabled(self, flag_name: str, default: bool = False) -> bool:
        """Check if a feature flag is enabled. Returns default on any error."""
        try:
            return self.provider.get_flag(flag_name)
        except Exception:
            logger.warning(
                "Failed to read flag %s, returning default: %s",
                flag_name,
                default,
            )
            return default

    def rollback_flag(self, flag_name: str, reason: str) -> FlagState:
        """Disable a feature flag and record the rollback."""
        try:
            self.provider.set_flag(flag_name, False)
            state = FlagState(
                enabled=False,
                rollback_reason=reason,
                disabled_at=datetime.utcnow(),
            )
            self._rollback_log.append({
                "flag": flag_name,
                "reason": reason,
                "timestamp": state.disabled_at.isoformat(),
            })
            logger.info("Rolled back flag %s: %s", flag_name, reason)
            return state
        except Exception:
            logger.exception("Failed to roll back flag %s", flag_name)
            raise
```
