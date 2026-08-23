#!/usr/bin/env bash
# Entry point for macOS and Linux installation.
#
# Dual-mode (v3.7.0):
#   * In-repo    - run from a cloned checkout (./install.sh). Delegates to
#                  ./scripts/installer.sh exactly as before.
#   * Standalone - piped from the network:
#                      curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash
#                  Prechecks the required tools, downloads the catalog tarball
#                  from the project's own GitHub, extracts it to ~/.nexus-hub/src,
#                  and runs the extracted scripts/installer.sh. No prior clone,
#                  no unzip, no cd.
#
# The ONLY outbound call is to the project's own GitHub (github.com /
# raw.githubusercontent.com) -- the standard, audited bootstrap posture. No
# third-party data processor, credential, or new dependency is introduced.
#
# Internal testing affordances (environment variables):
#   NEXUS_HUB_REF                git ref to fetch                 (default: main)
#   NEXUS_HUB_REPO               owner/name slug      (default: bendourthe/Nexus-Hub)
#   NEXUS_HUB_TARBALL            explicit tarball source (local path OR URL);
#                                bypasses URL construction (used by the CI smoke test)
#   NEXUS_HUB_SRC                extraction target      (default: ~/.nexus-hub/src)
#   NEXUS_HUB_FORCE_STANDALONE=1 force standalone mode even inside a checkout
#   NEXUS_HUB_PRECHECK_ONLY=1    run the dependency precheck then exit (no fetch)
#   NEXUS_HUB_EXPECTED_SHA256    pin the archive SHA-256 (64 hex chars)
#   NEXUS_HUB_CHECKSUMS          path to a GNU sha256sum-format checksums.txt
#   NEXUS_HUB_SKIP_CHECKSUM=1    skip SHA-256 verification (path-traversal
#                                guard still runs). Mirrors RTK_SKIP_CHECKSUM.

set -euo pipefail

readonly NEXUS_HUB_REPO_DEFAULT="bendourthe/Nexus-Hub"

log_info()  { printf '%s\n' "$*" >&2; }
log_error() { printf 'Error: %s\n' "$*" >&2; }

# Resolve the directory this script lives in, or print nothing when it was piped
# via stdin (curl | bash leaves BASH_SOURCE unset / pointing at a non-file).
resolve_script_dir() {
    local src="${BASH_SOURCE[0]:-}"
    # Best-effort: never let a resolution failure (e.g. a stripped PATH with no
    # `dirname`) abort the script under `set -e`; just return empty.
    [ -n "$src" ] && [ -f "$src" ] || return 0
    ( cd "$( dirname "$src" 2>/dev/null )" >/dev/null 2>&1 && pwd ) || true
}

# Print an OS-appropriate "install with Y" hint for a missing tool. Uses the
# bash-provided $OSTYPE rather than the external `uname` so it still works when
# PATH is empty (the missing-tool test).
install_hint() {
    local tool="$1"
    case "${OSTYPE:-}" in
        darwin*) printf 'install it with: brew install %s' "$tool" ;;
        linux*)  printf 'install it with your package manager, e.g. "sudo apt-get install -y %s" or "sudo dnf install %s"' "$tool" "$tool" ;;
        *)       printf 'please install %s and re-run' "$tool" ;;
    esac
}

# Verify the tools the standalone bootstrap needs: a downloader (curl OR wget),
# tar, and a Python interpreter (the core installer's own dependency). Uses only
# shell builtins (command -v, printf) so it runs even with an empty PATH. Fails
# with a clear, actionable message and a non-zero exit on the first miss.
precheck_dependencies() {
    if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
        log_error "no downloader found -- need 'curl' or 'wget'. $( install_hint curl )"
        exit 1
    fi
    if ! command -v tar >/dev/null 2>&1; then
        log_error "required tool 'tar' was not found on PATH -- $( install_hint tar )"
        exit 1
    fi
    if ! command -v python3 >/dev/null 2>&1 \
        && ! command -v python >/dev/null 2>&1 \
        && ! command -v py >/dev/null 2>&1; then
        log_error "Python 3 is required by the installer but was not found -- $( install_hint python3 )"
        exit 1
    fi
}

# Download $1 (URL) to $2 (file), preferring curl and falling back to wget. Both
# carry explicit connect/total timeouts so a hung network never blocks forever.
download() {
    local url="$1" dest="$2"
    if command -v curl >/dev/null 2>&1; then
        if ! curl -fsSL --connect-timeout 15 --max-time 300 -o "$dest" "$url"; then
            log_error "download failed (curl): $url"
            exit 1
        fi
    elif command -v wget >/dev/null 2>&1; then
        if ! wget -q --timeout=300 -O "$dest" "$url"; then
            log_error "download failed (wget): $url"
            exit 1
        fi
    else
        log_error "no downloader available to fetch $url -- $( install_hint curl )"
        exit 1
    fi
}

