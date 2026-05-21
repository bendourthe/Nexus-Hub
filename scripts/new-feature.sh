#!/usr/bin/env bash
# new-feature.sh -- Resolve the next feature-directory prefix and create the
# directory under specs/. Used by /generate-plan --specs-layout (and other
# spec-driven commands) to pick a sequential or timestamp prefix without
# coupling the agent flow to git branch state.
#
# Usage:
#   scripts/new-feature.sh <slug>
#   scripts/new-feature.sh --style sequential <slug>
#   scripts/new-feature.sh --style timestamp <slug>
#   scripts/new-feature.sh --repo-root /path/to/repo <slug>
#
# Behavior:
# - Reads .specify/init-options.json at the repo root for the key
#   "branch_numbering" (values: sequential | timestamp). Falls back to
#   sequential when the file is missing or unreadable.
# - Sequential mode scans specs/*/ for directories matching ^[0-9]{3}- and
#   picks the next available three-digit number (start at 001 on empty).
# - Timestamp mode uses UTC time formatted as YYYYMMDD-HHMMSS.
# - mkdir -p the resolved directory under specs/<prefix>-<slug>/.
# - Writes .specify/feature.json with {"feature_directory": "..."}.
# - Prints the resolved relative directory path on stdout. Exits non-zero
#   on collision unless --force is passed.
#
# Cross-platform parity: scripts/new-feature.ps1 implements the same
# behavior on Windows. Keep the two in lockstep per AGENTS.md.

set -euo pipefail

PROGNAME="new-feature.sh"

log_info()  { echo "[INFO]  $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

die() {
    log_error "$1"
    exit "${2:-1}"
}

usage() {
    cat >&2 <<EOF
Usage: $PROGNAME [--style sequential|timestamp] [--repo-root PATH] [--force] <slug>

Resolves the next specs/<prefix>-<slug>/ directory and creates it.
Prints the relative path on stdout.
EOF
}

# --- Argument parsing -----------------------------------------------------

style=""
repo_root=""
force="false"
slug=""

while [ $# -gt 0 ]; do
    case "$1" in
        --style)
            [ $# -ge 2 ] || die "--style requires a value"
            style="$2"
            shift 2
            ;;
        --repo-root)
            [ $# -ge 2 ] || die "--repo-root requires a value"
            repo_root="$2"
            shift 2
            ;;
        --force)
            force="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --*)
            die "Unknown flag: $1"
            ;;
        *)
            if [ -z "$slug" ]; then
                slug="$1"
            else
                die "Unexpected argument: $1"
            fi
            shift
            ;;
    esac
done

[ -n "$slug" ] || { usage; exit 2; }

# Sanitize the slug to [a-z0-9-]+ defensively (the caller should have done
# this; we re-enforce as a guardrail).
sanitized_slug="$(printf '%s' "$slug" | tr '[:upper:]' '[:lower:]' | tr ' _' '-' | tr -cd 'a-z0-9-')"
[ -n "$sanitized_slug" ] || die "Slug sanitized to empty string -- refusing"
[ "$sanitized_slug" = "index" ] && die "Reserved slug: index"
[ "$sanitized_slug" = "readme" ] && die "Reserved slug: readme"
[ "$sanitized_slug" = "template" ] && die "Reserved slug: template"

# --- Resolve repo root ----------------------------------------------------

if [ -z "$repo_root" ]; then
    if command -v git >/dev/null 2>&1; then
        repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    fi
    if [ -z "$repo_root" ]; then
        repo_root="$(pwd)"
    fi
fi

[ -d "$repo_root" ] || die "Repo root does not exist: $repo_root"

# --- Resolve numbering style ---------------------------------------------

init_options="$repo_root/.specify/init-options.json"
if [ -z "$style" ] && [ -f "$init_options" ]; then
    style="$(awk '
        /"branch_numbering"/ {
            sub(/.*"branch_numbering"[[:space:]]*:[[:space:]]*"/, "", $0)
            sub(/".*/, "", $0)
            print
            exit
        }
    ' "$init_options" 2>/dev/null || true)"
fi

if [ -z "$style" ]; then
    style="sequential"
fi

case "$style" in
    sequential|timestamp) ;;
    *) die "Invalid numbering style: $style (must be sequential or timestamp)" ;;
esac

# --- Resolve prefix -------------------------------------------------------

specs_dir="$repo_root/specs"
mkdir -p "$specs_dir"

prefix=""
if [ "$style" = "sequential" ]; then
    next=1
    if [ -d "$specs_dir" ]; then
        for entry in "$specs_dir"/*/; do
            [ -d "$entry" ] || continue
            base="$(basename "$entry")"
            case "$base" in
                [0-9][0-9][0-9]-*)
                    num="${base%%-*}"
                    # Strip leading zeros for arithmetic.
                    num_int=$((10#$num))
                    if [ "$num_int" -ge "$next" ]; then
                        next=$((num_int + 1))
                    fi
                    ;;
            esac
        done
    fi
    prefix="$(printf '%03d' "$next")"
else
    prefix="$(date -u '+%Y%m%d-%H%M%S')"
fi

# --- Construct and create directory --------------------------------------

dir_name="${prefix}-${sanitized_slug}"
target="$specs_dir/$dir_name"

if [ -d "$target" ]; then
    if [ "$force" != "true" ]; then
        die "Directory already exists: $target (pass --force to reuse)" 3
    fi
fi

mkdir -p "$target"

# --- Persist feature.json -------------------------------------------------

specify_dir="$repo_root/.specify"
mkdir -p "$specify_dir"
feature_json="$specify_dir/feature.json"
rel_path="specs/$dir_name"

# Write JSON atomically.
tmp_json="$(mktemp "$feature_json.XXXXXX")"
printf '{\n  "feature_directory": "%s"\n}\n' "$rel_path" > "$tmp_json"
mv -f "$tmp_json" "$feature_json"

# --- Output --------------------------------------------------------------

printf '%s\n' "$rel_path"
log_info "Created $rel_path (style=$style, prefix=$prefix)"
log_info "Persisted $feature_json"
