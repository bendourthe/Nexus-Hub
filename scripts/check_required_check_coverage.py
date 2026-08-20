#!/usr/bin/env python3
"""Assert every required status check is produced by an unconditionally-triggered workflow.

GitHub treats a missing check and a skipped check as opposite outcomes:

    "If a workflow is skipped due to path filtering, branch filtering or a commit
    message, then checks associated with that workflow will remain in a Pending
    state." ... "If a job within a workflow is skipped due to a conditional, it
    will report its status as Success."

    -- GitHub Docs, "Troubleshooting required status checks", fetched 2026-08-19
       https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks

So a required check whose WORKFLOW is filtered blocks the pull request forever,
while the same filtering expressed as a job-level `if:` reports Success and
merges. The two look like the same Actions-minute optimization and are not.

That asymmetry is not theoretical here: shipping v3.17.5 took seven administrator
bypasses in one day, every one traced to this mechanism. Routine bypassing is the
real damage, because it erodes the gate for the cases that actually matter.

This guard therefore enforces one rule: a context listed in the manifest must be
produced by a job whose workflow triggers on a pull request into the protected
branch with NO path filter and NO branch filter excluding that branch. A
job-level `if:` is CORRECT and is deliberately never inspected -- flagging it
would push authors back toward the workflow-level filter that causes the defect.

Three failure classes are reported separately because their remedies differ:

    UNPRODUCED  no workflow defines the job -- the manifest is stale, or a job
                was renamed and silently dropped its gate
    CONDITIONAL produced, but by a conditionally-triggered workflow -- move the
                filter from the trigger to a job-level `if:`
    BAD         an unparseable workflow or a malformed manifest -- the guard
                cannot answer, and says so rather than passing

Every failure is collected before a single exit 1, so one run shows the whole
picture instead of one item per fix-and-rerun cycle.

Fail-open is treated as the worst outcome available, not a lenient default. An
unparseable workflow is BAD rather than skipped, a manifest naming a check no
workflow produces fails rather than passing vacuously, and a missing PyYAML is
an explicit error rather than an empty pass. (v3.17.5 shipped a fail-open
validator and had to patch it the same day; that is the shape being avoided.)

Repo-internal guard, standard library plus the PyYAML the catalog tooling
already uses, no outbound call at validate time. It is NOT a distributed
artifact and therefore needs no installer copy step; it belongs in
DEV_ONLY_SCRIPTS alongside the other repo-only guards.

Usage:
    python scripts/check_required_check_coverage.py [--root .]
        [--manifest docs/policy/required-checks.json]
        [--workflows .github/workflows]
    python scripts/check_required_check_coverage.py --sync [--repo owner/name]

Exit codes:
    0  every required context is produced unconditionally
    1  at least one context failed, or the guard could not answer
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path("docs/policy/required-checks.json")
DEFAULT_WORKFLOWS = Path(".github/workflows")

# A matrix leg reports as `job (value)` -- `bootstrap (ubuntu-latest)`. Matrix
# values in this repo are `${{ ... fromJSON(...) }}` expressions evaluated at run
# time, so they cannot be enumerated statically; resolution is by job id and the
# parenthesised leg is informational only.
MATRIX_CONTEXT_RE = re.compile(r"^(?P<job>.+?) \((?P<leg>[^()]*)\)$")

# PyYAML resolves the bare key `on` to boolean True under YAML 1.1, and GitHub's
# workflow schema uses exactly that word for its trigger block. Looking up only
# the string would find no triggers in ANY workflow and pass everything -- the
# fail-open outcome this guard exists to prevent. Both spellings are accepted.
ON_KEYS: tuple[Any, ...] = ("on", True)

# Triggers that can produce a check on a pull request's head commit.
PR_EVENTS = ("pull_request", "pull_request_target")


class Failure:
    """One collected failure, carrying its class so the remedy is unambiguous."""

    def __init__(self, kind: str, branch: str, context: str, detail: str) -> None:
        self.kind = kind
        self.branch = branch
        self.context = context
        self.detail = detail

    def __str__(self) -> str:
        return f"  {self.kind:<11} [{self.branch}] {self.context}: {self.detail}"


def require_yaml() -> Any:
    """Import PyYAML, failing loudly rather than degrading to an empty pass."""
    try:
        return importlib.import_module("yaml")
    except ImportError as exc:
        raise SystemExit(
            "ERROR: PyYAML is required to parse .github/workflows/*.yml and is not "
            "installed. This guard refuses to pass without parsing the workflows, "
            "because a silent pass here re-permits the exact defect it exists to "
            "catch.\n  Please run: pip install PyYAML\n"
            f"  (import error: {exc})"
        ) from exc


def get_triggers(workflow: dict[str, Any]) -> Any:
    """Return the raw `on:` value, tolerating PyYAML's boolean-True key."""
    for key in ON_KEYS:
        if key in workflow:
            return workflow[key]
    return None


