#!/usr/bin/env bash
# Auto DevLog - Stop Hook for Claude Code
# Automatically prepends a git-summary entry to DEVLOG.md at session end.
# Part of Nexus-Hub
#
# How it works:
#   Fires on the Stop event. Checks whether DEVLOG.md exists in the docs/ directory
#   and whether there are at least MIN_COMMITS new commits since the last
#   recorded entry date. If so, prepends a structured summary block.
#
# Opt-in:        set AUTO_DEVLOG=1 in your shell profile (e.g. ~/.bashrc).
# AI enrichment: also set AUTO_DEVLOG_AI=1 (requires claude CLI, uses tokens).
# Min commits:   AUTO_DEVLOG_MIN_COMMITS=2 (default; override as needed).
#
# Requirements: git, grep, awk, date (jq optional)
# Exit code: always 0 - Stop hooks must never block.

# Never fail loudly
trap 'exit 0' ERR
set -uo pipefail 2>/dev/null || true

# --- Colors (consistent with other Nexus-Hub hooks) ---
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_CYAN='\033[0;36m'

# --- Opt-in gate ---
[ "${AUTO_DEVLOG:-}" = "1" ] || exit 0

# --- Configuration ---
MIN_COMMITS="${AUTO_DEVLOG_MIN_COMMITS:-2}"
SKIP_IF_MODIFIED_WITHIN=300   # seconds; prevents double-run within 5 minutes

# --- Dependencies ---
command -v git >/dev/null 2>&1 || exit 0

# --- Must be inside a git repo with a DEVLOG.md ---
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
DEVLOG="$GIT_ROOT/docs/DEVLOG.md"
[ -f "$DEVLOG" ] || exit 0

# --- Index-format guard: never prepend narrative into a per-release index ---
# docs/DEVLOG.md may be a bounded per-release INDEX (a header plus one table row
# per release) rather than an append-only narrative log. Prepending an entry into
# that table corrupts it, and the corruption is silent. Detect the index header
# and stand down; session narrative belongs in the per-version
# development/history/ file instead (see the session-history skill).
if grep -qE '^[[:space:]]*\|[[:space:]]*Date[[:space:]]*\|[[:space:]]*Version[[:space:]]*\|' "$DEVLOG" 2>/dev/null; then
    printf '%b[auto-devlog]%b docs/DEVLOG.md is a per-release index; skipping. Session narrative belongs in docs/v*/*/development/history/.\n' \
        "$COLOR_CYAN" "$COLOR_RESET" >&2
    exit 0
fi

# --- Consume stdin (Stop hooks receive JSON payload) ---
# shellcheck disable=SC2034  # INPUT intentionally unused; drains stdin to prevent SIGPIPE
INPUT=$(cat 2>/dev/null || true)

# --- Double-run guard: skip if DEVLOG.md was modified recently ---
NOW_EPOCH=$(date +%s 2>/dev/null) || exit 0
if stat --version >/dev/null 2>&1; then
    # GNU stat (Linux, Git Bash on Windows)
    DEVLOG_MTIME=$(stat -c %Y "$DEVLOG" 2>/dev/null || echo 0)
else
    # BSD stat (macOS)
    DEVLOG_MTIME=$(stat -f %m "$DEVLOG" 2>/dev/null || echo 0)
fi
DEVLOG_AGE=$(( NOW_EPOCH - DEVLOG_MTIME ))
[ "$DEVLOG_AGE" -lt "$SKIP_IF_MODIFIED_WITHIN" ] && exit 0

# --- Parse date of the last DEVLOG entry ---
# Matches heading formats: ## [YYYY-MM-DD ...] or ## [YYYY-MM-DD HH:MM ...]
LAST_ENTRY_DATE=$(grep -m 1 '^## \[' "$DEVLOG" 2>/dev/null \
    | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)

# --- Count commits since last entry ---
if [ -n "${LAST_ENTRY_DATE:-}" ]; then
    COMMIT_COUNT=$(git -C "$GIT_ROOT" log --oneline --after="$LAST_ENTRY_DATE" 2>/dev/null | wc -l | tr -d ' ')
else
    COMMIT_COUNT=$(git -C "$GIT_ROOT" log --oneline --after="7 days ago" 2>/dev/null | wc -l | tr -d ' ')
fi
COMMIT_COUNT="${COMMIT_COUNT:-0}"
echo "$COMMIT_COUNT" | grep -qE '^[0-9]+$' || COMMIT_COUNT=0
[ "$COMMIT_COUNT" -ge "$MIN_COMMITS" ] || exit 0

