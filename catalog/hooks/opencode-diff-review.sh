#!/usr/bin/env bash
# opencode-diff-review.sh - opt-in git pre-commit hook (Nexus-Hub).
# Pipes the staged diff through `opencode run` (OpenCode CLI) for an LLM review of
# hardcoded secrets, debug artifacts (console.log, print, debugger),
# unfinished TODOs, and large commented-out code blocks.
#
# Independent of the Claude / Gemini / Codex variants - calls the OpenCode CLI only.
# OpenCode is a multi-provider agentic CLI (https://github.com/opencode-ai/opencode)
# that the user has already configured with a model + API key of their choice.
#
# Install:
#   /install-pre-commit-review-hook --platform=opencode   (run from inside the target repo)
#
# Per-commit bypass:
#   NEXUS_DIFF_REVIEW_DISABLE=1 git commit -m "..."
#   git commit -n -m "..."   (--no-verify; skips ALL pre-commit hooks)
#
# Diff-size cap (default 50 KB, raise to allow larger commits):
#   NEXUS_DIFF_REVIEW_MAX_BYTES=204800 git commit -m "..."
#
# Disable globally for a repo:
#   rm .git/hooks/pre-commit

set -euo pipefail

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
readonly _NEXUS_TAG="[Nexus-Hub: opencode-diff-review]"
# Print the tag and the message to stderr; every further argument is a
# continuation line printed as is.
_nexus_msg() {
    local line
    printf '%s %s\n' "$_NEXUS_TAG" "$1" >&2
    shift
    for line in "$@"; do printf '%s\n' "$line" >&2; done
}

# --- Bypass paths --------------------------------------------------------
if [ "${NEXUS_DIFF_REVIEW_DISABLE:-0}" = "1" ]; then
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

# --- Locate opencode CLI -------------------------------------------------
if ! command -v opencode >/dev/null 2>&1; then
    _nexus_msg "WARNING: opencode CLI not found on PATH; skipping review."
    _nexus_msg "Install OpenCode (https://github.com/opencode-ai/opencode) or set NEXUS_DIFF_REVIEW_DISABLE=1 to silence this warning."
    exit 0
fi

# --- Get staged diff -----------------------------------------------------
DIFF=$(git diff --cached --no-color 2>/dev/null || echo "")
if [ -z "$DIFF" ]; then
    exit 0
fi

# --- Cap diff size -------------------------------------------------------
MAX_BYTES="${NEXUS_DIFF_REVIEW_MAX_BYTES:-51200}"
DIFF_BYTES=${#DIFF}
if [ "$DIFF_BYTES" -gt "$MAX_BYTES" ]; then
    _nexus_msg "WARNING: staged diff is ${DIFF_BYTES} bytes (cap=${MAX_BYTES}); skipping review."
    _nexus_msg "Raise the cap with NEXUS_DIFF_REVIEW_MAX_BYTES=N or commit fewer files at a time."
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

# --- Run opencode (fail-open on any error) -------------------------------
# Combine prompt + diff into a single argument since OpenCode's `run` subcommand
# does not consistently accept piped stdin across versions / model providers.
COMBINED=$(printf '%s\n%s' "$PROMPT" "$DIFF")
RESPONSE=$(opencode run "$COMBINED" 2>/dev/null || true)
if [ -z "$RESPONSE" ]; then
    _nexus_msg "WARNING: opencode CLI returned no output; allowing commit."
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
        _nexus_msg "WARN:"
        echo "$RESPONSE" | tail -n +2 >&2  # nexus: hook-msg-exempt relayed reviewer output
        echo "" >&2  # nexus: hook-msg-exempt blank separator
        _nexus_msg "Commit allowed; review the warnings above and consider amending."
        exit 0
        ;;
    BLOCK)
        _nexus_msg "BLOCK:"
        echo "$RESPONSE" | tail -n +2 >&2  # nexus: hook-msg-exempt relayed reviewer output
        echo "" >&2  # nexus: hook-msg-exempt blank separator
        _nexus_msg "Commit refused. Fix the issue, or bypass this commit with: NEXUS_DIFF_REVIEW_DISABLE=1 git commit ..."
        exit 1
        ;;
    *)
        _nexus_msg "WARNING: unparseable verdict from opencode (expected PASS|WARN|BLOCK); allowing commit."
        exit 0
        ;;
esac
