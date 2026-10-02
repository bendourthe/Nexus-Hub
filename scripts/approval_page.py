#!/usr/bin/env python3
"""Render the plain-language approval page and its paste line(s).

Installed at ~/.nexus-hub/scripts/approval_page.py beside approval_binding.py,
which imports it for the paste-line templates, and run_plan.py, which imports it
for the headless goal line. The page layout is documented in
catalog/skills/workflow/implement-phase/references/approval-page.md; the rule it
serves is the completion contract's "Approval origin" section.

    paste_set   the line(s) a page tells the user to paste, and every whole
                message that records the approval, chosen per platform from
                GOAL_CAPTURE
    goal_line   the fixed-template /goal line (with or without the approval code)
    goal_text   the same goal as a plain sentence, for a platform with no goal command
    render_page the page text, built ONLY from the JSON `record render --json`
                prints, so the page and the bound data can never disagree

Every paste line is built from a fixed template plus a validated version token,
a validated base32 code, and (for an answer) a blocker index. No plan title, plan
text, gap text, path, script name, or round nonce ever reaches a paste line.
Plan titles, plan goals, and gap titles appear only as quoted, escaped data in the
details list that follows the paste line. A field that fails validation renders
nothing: PageError is raised and the caller reports it.

    python approval_page.py render <file|->     print the page for that JSON
    python approval_page.py goal-line vX.Y[.Z]  print the goal line without a code
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

SCOPE_RE = re.compile(r"^v\d+\.\d+(?:\.\d+)?\Z", re.ASCII)
MINOR_RE = re.compile(r"^v\d+\.\d+\Z", re.ASCII)
CODE_RE = re.compile(r"^[A-Z2-7]{8}\Z", re.ASCII)
GAP_ID_RE = re.compile(r"^v\d+\.\d+(?:\.\d+)?#[A-Z]{2,4}-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\Z", re.ASCII)
VENDOR_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}\Z", re.ASCII)
ACTIONS = ("create", "answer", "pause", "resume", "retire")
MAX_PASTE = 300
# The goal names every step of the run, so it needs more room than an approval line.
# Claude Code documents a 4,000-character /goal condition; no other platform in
# docs/policy/completion-levers.json documents a limit, so the cap stays well under it.
MAX_GOAL = 1000
DETAIL_MAX = 200
DETAIL_GAPS = 10
GOAL_CAPTURE_VALUES = ("verbatim", "not-captured", "no-goal", "unverified")

# Row -> (goal_capture value, the platform has a typed goal command). A copy of
# docs/policy/completion-levers.json, which is not installed; the drift test in
# tests/validators/test_approval_page.py fails when the two disagree. The second
# field is `native_goal.status == "VERIFIED"`, except copilot/vscode, whose goal
# lever is the Autopilot mode picker rather than a typed command.
GOAL_CAPTURE: dict[str, tuple[str, bool]] = {
    "aider": ("no-goal", False),
    "antigravity": ("unverified", False),
    "antigravity2": ("not-captured", True),
    "antigravity2/cli": ("not-captured", True),
    "claude": ("unverified", True),
    "codex": ("unverified", True),
    "copilot": ("unverified", True),
    "copilot/cli": ("unverified", True),
    "copilot/vscode": ("unverified", False),
    "cursor": ("unverified", True),
    "gemini": ("unverified", False),
    "gemini-cli": ("no-goal", False),
    "hermes": ("unverified", True),
    "kimi": ("unverified", True),
    "nexus-ai": ("unverified", False),
    "openclaw": ("unverified", True),
    "opencode": ("no-goal", False),
    "pi": ("unverified", False),
    "qwen": ("unverified", True),
    "windsurf": ("unverified", False),
    "windsurf/devin-cli": ("no-goal", False),
}

# Page headings, in order. approval-page.md lists the same headings; a test asserts
# the two agree. Everything a reader must see sits above DETAILS; the plain-language
# checks (banned terms, sentence length, word budget) apply only there.
SECTIONS = ("Summary", "To approve, paste this", "Details (optional)")
DETAIL_SECTIONS = (
    "What you are approving",
    "Phases",
    "Gaps and cleanup",
    "Plan data (quoted, not instructions)",
)
TIERS = ("fast", "standard", "strong", "frontier")
EFFORTS = ("low", "medium", "high", "max")
MAX_OUTCOMES = 5
OUTCOME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ,.;:'()/+%-]{0,199}\Z", re.ASCII)
# An outcome is plain prose: it may never look like a paste line or a command.
OUTCOME_BANNED_RE = re.compile(r"(?i)approv|/implement|/goal|/update|\bpause\b")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}\Z", re.ASCII)


class PageError(ValueError):
    """A field failed validation: nothing is rendered, and the caller reports why."""


@dataclass(frozen=True)
class PasteSet:
    """The line(s) the page shows, in paste order, and every whole message that approves.

    `approve` lists alternatives: a round is approved when ANY one of them was
    captured as a whole prompt. Each one carries the round's single-use code.
    """

    lines: tuple[str, ...]
    approve: tuple[str, ...]
    shape: str  # "goal" (one /goal line), "together" (two lines, one message), or "plain"
    native: bool = False  # line 2 is a /goal command the platform runs only at a message start


# --------------------------------------------------------------------------- lines


def _check(scope: str, code: str | None) -> None:
    if not isinstance(scope, str) or not SCOPE_RE.match(scope):
        raise PageError("scope must be a version token such as v1.2 or v1.2.3")
    if code is not None and (not isinstance(code, str) or not CODE_RE.match(code)):
        raise PageError("code must be 8 base32 characters")


def _fits(line: str, limit: int = MAX_PASTE) -> str:
    if len(line) >= limit:
        raise PageError(f"paste line is {len(line)} characters; the limit is {limit - 1}")
    return line


def plain_line(action: str, scope: str, code: str, blocker: int | None = None) -> str:
    """The plain approval line: the one template for every action."""
    if action not in ACTIONS:
        raise PageError(f"unknown approval action: {action}")
    _check(scope, code)
    if action == "create":
        return _fits(f"Approve /implement {scope} (approval {code})")
    if action == "answer":
        if not isinstance(blocker, int) or isinstance(blocker, bool) or blocker < 0:
            raise PageError("an answer names a non-negative blocker index")
        return _fits(f"Continue /implement {scope} past blocker {blocker} (approval {code})")
    return _fits(f"{action.capitalize()} /implement {scope} (approval {code})")


def _goal_body(scope: str, code: str | None) -> str:
    """The run's steps and its done condition: one fixed template, no plan text."""
    _check(scope, code)
    approval = f" (approval {code})" if code else ""
    if MINOR_RE.match(scope):
        done = f"starts with MINOR COMPLETE {scope}"
        steps = (
            f"1) implement every task in every phase of every {scope} plan; "
            "2) add or update the tests and CI/CD the work needs, and make both pass on the final tree; "
            "3) fix the open known gaps; "
            "4) run /update release for each plan; "
            "5) merge every pull request, then delete the merged branches, worktrees, and their local copies; "
            "6) move every gap still open to the next minor's known-gaps file; "
            f"7) archive the {scope} folder and delete any folder left empty."
        )
    else:
        done = f"starts with PLAN COMPLETE followed by the {scope} plan file"
        steps = (
            "1) implement every task in every phase of the plan; "
            "2) add or update the tests and CI/CD the work needs, and make both pass on the final tree; "
            "3) fix the open known gaps; "
            "4) run /update release; "
            "5) merge every pull request, then delete the merged branches, worktrees, and their local copies; "
            "6) record every gap still open in the next version's known-gaps section; "
            "7) when this is the last plan in its version folder, archive that folder and delete any folder left empty."
        )
    return (
        f"Finish /implement {scope}{approval}. Do every step: {steps} "
        f"Done only when the completion check's first output line {done}; "
        "stop and report when it starts with BLOCKED or PAUSED."
    )


