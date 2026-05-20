#!/usr/bin/env bash
# Usage Display - Stop Hook for Claude Code
# Shows a compact usage limits summary after each conversation turn.
# Part of Nexus-Hub
#
# How it works:
#   Fires on the Stop event (after Claude finishes responding).
#   Fetches usage data from the Anthropic OAuth API, caches for 5 minutes,
#   and displays a one-line summary to stderr when any metric exceeds 50%.
#   Completely silent when usage is healthy or if any dependency is missing.
#
# Requirements: curl, jq (fails silently without them)
# Cache: ~/.claude/.usage-cache.json (5-minute TTL)

# Never fail loudly - always exit 0
trap 'exit 0' ERR

# --- Configuration ---
DISPLAY_THRESHOLD=50        # Only show when any metric exceeds this %
CACHE_TTL_SECONDS=300       # 5 minutes

# --- Paths ---
CREDENTIALS_FILE="$HOME/.claude/.credentials.json"
CACHE_FILE="$HOME/.claude/.usage-cache.json"
API_URL="https://api.anthropic.com/api/oauth/usage"
BETA_HEADER="oauth-2025-04-20"

# --- Colors (ANSI) ---
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_ORANGE='\033[0;38;5;208m'
COLOR_RED='\033[0;31m'
COLOR_GRAY='\033[0;90m'

# --- Dependency check ---
command -v curl >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

# --- Color for a given percentage ---
color_for_percent() {
    local pct=$1
    if [ "$pct" -ge 90 ]; then
        echo -ne "$COLOR_RED"
    elif [ "$pct" -ge 75 ]; then
        echo -ne "$COLOR_ORANGE"
    elif [ "$pct" -ge 50 ]; then
        echo -ne "$COLOR_YELLOW"
    else
        echo -ne "$COLOR_GREEN"
    fi
}

# --- Format reset time from ISO 8601 ---
format_reset_time() {
    local iso_timestamp="$1"
    if [ -z "$iso_timestamp" ] || [ "$iso_timestamp" = "null" ]; then
        echo "N/A"
        return
    fi

    local reset_epoch
    reset_epoch=$(date -d "$iso_timestamp" +%s 2>/dev/null || date -jf "%Y-%m-%dT%H:%M:%S" "${iso_timestamp%%.*}" +%s 2>/dev/null)
    if [ -z "$reset_epoch" ]; then
        echo "N/A"
        return
    fi

    local now_epoch
    now_epoch=$(date +%s)
    local diff_seconds=$((reset_epoch - now_epoch))

    if [ "$diff_seconds" -le 0 ]; then
        echo "any moment"
        return
    fi

    local diff_minutes=$((diff_seconds / 60))
    if [ "$diff_minutes" -lt 60 ]; then
        echo "${diff_minutes}m"
        return
    fi

    local diff_hours=$((diff_minutes / 60))
    local remaining_min=$((diff_minutes % 60))
    if [ "$diff_hours" -lt 24 ]; then
        if [ "$remaining_min" -gt 0 ]; then
            echo "${diff_hours}h ${remaining_min}m"
        else
            echo "${diff_hours}h"
        fi
        return
    fi

    # More than 24 hours: show day and time
    if date --version >/dev/null 2>&1; then
        # GNU date
        date -d "$iso_timestamp" "+%a %l:%M %p" 2>/dev/null || echo "${diff_hours}h"
    else
        # BSD date (macOS)
        date -jf "%Y-%m-%dT%H:%M:%S" "${iso_timestamp%%.*}" "+%a %l:%M %p" 2>/dev/null || echo "${diff_hours}h"
    fi
}

# --- Check cache freshness ---
use_cache=false
if [ -f "$CACHE_FILE" ]; then
    cache_age=0
    if stat --version >/dev/null 2>&1; then
        # GNU stat
        cache_mtime=$(stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0)
    else
        # BSD stat (macOS)
        cache_mtime=$(stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)
    fi
    now_epoch=$(date +%s)
    cache_age=$((now_epoch - cache_mtime))

    if [ "$cache_age" -lt "$CACHE_TTL_SECONDS" ]; then
        use_cache=true
    fi
fi

# --- Fetch or use cached data ---
if [ "$use_cache" = true ]; then
    API_RESPONSE=$(cat "$CACHE_FILE" 2>/dev/null)
