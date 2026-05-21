#!/usr/bin/env bash
# tasks-to-issues.sh -- Parse the strict-format task lines in a feature
# directory's tasks.md or plan.md and either dry-run the resulting
# gh issue create invocations or execute them sequentially.
#
# Usage:
#   tasks-to-issues.sh [--dry-run] [--feature-dir DIR] [--repo-root DIR]
#
# Exit codes:
#   0  -- success (all tasks filed or all dry-run lines printed)
#   1  -- generic error (bad input, missing gh, malformed source)
#   2  -- usage error (bad flag)
#   3  -- pre-flight check failed (gh auth, repo not on GitHub)
#   4  -- partial failure (some tasks filed, then a gh call failed)
#
# Cross-platform parity: tasks-to-issues.ps1 implements the same flow on
# Windows. Keep the two in lockstep per AGENTS.md.

set -euo pipefail

PROGNAME="tasks-to-issues.sh"
TASK_REGEX='^- \[ \] T[0-9]{3,}( \[P\])?( \[US[0-9]+\])? .+$'

log_info()  { echo "[INFO]  $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

die() {
    log_error "$1"
    exit "${2:-1}"
}

usage() {
    cat >&2 <<EOF
Usage: $PROGNAME [--dry-run] [--feature-dir DIR] [--repo-root DIR]

Parses the strict-format task lines in <feature-dir>/tasks.md or plan.md
and either dry-runs the gh issue create invocations (--dry-run) or
executes them sequentially after user confirmation.
EOF
}

# --- Argument parsing -----------------------------------------------------

dry_run="false"
feature_dir=""
repo_root=""

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run)
            dry_run="true"
            shift
            ;;
        --feature-dir)
            [ $# -ge 2 ] || die "--feature-dir requires a value" 2
            feature_dir="$2"
            shift 2
            ;;
        --repo-root)
            [ $# -ge 2 ] || die "--repo-root requires a value" 2
            repo_root="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown argument: $1" 2
            ;;
    esac
done

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

# --- Pre-flight checks ----------------------------------------------------

command -v gh >/dev/null 2>&1 \
    || die 'Install the GitHub CLI from https://cli.github.com and run "gh auth login" before re-trying.' 3

if ! gh auth status >/dev/null 2>&1; then
    die 'gh is not authenticated. Run "gh auth login" before re-trying.' 3
fi

repo_slug="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)"
[ -n "$repo_slug" ] \
    || die 'Working directory does not resolve to a GitHub repo. Configure the remote with "gh repo set-default" or run from a GitHub-tracked clone.' 3

# --- Resolve feature directory + task source -----------------------------

if [ -z "$feature_dir" ]; then
    feature_json="$repo_root/.specify/feature.json"
    if [ -f "$feature_json" ]; then
        feature_dir="$(awk '
            /"feature_directory"/ {
                sub(/.*"feature_directory"[[:space:]]*:[[:space:]]*"/, "", $0)
                sub(/".*/, "", $0)
                print
                exit
            }
        ' "$feature_json" 2>/dev/null || true)"
    fi
fi

if [ -z "$feature_dir" ]; then
    # Fall back to the most recent plan under docs/<version>/plans/.
    latest_plan="$(ls -t "$repo_root"/docs/v*/plans/*.md 2>/dev/null | head -n 1 || true)"
    if [ -n "$latest_plan" ]; then
        feature_dir="$(dirname "$latest_plan")"
    fi
fi

[ -n "$feature_dir" ] || die "Could not resolve a feature directory. Pass --feature-dir DIR explicitly." 1

# Allow relative paths.
case "$feature_dir" in
    /*) ;;
    *) feature_dir="$repo_root/$feature_dir" ;;
esac

[ -d "$feature_dir" ] || die "Feature directory does not exist: $feature_dir"

source_file=""
if [ -f "$feature_dir/tasks.md" ]; then
    source_file="$feature_dir/tasks.md"
elif [ -f "$feature_dir/plan.md" ]; then
    source_file="$feature_dir/plan.md"
else
    # Default layout: a single <slug>.md under docs/<version>/plans/.
    only_md="$(ls "$feature_dir"/*.md 2>/dev/null | head -n 1 || true)"
    if [ -n "$only_md" ]; then
        source_file="$only_md"
    fi
fi

[ -n "$source_file" ] && [ -f "$source_file" ] \
    || die "No tasks.md, plan.md, or fallback <slug>.md found in $feature_dir"

log_info "Repo:           $repo_slug"
log_info "Feature dir:    $feature_dir"
log_info "Source file:    $source_file"
log_info "Mode:           $([ "$dry_run" = "true" ] && echo "dry-run" || echo "execute")"

# --- Parse task lines -----------------------------------------------------

# Extract candidate lines (start with "- [ ]" and contain T###).
candidate_lines="$(grep -nE '^- \[ \] T[0-9]+' "$source_file" || true)"

if [ -z "$candidate_lines" ]; then
    die "No task lines found in $source_file. Re-run /generate-plan with the strict-format validator." 1
fi

# Validate every candidate against the strict regex; collect violations.
violations=""
while IFS= read -r raw; do
    [ -z "$raw" ] && continue
    line_no="${raw%%:*}"
    line_body="${raw#*:}"
    if ! printf '%s' "$line_body" | grep -Eq "$TASK_REGEX"; then
        violations="${violations}${line_no}: ${line_body}
"
    fi
done <<EOF
$candidate_lines
EOF

if [ -n "$violations" ]; then
    log_error "Source file contains lines that look like tasks but do not match the strict regex:"
    printf '%s' "$violations" >&2
    die "Re-run /generate-plan with the strict-format validator to fix these lines." 1
fi

# --- Build per-task payload + drive gh ------------------------------------

newly_created=0
skipped=0
failed=0
summary_rows=""

while IFS= read -r raw; do
    [ -z "$raw" ] && continue
    line_no="${raw%%:*}"
    line_body="${raw#*:}"

    # Detect idempotency marker.
    if printf '%s' "$line_body" | grep -q '\[gh#[0-9]\+\]'; then
        skipped=$((skipped + 1))
        continue
    fi

    # Decompose the line. Use awk to extract fields. The regex above
    # guarantees the structure: '- [ ] T### [P]? [US#]? description'.
    task_id="$(printf '%s' "$line_body" | awk '{print $3}')"
    rest="${line_body#- \[ \] $task_id }"

    parallel="false"
    user_story=""

    if printf '%s' "$rest" | grep -q '^\[P\] '; then
        parallel="true"
        rest="${rest#\[P\] }"
    fi

    if printf '%s' "$rest" | grep -Eq '^\[US[0-9]+\] '; then
        user_story="$(printf '%s' "$rest" | awk -F'[][]' '{print $2}')"
        rest="${rest#\[US*\] }"
        # awk above leaves us with US<n>; strip the prefix to keep <n>.
        user_story="${user_story#US}"
    fi

    description="$rest"
    # Extract trailing file path heuristically: last whitespace-separated token
    # that contains a slash or a dot.
    file_path="$(printf '%s' "$description" | awk '{
        for (i = NF; i >= 1; i--) {
            if ($i ~ /[\/.]/) { print $i; exit }
        }
    }')"

    # Build labels.
    labels="nexus-hub,spec-kit-task"
    [ "$parallel" = "true" ] && labels="${labels},parallel"
    [ -n "$user_story" ] && labels="${labels},user-story-${user_story}"

    # Build title (cap at 200 chars).
    title="[${task_id}] ${description}"
    if [ ${#title} -gt 200 ]; then
        title="$(printf '%.197s...' "$title")"
    fi

    # Build body.
    body=$(cat <<EOF
Task: ${task_id}
File: ${file_path:-n/a}
Parallel: $([ "$parallel" = "true" ] && echo "yes" || echo "no")
User story: ${user_story:+US${user_story}}${user_story:-n/a}
Source: ${source_file#$repo_root/}

Generated by /tasks-to-issues
EOF
)

    if [ "$dry_run" = "true" ]; then
        # Print the resolved gh invocation. Use single quotes around body
        # for shell-safety in the printed line.
        printf 'gh issue create --title %q --body %q --label %q\n' \
            "$title" "$body" "$labels"
        summary_rows="${summary_rows}${task_id} | (dry-run) | ${labels}
"
        continue
    fi

    # Execute.
    log_info "Creating issue for ${task_id} ..."
    if issue_url="$(gh issue create --title "$title" --body "$body" --label "$labels" 2>&1)"; then
        # Extract trailing number from URL.
        issue_num="${issue_url##*/}"
        log_info "  -> ${issue_url}"
        newly_created=$((newly_created + 1))
        summary_rows="${summary_rows}${task_id} | ${issue_url} | ${labels}
"

        # Rewrite source file: append [gh#<num>] to the task line.
        tmp_file="$(mktemp "${source_file}.XXXXXX")"
        awk -v target="$line_no" -v marker="[gh#${issue_num}]" '
            NR == target { print $0 " " marker; next }
            { print }
        ' "$source_file" > "$tmp_file"
        mv -f "$tmp_file" "$source_file"
    else
        failed=$((failed + 1))
        log_error "Issue creation for ${task_id} failed:"
        printf '%s\n' "$issue_url" >&2
        log_error 'Already-created issues remain. Re-run /tasks-to-issues to file the rest.'
        exit 4
    fi
done <<EOF
$candidate_lines
EOF

# --- Final summary --------------------------------------------------------

echo ""
echo "Summary:"
echo "T### | Issue URL | Labels"
printf '%s' "$summary_rows"
echo ""
echo "Newly created: $newly_created"
echo "Skipped (already filed): $skipped"
echo "Failed: $failed"
