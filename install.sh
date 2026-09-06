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
#   NEXUS_HUB_RELEASE_BASE       where a TAGGED ref's published artifact set lives
#                                (URL base or a local directory holding
#                                Nexus-Hub-<version>.tar.gz and SHA256SUMS);
#                                default: the tag's GitHub Release assets
#
# Pinning (v4.7.0): `--ref <tag-or-branch>` (consumed here, not passed on) or
# NEXUS_HUB_REF selects what to install. A release tag (vX.Y.Z) downloads the
# tarball the release workflow published and verifies it against the published
# SHA256SUMS, FAIL-CLOSED: a mismatch, a missing checksum file, or an
# unresolvable ref aborts with a non-zero exit and never installs unverified.
# A branch ref (the default, main) has no publishable digest because every
# commit changes the archive, so it keeps the pin/checksums/warning behavior
# above. A tag install writes ~/.nexus-hub/PINNED_REF; a branch install
# removes it; `nexus-hub upgrade` reads it.

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

# Like download(), but returns 1 on failure so the caller can name the ref that
# failed to resolve instead of printing a bare URL error.
download_ok() {
    local url="$1" dest="$2"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL --connect-timeout 15 --max-time 300 -o "$dest" "$url" && return 0
        return 1
    fi
    if command -v wget >/dev/null 2>&1; then
        wget -q --timeout=300 -O "$dest" "$url" && return 0
        return 1
    fi
    log_error "no downloader available to fetch $url -- $( install_hint curl )"
    return 1
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


# --- Release-tag verification (v4.7.0, fail-closed) -------------------------

# Return 0 when $1 looks like a release tag (vX.Y.Z...).
is_release_tag() {
    case "$1" in
        v[0-9]*) return 0 ;;
    esac
    return 1
}

# Base of the published artifact set for tag $2 in repo $1: a URL, or a local
# directory when NEXUS_HUB_RELEASE_BASE points at one (the test seam).
release_asset_base() {
    local repo="$1" ref="$2"
    printf '%s\n' "${NEXUS_HUB_RELEASE_BASE:-https://github.com/$repo/releases/download/$ref}"
}

# Fetch published file $2 from base $1 into $3. Returns 1 on any failure, 2 when
# the base is a local directory that has no such file (so callers can tell a
# missing asset from a network failure).
fetch_release_file() {
    local base="$1" name="$2" dest="$3"
    if [ -d "$base" ]; then
        [ -f "$base/$name" ] || return 2
        cp -- "$base/$name" "$dest" || return 1
        return 0
    fi
    try_download "$base/$name" "$dest" || return 1
}

# Verify tagged archive $1 (named $2 in SHA256SUMS) for ref $3 against the
# published SHA256SUMS at base $4. Never falls back to an unverified install.
verify_release_archive() {
    local archive="$1" name="$2" ref="$3" base="$4" actual expected sums rc
    if [ "${NEXUS_HUB_SKIP_CHECKSUM:-0}" = "1" ]; then
        log_info "WARNING: checksum verification skipped for release $ref (NEXUS_HUB_SKIP_CHECKSUM=1). This install is unverified by your explicit choice."
        return 0
    fi
    actual="$( sha256_file "$archive" )"
    expected="$( printf '%s' "${NEXUS_HUB_EXPECTED_SHA256:-}" | tr 'A-F' 'a-f' )"
    if [ -z "$expected" ] && [ -n "${NEXUS_HUB_CHECKSUMS:-}" ]; then
        expected="$( lookup_checksum "$NEXUS_HUB_CHECKSUMS" "$name" )"
    fi
    if [ -z "$expected" ]; then
        sums="$( dirname -- "$archive" )/SHA256SUMS"
        rc=0
        fetch_release_file "$base" "SHA256SUMS" "$sums" || rc=$?
        if [ "$rc" -eq 2 ]; then
            log_error "release $ref carries no SHA256SUMS at $base. Tags published before v4.7.0 have no artifact set; install a newer tag, or supply NEXUS_HUB_TARBALL plus NEXUS_HUB_EXPECTED_SHA256 for this one. Not installing unverified."
            exit 1
        elif [ "$rc" -ne 0 ]; then
            log_error "could not fetch SHA256SUMS for release $ref from $base (network failure or the asset is absent; this is NOT evidence of tampering). Check the connection or the Releases page, or supply NEXUS_HUB_EXPECTED_SHA256. Not installing unverified."
            exit 1
        fi
        expected="$( lookup_checksum "$sums" "$name" )"
        if [ -z "$expected" ]; then
            log_error "SHA256SUMS for release $ref has no entry for $name. Not installing unverified."
            exit 1
        fi
    fi
    if [ "$actual" != "$expected" ]; then
        log_error "checksum mismatch for $name (release $ref): expected $expected, got $actual. The download does not match what the release published; delete it and re-download, and if it repeats, treat the artifact as suspect. Not installing."
        exit 1
    fi
    log_info "checksum OK ($actual)"
}