else
    # Read credentials
    [ -f "$CREDENTIALS_FILE" ] || exit 0
    TOKEN=$(jq -r '.claudeAiOauth.accessToken // empty' "$CREDENTIALS_FILE" 2>/dev/null)
    [ -n "$TOKEN" ] || exit 0

    # Check token expiry
    EXPIRES_AT=$(jq -r '.claudeAiOauth.expiresAt // 0' "$CREDENTIALS_FILE" 2>/dev/null)
    NOW_MS=$(($(date +%s) * 1000))
    if [ "$EXPIRES_AT" -gt 0 ] && [ "$NOW_MS" -ge "$EXPIRES_AT" ]; then
        exit 0  # Token expired
    fi

    # Fetch from API (3-second timeout to avoid blocking)
    API_RESPONSE=$(curl -s --max-time 3 \
        -H "Authorization: Bearer $TOKEN" \
        -H "anthropic-beta: $BETA_HEADER" \
        "$API_URL" 2>/dev/null)

    [ -n "$API_RESPONSE" ] || exit 0

    # Verify response is valid JSON with expected fields
    echo "$API_RESPONSE" | jq -e '.five_hour' >/dev/null 2>&1 || exit 0

    # Cache the response
    echo "$API_RESPONSE" > "$CACHE_FILE" 2>/dev/null
fi

# --- Parse metrics ---
SESSION=$(echo "$API_RESPONSE" | jq -r '.five_hour.utilization // 0' 2>/dev/null)
WEEKLY=$(echo "$API_RESPONSE" | jq -r '.seven_day.utilization // 0' 2>/dev/null)
SONNET=$(echo "$API_RESPONSE" | jq -r '.seven_day_sonnet.utilization // 0' 2>/dev/null)

# Round to integers
SESSION=${SESSION%.*}
WEEKLY=${WEEKLY%.*}
SONNET=${SONNET%.*}

# Default to 0 if empty
SESSION=${SESSION:-0}
WEEKLY=${WEEKLY:-0}
SONNET=${SONNET:-0}

# --- Check threshold ---
if [ "$SESSION" -lt "$DISPLAY_THRESHOLD" ] && [ "$WEEKLY" -lt "$DISPLAY_THRESHOLD" ] && [ "$SONNET" -lt "$DISPLAY_THRESHOLD" ]; then
    exit 0  # All metrics below threshold, stay silent
fi

# --- Find highest metric and its reset time ---
HIGHEST_NAME="Session"
HIGHEST_PCT=$SESSION
HIGHEST_RESET_FIELD=".five_hour.resets_at"

if [ "$WEEKLY" -gt "$HIGHEST_PCT" ]; then
    HIGHEST_NAME="Weekly"
    HIGHEST_PCT=$WEEKLY
    HIGHEST_RESET_FIELD=".seven_day.resets_at"
fi

if [ "$SONNET" -gt "$HIGHEST_PCT" ]; then
    HIGHEST_NAME="Sonnet"
    HIGHEST_PCT=$SONNET
    HIGHEST_RESET_FIELD=".seven_day_sonnet.resets_at"
fi

RESET_ISO=$(echo "$API_RESPONSE" | jq -r "$HIGHEST_RESET_FIELD // empty" 2>/dev/null)
RESET_DISPLAY=$(format_reset_time "$RESET_ISO")

# --- Build output ---
SESSION_COLOR=$(color_for_percent "$SESSION")
WEEKLY_COLOR=$(color_for_percent "$WEEKLY")
SONNET_COLOR=$(color_for_percent "$SONNET")

OUTPUT="${COLOR_GRAY}Usage:${COLOR_RESET}"
OUTPUT+=" Session ${SESSION_COLOR}${SESSION}%${COLOR_RESET}"
OUTPUT+=" | Weekly ${WEEKLY_COLOR}${WEEKLY}%${COLOR_RESET}"
OUTPUT+=" | Sonnet ${SONNET_COLOR}${SONNET}%${COLOR_RESET}"

if [ -n "$RESET_DISPLAY" ] && [ "$RESET_DISPLAY" != "N/A" ]; then
    OUTPUT+="  ${COLOR_GRAY}(${HIGHEST_NAME} resets in ${RESET_DISPLAY})${COLOR_RESET}"
fi

# Output to stderr (Claude Code displays hook stderr to the user)
echo -e "$OUTPUT" >&2

exit 0
