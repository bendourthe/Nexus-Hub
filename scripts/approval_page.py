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
ACTIONS = ("create", "answer", "pause", "resume", "retire", "add-class", "supplement-scope", "permit-manifest", "permit-outputs", "correct-ci-read", "amend-minor", "permit-member-execution-paths")
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
SECTIONS = ("Summary", "Decision", "Details (optional)")
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
# Words, paths, and script names that may never sit above Details (v4.13.6 WN-6).
# Allowed character sets stop sentence injection, not a mechanism term: a branch,
# surface, or vendor name such as `predicate` passes its own pattern, so render_page
# checks the rendered Summary and paste section and raises instead of printing it.
PLAIN_BANNED = ("HMAC", "nonce", "predicate", "schema", "worktree prune", "headRefOid", "refs/heads")
PLAIN_PATH_RE = re.compile(r"(?:~/|[A-Za-z]:\\|(?<![\w/])(?:[\w.-]+/)+[\w.-]+\.[A-Za-z]{1,5}\b)")
PLAIN_SCRIPT_RE = re.compile(r"\b[\w-]+\.(?:py|sh|ps1)\b")


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
    if action == "amend-minor":
        if not MINOR_RE.match(scope):
            raise PageError("membership is amended only for a minor run")
        return _fits(f"Approve the displayed added plans in /implement {scope} (approval {code})")
    if action == "correct-ci-read":
        if scope != "v4.15":
            raise PageError("the reviewed read correction belongs only to minor v4.15")
        return _fits(f"Correct the one-file CI read reservation in /implement {scope} (approval {code})")
    if action == "permit-member-execution-paths":
        if scope != "v4.15":
            raise PageError("typed execution permission belongs only to v4.15")
        return _fits(f"Permit the displayed member execution paths in /implement {scope} (approval {code})")
    if action == "permit-outputs":
        if scope != "v4.15":
            raise PageError("the reviewed output permission belongs only to minor v4.15")
        return _fits(f"Permit the displayed publication outputs in /implement {scope} (approval {code})")
    if action == "permit-manifest":
        if not MINOR_RE.match(scope):
            raise PageError("the manifest duty is permitted only for a minor run")
        return _fits(f"Permit the publication manifest in /implement {scope} (approval {code})")
    if action == "supplement-scope":
        if not MINOR_RE.match(scope):
            raise PageError("historical scope is supplemented only for a minor run")
        return _fits(f"Approve exact historical scope in /implement {scope} (approval {code})")
    if action == "add-class":
        if not MINOR_RE.match(scope):
            raise PageError("a class is added only to a minor run")
        # The one class a running minor may gain (completion_minor.ADDABLE_CLASSES).
        return _fits(f"Archive each released plan early in /implement {scope} (approval {code})")
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
            f"7) archive the {scope} folder (where approved, each plan's own documents right after its release) "
            "and delete any folder left empty."
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
    if name == "archive-member":
        _no_bound(entry)
        if not MINOR_RE.match(token):
            raise PageError("archive-member belongs to a minor run")
        return (f"Archive each {token} plan's own documents in a pull request as soon as that plan is released. "
                "Shared files such as the known-gaps list stay until the final archive.")
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
    if page.get('autonomy'):
        lines += ['Trusted full access continues covered actions without another permission request.',
                  'Changed destinations, failed verification and user edits remain unresolved until addressed.',
                  'The exact policy and planned paths are quoted in Details below.']
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
    if minor and "archive-minor" in names and "archive-member" in names:
        rows.append(("Archived", f"The {_scope_token(page)} documents, each plan's own as soon as it is released"))
    elif minor and "archive-minor" in names:
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
    if (page.get('autonomy') or {}).get('planned_actions'):
        never = '**Another decision is required for actions outside the displayed scope and paid use beyond the recorded caps. Unresolved failures and changed user files still require their own evidence or decision.**'
    elif caps:
        never = f"**Never without asking you: changes to CI, permissions, or secrets, or paid API use beyond {_joined(caps)}.**"
    else:
        never = "**Never without asking you: changes to CI, permissions, or secrets, and any paid API use.**"
    tail = ["| | Result |", "|---|---|", *(f"| {k} | {v} |" for k, v in rows), "", never, "",
            "**Stop any time: type /implement pause**"]
    # The plan's own outcomes are prose already held to OUTCOME_RE and OUTCOME_BANNED_RE;
    # the rows carry the validated identifiers (branches, releases, vendors) WN-6 names.
    _assert_plain(tail, "summary")
    return ["**What this run will do:**", "", *(f"- {o}" for o in outcomes), "", *tail]