def goal_line(scope: str, code: str | None = None) -> str:
    """The native goal line. With a code it is also an approval line; without one
    (a runner-launched session, which is never captured) it only sets the goal.

    The condition names the completion check's verdict line (`MINOR COMPLETE vX.Y
    <head> <nonce>`, or `PLAN COMPLETE <plan file> <head> <nonce>`), never a string
    the agent could simply print, because the goal evaluator reads the transcript.
    The numbered steps restate what the run must do; the checker, not the goal,
    decides whether it is done.
    """
    return _fits("/goal " + _goal_body(scope, code), MAX_GOAL)


def goal_text(scope: str, code: str | None = None) -> str:
    """The same goal as a plain sentence, for a platform without a goal command."""
    return _fits("Goal: " + _goal_body(scope, code), MAX_GOAL)


def _together(first: str, second: str) -> tuple[str, str]:
    """Both orders of a two-line message; a capture compares whitespace-normalized text."""
    return f"{first}\n{second}", f"{second}\n{first}"


def platform_capture(platform: str | None) -> tuple[str, bool]:
    """(goal_capture, has a goal command); an unknown platform is `unverified`."""
    return GOAL_CAPTURE.get(platform or "", ("unverified", False))


def paste_set(
    action: str,
    scope: str,
    code: str,
    blocker: int | None = None,
    platform: str | None = None,
) -> PasteSet:
    """The exact paste line(s) for a round. Only a create round sets a goal.

    A create round always shows the goal, and one pasted message always approves,
    on every platform. Where the hook sees a typed /goal (`verbatim`) the /goal line
    alone is the paste. Everywhere else the page shows two lines to paste together
    as one ordinary message, which every hook captures: the approval line, then the
    /goal line (or the goal as a sentence, where there is no goal command). Pasting
    either line alone, or both together, also approves, so a user who sends them as
    two messages or as one is never refused. The /goal line alone is not accepted
    where the hook cannot see it (`not-captured`), because it can never arrive there.
    """
    plain = plain_line(action, scope, code, blocker)
    if action != "create":
        return PasteSet((plain,), (plain,), "plain")
    capture, has_goal = platform_capture(platform)
    if capture == "verbatim":
        goal = goal_line(scope, code)
        return PasteSet((goal,), (goal, plain, *_together(plain, goal)), "goal")
    second = goal_line(scope, code) if has_goal else goal_text(scope, code)
    accepted = (plain, *_together(plain, second))
    if capture != "not-captured":
        accepted += (second,)
    return PasteSet((plain, second), accepted, "together", native=has_goal)


