#!/usr/bin/env bash
#
# volatility-runner.sh - deterministic Volatility 3 triage wrapper (defensive).
#
# Runs a fixed, read-only triage plugin set against a memory image using a
# locally-installed Volatility 3 (`vol`) and writes each plugin's output to a
# per-case directory for review. The script itself makes ZERO network calls;
# it relies on the symbol tables bundled with the locally-installed Volatility
# 3 (no symbol packs are fetched). It never executes carved samples.
#
# Usage:
#   volatility-runner.sh <image_path> [output_dir] [--os windows|linux|mac]
#
# Defaults: output_dir = ./vol-triage-<image-basename>, os = windows.

set -euo pipefail

log_info()  { printf '[INFO]  %s\n' "$*" >&2; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }

usage() {
    cat >&2 <<'EOF'
Usage: volatility-runner.sh <image_path> [output_dir] [--os windows|linux|mac]

Runs a fixed read-only Volatility 3 triage plugin set against a memory image.
Requires Volatility 3 (`vol`) installed locally. Makes no network calls.
EOF
    exit 2
}

# --- Argument parsing -------------------------------------------------------

os_family="windows"
image_path=""
output_dir=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --os)
            [ "$#" -ge 2 ] || { log_error "--os requires a value"; usage; }
            os_family="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            if [ -z "$image_path" ]; then
                image_path="$1"
            elif [ -z "$output_dir" ]; then
                output_dir="$1"
            else
                log_error "unexpected argument: $1"
                usage
            fi
            shift
            ;;
    esac
done

[ -n "$image_path" ] || usage

# --- Preconditions ----------------------------------------------------------

if ! command -v vol >/dev/null 2>&1; then
    log_error "Volatility 3 ('vol') not found on PATH. Install it first; this wrapper fetches nothing."
    exit 1
fi

if [ ! -f "$image_path" ]; then
    log_error "image not found: $image_path"
    exit 1
fi

case "$os_family" in
    windows|linux|mac) ;;
    *) log_error "unknown --os value: $os_family (expected windows|linux|mac)"; exit 2 ;;
esac

if [ -z "$output_dir" ]; then
    output_dir="./vol-triage-$(basename -- "$image_path")"
fi
mkdir -p -- "$output_dir"

# --- Fixed triage plugin set (per OS family) --------------------------------
# Mirrors the SKILL.md "Triage Plugin Map": process list, hidden-process
# scan, module list, injection scan, network connections, handles, cmdline.

case "$os_family" in
    windows)
        plugins="windows.pstree windows.psscan windows.dlllist windows.malfind windows.netscan windows.handles windows.cmdline"
        ;;
    linux)
        plugins="linux.pstree linux.pslist linux.lsmod linux.malfind linux.sockstat linux.bash"
        ;;
    mac)
        plugins="mac.pstree mac.pslist mac.lsmod mac.malfind mac.netstat"
        ;;
esac

# --- Run ---------------------------------------------------------------------

log_info "Image:      $image_path"
log_info "OS family:  $os_family"
log_info "Output dir: $output_dir"

# Record the image hash so the run is reproducible and the chain of custody
# is documented (matches SKILL.md step 1).
if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -- "$image_path" > "$output_dir/image.sha256" || log_error "hashing failed"
fi

failed=0
for plugin in $plugins; do
    out_file="$output_dir/${plugin}.txt"
    log_info "Running $plugin ..."
    # Guard each plugin: a missing/unsupported plugin must not abort the
    # whole triage run under `set -e`.
    if ! vol -f "$image_path" "$plugin" > "$out_file" 2> "$output_dir/${plugin}.err"; then
        log_error "$plugin failed (see ${plugin}.err)"
        failed=$((failed + 1))
    fi
done

log_info "Triage complete. $failed plugin(s) failed; output under $output_dir"
log_info "Review output statically. Do NOT execute any carved sample."
exit 0
