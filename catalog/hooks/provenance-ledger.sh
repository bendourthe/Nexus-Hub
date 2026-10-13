#!/usr/bin/env bash
# Provenance Ledger - PostToolUse hook for Claude Code (Write, Edit, Bash).
# Maintains a best-effort file-provenance / trust-seam ledger: it records which
# paths the agent wrote, then flags a later command that references one of them.
# Part of Nexus-Hub (v3.15.6 / AC3).
#
# Why this exists:
#   The config-write-then-executed escape pattern decouples the write from the
#   execution: the agent writes a file, and some component runs it later, at a
#   time nothing is watching. Nothing in this catalog previously correlated the
#   two, so a write and its later execution looked like unrelated events. This
#   hook instruments that handoff, which the agentic-endpoint-hardening skill
#   calls the trust seam.
#
# What it records (and what it never records):
#   Only a timestamp, a content hash, and a path -- one tab-separated line per
#   agent write. It NEVER records file contents, diffs, environment values, or
#   secret material, per the egress-redaction discipline. The hash exists so a
#   later reader can tell whether the file still holds what the agent wrote,
#   without the ledger holding the bytes.
#
# HONEST BOUNDARY (read this before trusting it):
#   A hook observes the tool calls of the harness it is installed in. It CANNOT
#   instrument an editor extension, a language server, a version-control
#   integration, or any other trusted executor running in a different process, so
#   it cannot see the execution half of most real escapes. Correlating an agent
#   write with a later command IN THE SAME SESSION is achievable and is what
#   ships here; full cross-executor instrumentation is not locally achievable and
#   is explicitly out of scope. This is the reverse-engineered `re-partial`
#   capability: useful as a local audit trail and a same-session tripwire, not an
#   endpoint detection agent.
#
# Registration:
#   Registered in the default catalog/hooks/settings.json under PostToolUse with
#   a `Write|Edit|Bash` matcher. Advisory only: it always exits 0 and never
#   blocks. Disable per-session with
#   `export NEXUS_DISABLED_HOOKS=provenance-ledger`, or skip all advisory hooks
#   with `export NEXUS_HOOK_PROFILE=minimal`.
#
# Configuration:
#   NEXUS_PROVENANCE_DIR    ledger directory (default ~/.nexus-hub/cache/provenance)
#   NEXUS_PROVENANCE_MAX    max ledger lines retained per session (default 500)
#   NEXUS_PROVENANCE_MAX_BYTES  max ledger bytes (default 1048576; minimum 8192)
#   NEXUS_PROVENANCE_HASH_MAX_BYTES  skip hashing above this size (default 10485760)

set -euo pipefail

# Never fail loudly on internal errors - this hook is advisory only.
trap 'exit 0' ERR

# --- Runtime controls ---
_HOOK_NAME="provenance-ledger"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

LEDGER_DIR="${NEXUS_PROVENANCE_DIR:-$HOME/.nexus-hub/cache/provenance}"
MAX_LINES="${NEXUS_PROVENANCE_MAX:-500}"
MAX_BYTES="${NEXUS_PROVENANCE_MAX_BYTES:-1048576}"
if ! [[ "$MAX_BYTES" =~ ^[0-9]+$ ]] || ! [ "$MAX_BYTES" -gt 0 ] 2>/dev/null; then
    MAX_BYTES=1048576
fi
# A supported 4096-byte path, hash and timestamp must fit as one intact row.
if [ "$MAX_BYTES" -lt 8192 ]; then
    MAX_BYTES=8192
    printf '[provenance-ledger] byte cap raised to minimum 8192 for complete records.\n' >&2
fi
HASH_MAX_BYTES="${NEXUS_PROVENANCE_HASH_MAX_BYTES:-10485760}"

# --- Read the PostToolUse payload ---
# Bash command substitution drops raw NUL bytes. Detect them before decoding.
INPUT=""
if IFS= read -r -d '' INPUT; then
    printf '[provenance-ledger] cannot decode payload containing NUL; skipping.\n' >&2
    exit 0
fi
[ -n "${INPUT:-}" ] || exit 0