# --- Gather session data ---
TIMESTAMP=$(date "+%Y-%m-%d %H:%M" 2>/dev/null || echo "unknown")
BRANCH=$(git -C "$GIT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

if [ -n "${LAST_ENTRY_DATE:-}" ]; then
    RECENT_COMMITS=$(git -C "$GIT_ROOT" log --oneline --after="$LAST_ENTRY_DATE" 2>/dev/null | head -10)
    BASE_HASH=$(git -C "$GIT_ROOT" log --format="%H" --before="$LAST_ENTRY_DATE" -1 2>/dev/null || true)
else
    RECENT_COMMITS=$(git -C "$GIT_ROOT" log --oneline -10 2>/dev/null)
    BASE_HASH=""
fi

if [ -n "${BASE_HASH:-}" ]; then
    FILES_CHANGED=$(git -C "$GIT_ROOT" diff --name-only "$BASE_HASH" HEAD 2>/dev/null | head -20)
else
    FILES_CHANGED=$(git -C "$GIT_ROOT" diff --name-only "HEAD~${COMMIT_COUNT}" HEAD 2>/dev/null | head -20 || true)
fi

# --- Optional AI enrichment path ---
# Set AUTO_DEVLOG_AI=1 for a richer, AI-written entry (uses claude CLI + tokens).
# Uses a compact inline prompt rather than the full update-devlog command, which
# contains an iterative refinement loop unsuitable for non-interactive --print mode.
if [ "${AUTO_DEVLOG_AI:-}" = "1" ] && command -v claude >/dev/null 2>&1; then
    AI_PROMPT="You are updating docs/DEVLOG.md for the '$(basename "$GIT_ROOT")' project.
Read docs/DEVLOG.md to understand its exact heading style and section format.
Write ONE new entry to prepend above the first ## heading, using timestamp: $TIMESTAMP.
Base it on these commits:
$RECENT_COMMITS

Files changed:
$FILES_CHANGED

Write ONLY the entry block - no preamble, no commentary. Then write the updated file."

    if command -v timeout >/dev/null 2>&1; then
        timeout 30 claude --print --max-turns 1 "$AI_PROMPT" >/dev/null 2>&1 && \
            echo -e "${COLOR_CYAN}[auto-devlog]${COLOR_RESET} ${COLOR_GREEN}AI entry written to DEVLOG.md${COLOR_RESET}" >&2 && exit 0
    else
        claude --print --max-turns 1 "$AI_PROMPT" >/dev/null 2>&1 && \
            echo -e "${COLOR_CYAN}[auto-devlog]${COLOR_RESET} ${COLOR_GREEN}AI entry written to DEVLOG.md${COLOR_RESET}" >&2 && exit 0
    fi
    # Fall through to shell-only entry on failure
    echo -e "${COLOR_YELLOW}[auto-devlog]${COLOR_RESET} AI enrichment failed - writing shell summary instead." >&2
fi

# --- Build shell-only entry ---
ENTRY="## [$TIMESTAMP] - Session auto-summary [auto]\n\n"
ENTRY+="### What Changed\n\n"
while IFS= read -r line; do
    [ -n "$line" ] && ENTRY+="- $line\n"
done <<< "$RECENT_COMMITS"

if [ -n "${FILES_CHANGED:-}" ]; then
    ENTRY+="\n### Files Modified\n\n"
    while IFS= read -r line; do
        [ -n "$line" ] && ENTRY+="- \`$line\`\n"
    done <<< "$FILES_CHANGED"
fi

ENTRY+="\n### Current Status\n\nAuto-captured at session end on branch \`$BRANCH\`. Review and annotate as needed.\n\n---\n\n"

# --- Prepend above the first ## heading (DEVLOG is newest-first) ---
# awk is used instead of sed -i to avoid BSD/GNU portability issues.
FIRST_H2_LINE=$(grep -n '^## \[' "$DEVLOG" 2>/dev/null | head -1 | cut -d: -f1)
if [ -n "${FIRST_H2_LINE:-}" ] && echo "$FIRST_H2_LINE" | grep -qE '^[0-9]+$'; then
    INSERT_LINE=$(( FIRST_H2_LINE - 1 ))
    TMPFILE=$(mktemp 2>/dev/null) || exit 0
    awk -v ins="$INSERT_LINE" -v entry="$ENTRY" '
        NR == ins { printf "%s", entry }
        { print }
    ' "$DEVLOG" > "$TMPFILE" 2>/dev/null && mv "$TMPFILE" "$DEVLOG" 2>/dev/null
    rm -f "$TMPFILE" 2>/dev/null || true
else
    # No existing ## heading found; append to end
    printf "\n%s" "$ENTRY" >> "$DEVLOG" 2>/dev/null || true
fi

echo -e "${COLOR_CYAN}[auto-devlog]${COLOR_RESET} ${COLOR_GREEN}entry prepended ($COMMIT_COUNT commits since ${LAST_ENTRY_DATE:-7 days ago})${COLOR_RESET}" >&2

exit 0
