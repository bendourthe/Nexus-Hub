#!/bin/bash
# Nexus-Hub Universal Installer V10 (macOS/Linux)
# Installs AI Skills Globally OR to a Workspace with Safe Overwrite

set -e

# --- Version ---
# Single source of truth for the installer banner version label.
# Keep in sync with .claude-plugin/plugin.json and CHANGELOG.md.
NEXUS_HUB_VERSION="4.7.0"

# --- Window Title ---
printf '\033]0;Nexus-Hub Installer\007'

# --- Colors ---
RESET='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
DARK_YELLOW='\033[0;33m' # Approximate
BRIGHT_CYAN='\033[0;96m'    # OpenCode - distinct from the teal CYAN used by Microsoft
BRIGHT_MAGENTA='\033[0;95m' # Anysphere/Cursor - distinct from the dark MAGENTA used by OpenAI
DARK_BLUE='\033[38;5;18m'   # Nexus - navy, distinct from the BLUE used by Google
DARK_GREEN='\033[38;5;22m'  # Windsurf - distinct from the GREEN used by Aider
DARK_RED='\033[38;5;88m'    # Qwen - distinct from the RED used by Kimi
# DARK_CYAN removed in v2.1.0 - only used by the legacy 120-char banner rules.

# Resolved overwrite decision (v3.7.0 / Phase 2).
#   true  = "refresh" mode: existing managed files are overwritten with the
#           Nexus-Hub version silently (the non-interactive / --yes / --force /
#           bootstrap path). Also threaded to the registry runner as --overwrite.
#   false = "conflict-collection" mode (interactive, no --yes/--force): managed
#           single files whose on-disk content differs are recorded as conflicts
#           and KEPT; after the install pass resolve_conflicts() lists them and
#           asks once whether to overwrite. Resolved once at startup; install_*
#           no longer toggle it.
OVERWRITE_ALL=false

# Non-interactive / assume-yes decision (v3.7.0 / Phase 2). True under --yes,
# --force, or when stdin is not a TTY (piped curl|bash, CI). Drives both the
# OVERWRITE_ALL refresh decision and the suppression of any remaining content
# prompts (e.g. workspace language selection).
ASSUME_YES=false

# Conflict accumulators (interactive mode only). Parallel arrays of source ->
# destination pairs for managed single files that differ on disk and were kept
# pending the single end-of-run confirmation in resolve_conflicts().
CONFLICT_SRCS=()
CONFLICT_DSTS=()

# Temp files created for deferred writes (e.g. the generated Copilot workspace
# instruction file routed through safe_copy). Cleaned on EXIT.
TEMP_FILES=()
cleanup_temp_files() {
    local f
    for f in ${TEMP_FILES[@]+"${TEMP_FILES[@]}"}; do
        [ -n "$f" ] && rm -f "$f"
    done
}
trap cleanup_temp_files EXIT

# Platform subset filter (v3.7.0 / Phase 2). Empty = install ALL platforms
# (the default). Otherwise a space-delimited set of integration keys; only the
# matching per-provider blocks run. Populated from --platforms <csv>.
PLATFORMS_FILTER=""

# should_install <integration-key> -- gate a per-provider install block on the
# --platforms subset. Returns 0 (install) when no filter is set or the key is in
# the filter; 1 (skip) otherwise.
should_install() {
    [ -z "$PLATFORMS_FILTER" ] && return 0
    case " $PLATFORMS_FILTER " in
        *" $1 "*) return 0 ;;
        *) return 1 ;;
    esac
}

# --- Formatting Helpers ---

# Modernized in v2.1.0: dropped the 120-char dash rules in favor of light
# typographical accents. Function names are preserved so call sites and smoke
# tests do not need to change.

get_provider_color() {
    # Provider-level headers (v2.1.0+)
    case "$1" in
        "ANTHROPIC")        echo -ne "${DARK_YELLOW}" ;;
        "OPENAI")           echo -ne "${MAGENTA}" ;;
        "GOOGLE")           echo -ne "${BLUE}" ;;
        "MICROSOFT")        echo -ne "${CYAN}" ;;
        "ANYSPHERE")        echo -ne "${BRIGHT_MAGENTA}" ;;
        "OPENCODE")         echo -ne "${BRIGHT_CYAN}" ;;
        "AIDER")            echo -ne "${GREEN}" ;;
        "WINDSURF")         echo -ne "${DARK_GREEN}" ;;
        "KIMI")             echo -ne "${RED}" ;;
        "QWEN")             echo -ne "${DARK_RED}" ;;
        "OPENCLAW")         echo -ne "${YELLOW}" ;;
        "NEXUS")            echo -ne "${DARK_BLUE}" ;;
        *)                  echo -ne "${RESET}" ;;
    esac
}

write_header() {
    local provider="$1"
    local color
    color=$(get_provider_color "$provider")
    echo ""
    echo -e "  ${color}> ${provider}${RESET}"
}

write_item() {
    local message="$1"
    local color_code="$2" # e.g., $GREEN
    local indent="${3:-2}"

    local spaces=""
    for ((i=0; i<indent; i++)); do spaces+=" "; done

    if [ -z "$color_code" ]; then color_code="${RESET}"; fi
    echo -e "${spaces}${color_code}${message}${RESET}"
}

read_prompt() {
    local message="$1"
    local indent="${2:-2}"

    local spaces=""
    for ((i=0; i<indent; i++)); do spaces+=" "; done

    echo -ne "${spaces}${YELLOW}${message}: ${RESET}" >&2
    read -r response
    echo "$response"
}

write_subsection_banner() {
    local text="$1"
    local color="${2:-$YELLOW}"
    echo ""
    echo -e "  ${color}- ${text}${RESET}"
}

# A top-level "> SECTION" banner (column 0, uppercase) - the bash analogue of the
# PowerShell installer's "> TEXT" main-section header. Prepends its own single
# blank line so callers do not add one. Providers (write_header) and
# subsections (write_subsection_banner) render indented beneath it.
write_section_banner() {
    local text="$1"
    local color="${2:-$CYAN}"
    echo ""
    echo -e "${color}> ${text}${RESET}"
}

# --- Per-platform install checklist (v3.14.5 Phase 2) ---
# The registry runner emits a structured per-surface summary
# (runner.py --summary-json); render it as a fixed-order checklist so every
# platform reads identically, and collect platforms whose tool was not detected
# into one "NOT DETECTED" group. Mirrors the PowerShell installer.

CHECKLIST_ORDER="instruction skills commands agents rules hooks settings"

checklist_label() {
    case "$1" in
        instruction) echo "Core Files" ;;
        skills)      echo "Skills" ;;
        commands)    echo "Commands" ;;
        agents)      echo "Agents" ;;
        rules)       echo "Rules" ;;
        hooks)       echo "Hooks" ;;
        settings)    echo "Core Settings" ;;
        *)           echo "$1" ;;
    esac
}

# Platforms whose tool was not detected on this machine (grouped at run end).
UNDETECTED_PLATFORMS=()

reset_undetected_platforms() { UNDETECTED_PLATFORMS=(); }

add_undetected_platform() {
    # Args: name reason
    UNDETECTED_PLATFORMS+=("$1 ($2)")
}

write_undetected_group() {
    [ "${#UNDETECTED_PLATFORMS[@]}" -eq 0 ] && return 0
    echo ""
    echo -e "  ${GRAY}> NOT DETECTED (skipped)${RESET}"
    local entry
    for entry in "${UNDETECTED_PLATFORMS[@]}"; do
        echo -e "    ${GRAY}- ${entry}${RESET}"
    done
}

write_checklist_row() {
    # Args: label state detail   (state: ok|warn)
    local label="$1" state="$2" detail="$3"
    local mark color col
    if [ "$state" = "ok" ]; then mark="[OK]"; color="$GREEN"; else mark="[!]"; color="$YELLOW"; fi
    # Pad the label column (printf, no color escapes) then colorize via echo -e.
    col="$(printf '%-16s' "${label}:")"
    echo -e "    ${color}${mark} ${col} ${detail}${RESET}"
}

render_platform_from_summary() {
    # Args: summary_file key provider display py
    # Renders the platform's fixed-order checklist (lazy header when provider is
    # set) or records it in the undetected group when it delivered no surface.
    local sfile="$1" key="$2" provider="$3" display="$4" py="$5"
    local extract
    extract="$("$py" - "$sfile" "$key" <<'PYEOF'
import json, sys
sfile, key = sys.argv[1], sys.argv[2]
try:
    data = json.load(open(sfile, encoding="utf-8"))
except Exception:
    print("META\t\t0\t0"); sys.exit(0)
plat = next((p for p in data.get("platforms", []) if p.get("platform") == key), None)
if not plat:
    print("META\t\t0\t0"); sys.exit(0)
det = plat.get("detected")
det_s = "true" if det is True else ("false" if det is False else "")
notes = plat.get("notes") or []
surfaces = plat.get("surfaces", {}) or {}
print("META\t%s\t%d\t%d" % (det_s, len(surfaces), len(notes)))
for skey, entry in surfaces.items():
    print("ROW\t%s\t%s\t%s" % (skey, entry.get("status", ""), entry.get("path", "")))
PYEOF
)"
    local detected surface_count note_count
    detected="$(printf '%s\n' "$extract" | awk -F'\t' '$1=="META"{print $2; exit}')"
    surface_count="$(printf '%s\n' "$extract" | awk -F'\t' '$1=="META"{print $3; exit}')"
    note_count="$(printf '%s\n' "$extract" | awk -F'\t' '$1=="META"{print $4; exit}')"

    if [ "${surface_count:-0}" -eq 0 ]; then
        local reason="not detected"
        if [ "$detected" != "false" ] && [ "${note_count:-0}" -gt 0 ]; then
            reason="no surface at this scope"
        fi
        if [ -n "$provider" ]; then
            add_undetected_platform "$display" "$reason"
        else
            write_item "$display" "$GRAY"
            write_item "($reason)" "$GRAY" 4
        fi
        return 0
    fi

    [ -n "$provider" ] && write_header "$provider"
    write_item "$display" "$GRAY"
    local surface line status path label
    for surface in $CHECKLIST_ORDER; do
        line="$(printf '%s\n' "$extract" | awk -F'\t' -v s="$surface" '$1=="ROW" && $2==s {print; exit}')"
        [ -z "$line" ] && continue
        status="$(printf '%s\n' "$line" | cut -f3)"
        path="$(printf '%s\n' "$line" | cut -f4)"
        label="$(checklist_label "$surface")"
        if [ "$status" = "installed" ]; then
            write_checklist_row "$label" "ok" "$path"
        else
            write_checklist_row "$label" "warn" "install reported an issue"
        fi
    done
}

# Copy a single managed file with conflict-only overwrite semantics (v3.7.0 /
# Phase 2). The third parameter (`confirm`) is retained for call-site signature
# compatibility but no longer gates a prompt: conflict handling is now uniform
# and driven by the resolved OVERWRITE_ALL decision.
#
#   - source missing                -> skip-with-note
#   - destination missing           -> create
#   - destination identical to src  -> nothing to do (idempotent, silent)
#   - destination differs:
#       OVERWRITE_ALL=true (refresh)  -> overwrite now
#       OVERWRITE_ALL=false (interactive) -> record conflict + KEEP; the single
#         end-of-run resolve_conflicts() prompt decides whether to overwrite.
safe_copy() {
    local source="$1"
    local destination="$2"
    # The 3rd positional arg (formerly the per-file confirm flag) is retained so
    # the ~30 existing 4-arg call sites keep working; conflict handling is now
    # uniform and driven by OVERWRITE_ALL, so the value itself is unused.
    # shellcheck disable=SC2034
    local confirm="${3:-false}"
    local custom_message="$4"

    if [ ! -f "$source" ]; then
        write_item "Skip: Source not found ($(basename "$source"))" "$GRAY"
        return
    fi

    if [ -f "$destination" ]; then
        if cmp -s "$source" "$destination"; then
            # Already current -- nothing to write.
            return
        fi
        if [ "$OVERWRITE_ALL" != true ]; then
            # Interactive conflict: a managed file the user may have customized
            # differs from the catalog version. Keep it for now and defer to the
            # single end-of-run confirmation.
            CONFLICT_SRCS+=("$source")
            CONFLICT_DSTS+=("$destination")
            write_item "Differs (kept; pending confirmation): $destination" "$DARK_YELLOW"
            return
        fi
    fi

    mkdir -p "$(dirname "$destination")"
    cp "$source" "$destination"
    if [ -n "$custom_message" ]; then
        write_item "$custom_message" "$GREEN"
    else
        write_item "[OK] Installed to $destination" "$GREEN"
    fi
}