# --- Field extraction (jq when available, text fallback otherwise) ---
PY=""
if command -v python3 >/dev/null 2>&1; then PY="python3"
elif command -v python >/dev/null 2>&1; then PY="python"; fi
# The fallback mirrors escalation-trigger.sh: it reads the RAW JSON string, so it
# decodes the backslash escape before use or a Windows path would arrive doubled.
_json_str() {
    local key="$1"
    if command -v jq >/dev/null 2>&1; then
        # ASCII escapes avoid native Windows stdout changing LF bytes to CRLF.
        local value
        value=$(printf '%s' "$INPUT" | jq -j "($2 // empty) | @uri" 2>/dev/null || true)
        # Bash cannot store NUL bytes; refuse before decoding instead of aliasing a path.
        if [ "$key" = "file_path" ] && [[ "$value" == *%00* ]]; then
            printf '[provenance-ledger] cannot record path containing NUL; skipping.\n' >&2
            return
        fi
        printf '%b' "${value//%/\\x}"
    elif [ -n "$PY" ]; then
        printf '%s' "$INPUT" | PYTHONIOENCODING=utf-8 "$PY" -c '
import json, sys
try:
    data = json.load(sys.stdin)
    key = sys.argv[1]
    source = data.get("tool_input") or {} if key in ("file_path", "command") else data
    value = source.get(key) or (source.get("path") if key == "file_path" else "")
    if isinstance(value, str):
        if key == "file_path" and "\x00" in value:
            sys.stderr.write("[provenance-ledger] cannot record path containing NUL; skipping.\n")
        else:
            sys.stdout.buffer.write(value.encode("utf-8"))
except (ValueError, TypeError, AttributeError):
    pass
' "$key" || true
    else
        local v
        v=$(printf '%s' "$INPUT" \
            | grep -oE "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" \
            | head -1 \
            | sed -E "s/.*\"$key\"[[:space:]]*:[[:space:]]*\"//; s/\"$//" || true)
        # Only doubled backslashes are provably decodable without a JSON helper.
        case "${v//\\\\/}" in
            *\\*) printf '[provenance-ledger] cannot decode escaped field without a JSON helper; skipping.\n' >&2; return 1 ;;
        esac
        printf '%s' "${v//\\\\/\\}"
    fi
}

TOOL_NAME=$(_json_str "tool_name" '.tool_name')
SESSION_ID=$(_json_str "session_id" '.session_id')
# A sentinel keeps Bash command substitution from stripping trailing LF bytes.
FILE_PATH=$(_json_str "file_path" '.tool_input.file_path // .tool_input.path'; printf '.')
FILE_PATH="${FILE_PATH%.}"
COMMAND=$(_json_str "command" '.tool_input.command')

[ "${TOOL_NAME:-}" = "null" ] && TOOL_NAME=""
[ "${SESSION_ID:-}" = "null" ] && SESSION_ID=""

# Decide which branch to run. Prefer the explicit tool name over guessing from
# which field is present: a payload carrying BOTH a path and a command would
# otherwise be ambiguous. Fall back to field presence so a harness that omits
# tool_name still works.
IS_WRITE=0
IS_COMMAND=0
case "${TOOL_NAME:-}" in
    Write|Edit|MultiEdit|NotebookEdit) IS_WRITE=1 ;;
    Bash)                              IS_COMMAND=1 ;;
    *)
        [ -n "${FILE_PATH:-}" ] && [ "${FILE_PATH}" != "null" ] && IS_WRITE=1
        [ -n "${COMMAND:-}" ] && [ "${COMMAND}" != "null" ] && IS_COMMAND=1
        ;;
esac

# Session scoping: the ledger is per-session by design, so correlation cannot
# reach across unrelated sessions. Without a session id, fall back to a stable
# per-day file rather than a global one.
if [ -z "${SESSION_ID:-}" ]; then
    SESSION_ID="nosession-$(date +%Y%m%d)"
fi
# Keep the id filesystem-safe.
SESSION_ID=$(printf '%s' "$SESSION_ID" | tr -c 'A-Za-z0-9._-' '_')
LEDGER="$LEDGER_DIR/$SESSION_ID.tsv"

# --- Hash helper (path + hash only; never contents) ---
_hash_file() {
    local f="$1"
    [ -f "$f" ] || { printf 'NOFILE'; return; }

    local size=0
    size=$(wc -c < "$f" 2>/dev/null | tr -d ' ' || echo 0)
    if [ "${size:-0}" -gt "$HASH_MAX_BYTES" ] 2>/dev/null; then
        printf 'SKIPPED-LARGE'
        return
    fi

    # Hash via STDIN, not by passing the filename. GNU coreutils escapes a
    # filename containing a backslash or newline and prefixes the whole output
    # line with `\`, so `sha256sum "C:\repo\x.sh" | cut -d' ' -f1` yields a
    # 65-character value with a leading backslash on Windows paths. Reading from
    # stdin removes the filename from the output entirely and sidesteps the class.
    local out=""
    if command -v sha256sum >/dev/null 2>&1; then
        out=$(sha256sum < "$f" 2>/dev/null | cut -d' ' -f1 || true)
    elif command -v shasum >/dev/null 2>&1; then
        out=$(shasum -a 256 < "$f" 2>/dev/null | cut -d' ' -f1 || true)
    elif command -v openssl >/dev/null 2>&1; then
        out=$(openssl dgst -sha256 < "$f" 2>/dev/null | awk '{print $NF}' || true)
    fi
    printf '%s' "${out:-NOHASH}"
}