# Like download(), but returns 1 on failure instead of exiting. Used for optional
# checksums.txt fetches so a missing tag asset does not abort the bootstrap.
try_download() {
    local url="$1" dest="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL --connect-timeout 15 --max-time 30 -o "$dest" "$url" && return 0
        return 1
    fi
    if command -v wget >/dev/null 2>&1; then
        wget -q --timeout=30 -O "$dest" "$url" && return 0
        return 1
    fi
    return 1
}

# Resolve a Python interpreter. precheck_dependencies already guaranteed one.
find_python() {
    if command -v python3 >/dev/null 2>&1; then
        printf '%s\n' python3
    elif command -v python >/dev/null 2>&1; then
        printf '%s\n' python
    elif command -v py >/dev/null 2>&1; then
        printf '%s\n' py
    else
        return 1
    fi
}

# Print the SHA-256 (lowercase hex) of file $1. Prefers sha256sum/shasum, then
# Python hashlib (already a bootstrap dependency). Never uses a network tool.
sha256_file() {
    local f="$1" py
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum -- "$f" | awk '{print $1}'
        return 0
    fi
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 -- "$f" | awk '{print $1}'
        return 0
    fi
    py="$( find_python )" || {
        log_error "cannot hash $f: no sha256sum, shasum, or Python"
        exit 1
    }
    "$py" -c 'import hashlib, sys; h = hashlib.sha256(); f = open(sys.argv[1], "rb");
chunk = f.read(1024 * 1024)
while chunk:
    h.update(chunk)
    chunk = f.read(1024 * 1024)
print(h.hexdigest())' "$f"
}

