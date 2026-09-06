#!/usr/bin/env bash
# Code Search Routing - PreToolUse advisory hook
# Nudges broad native search calls toward the local nexus-code-search index.
# Intentionally omits `set -e`: any helper failure must fail open.

_HOOK_NAME="code-search-routing"
_DISABLED="${NEXUS_DISABLED_HOOKS:-}"
if [[ ",$_DISABLED," == *",$_HOOK_NAME,"* ]]; then exit 0; fi
if [[ "${NEXUS_HOOK_PROFILE:-full}" == "minimal" ]]; then exit 0; fi

debug_log() {
  if [[ "${NEXUS_CODE_SEARCH_ROUTING_DEBUG:-0}" == "1" ]]; then
    echo "[code-search-routing debug] $*" >&2
  fi
}

INPUT=$(cat 2>/dev/null || true)
if [[ -z "$INPUT" ]]; then
  debug_log "empty stdin; allowing"
  exit 0
fi

json_field() {
  local field="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$INPUT" | jq -r "$field // empty" 2>/dev/null
    return
  fi

  local python_bin=""
  if command -v python3 >/dev/null 2>&1; then
    python_bin="python3"
  elif command -v python >/dev/null 2>&1; then
    python_bin="python"
  else
    return
  fi

  printf '%s' "$INPUT" | "$python_bin" -c '
import json
import sys

path = sys.argv[1].split(".")
value = json.load(sys.stdin)
for part in path:
    if not isinstance(value, dict):
        value = ""
        break
    value = value.get(part, "")
print(value if isinstance(value, (str, int, float, bool)) else "")
' "${field#.}" 2>/dev/null
}

TOOL_NAME=$(json_field '.tool_name' || true)
COMMAND=$(json_field '.tool_input.command' || true)

if [[ -z "$TOOL_NAME" ]]; then
  debug_log "malformed or incomplete payload; allowing"
  exit 0
fi

# Read is load-bearing for subsequent Edit/Write operations and is never routed.
if [[ "$TOOL_NAME" == "Read" ]]; then
  debug_log "Read is explicitly excluded"
  exit 0
fi

INDEXED_TOOL=""
HINT=""
case "$TOOL_NAME" in
  Grep)
    INDEXED_TOOL="search_code"
    HINT='search_code(root="<repo>", query="<pattern>")'
    ;;
  Glob)
    INDEXED_TOOL="code_search"
    HINT='code_search(root="<repo>", query="<file-or-symbol>")'
    ;;
  Bash)
    LOWER_COMMAND=$(printf '%s' "$COMMAND" | tr '[:upper:]' '[:lower:]' 2>/dev/null || true)
    if [[ "$LOWER_COMMAND" =~ (^|[\|\;\&][[:space:]]*)(grep|rg)([[:space:]]|$) ]]; then
      INDEXED_TOOL="search_code"
      HINT='search_code(root="<repo>", query="<pattern>")'
    elif [[ "$LOWER_COMMAND" =~ (^|[\|\;\&][[:space:]]*)find([[:space:]]|$) ]] \
      && [[ "$LOWER_COMMAND" =~ [[:space:]]-(name|iname|path|regex)[[:space:]] ]] \
      && [[ ! "$LOWER_COMMAND" =~ [[:space:]]-(delete|exec|execdir)([[:space:]]|$) ]]; then
      INDEXED_TOOL="code_search"
      HINT='code_search(root="<repo>", query="<file-or-symbol>")'
    fi
    ;;
  *)
    debug_log "tool $TOOL_NAME is outside the routing surface"
    exit 0
    ;;
esac

if [[ -z "$INDEXED_TOOL" ]]; then
  debug_log "no conservative match for $TOOL_NAME"
  exit 0
fi

MSG="[code-search-routing] Prefer the local nexus-code-search index for this search: ${HINT}. Native search remains available if the index is absent or the query needs raw filesystem semantics."
echo "$MSG" >&2

if [[ "${NEXUS_CODE_SEARCH_ROUTING:-soft}" == "block" ]]; then
  echo "[code-search-routing] Blocked by NEXUS_CODE_SEARCH_ROUTING=block; unset it or use 'soft' to continue." >&2
  exit 2
fi

exit 0
