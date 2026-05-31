#!/usr/bin/env bash
#
# discover-sessions.sh - Locate local AI session-log JSONL files (zero-outbound).
#
# Prints one "tool<TAB>path" line per discovered *.jsonl transcript across the
# known local session-log roots for Claude Code, Codex, and Cursor. The output
# is designed to be piped into extract-session.py / extract-session.ps1.
#
# This script only reads the local filesystem: no network call is made.
#
# Usage:
#   discover-sessions.sh                       # scan all known default roots
#   discover-sessions.sh --tool claude         # only the claude root
#   discover-sessions.sh --root /path/to/dir   # scan a custom root (tool=custom)
#   discover-sessions.sh --help
#
set -euo pipefail

log_error() { printf '[ERROR] %s\n' "$*" >&2; }

print_help() {
    cat <<'EOF'
discover-sessions.sh - locate local AI session-log JSONL files.

Options:
  --tool <name>    Restrict to one known tool root: claude | codex | cursor.
  --root <dir>     Scan a custom directory (labelled "custom"); repeatable.
  -h, --help       Show this help and exit.

Output: one "tool<TAB>absolute-path" line per discovered *.jsonl file.
All discovery is local; this script makes no network calls.
EOF
}

# Known default roots, keyed by tool. Values are colon-free absolute paths.
home="${HOME:-$USERPROFILE}"
declare -a custom_roots=()
tool_filter=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tool)
            tool_filter="${2:-}"
            shift 2
            ;;
        --root)
            custom_roots+=("${2:?--root requires a directory}")
            shift 2
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            print_help >&2
            exit 2
            ;;
    esac
done

emit_root() {
    # emit_root <tool> <dir>
    local tool="$1" dir="$2"
    [[ -d "$dir" ]] || return 0
    # -print is POSIX-portable (avoid GNU-only -printf); prefix the tool tag here.
    find "$dir" -type f -name '*.jsonl' -print 2>/dev/null | while IFS= read -r f; do
        printf '%s\t%s\n' "$tool" "$f"
    done
}

if [[ ${#custom_roots[@]} -gt 0 ]]; then
    for d in "${custom_roots[@]}"; do
        emit_root "custom" "$d"
    done
    exit 0
fi

# Default known roots per tool.
claude_root="$home/.claude/projects"
codex_root="$home/.codex"
cursor_root="$home/.cursor"

if [[ -z "$tool_filter" || "$tool_filter" == "claude" ]]; then
    emit_root "claude" "$claude_root"
fi
if [[ -z "$tool_filter" || "$tool_filter" == "codex" ]]; then
    emit_root "codex" "$codex_root"
fi
if [[ -z "$tool_filter" || "$tool_filter" == "cursor" ]]; then
    emit_root "cursor" "$cursor_root"
fi