def normalize_triggers(raw: Any) -> dict[str, dict[str, Any]]:
    """Normalize every `on:` spelling to {event: {filter: value}}.

    Accepts `on: push`, `on: [push, pull_request]`, and the mapping form. A
    listed-but-unconfigured event maps to an empty dict, which correctly reads as
    "no filters".
    """
    if raw is None:
        return {}
    if isinstance(raw, str):
        return {raw: {}}
    if isinstance(raw, list):
        return {str(event): {} for event in raw}
    if isinstance(raw, dict):
        out: dict[str, dict[str, Any]] = {}
        for event, cfg in raw.items():
            out[str(event)] = cfg if isinstance(cfg, dict) else {}
        return out
    raise ValueError(f"unsupported `on:` value of type {type(raw).__name__}")


def as_list(value: Any) -> list[str]:
    """Coerce a scalar-or-list YAML filter value to a list of strings."""
    if value is None:
        return []
    if isinstance(value, (str, int, float)):
        return [str(value)]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def branch_pattern_matches(pattern: str, branch: str) -> bool:
    """Match a GitHub branch filter pattern against a concrete branch name.

    Only the `*` / `**` wildcards are honoured; a `!`-negated pattern is handled
    by the caller. Anything unrecognised falls through to a literal comparison,
    which is the conservative direction: an unmatched pattern reads as "this
    branch is filtered out" and produces a reported failure rather than a pass.
    """
    if pattern == branch:
        return True
    if "*" not in pattern:
        return False
    regex = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    return re.fullmatch(regex, branch) is not None


def branch_included(cfg: dict[str, Any], branch: str) -> tuple[bool, str]:
    """Decide whether a trigger fires for `branch`, and say why when it does not."""
    include = as_list(cfg.get("branches"))
    exclude = as_list(cfg.get("branches-ignore"))

    if include:
        positive = [p for p in include if not p.startswith("!")]
        negative = [p[1:] for p in include if p.startswith("!")]
        if positive and not any(branch_pattern_matches(p, branch) for p in positive):
            return False, f"`branches:` {include} does not include '{branch}'"
        if any(branch_pattern_matches(p, branch) for p in negative):
            return False, f"`branches:` negates '{branch}' ({include})"

    if exclude and any(branch_pattern_matches(p, branch) for p in exclude):
        return False, f"`branches-ignore:` {exclude} excludes '{branch}'"

    return True, ""


def trigger_is_unconditional(cfg: dict[str, Any], branch: str) -> tuple[bool, str]:
    """A trigger is unconditional for `branch` when no path filter applies to it.

    Path filtering is the fatal case: GitHub leaves the check Pending forever.
    Branch filtering is fatal in the same way when it excludes the protected
    branch, and harmless when it includes it (`branches: [main, develop]` on a
    PR trigger is both idiomatic and correct).
    """
    for key in ("paths", "paths-ignore"):
        if cfg.get(key) is not None:
            return False, (
                f"trigger carries `{key}:`, so the workflow does not run on an "
                "unrelated PR and the check stays Pending forever; move the "
                "filter to a job-level `if:` instead"
            )
    return branch_included(cfg, branch)


