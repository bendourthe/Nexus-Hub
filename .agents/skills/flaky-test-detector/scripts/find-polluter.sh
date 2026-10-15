#!/usr/bin/env bash
#
# find-polluter.sh - bisect a test suite to find the file that pollutes shared state.
#
# Runs each test file in isolation, cleaning a watched artifact (a file or
# directory a well-behaved run should never leave behind) before each run, and
# reports the first test file whose isolated run re-creates that artifact. Use
# it when a suite is order-dependent because one test leaks filesystem or global
# state into the others.
#
# The script is project-agnostic: you supply the watched artifact, a glob for
# the test files to bisect, and your own test-runner command. It hardcodes no
# language or framework and makes NO network calls. The only thing it writes is
# the removal of the watched artifact between runs (guarded against unsafe
# paths).
#
# Usage:
#   find-polluter.sh --watch <artifact> --tests <glob> -- <test-cmd> [args...]
#
#   --watch <artifact>   Path or glob of the pollution artifact to watch for.
#                        Removed before each isolated run; its reappearance
#                        identifies the polluter.
#   --tests <glob>       Quoted glob selecting the test files to bisect, e.g.
#                        "tests/*.test.js" or "tests/test_*.py". Expanded inside
#                        the script, so quote it to stop the shell expanding it
#                        first.
#   -- <test-cmd> ...    Everything after -- is your test command. Use {} as the
#                        placeholder for the current test file; if {} is absent
#                        the file is appended as the final argument.
#
# Examples:
#   find-polluter.sh --watch "tmp/leaked.lock" --tests "tests/*.test.js" -- node --test {}
#   find-polluter.sh --watch ".cache/state" --tests "tests/test_*.py" -- pytest -p no:randomly {}
#
# Exit code: 0 when the scan ran (whether or not a polluter was found - this is
# a diagnostic aid, not a gate); 2 on a usage or IO error.

set -euo pipefail

log_info()  { printf '[INFO]  %s\n' "$*" >&2; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }

usage() {
    cat >&2 <<'EOF'
Usage: find-polluter.sh --watch <artifact> --tests <glob> -- <test-cmd> [args...]

Bisects a test suite by running each test file in isolation and reporting the
first file whose run re-creates the watched pollution artifact. Use {} in the
test command as the per-file placeholder (appended if omitted). Local and
read-only except for removing the watched artifact between runs.
EOF
    exit 2
}

watch=""
tests_glob=""
declare -a test_cmd=()
saw_dashdash=0

while [ "$#" -gt 0 ]; do
    if [ "$saw_dashdash" -eq 1 ]; then
        test_cmd+=( "$1" )
        shift
        continue
    fi
    case "$1" in
        --watch)
            [ "$#" -ge 2 ] || { log_error "--watch requires a value"; usage; }
            watch="$2"; shift 2 ;;
        --tests)
            [ "$#" -ge 2 ] || { log_error "--tests requires a value"; usage; }
            tests_glob="$2"; shift 2 ;;
        --)
            saw_dashdash=1; shift ;;
        -h|--help)
            usage ;;
        *)
            log_error "unexpected argument: $1"; usage ;;
    esac
done

[ -n "$watch" ] || { log_error "--watch is required"; usage; }
[ -n "$tests_glob" ] || { log_error "--tests is required"; usage; }
[ "${#test_cmd[@]}" -ge 1 ] || { log_error "a test command is required after --"; usage; }

# Guard: never let the watch pattern resolve to an obviously catastrophic path.
case "$watch" in
    "" | "/" | "." | ".." | "/*" | "*" | "~" | "${HOME:-}" | "${HOME:-}/" )
        log_error "refusing to use an unsafe --watch pattern: '$watch'"
        exit 2 ;;
esac

# Expand the watched artifact glob and remove every match that exists. Each
# match is re-checked against the unsafe-path guard before removal. The -e test
# matters: a literal pattern (no glob metacharacters) is not subject to nullglob,
# so it expands to itself even when absent - only -e tells us it is really there.
remove_artifact() {
    local p
    shopt -s nullglob
    # Word-splitting is intentional here: $watch is a glob to expand.
    # shellcheck disable=SC2086
    for p in $watch; do
        [ -e "$p" ] || continue
        case "$p" in
            "" | "/" | "." | ".." | "${HOME:-}" | "${PWD:-}")
                shopt -u nullglob
                log_error "refusing to remove unsafe path: '$p'"
                exit 2 ;;
        esac
        rm -rf -- "$p"
    done
    shopt -u nullglob
}

# Return 0 if at least one path matching the watched artifact pattern exists on
# disk. The -e test is required: nullglob does not suppress a literal,
# metacharacter-free pattern, so `for p in leaked.lock` always yields the literal
# whether or not the file exists. Testing -e makes this correct for both literal
# paths and true globs.
artifact_exists() {
    local p
    shopt -s nullglob
    # shellcheck disable=SC2086
    for p in $watch; do
        if [ -e "$p" ]; then
            shopt -u nullglob
            return 0
        fi
    done
    shopt -u nullglob
    return 1
}

# Run the user's test command for a single file, substituting {} (or appending
# the file when no placeholder is present). A failing test must NOT abort the
# bisection - only pollution matters - so the exit status is swallowed.
run_one() {
    local test_file="$1"
    local -a cmd=()
    local part
    local substituted=0
    for part in "${test_cmd[@]}"; do
        if [ "$part" = "{}" ]; then
            cmd+=( "$test_file" )
            substituted=1
        else
            cmd+=( "$part" )
        fi
    done
    [ "$substituted" -eq 1 ] || cmd+=( "$test_file" )
    set +e
    "${cmd[@]}" >/dev/null 2>&1
    set -e
}

# Expand the test glob (sorted by default bash globbing) into a file list.
# Only keep paths that exist, so a literal, metacharacter-free --tests value
# does not slip an absent path into the list (nullglob does not suppress it).
declare -a files=()
shopt -s nullglob
# shellcheck disable=SC2086
for f in $tests_glob; do
    [ -e "$f" ] && files+=( "$f" )
done
shopt -u nullglob

[ "${#files[@]}" -ge 1 ] || { log_error "no test files matched: $tests_glob"; exit 2; }

log_info "Watching artifact: $watch"
log_info "Bisecting ${#files[@]} test file(s) from: $tests_glob"

# Start clean so a pre-existing artifact does not produce a false positive.
if artifact_exists; then
    log_info "Watched artifact already present at start; removing for a clean baseline."
    remove_artifact
fi

polluter=""
for test_file in "${files[@]}"; do
    remove_artifact
    log_info "Running in isolation: $test_file"
    run_one "$test_file"
    if artifact_exists; then
        polluter="$test_file"
        break
    fi
done

if [ -n "$polluter" ]; then
    printf '\n[RESULT] Polluter found: %s\n' "$polluter" >&2
    # The polluter path goes to stdout so the result is scriptable.
    printf '%s\n' "$polluter"
    log_info "This file re-created '$watch' when run in isolation."
else
    printf '\n[RESULT] No polluter found among %s file(s).\n' "${#files[@]}" >&2
    log_info "None of the bisected files re-created '$watch' in isolation."
fi

exit 0
