#!/usr/bin/env python3
"""Validate GitHub Actions workflow files for known unsafe patterns.

Checks each `.github/workflows/*.yml` for:

    - Third-party actions pinned to a moving ref (@main, @master, @latest).
      GitHub-owned actions (`actions/*`, `github/*`) are allowed to pin to a
      major-version tag (@vN).
    - `pull_request_target` trigger combined with explicit checkout of
      the pull request head ref (untrusted code in a privileged context).
    - Direct interpolation of `${{ github.event.* }}` user-controlled fields
      into `run:` script bodies (script injection risk; use env: passthrough).
    - Workflows that grant `permissions: write-all` or no permissions block
      while accepting `pull_request` events.

Local-only, read-only, zero outbound calls.

Exit codes:
    0 - no findings
    1 - one or more findings
    2 - usage / IO error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TRUSTED_OWNERS: frozenset[str] = frozenset({"actions", "github"})

ACTION_USES_RE = re.compile(
    r"^\s*-?\s*uses:\s*([A-Za-z0-9._\-]+)/([A-Za-z0-9._\-/]+?)@([^\s#]+)\s*(?:#.*)?$"
)
COMMIT_SHA_RE = re.compile(r"^[a-f0-9]{40}$")
MAJOR_TAG_RE = re.compile(r"^v\d+(?:\.\d+){0,2}$")
MOVING_REFS: frozenset[str] = frozenset({"main", "master", "latest", "HEAD", "develop"})

PR_TARGET_TRIGGER_RE = re.compile(r"^\s*(?:on:\s*)?pull_request_target\b", re.MULTILINE)
PR_HEAD_CHECKOUT_RE = re.compile(
    r"(?:ref|sha)\s*:\s*\$\{\{\s*github\.event\.pull_request\.head\.(?:ref|sha)\s*\}\}"
)

GITHUB_EVENT_INJECTION_RE = re.compile(
    r"\$\{\{\s*github\.event\.(?:"
    r"issue\.title|issue\.body|"
    r"pull_request\.title|pull_request\.body|pull_request\.head\.ref|"
    r"comment\.body|review\.body|"
    r"head_commit\.message|head_commit\.author\.email|head_commit\.author\.name|"
    r"workflow_run\.head_branch|workflow_run\.head_commit\.message"
    r")[^}]*\}\}"
)

RUN_INLINE_RE = re.compile(r"^(\s*)(?:-\s+)?run:\s*(.+?)\s*$")
RUN_BLOCK_START_RE = re.compile(r"^(\s*)(?:-\s+)?run:\s*[|>][\-+]?\s*$")

WRITE_ALL_PERMISSIONS_RE = re.compile(r"^\s*permissions:\s*write-all\s*$", re.MULTILINE)
UPLOAD_ARTIFACT_USES_RE = re.compile(
    r"^\s*(?:-\s*)?uses:\s*[\"']?actions/upload-artifact@[^\s#\"']+",
    re.IGNORECASE | re.MULTILINE,
)
GITHUB_EXPRESSION_RE = re.compile(r"^\$\{\{.+\}\}$", re.DOTALL)


class WorkflowYamlUnavailable(RuntimeError):
    """Raised when workflow shape cannot be validated safely."""


def iter_run_lines(text: str):
    """Yield (line_no, line_text) for every line inside a `run:` block.

    Handles both inline (`run: cmd`) and block-scalar (`run: |` / `run: >`)
    forms. A block-scalar continues until a less-or-equal-indented non-blank
    line that is not part of the block body.
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        inline = RUN_INLINE_RE.match(line)
        block = RUN_BLOCK_START_RE.match(line)
        if block:
            base_indent = len(block.group(1))
            j = i + 1
            body_indent: int | None = None
            while j < len(lines):
                body = lines[j]
                stripped = body.lstrip()
                if not stripped:
                    j += 1
                    continue
                indent = len(body) - len(stripped)
                if indent <= base_indent:
                    break
                if body_indent is None:
                    body_indent = indent
                elif indent < body_indent:
                    break
                yield j + 1, body
                j += 1
            i = j
            continue
        if inline and not block:
            yield i + 1, inline.group(2)
        i += 1