class ManifestError(Exception):
    """A defect in the required-checks manifest.

    One exception type for every manifest defect on purpose: the caller's only
    decision is "report BAD and exit 1", so splitting shape errors from value
    errors would add a branch nothing acts on.
    """


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    """Load and strictly validate the manifest, raising ManifestError on any defect."""
    if not path.is_file():
        raise ManifestError(f"manifest not found at {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"manifest {path} must be a JSON object")

    branches = data.get("branches")
    if not isinstance(branches, dict) or not branches:
        raise ManifestError(
            f"manifest {path} must carry a non-empty `branches` object; an empty "
            "manifest would pass vacuously and assert nothing"
        )

    out: dict[str, dict[str, Any]] = {}
    for branch, cfg in branches.items():
        if not isinstance(cfg, dict):
            raise ManifestError(f"manifest branch '{branch}' must be an object")
        contexts = cfg.get("contexts")
        if not isinstance(contexts, list) or not contexts:
            raise ManifestError(
                f"manifest branch '{branch}' must list a non-empty `contexts` array"
            )
        if not all(isinstance(c, str) and c.strip() for c in contexts):
            raise ManifestError(
                f"manifest branch '{branch}' has a non-string or empty context entry"
            )
        out[str(branch)] = {"contexts": [str(c) for c in contexts]}
    return out


def load_workflows(
    directory: Path, yaml_mod: Any
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Index every workflow job by id. Returns (jobs, bad) where bad is fatal."""
    jobs: dict[str, list[dict[str, Any]]] = {}
    bad: list[str] = []

    if not directory.is_dir():
        bad.append(f"workflow directory not found at {directory}")
        return jobs, bad

    paths = sorted(
        p for p in directory.iterdir() if p.suffix in (".yml", ".yaml") and p.is_file()
    )
    if not paths:
        bad.append(f"no workflow files found under {directory}")
        return jobs, bad

    for path in paths:
        try:
            parsed = yaml_mod.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - any parse failure is fatal here
            bad.append(f"{path.name}: unparseable YAML ({type(exc).__name__}: {exc})")
            continue
        if not isinstance(parsed, dict):
            bad.append(f"{path.name}: top level is not a mapping")
            continue

        try:
            triggers = normalize_triggers(get_triggers(parsed))
        except ValueError as exc:
            bad.append(f"{path.name}: {exc}")
            continue
        if not triggers:
            bad.append(f"{path.name}: no `on:` trigger block found")
            continue

        wf_jobs = parsed.get("jobs")
        if not isinstance(wf_jobs, dict):
            bad.append(f"{path.name}: no `jobs:` mapping found")
            continue

        for job_id in wf_jobs:
            jobs.setdefault(str(job_id), []).append(
                {"name": path.name, "triggers": triggers}
            )

    return jobs, bad


def resolve_context(context: str, jobs: dict[str, list[dict[str, Any]]]) -> str | None:
    """Resolve a required context to a job id, unwrapping a matrix leg suffix."""
    if context in jobs:
        return context
    match = MATRIX_CONTEXT_RE.match(context)
    if match and match.group("job") in jobs:
        return match.group("job")
    return None


def check(
    manifest: dict[str, dict[str, Any]], jobs: dict[str, list[dict[str, Any]]]
) -> list[Failure]:
    """Evaluate every declared context against the indexed workflows."""
    failures: list[Failure] = []

    for branch, cfg in manifest.items():
        for context in cfg["contexts"]:
            job_id = resolve_context(context, jobs)
            if job_id is None:
                failures.append(
                    Failure(
                        "UNPRODUCED",
                        branch,
                        context,
                        "no workflow defines a job with this id; the manifest is "
                        "stale, or the job was renamed and silently dropped its gate",
                    )
                )
                continue

            reasons: list[str] = []
            for definition in jobs[job_id]:
                pr_cfgs = [
                    definition["triggers"][event]
                    for event in PR_EVENTS
                    if event in definition["triggers"]
                ]
                if not pr_cfgs:
                    reasons.append(
                        f"{definition['name']}: no `pull_request` trigger, so the "
                        "check never reports on a pull request"
                    )
                    continue
                unconditional = False
                local: list[str] = []
                for pr_cfg in pr_cfgs:
                    ok, why = trigger_is_unconditional(pr_cfg, branch)
                    if ok:
                        unconditional = True
                        break
                    local.append(f"{definition['name']}: {why}")
                if unconditional:
                    reasons = []
                    break
                reasons.extend(local)

            if reasons:
                failures.append(
                    Failure(
                        "CONDITIONAL",
                        branch,
                        context,
                        f"job '{job_id}' is produced only conditionally -- "
                        + "; ".join(reasons),
                    )
                )

    return failures


def run_sync(repo: str | None, branches: tuple[str, ...] = ("main", "develop")) -> int:
    """Print the live required contexts via the user's own gh CLI. Never writes.

    `branches` defaults to the develop+main model but is passed from the
    manifest when one is readable, so a repository whose protected branch is
    named something else still gets an answer instead of a silent nothing.
    """
    if repo is None:
        try:
            repo = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    "--json",
                    "nameWithOwner",
                    "-q",
                    ".nameWithOwner",
                ],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            print(
                f"ERROR: could not determine the repository via gh: {exc}",
                file=sys.stderr,
            )
            return 1

    print(f"# Live required status checks for {repo}")
    print("# Printed only -- update docs/policy/required-checks.json by hand.")
    failed = False
    for branch in branches:
        try:
            out = subprocess.run(
                [
                    "gh",
                    "api",
                    f"repos/{repo}/branches/{branch}/protection",
                    "--jq",
                    (
                        "{strict: .required_status_checks.strict, "
                        "contexts: .required_status_checks.contexts}"
                    ),
                ],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"  {branch}: unavailable ({exc})", file=sys.stderr)
            failed = True
            continue
        print(f"  {branch}: {out}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--manifest", default=None, help=f"default: {DEFAULT_MANIFEST}")
    parser.add_argument(
        "--workflows", default=None, help=f"default: {DEFAULT_WORKFLOWS}"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="print the live required contexts via gh and exit; never writes the manifest",
    )
    parser.add_argument(
        "--repo", default=None, help="owner/name for --sync (default: detected)"
    )
    args = parser.parse_args(argv)

    if args.sync:
        # Prefer the manifest's own branch list; fall back to the default pair
        # when the manifest is absent or malformed, since --sync is a
        # reporting aid and must still work while the manifest is being fixed.
        sync_manifest = (
            Path(args.manifest) if args.manifest else Path(args.root) / DEFAULT_MANIFEST
        )
        try:
            branches = tuple(load_manifest(sync_manifest))
        except ManifestError:
            branches = ("main", "develop")
        return run_sync(args.repo, branches)

    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest) if args.manifest else root / DEFAULT_MANIFEST
    workflows_dir = Path(args.workflows) if args.workflows else root / DEFAULT_WORKFLOWS

    yaml_mod = require_yaml()

    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        print("Required-check coverage: FAIL", file=sys.stderr)
        print(f"  BAD         manifest: {exc}", file=sys.stderr)
        return 1

    jobs, bad = load_workflows(workflows_dir, yaml_mod)
    failures = check(manifest, jobs) if jobs else []

    if not bad and not failures:
        total = sum(len(cfg["contexts"]) for cfg in manifest.values())
        print(
            f"Required-check coverage: OK -- {total} declared context(s) across "
            f"{len(manifest)} branch(es), every one produced unconditionally."
        )
        return 0

    print("Required-check coverage: FAIL", file=sys.stderr)
    for entry in bad:
        print(f"  BAD         {entry}", file=sys.stderr)
    for failure in failures:
        print(str(failure), file=sys.stderr)
    print(
        "\nA required status check must be produced by a job whose workflow triggers "
        "unconditionally.\nFilter at the JOB level with `if:`, never at the workflow "
        "level with `paths:`: a skipped job\nreports Success, while an untriggered "
        "workflow reports nothing and blocks the PR forever.\nSee "
        "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