# --------------------------------------------------------------------------- page

# Strict shapes for every bound value the page states in words. A value outside
# them renders nothing (PageError), so no approvals-file text reaches the page.
BRANCH_RE = re.compile(r"^(?!refs/)(?!-)(?!.*\.\.)(?!.*//)(?!.*\.lock$)[A-Za-z0-9][A-Za-z0-9._/-]{0,99}(?<![./])\Z", re.ASCII)
REPO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}\Z", re.ASCII)
REMOTE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,39}\Z", re.ASCII)
SURFACE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}\Z", re.ASCII)
GAP_TYPES = ("NI", "DF", "BG", "MT", "WN", "QG")
MAX_BOUND_COUNT = 20


def quoted(value: object) -> str:
    """Untrusted text as one inert quoted token: JSON-escaped, capped, and with
    backticks and tildes escaped, so it can never open or close a code fence."""
    text = " ".join(str(value).split())
    if len(text) > DETAIL_MAX:
        text = text[: DETAIL_MAX - 3] + "..."
    return json.dumps(text, ensure_ascii=True).replace("`", "\\u0060").replace("~", "\\u007e")


def _joined(items: list[str]) -> str:
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _count(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


def _order(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.lstrip("v").split("."))


def _next_minor(scope: str) -> str:
    major, minor = scope.lstrip("v").split(".")[:2]
    return f"v{int(major)}.{int(minor) + 1}"


def _classes(page: dict) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for entry in page.get("classes") or []:
        if not isinstance(entry, dict) or not isinstance(entry.get("class"), str):
            raise PageError("an approval class is not a named object")
        found[entry["class"]] = entry
    return found


def _minor_token(token: str) -> str:
    """`vX.Y` for a version token of either length."""
    return "v" + ".".join(token.lstrip("v").split(".")[:2])


def _scope_token(page: dict) -> str:
    scope = page.get("scope") or {}
    token = scope.get("minor") if scope.get("kind") == "minor" else scope.get("version")
    if not isinstance(token, str) or not SCOPE_RE.match(token):
        raise PageError("the page scope is not a version token")
    return token


def _versions(page: dict) -> list[str]:
    found = []
    for release in page.get("releases") or []:
        version = str((release or {}).get("version", ""))
        if not SCOPE_RE.match(version):
            raise PageError("a release version is not a version token")
        found.append(version)
    if not found:
        raise PageError("the page lists no release")
    return found


def _branch(value: object) -> str:
    if not isinstance(value, str) or not BRANCH_RE.match(value):
        raise PageError("a branch name is not a plain ref name")
    return value


def _repo(page: dict) -> str:
    repo = page.get("repo")
    if not isinstance(repo, str) or not REPO_RE.match(repo):
        raise PageError("the repository is not owner/name")
    return repo


def _bound_count(entry: dict, default: int | None = None) -> int | None:
    bound = entry.get("bound", default)
    if bound is None:
        return None
    if not isinstance(bound, int) or isinstance(bound, bool) or not 0 <= bound <= MAX_BOUND_COUNT:
        raise PageError(f"the {entry['class']} bound is not a count from 0 to {MAX_BOUND_COUNT}")
    return bound


def _no_bound(entry: dict) -> None:
    if entry.get("bound") not in (None, [], {}):
        raise PageError(f"the {entry['class']} class takes no bound")


def _cleanup_counts(page: dict) -> tuple[int, int]:
    estimate = (page.get("cleanup") or {}).get("estimate") or {}
    groups = estimate.values() if MINOR_RE.match(_scope_token(page)) else [estimate]
    branches = worktrees = 0
    for group in groups:
        if isinstance(group, dict):
            branches += len(group.get("branches") or [])
            worktrees += len(group.get("worktrees") or [])
    return branches, worktrees


def _gap_ids(values: object, what: str) -> list[str]:
    if values in (None, []):
        return []
    if not isinstance(values, list) or not all(isinstance(i, str) and GAP_ID_RE.match(i) for i in values):
        raise PageError(f"the {what} list holds a malformed gap id")
    return list(values)


def _moves(page: dict, minor: bool, target: str) -> list[str]:
    if not minor:
        if "carry-gaps" in _classes(page):
            return ["Any gap it leaves open is recorded in the next version's known-gaps section.",
                    "Each recorded gap keeps a note saying where it came from."]
        if "defer-gaps" in _classes(page):
            return ["A single-plan run moves no gaps to another version.", "It may leave some open gaps for later, as listed below."]
        return ["A single-plan run moves no gaps to another version.", "Any gap it cannot fix stays open and stops the run."]
    ids = _gap_ids(page.get("migratable_gaps"), "migratable gap")
    if not ids:
        return [f"It will move no gaps to {target}.", "Any gap it cannot fix stops the run and waits for you."]
    named = _gap_ids((_classes(page).get("gap-migration") or {}).get("named"), "named gap")
    lines = [f"If it cannot fix them, it may move these gaps to {target}: {_joined(ids)}.",
             "Each moved gap keeps a note saying where it came from."]
    if named:
        lines.append(f"These involve security or high severity, and you approve them by name: {_joined(named)}.")
    return lines


def _push_merge(page: dict, entry: dict, minor: bool) -> str:
    repo = _repo(page)
    branches = page.get("branches") or {}
    target = _branch(branches.get("target") or "develop")
    bound = entry.get("bound")
    extra = ""
    if bound not in (None, {}):
        if not isinstance(bound, dict) or not set(bound) <= {"remote", "source", "target", "repo"}:
            raise PageError("the push-merge bound names an unknown field")
        parts = []
        for key in ("remote", "source", "target", "repo"):
            if key in bound:
                value = bound[key]
                ok = (REMOTE_RE if key == "remote" else REPO_RE if key == "repo" else BRANCH_RE).match(str(value))
                if not isinstance(value, str) or not ok:
                    raise PageError(f"the push-merge {key} is not a plain name")
                # The page's own repo and branches are what the record freezes; a bound
                # that names different ones would make the sentence contradict the record.
                page_value = {"repo": repo, "target": target, "source": branches.get("source")}.get(key)
                if key != "remote" and page_value is not None and value != page_value:
                    raise PageError(f"the push-merge {key} differs from the page's {key}")
                parts.append(f"{key} {value}")
        extra = f" It is limited to {_joined(parts)}."
    if minor:
        return f"Push each plan's branch to {repo} and merge it into {target} once its checks pass.{extra}"
    source = _branch(branches.get("source")) if branches.get("source") else "the plan's branch"
    return f"Push {source} to {repo} and merge it into {target} once its checks pass.{extra}"


def _release(page: dict, entry: dict, releases: list[str]) -> str:
    bound = entry.get("bound")
    if bound is not None:
        wanted = bound if isinstance(bound, list) else [bound]
        if not all(isinstance(v, str) and SCOPE_RE.match(v) for v in wanted) or not set(wanted) <= set(releases):
            raise PageError("the release bound is not one of the listed versions")
    return f"Publish the release, tag, and release pull request for {_joined(releases)}."


def _defer(entry: dict) -> str:
    kinds = entry.get("bound") or []
    if not isinstance(kinds, list) or not kinds or not set(kinds) <= set(GAP_TYPES):
        raise PageError("the defer-gaps bound is not a list of gap kinds")
    return f"Leave open gaps of these kinds for a later version: {_joined(sorted(kinds))}."


def _approval_line(page: dict, name: str, entry: dict, minor: bool, releases: list[str], target: str) -> str:
    """One plain sentence for one hashed approval class, or PageError."""
    token = _scope_token(page)
    if name == "push-merge":
        return _push_merge(page, entry, minor)
    if name == "release":
        return _release(page, entry, releases)
    if name == "repush":
        n = _bound_count(entry, 3)
        return f"Push a fix again, up to {_count(n or 0, 'time')}, after reproducing a failed check on this computer."
    if name == "release-notes":
        _no_bound(entry)
        return "Write and publish the release notes."
    if name == "refactor-moves":
        _no_bound(entry)
        return "Move or rename files, but only inside folders the plan already touches."
    if name == "spend":
        return "Use paid services within the spending caps the summary names."
    if name == "defer-gaps":
        return _defer(entry)
    if name == "unattended-with-bypass":
        _no_bound(entry)
        return "Run the agent with permission prompts turned off, so it does not stop to ask before each tool."
    if name == "cleanup-merged":
        _no_bound(entry)
        return "Delete branches and worktrees that are merged and idle, checking each one right before removing it."
    if name == "gap-migration":
        ids = _gap_ids(entry.get("bound"), "gap-migration")
        return f"Move the {_count(len(ids), 'listed gap')} to {target} when a gap cannot be fixed in this run."
    if name == "archive-minor":
        _no_bound(entry)
        if MINOR_RE.match(token):
            return f"Archive the {token} documents after the final pull request merges."
        return (f"Archive the {_minor_token(token)} documents, and delete any folder left empty, "
                "if this is the last plan of that version.")
    if name == "carry-gaps":
        named = _gap_ids(entry.get("named"), "carry-gaps named")
        line = ("Record every gap this run leaves open in the next version's known-gaps section, "
                "with a note saying where it came from.")
        if named:
            line += f" These involve security or high severity and are approved by name: {_joined(named)}."
        return line
    if name == "minor-close-pr":
        # The bound is the closing pull request's re-push limit (runbook "Minor close"
        # step 7: re-push "within the recorded `minor-close-pr` repush bound").
        n = _bound_count(entry)
        retry = f" If a required check fails, it may push a fix up to {_count(n, 'time')}." if n is not None else ""
        return (f"Open one final pull request that closes {_minor_token(token)} and merge it once its checks pass, "
                f"then copy any newer main changes into develop.{retry}")
    if name.startswith("ask-first:"):
        surface = name.split(":", 1)[1]
        if not SURFACE_RE.match(surface):
            raise PageError("an ask-first surface is not a plain name")
        _no_bound(entry)
        return f"Change the {surface} area, which the plan marks as ask-first."
    raise PageError(f"no plain-language sentence exists for approval class {name}")


def _approvals(page: dict, minor: bool, releases: list[str], target: str) -> list[str]:
    names = _classes(page)
    if not names:
        raise PageError("the page lists no approval class")
    lines = ["Your paste allows each of these without asking again:"]
    lines += [f"- {_approval_line(page, n, e, minor, releases, target)}" for n, e in names.items()]
    return lines


def _merged_rule(page: dict) -> bool:
    rule = (page.get("cleanup") or {}).get("rule")
    if rule not in ("merged-and-idle", "run-owned"):
        raise PageError("the cleanup rule is unknown")
    return rule == "merged-and-idle"


def _open_gaps(display: dict) -> dict[str, int]:
    counts = display.get("gap_counts") or {}
    if not isinstance(counts, dict):
        raise PageError("gap counts are not a mapping")
    return {k: v for k, v in counts.items()
            if SCOPE_RE.match(str(k)) and isinstance(v, int) and not isinstance(v, bool) and v > 0}


def _caps(page: dict) -> list[str]:
    raw = page.get("spend_caps") or {}
    bound = (_classes(page).get("spend") or {}).get("bound")
    if not isinstance(raw, dict) or (bound is not None and not isinstance(bound, dict)):
        raise PageError("a spending cap is not a vendor-to-number mapping")
    shown = []
    for vendor, cap in sorted({**raw, **(bound or {})}.items()):
        if not VENDOR_RE.match(str(vendor)) or not isinstance(cap, (int, float)) or isinstance(cap, bool) or not 0 <= cap < 1e6:
            raise PageError("a spending cap is not a vendor name with a number")
        shown.append(f"USD {cap:g} for {vendor}")
    return shown


# --------------------------------------------------------------------------- plan profile

# A rough guide only: minutes of building per open task at each effort level, then
# testing and fixing as a share of building, then a fixed time per release. These
# numbers set the summary's time estimate; tune them here, nowhere else.
MINUTES_PER_TASK = {"low": 10, "medium": 20, "high": 30, "max": 40}
TESTING_SHARE = 0.3
FIXING_SHARE = 0.2
RELEASE_MINUTES = 45


def _phases(display: dict) -> list[dict]:
    """The plan phases whose tier, effort, and task count all pass a strict check."""
    found = []
    for entry in display.get("phases") or []:
        if not isinstance(entry, dict):
            continue
        version, tier, effort = str(entry.get("version", "")), entry.get("tier"), entry.get("effort")
        phase, tasks = entry.get("phase"), entry.get("tasks")
        if (SCOPE_RE.match(version) and tier in TIERS and effort in EFFORTS
                and isinstance(phase, int) and not isinstance(phase, bool) and 0 < phase < 100
                and isinstance(tasks, int) and not isinstance(tasks, bool) and 0 <= tasks < 1000):
            found.append({"version": version, "phase": phase, "tier": tier, "effort": effort, "tasks": tasks})
    return found


def whole_run_setting(phases: list[dict]) -> tuple[str, str, list[dict]] | None:
    """(tier, effort, phases that want more) for a reader who will not switch per phase.

    The task-weighted average of each scale, rounded to the nearest step (a half
    rounds up); every phase above it is listed so the reader can switch for those.
    """
    if not phases:
        return None
    weights = [max(p["tasks"], 1) for p in phases]

    def average(scale: tuple[str, ...], key: str) -> int:
        total = sum(w * scale.index(p[key]) for w, p in zip(weights, phases))
        return min(len(scale) - 1, (2 * total + sum(weights)) // (2 * sum(weights)))

    tier, effort = average(TIERS, "tier"), average(EFFORTS, "effort")
    above = [p for p in phases if TIERS.index(p["tier"]) > tier or EFFORTS.index(p["effort"]) > effort]
    return TIERS[tier], EFFORTS[effort], above


def time_estimate(phases: list[dict], releases: int) -> dict[str, float]:
    """Rough hours per part of the run: building, testing, fixing, releasing."""
    build = sum(MINUTES_PER_TASK[p["effort"]] * max(p["tasks"], 1) for p in phases) / 60
    parts = {"building": build, "testing": build * TESTING_SHARE, "fixing": build * FIXING_SHARE,
             "releasing": releases * RELEASE_MINUTES / 60}
    return {k: round(v * 2) / 2 for k, v in parts.items()}


def _hours(value: float) -> str:
    return f"{value:g} h"


def _phase_label(entry: dict, minor: bool) -> str:
    return f"{entry['version']} phase {entry['phase']}" if minor else f"phase {entry['phase']}"


def _outcomes(display: dict) -> list[str]:
    raw = display.get("outcomes") or []
    if not isinstance(raw, list) or len(raw) > MAX_OUTCOMES:
        raise PageError(f"the summary outcomes are not a list of at most {MAX_OUTCOMES}")
    shown = []
    for item in raw:
        text = " ".join(str(item).split()) if isinstance(item, str) else ""
        if not OUTCOME_RE.match(text) or OUTCOME_BANNED_RE.search(text) or len(text.split()) > 25:
            raise PageError("a summary outcome is not one plain sentence of at most 25 words")
        shown.append(text if text.endswith(".") else text + ".")
    return shown


def _parallel(display: dict) -> str:
    parallel = display.get("parallel")
    if not isinstance(parallel, dict) or parallel.get("checked") is not True:
        return "Not checked yet"
    plans = []
    for entry in parallel.get("plans") or []:
        version, slug = str((entry or {}).get("version", "")), str((entry or {}).get("slug", ""))
        if not SCOPE_RE.match(version) or not SLUG_RE.match(slug):
            raise PageError("a parallel plan is not a version and a plain slug")
        plans.append(version)
    return _joined(plans) if plans else "No other queued plan can"


# --------------------------------------------------------------------------- summary


def _summary(page: dict, display: dict, releases: list[str], minor: bool, target: str) -> list[str]:
    """What the run does and leaves behind, how to run it, and the two limits.

    Every hard-to-undo result (a release, a deletion, the archive, prompts off) has
    its own row whenever its class is approved; mechanics stay under Details.
    """
    names = _classes(page)
    outcomes = _outcomes(display) or ["The plan's own goal is quoted under Details."]
    rows = []
    if "release" in names:
        rows.append(("Released", _joined(releases)))
    else:
        rows.append(("Released", "Nothing: it stops and asks before releasing"))
    total = sum(_open_gaps(display).values())
    fixed = f"{_count(total, 'known problem')}" if total else "No known problems are open today"
    movable = _gap_ids(page.get("migratable_gaps"), "migratable gap") if minor else []
    if movable:
        fixed += f"; {len(movable)} may move to {target}"
    elif not minor and "defer-gaps" in names:
        fixed += "; some may wait for a later version"
    rows.append(("Fixed", fixed))
    if minor and "archive-minor" in names:
        rows.append(("Archived", f"The {_scope_token(page)} documents"))
    elif "archive-minor" in names:
        rows.append(("Archived", f"The {_minor_token(_scope_token(page))} documents, if this is their last plan"))
    if _merged_rule(page):
        rows.append(("Cleaned up", "Merged branches and working folders nobody is using"))
    else:
        rows.append(("Cleaned up", "Only this run's own branch and working folder, once merged"))
    if "unattended-with-bypass" in names:
        rows.append(("Permission prompts", "Off for the whole run"))
    phases = _phases(display)
    setting = whole_run_setting(phases)
    if setting:
        tier, effort, above = setting
        more = f"; more for {_count(len(above), 'phase')}, see Phases" if above else ""
        rows.append(("Run it on", f"{tier.capitalize()} models at {effort} effort{more}"))
        hours = time_estimate(phases, len(releases) if "release" in names else 0)
        rows.append(("Time", f"About {_hours(sum(hours.values()))}, rough: " + ", ".join(
            f"{_hours(v)} {k}" for k, v in hours.items())))
    rows.append(("In parallel", _parallel(display)))
    caps = _caps(page)
    if caps:
        never = f"**Never without asking you: changes to CI, permissions, or secrets, or paid API use beyond {_joined(caps)}.**"
    else:
        never = "**Never without asking you: changes to CI, permissions, or secrets, and any paid API use.**"
    return ["**What this run will do:**", "", *(f"- {o}" for o in outcomes), "",
            "| | Result |", "|---|---|", *(f"| {k} | {v} |" for k, v in rows), "", never, "",
            "**Stop any time: type /implement pause**"]


def _paste_section(paste: PasteSet) -> list[str]:
    # The binding records only a whole captured prompt equal to an approving message,
    # so an added word makes the approval silently fail: the page says so plainly.
    body = ["```text", *paste.lines, "```", ""]
    if paste.shape == "goal":
        return [*body, ("Paste this line as one message, with nothing added. "
                        "It approves everything listed under Details and sets the run's goal.")]
    body.append("Copy both lines and paste them as one message, with nothing added. "
                "It approves everything listed under Details and gives the run its goal.")
    if paste.native:
        body += ["", "Then send the second line again by itself to start this tool's goal tracker."]
    return body


# --------------------------------------------------------------------------- details


def _phase_detail(display: dict, minor: bool) -> list[str]:
    phases = _phases(display)
    setting = whole_run_setting(phases)
    if not setting:
        return ["The plan names no per-phase model or effort, so no setting or time estimate is shown."]
    tier, effort, above = setting
    rows = [f"| {_phase_label(p, minor)} | {p['tasks']} | {p['tier']} | {p['effort']} |" for p in phases]
    lines = ["| Phase | Open tasks | Model | Effort |", "|---|---|---|---|", *rows, "",
             f"- Whole run on one setting: {tier} models at {effort} effort, the task-weighted average."]
    if above:
        lines.append(f"- Switch up for {_joined([_phase_label(p, minor) for p in above])} if you can.")
    minutes = _joined([str(m) for m in MINUTES_PER_TASK.values()])
    lines.append(f"- The time allows {minutes} minutes per open task at {_joined(list(MINUTES_PER_TASK))} effort, "
                 f"plus {round(TESTING_SHARE * 100)}% for testing, "
                 f"{round(FIXING_SHARE * 100)}% for fixing, and {RELEASE_MINUTES} minutes per release.")
    return lines


def _gaps_and_cleanup(page: dict, display: dict, releases: list[str], minor: bool, target: str) -> list[str]:
    clean = _open_gaps(display)
    if clean:
        parts = [f"{n} in {v}" for v, n in sorted(clean.items(), key=lambda kv: _order(kv[0]), reverse=True)]
        lines = [f"- It will try to fix {_count(sum(clean.values()), 'open gap')}: {_joined(parts)}."]
    else:
        lines = ["- There are no open gaps to fix today."]
    if display.get("gaps_unreadable"):
        lines.append("- Some gap lists could not be read today, so this count may be low.")
    lines += [f"- {line}" for line in _moves(page, minor, target)]
    if _merged_rule(page):
        lines.append("- Cleanup removes any branch or worktree merged into the target branch and idle, "
                     "even one another session made, unless a live run still owns it.")
    else:
        lines.append("- Cleanup removes only the branch and worktree this run created, once merged.")
    lines.append("- Each item is checked again right before removal; anything not verified as merged is kept and listed.")
    names = _classes(page)
    shipped = len(releases) if "release" in names else 0
    prs = len(releases) + (1 if minor and "minor-close-pr" in names else 0)
    branches, worktrees = _cleanup_counts(page)
    lines.append(f"- Expect {_count(shipped, 'release')}, {_count(shipped, 'tag')}, and {_count(prs, 'pull request')}; "
                 f"cleanup would remove {_count(branches, 'branch', 'branches')} and "
                 f"{_count(worktrees, 'worktree')} today.")
    return lines


def _details(page: dict, display: dict) -> list[str]:
    """Every untrusted value, JSON-quoted, inside ONE fenced text block, so no
    Markdown, link, or HTML in a title, goal, gap, or reason is ever rendered."""
    rows = []
    for member in display.get("plans") or []:
        if not isinstance(member, dict):
            continue
        version = str(member.get("version", ""))
        label = version if SCOPE_RE.match(version) else "plan"
        rows.append(f"{label} title: {quoted(member.get('title', ''))}")
        if member.get("goal"):
            rows.append(f"{label} goal: {quoted(member['goal'])}")
        if member.get("path"):
            rows.append(f"{label} file: {quoted(member['path'])}")
    gaps = [g for g in display.get("gaps") or [] if isinstance(g, dict) and GAP_ID_RE.match(str(g.get("id", "")))]
    rows += [f"gap {gap['id']}: {quoted(gap.get('title', ''))}" for gap in gaps[:DETAIL_GAPS]]
    if len(gaps) > DETAIL_GAPS:
        rows.append(f"and {len(gaps) - DETAIL_GAPS} more open gaps in the known-gaps files")
    parallel = display.get("parallel") if isinstance(display.get("parallel"), dict) else {}
    for entry in parallel.get("plans") or []:
        if isinstance(entry, dict) and SCOPE_RE.match(str(entry.get("version", ""))):
            rows.append(f"can run in parallel: {entry['version']} {quoted(entry.get('slug', ''))}")
    for excluded in page.get("excluded") or []:
        if isinstance(excluded, dict):
            rows.append(f"not included: {quoted(excluded.get('version', ''))} ({quoted(excluded.get('reason', ''))})")
    return ["```text", *(rows or ["none"]), "```"]


def _section(title: str, body: list[str], level: int = 2) -> list[str]:
    return [f"{'#' * level} {title}", "", *body, ""] if body else []


def _action_page(data: dict, paste: PasteSet) -> str:
    action = data["action"]
    scope = data["scope"]
    verb = {"answer": "continue past the blocker", "pause": "pause", "resume": "resume", "retire": "retire the run record"}[action]
    out = _section("What this will do", [f"This will {verb} for /implement {scope}.", "Nothing else changes."])
    out += _section("To approve, paste this line",
                    ["Paste this line as your whole message, with nothing added.", "", "```text", paste.lines[0], "```"])
    return "\n".join(out).rstrip() + "\n"


def render_page(data: dict) -> str:
    """The page for one `record render --json` object. Raises PageError, never partial."""
    if not isinstance(data, dict):
        raise PageError("render data must be a JSON object")
    action, scope, code = data.get("action"), data.get("scope"), data.get("code")
    page, display = data.get("page"), data.get("display") or {}
    if not isinstance(page, dict) or not isinstance(display, dict):
        raise PageError("render data needs a page object")
    paste = paste_set(str(action), str(scope), str(code), data.get("blocker"), data.get("platform"))
    # The lines the binding stored must be exactly the lines rebuilt from validated fields.
    if list(paste.lines) != list(data.get("paste") or []):
        raise PageError("the stored paste lines do not match the validated template")
    if action != "create":
        return _action_page(data, paste)
    if _scope_token(page) != scope:
        raise PageError("the page scope does not match the paste scope")
    minor = bool(MINOR_RE.match(scope))
    releases = _versions(page)
    target = _next_minor(scope)
    details = [
        _approvals(page, minor, releases, target),
        _phase_detail(display, minor),
        _gaps_and_cleanup(page, display, releases, minor, target),
        _details(page, display),
    ]
    out = _section(SECTIONS[0], _summary(page, display, releases, minor, target))
    out += _section(SECTIONS[1], _paste_section(paste))
    out += [f"## {SECTIONS[2]}", ""]
    for title, body in zip(DETAIL_SECTIONS, details):
        out += _section(title, body, level=3)
    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------------------- record render output


def render_data(pending: dict, *, scope: str, blocker: int | None, display: dict | None) -> dict:
    """The canonical JSON `record render --json` prints, and the only input of render_page.

    `page` is the hashed page the code is derived from; `display` holds what the
    page shows beside it without binding it (plan titles and goals, gap counts and
    titles), so a changed title never refuses a paste.
    """
    return {
        "action": pending["action"],
        "scope": scope,
        "code": pending["code"],
        "blocker": blocker,
        "platform": pending.get("platform"),
        "shape": pending.get("shape"),
        "paste": list(pending["paste_lines"]),
        "page": pending["page"],
        "display": display or {},
    }


def emit(data: dict, mode: str) -> int:
    """Print `record render` output: `json`, `page`, or the bare paste line(s).

    Returns 0, or 2 after reporting a PageError with nothing on stdout.
    """
    if mode == "json":
        print(json.dumps(data, sort_keys=True))
        return 0
    if mode == "page":
        try:
            text = render_page(json.loads(json.dumps(data)))
        except PageError as exc:
            print(f"approval page not rendered: {exc}", file=sys.stderr)
            return 2
        sys.stdout.write(text)
        return 0
    for line in data["paste"]:
        print(line)
    return 0


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="approval_page.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    render = sub.add_parser("render", help="print the page for a `record render --json` object")
    render.add_argument("source", help="a JSON file, or - for stdin")
    goal = sub.add_parser("goal-line", help="print the goal line without an approval code")
    goal.add_argument("scope")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "goal-line":
            print(goal_line(args.scope))
            return 0
        if args.source == "-":
            raw = sys.stdin.read()
        else:
            with open(args.source, encoding="utf-8") as handle:
                raw = handle.read()
        sys.stdout.write(render_page(json.loads(raw)))
        return 0
    except (OSError, ValueError) as exc:
        # PageError is a ValueError; so is a JSON decode error. Nothing was printed.
        print(f"approval page not rendered: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