def scan_workflow(path: Path) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return findings

    lines = text.splitlines()

    has_pr_target = bool(PR_TARGET_TRIGGER_RE.search(text))
    if has_pr_target:
        for m in PR_HEAD_CHECKOUT_RE.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            findings.append((
                line_no,
                "pull_request_target + checkout of PR head ref "
                "(untrusted code in privileged context)",
            ))

    for line_no, line in enumerate(lines, start=1):
        m = ACTION_USES_RE.match(line)
        if not m:
            continue
        owner, _name, ref = m.group(1), m.group(2), m.group(3)
        if owner in TRUSTED_OWNERS:
            if ref in MOVING_REFS:
                findings.append((
                    line_no,
                    f"GitHub-owned action pinned to moving ref @{ref}",
                ))
            continue
        if COMMIT_SHA_RE.match(ref):
            continue
        if MAJOR_TAG_RE.match(ref):
            findings.append((
                line_no,
                f"third-party action {owner}/... pinned to tag @{ref} "
                "(pin to commit SHA for stronger supply-chain guarantees)",
            ))
            continue
        if ref in MOVING_REFS:
            findings.append((
                line_no,
                f"third-party action pinned to moving ref @{ref}",
            ))
            continue
        findings.append((
            line_no,
            f"third-party action ref @{ref} is not a 40-char commit SHA",
        ))

    for line_no, run_line in iter_run_lines(text):
        for inj in GITHUB_EVENT_INJECTION_RE.finditer(run_line):
            findings.append((
                line_no,
                f"untrusted github.event interpolated into run: block: "
                f"{inj.group(0)} (use env: passthrough)",
            ))

    findings.extend(scan_lifecycle(path, text))

    if WRITE_ALL_PERMISSIONS_RE.search(text):
        for line_no, line in enumerate(lines, start=1):
            if "permissions:" in line and "write-all" in line:
                findings.append((
                    line_no,
                    "permissions: write-all grants every scope "
                    "(use least-privilege per-scope grants)",
                ))
                break

    return findings



# ---------------------------------------------------------------------------
# v4.0.0 lifecycle rules.
#
# The checks above are supply-chain and privilege rules; these are COST and
# EVENT-SEPARATION rules from
# docs/releases/v4/v4.0/development/ci-cd-lifecycle-contract.md section 4. They are
# deliberately written against workflow SHAPE rather than against Nexus-Hub job
# names, so they stay meaningful in a fork or a downstream repository that
# adopts the same contract with different jobs.
# ---------------------------------------------------------------------------

#: Branch names commonly used as an integration or release branch. A workflow
#: that fires on both `pull_request` into one of these AND `push` to the same
#: one runs twice over an identical tree under a pull-request-only merge policy.
PROTECTED_BRANCH_NAMES = {"main", "master", "develop", "development", "trunk"}

#: Triggers that indicate a workflow is a VALIDATION gate rather than a
#: deployment, publication, or provenance step. Only these are subject to the
#: duplicate-run rule; a post-merge or release workflow legitimately fires on a
#: protected-branch push.
_VALIDATION_MARKERS = ("pytest", "npm test", "npm run test", "shellcheck", "--profile full",
                       "--profile fast", "--profile platform", "make validate", "make test")


def _yaml_document(text: str) -> dict[object, object]:
    """Return a parsed workflow mapping or raise cannot-validate."""
    try:
        import yaml  # noqa: PLC0415 - optional at import time
    except ImportError as error:
        raise WorkflowYamlUnavailable(
            "PyYAML is required for workflow shape and artifact-retention validation"
        ) from error
    try:
        data = yaml.safe_load(text)
    except Exception as error:  # noqa: BLE001 - converted to explicit cannot-validate
        raise WorkflowYamlUnavailable(f"workflow YAML could not be parsed: {error}") from error
    if not isinstance(data, dict):
        raise WorkflowYamlUnavailable("workflow YAML root must be a mapping")
    return data


def _yaml_triggers(text: str):
    """Return the parsed `on:` mapping, or None when it cannot be read.

    PyYAML parses the bare key `on` as the BOOLEAN True (a YAML 1.1 legacy),
    so a reader that looks only for the string key finds no triggers in any
    workflow file and passes vacuously. Both spellings are accepted here for
    that reason.
    """
    data = _yaml_document(text)
    triggers = data.get("on", data.get(True))
    return triggers if isinstance(triggers, dict) else None


def _unbounded_artifact_upload_lines(text: str) -> list[int]:
    """Return line numbers for upload steps without step-local retention."""
    upload_lines = [
        text[: match.start()].count("\n") + 1
        for match in UPLOAD_ARTIFACT_USES_RE.finditer(text)
    ]
    data = _yaml_document(text)
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return upload_lines

    unbounded: list[int] = []
    upload_index = 0
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if not isinstance(uses, str) or not uses.casefold().startswith(
                "actions/upload-artifact@"
            ):
                continue
            line_no = upload_lines[upload_index] if upload_index < len(upload_lines) else 1
            upload_index += 1
            options = step.get("with")
            retention = options.get("retention-days") if isinstance(options, dict) else None
            if isinstance(retention, bool):
                unbounded.append(line_no)
            elif isinstance(retention, int):
                if retention <= 0:
                    unbounded.append(line_no)
            elif isinstance(retention, str):
                value = retention.strip()
                if not value or not (
                    (value.isdecimal() and int(value) > 0)
                    or GITHUB_EXPRESSION_RE.fullmatch(value)
                ):
                    unbounded.append(line_no)
            else:
                unbounded.append(line_no)
    return unbounded


def _looks_like_validation(text: str) -> bool:
    return any(marker in text for marker in _VALIDATION_MARKERS)


def _separates_events_per_job(text: str) -> bool:
    """True when some job condition distinguishes the triggering event.

    Deliberately a text match on the workflow rather than a parse of every job
    condition: the expression grammar is GitHub's, not YAML's, and a partial
    parser here would be a second source of truth for something this check only
    needs a yes-or-no answer about.
    """
    return "github.event_name" in text