# Return 0 if tar member $1 is absolute, drive-qualified, or has a '..' component.
tar_entry_is_unsafe() {
    local entry="$1" rest part
    case "$entry" in
        /*|\\*|[A-Za-z]:*) return 0 ;;
    esac
    rest="$entry"
    while [ -n "$rest" ]; do
        part="${rest%%/*}"
        [ "$part" = "$rest" ] && part="${rest%%\\*}"
        [ "$part" = ".." ] && return 0
        if [ "$part" = "$rest" ]; then
            break
        fi
        rest="${rest#"$part"}"
        rest="${rest#/}"
        rest="${rest#\\}"
    done
    return 1
}

# List archive members (tar -tzf) and refuse CWE-22 paths. Always runs, even
# when checksum verification is skipped.
assert_archive_safe() {
    local archive="$1" entry
    while IFS= read -r entry; do
        [ -z "$entry" ] && continue
        if tar_entry_is_unsafe "$entry"; then
            log_error "refusing to extract $archive: unsafe member '$entry' (absolute or '..' path, CWE-22)"
            exit 1
        fi
    done < <( tar -tzf "$archive" )
}

# Look up a SHA-256 in a GNU sha256sum file for basename $2. Prints the hash
# if found, nothing otherwise. Comment lines (#) are ignored.
lookup_checksum() {
    local file="$1" name="$2" hash rest
    [ -f "$file" ] || return 0
    while IFS= read -r rest; do
        case "$rest" in
            ''|\#*) continue ;;
        esac
        hash="${rest%% *}"
        rest="${rest#"$hash"}"
        rest="${rest# }"
        rest="${rest# }"
        rest="${rest#\*}"
        if [ "$hash" = "$rest" ]; then
            printf '%s\n' "$hash"
            return 0
        fi
        if [ "$( basename -- "$rest" )" = "$name" ]; then
            printf '%s\n' "$hash"
            return 0
        fi
    done < "$file"
}

# Verify SHA-256 of $1 for ref $2. Tagged refs may fetch checksums.txt from
# the project's GitHub; main warns unless a pin or skip env is set.
verify_archive_checksum() {
    local archive="$1" ref="$2" repo="$3" actual expected checksums tmp_sum name
    if [ "${NEXUS_HUB_SKIP_CHECKSUM:-0}" = "1" ]; then
        log_info "checksum verification skipped (NEXUS_HUB_SKIP_CHECKSUM=1)"
        return 0
    fi
    actual="$( sha256_file "$archive" )"
    expected="${NEXUS_HUB_EXPECTED_SHA256:-}"
    expected="$( printf '%s' "$expected" | tr 'A-F' 'a-f' )"
    checksums="${NEXUS_HUB_CHECKSUMS:-}"
    name="$( basename -- "$archive" )"
    if [ -z "$expected" ] && [ -n "$checksums" ]; then
        expected="$( lookup_checksum "$checksums" "$name" )"
    fi
    if [ -z "$expected" ]; then
        case "$ref" in
            v[0-9]*|[0-9]*.[0-9]*)
                tmp_sum="$( dirname -- "$archive" )/checksums.txt"
                if try_download "https://raw.githubusercontent.com/$repo/$ref/checksums.txt" "$tmp_sum"; then
                    expected="$( lookup_checksum "$tmp_sum" "$name" )"
                    [ -z "$expected" ] && expected="$( lookup_checksum "$tmp_sum" "Nexus-Hub-${ref}.tar.gz" )"
                fi
                ;;
        esac
    fi
    if [ -n "$expected" ]; then
        if [ "$actual" != "$expected" ]; then
            log_error "checksum mismatch for $archive: expected $expected, got $actual"
            exit 1
        fi
        log_info "checksum OK ($actual)"
        return 0
    fi
    log_info "warning: unverified '${ref}' tarball (no published checksum). Set NEXUS_HUB_EXPECTED_SHA256 or NEXUS_HUB_CHECKSUMS, or NEXUS_HUB_SKIP_CHECKSUM=1 to skip."
}

# Standalone bootstrap: precheck, fetch the catalog tarball, extract it, and
# hand off to the extracted core installer.
run_standalone() {
    precheck_dependencies
    if [ "${NEXUS_HUB_PRECHECK_ONLY:-0}" = "1" ]; then
        log_info "[precheck] all required tools present (downloader, tar, python)."
        exit 0
    fi

    local ref repo src tarball archive tmp url installer
    ref="${NEXUS_HUB_REF:-main}"
    repo="${NEXUS_HUB_REPO:-$NEXUS_HUB_REPO_DEFAULT}"
    src="${NEXUS_HUB_SRC:-$HOME/.nexus-hub/src}"

    # Guard the destructive refresh below: never operate on an empty or root path.
    if [ -z "$src" ] || [ "$src" = "/" ]; then
        log_error "refusing to use unsafe extraction directory: '$src'"
        exit 1
    fi

    tmp="$( mktemp -d "${TMPDIR:-/tmp}/nexus-hub-bootstrap.XXXXXX" )"
    # shellcheck disable=SC2064  # expand $tmp now so the trap removes this run's dir
    trap "rm -rf -- '$tmp'" EXIT

    tarball="${NEXUS_HUB_TARBALL:-}"
    archive="$tmp/nexus-hub.tar.gz"
    if [ -n "$tarball" ] && [ -f "$tarball" ]; then
        log_info "Using local catalog tarball: $tarball"
        archive="$tarball"
    else
        if [ -n "$tarball" ]; then
            url="$tarball"
        else
            url="https://github.com/$repo/archive/refs/heads/$ref.tar.gz"
        fi
        log_info "Downloading Nexus-Hub catalog ($repo@$ref)..."
        download "$url" "$archive"
    fi

    assert_archive_safe "$archive"
    verify_archive_checksum "$archive" "$ref" "$repo"

    log_info "Extracting catalog to $src ..."
    rm -rf -- "$src"
    mkdir -p "$src"
    if ! tar -xzf "$archive" --strip-components=1 -C "$src"; then
        log_error "failed to extract catalog from $archive"
        exit 1
    fi

    installer="$src/scripts/installer.sh"
    if [ ! -f "$installer" ]; then
        log_error "extracted catalog has no scripts/installer.sh at $installer"
        exit 1
    fi
    chmod +x "$installer" 2>/dev/null || true

    log_info "Running installer from $src ..."
    rm -rf -- "$tmp"
    trap - EXIT
    exec bash "$installer" "$@"
}

# In-repo path: behave exactly as the pre-v3.7.0 entry point did.
run_in_repo() {
    local dir="$1"
    local installer="$dir/scripts/installer.sh"
    shift
    if [ ! -f "$installer" ]; then
        log_error "Installer script not found at $installer"
        exit 1
    fi
    chmod +x "$installer" 2>/dev/null || true
    exec "$installer" "$@"
}

main() {
    local script_dir
    script_dir="$( resolve_script_dir )"
    if [ "${NEXUS_HUB_FORCE_STANDALONE:-0}" != "1" ] \
        && [ -n "$script_dir" ] \
        && [ -f "$script_dir/scripts/installer.sh" ]; then
        run_in_repo "$script_dir" "$@"
    else
        run_standalone "$@"
    fi
}

main "$@"
