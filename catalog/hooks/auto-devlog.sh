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
COLOR_YELLOW='\033[0;33m'
COLOR_CYAN='\033[0;36m'

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: auto-devlog]"
# Make CR, LF, ESC and the other C0 control characters in an echoed value
# visible, so a file name or command cannot start a forged tagged line.
_nexus_esc() {
  local s=$1 ctrl i c r
  ctrl=$'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x7f'
  for ((i = 0; i < ${#ctrl}; i++)); do
    c=${ctrl:i:1}
    case $c in
      $'\t') r='\t' ;; $'\n') r='\n' ;; $'\r') r='\r' ;; $'\x1b') r='\x1b' ;; $'\x7f') r='\x7f' ;;
      *) printf -v r '%s%02x' '\x' $((i + 1)) ;;
    esac
    s=${s//"$c"/"$r"}
  done
  printf '%s' "$s"
}
# Print the tag and the message to stderr; every further argument is a
# continuation line printed as is. $1 is an optional color code for the tag.
_nexus_msg() {
  local color=$1 message=$2 line
  shift 2
  printf '%b%s%b %s\n' "$color" "$_NEXUS_TAG" "${color:+$COLOR_RESET}" "$message" >&2
  for line in "$@"; do printf '%s\n' "$line" >&2; done
}

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
    _nexus_msg "$COLOR_CYAN" "docs/DEVLOG.md is a per-release index; skipping. Session narrative belongs in docs/v*/*/development/history/."
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
    RECENT_COMMITS=$(git -C "$GIT_ROOT" log --oneline -10 --after="$LAST_ENTRY_DATE" 2>/dev/null)
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

# Bound display subjects, preserving the separate commit identifier.
# Pipe input so Git Bash does not stall preparing a large here-string.
RECENT_COMMITS=$(printf '%s\n' "$RECENT_COMMITS" | while IFS= read -r line; do
    [ -n "$line" ] || continue
    subject="${line#* }"
    printf '%s %s\n' "${line%% *}" "${subject:0:200}"
done)

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
            _nexus_msg "$COLOR_CYAN" "AI entry written to DEVLOG.md" && exit 0
    else
        claude --print --max-turns 1 "$AI_PROMPT" >/dev/null 2>&1 && \
            _nexus_msg "$COLOR_CYAN" "AI entry written to DEVLOG.md" && exit 0
    fi
    # Fall through to shell-only entry on failure
    _nexus_msg "$COLOR_YELLOW" "AI enrichment failed - writing shell summary instead."
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
FIRST_H2_LINE=$(grep -m 1 -n '^## \[' "$DEVLOG" 2>/dev/null | cut -d: -f1)
if [ -n "${FIRST_H2_LINE:-}" ] && echo "$FIRST_H2_LINE" | grep -qE '^[0-9]+$'; then
    INSERT_LINE=$FIRST_H2_LINE
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

_nexus_msg "$COLOR_CYAN" "entry prepended ($COMMIT_COUNT commits since $(_nexus_esc "${LAST_ENTRY_DATE:-7 days ago}"))"

exit 0