def _assert_plain(lines: list[str], section: str) -> None:
    """PageError when a section above Details names a mechanism term, a path, or a script."""
    text = "\n".join(lines)
    lowered = text.lower()
    for term in PLAIN_BANNED:
        if term.lower() in lowered:
            raise PageError(f"the {section} would show the internal term {term!r}; move the value under Details")
    if PLAIN_PATH_RE.search(text) or PLAIN_SCRIPT_RE.search(text):
        raise PageError(f"the {section} would show a file path or script name")


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
    if page.get('autonomy'):
        rows.append('Approved-plan policy: ' + quoted(json.dumps(page['autonomy'], sort_keys=True)))
    return ["```text", *(rows or ["none"]), "```"]


def _section(title: str, body: list[str], level: int = 2) -> list[str]:
    return [f"{'#' * level} {title}", "", *body, ""] if body else []


def _amendment_page(data: dict, paste: PasteSet) -> str:
    """Display the shared canonical amendment page without deriving authority."""
    from repo_host import parse_remote

    page, scope = data["page"], data["scope"]
    fields = {"action", "scope", "record_nonce", "repo", "owner_session", "record_sha256",
              "original_members_sha256", "controller", "push_remote_url", "integration_head",
              "sequence", "previous_history_sha256", "members", "gap_migration", "spend_caps"}
    if (set(page) != fields or page.get("action") != "amend-minor"
            or not MINOR_RE.fullmatch(scope)
            or page.get("scope") != {"kind": "minor", "minor": scope}):
        raise PageError("amendment requires its exact canonical minor page")
    _repo(page)
    for key in ("record_nonce", "owner_session", "push_remote_url"):
        if not isinstance(page[key], str) or not page[key].strip() or any(ord(c) < 32 for c in page[key]):
            raise PageError("amendment identity is incomplete")
    route = parse_remote(page["push_remote_url"])
    if route is None or route[1].lower() != page["repo"].lower():
        raise PageError("amendment push route differs from its repository")
    for key in ("record_sha256", "original_members_sha256", "previous_history_sha256"):
        if not isinstance(page[key], str) or not re.fullmatch(r"[0-9a-f]{64}", page[key]):
            raise PageError("amendment identity requires exact hashes")
    if not isinstance(page["integration_head"], str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", page["integration_head"]):
        raise PageError("amendment requires an exact integration commit")
    if type(page["sequence"]) is not int or page["sequence"] < 1:
        raise PageError("amendment sequence must be positive")
    controller = page["controller"]
    if (not isinstance(controller, dict)
            or set(controller) != {"origin_root", "repo_root", "generation", "git_common_dir", "origin_record_key"}
            or type(controller.get("generation")) is not int or controller["generation"] < 0
            or any(not isinstance(controller.get(key), str) or not controller[key].strip()
                   for key in ("origin_root", "repo_root", "git_common_dir", "origin_record_key"))):
        raise PageError("amendment requires the complete controller identity")
    if not isinstance(page["spend_caps"], dict):
        raise PageError("amendment requires unchanged aggregate spending caps")
    caps = _caps({"spend_caps": page["spend_caps"]})
    members = page["members"]
    if not isinstance(members, list) or not members:
        raise PageError("amendment must list every added member")
    descriptions, versions, sources = [], set(), set()
    release_count = archive_count = cleanup_count = 0
    allowed = {"push-merge", "release", "repush", "release-notes", "refactor-moves",
               "archive-member", "cleanup-merged"}
    member_fields = {"version", "plan_path", "plan_sha256", "source_branch", "target_branch",
                     "release_version", "tag", "approvals"}
    for member in members:
        if not isinstance(member, dict) or set(member) != member_fields:
            raise PageError("an added member requires its complete descriptor")
        version = member["version"]
        if (not isinstance(version, str) or not re.fullmatch(re.escape(scope) + r"\.\d+", version)
                or version in versions or member["release_version"] != version):
            raise PageError("added members must have unique matching release versions in this minor")
        versions.add(version)
        source, target, tag = (_branch(member[key]) for key in ("source_branch", "target_branch", "tag"))
        if source == target or source in sources:
            raise PageError("added members require distinct source and target branches")
        sources.add(source)
        path = member["plan_path"]
        major = scope.split(".")[0]
        if (not isinstance(path, str) or not path.startswith(f"docs/releases/{major}/{scope}/plans/{version}-")
                or not path.endswith(".md") or "\\" in path or any(p in ("", ".", "..") for p in path.split("/"))
                or any(ord(c) < 32 for c in path)
                or not isinstance(member["plan_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", member["plan_sha256"])):
            raise PageError("an added member requires its exact release plan and hash")
        approvals = member["approvals"]
        if not isinstance(approvals, dict) or set(approvals) != {"classes", "cleanup"}:
            raise PageError("an added member requires explicit classes and cleanup")
        classes, cleanup = approvals["classes"], approvals["cleanup"]
        if not isinstance(classes, list) or not classes:
            raise PageError("an added member requires explicit approval classes")
        if not isinstance(cleanup, dict) or set(cleanup) != {"branches", "worktrees"}:
            raise PageError("member cleanup must list exact branches and working folders")
        for key, values in cleanup.items():
            if (not isinstance(values, list) or any(not isinstance(v, str) or not v.strip()
                    or any(ord(c) < 32 for c in v) for v in values) or len(set(values)) != len(values)):
                raise PageError("member cleanup contains ambiguous entries")
            if key == "branches":
                for value in values:
                    _branch(value)
                    if value != source:
                        raise PageError("member cleanup branch must be its own source branch")
            elif values:
                raise PageError("amendment grants no pre-existing working folder deletion")
        names, lines = set(), []
        context = {"scope": page["scope"], "repo": page["repo"],
                   "branches": {"source": source, "target": target}}
        for entry in classes:
            if (not isinstance(entry, dict) or not set(entry) <= {"class", "bound"}
                    or not isinstance(entry.get("class"), str)
                    or entry["class"] in names or entry["class"] not in allowed):
                raise PageError("member approval class is duplicated, unsupported or ambiguous")
            name = entry["class"]
            names.add(name)
            if name == "release" and entry.get("bound") != version:
                raise PageError("member release permission must bind its exact version")
            sentence = _approval_line(context, name, entry, name != "push-merge", [version], _next_minor(scope))
            if name == "archive-member":
                sentence = f"Archive only {version}'s own documents after its release; shared minor documents keep their existing archive rules."
            elif name == "cleanup-merged":
                sentence = "Delete only the quoted branches and working folders after checking they are merged, idle and unused."
            lines.append("- " + sentence)
        release_count += "release" in names
        archive_count += "archive-member" in names
        cleanup_count += bool(any(cleanup.values()))
        if "release" in names:
            lines.append(f"- The release is {version}; its exact tag is {tag}.")
        if "cleanup-merged" not in names and any(cleanup.values()):
            raise PageError("member cleanup needs an explicit cleanup-merged grant")
        lines.append("- Cleanup covers only the exact entries quoted below, after merged and idle checks." if any(cleanup.values())
                     else "- No additional branch or working folder deletion is granted.")
        descriptions.append((version, lines))
    if [member["version"] for member in members] != sorted(versions, key=_order):
        raise PageError("amendment members must follow release order")
    migration = page["gap_migration"]
    if (not isinstance(migration, dict) or set(migration) != {"items", "named_high_risk_ids"}
            or not isinstance(migration["items"], list)):
        raise PageError("amendment gap migration requires exact items and named high-risk ids")
    ids = []
    for item in migration["items"]:
        if (not isinstance(item, dict) or set(item) != {"id", "reason"}
                or item.get("reason") not in ("vendor-feature", "user-credential", "user-deferred")):
            raise PageError("amendment gap migration has an unsupported reason")
        ids.extend(_gap_ids([item["id"]], "amendment migration"))
    named = _gap_ids(migration["named_high_risk_ids"], "named high-risk")
    if (len(set(ids)) != len(ids) or len(set(named)) != len(named) or not set(named) <= set(ids)
            or any(_minor_token(gid.split("#")[0]) != scope for gid in ids)):
        raise PageError("amendment migration ids must be unique and belong to this minor")
    summary = [
        f"Add {len(members)} displayed plans to {scope}, with only their listed permissions.",
        f"Allow {release_count} additional releases and {archive_count} early plan archives, with {cleanup_count} exact deletion lists below.",
        "The original plans, existing claims, spending limits, retries, verification limits and release order stay unchanged.",
        "Earlier work gains no permission. New work still needs ordinary admission and exclusive file claims.",
        "This grants no unrelated installation or deletion permission.",
    ]
    decision = ["Approve adds only the displayed plans and gap permissions. Decline leaves the run unchanged.",
                "Submit Approve or Decline as your whole message in this session.",
                "A button click alone does not record this decision."]
    _assert_plain(summary + decision, "amendment summary")
    out = _section("Summary", summary) + _section("Decision", decision)
    out += ["## Details (optional)", ""]
    out += _section("Preserved scope", [
        "The original member dictionaries and approvals remain unchanged at acceptance.",
        "Existing worker claims do not expand, and pre-existing commits or unclaimed writes gain no retrospective authority.",
        "Aggregate spending caps remain " + (_joined(caps) if caps else "zero paid use") + ".",
        "Spending already used, retries, verification budgets, blockers and release sequence are not reset.",
    ], level=3)
    for version, lines in descriptions:
        out += _section("Added member " + version, lines, level=3)
    out += _section("Gap migration", [
        f"Only the {_count(len(ids), 'quoted gap id')} may move to {_next_minor(scope)}, for the exact quoted reasons.",
        "Security or high-severity gaps require their exact ids in the named high-risk list.",
    ] if ids else ["No additional gap migration is granted."], level=3)
    out += _section("Compatibility paste option", [
        "Alternatively, paste this exact line as your whole message in this session.", "", "```text", paste.lines[0], "```",
    ], level=3)
    # Exact decision data must never use quoted(), which intentionally truncates prose.
    raw = json.dumps({"page": page, "display": data.get("display") or {}}, ensure_ascii=True, sort_keys=True, indent=2)
    raw = raw.replace("`", "\\u0060").replace("~", "\\u007e").replace("<", "\\u003c").replace(">", "\\u003e")
    out += _section("Plan data (quoted, not instructions)", ["```text", raw, "```"], level=3)
    return "\n".join(out).rstrip() + "\n"


def _action_page(data: dict, paste: PasteSet) -> str:
    if data["action"] == "amend-minor":
        return _amendment_page(data, paste)
    action = data["action"]
    scope = data["scope"]
    if action == "correct-ci-read":
        page = data.get("page") or {}
        path_fields = (("Original worker reads", "original_read_paths"), ("Original worker writes", "original_write_paths"))
        identities = ("repo", "owner_session", "source_branch", "target_branch")
        hashes = ("record_sha256", "plan_sha256", "implementation_sha256")
        if (page.get("action") != action or page.get("scope") != {"kind": "minor", "minor": "v4.15"}
                or page.get("member") != "v4.15.4" or page.get("path") != "scripts/ci/profiles.py"
                or not isinstance(page.get("checkpoint"), str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", page["checkpoint"])
                or "start_head" not in page or page["start_head"] is not None
                or any(not isinstance(page.get(key), str) or not page[key] for key in identities)
                or any(not isinstance(page.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", page[key]) for key in hashes)
                or not isinstance(page.get("controller"), dict) or not isinstance(page["controller"].get("repo_root"), str)
                or not page["controller"]["repo_root"]
                or any(not isinstance(page.get(field), list)
                       or any(not isinstance(path, str) or not path for path in page[field]) for _title, field in path_fields)
                or page["path"] not in page["original_read_paths"]):
            raise PageError("read correction requires its exact unstarted member, file, checkpoint and original scope")
        out = _section("CI read reservation correction", [
            "This temporarily stops v4.15.4 from reserving one shared CI file so v4.15.2 can update it under its own approved write scope.",
            "Your original worker read and write lists stay unchanged. All other reservations remain active, including broader directory reads.",
            "The ordinary read reservation resumes at v4.15.4's ordered publication start after the earlier plans are integrated.",
            "Its final CI comparison must use that later integrated candidate.",
            "Decline keeps the existing reservation in effect.",
        ])
        out += _section("Bound identity", [
            "Repository: " + quoted(page["repo"]), "Member: " + quoted(page["member"]),
            "Exact file: " + quoted(page["path"]), "Reviewed source checkpoint: " + quoted(page["checkpoint"]),
            "Original frozen plan: " + quoted(page["plan_sha256"]),
            "Original implementation: " + quoted(page["implementation_sha256"]),
            "Source branch: " + quoted(page["source_branch"]), "Target branch: " + quoted(page["target_branch"]),
            "Owner session: " + quoted(page["owner_session"]),
            "Controller: " + json.dumps(page["controller"], ensure_ascii=True, sort_keys=True).replace("`", "\\u0060").replace("~", "\\u007e"),
            "Current record: " + quoted(page["record_sha256"]),
        ])
        for title, field in path_fields:
            rows = ["- " + json.dumps(path, ensure_ascii=True).replace("`", "\\u0060").replace("~", "\\u007e") for path in page[field]]
            out += _section(title, rows or ["None."])
        out += _section("Approval reply", ["Paste this line as your whole message, with nothing added.", "", "```text", paste.lines[0], "```"])
        return "\n".join(out).rstrip() + "\n"
    if action == "permit-member-execution-paths":
        import completion_minor as execution_owner
        try:
            page = execution_owner.validate_execution_page(data.get("page"))
        except (execution_owner.MinorMalformed, KeyError, TypeError, ValueError) as exc:
            raise PageError("typed execution permission requires every exact bound field") from exc
        hook = page["capability_kind"] == "hook-registration"
        out = _section("Member execution permission", [
            "This decision covers " + quoted(page["member"]) + " in the displayed repository.",
            (("The displayed post-tool events call stuck-turn-notice to provide a nonblocking advisory notice "
              "when a turn repeats failing commands or repeatedly changes one file."
              if page["member"] == "v4.15.5" else
              "The displayed pre-tool event calls worktree-policy. This guard checks proposed worktree commands "
              "against the configured location policy and can block commands that violate it.")
             if hook else "The displayed workflows automate repository execution and use existing access tokens."),
            *( ["The pre-commit configuration runs programs locally when you commit code."] if ".pre-commit-config.yaml" in page["write_paths"] else []),
            ("Role: implementation means this member's own worker changes."
             if page["role"] == "implementation" else "Role: coordinator means ordered publication changes, not worker CI authority."),
            "Approval captures prospective exact permission only. It stays dormant until ordinary admission activates it; it edits no file and starts no publication.",
            # State only what the gates enforce: a hook registration must equal the displayed recipe,
            # but granted CI files are limited by path alone; their content is never machine-checked.
            ("This registration grants no secret access or token permission. Any settings change other than the displayed "
             "registration recipe is refused, and so is any change outside the exact files below."
             if hook else
             "Only the exact files below may change, but Nexus-Hub does not check what goes into them. "
             "Review every change to these files before merge: new token permissions, secret references, new triggers "
             "and deployment steps are not blocked automatically."),
            "Doing nothing leaves this member's required registration or CI work blocked.",
            "Recommendation: approve only this reviewed necessary scope so the required work can proceed under unchanged preservation and verification gates.",
        ])
        rows = []
        for field in sorted(page):
            if field not in {"write_paths", "hook_recipe"}:
                rows.append(field + ": " + json.dumps(page[field], ensure_ascii=True, sort_keys=True).replace("`", "\\u0060").replace("~", "\\u007e"))
        out += _section("Bound identity", rows)
        out += _section("Exact execution files", ["- " + json.dumps(path, ensure_ascii=True) for path in page["write_paths"]])
        if hook:
            out += _section("Exact registration recipe", ["```json", json.dumps(page["hook_recipe"], ensure_ascii=True, indent=2), "```"])
        out += _section("Approval reply", ["Paste this line as your whole message, with nothing added.", "", "```text", paste.lines[0], "```"])
        return "\n".join(out).rstrip() + "\n"
    if action == "permit-outputs":
        page = data.get("page") or {}
        path_fields = (("Original worker reads", "original_read_paths"),
                       ("Original worker writes", "original_write_paths"),
                       ("Existing coordinator files", "coordinator_paths"),
                       ("Additional exact files", "write_paths"))
        start = page.get("start_head")
        identities = ("repo", "owner_session", "source_branch", "target_branch")
        hashes = ("record_sha256", "plan_sha256", "implementation_sha256")
        if (page.get("action") != action or page.get("scope") != {"kind": "minor", "minor": "v4.15"}
                or not isinstance(page.get("member"), str) or page["member"] not in {f"v4.15.{patch}" for patch in range(5)}
                or any(not isinstance(page.get(key), str) or not page[key] for key in identities)
                or any(not isinstance(page.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", page[key]) for key in hashes)
                or not isinstance(page.get("controller"), dict) or not isinstance(page["controller"].get("repo_root"), str)
                or not page["controller"]["repo_root"] or "start_head" not in page
                or start is not None and (not isinstance(start, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", start))
                or any(not isinstance(page.get(field), list)
                       or any(not isinstance(path, str) or not path for path in page[field]) for _title, field in path_fields)
                or not page["write_paths"]):
            raise PageError("output permission requires the exact member, original scope, start and additional files")
        effect = ("Approving will append the additional exact files to this member's existing coordinator publication scope now."
                  if start else "Approving registers a dormant permission. It grants no file write before ordinary ordered publication admission.")
        out = _section("Publication output permission", [
            "This decision covers only the displayed additional files for " + quoted(page["member"]) + ".",
            effect,
            "Original worker claims, publication order, approval classes and spending limits stay unchanged.",
            "Original-scope checks and active file conflicts must pass before any permission activates.",
            "Decline leaves these additional files unapproved.",
        ])
        out += _section("Bound identity", [
            "Repository: " + quoted(page.get("repo")),
            "Source branch: " + quoted(page.get("source_branch")),
            "Target branch: " + quoted(page.get("target_branch")),
            "Original frozen plan: " + quoted(page.get("plan_sha256")),
            "Original implementation: " + quoted(page.get("implementation_sha256")),
            "Existing publication start: " + quoted(start),
            "Owner session: " + quoted(page.get("owner_session")),
            "Controller: " + json.dumps(page["controller"], ensure_ascii=True, sort_keys=True).replace("`", "\\u0060").replace("~", "\\u007e"),
            "Current record: " + quoted(page.get("record_sha256")),
        ])
        for title, field in path_fields:
            # File lists are exact decision data, so the general prose cap must not truncate them.
            rows = ["- " + json.dumps(path, ensure_ascii=True).replace("`", "\\u0060").replace("~", "\\u007e") for path in page[field]]
            out += _section(title, rows or ["None."])
        out += _section("Approval reply", ["Paste this line as your whole message, with nothing added.", "", "```text", paste.lines[0], "```"])
        return "\n".join(out).rstrip() + "\n"
    if action == "permit-manifest":
        page = data.get("page") or {}
        if page.get("path") != "MANIFEST.sha256" or not page.get("member"):
            raise PageError("the manifest permission requires its exact member and file")
        out = _section("Publication manifest permission", [
            "This registers one dormant publication duty for " + quoted(page.get("member")) + ".",
            "Repository: " + quoted(page.get("repo")),
            "File: " + quoted(page.get("path")),
            "Frozen plan: " + quoted(page.get("plan_sha256")),
            "Original implementation: " + quoted(page.get("implementation_sha256")),
            "The member's original worker claims stay unchanged. This grants no immediate file write or release.",
            "The normal publication admission still requires the preceding release, its back-merge, a clean original scope and no active claim conflict.",
            "Decline leaves this publication file unapproved.",
        ])
        out += _section("Approval reply", ["Paste this line as your whole message, with nothing added.", "", "```text", paste.lines[0], "```"])
        return "\n".join(out).rstrip() + "\n"
    if action == "supplement-scope":
        page = data.get("page") or {}
        bounds = page.get("merge_bounds") or {}
        rows = bounds.get("rows")
        if not isinstance(rows, list) or not rows or any(not isinstance(row, list) or len(row) != 6
                or any(not isinstance(value, str) for value in row) for row in rows):
            raise PageError("historical scope requires exact file and blob bounds")
        out = _section("Historical scope", [
            "This acknowledges only the displayed files in the already merged contribution for " + quoted(page.get("member")) + ".",
            "Repository: " + quoted(page.get("repo")),
            "Merge: " + quoted(bounds.get("merge")),
            "Integration parent: " + quoted(bounds.get("first_parent")),
            "Tree: " + quoted(bounds.get("tree")),
            "Original claims and baselines stay unchanged. Future writes, release, archive, spending and retry budgets require their existing approvals.",
            "Decline leaves this historical contribution outside the original file claims and keeps the member unreleased.",
        ])
        out += _section("Exact files", ["- " + quoted(row[0]) + ": " + row[5] + "; " + row[1] + " " + row[3] + " -> " + row[2] + " " + row[4] for row in rows])
        out += _section("To approve, paste this line", ["Paste this line as your whole message, with nothing added.", "", chr(96) * 3 + "text", paste.lines[0], chr(96) * 3])
        return "\n".join(out).rstrip() + "\n"
    if action == "add-class":
        if (data.get("page") or {}).get("class") != "archive-member":
            raise PageError("only the archive-member class can be added to a running minor")
        out = _section("What this will do", [
            f"This adds the archive-member approval to /implement {scope}.",
            "Today each plan's documents stay where they are until the whole minor closes, then move to the archive together.",
            "With this approval, each plan's own documents move to the archive as soon as that plan is released.",
            "Shared files, such as the known-gaps list and the minor's evidence, still move only when the minor closes.",
            "Each early archive is one pull request, merged once its checks pass.",
            "Nothing else changes.",
        ])
        out += _section("To approve, paste this line",
                        ["Paste this line as your whole message, with nothing added.", "", "```text", paste.lines[0], "```"])
        return "\n".join(out).rstrip() + "\n"
    verb = {"answer": "continue past the blocker", "pause": "pause", "resume": "resume", "retire": "retire the run record"}[action]
    out = _section("What this will do", [f"This will {verb} for /implement {scope}.", "Nothing else changes."])
    detail = data.get('page', {}).get('blocker') or {}
    if detail:
        out += _section('Decision details', [
            'Requested action: ' + quoted(detail.get('purpose') or detail.get('category') or 'Continue the displayed work'),
            'Reason: ' + quoted(detail.get('why') or 'This action needs a decision before work continues.'),
            'Scope: ' + quoted(json.dumps(detail.get('request') or {}, sort_keys=True)),
            'Decline leaves this action unapproved; no authority or completion predicate changes.',
        ])
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
    pasted = _paste_section(paste)
    # Only the verified template field contains an opaque approval code.
    plain_paste = [line.replace(f"(approval {code})", "(approval AAAAAAAA)") for line in pasted]
    _assert_plain(plain_paste, "paste section")
    out += _section(SECTIONS[1], pasted)
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
        "challenge": pending['nonce'],
        "allow_short_reply": pending.get('allow_short_reply', False),
        "paste": list(pending["paste_lines"]),
        "page": pending["page"],
        "display": display or {},
    }



def question_data(data: dict) -> dict:
    """Question-tool input is descriptive, never an invented host approval callback."""
    action = data['action']
    scope = data['scope']
    effect = {
        'create': 'Start the displayed plan and carry out its listed approvals',
        'pause': 'Pause this run until you choose to resume it',
        'resume': 'Resume this run in the current session',
        'retire': 'Retire this run record and its authority',
        'supplement-scope': 'Acknowledge only the displayed exact files in the reviewed historical merge',
        'permit-manifest': 'Register only the displayed dormant member publication manifest duty',
        'permit-outputs': 'Permit only the displayed exact additional publication output files',
        'permit-member-execution-paths': 'Permit only the displayed exact member execution capability',
        'correct-ci-read': 'Temporarily release only the displayed one-file read reservation',
        'amend-minor': 'Add only the displayed plans and exact permissions while preserving the existing run limits',
        'add-class': ("Archive each plan's own documents as soon as that plan is released, "
                      "instead of all at once when the minor closes"),
    }.get(action)
    blocker = data.get('page', {}).get('blocker') or {}
    if action == 'answer':
        effect = {
            'approval-not-covered': 'Allow the displayed action that needs your decision',
            'ci-security-change': 'Allow the displayed pipeline or security change',
            'user-edit-guard': 'Allow work to continue after reviewing the changed file',
            'destructive-outside-approval': 'Allow the displayed destructive action',
            'unreproducible-red-check': 'Decide whether work may continue after the reported failed check',
            'platform-unavailable': 'Continue after the reported platform availability issue',
            'no-progress': 'Continue the reported stalled work',
            'record-tampered': 'Review the run integrity problem before continuing',
        }.get(blocker.get('category'), 'Review the displayed issue before continuing')
    question = f'{effect} for {scope}?'
    return {'header': 'Approval', 'question': question, 'challenge': data['challenge'],
            'options': [{'label': 'Approve', 'description': 'Continue only with the displayed scope.'},
                        {'label': 'Decline', 'description': 'Leave the pending action unapproved.'}],
            'review_page': render_page(data).replace('To approve, paste this line', 'Compatibility paste option').replace('Paste this line as your whole message, with nothing added.', 'For the primary decision, reply Approve, Yes or Continue. Decline leaves the action unapproved.'),
            'action_scope': data.get('page', {}) if action in ('supplement-scope', 'permit-manifest', 'permit-outputs', 'correct-ci-read', 'amend-minor', 'permit-member-execution-paths') else blocker.get('request') or {},
            'purpose': blocker.get('purpose'), 'why': blocker.get('why'),
            'capture': {'direct_question_callback_supported': False,
                        'fallback': 'Reply Approve, Yes or Continue as your whole message in this session.',
                        'requires_genuine_prompt_submit': True},
            'compatibility_paste': data['paste']}


def emit(data: dict, mode: str) -> int:
    """Print `record render` output: `json`, `page`, or the bare paste line(s).

    Returns 0, or 2 after reporting a PageError with nothing on stdout.
    """
    if mode == 'question':
        print(json.dumps(question_data(data), sort_keys=True))
        return 0
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