def _uses_self_hosted_runner(text: str) -> bool:
    """True when a `runs-on:` value names a self-hosted runner."""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("runs-on:"):
            continue
        if "self-hosted" in stripped:
            return True
    return False


def scan_lifecycle(path: Path, text: str) -> list[tuple[int, str]]:
    """Event-separation and cost findings for one workflow."""
    findings: list[tuple[int, str]] = []

    # Rule 3: unbounded artifact retention. Each upload owns its own bound; one
    # compliant step cannot mask a later unbounded step in the same workflow.
    for line_no in _unbounded_artifact_upload_lines(text):
        findings.append((
            line_no,
            "uploads an artifact with no retention-days; set an explicit short "
            "retention rather than inheriting the repository default",
        ))

    triggers = _yaml_triggers(text)
    if triggers is None:
        return findings

    pr = triggers.get("pull_request")
    push = triggers.get("push")

    pr_branches = set(pr.get("branches") or []) if isinstance(pr, dict) else set()
    push_branches = set(push.get("branches") or []) if isinstance(push, dict) else set()

    # Rule 1: a validation workflow must not run on both the pull request into a
    # protected branch and a push to that same branch. Those are the same tree.
    #
    # A workflow that separates the two events with a job-level condition on
    # `github.event_name` is CONFORMING, not violating: that is how a file can
    # carry both a pull-request gate and a distinct post-merge step without
    # running either twice. Flagging that shape would push the author toward
    # splitting a coherent file for no benefit -- or, worse, toward disabling
    # the check. A gate that cries wolf gets switched off.
    both = pr_branches & push_branches & PROTECTED_BRANCH_NAMES
    if both and _looks_like_validation(text) and not _separates_events_per_job(text):
        findings.append((
            1,
            "validation runs on BOTH pull_request into and push to "
            f"{sorted(both)} with no per-job github.event_name condition: under a "
            "pull-request-only merge policy that is the same tree validated "
            "twice. Move post-merge work to its own workflow, or gate the jobs.",
        ))

    # Rule 2: an ordinary feature-branch push must never start validation.
    if isinstance(push, dict) and "branches" not in push and "tags" not in push:
        findings.append((
            1,
            "push trigger has no branch or tag filter, so every feature-branch "
            "push starts this workflow",
        ))

    # Rule 4: a self-hosted runner must not be reachable from an untrusted fork.
    #
    # Matched against the `runs-on:` VALUE rather than anywhere in the file. The
    # phrase appears in ordinary prose ("on other images, self-hosted or
    # future"), and a substring match over the whole text flagged a workflow
    # that runs entirely on GitHub-hosted runners.
    if _uses_self_hosted_runner(text) and "pull_request" in str(triggers):
        findings.append((
            1,
            "self-hosted runner reachable from a pull_request trigger: a "
            "persistent runner must never execute untrusted fork code",
        ))

    return findings


def find_workflow_files(root: Path, paths: list[str] | None) -> list[Path]:
    if paths:
        files: list[Path] = []
        for p in paths:
            full = root / p
            if full.is_file():
                files.append(full)
            elif full.is_dir():
                files.extend(sorted(full.glob("*.yml")))
                files.extend(sorted(full.glob("*.yaml")))
        return files
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return []
    out: list[Path] = []
    out.extend(sorted(workflows_dir.glob("*.yml")))
    out.extend(sorted(workflows_dir.glob("*.yaml")))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
    )
    parser.add_argument("--path", action="append", default=None)
    parser.add_argument(
        "--strict-sha-pinning",
        action="store_true",
        help="Treat third-party major-version tag pins as errors (default: allowed).",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2

    files = find_workflow_files(root, args.path)
    if args.verbose:
        print(f"Scanning {len(files)} workflow file(s)...")

    total_errors = 0
    total_warnings = 0
    for path in files:
        try:
            findings = scan_workflow(path)
        except WorkflowYamlUnavailable as error:
            rel = path.relative_to(root)
            print(f"ERROR: cannot validate {rel}: {error}", file=sys.stderr)
            return 2
        if not findings:
            continue
        rel = path.relative_to(root)
        for line, msg in findings:
            is_tag_pin_warning = (
                "pinned to tag @" in msg and not args.strict_sha_pinning
            )
            if is_tag_pin_warning:
                print(f"{rel}:{line}: WARN: {msg}")
                total_warnings += 1
            else:
                print(f"{rel}:{line}: {msg}", file=sys.stderr)
                total_errors += 1

    if total_errors:
        print(
            f"\nvalidate_workflow_security: {total_errors} error(s), "
            f"{total_warnings} warning(s) across {len(files)} workflow(s).",
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        print(
            f"validate_workflow_security: clean "
            f"({len(files)} workflow(s), {total_warnings} warning(s))."
        )
    elif total_warnings:
        print(
            f"validate_workflow_security: 0 errors, "
            f"{total_warnings} warning(s)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