# Record or clear the pin marker beside the extraction root ($1) for ref $2.
record_pin() {
    local src="$1" ref="$2" pin_dir
    pin_dir="$( dirname -- "$src" )"
    if is_release_tag "$ref"; then
        mkdir -p -- "$pin_dir" 2>/dev/null || true
        printf '%s\n' "$ref" > "$pin_dir/PINNED_REF" 2>/dev/null || true
    else
        rm -f -- "$pin_dir/PINNED_REF" 2>/dev/null || true
    fi
}

# Standalone bootstrap: precheck, fetch the catalog tarball, extract it, and
# hand off to the extracted core installer.
run_standalone() {
    precheck_dependencies
    if [ "${NEXUS_HUB_PRECHECK_ONLY:-0}" = "1" ]; then
        log_info "[precheck] all required tools present (downloader, tar, python)."
        exit 0
    fi

    local ref repo src tarball archive tmp url installer ref_flag="" base name
    # Consume --ref / --ref=<value> here; everything else passes through to the
    # core installer untouched.
    local -a passthru=()
    while [ $# -gt 0 ]; do
        case "$1" in
            --ref)
                [ $# -ge 2 ] || { log_error "--ref needs a value (a tag such as v4.7.0, or a branch)"; exit 1; }
                ref_flag="$2"; shift 2 ;;
            --ref=*)
                ref_flag="${1#--ref=}"; shift ;;
            *)
                passthru+=("$1"); shift ;;
        esac
    done
    set -- ${passthru[@]+"${passthru[@]}"}
    ref="${ref_flag:-${NEXUS_HUB_REF:-main}}"
    if [ -z "$ref" ]; then
        log_error "--ref needs a value (a tag such as v4.7.0, or a branch)"
        exit 1
    fi
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
    name="Nexus-Hub-${ref#v}.tar.gz"
    base="$( release_asset_base "$repo" "$ref" )"
    if [ -n "$tarball" ] && [ -f "$tarball" ]; then
        log_info "Using local catalog tarball: $tarball"
        archive="$tarball"
    elif is_release_tag "$ref"; then
        # A release tag installs the artifact the project PUBLISHED, not GitHub's
        # generated archive, and the download is verified fail-closed below.
        log_info "Downloading Nexus-Hub release $ref ($repo)..."
        if ! fetch_release_file "$base" "$name" "$archive"; then
            log_error "could not resolve release '$ref' at $base: no $name (a typo, a tag that was never published, or a network failure). List versions at https://github.com/$repo/releases or with: gh release list -R $repo"
            exit 1
        fi
    else
        if [ -n "$tarball" ]; then
            url="$tarball"
        else
            url="https://github.com/$repo/archive/refs/heads/$ref.tar.gz"
        fi
        log_info "Downloading Nexus-Hub catalog ($repo@$ref)..."
        if ! download_ok "$url" "$archive"; then
            log_error "could not resolve branch '$ref' in $repo (a typo or a branch that does not exist). List releases at https://github.com/$repo/releases or pin one with --ref vX.Y.Z"
            exit 1
        fi
    fi

    assert_archive_safe "$archive"
    if is_release_tag "$ref"; then
        verify_release_archive "$archive" "$name" "$ref" "$base"
    else
        verify_archive_checksum "$archive" "$ref" "$repo"
    fi
    record_pin "$src" "$ref"

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