# --- Branch 1: a write. Append one path+hash line. ---
if [ "$IS_WRITE" = "1" ] && [ -n "${FILE_PATH:-}" ] && [ "${FILE_PATH}" != "null" ]; then
    mkdir -p "$LEDGER_DIR" 2>/dev/null || exit 0
    NORM_PATH="${FILE_PATH//\\//}"
    HASH=$(_hash_file "$FILE_PATH")
    # TSV supports whole paths up to 4096 UTF-8 bytes, with no row delimiters.
    # Larger filesystem paths retain their complete normalized-path identity as
    # a digest marker, explicitly outside the command-correlation heuristic.
    PATH_BYTES=$(printf '%s' "$NORM_PATH" | wc -c | tr -d ' ')
    if [ "$PATH_BYTES" -gt 4096 ] || [[ "$NORM_PATH" == *$'\t'* || "$NORM_PATH" == *$'\n'* || "$NORM_PATH" == *$'\r'* ]]; then
        PATH_HASH=""
        if command -v sha256sum >/dev/null 2>&1; then
            PATH_HASH=$(printf '%s' "$NORM_PATH" | sha256sum | cut -d' ' -f1)
        elif command -v shasum >/dev/null 2>&1; then
            PATH_HASH=$(printf '%s' "$NORM_PATH" | shasum -a 256 | cut -d' ' -f1)
        elif command -v openssl >/dev/null 2>&1; then
            PATH_HASH=$(printf '%s' "$NORM_PATH" | openssl dgst -sha256 | awk '{print $NF}')
        fi
        if ! [[ "$PATH_HASH" =~ ^[0-9a-fA-F]{64}$ ]]; then
            printf '[provenance-ledger] unsupported TSV path and no complete SHA-256 digest; skipping.\n' >&2
            exit 0
        fi
        NORM_PATH="UNSUPPORTED-PATH-SHA256:$PATH_HASH"
        printf '[provenance-ledger] recorded path digest without path correlation.\n' >&2
    fi
    printf '%s\t%s\t%s\n' "$(date +%s)" "$HASH" "$NORM_PATH" >> "$LEDGER" 2>/dev/null || exit 0

    # Retain complete newest rows under both line and UTF-8 byte caps.
    line_count=$(wc -l < "$LEDGER" 2>/dev/null | tr -d ' ' || echo 0)
    byte_count=$(wc -c < "$LEDGER" 2>/dev/null | tr -d ' ' || echo 0)
    if [ "${line_count:-0}" -gt "$MAX_LINES" ] 2>/dev/null || [ "${byte_count:-0}" -gt "$MAX_BYTES" ]; then
        TMPFILE="$LEDGER.tmp.$$"
        # The C locale counts bytes without changing the UTF-8 record contents.
        if LC_ALL=C awk -v max_lines="$MAX_LINES" -v max_bytes="$MAX_BYTES" '
            BEGIN { first = 1; bytes = 0 }
            {
                rows[NR] = $0 "\n"
                bytes += length(rows[NR])
                while (NR - first + 1 > max_lines || bytes > max_bytes) {
                    bytes -= length(rows[first])
                    delete rows[first++]
                }
            }
            END { for (i = first; i <= NR; i++) printf "%s", rows[i] }
        ' "$LEDGER" > "$TMPFILE" 2>/dev/null && mv "$TMPFILE" "$LEDGER" 2>/dev/null; then
            :
        else
            rm -f "$TMPFILE" 2>/dev/null || true
            printf '[provenance-ledger] degraded rotation; ledger retained above its cap.\n' >&2
        fi
    fi
    exit 0
fi

# --- Branch 2: a command. Flag it if it references a recently written path. ---
# Heuristic, stated plainly: this matches the path or its basename anywhere in
# the command string. It therefore over-reports (a path merely mentioned as an
# argument reads the same as one being executed) and under-reports (a path
# reached through a variable, an alias, or a wrapper is invisible). It is a
# tripwire that says "look at this", not a determination that execution occurred.
if [ "$IS_COMMAND" = "1" ] && [ -n "${COMMAND:-}" ] && [ "${COMMAND}" != "null" ] && [ -f "$LEDGER" ]; then
    HITS=""
    NOW=$(date +%s)
    while IFS=$'\t' read -r ts hash path; do
        [ -n "${path:-}" ] || continue
        case "$path" in UNSUPPORTED-PATH-SHA256:*) continue ;; esac
        base="${path##*/}"
        # Ignore very short basenames: they collide with ordinary words.
        if [ "${#base}" -lt 4 ]; then continue; fi
        case "$COMMAND" in
            *"$path"*|*"$base"*)
                # Report the age: "written 2s ago" reads very differently from
                # "written 40 minutes ago" when judging whether this is the agent
                # closing a loop it just opened.
                age="unknown"
                case "$ts" in
                    ''|*[!0-9]*) : ;;
                    *) age="$(( NOW - ts ))s" ;;
                esac
                HITS="${HITS}
  - ${path} (agent-written ${age} ago, hash ${hash:0:12})"
                ;;
        esac
    done < "$LEDGER"

    if [ -n "$HITS" ]; then
        {
            echo "[provenance-ledger] TRUST SEAM: this command references a path the agent wrote in this session:${HITS}"
            echo "  A write the agent made is now reaching an executor. Confirm the command is running what you intend."
            echo "  Advisory only. See the Limits section of the agentic-endpoint-hardening skill: a local hook cannot observe executors in other processes."
        } >&2
    fi
fi

exit 0
