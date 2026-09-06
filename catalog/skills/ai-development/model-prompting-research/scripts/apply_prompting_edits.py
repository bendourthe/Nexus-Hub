#!/usr/bin/env python3
"""Edit-routing classifier and guard-gated auto-apply engine.

Research produces two kinds of finding, and they must go to different places:

  * model-specific        -> the bundled profile layer, and NOWHERE else.
  * model-agnostic        -> eligible to PROPOSE an edit to a shared catalog body
                             (a SKILL.md, a command, a base-*.md template), but
                             only behind the full guard suite on an isolated
                             branch that stops for human merge.

This script owns that routing and the apply loop. The agent authors the edit
text (prose is genuinely agent work); this script decides whether the edit is
allowed to exist at all, applies it, runs the guards, and keeps or reverts it.

THE HARD RAIL, AND WHY IT LIVES HERE
------------------------------------
The v3.15.5 plan asserted that `scripts/check_base_template_parity.py` makes the
rail physical, on the theory that "a model-named line in a shared base-*.md fails
the build". That is NOT true, and it was verified empirically before this script
was written:

  * A model-named line added to ALL FIVE base-*.md files inside an invariant
    section PASSES the parity guard, because the guard compares the five files to
    EACH OTHER. Lockstep is exactly what it checks, so an auto-apply engine
    dutifully applying the same model-named line five times satisfies it.
  * A model-named line in a NON-invariant section of one file also passes, since
    only four section bodies are compared.

The parity guard prevents DRIFT between the templates. It says nothing about
model-specific content. So the rail is enforced here instead, at the only point
where this feature can autonomously write: an edit may not INTRODUCE a model
identifier into a shared body, whatever its claim's `scope` tag says. Detection
runs on what the edit ADDS (tokens in `new` that are absent from `old`), so
rewording a line that already names a model is allowed while smuggling a new one
in is not.

Residual, stated plainly: this rail binds THIS engine. A human hand-editing a
shared body is still unguarded, because a catalog-wide leakage gate would fail
today on pre-existing legitimate mentions (model-routing documents tiers by
name) and triaging those is a separate decision.

Deterministic, offline, stdlib-only apart from `git`. Nothing here calls the
network or an LLM.

Usage:
    python apply_prompting_edits.py classify --input proposals.json
    python apply_prompting_edits.py apply --input proposals.json --stamp 20260727-1200
    python apply_prompting_edits.py apply --input proposals.json --stamp S --commit
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Branches this engine must never write to. Asserted after checkout, so the
# invariant holds even if the caller passes something unexpected.
PROTECTED_BRANCHES = frozenset({"main", "master", "develop"})

BRANCH_PREFIX = "feat/tune-prompting-"

# The only shared-body surfaces a model-agnostic finding may target. Anything
# else is rejected outright rather than applied: the research loop exists to
# sharpen authoring, not to refactor the catalog.
ALLOWED_TARGET_KINDS = frozenset({
    "skill-description",
    "skill-trigger-phrase",
    "skill-rationalization",
    "skill-verification",
    "command-body",
    "base-template-line",
})

# Model-identifier patterns. Deliberately broad on the vendor-family + version
# shape, because a false positive costs one rejected edit while a false negative
# ships model-specific text to every platform.
MODEL_PATTERNS: tuple[re.Pattern[str], ...] = (
    # The optional `v` covers vendor ids written as deepseek-v3 / llama-v2.
    re.compile(r"\b(?:claude|gpt|gemini|llama|mistral|grok|qwen|kimi|deepseek|command)[-\s]?v?\d[\w.-]*", re.I),
    re.compile(r"\bclaude-(?:opus|sonnet|haiku|fable)[\w.-]*", re.I),
    re.compile(r"\b(?:opus|sonnet|haiku|fable)\b(?:[-\s]?\d[\w.]*)?", re.I),
    re.compile(r"\bo\d(?:-mini|-preview)?\b"),
)

# Guard commands run after EVERY applied edit. `make` is not available on every
# host, so the individual gates are invoked directly (this is also what CI runs).
DEFAULT_GUARDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("skill-bundles", (sys.executable, "scripts/validate_skills.py", "--bundles-only")),
    ("base-template-parity", (sys.executable, "scripts/check_base_template_parity.py")),
    ("profile-schema", (sys.executable, "scripts/verify_model_prompting_profiles.py", "--quiet")),
    ("version-sync", (sys.executable, "scripts/check_version_sync.py")),
    ("trigger-routing", (sys.executable, "scripts/run_trigger_evals.py", "--gate")),
)

PROFILE_ONLY = "profile-only"
ELIGIBLE = "eligible"
REJECTED = "rejected"


class ApplyError(Exception):
    """A condition that must abort the whole run rather than one edit."""


# ---------------------------------------------------------------------------
# Classification (3.1)
# ---------------------------------------------------------------------------


def model_mentions(text: str) -> list[str]:
    """Every model identifier appearing in `text`, lowercased and deduped."""
    found: set[str] = set()
    for pattern in MODEL_PATTERNS:
        for match in pattern.finditer(text or ""):
            found.add(match.group(0).strip().lower())
    return sorted(found)


def introduced_model_mentions(old: str, new: str) -> list[str]:
    """Model identifiers present in `new` but not already in `old`.

    Rewording a line that already names a model is fine; ADDING a model name to a
    shared body is what the rail forbids.
    """
    before = set(model_mentions(old))
    return [m for m in model_mentions(new) if m not in before]


def classify(proposal: dict) -> dict:
    """Route one proposal. Pure; returns a decision dict, never raises.

    Order matters. Scope is checked first (the cheap, declared signal), then the
    target surface, then the leakage rail last, because the rail must be able to
    veto an edit that looks perfectly well-formed.
    """
    pid = str(proposal.get("id", "<unidentified>"))
    scope = proposal.get("scope")
    target_kind = proposal.get("target_kind")
    old = proposal.get("old") or ""
    new = proposal.get("new") or ""

    def decision(route: str, reason: str, **extra) -> dict:
        return {"id": pid, "route": route, "reason": reason, **extra}

    # Ambiguity resolves to model-specific. A claim parked in the profile layer
    # is merely unhelpful to other models; the reverse ships to every platform.
    if scope != "model-agnostic-candidate":
        return decision(
            PROFILE_ONLY,
            f"scope is {scope!r}; only 'model-agnostic-candidate' is eligible for a "
            f"shared body, and anything else (including missing or unrecognized) "
            f"defaults to model-specific",
        )

    if target_kind not in ALLOWED_TARGET_KINDS:
        return decision(
            REJECTED,
            f"target_kind {target_kind!r} is not one of the allowed shared-body "
            f"surfaces: {', '.join(sorted(ALLOWED_TARGET_KINDS))}",
        )

    if not proposal.get("target"):
        return decision(REJECTED, "proposal has no target file path")
    if not old:
        return decision(REJECTED, "proposal has no 'old' anchor text to replace")
    if new == old:
        return decision(REJECTED, "proposal is a no-op ('new' equals 'old')")

    introduced = introduced_model_mentions(old, new)
    if introduced:
        return decision(
            PROFILE_ONLY,
            f"HARD RAIL: the edit would introduce model identifier(s) "
            f"{', '.join(introduced)} into a shared body, which is model-specific "
            f"content regardless of the declared scope",
            introduced_models=introduced,
        )

    return decision(ELIGIBLE, "model-agnostic, allowed target, introduces no model identifier")


def classify_all(proposals: list) -> list[dict]:
    return [classify(p if isinstance(p, dict) else {}) for p in proposals]


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=False
    )
    if check and result.returncode != 0:
        raise ApplyError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


def current_branch(repo: Path) -> str:
    return git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def ensure_working_branch(repo: Path, stamp: str, base_branch: str) -> str:
    """Create or check out the isolated feature branch, then ASSERT isolation."""
    if not stamp or not str(stamp).strip():
        raise ApplyError("--stamp is required; the caller supplies it (the workflow runtime has no clock)")
    branch = f"{BRANCH_PREFIX}{str(stamp).strip()}"

    existing = git(repo, "branch", "--list", branch).stdout.strip()
    if existing:
        git(repo, "checkout", branch)
    else:
        base_exists = git(repo, "rev-parse", "--verify", base_branch, check=False).returncode == 0
        if base_exists:
            git(repo, "checkout", "-b", branch, base_branch)
        else:
            git(repo, "checkout", "-b", branch)

    landed = current_branch(repo)
    if landed != branch:
        raise ApplyError(f"expected to be on {branch} but HEAD is {landed}; aborting")
    # The invariant this whole phase exists to guarantee.
    if landed in PROTECTED_BRANCHES:
        raise ApplyError(f"refusing to operate on protected branch {landed!r}")
    return branch


# ---------------------------------------------------------------------------
# Guard suite (3.2)
# ---------------------------------------------------------------------------


def run_guards(repo: Path, guards, changed: Path | None = None) -> tuple[bool, str, str]:
    """Run every guard in order. Returns (passed, failing_guard_name, detail)."""
    for name, command in guards:
        result = subprocess.run(
            list(command), cwd=str(repo), capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip().splitlines()
            return False, name, " ".join(detail[-3:])[:400] if detail else f"exit {result.returncode}"
    if changed is not None and changed.suffix == ".sh":
        shell = subprocess.run(
            ["shellcheck", "--severity=warning", str(changed)],
            cwd=str(repo), capture_output=True, text=True, check=False,
        )
        if shell.returncode not in (0, 127):  # 127: shellcheck absent, not a failure
            detail = (shell.stdout or shell.stderr or "").strip().splitlines()
            return False, "shellcheck", " ".join(detail[:3])[:400]
    return True, "", ""


def apply_edit(path: Path, old: str, new: str) -> tuple[bool, str]:
    """Replace the FIRST occurrence of `old` with `new`. Returns (ok, reason)."""
    if not path.is_file():
        return False, f"target file does not exist: {path}"
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return False, "anchor text 'old' not found in the target file"
    if text.count(old) > 1:
        return False, f"anchor text 'old' is ambiguous ({text.count(old)} occurrences)"
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="")
    return True, ""


def apply_loop(repo: Path, proposals: list, decisions: list[dict], guards) -> dict:
    """Apply every ELIGIBLE proposal, guarding each and reverting on failure.

    Reverts restore an in-memory SNAPSHOT rather than running `git checkout --`.
    That is a deliberate correction to the plan's wording: two eligible edits can
    target the same file, and `git checkout --` reverts to HEAD, which would
    silently discard an earlier surviving edit along with the failing one.
    """
    applied: list[dict] = []
    quarantined: list[dict] = []
    by_id = {str(p.get("id", i)): p for i, p in enumerate(proposals) if isinstance(p, dict)}

    for decision in decisions:
        if decision["route"] != ELIGIBLE:
            continue
        proposal = by_id.get(decision["id"])
        if proposal is None:
            continue
        target = repo / proposal["target"]
        snapshot = target.read_text(encoding="utf-8") if target.is_file() else None

        ok, reason = apply_edit(target, proposal["old"], proposal["new"])
        if not ok:
            quarantined.append({**decision, "failing_guard": "apply", "detail": reason,
                                "target": proposal["target"]})
            continue

        passed, failing, detail = run_guards(repo, guards, target)
        if passed:
            applied.append({**decision, "target": proposal["target"]})
            continue

        # Auto-revert this ONE edit; the run continues with the next proposal.
        if snapshot is not None:
            target.write_text(snapshot, encoding="utf-8", newline="")
        quarantined.append({**decision, "failing_guard": failing, "detail": detail,
                            "target": proposal["target"]})

    return {"applied": applied, "quarantined": quarantined}


# ---------------------------------------------------------------------------
# Gap report (3.3)
# ---------------------------------------------------------------------------


def _rows(items: list[dict], columns) -> str:
    if not items:
        return "_None._\n"
    head = "| " + " | ".join(c[0] for c in columns) + " |\n"
    sep = "|" + "|".join("---" for _ in columns) + "|\n"
    body = ""
    for item in items:
        cells = [str(c[1](item)).replace("|", "\\|").replace("\n", " ") for c in columns]
        body += "| " + " | ".join(cells) + " |\n"
    return head + sep + body


def build_report(
    stamp: str,
    branch: str,
    decisions: list[dict],
    result: dict,
    proposals: list,
    unverified_models: list[str],
    diff_stat: str,
) -> str:
    """Render the per-run gap report. Deterministic: same inputs, same bytes."""
    by_id = {str(p.get("id", i)): p for i, p in enumerate(proposals) if isinstance(p, dict)}
    profile_only = [d for d in decisions if d["route"] == PROFILE_ONLY]
    rejected = [d for d in decisions if d["route"] == REJECTED]
    applied = result["applied"]
    quarantined = result["quarantined"]

    def model_of(d: dict) -> str:
        return str(by_id.get(d["id"], {}).get("model", "unknown"))

    def source_of(d: dict) -> str:
        return str(by_id.get(d["id"], {}).get("source_url", ""))

    lines = [
        f"# Prompting-Research Gap Report: {stamp}",
        "",
        f"**Branch**: `{branch}`",
        f"**Proposals considered**: {len(decisions)}",
        f"**Applied**: {len(applied)}  |  **Quarantined**: {len(quarantined)}  |  "
        f"**Routed to the profile layer**: {len(profile_only)}  |  **Rejected**: {len(rejected)}",
        "",
        "This report is generated deterministically from one run's results. Every shared-body edit listed as applied passed the full guard suite; every quarantined edit was reverted and left unapplied.",
        "",
        "## Applied to shared bodies",
        "",
        _rows(applied, [
            ("Proposal", lambda d: d["id"]),
            ("Model", model_of),
            ("Target", lambda d: f"`{d.get('target', '')}`"),
            ("Source", source_of),
        ]),
        "",
        "## Quarantined (auto-reverted, not applied)",
        "",
        _rows(quarantined, [
            ("Proposal", lambda d: d["id"]),
            ("Target", lambda d: f"`{d.get('target', '')}`"),
            ("Failing guard", lambda d: f"`{d.get('failing_guard', '')}`"),
            ("Detail", lambda d: d.get("detail", "")[:160]),
        ]),
        "",
        "## Routed to the profile layer only",
        "",
        "These findings are model-specific (declared, defaulted, or caught by the hard rail) and may never reach a shared body.",
        "",
        _rows(profile_only, [
            ("Proposal", lambda d: d["id"]),
            ("Model", model_of),
            ("Reason", lambda d: d["reason"][:200]),
        ]),
        "",
        "## Rejected proposals",
        "",
        _rows(rejected, [
            ("Proposal", lambda d: d["id"]),
            ("Reason", lambda d: d["reason"][:200]),
        ]),
        "",
        "## Branch diff summary",
        "",
        "```",
        diff_stat.strip() or "(no changes)",
        "```",
        "",
        "## Known-gaps entries to record",
        "",
    ]

    if not quarantined and not unverified_models:
        lines.append("_None: every eligible edit passed its guards, and every rostered model was verified._")
        lines.append("")
    else:
        for item in quarantined:
            lines += [
                f"##### QG-{item['id']} - shared-body edit quarantined by the `{item.get('failing_guard', '')}` guard",
                "",
                f"- **Source phase**: the `{stamp}` tune-prompting run.",
                f"- **Target**: `{item.get('target', '')}`.",
                f"- **Reason**: the edit was applied and then reverted because the `{item.get('failing_guard', '')}` guard failed: {item.get('detail', '')}",
                "- **Suggested next step**: fix the edit so the guard passes, or record the guidance in the profile layer instead.",
                "",
            ]
        for model in unverified_models:
            lines += [
                f"##### NI-{model} - model left UNVERIFIED by the `{stamp}` run",
                "",
                f"- **Source phase**: the `{stamp}` tune-prompting run.",
                f"- **Reason**: no claim for `{model}` survived verification, or the run stopped at the budget cap before reaching it.",
                "- **Suggested next step**: re-run the research for this model, or record why its vendor documentation could not be used.",
                "",
            ]

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _load(path: Path) -> dict:
    raw = sys.stdin.read() if str(path) == "-" else path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ApplyError("payload must be a JSON object")
    if not isinstance(payload.get("proposals"), list):
        raise ApplyError("payload.proposals must be an array")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apply-prompting-edits",
        description="Classify research findings and apply model-agnostic edits behind the guard suite.",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    for name in ("classify", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--input", type=Path, required=True, help="Proposals JSON, or - for stdin.")
        p.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root.")
        p.add_argument("--report", type=Path, help="Write the gap report here.")
        p.add_argument("--json", action="store_true", help="Emit the machine-readable result.")
        if name == "apply":
            p.add_argument("--stamp", required=True, help="Branch stamp, supplied by the caller.")
            p.add_argument("--base-branch", default="develop", help="Branch to cut from.")
            p.add_argument("--commit", action="store_true", help="Commit surviving edits (ask first).")
            p.add_argument(
                "--guard", action="append", default=None,
                help="Override a guard as 'name:command'. Repeatable. Defaults to the full suite.",
            )

    args = parser.parse_args(argv)
    repo: Path = args.repo.resolve()

    try:
        payload = _load(args.input)
    except (OSError, ValueError, ApplyError) as exc:
        print(f"[apply-edits] ERROR: {exc}", file=sys.stderr)
        return 1

    proposals = payload["proposals"]
    unverified = [str(m) for m in payload.get("unverified_models", [])]
    decisions = classify_all(proposals)

    if args.mode == "classify":
        report = build_report(
            payload.get("stamp", "classify-only"), "(not created)", decisions,
            {"applied": [], "quarantined": []}, proposals, unverified, "",
        )
        if args.report:
            args.report.write_text(report, encoding="utf-8", newline="\n")
        if args.json:
            print(json.dumps({"decisions": decisions}, indent=2))
        else:
            counts = {r: sum(1 for d in decisions if d["route"] == r)
                      for r in (ELIGIBLE, PROFILE_ONLY, REJECTED)}
            print(f"[apply-edits] classified {len(decisions)}: {counts}")
        return 0

    guards = DEFAULT_GUARDS
    if args.guard:
        parsed = []
        for spec in args.guard:
            name, _, command = spec.partition(":")
            if not command:
                print(f"[apply-edits] ERROR: --guard needs 'name:command', got {spec!r}", file=sys.stderr)
                return 1
            parsed.append((name, tuple(command.split())))
        guards = tuple(parsed)

    try:
        branch = ensure_working_branch(repo, args.stamp, args.base_branch)
        result = apply_loop(repo, proposals, decisions, guards)
        if args.commit and result["applied"]:
            if current_branch(repo) in PROTECTED_BRANCHES:
                raise ApplyError("refusing to commit on a protected branch")
            git(repo, "add", "-A")
            git(repo, "commit", "-m",
                f"chore(tune-prompting): {len(result['applied'])} guard-passing edit(s) [{args.stamp}]")
        diff_stat = git(repo, "diff", "--stat", f"{args.base_branch}...HEAD", check=False).stdout
    except ApplyError as exc:
        print(f"[apply-edits] ERROR: {exc}", file=sys.stderr)
        return 1

    report = build_report(args.stamp, branch, decisions, result, proposals, unverified, diff_stat)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8", newline="\n")

    if args.json:
        print(json.dumps({"branch": branch, "decisions": decisions, **result}, indent=2))
    else:
        print(f"[apply-edits] branch {branch}: {len(result['applied'])} applied, "
              f"{len(result['quarantined'])} quarantined")
        if not args.commit and result["applied"]:
            print("  Edits are UNCOMMITTED on the branch. Re-run with --commit once reviewed.")
        print("  STOP: this branch is for human merge. Never merged automatically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
