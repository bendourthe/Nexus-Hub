#!/usr/bin/env bash
#
# ioc-log-scan.sh - local, read-only IOC sweep over a log file (defensive).
#
# Matches every indicator in an IOC list file (one indicator per line; blank
# lines and lines beginning with '#' are ignored) against a target log file
# using fixed-string matching, and reports the per-indicator match count plus
# the matching lines. Purely local: makes NO network calls and writes nothing
# outside stdout/stderr.
#
# Usage:
#   ioc-log-scan.sh <log_file> <ioc_list_file> [--max-lines N]
#
# --max-lines N caps how many matching lines are printed per indicator
# (default 5; use 0 for unlimited). Exit code is 0 when the scan ran, 2 on a
# usage/IO error. A successful scan that finds matches still exits 0 - this is
# a hunt aid, not a gate.

set -euo pipefail

log_info()  { printf '[INFO]  %s\n' "$*" >&2; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }

usage() {
    cat >&2 <<'EOF'
Usage: ioc-log-scan.sh <log_file> <ioc_list_file> [--max-lines N]

Sweeps a log file for each indicator in an IOC list (fixed-string match).
Local and read-only; makes no network calls.
EOF
    exit 2
}

max_lines=5
log_file=""
ioc_file=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --max-lines)
            [ "$#" -ge 2 ] || { log_error "--max-lines requires a value"; usage; }
            max_lines="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            if [ -z "$log_file" ]; then
                log_file="$1"
            elif [ -z "$ioc_file" ]; then
                ioc_file="$1"
            else
                log_error "unexpected argument: $1"
                usage
            fi
            shift
            ;;
    esac
done

[ -n "$log_file" ] && [ -n "$ioc_file" ] || usage

if [ ! -f "$log_file" ]; then
    log_error "log file not found: $log_file"
    exit 2
fi
if [ ! -f "$ioc_file" ]; then
    log_error "IOC list not found: $ioc_file"
    exit 2
fi

case "$max_lines" in
    ''|*[!0-9]*) log_error "--max-lines must be a non-negative integer"; exit 2 ;;
esac

log_info "Log file:  $log_file"
log_info "IOC list:  $ioc_file"

total_hits=0
indicators=0

# Read the IOC list line by line; ignore blanks and comments.
while IFS= read -r raw_ioc || [ -n "$raw_ioc" ]; do
    # Trim leading/trailing whitespace.
    ioc="$(printf '%s' "$raw_ioc" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    [ -z "$ioc" ] && continue
    case "$ioc" in \#*) continue ;; esac

    indicators=$((indicators + 1))
    # -F fixed string, -c count. grep exits 1 on no match; tolerate under set -e.
    count="$(grep -F -c -- "$ioc" "$log_file" || true)"
    count="${count:-0}"

    if [ "$count" -gt 0 ]; then
        total_hits=$((total_hits + count))
        printf '\n=== IOC: %s  (matches: %s) ===\n' "$ioc" "$count"
        if [ "$max_lines" -eq 0 ]; then
            grep -F -n -- "$ioc" "$log_file" || true
        else
            grep -F -n -- "$ioc" "$log_file" | head -n "$max_lines" || true
        fi
    fi
done < "$ioc_file"

printf '\n[SUMMARY] %s indicator(s) scanned, %s total matching line(s).\n' "$indicators" "$total_hits"
exit 0
