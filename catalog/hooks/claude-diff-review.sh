#!/usr/bin/env bash
# claude-diff-review.sh - opt-in git pre-commit hook (Nexus-Hub).
# Pipes the staged diff through `claude -p` for a quick LLM review of
# hardcoded secrets, debug artifacts (console.log, print, debugger),
# unfinished TODOs, and large commented-out code blocks.
#
# Install:
#   /install-claude-pre-commit-hook   (run from inside the target repo)
#
# Per-commit bypass:
#   DEVAI_DIFF_REVIEW_DISABLE=1 git commit -m "..."
#   git commit -n -m "..."   (--no-verify; skips ALL pre-commit hooks)
#
# Diff-size cap (default 50 KB, raise to allow larger commits):
#   DEVAI_DIFF_REVIEW_MAX_BYTES=204800 git commit -m "..."
#
# Disable globally for a repo:
#   rm .git/hooks/pre-commit

set -euo pipefail

# --- Bypass paths --------------------------------------------------------
if [ "${DEVAI_DIFF_REVIEW_DISABLE:-0}" = "1" ]; then
    exit 0
fi

# Skip during merge / cherry-pick / rebase: the staged diff is not author-curated
# and re-reviewing inherited code would block legitimate merges.
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || echo "")
if [ -n "$GIT_DIR" ]; then
    if [ -e "$GIT_DIR/MERGE_HEAD" ] \
       || [ -e "$GIT_DIR/CHERRY_PICK_HEAD" ] \
       || [ -e "$GIT_DIR/REBASE_HEAD" ] \
       || [ -d "$GIT_DIR/rebase-merge" ] \
       || [ -d "$GIT_DIR/rebase-apply" ]; then
        exit 0
    fi
fi

# --- Locate claude CLI ---------------------------------------------------
if ! command -v claude >/dev/null 2>&1; then
    echo "[claude-diff-review] WARNING: claude CLI not found on PATH; skipping review." >&2
    echo "[claude-diff-review] Install Claude Code (https://claude.ai/download) or set DEVAI_DIFF_REVIEW_DISABLE=1 to silence this warning." >&2
    exit 0
fi

# --- Get staged diff -----------------------------------------------------
DIFF=$(git diff --cached --no-color 2>/dev/null || echo "")
if [ -z "$DIFF" ]; then
    exit 0
fi

# --- Cap diff size -------------------------------------------------------
MAX_BYTES="${DEVAI_DIFF_REVIEW_MAX_BYTES:-51200}"
DIFF_BYTES=${#DIFF}
if [ "$DIFF_BYTES" -gt "$MAX_BYTES" ]; then
    echo "[claude-diff-review] WARNING: staged diff is ${DIFF_BYTES} bytes (cap=${MAX_BYTES}); skipping review." >&2
    echo "[claude-diff-review] Raise the cap with DEVAI_DIFF_REVIEW_MAX_BYTES=N or commit fewer files at a time." >&2
    exit 0
fi

# --- Build review prompt -------------------------------------------------
PROMPT=$(cat <<'EOF'
You are a strict pre-commit reviewer for a staged git diff. Inspect ONLY the lines added in this diff (lines starting with `+` excluding the `+++` file headers). Look for:

1. Hardcoded credentials: API keys, tokens, passwords, private keys, connection strings with embedded secrets. Any value that looks credential-shaped on a literal assignment.
2. Debug artifacts that look unintentional in production code: console.log / console.debug / console.error, print() / println() / fmt.Println, debugger;, alert(), pdb.set_trace, dd() / dump() / var_dump.
3. Unfinished work newly added in this diff: TODO / FIXME / XXX / HACK comments without ticket references or owner, AND bare placeholder values like "todo", "fixme", "tbd", "xxx", "lorem ipsum".
4. Commented-out code blocks larger than 3 contiguous lines.

Respond on the FIRST LINE in EXACTLY this format and nothing else:

VERDICT: PASS

or

VERDICT: WARN

or

VERDICT: BLOCK

Then a blank line, then concise findings under 200 words. Use file:line references where possible.

Use BLOCK only for clear hardcoded credentials. Use WARN for debug artifacts, unfinished TODOs, or large commented-out blocks. Use PASS otherwise.

Default to PASS for: documentation-only diffs, lockfiles (package-lock.json, poetry.lock, go.sum), generated code, test fixtures with obvious dummy values ("password123", "test@example.com"), and config templates that explicitly mark placeholder values ("REPLACE_ME", "<your-key-here>").

Diff follows:

EOF
)

# --- Run claude (fail-open on any error) ---------------------------------
RESPONSE=$(printf '%s' "$DIFF" | claude -p "$PROMPT" 2>/dev/null || true)
if [ -z "$RESPONSE" ]; then
    echo "[claude-diff-review] WARNING: claude CLI returned no output; allowing commit." >&2
    exit 0
fi

# --- Parse verdict -------------------------------------------------------
VERDICT_LINE=$(echo "$RESPONSE" | grep -m1 '^VERDICT:' || echo "")
VERDICT=$(echo "$VERDICT_LINE" | sed -E 's/^VERDICT:[[:space:]]*//' | tr -d '[:space:]')

case "$VERDICT" in
    PASS)
        exit 0
        ;;
    WARN)
        echo "[claude-diff-review] WARN:" >&2
        echo "$RESPONSE" | tail -n +2 >&2
        echo "" >&2
        echo "[claude-diff-review] Commit allowed; review the warnings above and consider amending." >&2
        exit 0
        ;;
    BLOCK)
        echo "[claude-diff-review] BLOCK:" >&2
        echo "$RESPONSE" | tail -n +2 >&2
        echo "" >&2
        echo "[claude-diff-review] Commit refused. Fix the issue, or bypass this commit with: DEVAI_DIFF_REVIEW_DISABLE=1 git commit ..." >&2
        exit 1
        ;;
    *)
        echo "[claude-diff-review] WARNING: unparseable verdict from claude (expected PASS|WARN|BLOCK); allowing commit." >&2
        exit 0
        ;;
esac
