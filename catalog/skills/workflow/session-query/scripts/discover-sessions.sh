#!/usr/bin/env bash
#
# discover-sessions.sh - Locate local prior-context source files (zero-outbound).
#
# Prints one "tool<TAB>path" line per discovered source file across the known
# local roots. The output is designed to be piped into extract-session.py /
# extract-session.ps1, which uses the "tool" tag to select the right parser.
#
# Sources:
#   - JSONL session logs: Claude Code, Codex, Cursor (scanned by default)
#   - Obsidian vault notes (.md), selected with --tool obsidian
#   - Exported ChatGPT history (conversations.json), selected with --tool chatgpt
#   - Exported Gemini history ("My Activity" JSON), selected with --tool gemini
#
# The default (no --tool) scan covers ONLY the three JSONL tools, so existing
# behavior is unchanged. The Obsidian / ChatGPT / Gemini sources are opt-in via
# --tool (with a sensible default root) or --root, and emit nothing when absent.
#
# This script only reads the local filesystem: no network call is made.
#
# Usage:
#   discover-sessions.sh                          # claude + codex + cursor JSONL
#   discover-sessions.sh --tool claude            # only the claude root
#   discover-sessions.sh --tool obsidian          # Obsidian vaults under ~/Documents
#   discover-sessions.sh --tool chatgpt           # ChatGPT exports under ~/Downloads
#   discover-sessions.sh --tool gemini            # Gemini exports under ~/Downloads
#   discover-sessions.sh --root /path/to/dir      # custom JSONL root (tool=custom)
#   discover-sessions.sh --root ./vault --tool obsidian
#   discover-sessions.sh --help
#
set -euo pipefail

log_error() { printf '[ERROR] %s\n' "$*" >&2; }

print_help() {
    cat <<'EOF'
discover-sessions.sh - locate local prior-context source files.

Options:
  --tool <name>    Restrict to one source: claude | codex | cursor (JSONL),
                   or obsidian | chatgpt | gemini (the non-JSONL sources).
  --root <dir>     Scan a custom directory; repeatable. Tagged by --tool when
                   that tool is obsidian/chatgpt/gemini, else "custom" (JSONL).
  -h, --help       Show this help and exit.

Output: one "tool<TAB>absolute-path" line per discovered source file.
All discovery is local; this script makes no network calls.
EOF
}

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

# Emit *.jsonl transcripts under a directory, tagged with the given tool.
emit_jsonl() {
    local tool="$1" dir="$2"
    [[ -d "$dir" ]] || return 0
    # -print is POSIX-portable (avoid GNU-only -printf); prefix the tool tag here.
    find "$dir" -type f -name '*.jsonl' -print 2>/dev/null | while IFS= read -r f; do
        printf '%s\t%s\n' "$tool" "$f"
    done
}

# Emit Obsidian notes: locate vault roots by the .obsidian marker (bounded
# depth) and print their *.md notes; fall back to a plain *.md folder.
emit_obsidian() {
    local dir="$1"
    [[ -d "$dir" ]] || return 0
    local found_marker=0 odir vault
    while IFS= read -r odir; do
        [[ -n "$odir" ]] || continue
        found_marker=1
        vault="$(dirname "$odir")"
        find "$vault" -type f -name '*.md' -not -path '*/.obsidian/*' -print 2>/dev/null | while IFS= read -r f; do
            printf 'obsidian\t%s\n' "$f"
        done
    done < <(find "$dir" -maxdepth 6 -type d -name '.obsidian' 2>/dev/null)
    if [[ "$found_marker" -eq 0 ]]; then
        find "$dir" -type f -name '*.md' -print 2>/dev/null | while IFS= read -r f; do
            printf 'obsidian\t%s\n' "$f"
        done
    fi
}

# Emit exported ChatGPT/Gemini history files. In "default" mode (a broad
# download root) match only the canonical export name to avoid noise; in
# "explicit" mode (a user-supplied --root) emit all .json / .md export files.
emit_export() {
    local tool="$1" dir="$2" mode="$3"
    [[ -d "$dir" ]] || return 0
    if [[ "$mode" == "default" ]]; then
        local namepat
        if [[ "$tool" == "chatgpt" ]]; then namepat='conversations.json'; else namepat='*ctivity*.json'; fi
        find "$dir" -maxdepth 4 -type f -iname "$namepat" -print 2>/dev/null | while IFS= read -r f; do
            printf '%s\t%s\n' "$tool" "$f"
        done
    else
        find "$dir" -type f \( -name '*.json' -o -name '*.md' \) -print 2>/dev/null | while IFS= read -r f; do
            printf '%s\t%s\n' "$tool" "$f"
        done
    fi
}

# Default known roots per source.
claude_root="$home/.claude/projects"
codex_root="$home/.codex"
cursor_root="$home/.cursor"
obsidian_root="$home/Documents"
chatgpt_root="$home/Downloads"
gemini_root="$home/Downloads"

# Custom --root: tag by the new sources when requested, else "custom" JSONL
# (the unchanged legacy behavior).
if [[ ${#custom_roots[@]} -gt 0 ]]; then
    for d in "${custom_roots[@]}"; do
        case "$tool_filter" in
            obsidian) emit_obsidian "$d" ;;
            chatgpt)  emit_export chatgpt "$d" explicit ;;
            gemini)   emit_export gemini "$d" explicit ;;
            *)        emit_jsonl "custom" "$d" ;;
        esac
    done
    exit 0
fi

# No custom root: scan default roots. The empty (no --tool) case covers ONLY
# the three JSONL tools, exactly as before.
case "$tool_filter" in
    obsidian) emit_obsidian "$obsidian_root" ;;
    chatgpt)  emit_export chatgpt "$chatgpt_root" default ;;
    gemini)   emit_export gemini "$gemini_root" default ;;
    "")
        emit_jsonl "claude" "$claude_root"
        emit_jsonl "codex" "$codex_root"
        emit_jsonl "cursor" "$cursor_root"
        ;;
    claude) emit_jsonl "claude" "$claude_root" ;;
    codex)  emit_jsonl "codex" "$codex_root" ;;
    cursor) emit_jsonl "cursor" "$cursor_root" ;;
    *)
        log_error "Unknown --tool: $tool_filter"
        exit 2
        ;;
esac