# Recursively copies an entire folder tree from source to destination.
#
# Per-skill bundled resources (scripts/, references/, assets/) under
# catalog/skills/<cat>/<name>/ are copied recursively as part of the parent
# skill folder copy - both the rsync -a path and the cp -R fallback preserve
# arbitrary subdirectory depth. This is the auto-distribution behavior
# documented in AGENTS.md "Per-skill Bundled Resources"; no per-skill
# explicit-name copy step is needed for skill-bundled content.
safe_folder_copy() {
    local source="$1"
    local destination="$2"
    local custom_message="$3"

    if [ ! -d "$source" ]; then
        return
    fi

    local do_copy=true

    # Catalog trees (skills/commands/agents/rules) are Nexus-owned content meant
    # to be refreshed on every install/upgrade, so they no longer prompt
    # (v3.7.0 / Phase 2). The resolved OVERWRITE_ALL decision picks the sync mode:
    #   refresh (true)      -> full sync: refresh files AND remove stale ones
    #                          (the non-interactive / --yes / --force / bootstrap
    #                          path; matches the previous "[A]ll" behavior).
    #   interactive (false) -> merge-only: add/update files but keep any extras
    #                          the user added (never destructive, no prompt).
    local full_sync=true
    [ "$OVERWRITE_ALL" = true ] || full_sync=false

    if [ ! -d "$destination" ]; then
        mkdir -p "$destination"
    fi

    if [ "$do_copy" = true ]; then
        if [ "$full_sync" = true ]; then
            write_item "Syncing (stale files in destination will be removed)..." "$GRAY"
            # Use rsync if available, otherwise cp
            if command -v rsync >/dev/null 2>&1; then
                rsync -a --delete "$source/" "$destination/"
            else
                rm -rf "${destination:?}"/*
                cp -R "$source/"* "$destination/"
            fi
        else
            write_item "Merging (adding/updating files, keeping extras)..." "$GRAY"
            if command -v rsync >/dev/null 2>&1; then
                rsync -a "$source/" "$destination/"
            else
                cp -R "$source/"* "$destination/"
            fi
        fi

        if [ -n "$custom_message" ]; then
            write_item "$custom_message" "$GREEN"
        else
            write_item "[OK] Installed to $destination" "$GREEN"
        fi
    fi
}

# Install the skills catalog FLATTENED to the one-level layout Claude Code
# requires. Claude discovers skills exactly one level deep
# (<dir>/skills/<name>/SKILL.md), so the catalog's <category>/ tier must be
# dropped (this honors scripts/lib/integrations/claude.py's
# flatten_skills_layout: True; Codex / Gemini already flatten via the registry
# adapter). A verbatim category-nested copy leaves every SKILL.md at
# <dir>/skills/<category>/<name>/, which Claude cannot see. We stage a flattened
# copy in a temp dir, then hand it to safe_folder_copy, reusing its refresh-prune
# (rsync --delete) and merge semantics unchanged - so a prior category-nested
# layout and any upstream-removed skill are pruned in refresh mode, with no
# bespoke prune logic here and strict parity with the PowerShell installer.
flatten_skills_into() {
    local source="$1"       # catalog/skills
    local destination="$2"  # <claude>/skills
    local custom_message="$3"

    if [ ! -d "$source" ]; then
        return
    fi

    local staging
    staging="$(mktemp -d)"

    local category skill
    for category in "$source"/*/; do
        [ -d "$category" ] || continue
        for skill in "$category"*/; do
            [ -d "$skill" ] || continue
            cp -R "${skill%/}" "$staging/"
        done
    done

    # Drop any category directories left by a PRIOR category-nested install so
    # the undiscoverable <dir>/skills/<category>/ layout never lingers. In refresh
    # mode safe_folder_copy's --delete already prunes them; this also covers merge
    # mode (catalog category names are never skill names, so flat skills and any
    # user-added skills are untouched).
    if [ -d "$destination" ]; then
        for category in "$source"/*/; do
            [ -d "$category" ] || continue
            rm -rf "${destination:?}/$(basename "$category")"
        done
    fi

    safe_folder_copy "$staging" "$destination" "$custom_message"
    rm -rf "$staging"
}

# Resolve any conflicts accumulated by safe_copy during an interactive install
# (v3.7.0 / Phase 2). Conflicts are only ever recorded in interactive mode
# (OVERWRITE_ALL=false), so this prints the list, asks ONCE, and -- on
# confirmation -- overwrites the kept files with the Nexus-Hub version. The
# non-interactive / --yes / --force path overwrites inline and reaches here with
# an empty list (no-op).
resolve_conflicts() {
    local count="${#CONFLICT_DSTS[@]}"
    [ "$count" -eq 0 ] && return 0

    write_subsection_banner "Existing customizations detected"
    write_item "${count} managed file(s) on disk differ from the Nexus-Hub version:" "$YELLOW"
    local i
    for ((i=0; i<count; i++)); do
        write_item "- ${CONFLICT_DSTS[$i]}" "$DARK_YELLOW"
    done

    local resp
    resp=$(read_prompt "Overwrite these with the Nexus-Hub version? [y/N]")
    if [[ "$resp" =~ ^[Yy] ]]; then
        for ((i=0; i<count; i++)); do
            mkdir -p "$(dirname "${CONFLICT_DSTS[$i]}")"
            cp "${CONFLICT_SRCS[$i]}" "${CONFLICT_DSTS[$i]}"
            write_item "[OK] Refreshed ${CONFLICT_DSTS[$i]}" "$GREEN"
        done
    else
        write_item "Kept your ${count} customized file(s). Re-run with --yes (or --force) to refresh them." "$GRAY"
    fi
}

# --- Hook Installation ---

install_claude_hook_files() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"
    local hooks_dir="$target_claude_dir/hooks"
    local source

    mkdir -p "$hooks_dir"
    for source in "$repo_root"/catalog/hooks/*.sh "$repo_root"/catalog/hooks/*.py; do
        [ -f "$source" ] || continue
        safe_copy "$source" "$hooks_dir/$(basename "$source")" true "[OK] $scope hook installed: $(basename "$source")"
        if [[ "$source" == *.sh ]]; then
            chmod +x "$hooks_dir/$(basename "$source")" 2>/dev/null || true
        fi
    done
}

convert_claude_hook_commands_for_posix() {
    local repo_root="$1"
    local settings_file="$2"
    local scope="$3"
    local python_bin

    [ -f "$settings_file" ] || return 0
    if ! python_bin=$(resolve_python_executable); then
        write_item "ERROR: Python is required to migrate Claude hook commands for Cursor compatibility" "$RED" >&2
        return 1
    fi
    "$python_bin" "$repo_root/catalog/hooks/cursor-hook-compat.py" \
        --rewrite-settings "$settings_file" \
        --catalog-hooks-dir "$repo_root/catalog/hooks" \
        --host posix \
        --scope "$(printf '%s' "$scope" | tr '[:upper:]' '[:lower:]')"
}

resolve_settings_write_target() {
    local path="$1"
    local link_target target_dir
    local depth=0

    while [ -L "$path" ]; do
        depth=$((depth + 1))
        if [ "$depth" -gt 40 ]; then
            return 1
        fi
        if ! link_target=$(readlink "$path"); then
            return 1
        fi
        case "$link_target" in
            /*) path="$link_target" ;;
            *) path="$(dirname "$path")/$link_target" ;;
        esac
    done

    if ! target_dir=$(cd -P "$(dirname "$path")" 2>/dev/null && pwd); then
        return 1
    fi
    printf '%s/%s\n' "$target_dir" "$(basename "$path")"
}

merge_managed_claude_hooks() {
    local settings_file="$1"
    local template_file="$2"

    if command -v jq >/dev/null 2>&1; then
        jq -s '
            def hook_stem:
                (.command // "") as $command |
                (([
                    $command |
                    match("(?<stem>[A-Za-z0-9_-]+)\\.(?:sh|ps1|py)"; "g") |
                    .captures[0].string
                ] | last) // $command);
            def hook_exists($hooks; $event; $matcher; $candidate):
                any(($hooks[$event] // [])[];
                    (.matcher // "") == $matcher and
                    any((.hooks // [])[];
                        (.type // "") == ($candidate.type // "") and
                        hook_stem == ($candidate | hook_stem)
                    )
                );
            .[0] as $existing | .[1] as $template |
            reduce (($template.hooks // {}) | to_entries[]) as $event (
                ($existing |
                    if (.hooks | type) == "object" then .
                    else . + {hooks: {}}
                    end
                );
                reduce (($event.value // [])[]) as $entry (.;
                    reduce (($entry.hooks // [])[]) as $hook (.;
                        if hook_exists(.hooks; $event.key; ($entry.matcher // ""); $hook) then .
                        else .hooks[$event.key] = (
                            (.hooks[$event.key] // []) + [($entry | .hooks = [$hook])]
                        )
                        end
                    )
                )
            )
        ' "$settings_file" "$template_file" 2>/dev/null
        return
    fi

    local python_bin
    if ! python_bin=$(resolve_python_executable); then
        return 127
    fi

    "$python_bin" - "$settings_file" "$template_file" <<'PY'
import json
import re
import sys


HOOK_STEM_PATTERN = re.compile(r"(?P<stem>[A-Za-z0-9_-]+)\.(?:sh|ps1|py)")


def load_object(path):
    with open(path, encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def hook_stem(hook):
    command = hook.get("command") or ""
    if not isinstance(command, str):
        raise ValueError("managed hook command must be a string")
    matches = list(HOOK_STEM_PATTERN.finditer(command))
    return matches[-1].group("stem") if matches else command


def hook_exists(hooks, event, matcher, candidate):
    entries = hooks.get(event, [])
    if not isinstance(entries, list):
        raise ValueError(f"existing hooks.{event} must be an array")
    for entry in entries:
        if not isinstance(entry, dict) or (entry.get("matcher") or "") != matcher:
            continue
        installed_hooks = entry.get("hooks") or []
        if not isinstance(installed_hooks, list):
            raise ValueError(f"existing hooks.{event}[].hooks must be an array")
        for installed in installed_hooks:
            if not isinstance(installed, dict):
                continue
            if (installed.get("type") or "") == (candidate.get("type") or "") and hook_stem(installed) == hook_stem(candidate):
                return True
    return False


try:
    existing = load_object(sys.argv[1])
    template = load_object(sys.argv[2])
    hooks = existing.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        existing["hooks"] = hooks
    template_hooks = template.get("hooks") or {}
    if not isinstance(template_hooks, dict):
        raise ValueError("template hooks must be an object")

    for event, entries in template_hooks.items():
        if not isinstance(entries, list):
            raise ValueError(f"template hooks.{event} must be an array")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"template hooks.{event} entries must be objects")
            matcher = entry.get("matcher") or ""
            candidates = entry.get("hooks") or []
            if not isinstance(candidates, list):
                raise ValueError(f"template hooks.{event}[].hooks must be an array")
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    raise ValueError(f"template hooks.{event}[].hooks entries must be objects")
                if hook_exists(hooks, event, matcher, candidate):
                    continue
                event_hooks = hooks.setdefault(event, [])
                if not isinstance(event_hooks, list):
                    raise ValueError(f"existing hooks.{event} must be an array")
                new_entry = dict(entry)
                new_entry["hooks"] = [candidate]
                event_hooks.append(new_entry)

    json.dump(existing, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
except (OSError, TypeError, ValueError) as error:
    print(f"managed hook merge failed: {error}", file=sys.stderr)
    raise SystemExit(1)
PY
}

install_git_guardrails() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"  # "Global" or "Workspace"

    # Materialize every shell/Python hook referenced by the full settings template.
    install_claude_hook_files "$repo_root" "$target_claude_dir" "$scope"

    # Preserve the legacy explicit copies for compatibility with narrowly staged
    # source bundles while the full catalog copy above owns normal installations.
    local hooks_dir="$target_claude_dir/hooks"
    mkdir -p "$hooks_dir"
    safe_copy "$repo_root/catalog/hooks/git-guardrails.sh" "$hooks_dir/git-guardrails.sh" true "[OK] $scope git guardrails hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/git-guardrails.sh" 2>/dev/null || true

    # compress-output.sh is the other PreToolUse Bash hook; it ships alongside
    # git-guardrails because the settings.json merge below pulls the whole
    # PreToolUse array (which now includes it). It is opt-in / default-off
    # (inert unless NEXUS_CONTEXT_COMPRESS=1), so copying the file is harmless.
    safe_copy "$repo_root/catalog/hooks/compress-output.sh" "$hooks_dir/compress-output.sh" true "[OK] $scope output-compression hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/compress-output.sh" 2>/dev/null || true

    # Merge hook config into settings.json
    local settings_file="$target_claude_dir/settings.json"
    local template_file="$repo_root/catalog/hooks/settings.json"
    local settings_write_target

    if [ ! -f "$template_file" ]; then
        write_item "Skip: Hook template not found" "$GRAY"
        return
    fi

    if ! settings_write_target=$(resolve_settings_write_target "$settings_file"); then
        write_item "ERROR: Could not resolve the settings write target for $settings_file" "$RED" >&2
        return 1
    fi

    if [ -f "$settings_file" ]; then
        # Reconcile every managed template hook. Hook identity ignores the host
        # suffix so an existing .ps1 registration and a template .sh registration
        # represent the same managed hook during cross-host upgrades.
        local merged merge_status candidate_file
        if merged=$(merge_managed_claude_hooks "$settings_file" "$template_file"); then
            if [ -z "$merged" ]; then
                write_item "ERROR: Managed hook reconciliation produced no settings content for $settings_file" "$RED" >&2
                return 1
            else
                if ! candidate_file=$(mktemp "${settings_write_target}.nexus-candidate.XXXXXX"); then
                    write_item "ERROR: Could not create a transactional settings candidate for $settings_file" "$RED" >&2
                    return 1
                fi
                if ! printf '%s\n' "$merged" > "$candidate_file"; then
                    rm -f "$candidate_file"
                    write_item "ERROR: Could not stage reconciled settings for $settings_file" "$RED" >&2
                    return 1
                fi
                if ! convert_claude_hook_commands_for_posix "$repo_root" "$candidate_file" "$scope"; then
                    rm -f "$candidate_file"
                    write_item "ERROR: Hook command conversion failed; $settings_file was left unchanged" "$RED" >&2
                    return 1
                fi
                if ! mv -f "$candidate_file" "$settings_write_target"; then
                    rm -f "$candidate_file"
                    write_item "ERROR: Could not replace $settings_file with reconciled settings" "$RED" >&2
                    return 1
                fi
                write_item "[OK] $scope settings.json reconciled with managed hooks" "$GREEN"
            fi
        else
            merge_status=$?
            if [ "$merge_status" -eq 127 ]; then
                write_item "ERROR: Cannot safely upgrade $settings_file without jq, python3, or python" "$RED" >&2
                write_item "Install one of these JSON parsers and rerun the installer; settings were left unchanged." "$RED" >&2
            else
                write_item "ERROR: Could not safely reconcile $settings_file with managed hooks" "$RED" >&2
            fi
            return 1
        fi
    else
        # A fresh settings file is also transactional: conversion failure must
        # not leave a copied but non-runnable hook registration behind.
        local candidate_file
        if ! candidate_file=$(mktemp "${settings_write_target}.nexus-candidate.XXXXXX"); then
            write_item "ERROR: Could not create a transactional settings candidate for $settings_file" "$RED" >&2
            return 1
        fi
        if ! cp "$template_file" "$candidate_file"; then
            rm -f "$candidate_file"
            write_item "ERROR: Could not stage hook settings from $template_file" "$RED" >&2
            return 1
        fi
        if ! convert_claude_hook_commands_for_posix "$repo_root" "$candidate_file" "$scope"; then
            rm -f "$candidate_file"
            write_item "ERROR: Hook command conversion failed; $settings_file was not created" "$RED" >&2
            return 1
        fi
        if ! mv -f "$candidate_file" "$settings_write_target"; then
            rm -f "$candidate_file"
            write_item "ERROR: Could not create $settings_file from converted settings" "$RED" >&2
            return 1
        fi
        write_item "[OK] $scope settings.json created with git guardrails hook" "$GREEN"
    fi
}

install_usage_display() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"  # "Global" or "Workspace"

    # Copy hook script
    local hooks_dir="$target_claude_dir/hooks"
    mkdir -p "$hooks_dir"
    safe_copy "$repo_root/catalog/hooks/usage-display.sh" "$hooks_dir/usage-display.sh" true "[OK] $scope usage display hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/usage-display.sh" 2>/dev/null || true

    # Merge Stop hook config into settings.json
    local settings_file="$target_claude_dir/settings.json"
    local template_file="$repo_root/catalog/hooks/settings.json"

    if [ ! -f "$template_file" ]; then
        write_item "Skip: Hook template not found" "$GRAY"
        return
    fi

    if [ -f "$settings_file" ]; then
        # Check if usage-display already installed
        if grep -q "usage-display" "$settings_file" 2>/dev/null; then
            write_item "[OK] Usage display hook already configured in settings.json" "$GREEN"
            return
        fi

        # Merge using jq if available
        if command -v jq >/dev/null 2>&1; then
            local merged
            merged=$(jq -s '
                .[0] as $existing | .[1] as $template |
                if $existing.hooks then
                    if $existing.hooks.Stop then
                        $existing | .hooks.Stop += $template.hooks.Stop
                    else
                        $existing | .hooks.Stop = $template.hooks.Stop
                    end
                else
                    $existing + {hooks: {Stop: $template.hooks.Stop}}
                end
            ' "$settings_file" "$template_file" 2>/dev/null)

            if [ -n "$merged" ]; then
                echo "$merged" > "$settings_file"
                convert_claude_hook_commands_for_posix "$repo_root" "$settings_file" "$scope"
                write_item "[OK] $scope settings.json updated with usage display hook" "$GREEN"
            else
                write_item "Warning: Could not merge usage display hook into settings.json" "$YELLOW"
                write_item "  You may need to manually add the Stop hook config" "$YELLOW"
            fi
        else
            write_item "Warning: jq not found, cannot merge settings.json automatically" "$YELLOW"
            write_item "  Please manually add Stop hook config from: $template_file" "$YELLOW"
        fi
    fi
    # If no settings.json exists, install_git_guardrails will create it from the
    # template (which now includes both PreToolUse and Stop hooks).
}

install_require_description() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"  # "Global" or "Workspace"

    # Copy hook scripts
    local hooks_dir="$target_claude_dir/hooks"
    mkdir -p "$hooks_dir"
    safe_copy "$repo_root/catalog/hooks/require-description.sh" "$hooks_dir/require-description.sh" true "[OK] $scope require-description hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/require-description.sh" 2>/dev/null || true
    safe_copy "$repo_root/catalog/hooks/format-bash-description.py" "$hooks_dir/format-bash-description.py" true "[OK] $scope format-bash-description hook installed at: $hooks_dir"
    safe_copy "$repo_root/catalog/hooks/require-powershell-description.sh" "$hooks_dir/require-powershell-description.sh" true "[OK] $scope require-powershell-description hook installed at: $hooks_dir"
    chmod +x "$hooks_dir/require-powershell-description.sh" 2>/dev/null || true
    safe_copy "$repo_root/catalog/hooks/format-powershell-description.py" "$hooks_dir/format-powershell-description.py" true "[OK] $scope format-powershell-description hook installed at: $hooks_dir"

    # Merge hook config into settings.json
    local settings_file="$target_claude_dir/settings.json"

    if [ ! -f "$settings_file" ]; then
        # install_git_guardrails will create it from the template (which includes both Bash and PowerShell description hooks)
        return
    fi

    if ! command -v jq >/dev/null 2>&1; then
        write_item "Warning: jq not found, cannot merge description hooks into settings.json automatically" "$YELLOW"
        write_item "  Please manually add the PreToolUse hooks for require-description.sh and require-powershell-description.sh" "$YELLOW"
        return
    fi

    # Bash require-description: check uses a more specific pattern so it does
    # not match require-powershell-description.
    if grep -qE 'require-description\.sh|require-description"' "$settings_file" 2>/dev/null; then
        write_item "[OK] Require-description (Bash) hook already configured in settings.json" "$GREEN"
    else
        local merged_bash
        merged_bash=$(jq '.hooks.PreToolUse |= (. + [{"matcher": "Bash", "hooks": [{"type": "command", "command": "bash .claude/hooks/require-description.sh"}]}])' "$settings_file" 2>/dev/null)
        if [ -n "$merged_bash" ]; then
            echo "$merged_bash" > "$settings_file"
            write_item "[OK] $scope settings.json updated with require-description (Bash) hook" "$GREEN"
        else
            write_item "Warning: Could not merge require-description (Bash) hook into settings.json" "$YELLOW"
        fi
    fi

    # PowerShell require + format hooks: registered independently from Bash so
    # an upgrade path that already has the Bash hook still picks these up.
    if grep -q "require-powershell-description" "$settings_file" 2>/dev/null; then
        write_item "[OK] Require-description (PowerShell) hook already configured in settings.json" "$GREEN"
    else
        local merged_ps
        merged_ps=$(jq '.hooks.PreToolUse |= (. + [
            {"matcher": "PowerShell", "hooks": [{"type": "command", "command": "python3 .claude/hooks/format-powershell-description.py"}]},
            {"matcher": "PowerShell", "hooks": [{"type": "command", "command": "bash .claude/hooks/require-powershell-description.sh"}]}
        ])' "$settings_file" 2>/dev/null)
        if [ -n "$merged_ps" ]; then
            echo "$merged_ps" > "$settings_file"
            write_item "[OK] $scope settings.json updated with PowerShell description hooks" "$GREEN"
        else
            write_item "Warning: Could not merge PowerShell description hooks into settings.json" "$YELLOW"
            write_item "  You may need to manually add the PowerShell PreToolUse hooks" "$YELLOW"
        fi
    fi

    convert_claude_hook_commands_for_posix "$repo_root" "$settings_file" "$scope"
}

install_core_settings() {
    local repo_root="$1"
    local target_claude_dir="$2"
    local scope="$3"

    local settings_file="$target_claude_dir/settings.json"
    local template_file="$repo_root/catalog/hooks/settings.json"

    if [ ! -f "$settings_file" ]; then
        write_item "Skip: settings.json not found, will be created by hook installer" "$GRAY"
        return
    fi

    if ! command -v jq >/dev/null 2>&1; then
        write_item "Warning: jq not found, cannot set core settings (effortLevel, model, env)" "$YELLOW" >&2
        write_item "  Manually copy effortLevel/model/env from $template_file to $settings_file" "$YELLOW" >&2
        return
    fi

    # Core defaults seeded from the template: effortLevel + model, plus the
    # env.CLAUDE_CODE_EFFORT_LEVEL override. The env var is the highest-precedence
    # effort lever per the Claude Code docs, so it forces the effort past the VS
    # Code effort toggle (which otherwise resets to the model default each session).
    # Seed-if-absent: a reinstall must not replace a value the user already chose.
    if jq -e '
        has("model")
        and (
            has("effortLevel")
            or (if ((.env | type) == "object") then
                (.env | has("CLAUDE_CODE_EFFORT_LEVEL"))
              else false end)
        )
    ' "$settings_file" >/dev/null 2>&1; then
        write_item "[OK] Core settings already present or user-set; existing values preserved in settings.json" "$GREEN"
        return
    fi

    local env_seed_blocked=0
    if jq -e '(has("effortLevel") | not) and has("env") and ((.env | type) != "object")' "$settings_file" >/dev/null 2>&1; then
        env_seed_blocked=1
        write_item "Warning: existing env is not an object; preserving it and skipping env.CLAUDE_CODE_EFFORT_LEVEL" "$YELLOW" >&2
    fi

    # Treat the scalar and higher-precedence env lever as one user-owned pair:
    # when either exists, preserve the pair exactly. Only a config with neither
    # effort lever and an absent or object-shaped env receives both defaults,
    # avoiding a new env pin on upgrade.
    local merged
    merged=$(jq -s '
        .[0] as $e | .[1] as $t |
        ($e | has("effortLevel")) as $has_scalar_effort |
        (if (($e.env | type) == "object") then
            ($e.env | has("CLAUDE_CODE_EFFORT_LEVEL"))
          else false end) as $has_env_effort |
        ($has_scalar_effort or $has_env_effort) as $has_any_effort |
        $e
        | if $has_any_effort then . else .effortLevel = $t.effortLevel end
        | if has("model") then . else .model = $t.model end
        | if $has_any_effort then .
          elif has("env") then
            if ((.env | type) == "object") then
                .env.CLAUDE_CODE_EFFORT_LEVEL = $t.env.CLAUDE_CODE_EFFORT_LEVEL
            else . end
          else .env = {CLAUDE_CODE_EFFORT_LEVEL: $t.env.CLAUDE_CODE_EFFORT_LEVEL} end
    ' "$settings_file" "$template_file" 2>/dev/null)

    if [ -n "$merged" ]; then
        if printf '%s\n' "$merged" | jq -e --slurpfile existing "$settings_file" '. == $existing[0]' >/dev/null 2>&1; then
            if [ "$env_seed_blocked" -eq 1 ]; then
                write_item "[OK] Core settings unchanged; existing non-object env preserved" "$GREEN"
            else
                write_item "[OK] Core settings already present in settings.json" "$GREEN"
            fi
            return
        fi
        echo "$merged" > "$settings_file"
        write_item "[OK] $scope settings.json seeded absent core settings; existing values preserved" "$GREEN"
    else
        write_item "Warning: Could not merge core settings into settings.json" "$YELLOW" >&2
    fi
}

# --- Permission Installation ---

# Ensure the OpenAI Codex CLI is present before writing its config. Nexus-Hub
# configures Codex permissions on every install; when the CLI is absent the
# config is never validated until the user installs Codex later, so install it
# now (via npm) when missing. Non-fatal: a failed or skipped install only prints
# a hint and never aborts the installer.
ensure_codex_cli() {
    if command -v codex >/dev/null 2>&1; then
        write_item "[OK] Codex CLI detected" "$GREEN"
        return 0
    fi
    if command -v npm >/dev/null 2>&1; then
        write_item "Codex CLI not found; installing (npm install -g @openai/codex)..." "$GRAY"
        if npm install -g @openai/codex >/dev/null 2>&1 && command -v codex >/dev/null 2>&1; then
            write_item "[OK] Codex CLI installed" "$GREEN"
        else
            write_item "Warning: could not auto-install Codex CLI. Install manually: npm install -g @openai/codex" "$YELLOW"
        fi
    else
        write_item "Codex CLI not found and npm is unavailable. Install Node.js, then run: npm install -g @openai/codex" "$YELLOW"
    fi
}

# v3.15.6 / AC5 -- opt-in hardened deny/ask overlay.
#
# Union-merges the `deny` and `ask` arrays from claude-permissions-strict.json
# into settings.json. Three deliberate properties:
#   * ADDITIVE: a user's existing deny/ask entries are never removed.
#   * NO defaultMode: that key's documented value set is unverified in this repo
#     (see the v3.16.0 autonomy plan, which confirms it as scheduled work), and
#     "default" is already Claude Code's behavior, so writing it would be a
#     schema bet on a user's config file with no benefit.
#   * SEPARATE from install_permissions(): that function has early `return`s in
#     its allow-merge path (jq missing, nothing new to add, merge failed), so
#     calling this from inside it would silently skip the overlay in the common
#     "allow list already up to date" case. It is invoked from the call site.
merge_strict_permissions() {
    local settings_file="$1"
    local overlay_file="$2"
    local scope="$3"

    if [ ! -f "$overlay_file" ]; then
        write_item "Skip: strict permissions overlay not found" "$GRAY"
        return
    fi

    if ! command -v jq >/dev/null 2>&1; then
        write_item "Warning: jq not found, cannot merge the strict permission overlay" "$YELLOW"
        write_item "  Copy the deny/ask entries manually from: $overlay_file" "$YELLOW"
        return
    fi

    if [ ! -f "$settings_file" ]; then
        write_item "Skip: settings.json not present, cannot apply the strict overlay" "$GRAY"
        return
    fi

    local added
    added=$(jq -sr '
        .[0] as $s | .[1] as $o |
        (($s.permissions.deny // []) as $sd | ($o.permissions.deny // []) as $od |
          (($sd + $od) | unique | length) - ($sd | length))
        +
        (($s.permissions.ask // []) as $sa | ($o.permissions.ask // []) as $oa |
          (($sa + $oa) | unique | length) - ($sa | length))
    ' "$settings_file" "$overlay_file" 2>/dev/null)

    if [ "${added:-0}" = "0" ]; then
        write_item "[OK] Strict deny/ask entries already up to date (0 new)" "$GREEN"
        return
    fi

    local backup_path
    backup_path="$settings_file.bak.$(date +%Y%m%d-%H%M%S)"
    cp "$settings_file" "$backup_path"
    write_item "  Backup created: $backup_path" "$GRAY"

    local merged
    merged=$(jq -s '
        .[0] as $s | .[1] as $o |
        $s
        | .permissions.deny = ((($s.permissions.deny // []) + ($o.permissions.deny // [])) | unique)
        | .permissions.ask  = ((($s.permissions.ask  // []) + ($o.permissions.ask  // [])) | unique)
    ' "$settings_file" "$overlay_file" 2>/dev/null)

    if [ -n "$merged" ]; then
        echo "$merged" > "$settings_file"
        write_item "[OK] $scope STRICT permission overlay applied (${added} new deny/ask entries)" "$GREEN"
        write_item "  Denied: version-control hook/config writes, interpreter paths, git execution-indirection commands" "$GRAY"
        write_item "  Ask: harness settings and hooks, editor task/launch config, editor rules" "$GRAY"
    else
        write_item "Warning: Could not merge the strict permission overlay into settings.json" "$YELLOW"
    fi
}

# v3.17.0 Phase 1.2 -- the single permission-merge path for BOTH installers.
#
# Delegates to scripts/merge_permissions.py, which installer.ps1 calls identically.
# One implementation, two thin callers.
#
# DEVIATION from the v3.17.0 plan, sub-task 1.2: the plan asked to keep `jq` as a
# fast path when present and add a Python fallback only for hosts without it. That
# was correct for an add-only merge, but amendment A3 added removal propagation,
# which lives in the Python helper. Retaining a `jq` path would mean a host WITH jq
# silently keeps retired mutation-capable entries while a host WITHOUT jq has them
# removed -- reintroducing, inside a single installer, exactly the divergence this
# phase exists to eliminate. Python is already a documented dependency and both
# installers already check for it, so the `jq` path is dropped rather than forked.
#
# Resolve the helper script and a Python interpreter into PERM_HELPER_SCRIPT and
# PERM_HELPER_PY. Two globals rather than one word-split string on purpose: an
# unquoted expansion here would trip shellcheck at the severity `make lint` uses.
PERM_HELPER_PY=""
PERM_HELPER_SCRIPT=""
resolve_permissions_helper() {
    local repo_root="$1"
    PERM_HELPER_SCRIPT="$repo_root/scripts/merge_permissions.py"
    if [ ! -f "$PERM_HELPER_SCRIPT" ]; then
        write_item "Warning: merge helper not found at $PERM_HELPER_SCRIPT" "$YELLOW"
        return 1
    fi
    if ! PERM_HELPER_PY=$(resolve_python_executable); then
        write_item "Warning: Python not found, cannot sync permissions automatically" "$YELLOW"
        return 1
    fi
    return 0
}

# Surface the helper's stdout protocol (added: / removed: / set:) to the user. Each
# retired entry is reported rather than removed silently, because the target file is
# one the user may have hand-edited.
report_permissions_helper_output() {
    local output="$1"
    [ -n "$output" ] || return 0
    while IFS= read -r line; do
        case "$line" in
            removed:*|set:*) write_item "  $line" "$GRAY" ;;
        esac
    done <<< "$output"
}

# Returns 0 on success, 1 when the merge failed.
merge_permissions_via_helper() {
    local repo_root="$1"
    local template_file="$2"
    local settings_file="$3"
    local key="$4"          # permissions.allow | tools.allowed | allowedDomains
    local platform="$5"     # manifest key: CLAUDE, GEMINI, ...

    if ! resolve_permissions_helper "$repo_root"; then
        write_item "  Copy permissions manually from: $template_file" "$YELLOW"
        return 1
    fi

    local manifest="$HOME/.nexus-hub/permissions-manifest.json"
    local output
    if ! output=$("$PERM_HELPER_PY" "$PERM_HELPER_SCRIPT" \
            --template "$template_file" \
            --settings "$settings_file" \
            --key "$key" \
            --manifest "$manifest" \
            --platform "$platform"); then
        write_item "Warning: could not merge permissions into $settings_file" "$YELLOW"
        return 1
    fi

    report_permissions_helper_output "$output"
    return 0
}

# Set one LITERAL boolean key to true through the same helper. Copilot's permission
# surface is a single VS Code settings key rather than an array, and this branch
# previously used `jq` and skipped without it -- which made the Git-Bash path below
# unreachable in practice, since Git-Bash ships no `jq`.
set_permission_flag_via_helper() {
    local repo_root="$1"
    local settings_file="$2"
    local literal_key="$3"

    if ! resolve_permissions_helper "$repo_root"; then
        write_item "  Set \"$literal_key\": true manually in: $settings_file" "$YELLOW"
        return 1
    fi

    local output
    if ! output=$("$PERM_HELPER_PY" "$PERM_HELPER_SCRIPT" \
            --settings "$settings_file" \
            --set-true "$literal_key"); then
        write_item "Warning: could not update $settings_file" "$YELLOW"
        return 1
    fi

    report_permissions_helper_output "$output"
    return 0
}

# v3.17.0 Phase 1.2: the `scope` parameter is now load-bearing. It was documented as
# "Global" or "Workspace" since v0.9.x, but every call site passed "Global" and
# install_workspace never called this function at all, so a --workspace install
# received no permission baseline on any operating system.
#
# Only CLAUDE is wired at workspace scope. The other three skip WITH A NOTE rather
# than guessing:
#   * GEMINI / CODEX -- no project-scoped permission path is documented well enough
#     to write. A guessed path is worse than none: it looks configured and is not.
#   * COPILOT -- its surface is .vscode/settings.json, which is COMMIT-VISIBLE. The
#     plan forbids pushing a permission grant into a user's repository history
#     without an explicit maintainer decision (same reasoning that made the v3.11.0
#     Copilot .github/skills/ surface opt-in).
install_permissions() {
    local repo_root="$1"
    local platform="$2"    # "CLAUDE", "GEMINI", "CODEX", "COPILOT"
    local scope="$3"       # "Global" or "Workspace"
    local target_path="${4:-}"  # project root; required when scope is "Workspace"
    local user_home="$HOME"
    local perm_dir="$repo_root/configs/permissions"

    if [ "$scope" = "Workspace" ]; then
        if [ -z "$target_path" ] || [ ! -d "$target_path" ]; then
            write_item "Skip: workspace permissions need a valid target path" "$GRAY"
            return
        fi
        case "$platform" in
            GEMINI)
                write_item "Skip: Gemini has no documented project-scoped permission path (global scope only)" "$GRAY"
                return
                ;;
            CODEX)
                write_item "Skip: Codex has no documented project-scoped permission path (global scope only)" "$GRAY"
                return
                ;;
            COPILOT)
                write_item "Skip: Copilot's only permission surface is .vscode/settings.json, which is commit-visible" "$GRAY"
                write_item "  A workspace grant there would enter your repository history; use a global install instead." "$GRAY"
                return
                ;;
        esac
    fi

    case "$platform" in
        CLAUDE)
            local config_dir="$user_home/.claude"
            local settings_file="$config_dir/settings.json"
            local template_file="$perm_dir/claude-permissions.json"

            if [ "$scope" = "Workspace" ]; then
                # settings.local.json, NEVER settings.json: the latter is
                # commit-visible and would push a permission grant into the
                # user's repository history. Confirmed target (maintainer
                # decision, v3.17.0 Phase 1.2).
                config_dir="$target_path/.claude"
                settings_file="$config_dir/settings.local.json"
            fi

            if [ ! -f "$template_file" ]; then
                write_item "Skip: Claude permissions template not found" "$GRAY"
                return
            fi

            # v3.17.0: one path for create AND merge. The helper creates the file
            # when absent, unions new entries, retires entries a prior Nexus-Hub
            # version shipped and this one no longer does (never a user's own
            # entry), backs up before any change, and strips the template's
            # `_`-prefixed documentation keys so they never reach a live config.
            # The old creation path used `cp` when jq was missing, which DID copy
            # them.
            mkdir -p "$config_dir"
            if merge_permissions_via_helper "$repo_root" "$template_file" \
                    "$settings_file" "permissions.allow" "CLAUDE"; then
                write_item "[OK] $scope auto-approve permissions synced in settings.json" "$GREEN"
            else
                return
            fi

            write_item "  Auto-approved: file reads, search (Glob/Grep), web search, git read-only commands" "$GRAY"
            write_item "  WebFetch: scoped to trusted domains (see $settings_file to customize)" "$GRAY"
            write_item "  NOT auto-approved: file writes, destructive commands, git mutations, package installs" "$GRAY"
            write_item "  Config: $settings_file" "$GRAY"

            # A workspace grant is only private if the file is actually ignored.
            # settings.local.json is Claude Code's local-only convention, but nothing
            # guarantees THIS repository ignores it, so check rather than assume.
            if [ "$scope" = "Workspace" ] && command -v git >/dev/null 2>&1; then
                if ! git -C "$target_path" check-ignore -q "$settings_file" 2>/dev/null; then
                    write_item "  Note: $settings_file is NOT git-ignored in this project." "$DARK_YELLOW"
                    write_item "  Add '.claude/settings.local.json' to .gitignore so the grant stays local." "$DARK_YELLOW"
                fi
            fi
            ;;

        GEMINI)
            local config_dir="$user_home/.gemini"
            local settings_file="$config_dir/settings.json"
            local template_file="$perm_dir/gemini-permissions.json"

            if [ ! -f "$template_file" ]; then
                write_item "Skip: Gemini permissions template not found" "$GRAY"
                return
            fi

            # v3.17.0 amendment A3, bug 1: this branch previously gated on a fixed
            # sentinel (`grep -q 'run_shell_command(docker ps)'`) to decide whether
            # permissions were already configured. That is the identical stale-marker
            # defect the CLAUDE branch was fixed for: because the sentinel entry is
            # present in every existing user's settings.json, the branch returned
            # early forever and those users never received newly-shipped entries --
            # including, critically, the v3.17.0 Phase 1.1 hardening. The sentinel is
            # replaced by the same count-and-sync path the CLAUDE branch uses, which
            # is idempotent by construction and needs no marker.
            mkdir -p "$config_dir"
            local gemini_ok=0
            merge_permissions_via_helper "$repo_root" "$template_file" \
                "$settings_file" "tools.allowed" "GEMINI" || gemini_ok=1
            merge_permissions_via_helper "$repo_root" "$template_file" \
                "$settings_file" "allowedDomains" "GEMINI_DOMAINS" || gemini_ok=1
            if [ "$gemini_ok" -eq 0 ]; then
                write_item "[OK] $scope auto-approve permissions synced in settings.json" "$GREEN"
            else
                return
            fi

            write_item "  Auto-approved: file reads, search, web search, git read-only shell commands" "$GRAY"
            write_item "  Domains: scoped to trusted list (see $settings_file to customize)" "$GRAY"
            write_item "  Limitation: piped commands bypass allowlists (upstream issue)" "$GRAY"
            write_item "  Config: $settings_file" "$GRAY"
            ;;

        CODEX)
            ensure_codex_cli
            local config_dir="$user_home/.codex"
            local config_file="$config_dir/config.toml"
            local template_file="$perm_dir/codex-permissions.toml"

            if [ ! -f "$template_file" ]; then
                write_item "Skip: Codex permissions template not found" "$GRAY"
                return
            fi

            if [ -f "$config_file" ]; then
                # Repair an already-broken config: if it defines [permissions.*]
                # but lacks default_permissions, the newer Codex CLI refuses to
                # load it. Insert the key before the FIRST table header of any
                # kind (the only valid spot for a root-level key in TOML) rather
                # than appending it after a table, where it would silently bind
                # to that table and stay broken.
                if grep -q '^\[permissions' "$config_file" 2>/dev/null && ! grep -q 'default_permissions' "$config_file" 2>/dev/null; then
                    cp "$config_file" "$config_file.bak.$(date +%Y%m%d-%H%M%S)"
                    if awk 'BEGIN{ins=0} /^\[/ && ins==0 {print "default_permissions = \"default\""; print ""; ins=1} {print}' "$config_file" > "$config_file.nexus.tmp"; then
                        mv "$config_file.nexus.tmp" "$config_file"
                        write_item "[OK] Repaired Codex config.toml: inserted missing default_permissions" "$GREEN"
                    else
                        rm -f "$config_file.nexus.tmp"
                        write_item "Warning: could not repair Codex config.toml; review it manually" "$YELLOW"
                    fi
                fi

                # Already fully configured (managed block complete, incl. default_permissions)?
                if grep -q 'permissions.default.network' "$config_file" 2>/dev/null && grep -q 'allowed_domains' "$config_file" 2>/dev/null && grep -q 'default_permissions' "$config_file" 2>/dev/null; then
                    write_item "[OK] Auto-approve permissions already configured in config.toml" "$GREEN"
                    return
                fi

                local backup_path
                backup_path="$config_file.bak.$(date +%Y%m%d-%H%M%S)"
                cp "$config_file" "$backup_path"
                write_item "  Backup created: $backup_path" "$GRAY"

                # Append permission sections if not present
                printf '\n\n# --- Nexus-Hub auto-approve permissions ---\n' >> "$config_file"
                if ! grep -q 'approval_policy' "$config_file" 2>/dev/null; then
                    printf 'approval_policy = "on-request"\n\n' >> "$config_file"
                fi
                # default_permissions selects the profile defined below; the newer
                # Codex CLI rejects a config with [permissions.*] but no default_permissions.
                if ! grep -q 'default_permissions' "$config_file" 2>/dev/null; then
                    printf 'default_permissions = "default"\n\n' >> "$config_file"
                fi
                if ! grep -q '\[permissions.default.filesystem\]' "$config_file" 2>/dev/null; then
                    grep -A2 '\[permissions.default.filesystem\]' "$template_file" >> "$config_file"
                    printf '\n' >> "$config_file"
                fi
                if ! grep -q '\[permissions.default.network\]' "$config_file" 2>/dev/null; then
                    sed -n '/\[permissions.default.network\]/,$p' "$template_file" >> "$config_file"
                fi
                write_item "[OK] $scope config.toml updated with auto-approve permissions" "$GREEN"
            else
                mkdir -p "$config_dir"
                cp "$template_file" "$config_file"
                write_item "[OK] $scope config.toml created with auto-approve permissions" "$GREEN"
            fi

            write_item "  Auto-approved: filesystem read access to project roots, network access to trusted domains" "$GRAY"
            write_item "  NOT auto-approved: file writes, arbitrary network access" "$GRAY"
            write_item "  Note: Codex does not support per-command Bash allowlisting" "$GRAY"
            write_item "  Config: $config_file" "$GRAY"
            ;;

        COPILOT)
            local template_file="$perm_dir/copilot-permissions.json"

            if [ ! -f "$template_file" ]; then
                write_item "Skip: Copilot permissions template not found" "$GRAY"
                return
            fi

            # Locate VS Code settings.json
            local vscode_settings=""
            case "$(uname -s)" in
                Darwin*) vscode_settings="$user_home/Library/Application Support/Code/User/settings.json" ;;
                Linux*)  vscode_settings="$user_home/.config/Code/User/settings.json" ;;
                # v3.17.0 Phase 1.2: Windows Git-Bash previously fell through to the
                # skip below, so a bash invocation on Windows configured Copilot not
                # at all. Mirrors installer.ps1 exactly:
                #   Join-Path $env:APPDATA "Code\User\settings.json"
                MINGW*|MSYS*|CYGWIN*)
                    local appdata="${APPDATA:-}"
                    if [ -z "$appdata" ]; then
                        write_item "Skip: APPDATA is not set, cannot locate VS Code settings from Git-Bash" "$GRAY"
                        return
                    fi
                    # APPDATA arrives as a Windows path (C:\Users\...\Roaming); bash
                    # file tests need a POSIX one.
                    if command -v cygpath >/dev/null 2>&1; then
                        appdata=$(cygpath -u "$appdata")
                    else
                        appdata=$(printf '%s' "$appdata" | tr '\\' '/')
                    fi
                    vscode_settings="$appdata/Code/User/settings.json"
                    ;;
                *)       write_item "Skip: Copilot permission config not supported on this OS via bash" "$GRAY"; return ;;
            esac

            if [ ! -f "$vscode_settings" ]; then
                write_item "Skip: VS Code settings.json not found at $vscode_settings" "$GRAY"
                write_item "  Copilot permissions require VS Code. Install VS Code and retry." "$GRAY"
                return
            fi

            if grep -q 'useInstructionFiles.*true' "$vscode_settings" 2>/dev/null; then
                write_item "[OK] Copilot useInstructionFiles already enabled in VS Code settings" "$GREEN"
                return
            fi

            # The helper takes its own timestamped backup and writes atomically, so
            # this branch no longer backs up or merges by hand. It also drops the `jq`
            # requirement, which is what made the Git-Bash arm above reachable: Git-Bash
            # ships no `jq`, so mapping the path without this change would have moved
            # the silent skip rather than closing it.
            if set_permission_flag_via_helper "$repo_root" "$vscode_settings" \
                    "github.copilot.chat.codeGeneration.useInstructionFiles"; then
                write_item "[OK] $scope VS Code settings updated with Copilot instruction file support" "$GREEN"
            else
                return
            fi

            write_item "  Limitation: Copilot lacks per-command/per-domain auto-approve" "$GRAY"
            write_item "  Only useInstructionFiles is enabled (behavioral guardrails via .github/copilot-instructions.md)" "$GRAY"
            write_item "  Blanket auto-approve is NOT set (cannot distinguish reads from writes)" "$GRAY"
            write_item "  Config: $vscode_settings" "$GRAY"
            ;;
    esac
}

# --- Git Commit-Msg Hook ---

install_git_commit_msg_hook() {
    local repo_root="$1"
    local user_home="$HOME"
    local hook_src="$repo_root/catalog/hooks/commit-msg"
    local template_hooks_dir="$user_home/.git-templates/hooks"

    if [ ! -f "$hook_src" ]; then
        write_item "Skip: catalog/hooks/commit-msg not found" "$GRAY"
        return
    fi

    mkdir -p "$template_hooks_dir"
    cp "$hook_src" "$template_hooks_dir/commit-msg"
    chmod +x "$template_hooks_dir/commit-msg"
    write_item "[OK] Git commit-msg hook installed at: $template_hooks_dir/commit-msg" "$GREEN"

    # Register the template directory so all future repos inherit the hook
    git config --global init.templateDir "$HOME/.git-templates" 2>/dev/null || true
    write_item "[OK] git config --global init.templateDir set to $HOME/.git-templates" "$GREEN"
    write_item "  Note: run 'git init' in existing repos to apply the hook there too" "$GRAY"
}

# --- Install Functions ---

install_global() {
    local repo_root="$1"
    local user_home="$HOME"

    # OVERWRITE_ALL is resolved once at startup (refresh vs interactive-conflict);
    # the install functions no longer toggle it.
    # Each main section is a "> UPPERCASE" banner (write_section_banner prepends
    # its own single blank); there is no separate "Global install" super-header -
    # the scope is already stated in the welcome + farewell lines.
    write_section_banner "SKILLS & COMMANDS"

    echo -e "${GRAY}Checking User Profile ($user_home)...${RESET}"
    reset_undetected_platforms

    # Instruction-template placeholders, set unconditionally so every selected
    # provider renders a complete instruction body even when --platforms excludes
    # Claude (these globals are threaded to every invoke_registry_platform call).
    PROJECT_NAME="Global"
    OS_CONTEXT=""
    case "$(uname -s)" in
        Darwin*) OS_CONTEXT="I am a macOS user." ;;
        Linux*)  OS_CONTEXT="I am a Linux user." ;;
        *)       OS_CONTEXT="I am a Windows user." ;;
    esac
    PRIMARY_LANGUAGE=""
    PACKAGE_MANAGER=""
    BUILD_TOOL=""
    TEST_FRAMEWORK=""
    LINT_TOOL=""
    BUILD_CMD="# specify build command"
    TEST_CMD="# specify test command"
    LINT_CMD="# specify lint command"
    NON_OBVIOUS_TOOLING="- (configure per project with /setup project)"

    # Per-provider install blocks. Each is gated on the --platforms subset via
    # should_install <integration-key> (no filter => all run). The output groups
    # by organization (Anthropic / OpenAI / Google / Microsoft / Anysphere /
    # OpenCode / Nexus); each provider has a single colored write_header line and
    # its platforms listed underneath.

    # --- Anthropic -- Claude Code ---------------------------------------
    if should_install claude; then
    write_header "ANTHROPIC"
    local global_claude="$user_home/.claude"
    mkdir -p "$global_claude"

    # Claude is the one bespoke (non-registry) install; each helper prints its
    # own progress to stdout. Run every step quietly (>/dev/null suppresses the
    # "Merging..." lines and per-step notices; errors still go to stderr) and
    # render ONE unified checklist afterward so Claude reads identically to the
    # registry platforms. DF-001: the registry runner renders CLAUDE.md;
    # safe_folder_copy does the catalog mirror.
    # v3.16.1: catalog_src returns the filtered stage when a selection is active
    # and the real catalog otherwise, so the no-selector path is unchanged.
    flatten_skills_into "$(catalog_src "$repo_root" skills)"   "$global_claude/skills"   >/dev/null
    safe_folder_copy "$(catalog_src "$repo_root" commands)" "$global_claude/commands" >/dev/null
    safe_folder_copy "$(catalog_src "$repo_root" agents)"   "$global_claude/agents"   >/dev/null
    safe_folder_copy "$repo_root/catalog/rules"    "$global_claude/rules"    >/dev/null
    # Org rules are seeded by the registry after refresh-mode catalog pruning.
    invoke_registry_platform "$repo_root" "global" "" "claude" "CLAUDE.md (instruction file)" "" "true" >/dev/null

    mkdir -p "$global_claude/mcp-configs"
    safe_copy "$repo_root/catalog/mcp-configs/mcp-servers.json" "$global_claude/mcp-configs/mcp-servers.json" false >/dev/null

    install_git_guardrails    "$repo_root" "$global_claude" "Global" >/dev/null
    install_usage_display     "$repo_root" "$global_claude" "Global" >/dev/null
    install_require_description "$repo_root" "$global_claude" "Global" >/dev/null
    install_core_settings     "$repo_root" "$global_claude" "Global" >/dev/null

    # Unified checklist, built from the resulting on-disk state.
    write_item "Claude Code" "$GRAY"
    [ -f "$global_claude/CLAUDE.md" ] && write_checklist_row "Core Files" "ok" "$global_claude/CLAUDE.md"
    [ -d "$global_claude/skills" ]    && write_checklist_row "Skills" "ok" "$global_claude/skills"
    [ -d "$global_claude/commands" ]  && write_checklist_row "Commands" "ok" "$global_claude/commands"
    [ -d "$global_claude/agents" ]    && write_checklist_row "Agents" "ok" "$global_claude/agents"
    [ -d "$global_claude/rules" ]     && write_checklist_row "Rules" "ok" "$global_claude/rules"
    if [ -f "$global_claude/settings.json" ]; then
        write_checklist_row "Hooks" "ok" "git-guardrails, usage, require-description, compress-output"
        write_checklist_row "Core Settings" "ok" "settings.json retained; existing values preserved (see warnings above)"
    fi
    fi

    # --- OpenAI -- Codex ------------------------------------------------
    if should_install codex; then
    local global_codex_dir="$user_home/.codex"
    mkdir -p "$global_codex_dir"
    # The codex integration flattens skills to ~/.codex/skills AND ~/.agents/skills,
    # emits every command as a skill plus a legacy prompt, and renders
    # ~/.codex/AGENTS.md. Since v3.15.8 it also writes ~/.codex/agents/*.toml
    # (custom agents) and merges ~/.codex/hooks.json + ~/.codex/hooks/, enabling
    # [features] hooks in ~/.codex/config.toml (see
    # docs/policy/platform-read-contracts.md). Both surfaces ship through the
    # registry, so this bash path and installer.ps1 stay in lockstep by
    # construction rather than by duplicated copy blocks.
    invoke_registry_platform "$repo_root" "global" "" "codex" "Codex" "" "" "OPENAI"
    fi

    # --- Google -- Gemini / Antigravity 2.0 / Gemini CLI --------------
    # The GOOGLE header is shared by up to three platforms, so it prints eagerly
    # only when a platform that always renders (Gemini IDE / Antigravity 2.0) is
    # selected. Gemini CLI (non-enterprise) is a deliberate skip -> the group.
    if should_install gemini || should_install antigravity2; then
    write_header "GOOGLE"
    fi
    if should_install gemini; then
    local global_gemini_dir="$user_home/.gemini"
    mkdir -p "$global_gemini_dir"
    # Renders GEMINI.md and mirrors the catalog to ~/.gemini/{skills,workflows,agents,rules}.
    invoke_registry_platform "$repo_root" "global" "" "gemini" "Gemini IDE" "" ""
    fi
    if should_install antigravity2; then
    invoke_registry_platform "$repo_root" "global" "" "antigravity2" "Antigravity 2.0 + CLI" "" ""
    fi
    if should_install gemini-cli; then
    if [ "${ENTERPRISE:-0}" = "1" ]; then
        # GEMINI.md + skills + TOML commands + agents + rules + native hooks
        # (v3.15.8 Phase 6: a hooks key merged into ~/.gemini/settings.json,
        # with the .sh or .ps1 sibling chosen from the installing host because
        # Gemini CLI has no commandWindows equivalent).
        invoke_registry_platform "$repo_root" "global" "" "gemini-cli" "Gemini CLI" "" "" "GOOGLE"
    else
        add_undetected_platform "Gemini CLI" "enterprise-only; re-run with --enterprise"
    fi
    fi

    # --- Microsoft -- GitHub Copilot -----------------------------------
    # VS Code user-profile prompt files (slash commands) + custom agents at
    # ~/.copilot/agents (v3.15.8 Phase 8, verbatim catalog Markdown). Hooks are
    # NOT written: Copilot's default hook locations include ~/.claude/settings.json,
    # which the Claude block above already populates, so they are inherited.
    if should_install copilot; then
    invoke_registry_platform "$repo_root" "global" "" "copilot" "GitHub Copilot" "" "" "MICROSOFT"
    fi

    # --- Anysphere -- Cursor -------------------------------------------
    if should_install cursor; then
    invoke_registry_platform "$repo_root" "global" "" "cursor" "Cursor" "" "" "ANYSPHERE"
    fi

    # --- OpenCode ------------------------------------------------------
    if should_install opencode; then
    invoke_registry_platform "$repo_root" "global" "" "opencode" "OpenCode" "" "" "OPENCODE"
    fi

    # --- Aider ---------------------------------------------------------
    if should_install aider; then
    invoke_registry_platform "$repo_root" "global" "" "aider" "Aider" "" "" "AIDER"
    fi

    # --- Windsurf ------------------------------------------------------
    if should_install windsurf; then
    invoke_registry_platform "$repo_root" "global" "" "windsurf" "Windsurf" "" "" "WINDSURF"
    fi

    # --- Kimi ----------------------------------------------------------
    # AGENTS.md + skills + custom agents (verbatim catalog Markdown) + native
    # hooks as a marker-managed [[hooks]] block in ~/.kimi-code/config.toml
    # (v3.15.8 Phase 7). Detection-gated on ~/.kimi-code.
    if should_install kimi; then
    invoke_registry_platform "$repo_root" "global" "" "kimi" "Kimi Code CLI" "" "" "KIMI"
    fi

    # --- Qwen ----------------------------------------------------------
    # QWEN.md + skills + Markdown commands + agents + native hooks (v3.15.8
    # Phase 6: a hooks key merged into ~/.qwen/settings.json, host-selected
    # command plus Qwen's own shell field). Detection-gated on ~/.qwen.
    if should_install qwen; then
    invoke_registry_platform "$repo_root" "global" "" "qwen" "Qwen Code" "" "" "QWEN"
    fi

    # --- OpenClaw ------------------------------------------------------
    if should_install openclaw; then
    invoke_registry_platform "$repo_root" "global" "" "openclaw" "OpenClaw" "" "" "OPENCLAW"
    fi

    # --- Nexus -- Nexus-AI (Local Desktop Studio) ----------------------
    if should_install nexus-ai; then
    invoke_registry_platform "$repo_root" "global" "" "nexus-ai" "Nexus-AI" "" "" "NEXUS"
    fi

    # Platforms whose tool was not detected on this machine (or a scope with no
    # surface, e.g. Aider at global) were collected above; print them once here.
    write_undetected_group

    # --- Auto-Approve Permissions sub-section --------------------------
    # Permissions only apply to the legacy 4 (CLAUDE / GEMINI / CODEX /
    # COPILOT). Mirrored to provider headers for visual consistency. Each is
    # gated on the same --platforms subset as its provider block above.
    write_section_banner "AUTO-APPROVE PERMISSIONS"

    if should_install claude; then
    write_header "ANTHROPIC"
    install_permissions "$repo_root" "CLAUDE" "Global"
    # v3.15.6 / AC5: opt-in only. Without --strict-permissions this is a no-op and
    # the install stays exactly as it was (allow-only, no prompts). Invoked here
    # rather than inside install_permissions because that function returns early
    # in its allow-merge path; see the note on merge_strict_permissions.
    if [ "${STRICT_PERMISSIONS:-0}" = "1" ]; then
        merge_strict_permissions \
            "$HOME/.claude/settings.json" \
            "$repo_root/configs/permissions/claude-permissions-strict.json" \
            "Global"
    fi
    fi

    if should_install codex; then
    write_header "OPENAI"
    install_permissions "$repo_root" "CODEX" "Global"
    fi

    if should_install gemini; then
    write_header "GOOGLE"
    install_permissions "$repo_root" "GEMINI" "Global"
    fi

    if should_install copilot; then
    write_header "MICROSOFT"
    install_permissions "$repo_root" "COPILOT" "Global"
    fi

    # --- Usage Monitor Extensions section (VS Code + Cursor hosts) ---
    write_section_banner "USAGE MONITOR EXTENSIONS"
    install_vscode_extensions "$repo_root"

    # --- Cross-Platform Tools: capabilities that apply to every platform, grouped
    # under one section. Skill discovery + the git hook run here; install_templates
    # (next in the main flow) adds its own "- Report templates" subsection under
    # this same header.
    write_section_banner "CROSS-PLATFORM TOOLS"

    write_subsection_banner "Skill discovery"
    install_skill_discovery "$repo_root"

    write_subsection_banner "Git commit-msg hook"
    echo ""
    install_git_commit_msg_hook "$repo_root"
}

detect_languages() {
    local target_path="$1"
    local detected_langs=""

    # Simple count check
    if [ "$(find "$target_path" -maxdepth 3 -name "*.py" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="Python,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.js" -o -name "*.jsx" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="JavaScript,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="TypeScript,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.java" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="Java,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.cs" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="C#,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.go" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="Go,"; fi
    if [ "$(find "$target_path" -maxdepth 3 -name "*.cpp" -o -name "*.h" -o -name "*.hpp" 2>/dev/null | wc -l)" -gt 0 ]; then detected_langs+="C++,"; fi

    # Remove trailing comma
    echo "${detected_langs%,}"
}

detect_project_metadata() {
    local target_path="$1"
    local languages="$2"

    # Project name from directory
    PROJECT_NAME=$(basename "$target_path")

    # OS detection
    case "$(uname -s)" in
        Darwin*) OS_CONTEXT="I am a macOS user. Ensure shell commands are POSIX-compatible." ;;
        Linux*)  OS_CONTEXT="I am a Linux user. Ensure shell commands are POSIX-compatible." ;;
        *)       OS_CONTEXT="I am a Windows user. Ensure shell commands are PowerShell-compatible." ;;
    esac

    # Primary language (first detected)
    PRIMARY_LANGUAGE=$(echo "$languages" | cut -d',' -f1)

    # Package manager detection
    PACKAGE_MANAGER=""
    BUILD_TOOL=""
    TEST_FRAMEWORK=""
    LINT_TOOL=""
    BUILD_CMD=""
    TEST_CMD=""
    LINT_CMD=""
    NON_OBVIOUS_TOOLING=""

    if [ -f "$target_path/pyproject.toml" ]; then
        PACKAGE_MANAGER="uv (or pip with venv)"
        BUILD_TOOL="uv"
        TEST_FRAMEWORK="pytest"
        LINT_TOOL="ruff"
        BUILD_CMD="uv run python src/main.py"
        TEST_CMD="uv run pytest tests/"
        LINT_CMD="uv run ruff check . && uv run ruff format ."
        NON_OBVIOUS_TOOLING="- Use \`uv\` not \`pip\` for Python package management (10-100x faster)"
    elif [ -f "$target_path/requirements.txt" ]; then
        PACKAGE_MANAGER="pip with venv"
        BUILD_TOOL="pip"
        TEST_FRAMEWORK="pytest"
        LINT_TOOL="ruff"
        BUILD_CMD="python src/main.py"
        TEST_CMD="pytest tests/"
        LINT_CMD="ruff check . && ruff format ."
    fi

    if [ -f "$target_path/package.json" ]; then
        PACKAGE_MANAGER="npm"
        if [ -f "$target_path/yarn.lock" ]; then PACKAGE_MANAGER="yarn"; fi
        if [ -f "$target_path/pnpm-lock.yaml" ]; then PACKAGE_MANAGER="pnpm"; fi
        if [ -f "$target_path/bun.lockb" ]; then
            PACKAGE_MANAGER="bun"
            NON_OBVIOUS_TOOLING="- Use \`bun\` not \`npm\` for package management and script execution"
        fi
        BUILD_TOOL="$PACKAGE_MANAGER"
        TEST_FRAMEWORK="jest"
        LINT_TOOL="eslint + prettier"
        BUILD_CMD="$PACKAGE_MANAGER run build"
        TEST_CMD="$PACKAGE_MANAGER test"
        LINT_CMD="$PACKAGE_MANAGER run lint"
    fi

    if [ -f "$target_path/go.mod" ]; then
        PACKAGE_MANAGER="go mod"
        BUILD_TOOL="go"
        TEST_FRAMEWORK="go test"
        LINT_TOOL="golangci-lint"
        BUILD_CMD="go build ./..."
        TEST_CMD="go test ./..."
        LINT_CMD="golangci-lint run"
    fi

    if [ -f "$target_path/pom.xml" ]; then
        PACKAGE_MANAGER="Maven"
        BUILD_TOOL="mvn"
        TEST_FRAMEWORK="JUnit 5"
        LINT_TOOL="Checkstyle"
        BUILD_CMD="mvn compile"
        TEST_CMD="mvn test"
        LINT_CMD="mvn checkstyle:check"
    elif [ -f "$target_path/build.gradle" ] || [ -f "$target_path/build.gradle.kts" ]; then
        PACKAGE_MANAGER="Gradle"
        BUILD_TOOL="gradle"
        TEST_FRAMEWORK="JUnit 5"
        LINT_TOOL="Checkstyle"
        BUILD_CMD="./gradlew build"
        TEST_CMD="./gradlew test"
        LINT_CMD="./gradlew checkstyleMain"
    fi

    if ls "$target_path"/*.csproj >/dev/null 2>&1 || ls "$target_path"/*.sln >/dev/null 2>&1; then
        PACKAGE_MANAGER="NuGet (dotnet)"
        BUILD_TOOL="dotnet"
        TEST_FRAMEWORK="xUnit"
        LINT_TOOL="dotnet format"
        BUILD_CMD="dotnet build"
        TEST_CMD="dotnet test"
        LINT_CMD="dotnet format"
    fi

    if [ -f "$target_path/CMakeLists.txt" ]; then
        PACKAGE_MANAGER="CMake"
        BUILD_TOOL="cmake"
        TEST_FRAMEWORK="GoogleTest"
        LINT_TOOL="clang-format"
        BUILD_CMD="cmake --build build"
        TEST_CMD="ctest --test-dir build"
        LINT_CMD="clang-format -i src/*.cpp include/*.h"
    fi

    if [ -f "$target_path/Makefile" ] && [ -z "$BUILD_CMD" ]; then
        BUILD_CMD="make"
        TEST_CMD="make test"
    fi

    # Set defaults for unfilled values
    [ -z "$PACKAGE_MANAGER" ] && PACKAGE_MANAGER="(detect or specify)"
    [ -z "$BUILD_TOOL" ] && BUILD_TOOL="(detect or specify)"
    [ -z "$TEST_FRAMEWORK" ] && TEST_FRAMEWORK="(detect or specify)"
    [ -z "$LINT_TOOL" ] && LINT_TOOL="(detect or specify)"
    [ -z "$BUILD_CMD" ] && BUILD_CMD="# specify build command"
    [ -z "$TEST_CMD" ] && TEST_CMD="# specify test command"
    [ -z "$LINT_CMD" ] && LINT_CMD="# specify lint command"
    [ -z "$NON_OBVIOUS_TOOLING" ] && NON_OBVIOUS_TOOLING="- (add project-specific tooling notes here)"
}

# render_template() was removed in v2.3.0 / Phase 7 (DF-001). Instruction-file
# rendering now flows through scripts/lib/integrations/runner.py via
# invoke_registry_platform (single renderer shared with installer.ps1), which
# substitutes the same placeholder set and marker-merges the body. The detected
# globals above (PROJECT_NAME, BUILD_CMD, OS_CONTEXT, ...) are threaded to the
# runner by invoke_registry_platform.

get_language_selection() {
    local detected="$1"

    # Non-interactive (--yes / --force / piped / CI): auto-accept the detected
    # languages with no prompt; fall back to Python when nothing was detected.
    # This keeps a `--workspace <path>` install promptless (v3.7.0 / Phase 2).
    if [ "$ASSUME_YES" = true ]; then
        if [ -n "$detected" ]; then echo "$detected"; else echo "Python"; fi
        return
    fi

    if [ -n "$detected" ]; then
        echo -e "${YELLOW}Detected languages: $detected${RESET}" >&2
        local resp
        resp=$(read_prompt "Use these? [Y]es / [N]o")
        if [[ "$resp" =~ ^[Yy] ]]; then
            echo "$detected"
            return
        fi
    fi

    echo -e "  ${RESET}Select languages (comma separated):${RESET}" >&2
    echo -e "  ${RESET}1. Python  2. JS  3. TS  4. Java  5. C#  6. Go  7. C++${RESET}" >&2
    local input_str
    input_str=$(read_prompt "Selection")

    local result=""
    IFS=',' read -ra ADDR <<< "$input_str"
    for i in "${ADDR[@]}"; do
        case $(echo "$i" | xargs) in # trim whitespace
            1|Python) result+="Python," ;;
            2|JS|JavaScript) result+="JavaScript," ;;
            3|TS|TypeScript) result+="TypeScript," ;;
            4|Java) result+="Java," ;;
            5|"C#"|CS) result+="C#," ;;
            6|Go) result+="Go," ;;
            7|"C++"|CPP) result+="C++," ;;
        esac
    done

    if [ -z "$result" ]; then
        echo "Python"
    else
        echo "${result%,}"
    fi
}

install_workspace() {
    local repo_root="$1"
    local target_path="$2"  # pre-validated by main() in v0.9.7+

    # Main-section banner; no separate "Workspace install" super-header - the
    # scope is already stated in the welcome + farewell lines.
    write_section_banner "SKILLS & COMMANDS"

    if [ -z "$target_path" ] || [ ! -d "$target_path" ]; then
        write_item "Invalid target path: $target_path" "$RED"
        return 1
    fi

    # Single-pass workspace install. To install into multiple workspaces, re-run the installer.
    write_item "Target: $target_path" "$DARK_YELLOW"

        local detected
        detected=$(detect_languages "$target_path")
        local languages
        languages=$(get_language_selection "$detected")
        write_item "Selected: $languages" "$YELLOW"

        # Auto-detect project metadata for template rendering
        detect_project_metadata "$target_path" "$languages"

        # --- Install Logic (provider-grouped) ---
        # Each provider block is gated on the --platforms subset via
        # should_install <integration-key> (no filter => all run).

        # --- Anthropic -- Claude Code -------------------------------
        if should_install claude; then
        write_header "ANTHROPIC"
        write_item "Claude Code" "$GRAY"
        local claude_dir="$target_path/.claude"
        mkdir -p "$claude_dir"

        flatten_skills_into "$(catalog_src "$repo_root" skills)"   "$claude_dir/skills"   "[OK] Skills catalog installed (flattened) at: $claude_dir/skills"
        safe_folder_copy "$(catalog_src "$repo_root" commands)" "$claude_dir/commands" "[OK] Commands installed at: $claude_dir/commands"
        safe_folder_copy "$(catalog_src "$repo_root" agents)"   "$claude_dir/agents"   "[OK] Agents installed at: $claude_dir/agents"
        safe_folder_copy "$repo_root/catalog/rules"    "$claude_dir/rules"    "[OK] Rules installed at: $claude_dir/rules"
        # Org rules are seeded by the registry after refresh-mode catalog pruning.
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "claude" "CLAUDE.md (instruction file)" "$languages" "true"

        mkdir -p "$claude_dir/mcp-configs"
        safe_copy "$repo_root/catalog/mcp-configs/mcp-servers.json" "$claude_dir/mcp-configs/mcp-servers.json" false "[OK] MCP server config installed at: $claude_dir/mcp-configs"

        safe_folder_copy "$repo_root/catalog/context" "$claude_dir/context" "[OK] Context installed at: $claude_dir/context"
        safe_folder_copy "$repo_root/catalog/memory"  "$claude_dir/memory"  "[OK] Memory installed at: $claude_dir/memory"

        install_git_guardrails    "$repo_root" "$claude_dir" "Workspace"
        install_usage_display     "$repo_root" "$claude_dir" "Workspace"
        install_require_description "$repo_root" "$claude_dir" "Workspace"
        fi

        # --- OpenAI -- Codex ----------------------------------------
        if should_install codex; then
        write_header "OPENAI"
        write_item "Codex" "$GRAY"
        local codex_dir="$target_path/.codex"
        mkdir -p "$codex_dir"

        # Full registry mirror (v3.12.0): see the global Codex block. Workspace scope
        # writes .codex/{skills,prompts,agents,hooks}, .codex/hooks.json,
        # .agents/skills (flattened + command skills), and a repo-root AGENTS.md.
        # The [features] hooks switch is user-global, so a workspace install advises
        # rather than editing ~/.codex/config.toml.
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "codex" "Codex (AGENTS.md + skills + commands + agents + hooks)" "$languages" ""
        fi

        # --- Google -- Gemini / Antigravity 1.0 + 2.0 / Gemini CLI -
        if should_install gemini || should_install antigravity2 || should_install gemini-cli; then
        write_header "GOOGLE"
        if should_install gemini; then
        write_item "Gemini IDE" "$GRAY"
        local gemini_dir="$target_path/.gemini"
        mkdir -p "$gemini_dir"

        # Full registry mirror (v3.11.0): GEMINI.md + .gemini/{skills,workflows,agents,rules}.
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "gemini" "Gemini IDE (GEMINI.md + catalog mirror)" "$languages" ""
        fi

        # Antigravity 2.0 + CLI: the antigravity2 integration below owns the
        # .agents/ mirror -- it flattens skills to .agents/skills/<name>/SKILL.md,
        # mirrors commands to .agents/workflows/, and installs .agents/hooks/ +
        # .agents/hooks.json. The previous verbatim copies buried SKILL.md under a
        # category folder the IDE could not read.
        if should_install antigravity2; then
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "antigravity2" "Antigravity 2.0 + CLI"
        fi
        if should_install gemini-cli; then
        if [ "${ENTERPRISE:-0}" = "1" ]; then
            # Project .gemini/ surfaces plus native hooks merged into
            # .gemini/settings.json; commands resolve via $GEMINI_PROJECT_DIR so
            # a committed settings file carries no absolute local path.
            invoke_registry_platform "$repo_root" "workspace" "$target_path" "gemini-cli"   "Gemini CLI (enterprise)"
        else
            write_item "Gemini CLI: skipped (sunset on 2026-06-18 for free / Google AI Pro / Ultra / GitHub-installed users). Re-run with --enterprise to install (requires paid Gemini API key); Antigravity CLI above covers the same functionality." "$DARK_YELLOW"
        fi
        fi
        fi

        # --- Microsoft -- GitHub Copilot ----------------------------
        if should_install copilot; then
        write_header "MICROSOFT"
        # Render .github/copilot-instructions.md via the registry so it carries the
        # {{SKILL_INDEX}} block (from base-codex.md) and is marker-merged, preserving
        # user content above and below the managed block. Fixes C6: the prior
        # hand-built body dropped the skill index and full-overwrote the file
        # (v3.11.0 Phase 7 read-contract audit).
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "copilot" "GitHub Copilot (.github/copilot-instructions.md)" "$languages"
        fi

        # --- Anysphere -- Cursor ------------------------------------
        if should_install cursor; then
        write_header "ANYSPHERE"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "cursor" "Cursor"
        fi

        # --- OpenCode -----------------------------------------------
        if should_install opencode; then
        write_header "OPENCODE"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "opencode" "OpenCode"
        fi

        # --- Aider --------------------------------------------------
        if should_install aider; then
        write_header "AIDER"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "aider" "Aider (CONVENTIONS.md)" "$languages"
        fi

        # --- Windsurf -----------------------------------------------
        if should_install windsurf; then
        write_header "WINDSURF"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "windsurf" "Windsurf (.windsurfrules)" "$languages"
        fi

        # --- Kimi ---------------------------------------------------
        # Project .kimi-code/ AGENTS.md + skills + custom agents. NO hooks at
        # workspace scope: Kimi's project config is local.toml and documents only
        # a [workspace] table, so there is no project hook path to write.
        if should_install kimi; then
        write_header "KIMI"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "kimi" "Kimi Code CLI (.kimi-code/)" "$languages"
        fi

        # --- Qwen ---------------------------------------------------
        # Project QWEN.md + .qwen/ surfaces plus native hooks merged into
        # .qwen/settings.json, resolved via $QWEN_PROJECT_DIR (v3.15.8 Phase 6).
        if should_install qwen; then
        write_header "QWEN"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "qwen" "Qwen Code (QWEN.md)" "$languages"
        fi

        # --- OpenClaw -----------------------------------------------
        if should_install openclaw; then
        write_header "OPENCLAW"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "openclaw" "OpenClaw (.openclaw/ SOUL+AGENTS+IDENTITY)" "$languages"
        fi

        # --- Nexus -- Nexus-AI --------------------------------------
        if should_install nexus-ai; then
        write_header "NEXUS"
        invoke_registry_platform "$repo_root" "workspace" "$target_path" "nexus-ai" "Nexus-AI (Local Desktop Studio)"
        fi

        # --- Auto-Approve Permissions sub-section --------------------------
        # v3.17.0 Phase 1.2: previously absent entirely, so a --workspace install
        # received no permission baseline on any operating system while the `scope`
        # parameter of install_permissions sat decorative. Only CLAUDE has a
        # confirmed project-scoped target (.claude/settings.local.json); the other
        # three skip with a note stating why. Gated on the same --platforms subset
        # as the global block.
        write_section_banner "AUTO-APPROVE PERMISSIONS"

        if should_install claude; then
        write_header "ANTHROPIC"
        install_permissions "$repo_root" "CLAUDE" "Workspace" "$target_path"
        fi

        if should_install codex; then
        write_header "OPENAI"
        install_permissions "$repo_root" "CODEX" "Workspace" "$target_path"
        fi

        if should_install gemini; then
        write_header "GOOGLE"
        install_permissions "$repo_root" "GEMINI" "Workspace" "$target_path"
        fi

        if should_install copilot; then
        write_header "MICROSOFT"
        install_permissions "$repo_root" "COPILOT" "Workspace" "$target_path"
        fi

        echo ""
}

resolve_python_executable() {
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"; return 0
    fi
    if command -v python >/dev/null 2>&1; then
        echo "python"; return 0
    fi
    return 1
}

# ---------------------------------------------------------------------------
# Install selection (v3.16.1 Phase 6.1)
#
# Contract: docs/releases/v3/v3.16/development/install-selection-contract.md
#
# Resolution delegates to scripts/lib/installer/selection.py rather than being
# reimplemented here. The plan originally called for a native implementation so
# the installer would not depend on Python; that was reversed after the jq
# version proved untestable on the development host, because two implementations
# of a hashed contract where one is unverifiable is worse than one shared
# implementation.
#
# What the original constraint protects is preserved exactly: these functions are
# only reached when the user passed a selector. A NO-SELECTOR install never calls
# them and still needs neither Python nor jq. A Python-less host already skips
# every registry-backed platform, so requiring Python for selectors specifically
# imposes nothing new on that host.
#
# Filtering is applied by STAGING: when a selection is active we materialize a
# filtered copy of catalog/skills, catalog/commands, and catalog/agents once, and
# every downstream copy reads from the stage via catalog_src(). Concentrating the
# filter in one place means per-platform copy sites need no per-site logic and
# cannot drift apart. Only those three surfaces are ever filtered; hooks, rules,
# context, memory, style-guides, and mcp-configs are policy infrastructure and
# are always installed in full.
# ---------------------------------------------------------------------------

SELECT_PROFILE=""
SELECT_MODULES=""
SELECT_BUNDLES=""
SELECTION_ACTIVE=0
SELECTION_STAGE=""
SELECTION_HASH=""
SELECTION_SKILL_COUNT=0
SELECTION_COMMAND_COUNT=0
SELECTION_AGENT_COUNT=0

selection_requested() {
    [ -n "$SELECT_PROFILE" ] || [ -n "$SELECT_MODULES" ] || [ -n "$SELECT_BUNDLES" ]
}

# Effective source directory for one catalog surface. Callers pass the repo root
# and the surface name; under an active selection the staged (filtered) tree is
# returned for the three selectable surfaces, otherwise the real catalog path.
catalog_src() {
    local repo_root="$1" surface="$2"
    if [ "$SELECTION_ACTIVE" = "1" ] && [ -d "$SELECTION_STAGE/$surface" ]; then
        printf '%s' "$SELECTION_STAGE/$surface"
    else
        printf '%s' "$repo_root/catalog/$surface"
    fi
}

# Resolve selectors and build the staging tree. Exits non-zero on a bad selector
# (2) or a catalog defect (3) BEFORE anything is written, which is the contract's
# fail-before-write rule.
resolve_selection() {
    local repo_root="$1"
    selection_requested || return 0

    local py
    if ! py=$(resolve_python_executable); then
        echo "" >&2
        echo "ERROR: --profile / --modules / --bundles need Python to resolve." >&2
        echo "       Install Python 3, or re-run without a selector for a full install" >&2
        echo "       (a full install requires neither Python nor jq)." >&2
        exit 2
    fi

    local resolver="$repo_root/scripts/lib/installer/selection.py"
    if [ ! -f "$resolver" ]; then
        echo "ERROR: selection resolver not found at $resolver" >&2
        exit 3
    fi

    local args=("$resolver" "--repo-root" "$repo_root" "--emit" "lines")
    [ -n "$SELECT_PROFILE" ] && args+=("--profile" "$SELECT_PROFILE")
    [ -n "$SELECT_MODULES" ] && args+=("--modules" "$SELECT_MODULES")
    [ -n "$SELECT_BUNDLES" ] && args+=("--bundles" "$SELECT_BUNDLES")

    # `set -e` is active, so a bare `out=$(...)` on a non-zero exit aborts the
    # script at the assignment and never reaches the handler below -- the user
    # would get exit 2 with no explanation of which selector was wrong. Capturing
    # the status in the `||` branch keeps the failure ours to report.
    local out rc=0
    out=$("$py" "${args[@]}" 2>&1) || rc=$?
    if [ "$rc" -ne 0 ]; then
        echo "" >&2
        echo "$out" >&2
        exit "$rc"
    fi

    SELECTION_STAGE="$(mktemp -d)"
    mkdir -p "$SELECTION_STAGE/skills" "$SELECTION_STAGE/commands" "$SELECTION_STAGE/agents"

    local kind value
    while IFS=$'\t' read -r kind value; do
        # Strip a trailing CR. A Windows Python invoked from Git Bash writes
        # CRLF, so without this every value carries a \r, `find -name` matches
        # nothing, and the install silently stages an empty selection -- which
        # looks like a working install that shipped no skills.
        kind="${kind%$'\r'}"
        value="${value%$'\r'}"
        case "$kind" in
            HASH) SELECTION_HASH="$value" ;;
            SKILL)
                # Skills live under catalog/skills/<category>/<name>/; the stage
                # keeps the category level so a nested-layout copy still works.
                local src
                src=$(find "$repo_root/catalog/skills" -mindepth 2 -maxdepth 2 -type d -name "$value" 2>/dev/null | head -1)
                if [ -n "$src" ]; then
                    local category
                    category="$(basename "$(dirname "$src")")"
                    mkdir -p "$SELECTION_STAGE/skills/$category"
                    cp -R "$src" "$SELECTION_STAGE/skills/$category/"
                    SELECTION_SKILL_COUNT=$((SELECTION_SKILL_COUNT + 1))
                fi
                ;;
            COMMAND)
                if [ -f "$repo_root/catalog/commands/$value.md" ]; then
                    cp "$repo_root/catalog/commands/$value.md" "$SELECTION_STAGE/commands/"
                    SELECTION_COMMAND_COUNT=$((SELECTION_COMMAND_COUNT + 1))
                fi
                ;;
            AGENT)
                if [ -f "$repo_root/catalog/agents/$value.md" ]; then
                    cp "$repo_root/catalog/agents/$value.md" "$SELECTION_STAGE/agents/"
                    SELECTION_AGENT_COUNT=$((SELECTION_AGENT_COUNT + 1))
                fi
                ;;
            WARN)
                echo "WARNING: selection resolved to the entire catalog; '--profile full' says this directly." >&2
                ;;
        esac
    done <<< "$out"

    SELECTION_ACTIVE=1
    return 0
}

cleanup_selection_stage() {
    [ -n "$SELECTION_STAGE" ] && [ -d "$SELECTION_STAGE" ] && rm -rf "$SELECTION_STAGE"
    return 0
}

# Run runner.py for a single registry-backed integration. Caller is
# responsible for printing the provider header (write_header). This
# function prints a sub-item label for the platform display name and
# the [OK] / error line.
#
# The instruction-template placeholders (PRIMARY_LANGUAGE, BUILD_CMD,
# OS_CONTEXT, ...) are threaded from the globals that the global block and
# detect_project_metadata set, so the registry renders the same instruction
# body the legacy bash render_template produced (DF-001). Passing them to every
# registry platform is harmless and fixes the latent literal-placeholder bug for
# the platforms that were already registry-driven.
#
# Args: $1=repo_root  $2=scope (global|workspace)  $3=target_path (workspace only)
#       $4=integration_key  $5=display_name
#       $6=languages (csv, optional)  $7=instruction_only ("true" to render only
#       the instruction file and skip the catalog mirror -- used when the bash
#       block already copied catalog/ via safe_folder_copy)
invoke_registry_platform() {
    local repo_root="$1"
    local scope="$2"
    local target_path="$3"
    local key="$4"
    local display="$5"
    local languages="${6:-}"
    local instruction_only="${7:-}"
    local provider="${8:-}"

    local runner="$repo_root/scripts/lib/integrations/runner.py"
    if [ ! -f "$runner" ]; then return 0; fi
    local py
    if ! py=$(resolve_python_executable); then
        write_item "Python not found -- skipping $display." "$DARK_YELLOW"
        return 0
    fi

    local summary_file
    summary_file="$(mktemp)"
    local args=("$runner" "install" "--scope" "$scope" "--integrations" "$key" "--quiet" "--summary-json" "$summary_file")
    if [ "$scope" = "workspace" ]; then
        args+=("--target" "$target_path")
    fi
    # v3.16.1 Phase 6.1: forward the selectors so the registry resolves the same
    # plan this script did. Passed as separate array elements, never interpolated
    # into a command string, so a selector value cannot inject an argument.
    [ -n "$SELECT_PROFILE" ] && args+=("--profile" "$SELECT_PROFILE")
    [ -n "$SELECT_MODULES" ] && args+=("--modules" "$SELECT_MODULES")
    [ -n "$SELECT_BUNDLES" ] && args+=("--bundles" "$SELECT_BUNDLES")
    if [ "$OVERWRITE_ALL" = true ]; then
        args+=("--overwrite")
    fi
    if [ "$instruction_only" = "true" ]; then
        args+=("--instruction-only")
    fi
    if [ -n "$languages" ]; then
        args+=("--languages" "$languages")
    fi
    # Thread the instruction-template placeholders from the detected globals.
    args+=("--project-name" "${PROJECT_NAME:-}")
    args+=("--var" "PRIMARY_LANGUAGE=${PRIMARY_LANGUAGE:-}")
    args+=("--var" "PACKAGE_MANAGER=${PACKAGE_MANAGER:-}")
    args+=("--var" "BUILD_TOOL=${BUILD_TOOL:-}")
    args+=("--var" "TEST_FRAMEWORK=${TEST_FRAMEWORK:-}")
    args+=("--var" "LINT_TOOL=${LINT_TOOL:-}")
    args+=("--var" "BUILD_CMD=${BUILD_CMD:-}")
    args+=("--var" "TEST_CMD=${TEST_CMD:-}")
    args+=("--var" "LINT_CMD=${LINT_CMD:-}")
    args+=("--var" "NON_OBVIOUS_TOOLING=${NON_OBVIOUS_TOOLING:-}")
    args+=("--var" "OS_CONTEXT=${OS_CONTEXT:-}")
    if "$py" "${args[@]}"; then
        render_platform_from_summary "$summary_file" "$key" "$provider" "$display" "$py"
    else
        [ -n "$provider" ] && write_header "$provider"
        write_item "$display" "$GRAY"
        write_item "install reported a non-zero exit; continuing." "$YELLOW"
    fi
    rm -f "$summary_file"
}

install_vscode_extensions() {
    local repo_root="$1"

    write_item "Usage Monitor extensions show Claude Code, Codex (ChatGPT), GitHub, and" "$RESET"
    write_item "Cursor usage in the status bar. Claude/Codex/GitHub install into VS Code only;" "$RESET"
    write_item "Cursor Usage Monitor installs into Cursor only. Never cross-installed." "$RESET"
    echo ""

    # Check for Node.js (shared by every extension)
    if ! command -v node >/dev/null 2>&1; then
        write_item "Node.js is not installed (required to build the extensions)." "$DARK_YELLOW"

        # Detect platform and suggest install method
        if command -v brew >/dev/null 2>&1; then
            # A non-interactive run (the piped one-command bootstrap, --yes, or CI)
            # installs without asking so every dependency is present in one pass;
            # an interactive run prompts first.
            local install_resp
            if [ "$ASSUME_YES" = true ]; then install_resp="y"; else install_resp=$(read_prompt "Install Node.js LTS via Homebrew? [Y]es / [N]o"); fi
            if [[ "$install_resp" =~ ^[Yy] ]]; then
                write_item "Installing Node.js LTS via Homebrew..." "$RESET"
                brew install node@22 || {
                    write_item "Homebrew install failed. Please install Node.js from https://nodejs.org" "$RED"
                    return
                }
                write_item "[OK] Node.js installed successfully." "$GREEN"
            else
                write_item "Skipped. Install Node.js from https://nodejs.org and re-run." "$GRAY"
                return
            fi
        elif command -v apt-get >/dev/null 2>&1; then
            local install_resp
            if [ "$ASSUME_YES" = true ]; then install_resp="y"; else install_resp=$(read_prompt "Install Node.js via apt? [Y]es / [N]o"); fi
            if [[ "$install_resp" =~ ^[Yy] ]]; then
                write_item "Installing Node.js via apt..." "$RESET"
                sudo apt-get update -qq && sudo apt-get install -y -qq nodejs npm || {
                    write_item "apt install failed. Please install Node.js from https://nodejs.org" "$RED"
                    return
                }
                write_item "[OK] Node.js installed successfully." "$GREEN"
            else
                write_item "Skipped. Install Node.js from https://nodejs.org and re-run." "$GRAY"
                return
            fi
        else
            write_item "Please install Node.js from https://nodejs.org and re-run the installer." "$YELLOW"
            return
        fi
    else
        local node_version
        node_version=$(node --version)
        write_item "Found Node.js $node_version" "$GREEN"
    fi

    # Check for npm (shared)
    if ! command -v npm >/dev/null 2>&1; then
        write_item "npm not found. Please ensure Node.js is properly installed." "$RED"
        return
    fi

    # Dual-host resolution (v3.15.9 Phase 6): VS Code CLI and Cursor CLI are
    # discovered independently. Cursor must NEVER be a fallback for the VS Code
    # monitors, and VS Code must NEVER receive the Cursor monitor.
    local vscode_cli=""
    local vscode_label="VS Code"
    if command -v code >/dev/null 2>&1; then
        vscode_cli="code"
    else
        local candidate
        for candidate in \
            "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" \
            "$HOME/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" \
            "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code" \
            "/usr/share/code/bin/code" \
            "/usr/bin/code" \
            "/snap/bin/code" \
            "/var/lib/flatpak/exports/bin/com.visualstudio.code" \
            "/Applications/VSCodium.app/Contents/Resources/app/bin/codium" \
            "$HOME/Applications/VSCodium.app/Contents/Resources/app/bin/codium"; do
            if [ -x "$candidate" ]; then
                vscode_cli="$candidate"
                case "$candidate" in
                    *VSCodium*) vscode_label="VSCodium" ;;
                esac
                break
            fi
        done
    fi

    local cursor_cli=""
    local cursor_label="Cursor"
    if command -v cursor >/dev/null 2>&1; then
        cursor_cli="cursor"
    else
        local cursor_candidate
        for cursor_candidate in \
            "/Applications/Cursor.app/Contents/Resources/app/bin/cursor" \
            "$HOME/Applications/Cursor.app/Contents/Resources/app/bin/cursor"; do
            if [ -x "$cursor_candidate" ]; then
                cursor_cli="$cursor_candidate"
                break
            fi
        done
    fi

    # Build each extension under its own vendor header. VS Code monitors install
    # only via vscode_cli; the Cursor monitor installs only via cursor_cli. The
    # vendor order (Anthropic, OpenAI, Anysphere) is asserted by the
    # installer smoke test and must match scripts/installer.ps1.
    write_header "ANTHROPIC"
    build_and_install_one_extension "$repo_root/extensions/claude-usage-monitor" "nexus-hub.claude-usage-monitor" "Claude Usage Monitor" "Claude: --%" "$vscode_cli" "$vscode_label"

    write_header "OPENAI"
    build_and_install_one_extension "$repo_root/extensions/codex-usage-monitor" "nexus-hub.codex-usage-monitor" "Codex Usage Monitor" "Codex: --%" "$vscode_cli" "$vscode_label"

    write_header "ANYSPHERE"
    build_and_install_one_extension "$repo_root/extensions/cursor-usage-monitor" "nexus-hub.cursor-usage-monitor" "Cursor Usage Monitor" "Cursor: --%" "$cursor_cli" "$cursor_label"
}

# Build, package, and install one VS Code usage-monitor extension. Shared by
# install_vscode_extensions so every monitor installs identically.
# Args: $1 extension_dir  $2 extension_id  $3 display_name  $4 status_hint
#       $5 code_cli (may be empty)  $6 code_label
build_and_install_one_extension() {
    local extension_dir="$1"
    local extension_id="$2"
    local display_name="$3"
    local status_hint="$4"
    local code_cli="$5"
    local code_label="$6"
    # Optional SECOND host. One VSIX, installed into two editors: Cursor is a
    # separate application with its own extension directory, so an extension
    # installed into VS Code is simply absent there.
    local also_cli="${7:-}"
    local also_label="${8:-}"

    echo ""
    echo -e "  ${DARK_YELLOW}> ${display_name}${RESET}"

    if [ ! -d "$extension_dir" ]; then
        write_item "Extension source not found at: $extension_dir" "$RED"
        return
    fi

    write_item "Building ${display_name} extension..." "$RESET"

    pushd "$extension_dir" > /dev/null || return

    # Clean compiled output so deleted source files don't linger as stale JS
    if [ -d "$extension_dir/out" ]; then
        rm -rf "$extension_dir/out"
    fi

    # A node_modules tree copied in from another OS (e.g. zipping a Windows
    # checkout) leaves Windows .cmd/.ps1 bin shims that a Unix shell cannot
    # exec, so `tsc` resolves to "command not found" and the build fails with a
    # confusing error. Removing it forces a clean, OS-correct dependency tree.
    if [ -d node_modules ]; then
        rm -rf node_modules
    fi

    write_item "  Installing dependencies..." "$GRAY"
    local npm_log
    if ! npm_log=$(npm install --silent 2>&1); then
        write_item "npm install failed:" "$RED"
        echo "$npm_log" | tail -n 20
        popd > /dev/null
        return
    fi

    write_item "  Compiling TypeScript..." "$GRAY"
    local compile_log
    if ! compile_log=$(npm run compile 2>&1); then
        write_item "TypeScript compilation failed:" "$RED"
        echo "$compile_log" | tail -n 30
        popd > /dev/null
        return
    fi

    write_item "[OK] Extension built successfully." "$GREEN"

    # Package as VSIX (uses locally installed @vscode/vsce from devDependencies).
    # A bundled LICENSE file removes the only packaging warning, so vsce no longer
    # shows its interactive "Do you want to continue? [y/N]" prompt. Piping "y" is
    # belt-and-suspenders: if any future warning reappears it auto-confirms instead
    # of blocking an unattended install (harmless when there is no prompt).
    write_item "Packaging extension as VSIX..." "$RESET"
    echo "y" | npx vsce package --no-dependencies 2>/dev/null
    local vsix_file
    vsix_file=$(ls -t "$extension_dir"/*.vsix 2>/dev/null | head -1)

    if [ -z "$vsix_file" ]; then
        write_item "VSIX packaging failed." "$RED"
        write_item "You can still use the extension in development mode (F5 in VS Code)." "$YELLOW"
        popd > /dev/null
        return
    fi

    write_item "[OK] Packaged: $(basename "$vsix_file")" "$GREEN"

    popd > /dev/null

    # Install into the detected editor
    if [ -n "$code_cli" ]; then
        # Uninstall any existing version first so the editor does not skip the reinstall
        "$code_cli" --uninstall-extension "$extension_id" 2>/dev/null || true
        # --force ensures reinstall even when the version number has not changed
        if "$code_cli" --install-extension "$vsix_file" --force 2>/dev/null; then
            write_item "[OK] ${display_name} extension installed in $code_label!" "$GREEN"
            write_item "  Restart $code_label to activate. Look for '${status_hint}' in the status bar." "$RESET"
        else
            write_item "$code_label install failed. Install manually:" "$YELLOW"
            write_item "  \"$code_cli\" --install-extension \"$vsix_file\"" "$RESET"
        fi
    else
        write_item "$code_label CLI not found in PATH or standard install locations." "$YELLOW"
        write_item "VSIX saved at: $vsix_file" "$RESET"
        write_item "Install manually via $code_label: Extensions > ... > Install from VSIX" "$GRAY"
    fi

    # The second host, when one was requested AND detected. Silent when Cursor is
    # not installed: a missing optional editor is not a failure to report.
    if [ -n "$also_cli" ]; then
        "$also_cli" --uninstall-extension "$extension_id" 2>/dev/null || true
        if "$also_cli" --install-extension "$vsix_file" --force 2>/dev/null; then
            write_item "[OK] ${display_name} extension installed in $also_label!" "$GREEN"
            write_item "  Restart $also_label to activate. Look for '${status_hint}' in the status bar." "$RESET"
        else
            write_item "$also_label install failed. Install manually:" "$YELLOW"
            write_item "  \"$also_cli\" --install-extension \"$vsix_file\"" "$RESET"
        fi
    fi
}

# --- Template & Script Installation ---

install_templates() {
    local repo_root="$1"

    # A "- subsection" under the CROSS-PLATFORM TOOLS section opened in install_global.
    write_subsection_banner "Report templates & generator"
    echo ""
    write_item "Nexus-Hub can generate professional Word (.docx) and PowerPoint (.pptx)" "$RESET"
    write_item "reports from Markdown files using the /research report command." "$RESET"
    echo ""

    # Ensure global directories exist
    local nexus_home="$HOME/.nexus-hub"
    local templates_dest="$nexus_home/templates/documentation"
    local scripts_dest="$nexus_home/scripts"

    mkdir -p "$templates_dest"
    mkdir -p "$scripts_dest"

    # Copy bundled templates from repo
    local builtin_templates="$repo_root/templates/documentation"
    if [ -d "$builtin_templates" ]; then
        safe_folder_copy "$builtin_templates" "$templates_dest" "[OK] Built-in templates installed at: $templates_dest"
    fi

    # Copy report generator script
    local script_source="$repo_root/scripts/generate_report.py"
    if [ -f "$script_source" ]; then
        safe_copy "$script_source" "$scripts_dest/generate_report.py" true "[OK] Report generator installed at: $scripts_dest/generate_report.py"
    fi

    # Copy MCP benchmark script (v1.0.0+). Benchmarks the three internal MCPs
    # (nexus-skill-server, nexus-code-search, nexus-web-fetch). Pure-local.
    local benchmark_source="$repo_root/scripts/nexus_mcp_benchmark.py"
    if [ -f "$benchmark_source" ]; then
        safe_copy "$benchmark_source" "$scripts_dest/nexus_mcp_benchmark.py" true "[OK] MCP benchmark installed at: $scripts_dest/nexus_mcp_benchmark.py"
    fi

    # Copy skill-eval-loop dispatcher scripts (v1.2.0-wip / Phase 5 / A6 + A7).
    # Three repo-level scripts that work alongside the catalog/skills/workflow/
    # skill-eval-loop/ skill: the iteration aggregator, the browser-based
    # viewer, and the description optimizer. All three follow the v1.1.3
    # four-hook precedent for CLI dispatch (single dispatcher with --cli
    # flag, no cross-CLI fallback, parity-test enforced via pytest).
    local eval_aggregator_source="$repo_root/scripts/aggregate_benchmark.py"
    if [ -f "$eval_aggregator_source" ]; then
        safe_copy "$eval_aggregator_source" "$scripts_dest/aggregate_benchmark.py" true "[OK] Eval-loop benchmark aggregator installed at: $scripts_dest/aggregate_benchmark.py"
    fi
    local eval_viewer_source="$repo_root/scripts/skill_eval_viewer.py"
    if [ -f "$eval_viewer_source" ]; then
        safe_copy "$eval_viewer_source" "$scripts_dest/skill_eval_viewer.py" true "[OK] Eval-loop browser viewer installed at: $scripts_dest/skill_eval_viewer.py"
    fi
    local eval_optimizer_source="$repo_root/scripts/optimize_skill_description.py"
    if [ -f "$eval_optimizer_source" ]; then
        safe_copy "$eval_optimizer_source" "$scripts_dest/optimize_skill_description.py" true "[OK] Skill-description optimizer installed at: $scripts_dest/optimize_skill_description.py"
    fi
    # Copy the behavioral-eval schema converter (v3.15.2 / A4). Bidirectional,
    # lossless converter between the eval-loop's internal evals.json and the
    # interoperable behavioral-eval schema, for interop with external skill-eval
    # tooling. Stdlib-only single .py (cross-platform, no .ps1 sibling), sibling
    # of the eval-loop scripts above. Lockstep with the same block in
    # scripts/installer.ps1.
    local eval_convert_source="$repo_root/scripts/skill_eval_convert.py"
    if [ -f "$eval_convert_source" ]; then
        safe_copy "$eval_convert_source" "$scripts_dest/skill_eval_convert.py" true "[OK] Eval-loop schema converter installed at: $scripts_dest/skill_eval_convert.py"
    fi

    # Copy the trigger-and-routing eval (v3.15.2 / A1). A stdlib-only,
    # model-free detector that flags skill-description trigger-vocabulary
    # near-collisions across the whole catalog, plus its intentional-neighbor
    # allowlist. The runner defaults to warning-only and reads the allowlist
    # from the file beside it, so both must land together under scripts/.
    # Lockstep with the same block in scripts/installer.ps1.
    local trigger_evals_source="$repo_root/scripts/run_trigger_evals.py"
    if [ -f "$trigger_evals_source" ]; then
        safe_copy "$trigger_evals_source" "$scripts_dest/run_trigger_evals.py" true "[OK] Trigger-and-routing eval installed at: $scripts_dest/run_trigger_evals.py"
    fi
    # v3.17.0 Phase 1: permission-baseline tooling. merge_permissions.py is the
    # single merge implementation BOTH installers call (see
    # merge_permissions_via_helper above); validate_permission_baseline.py is the
    # guard that keeps mutation-capable entries out of the read-only baseline.
    local merge_permissions_source="$repo_root/scripts/merge_permissions.py"
    if [ -f "$merge_permissions_source" ]; then
        safe_copy "$merge_permissions_source" "$scripts_dest/merge_permissions.py" true "[OK] Permission merge helper installed at: $scripts_dest/merge_permissions.py"
    fi
    local validate_baseline_source="$repo_root/scripts/validate_permission_baseline.py"
    if [ -f "$validate_baseline_source" ]; then
        safe_copy "$validate_baseline_source" "$scripts_dest/validate_permission_baseline.py" true "[OK] Permission-baseline validator installed at: $scripts_dest/validate_permission_baseline.py"
    fi

    local trigger_evals_allowlist_source="$repo_root/scripts/run_trigger_evals.allowlist.json"
    if [ -f "$trigger_evals_allowlist_source" ]; then
        safe_copy "$trigger_evals_allowlist_source" "$scripts_dest/run_trigger_evals.allowlist.json" true "[OK] Trigger-eval allowlist installed at: $scripts_dest/run_trigger_evals.allowlist.json"
    fi

    # Copy the per-model prompting profile-layer scripts (v3.15.5 Phase 1). The
    # structural schema gate for the model-prompting-research skill's profile
    # layer, plus the ADVISORY roster-staleness checker. Both are stdlib-only and
    # make no outbound call. They must land together: the freshness checker
    # imports the bundle discovery and the canonical roster-hash definition from
    # the validator beside it, the same pairing rule as the trigger-eval allowlist
    # above. The skill bundle itself (profiles, references, assets) auto-copies via
    # the recursive skill-folder copy and needs no entry here; only these two
    # standalone scripts do. Lockstep with the same block in scripts/installer.ps1.
    local profile_schema_source="$repo_root/scripts/verify_model_prompting_profiles.py"
    if [ -f "$profile_schema_source" ]; then
        safe_copy "$profile_schema_source" "$scripts_dest/verify_model_prompting_profiles.py" true "[OK] Prompting-profile schema validator installed at: $scripts_dest/verify_model_prompting_profiles.py"
    fi
    local profile_freshness_source="$repo_root/scripts/check_model_prompting_freshness.py"
    if [ -f "$profile_freshness_source" ]; then
        safe_copy "$profile_freshness_source" "$scripts_dest/check_model_prompting_freshness.py" true "[OK] Prompting-profile freshness checker installed at: $scripts_dest/check_model_prompting_freshness.py"
    fi

    # Copy .skill packager script (v1.2.0-wip / Phase 7 / A16). Produces a
    # portable .skill ZIP archive from a catalog/skills/<cat>/<name>/ directory
    # for distribution to Claude.ai or the Anthropic API skill-upload endpoint
    # - delivery channels Nexus-Hub does not currently reach. Lockstep with
    # the same block in scripts/installer.ps1.
    local skill_packager_source="$repo_root/scripts/package_skill.py"
    if [ -f "$skill_packager_source" ]; then
        safe_copy "$skill_packager_source" "$scripts_dest/package_skill.py" true "[OK] Skill packager installed at: $scripts_dest/package_skill.py"
    fi

    # Copy the /skills import hygiene gate (v3.6.0 Phase 4 / N6). Hardens the
    # LOCAL import path with HTTPS-only source validation, an install_allowed
    # discovery-only flag, and hash-on-import (the hashing reuses
    # scripts/lib/integrations/manifest.py, copied separately under lib/). It
    # adds NO outbound call or credential and is additive to the pre-install
    # skill-security scan. Lockstep with the same block in scripts/installer.ps1.
    local import_hygiene_source="$repo_root/scripts/import_skills.py"
    if [ -f "$import_hygiene_source" ]; then
        safe_copy "$import_hygiene_source" "$scripts_dest/import_skills.py" true "[OK] Skill-import hygiene gate installed at: $scripts_dest/import_skills.py"
    fi

    # Copy nexus-hub affected CLI dispatcher (v2.2.0 / codegraph Phase 5 /
    # T032). Thin wrapper around the nexus-code-search code_affected_tests
    # graph query so users can pipe `git diff --name-only` into a test-impact
    # query without booting the MCP server. Lockstep with the same block in
    # scripts/installer.ps1.
    local affected_source="$repo_root/scripts/nexus_hub_affected.py"
    if [ -f "$affected_source" ]; then
        safe_copy "$affected_source" "$scripts_dest/nexus_hub_affected.py" true "[OK] Affected-tests CLI installed at: $scripts_dest/nexus_hub_affected.py"
    fi

    # Copy the nexus-hub CLI core (v3.7.0 Phase 3). The logic behind the
    # `nexus-hub` launcher on PATH: `nexus-hub --version` and `nexus-hub
    # upgrade`. Stdlib-only, cross-platform single .py (NI-v24-1), so no .ps1
    # sibling. The launcher itself + the VERSION file are installed by
    # install_cli_launcher below. Lockstep with the same block in
    # scripts/installer.ps1.
    local cli_source="$repo_root/scripts/nexus_hub_cli.py"
    if [ -f "$cli_source" ]; then
        safe_copy "$cli_source" "$scripts_dest/nexus_hub_cli.py" true "[OK] nexus-hub CLI installed at: $scripts_dest/nexus_hub_cli.py"
    fi

    # Copy the supply-chain manifest tooling (v3.10.0). generate_manifest.py
    # writes a SHA-256 MANIFEST.sha256 over the distributed catalog tree at
    # release time; verify_install.py powers `nexus-hub verify`, which recomputes
    # those hashes against the installed tree and reports OK/MODIFIED/MISSING/
    # EXTRA with zero outbound call. Both are stdlib-only single .py files
    # (NI-v24-1, no .ps1 sibling -- the nexus-hub.cmd launcher already covers
    # Windows via nexus_hub_cli.py). The MANIFEST.sha256 (committed at the repo
    # root by the release flow) is copied to the install root as a known-location
    # convenience; `nexus-hub verify` primarily reads the copy that rides inside
    # the materialized source tree (~/.nexus-hub/src/MANIFEST.sha256). Lockstep
    # with the same block in scripts/installer.ps1.
    local gen_manifest_source="$repo_root/scripts/generate_manifest.py"
    if [ -f "$gen_manifest_source" ]; then
        safe_copy "$gen_manifest_source" "$scripts_dest/generate_manifest.py" true "[OK] Manifest generator installed at: $scripts_dest/generate_manifest.py"
    fi
    local verify_source="$repo_root/scripts/verify_install.py"
    if [ -f "$verify_source" ]; then
        safe_copy "$verify_source" "$scripts_dest/verify_install.py" true "[OK] Install verifier installed at: $scripts_dest/verify_install.py"
    fi
    # setup_media_keys.py powers `nexus-hub setup-media`, the opt-in guided
    # bring-your-own-key helper for optional stock-media API keys (Pexels, for
    # stock video). Stdlib-only single .py (NI-v24-1, no .ps1 sibling -- the
    # nexus-hub.cmd launcher covers Windows via nexus_hub_cli.py, where the
    # setup-media subcommand is dispatched). Lockstep with scripts/installer.ps1.
    local media_setup_source="$repo_root/scripts/setup_media_keys.py"
    if [ -f "$media_setup_source" ]; then
        safe_copy "$media_setup_source" "$scripts_dest/setup_media_keys.py" true "[OK] Media-key setup helper installed at: $scripts_dest/setup_media_keys.py"
    fi
    local manifest_source="$repo_root/MANIFEST.sha256"
    if [ -f "$manifest_source" ]; then
        safe_copy "$manifest_source" "$nexus_home/MANIFEST.sha256" true "[OK] Supply-chain manifest installed at: $nexus_home/MANIFEST.sha256"
    fi

    # Copy v2.3.0 CI validators (Phase 2 / T004-T005). Four standalone static
    # validators that run on the clean tree and fail non-zero on a finding:
    # validate_no_personal_paths.py scans distributed docs for leaked
    # /Users/<name> or C:\Users\<name> paths; validate_unicode_safety.py
    # flags unsafe / confusable Unicode (Trojan Source, zero-width chars);
    # scan_supply_chain_iocs.py inspects dependency manifests and installers
    # for curl-pipe-bash, lifecycle shell-outs, floating GitHub Action refs,
    # and known typosquats; validate_workflow_security.py audits
    # .github/workflows/*.yml for pull_request_target + head checkout,
    # ${{ github.event.* }} injection in run: blocks, and write-all
    # permissions. Lockstep with the same block in scripts/installer.ps1.
    local no_paths_source="$repo_root/scripts/validate_no_personal_paths.py"
    if [ -f "$no_paths_source" ]; then
        safe_copy "$no_paths_source" "$scripts_dest/validate_no_personal_paths.py" true "[OK] No-personal-paths validator installed at: $scripts_dest/validate_no_personal_paths.py"
    fi
    local unicode_source="$repo_root/scripts/validate_unicode_safety.py"
    if [ -f "$unicode_source" ]; then
        safe_copy "$unicode_source" "$scripts_dest/validate_unicode_safety.py" true "[OK] Unicode-safety validator installed at: $scripts_dest/validate_unicode_safety.py"
    fi
    local iocs_source="$repo_root/scripts/scan_supply_chain_iocs.py"
    if [ -f "$iocs_source" ]; then
        safe_copy "$iocs_source" "$scripts_dest/scan_supply_chain_iocs.py" true "[OK] Supply-chain IOC scanner installed at: $scripts_dest/scan_supply_chain_iocs.py"
    fi
    local workflow_source="$repo_root/scripts/validate_workflow_security.py"
    if [ -f "$workflow_source" ]; then
        safe_copy "$workflow_source" "$scripts_dest/validate_workflow_security.py" true "[OK] Workflow-security validator installed at: $scripts_dest/validate_workflow_security.py"
    fi
    # validate_solution_frontmatter.py (v2.4.0) is a parser-safety linter for
    # solution-knowledge-base docs (docs/solutions/<category>/<slug>.md); it
    # uses Python stdlib only. Lockstep with scripts/installer.ps1.
    local solution_fm_source="$repo_root/scripts/validate_solution_frontmatter.py"
    if [ -f "$solution_fm_source" ]; then
        safe_copy "$solution_fm_source" "$scripts_dest/validate_solution_frontmatter.py" true "[OK] Solution-frontmatter validator installed at: $scripts_dest/validate_solution_frontmatter.py"
    fi
    # check_version_sync.py (v3.0.0): version-drift guard. Reads the canonical
    # version from .claude-plugin/plugin.json and asserts every other
    # version-carrying surface (both installers, marketplace.json, the latest
    # CHANGELOG heading, README/AGENTS markers) matches it. Stdlib-only, so it
    # is a single cross-platform .py file with no .ps1 sibling (NI-v24-1
    # convention). Lockstep with scripts/installer.ps1.
    local version_sync_source="$repo_root/scripts/check_version_sync.py"
    if [ -f "$version_sync_source" ]; then
        safe_copy "$version_sync_source" "$scripts_dest/check_version_sync.py" true "[OK] Version-sync guard installed at: $scripts_dest/check_version_sync.py"
    fi
    # check_release_preconditions.py (v3.17.6): release-flow guard. --pre-tag
    # refuses to tag unless HEAD is the expected release branch AND matches its
    # remote (the v3.17.5 mis-tag: a checkout failed on a locked directory and
    # the tag was created on the wrong commit). --branches and --repo-settings
    # report merged remote branches and delete_branch_on_merge, advisory only,
    # deleting nothing. Stdlib-only, so it is a single cross-platform .py file
    # with no .ps1 sibling (NI-v24-1 convention). Distributed because
    # /update release ships to users and must not describe a check they lack.
    # Lockstep with scripts/installer.ps1.
    local release_precond_source="$repo_root/scripts/check_release_preconditions.py"
    if [ -f "$release_precond_source" ]; then
        safe_copy "$release_precond_source" "$scripts_dest/check_release_preconditions.py" true "[OK] Release-preconditions guard installed at: $scripts_dest/check_release_preconditions.py"
    fi
    # scan_skill_security.py (v3.0.0): thin CLI launcher for the
    # nexus-skill-scanner static skill-security engine (extensions/nexus-skill-scanner).
    # Stdlib-only launcher; it locates the bundled package src under extensions/.
    # Single cross-platform .py file with no .ps1 sibling (NI-v24-1 convention).
    # Lockstep with scripts/installer.ps1.
    local scan_skill_source="$repo_root/scripts/scan_skill_security.py"
    if [ -f "$scan_skill_source" ]; then
        safe_copy "$scan_skill_source" "$scripts_dest/scan_skill_security.py" true "[OK] Skill-security scanner installed at: $scripts_dest/scan_skill_security.py"
    fi
    # generate_release_changelog.py / .ps1 (v2.4.0): local conventional-commit
    # release helper - computes the next semver bump + a Keep-a-Changelog
    # section from git history. Zero-outbound (local git only); an optional
    # helper for the /update version / /update changelog flows, NOT a GitHub
    # Action. Both siblings ship. Lockstep with scripts/installer.ps1.
    local release_changelog_py="$repo_root/scripts/generate_release_changelog.py"
    if [ -f "$release_changelog_py" ]; then
        safe_copy "$release_changelog_py" "$scripts_dest/generate_release_changelog.py" true "[OK] Release-changelog helper installed at: $scripts_dest/generate_release_changelog.py"
    fi
    local release_changelog_ps1="$repo_root/scripts/generate_release_changelog.ps1"
    if [ -f "$release_changelog_ps1" ]; then
        safe_copy "$release_changelog_ps1" "$scripts_dest/generate_release_changelog.ps1" true "[OK] Release-changelog helper (PowerShell) installed at: $scripts_dest/generate_release_changelog.ps1"
    fi

    # Copy v2.3.0 Phase 4 lifecycle scripts (T011 consult advisor + T012
    # harness audit). The doctor / repair / list-installed surface itself
    # lives on `scripts/lib/integrations/runner.py` so it ships via the
    # registry copy step further down; no separate file is needed for it.
    # Lockstep with the matching block in scripts/installer.ps1.
    local consult_source="$repo_root/scripts/nexus_hub_consult.py"
    if [ -f "$consult_source" ]; then
        safe_copy "$consult_source" "$scripts_dest/nexus_hub_consult.py" true "[OK] Consult advisor installed at: $scripts_dest/nexus_hub_consult.py"
    fi
    local audit_source="$repo_root/scripts/harness_audit.py"
    if [ -f "$audit_source" ]; then
        safe_copy "$audit_source" "$scripts_dest/harness_audit.py" true "[OK] Harness audit installed at: $scripts_dest/harness_audit.py"
    fi

    # Copy v2.3.0 Phase 6 framework-coverage generator (T017). Read-only,
    # zero-outbound: reads the optional framework-mapping frontmatter fields
    # (mitre_attack / atlas_techniques / d3fend_techniques / nist_csf /
    # nist_ai_rmf) across catalog/skills/ and emits a coverage matrix
    # (Markdown or JSON) of which skills cover which MITRE/NIST controls.
    # Lockstep with the matching block in scripts/installer.ps1.
    local coverage_source="$repo_root/scripts/build_framework_coverage.py"
    if [ -f "$coverage_source" ]; then
        safe_copy "$coverage_source" "$scripts_dest/build_framework_coverage.py" true "[OK] Framework coverage generator installed at: $scripts_dest/build_framework_coverage.py"
    fi

    # Copy feature-directory bootstrap scripts (v2.1.0 / adoption-spec-kit
    # Phase 7 / G5). The two scripts resolve the next specs/<NNN>-<slug>/
    # prefix (sequential or timestamp per .specify/init-options.json),
    # create the directory, and persist .specify/feature.json so downstream
    # commands (/spec clarify, /spec analyze, /plan issues) can locate
    # the active feature directory without git-branch coupling. Lockstep
    # with the same block in scripts/installer.ps1.
    local new_feature_sh_source="$repo_root/scripts/new-feature.sh"
    if [ -f "$new_feature_sh_source" ]; then
        safe_copy "$new_feature_sh_source" "$scripts_dest/new-feature.sh" true "[OK] Feature directory bootstrap (bash) installed at: $scripts_dest/new-feature.sh"
        chmod +x "$scripts_dest/new-feature.sh" 2>/dev/null || true
    fi
    local new_feature_ps1_source="$repo_root/scripts/new-feature.ps1"
    if [ -f "$new_feature_ps1_source" ]; then
        safe_copy "$new_feature_ps1_source" "$scripts_dest/new-feature.ps1" true "[OK] Feature directory bootstrap (PowerShell) installed at: $scripts_dest/new-feature.ps1"
    fi

    # Copy integration registry module (v2.1.0+). The integrations registrar
    # ships the per-platform install logic for the extended platforms (Windsurf,
    # Antigravity 2.0, Gemini CLI, Nexus-AI). The recursive folder copy lands
    # the whole class hierarchy under ~/.nexus-hub/scripts/lib/integrations/.
    # v3.16.1 (NI-3): copy the WHOLE scripts/lib tree, not just integrations/.
    # Six integration modules import from scripts/lib/installer/ (three at module
    # top level), so copying only integrations/ produced an installed tree that
    # looked importable and was not. Nothing executed it -- the registry always
    # runs from the checkout -- but shipping a knowingly-broken copy is worse
    # than either fixing it or not shipping it, and the resolver added in
    # v3.16.1 lands in that same directory.
    local lib_src="$repo_root/scripts/lib"
    local lib_dest="$scripts_dest/lib"
    if [ -d "$lib_src" ]; then
        safe_folder_copy "$lib_src" "$lib_dest" "[OK] Integration registry installed at: $lib_dest/integrations"
    fi
    # Empty package markers so the module can be imported from the installed location.
    if [ -d "$scripts_dest/lib" ]; then
        : > "$scripts_dest/lib/__init__.py" 2>/dev/null || true
    fi

    # Copy style-guides (v1.0.0+). Reference content for /research compile
    # and /research report; deliberately not in catalog/commands/ so the files
    # do not surface as slash commands.
    local style_guides_src="$repo_root/catalog/style-guides"
    local style_guides_dest="$nexus_home/style-guides"
    if [ -d "$style_guides_src" ]; then
        safe_folder_copy "$style_guides_src" "$style_guides_dest" "[OK] Style guides installed at: $style_guides_dest"
    fi

    # Copy opt-in git pre-commit hook sources (v1.1.2+; expanded to four
    # platform-parallel variants in v1.1.3). Each hook calls only its own
    # CLI - they are independent of each other. The hooks themselves are
    # NEVER auto-wired into a repository; users opt in by running the
    # /setup hooks slash command from inside the target
    # repo, which copies the chosen platform's script to .git/hooks/pre-commit.
    local nexus_hooks_dest="$nexus_home/hooks"
    mkdir -p "$nexus_hooks_dest"
    for diff_review_variant in claude-diff-review.sh gemini-diff-review.sh antigravity-cli-diff-review.sh codex-diff-review.sh opencode-diff-review.sh; do
        local diff_review_src="$repo_root/catalog/hooks/$diff_review_variant"
        if [ -f "$diff_review_src" ]; then
            safe_copy "$diff_review_src" "$nexus_hooks_dest/$diff_review_variant" true "[OK] Pre-commit review hook source installed at: $nexus_hooks_dest/$diff_review_variant"
            chmod +x "$nexus_hooks_dest/$diff_review_variant" 2>/dev/null || true
        fi
    done

    # Check Python availability
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        write_item "Note: Python 3 is required to generate reports." "$YELLOW"
        write_item "Install via your package manager (e.g., brew install python3, apt install python3)." "$YELLOW"
    else
        local python_cmd="python3"
        if ! command -v python3 >/dev/null 2>&1; then python_cmd="python"; fi

        if $python_cmd -c "import docx; import pptx" 2>/dev/null; then
            write_item "[OK] Python dependencies (python-docx, python-pptx) are available" "$GREEN"
        else
            write_item "Note: Install report dependencies with: pip install python-docx python-pptx" "$YELLOW"
        fi

        # v3.16.0 Phase 3: optional seeding dependencies. Platform install-time
        # behavioral defaults (configs/platform-defaults.json) are seeded into each
        # platform's own config. JSON targets use the stdlib; TOML targets need
        # tomlkit (which round-trips a user's comments and layout rather than
        # rewriting them) and YAML targets need PyYAML. Both are OPTIONAL: without
        # them the affected platforms simply skip seeding with a one-line hint, so
        # a missing library never breaks an install.
        if $python_cmd -c "import tomlkit; import yaml" 2>/dev/null; then
            write_item "[OK] Python dependencies (tomlkit, PyYAML) are available" "$GREEN"
        else
            write_item "Note: Install platform-defaults seeding deps with: pip install tomlkit PyYAML" "$YELLOW"
            write_item "      (without them, TOML/YAML platform defaults are skipped; JSON platforms are unaffected)" "$YELLOW"
        fi
    fi

    # v0.9.7: The interactive "Import custom Word/PowerPoint templates?" prompt has been
    # removed. Custom template selection is now handled at report-generation time by the
    # `/research report` command (generic vs custom path gate). Bundled generic templates
    # are still copied silently above so the command has a default to offer.

    # List installed templates
    echo ""
    write_item "Installed templates:" "$RESET"
    local found_templates=false
    for t in "$templates_dest"/*.docx "$templates_dest"/*.pptx; do
        if [ -f "$t" ]; then
            write_item "  $(basename "$t")" "$GREEN"
            found_templates=true
        fi
    done
    if [ "$found_templates" = false ]; then
        write_item "  (none)" "$GRAY"
    fi
    # No trailing blank: the next section banner prepends its own single blank.
}

# --- nexus-hub CLI launcher (v3.7.0 Phase 3) ---

# Writes the installed-version marker and drops the `nexus-hub` launcher on PATH
# (~/.nexus-hub/bin/nexus-hub). The launcher is a thin shim over the CLI core
# (scripts/nexus_hub_cli.py, copied by install_templates) that powers
# `nexus-hub --version` and `nexus-hub upgrade`. `upgrade`'s only outbound call
# is to the project's own GitHub. PATH wiring is best-effort: a clear hint is
# printed and shell-rc files are NEVER auto-edited (a no-prompt install must not
# silently mutate a user dotfile). Lockstep with Install-CliLauncher in
# scripts/installer.ps1.
install_cli_launcher() {
    local repo_root="$1"
    local nexus_home="$HOME/.nexus-hub"
    local bin_dest="$nexus_home/bin"

    write_section_banner "NEXUS-HUB CLI"
    echo ""

    # Installed-version marker (install-mode independent; read by the CLI's
    # --version and upgrade). Written from the canonical $NEXUS_HUB_VERSION, so
    # it is deliberately NOT a check_version_sync surface (never hand-edited).
    printf '%s\n' "$NEXUS_HUB_VERSION" > "$nexus_home/VERSION"
    write_item "[OK] Version marker written: $nexus_home/VERSION ($NEXUS_HUB_VERSION)" "$GREEN"

    mkdir -p "$bin_dest"
    local launcher_source="$repo_root/scripts/nexus-hub"
    if [ -f "$launcher_source" ]; then
        safe_copy "$launcher_source" "$bin_dest/nexus-hub" true "[OK] nexus-hub launcher installed at: $bin_dest/nexus-hub"
        chmod +x "$bin_dest/nexus-hub" 2>/dev/null || true
    fi

    # PATH hint (best-effort; never auto-edits a shell rc file).
    case ":${PATH:-}:" in
        *":$bin_dest:"*)
            write_item "[OK] $bin_dest is already on your PATH -- run: nexus-hub --version" "$GREEN"
            ;;
        *)
            # The tildes below are intentional display text in a user-facing
            # hint (shown literally as "~/.zshrc"), not paths to be expanded.
            # shellcheck disable=SC2088
            local rc="your shell profile (e.g. ~/.bashrc or ~/.zshrc)"
            # shellcheck disable=SC2088
            case "$(basename "${SHELL:-}")" in
                zsh)  rc="~/.zshrc" ;;
                bash) rc="~/.bashrc" ;;
            esac
            write_item "To use the 'nexus-hub' command, add its bin directory to your PATH." "$YELLOW"
            write_item "  Add this line to $rc, then restart your shell:" "$RESET"
            write_item "    export PATH=\"\$HOME/.nexus-hub/bin:\$PATH\"" "$CYAN"
            write_item "  Until then, run it directly: $bin_dest/nexus-hub --version" "$GRAY"
            ;;
    esac
}

# --- Project auto-seed + on-open hook (v3.11.0 Phase 7.3) ---
#
# Project-only-surface platforms (Antigravity 2.0 reads workflows/skills/rules
# ONLY from an open project's .agents/) are not served by a global-only install.
# This step (1) ships an opt-in "seed on project open" hook, and (2) seeds the
# CURRENT repo's project surfaces when a global install is run from inside a git
# work tree. Per the no-auto-rc-edit policy, the hook script is INSTALLED and its
# one-line enable is PRINTED (never written into a dotfile); the current-repo seed
# is fully automatic. Opt out with NEXUS_HUB_NO_AUTOSEED=1. Lockstep with
# Install-ProjectAutoseed in scripts/installer.ps1.
install_project_autoseed() {
    local repo_root="$1"
    local scope_label="$2"   # "Global" or "Workspace"
    local nexus_home="$HOME/.nexus-hub"
    local hooks_dest="$nexus_home/hooks"
    local runner="$repo_root/scripts/lib/integrations/runner.py"

    # A "- subsection" folded under the INSTALL VERIFICATION section: it is the
    # project-scoped follow-up to any NEEDS-ACTION hints the verify step printed.
    write_subsection_banner "Project seeding (this repo + other projects)"
    echo ""

    # Ship the on-open hook script (fail-open, idempotent, opt-out) regardless of scope.
    mkdir -p "$hooks_dest"
    local hook_src="$repo_root/scripts/nexus-hub-autoseed.sh"
    if [ -f "$hook_src" ]; then
        safe_copy "$hook_src" "$hooks_dest/nexus-hub-autoseed.sh" true "[OK] on-open hook installed at: $hooks_dest/nexus-hub-autoseed.sh"
        chmod +x "$hooks_dest/nexus-hub-autoseed.sh" 2>/dev/null || true
    fi

    # Auto-seed the current repo on a GLOBAL install run from inside a git work
    # tree (a workspace install already seeded its target). Skips the source cache
    # and honors the opt-out. (Under the curl|bash bootstrap the invocation dir may
    # be the cache; the nexus-hub init hint + the on-open hook cover that case.)
    if [ "$scope_label" = "Global" ] && [ "${NEXUS_HUB_NO_AUTOSEED:-0}" != "1" ]; then
        local py
        if [ -f "$runner" ] && py=$(resolve_python_executable 2>/dev/null); then
            local cwd; cwd="$(pwd -P 2>/dev/null || pwd)"
            case "$cwd" in
                "$nexus_home"|"$nexus_home"/*) : ;;  # never seed the source cache
                *)
                    if git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
                        write_item "Seeding project surfaces in the current repo: $cwd" "$GRAY"
                        "$py" "$runner" init --target "$cwd" --quiet >/dev/null 2>&1 || true
                        write_item "[OK] Current repo seeded (Antigravity .agents/, Cursor rules, Claude stub)." "$GREEN"
                    fi
                    ;;
            esac
        fi
    fi

    # Prominence: seeding OTHER repos, and enabling the on-open hook.
    write_item "To surface Nexus-Hub in another project, run inside it:  nexus-hub init" "$YELLOW"
    write_item "Optional 'seed on project open' hook (opt-in; the installer never edits your shell rc):" "$RESET"
    case "$(basename "${SHELL:-}")" in
        zsh)  write_item "  Add to ~/.zshrc:   source \"\$HOME/.nexus-hub/hooks/nexus-hub-autoseed.sh\"" "$CYAN" ;;
        *)    write_item "  Add to ~/.bashrc:  source \"\$HOME/.nexus-hub/hooks/nexus-hub-autoseed.sh\"" "$CYAN" ;;
    esac
    write_item "  Disable auto-seed anytime with: export NEXUS_HUB_NO_AUTOSEED=1" "$GRAY"
    echo ""
}

# --- Skill Discovery ---

install_skill_discovery() {
    local repo_root="$1"

    # --- Skill Index (all platforms) ---
    echo ""
    write_item "Installing skill index for all platforms..." "$RESET"

    local nexus_home="$HOME/.nexus-hub"
    local nexus_data="$nexus_home/data"
    mkdir -p "$nexus_data"

    local skill_index="$repo_root/data/SKILL_INDEX.md"
    if [ -f "$skill_index" ]; then
        cp "$skill_index" "$nexus_data/SKILL_INDEX.md"
        write_item "  Skill index copied to $nexus_data" "$GREEN"
    else
        write_item "  SKILL_INDEX.md not found. Run 'python infrastructure/tools/build_skills_catalog.py' first." "$YELLOW"
    fi

    # Copy skills.json and bundles.json
    [ -f "$repo_root/data/skills.json" ] && cp "$repo_root/data/skills.json" "$nexus_data/skills.json"
    [ -f "$repo_root/data/bundles.json" ] && cp "$repo_root/data/bundles.json" "$nexus_data/bundles.json"
    write_item "  Skill data installed to $nexus_data" "$GREEN"

    # --- MCP Skill Server (Claude Code only) ---
    echo ""
    write_item "MCP Skill Server (Claude Code integration)" "$RESET"

    # Check Python >= 3.10.
    # Ask the interpreter for its own version instead of parsing `--version`
    # output with grep. BSD grep (the macOS default) lacks `-P` (PCRE), so the old
    # `grep -oP` approach printed "grep: invalid option -- P" and silently left
    # python_cmd empty, skipping the entire MCP server install on macOS.
    detect_python_310() {
        local cmd ver
        for cmd in python3 python; do
            if command -v "$cmd" >/dev/null 2>&1; then
                ver=$("$cmd" -c 'import sys; print(sys.version_info[0] * 100 + sys.version_info[1])' 2>/dev/null)
                if [ -n "$ver" ] && [ "$ver" -ge 310 ]; then
                    echo "$cmd"
                    return 0
                fi
            fi
        done
        return 1
    }

    local python_cmd=""
    python_cmd=$(detect_python_310) || python_cmd=""

    # Offer to auto-install Python when it is missing or too old, mirroring the
    # Node.js auto-install flow so every dependency is handled in a single run. A
    # non-interactive run (the piped one-command bootstrap, --yes, or CI) installs
    # without asking; an interactive run prompts first. This only fires when no
    # usable Python exists, so it never shadows an existing conda/pyenv interpreter.
    if [ -z "$python_cmd" ]; then
        local py_resp=""
        if command -v brew >/dev/null 2>&1; then
            if [ "$ASSUME_YES" = true ]; then py_resp="y"; else py_resp=$(read_prompt "Python 3.10+ not found. Install it via Homebrew? [Y]es / [N]o"); fi
            if [[ "$py_resp" =~ ^[Yy] ]]; then
                write_item "  Installing Python via Homebrew..." "$RESET"
                brew install python@3.12 >/dev/null 2>&1 || true
                python_cmd=$(detect_python_310) || python_cmd=""
            fi
        elif command -v apt-get >/dev/null 2>&1; then
            if [ "$ASSUME_YES" = true ]; then py_resp="y"; else py_resp=$(read_prompt "Python 3.10+ not found. Install it via apt? [Y]es / [N]o"); fi
            if [[ "$py_resp" =~ ^[Yy] ]]; then
                write_item "  Installing Python via apt..." "$RESET"
                sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-venv python3-pip >/dev/null 2>&1 || true
                python_cmd=$(detect_python_310) || python_cmd=""
            fi
        fi
    fi

    if [ -z "$python_cmd" ]; then
        write_item "  Python 3.10+ not found. MCP server requires Python 3.10 or newer." "$YELLOW"
        write_item "  Install Python 3.10+ (macOS: brew install python@3.12; Linux: apt install python3) and re-run." "$YELLOW"
        return
    fi

    write_item "  Found $python_cmd" "$GREEN"

    # Copy MCP server source
    local mcp_src="$repo_root/extensions/nexus-skill-server"
    local mcp_dest="$nexus_home/mcp-server"
    rm -rf "$mcp_dest"
    cp -r "$mcp_src" "$mcp_dest"
    write_item "  MCP server source copied to $mcp_dest" "$GREEN"

    # Create venv and install
    local venv_path="$nexus_home/mcp-server-venv"

    if command -v uv >/dev/null 2>&1; then
        write_item "  Creating venv with uv..." "$RESET"
        uv venv "$venv_path" >/dev/null 2>&1
        uv pip install --python "$venv_path/bin/python" -e "$mcp_dest" >/dev/null 2>&1
    else
        write_item "  Creating venv with $python_cmd..." "$RESET"
        "$python_cmd" -m venv "$venv_path" >/dev/null 2>&1
        "$venv_path/bin/pip" install -q -e "$mcp_dest" >/dev/null 2>&1
    fi

    write_item "  MCP server venv created at $venv_path" "$GREEN"

    # Register in ~/.claude/settings.json
    local claude_dir="$HOME/.claude"
    local claude_settings="$claude_dir/settings.json"
    mkdir -p "$claude_dir"

    if [ ! -f "$claude_settings" ]; then
        echo '{}' > "$claude_settings"
    fi

    # Install nexus-code-search into the same venv (v1.0.0+).
    # Local-only code-search MCP. Zero outbound calls. See AGENTS.md MCP Registry Policy.
    local code_search_src="$repo_root/extensions/nexus-code-search"
    local code_search_dest="$nexus_home/code-search"
    if [ -d "$code_search_src" ]; then
        rm -rf "$code_search_dest"
        cp -r "$code_search_src" "$code_search_dest"
        # Repository-only measurement evidence must not reach user machines.
        rm -rf "$code_search_dest/benchmarks"
        if command -v uv >/dev/null 2>&1; then
            uv pip install --python "$venv_path/bin/python" -e "$code_search_dest" >/dev/null 2>&1
        else
            "$venv_path/bin/pip" install -q -e "$code_search_dest" >/dev/null 2>&1
        fi
        write_item "  nexus-code-search installed at $code_search_dest" "$GREEN"
    fi

    # Install nexus-web-fetch into the same venv (v1.0.0+).
    # Local-only web-fetch MCP (fetches user-specified URLs only). See AGENTS.md.
    local web_fetch_src="$repo_root/extensions/nexus-web-fetch"
    local web_fetch_dest="$nexus_home/web-fetch"
    if [ -d "$web_fetch_src" ]; then
        rm -rf "$web_fetch_dest"
        cp -r "$web_fetch_src" "$web_fetch_dest"
        if command -v uv >/dev/null 2>&1; then
            uv pip install --python "$venv_path/bin/python" -e "$web_fetch_dest" >/dev/null 2>&1
        else
            "$venv_path/bin/pip" install -q -e "$web_fetch_dest" >/dev/null 2>&1
        fi
        write_item "  nexus-web-fetch installed at $web_fetch_dest" "$GREEN"
    fi

    # Install nexus-context-compressor into the same venv (v3.2.0+).
    # Local-first context-compression engine. Zero outbound by default; tiktoken
    # is the only required dependency, with an offline stdlib fallback. Installed
    # with the [mcp] extra so the Phase 4 (T013) compress/retrieve MCP server runs;
    # the server is registered in the settings.json merge block below.
    # See AGENTS.md MCP Registry Policy.
    local context_compressor_src="$repo_root/extensions/nexus-context-compressor"
    local context_compressor_dest="$nexus_home/context-compressor"
    if [ -d "$context_compressor_src" ]; then
        rm -rf "$context_compressor_dest"
        cp -r "$context_compressor_src" "$context_compressor_dest"
        if command -v uv >/dev/null 2>&1; then
            uv pip install --python "$venv_path/bin/python" -e "${context_compressor_dest}[mcp]" >/dev/null 2>&1
        else
            "$venv_path/bin/pip" install -q -e "${context_compressor_dest}[mcp]" >/dev/null 2>&1
        fi
        write_item "  nexus-context-compressor installed at $context_compressor_dest" "$GREEN"
    fi

    # Install nexus-memory into the same venv (v3.19.1+). Local persistent
    # agent-memory CLI. Stdlib only, zero outbound, not an MCP server. Dest
    # is $nexus_home/nexus-memory so it does not collide with the default
    # store root $nexus_home/memory.
    local memory_src="$repo_root/extensions/nexus-memory"
    local memory_dest="$nexus_home/nexus-memory"
    if [ -d "$memory_src" ]; then
        rm -rf "$memory_dest"
        cp -r "$memory_src" "$memory_dest"
        if command -v uv >/dev/null 2>&1; then
            uv pip install --python "$venv_path/bin/python" -e "$memory_dest" >/dev/null 2>&1
        else
            "$venv_path/bin/pip" install -q -e "$memory_dest" >/dev/null 2>&1
        fi
        write_item "  nexus-memory installed at $memory_dest" "$GREEN"
    fi

    # Use python to safely merge MCP server config into settings.json (all three internal servers).
    "$python_cmd" -c "
import json, sys
path = sys.argv[1]
venv = sys.argv[2]
hub = sys.argv[3]
with open(path, 'r') as f:
    data = json.load(f)
if 'mcpServers' not in data:
    data['mcpServers'] = {}
data['mcpServers']['nexus-skill-server'] = {
    'command': venv + '/bin/python',
    'args': ['-m', 'nexus_skill_server'],
    'env': {'NEXUS_HUB_ROOT': hub}
}
data['mcpServers']['nexus-code-search'] = {
    'command': venv + '/bin/python',
    'args': ['-m', 'nexus_code_search'],
    'env': {'NEXUS_HUB_ROOT': hub}
}
data['mcpServers']['nexus-web-fetch'] = {
    'command': venv + '/bin/python',
    'args': ['-m', 'nexus_web_fetch'],
    'env': {'NEXUS_HUB_ROOT': hub}
}
data['mcpServers']['nexus-context-compressor'] = {
    'command': venv + '/bin/python',
    'args': ['-m', 'nexus_context_compressor', 'serve'],
    'env': {'NEXUS_HUB_ROOT': hub}
}
# Remove superseded legacy (devai-hub) MCP entries left by pre-rename installs;
# they are replaced one-for-one by the nexus-* servers registered above.
for legacy in ('devai-skill-server', 'devai-code-search', 'devai-web-fetch'):
    data['mcpServers'].pop(legacy, None)
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
" "$claude_settings" "$venv_path" "$nexus_home"

    write_item "  MCP servers registered in $claude_settings (nexus-skill-server, nexus-code-search, nexus-web-fetch, nexus-context-compressor)" "$GREEN"
    write_item "  Servers will auto-start with Claude Code. No manual steps needed." "$GREEN"
}

# --- Banner ---

# ASCII-art NEXUS-HUB wordmark. Printed at startup ahead of the welcome banner.
# Constraints: <=80 columns wide, <=8 rows tall, ASCII-only (no Unicode block
# characters - commit messages and source files are ASCII-only on Windows per
# project rules). Modeled after the Claude Code CLI banner style.
print_nexus_banner() {
    echo ""
    echo -e "${CYAN}"
    cat <<'NEXUS_BANNER_EOF'
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗      ██╗  ██╗██╗   ██╗██████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝      ██║  ██║██║   ██║██╔══██╗
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗█████╗███████║██║   ██║██████╔╝
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║╚════╝██╔══██║██║   ██║██╔══██╗
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║      ██║  ██║╚██████╔╝██████╔╝
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝      ╚═╝  ╚═╝ ╚═════╝ ╚═════╝
NEXUS_BANNER_EOF
    echo -e "${RESET}"
    echo -e "  ${GRAY}Multi-platform AI skill harness  -  v${NEXUS_HUB_VERSION}  -  https://github.com/bendourthe/Nexus-Hub${RESET}"
    echo ""
}

# Detects an existing ~/.devai-hub/ install and migrates it to ~/.nexus-hub/.
# One-shot, one-way per the backward-compat decision in
# docs/archive/v2/v2.0/rename-decisions.md. The installer does NOT ship a symlink or
# compatibility shim. Three branches:
#   1. legacy only            -> prompt to migrate (default Y), then `mv`.
#   2. legacy AND new co-exist -> ask user: keep-new, abort, or merge.
#   3. neither / new only      -> no-op (fresh or already-migrated install).
# Uninstalls the legacy DevAI-Hub VS Code extension if present. The
# Claude Usage Monitor was published under `devai-hub.claude-usage-monitor`
# before the rename; the current build ships as `nexus-hub.claude-usage-monitor`.
# Leaving both installed produces a duplicate entry in VS Code's Extensions
# pane and two status-bar items. Called unconditionally at startup -- the
# function silently no-ops when nothing legacy is installed, so it is safe
# (and necessary) to re-run on every install, including for users who
# migrated ~/.devai-hub/ in an earlier installer run.
remove_legacy_vscode_extensions() {
    # nexus-hub.github-usage-monitor was WITHDRAWN in v3.18.2. It reconstructed the
    # included-usage meter from data GitHub does not publish, and could report a
    # confident 0% against an exhausted allowance. Leaving it installed keeps that
    # wrong number on a user's status bar forever, so it is actively uninstalled
    # rather than merely unshipped.
    local legacy_ids=("devai-hub.claude-usage-monitor" "nexus-hub.github-usage-monitor")

    # Both hosts, not just VS Code. The GitHub monitor was the one dual-host
    # monitor, installed to Cursor as well, so a VS Code-only sweep would leave the
    # Cursor copy running.
    local cli emitted=0
    for cli in code cursor; do
        command -v "$cli" >/dev/null 2>&1 || continue
        local installed
        installed=$("$cli" --list-extensions 2>/dev/null) || continue
        local id
        for id in "${legacy_ids[@]}"; do
            if printf '%s
' "$installed" | grep -qx "$id"; then
                if [ "$emitted" -eq 0 ]; then echo ""; fi
                echo -e "  ${YELLOW}Removing retired extension from $cli: $id${RESET}"
                if "$cli" --uninstall-extension "$id" >/dev/null 2>&1; then
                    echo -e "  ${GREEN}[OK] Removed $id from $cli${RESET}"
                else
                    echo -e "  ${YELLOW}Could not auto-remove $id (uninstall it manually from $cli)${RESET}"
                fi
                emitted=1
            fi
        done
    done
    if [ "$emitted" -eq 1 ]; then echo ""; fi
}

migrate_legacy_install() {
    local legacy="$HOME/.devai-hub"
    local current="$HOME/.nexus-hub"

    if [ -d "$legacy" ] && [ ! -d "$current" ]; then
        echo ""
        echo -e "  ${YELLOW}Detected existing DevAI-Hub install at $legacy${RESET}"
        echo -ne "  ${YELLOW}Migrate to Nexus-Hub ($current)? [Y/n]: ${RESET}"
        local ans
        read -r ans
        ans=${ans:-Y}
        if [[ "$ans" =~ ^[Yy] ]]; then
            mv "$legacy" "$current"
            echo -e "  ${GREEN}Migrated $legacy -> $current${RESET}"
        else
            echo -e "  ${RED}Migration declined. Remove $legacy manually or rerun and accept.${RESET}"
            exit 1
        fi
        echo ""
    elif [ -d "$legacy" ] && [ -d "$current" ]; then
        echo ""
        echo -e "  ${YELLOW}Both $legacy and $current exist.${RESET}"
        echo -e "  Choose: [k]eep new + delete old, [a]bort + handle manually, [m]erge (best effort)"
        echo -ne "  ${YELLOW}Selection [k/a/m]: ${RESET}"
        local ans
        read -r ans
        case "$ans" in
            [Kk]*)
                rm -rf "$legacy"
                echo -e "  ${GREEN}Removed $legacy. Keeping $current.${RESET}"
                ;;
            [Mm]*)
                cp -R "$legacy"/. "$current"/
                rm -rf "$legacy"
                echo -e "  ${GREEN}Merged $legacy into $current (best effort).${RESET}"
                ;;
            *)
                echo -e "  ${RED}Aborted. Resolve $legacy and $current manually before rerunning.${RESET}"
                exit 1
                ;;
        esac
        echo ""
    fi
}

print_banner() {
    # The Nexus-Hub Universal Installer welcome line. The ASCII wordmark above
    # (and migrate_legacy_install when active) already produces a trailing
    # blank line, so this function deliberately does not add its own leading
    # blank. Title text is preserved for the installer-smoke test contract.
    echo -e "${CYAN}Welcome to the Nexus-Hub Universal Installer (v${NEXUS_HUB_VERSION})${RESET}"
}

# --- Main ---

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# --- Flag parsing (v2.2.0+) ----------------------------------------------
# Currently supported:
#   --enterprise        Opt in to the standalone Gemini CLI install path. After
#                       2026-06-18, Gemini CLI only serves enterprise tenants
#                       with a paid Gemini API key (per the 2026-05-21 Google
#                       Developers Blog announcement). Non-enterprise users
#                       install Antigravity CLI instead.
#   -h | --help         Show usage and exit.
ENTERPRISE=0
SUBCOMMAND=""
SUBCOMMAND_ARGS=()
BRANCH_NAME=""
PASSTHRU_ARGS=()

# v3.7.0 / Phase 2 -- no-prompt install controls.
WORKSPACE_PATH=""   # set by --workspace <path>; empty => global scope (default)
PLATFORMS_ARG=""    # set by --platforms <csv>; empty => all platforms (default)
YES_FLAG=0          # --yes : non-interactive, auto-confirm + refresh
FORCE_FLAG=0        # --force : overwrite existing managed files without asking

# v3.15.6 / AC5 -- opt-in hardened permission posture.
# Default 0 keeps the convenience default (allow-only auto-approve, no prompts)
# exactly as it was. With --strict-permissions the installer ALSO merges the
# deny/ask overlay from configs/permissions/claude-permissions-strict.json.
STRICT_PERMISSIONS=0

# Map an arbitrary git branch name to a filesystem-safe cache token: every
# character outside [A-Za-z0-9._-] becomes '-', parent-dir tokens are
# neutralized, and a leading dot/dash is stripped so the result is never a
# hidden dir or a path-traversal vector.
sanitize_branch_name() {
    local raw="$1" s
    s="${raw//[!A-Za-z0-9._-]/-}"
    s="${s//../-}"
    s="${s#[-.]}"
    [ -n "$s" ] || s="branch"
    printf '%s' "$s"
}

show_installer_usage() {
    cat <<EOF
Usage:
  bash scripts/installer.sh [--workspace PATH] [--platforms LIST] [--yes]
                            [--profile ID] [--modules LIST] [--bundles LIST]
                            [--force] [--enterprise] [-h | --help]
  bash scripts/installer.sh init [--target PATH] [--dry-run]
  bash scripts/installer.sh --print-config <integration-key>
  bash scripts/installer.sh --check
  bash scripts/installer.sh --branch <name> [--enterprise]

By default the installer runs with NO prompts: a global install across ALL
supported platforms (absent platforms skip-with-note). Existing managed files
that you have customized are detected and you are asked ONCE whether to
overwrite them; with --yes / --force (or any non-interactive / piped run) they
are refreshed to the latest version automatically.

Subcommands:
  init           Bootstrap project-local surfaces (Cursor rules, Claude
                 settings.json stub) from a global install. Walks every
                 registered integration that defines wire_project_surfaces()
                 and writes the corresponding files. --target defaults to the
                 current directory.
  doctor         Preflight: verify that every surface the platform read-contract
                 promises actually exists on this machine, per detected platform.
                 READ-ONLY. Exits 0 when every detected platform is complete, 1
                 when any is missing a promised surface, and 2 when the contract
                 itself cannot be read (never a false CLEAR). Accepts --target
                 PATH for the project-scoped checks and --repair to print the
                 remediation commands without running them.

Read-only modes (no disk writes):
  --print-config <key>  Dump the Markdown readout of what the given integration
                        would install. Use --print-config=<key> or
                        --print-config <key>.
  --check               Dry-run every integration and exit non-zero if any
                        action would create / update / remove a file. Useful in
                        CI to detect install drift.

Options:
  --workspace <path>  Install into a single project directory instead of the
                 default global (all-projects) scope. Use --workspace=<path> or
                 --workspace <path>.
  --platforms <list>  Install only the given comma-separated integration keys
                 instead of all platforms. Valid keys: claude, codex, gemini,
                 antigravity2, gemini-cli, copilot, cursor, opencode, nexus-ai,
                 aider, windsurf, kimi, qwen, openclaw. Use --platforms=<list>
                 or --platforms <list>.
  --profile <id>      Install one profile instead of the whole catalog:
                 minimal, core, or full. Default (no selector) is full.
  --modules <list>    Install the given comma-separated capability modules.
                 Repeatable; --modules a,b and --modules a --modules b are
                 equivalent.
  --bundles <list>    Install the given comma-separated role bundles. Repeatable.
                 Selectors combine by union: --profile core --modules ai-engineering
                 installs both. --profile full cannot be combined with others.
                 Hooks, rules, templates, and settings install under EVERY
                 selection; only skills and their dependent commands and agents
                 are filtered. Selectors need Python; a full install does not.
  --yes, -y      Non-interactive: never prompt, and refresh existing managed
                 files to the latest version (also implied when stdin is not a
                 TTY, e.g. a piped curl|bash install).
  --force        Overwrite existing managed files with the Nexus-Hub version
                 without asking (implies --yes for prompting).
  --enterprise   Install the standalone Gemini CLI integration. Requires a paid
                 Gemini API key. After 2026-06-18 (per the 2026-05-21 Google
                 Developers Blog announcement), Gemini CLI stops serving free /
                 Google AI Pro / Ultra / GitHub-installed users; this flag is
                 the only way to keep the integration after that date.
                 Default (without --enterprise): the installer prints a sunset
                 warning and skips the Gemini CLI install, but still installs
                 Antigravity CLI (which covers the same functionality via the
                 antigravity2 integration).
  --strict-permissions
                 Install the OPT-IN hardened Claude Code permission posture in
                 addition to the read-only auto-approve list: deny/ask entries
                 for the execution-trigger config surfaces (version-control
                 hooks and config, interpreter paths, harness and editor config)
                 from configs/permissions/claude-permissions-strict.json.
                 Without this flag the install is unchanged (allow-only,
                 no-prompt). This is a deliberate posture split: convenience by
                 default, hardened on request.
  --branch <name>  Install the catalog from a pushed branch instead of the
                 current checkout. Shallow-clones the repo at <name> into a
                 deterministic cache directory (~/.nexus-hub/branches/<name>/),
                 then runs the install from that checkout -- the user's working
                 copy is never touched. Combine with --check / --dry-run to
                 print the resolved cache path and clone source without cloning
                 (a probe). Use --branch=<name> or --branch <name>.
  -h, --help     Show this help and exit.
EOF
}

# --- nexus-hub doctor (v3.16.2 Phase 5) ---------------------------------
#
# Preflight that answers the question the installer never could: did the install
# actually land where the read-contract promises? Verifies each DETECTED
# platform's surfaces against the `install_verify` block of
# docs/policy/platform-read-contracts.json.
#
# NETWORK: none. This function makes no outbound call of any kind, which is what
# keeps it `re-full` under the MCP Registry Policy. Do not add one.
#
# READ-ONLY: it never writes, moves, or deletes. --repair prints the remediation
# command for each failing platform and explicitly does NOT execute it; a
# diagnostic that mutates an install is how a preflight becomes the thing that
# breaks you.
#
# Three states are kept distinct, because collapsing them is what makes a doctor
# untrustworthy:
#   SKIP  platform absent from this machine    -> not a failure
#   PASS  platform present, every surface there
#   FAIL  platform present, a promised surface missing or empty
#
# Exit codes: 0 all detected platforms complete; 1 at least one FAIL; 2 the
# contract could not be read or parsed. A checker that cannot read its own
# contract must fail LOUDLY rather than report a false CLEAR.
doctor_contract_path() {
    # NEXUS_DOCTOR_CONTRACT pins the contract explicitly. It exists so the
    # unreadable-contract path is testable (REPO_ROOT is derived from the script
    # location, so a test cannot otherwise steer the lookup) and so an operator
    # can point the doctor at a specific contract. When set, it is used even if
    # it does not exist -- an override that silently fell back to the repo copy
    # would make the fail-loud path untestable, which is the defect this whole
    # subcommand exists to avoid.
    if [ -n "${NEXUS_DOCTOR_CONTRACT:-}" ]; then
        printf '%s\n' "$NEXUS_DOCTOR_CONTRACT"
        [ -f "$NEXUS_DOCTOR_CONTRACT" ] && return 0
        return 1
    fi
    # Repo checkout first, then the two locations the install bootstrap uses.
    local candidate
    for candidate in \
        "$REPO_ROOT/docs/policy/platform-read-contracts.json" \
        "$HOME/.nexus-hub/src/docs/policy/platform-read-contracts.json" \
        "$HOME/.nexus-hub/docs/policy/platform-read-contracts.json"; do
        if [ -f "$candidate" ]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

# Flatten the install_verify block into tab-separated records the shell logic
# below consumes. Only the JSON TOKENIZATION is delegated; every decision (path
# resolution, surface evaluation, state classification, exit code) is made in
# this script.
#
# jq is preferred; Python is the fallback and is already a hard dependency of
# the init / --check / --print-config subcommands, so this adds none. When
# NEITHER is available we exit 2 rather than skipping the check: silently
# allowing is how catalog/hooks/secret-scan.sh became inert on a jq-less host
# (v3.16.2 BG-2), and a preflight repeating that defect would be worse than
# having no preflight at all.
doctor_flatten_contract() {
    local json="$1"
    if command -v jq >/dev/null 2>&1; then
        jq -r '
            .install_verify[]
            | . as $e
            | ($e.detect // [] | join("|")) as $detect
            | ($e.remediation // "") as $rem
            | ($e.surfaces // [])[]
            | [$e.label, $detect, $rem, .label, .kind, .path, (.needle // "")]
            | @tsv
        ' "$json" 2>/dev/null && return 0
        return 1
    fi
    local py
    if py=$(resolve_python_executable); then
        "$py" -c '
import json, sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
entries = data["install_verify"]
if not isinstance(entries, list):
    raise SystemExit(1)
for e in entries:
    detect = "|".join(e.get("detect", []))
    rem = e.get("remediation", "") or ""
    for s in e.get("surfaces", []):
        print("\t".join([
            e.get("label", "?"), detect, rem,
            s.get("label", "?"), s.get("kind", ""),
            s.get("path", ""), s.get("needle", "") or "",
        ]))
' "$json" 2>/dev/null && return 0
        return 1
    fi
    return 1
}

# Resolve a contract path token: `~/` -> $HOME, `{project}/` -> target root.
#
# Written with prefix-stripping rather than a `case "~/"*)` pattern on purpose.
# The tilde here is DATA (it is the literal first character of the contract's
# path spec), not a shell home reference, and matching it as a quoted glob trips
# ShellCheck SC2088 -- which CI runs at --severity=warning over this file. The
# honest fix is to not write the construct, rather than to disable the warning.
doctor_resolve_path() {
    local spec="$1" target_root="$2" stripped
    stripped="${spec#\~/}"
    if [ "$stripped" != "$spec" ]; then
        printf '%s\n' "$HOME/$stripped"
        return 0
    fi
    stripped="${spec#\{project\}/}"
    if [ "$stripped" != "$spec" ]; then
        printf '%s\n' "$target_root/$stripped"
        return 0
    fi
    printf '%s\n' "$spec"
}

# Evaluate one surface. Returns 0 when the surface is satisfied.
doctor_check_surface() {
    local kind="$1" path="$2" needle="$3"
    case "$kind" in
        nonempty_dir)
            [ -d "$path" ] || return 1
            # A directory that exists but is empty is a FAILED surface, not a
            # passing one: an empty skills dir surfaces nothing to the platform.
            [ -n "$(ls -A "$path" 2>/dev/null || true)" ] || return 1
            return 0
            ;;
        is_file)
            [ -f "$path" ] || return 1
            return 0
            ;;
        file_contains)
            [ -f "$path" ] || return 1
            grep -qF -- "$needle" "$path" 2>/dev/null || return 1
            return 0
            ;;
        *)
            # An unknown kind is a contract the doctor does not understand.
            # Treat it as a failure so a contract addition cannot silently
            # widen the set of things reported CLEAR.
            return 1
            ;;
    esac
}

run_doctor() {
    local target_root="$PWD" show_repair=0
    while [ $# -gt 0 ]; do
        case "$1" in
            --target)  target_root="${2:-}"; shift 2 ;;
            --target=*) target_root="${1#--target=}"; shift ;;
            --repair)  show_repair=1; shift ;;
            *) echo "doctor: unknown argument: $1" >&2; return 2 ;;
        esac
    done

    local json
    if ! json=$(doctor_contract_path); then
        echo "[doctor] FATAL: platform read-contract not found." >&2
        echo "         Looked in the repo checkout and ~/.nexus-hub/." >&2
        echo "         Refusing to report a result without the contract." >&2
        return 2
    fi

    local flat
    if ! flat=$(doctor_flatten_contract "$json"); then
        echo "[doctor] FATAL: could not parse $json" >&2
        echo "         Install jq or ensure python3 is on PATH, then re-run." >&2
        echo "         Refusing to report CLEAR on an unreadable contract." >&2
        return 2
    fi
    if [ -z "$flat" ]; then
        echo "[doctor] FATAL: install_verify block is empty or missing in $json" >&2
        return 2
    fi

    echo "[doctor] contract: $json"
    echo "[doctor] project:  $target_root"
    echo ""

    local cur_label="" detect="" remediation="" surfaces="" any_fail=0
    local n_pass=0 n_fail=0 n_skip=0
    local -a repair_lines=()

    # Emit the verdict for one platform once all of its surfaces are collected.
    doctor_emit() {
        [ -n "$cur_label" ] || return 0
        local detected=0 d
        local old_ifs="$IFS"
        IFS='|'
        for d in $detect; do
            [ -n "$d" ] || continue
            if [ -e "$(doctor_resolve_path "$d" "$target_root")" ]; then
                detected=1
                break
            fi
        done
        IFS="$old_ifs"
        if [ "$detected" -eq 0 ]; then
            printf '  SKIP  %-38s not installed on this machine\n' "$cur_label"
            n_skip=$((n_skip + 1))
            return 0
        fi
        if printf '%s' "$surfaces" | grep -q 'MISSING'; then
            printf '  FAIL  %-38s %s\n' "$cur_label" "$surfaces"
            [ -n "$remediation" ] && printf '        -> %s\n' "$remediation"
            [ -n "$remediation" ] && repair_lines+=("$cur_label: $remediation")
            n_fail=$((n_fail + 1))
            any_fail=1
        else
            printf '  PASS  %-38s %s\n' "$cur_label" "$surfaces"
            n_pass=$((n_pass + 1))
        fi
    }

    local label det rem s_label s_kind s_path s_needle resolved state
    while IFS=$'\t' read -r label det rem s_label s_kind s_path s_needle; do
        # Strip a trailing CR from the final field. Python's print() emits CRLF
        # on a Windows host, so the last TSV column arrives as "Skill Index\r"
        # and every `file_contains` surface would be reported MISSING while the
        # PowerShell sibling reported it ok -- a silent cross-platform
        # divergence of exactly the shape docs/incidents/shapes.md S-1 names.
        # Caught by running both implementations and diffing, which is why that
        # parity run is a requirement and not a formality.
        s_needle="${s_needle%$'\r'}"
        [ -n "$label" ] || continue
        if [ "$label" != "$cur_label" ]; then
            doctor_emit
            cur_label="$label"; detect="$det"; remediation="$rem"; surfaces=""
        fi
        resolved="$(doctor_resolve_path "$s_path" "$target_root")"
        if doctor_check_surface "$s_kind" "$resolved" "$s_needle"; then
            state="ok"
        else
            state="MISSING"
        fi
        if [ -z "$surfaces" ]; then
            surfaces="$s_label:$state"
        else
            surfaces="$surfaces, $s_label:$state"
        fi
    done <<EOF
$flat
EOF
    doctor_emit

    echo ""
    echo "[doctor] $n_pass complete, $n_fail incomplete, $n_skip not installed."

    if [ "$any_fail" -eq 1 ]; then
        if [ "$show_repair" -eq 1 ]; then
            echo ""
            echo "[doctor] --repair: the following would fix the failures above."
            echo "[doctor] NOTHING WAS CHANGED. Run these yourself:"
            local line
            for line in "${repair_lines[@]}"; do
                echo "         $line"
            done
        else
            echo "[doctor] re-run with --repair to print the remediation commands."
        fi
        return 1
    fi
    echo "[doctor] every detected platform surfaces the catalog."
    return 0
}

PRINT_CONFIG_KEY=""
CHECK_MODE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --enterprise)
            ENTERPRISE=1
            PASSTHRU_ARGS+=("--enterprise")
            shift
            ;;
        --strict-permissions)
            STRICT_PERMISSIONS=1
            PASSTHRU_ARGS+=("--strict-permissions")
            shift
            ;;
        --workspace)
            WORKSPACE_PATH="${2:-}"
            if [ -z "$WORKSPACE_PATH" ]; then
                echo "--workspace requires a path" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--workspace" "$WORKSPACE_PATH")
            shift 2
            ;;
        --workspace=*)
            WORKSPACE_PATH="${1#--workspace=}"
            if [ -z "$WORKSPACE_PATH" ]; then
                echo "--workspace requires a path" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--workspace=$WORKSPACE_PATH")
            shift
            ;;
        --platforms)
            PLATFORMS_ARG="${2:-}"
            if [ -z "$PLATFORMS_ARG" ]; then
                echo "--platforms requires a comma-separated list" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--platforms" "$PLATFORMS_ARG")
            shift 2
            ;;
        --platforms=*)
            PLATFORMS_ARG="${1#--platforms=}"
            if [ -z "$PLATFORMS_ARG" ]; then
                echo "--platforms requires a comma-separated list" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--platforms=$PLATFORMS_ARG")
            shift
            ;;
        --profile)
            SELECT_PROFILE="${2:-}"
            if [ -z "$SELECT_PROFILE" ]; then
                echo "--profile requires a profile id" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--profile" "$SELECT_PROFILE")
            shift 2
            ;;
        --profile=*)
            SELECT_PROFILE="${1#--profile=}"
            if [ -z "$SELECT_PROFILE" ]; then
                echo "--profile requires a profile id" >&2
                exit 2
            fi
            PASSTHRU_ARGS+=("--profile=$SELECT_PROFILE")
            shift
            ;;
        --modules)
            if [ -z "${2:-}" ]; then
                echo "--modules requires a comma-separated list" >&2
                exit 2
            fi
            SELECT_MODULES="${SELECT_MODULES:+$SELECT_MODULES,}$2"
            PASSTHRU_ARGS+=("--modules" "$2")
            shift 2
            ;;
        --modules=*)
            if [ -z "${1#--modules=}" ]; then
                echo "--modules requires a comma-separated list" >&2
                exit 2
            fi
            SELECT_MODULES="${SELECT_MODULES:+$SELECT_MODULES,}${1#--modules=}"
            PASSTHRU_ARGS+=("$1")
            shift
            ;;
        --bundles)
            if [ -z "${2:-}" ]; then
                echo "--bundles requires a comma-separated list" >&2
                exit 2
            fi
            SELECT_BUNDLES="${SELECT_BUNDLES:+$SELECT_BUNDLES,}$2"
            PASSTHRU_ARGS+=("--bundles" "$2")
            shift 2
            ;;
        --bundles=*)
            if [ -z "${1#--bundles=}" ]; then
                echo "--bundles requires a comma-separated list" >&2
                exit 2
            fi
            SELECT_BUNDLES="${SELECT_BUNDLES:+$SELECT_BUNDLES,}${1#--bundles=}"
            PASSTHRU_ARGS+=("$1")
            shift
            ;;
        --yes|-y)
            YES_FLAG=1
            PASSTHRU_ARGS+=("--yes")
            shift
            ;;
        --force)
            FORCE_FLAG=1
            PASSTHRU_ARGS+=("--force")
            shift
            ;;
        --branch)
            BRANCH_NAME="${2:-}"
            if [ -z "$BRANCH_NAME" ]; then
                echo "--branch requires a branch name" >&2
                exit 2
            fi
            shift 2
            ;;
        --branch=*)
            BRANCH_NAME="${1#--branch=}"
            if [ -z "$BRANCH_NAME" ]; then
                echo "--branch requires a branch name" >&2
                exit 2
            fi
            shift
            ;;
        --print-config)
            PRINT_CONFIG_KEY="${2:-}"
            if [ -z "$PRINT_CONFIG_KEY" ]; then
                echo "--print-config requires an integration key" >&2
                exit 2
            fi
            shift 2
            ;;
        --print-config=*)
            PRINT_CONFIG_KEY="${1#--print-config=}"
            shift
            ;;
        --check|--dry-run)
            CHECK_MODE=1
            shift
            ;;
        -h|--help)
            show_installer_usage
            exit 0
            ;;
        init)
            SUBCOMMAND="init"
            shift
            SUBCOMMAND_ARGS=("$@")
            break
            ;;
        doctor)
            SUBCOMMAND="doctor"
            shift
            SUBCOMMAND_ARGS=("$@")
            break
            ;;
        *)
            echo "Unknown installer flag: $1" >&2
            show_installer_usage >&2
            exit 2
            ;;
    esac
done

# --- Branch-based install (v2.4.0+) --------------------------------------
# When --branch <name> is given, install the catalog from a shallow clone of
# that pushed branch in a deterministic cache dir, leaving the user's working
# copy untouched. NEXUS_HUB_BRANCH_RESOLVED guards against re-cloning once we
# have re-exec'd into the cached checkout. This block runs before the read-only
# dispatch so that --branch + --check is a clone-free probe.
if [ -n "$BRANCH_NAME" ] && [ "${NEXUS_HUB_BRANCH_RESOLVED:-0}" != "1" ]; then
    branch_token="$(sanitize_branch_name "$BRANCH_NAME")"
    branch_cache_dir="$HOME/.nexus-hub/branches/$branch_token"
    branch_src_url="$(git -C "$REPO_ROOT" config --get remote.origin.url 2>/dev/null || true)"
    [ -n "$branch_src_url" ] || branch_src_url="file://$REPO_ROOT"

    if [ "$CHECK_MODE" = "1" ]; then
        # Probe: print the resolution and exit without cloning or installing.
        echo "nexus-hub branch install (dry-run):"
        echo "  branch:    $BRANCH_NAME"
        echo "  sanitized: $branch_token"
        echo "  source:    $branch_src_url"
        echo "  cache dir: $branch_cache_dir"
        exit 0
    fi

    if ! command -v git >/dev/null 2>&1; then
        echo "git is required for --branch installs but was not found on PATH." >&2
        exit 2
    fi

    echo "Installing Nexus-Hub from branch '$BRANCH_NAME' (cache: $branch_cache_dir)..."
    mkdir -p "$(dirname "$branch_cache_dir")"
    if [ -d "$branch_cache_dir/.git" ]; then
        git -C "$branch_cache_dir" fetch --depth 1 origin "$BRANCH_NAME" \
            && git -C "$branch_cache_dir" checkout -f FETCH_HEAD \
            || { echo "Failed to refresh branch cache at $branch_cache_dir" >&2; exit 2; }
    else
        rm -rf "$branch_cache_dir"
        git clone --depth 1 --branch "$BRANCH_NAME" "$branch_src_url" "$branch_cache_dir" \
            || { echo "Failed to clone branch '$BRANCH_NAME' from $branch_src_url" >&2; exit 2; }
    fi

    cached_installer="$branch_cache_dir/scripts/installer.sh"
    if [ ! -f "$cached_installer" ]; then
        echo "Cached checkout has no scripts/installer.sh at $cached_installer" >&2
        exit 2
    fi
    exec env NEXUS_HUB_BRANCH_RESOLVED=1 bash "$cached_installer" ${PASSTHRU_ARGS[@]+"${PASSTHRU_ARGS[@]}"}
fi

# Dispatch read-only subcommands BEFORE the interactive banner so they remain
# pipeable / scriptable.
# `doctor` is self-contained: it reads the contract and evaluates every surface
# in this script, so it runs even where the Python runner is unavailable.
if [ "$SUBCOMMAND" = "doctor" ]; then
    run_doctor "${SUBCOMMAND_ARGS[@]+"${SUBCOMMAND_ARGS[@]}"}"
    exit $?
fi

if [ "$SUBCOMMAND" = "init" ] || [ -n "$PRINT_CONFIG_KEY" ] || [ "$CHECK_MODE" = "1" ]; then
    runner="$REPO_ROOT/scripts/lib/integrations/runner.py"
    if [ ! -f "$runner" ]; then
        echo "Runner not found at $runner" >&2
        exit 2
    fi
    if ! py=$(resolve_python_executable); then
        echo "Python not found on PATH; cannot run read-only subcommand." >&2
        exit 2
    fi
    if [ "$SUBCOMMAND" = "init" ]; then
        # v3.15.6 / HO-2: declare installer-owned intent for the
        # escalation-trigger carve-out, which suppresses the sensitive-path
        # advisory for the project surfaces `init` legitimately writes
        # (.claude/settings.json, .cursor/rules, .agents/, .github/skills).
        #
        # Scope this honestly. Claude Code's PreToolUse Write/Edit hooks observe
        # the AGENT's tool calls, not this process, so `init`'s own writes never
        # reach that hook and were never going to warn. What this export buys is
        # an explicit, greppable intent marker for any hook chain that DOES wrap
        # the installer, and consistency with the PowerShell installer. The
        # carve-out's practical consumer is an operator exporting the same
        # variable for a deliberate setup pass in an agent session.
        #
        # It is NOT a security control: an agent can set this variable itself, so
        # it is a self-asserted signal. That is acceptable only because the hook
        # is advisory, so the carve-out suppresses a warning and never grants a
        # capability. Do not promote it to a boundary.
        export NEXUS_HUB_INIT=1
        exec "$py" "$runner" init "${SUBCOMMAND_ARGS[@]}"
    elif [ -n "$PRINT_CONFIG_KEY" ]; then
        exec "$py" "$runner" print-config "$PRINT_CONFIG_KEY"
    else
        exec "$py" "$runner" check
    fi
fi

# --- Resolve no-prompt install configuration (v3.7.0 / Phase 2) ----------
# Validate --platforms into the space-delimited PLATFORMS_FILTER (empty = all).
if [ -n "$PLATFORMS_ARG" ]; then
    known_platform_keys="claude codex gemini antigravity2 gemini-cli copilot cursor opencode nexus-ai aider windsurf kimi qwen openclaw"
    PLATFORMS_FILTER=""
    IFS=',' read -ra _requested_platforms <<< "$PLATFORMS_ARG"
    for _pk in "${_requested_platforms[@]}"; do
        _pk="$(printf '%s' "$_pk" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
        [ -z "$_pk" ] && continue
        case " $known_platform_keys " in
            *" $_pk "*) PLATFORMS_FILTER="$PLATFORMS_FILTER $_pk" ;;
            *)
                echo "Unknown platform key: '$_pk'" >&2
                echo "Valid keys: $known_platform_keys" >&2
                exit 2
                ;;
        esac
    done
    PLATFORMS_FILTER="$(printf '%s' "$PLATFORMS_FILTER" | sed 's/^ *//;s/ *$//')"
    if [ -z "$PLATFORMS_FILTER" ]; then
        echo "--platforms produced an empty platform set" >&2
        exit 2
    fi
fi

# --- Resolve the install selection (v3.16.1 Phase 6.1) -------------------
# Deliberately placed beside the --platforms validation above and BEFORE any
# write: an invalid selector must never leave a half-installed tree. A run with
# no selector returns immediately and takes the identical path it always did.
resolve_selection "$REPO_ROOT"
trap cleanup_selection_stage EXIT
if [ "$SELECTION_ACTIVE" = "1" ]; then
    echo ""
    echo "Selection: ${SELECTION_SKILL_COUNT} skills, ${SELECTION_COMMAND_COUNT} commands, ${SELECTION_AGENT_COUNT} agents"
    echo "           ${SELECTION_HASH}"
fi

# Resolve the assume-yes / overwrite decision. --yes or --force force it; a
# non-interactive stdin (piped curl|bash, CI) also implies it. In that case
# existing managed files are refreshed silently; otherwise interactive conflicts
# are collected and resolved once via resolve_conflicts().
if [ "$YES_FLAG" = 1 ] || [ "$FORCE_FLAG" = 1 ] || [ ! -t 0 ]; then
    ASSUME_YES=true
    OVERWRITE_ALL=true
else
    ASSUME_YES=false
    OVERWRITE_ALL=false
fi

print_nexus_banner
migrate_legacy_install
# Idempotent cleanup -- safe to run every install. Catches the case where the
# user already migrated ~/.devai-hub/ in an earlier run (before this cleanup
# existed) but still has devai-hub.claude-usage-monitor installed in VS Code.
remove_legacy_vscode_extensions
print_banner

# Scope is resolved from --workspace (no interactive scope/platform prompt).
# Default = global install across all platforms.
if [ -n "$WORKSPACE_PATH" ]; then
    SCOPE_LABEL="Workspace"
    # Strip pasted surrounding quotes and expand a leading tilde.
    WORKSPACE_PATH="${WORKSPACE_PATH%\"}"
    WORKSPACE_PATH="${WORKSPACE_PATH#\"}"
    WORKSPACE_PATH="${WORKSPACE_PATH/#\~/$HOME}"
    if [ ! -d "$WORKSPACE_PATH" ]; then
        echo "Workspace path not found: $WORKSPACE_PATH" >&2
        exit 2
    fi
    install_workspace "$REPO_ROOT" "$WORKSPACE_PATH"
else
    SCOPE_LABEL="Global"
    install_global "$REPO_ROOT"
fi

# CROSS-PLATFORM TOOLS: for a global install this header (plus the skill-discovery
# and git-hook subsections) was already opened inside install_global; a workspace
# install skips those global-only tools, so open the header here so the report
# templates below still render under a section rather than orphaned.
if [ "$SCOPE_LABEL" = "Workspace" ]; then write_section_banner "CROSS-PLATFORM TOOLS"; fi

# Bundled report-generator templates + scripts are user-scope and always install silently.
# Interactive custom-template import moved to /research report at use time (v0.9.7).
install_templates "$REPO_ROOT"

# Install the nexus-hub CLI launcher + version marker (v3.7.0 Phase 3).
install_cli_launcher "$REPO_ROOT"

# --- INSTALL VERIFICATION (with project seeding folded in) ---
# Post-install per-platform verification (v3.11.0 Phase 7.4): report PASS /
# NEEDS-ACTION per detected platform against its real read-path (advisory; never
# fails the install).
write_section_banner "INSTALL VERIFICATION"
if [ -f "$REPO_ROOT/scripts/lib/integrations/runner.py" ]; then
    if py=$(resolve_python_executable 2>/dev/null); then
        "$py" "$REPO_ROOT/scripts/lib/integrations/runner.py" verify --target "$(pwd -P 2>/dev/null || pwd)" 2>/dev/null || true
    fi
fi

# Project seeding (v3.11.0 Phase 7.3): seed the current repo on a global install
# run from inside it, ship the opt-in on-open hook, and surface `nexus-hub init`
# for other projects. Folded under INSTALL VERIFICATION as the project-scoped
# follow-up to any NEEDS-ACTION hints above.
install_project_autoseed "$REPO_ROOT" "$SCOPE_LABEL"

# Resolve any managed-file conflicts collected during an interactive install
# (single end-of-run prompt). No-op on the non-interactive / --yes / --force path.
resolve_conflicts

echo ""
echo -e "${GREEN}✓ Nexus-Hub v${NEXUS_HUB_VERSION} installed (${SCOPE_LABEL} scope).${RESET}"
echo ""
echo -e "${YELLOW}Restart any running AI assistant sessions (Claude Code, Cursor, Gemini CLI, Codex, Copilot, OpenCode) so they pick up the new settings, hooks, skills, and rules.${RESET}"
echo ""
