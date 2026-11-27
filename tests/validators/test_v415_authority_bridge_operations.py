"""Private finite-operation controls; never live permission or hosting proof."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.fixtures.gh_stub.launcher import make_stub
from .test_v415_authority_bridge import (
    ROOT, CODEX_SESSION, binding, bridge_case, capture_supplement, cm, ck,
    resume, run_plan, _isolated_git_config, _no_transport_overrides, _private_native_home,
)
from . import git_stub_fastpath
from .member_declarations import DECLARED_CHECKER
from .test_codex_transcript_approval import Transcript
from .test_completion_minor_record import GH_STUB

FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
AUTOUSE_FIXTURES = (_isolated_git_config, _no_transport_overrides, _private_native_home)
NEW_OWNER = "11111111-2222-4333-8444-555555555555"

# Unsupported reads go to the existing inert gh executable, never real gh.
# Mutations own a separate state/journal and actual disposable bare Git refs.
_HOST = r"""
import json, os, subprocess, sys, time
from pathlib import Path
path = Path(os.environ["BRIDGE_TEST_HOST_FILE"])
state = json.loads(path.read_text(encoding="utf-8"))
args = sys.argv[1:]
modes = set(state.get("modes", []))
prefix = "repos/bendourthe/Nexus-Hub"
flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
def save():
    temporary = path.with_name(path.name + "." + str(os.getpid()) + ".tmp")
    temporary.write_text(json.dumps(state), encoding="utf-8")
    os.replace(temporary, path)
def journal(kind):
    with Path(os.environ["BRIDGE_TEST_JOURNAL"]).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"kind": kind, "argv": args}) + "\n")
def emit(value):
    print(json.dumps(value))
    raise SystemExit(0)
def option(name, default=None):
    for index, value in enumerate(args):
        if value == name and index + 1 < len(args): return args[index + 1]
        if value.startswith(name + "="): return value.split("=", 1)[1]
    return default
def git(*argv, input=None):
    result = subprocess.run([os.environ["BRIDGE_TEST_REAL_GIT"], "-C", state["remote"],
        "-c", "user.name=Private Host", "-c", "user.email=host@example.invalid", *argv],
        input=input, capture_output=True, text=True, creationflags=flags)
    if result.returncode:
        print(result.stderr, file=sys.stderr); raise SystemExit(71)
    return result.stdout.strip()
def commit(message):
    return git("commit-tree", state["tree"], "-p", state["base"], "-p", state["head"], input=message + "\n")
def object_info(sha):
    tree = git("rev-parse", sha + "^{tree}")
    parents = git("rev-list", "--parents", "-n", "1", sha).split()[1:]
    return {"sha": sha, "tree": {"sha": tree}, "parents": [{"sha": parent} for parent in parents]}
def rest_pr():
    item = dict(state["pull"])
    item["head"] = {"sha": state["head"], "ref": state["branch"], "repo": {"full_name": "bendourthe/Nexus-Hub"}}
    item["base"] = {"sha": state["base"], "ref": "develop", "repo": {"full_name": "bendourthe/Nexus-Hub"}}
    item["merge_commit_sha"] = state.get("merged_sha") or state["preview"]
    if "wrong-pr-head" in modes: item["head"]["sha"] = "f" * 40
    if "wrong-pr-base" in modes: item["base"]["ref"] = "main"
    return item
if args[:2] == ["repo", "view"] and option("--json") == "description":
    if "reads-unavailable" in modes and state.get("description_effects"): raise SystemExit(75)
    emit({"description": state["description"]})
if args[:2] == ["release", "view"] and args[2] == "v4.15.6" and option("--json") == "tagName,isDraft,body":
    if state["release"] is None:
        print("release not found", file=sys.stderr); raise SystemExit(1)
    emit(state["release"])
if args[:2] == ["release", "edit"]:
    assert args[2] == "v4.15.6" and option("--repo") == "bendourthe/Nexus-Hub"
    journal("release-edit")
    state["release"]["body"] = option("--notes"); save(); emit(state["release"])
if args[:2] == ["pr", "list"] and option("--head") == state.get("branch"):
    if state["pull"] is None: emit([])
    pr = rest_pr()
    emit([{"number": pr["number"], "url": pr["url"], "state": "MERGED" if pr["merged"] else "OPEN",
           "headRefName": pr["head"]["ref"], "headRefOid": pr["head"]["sha"], "baseRefName": pr["base"]["ref"]}])
if args[:2] == ["pr", "create"]:
    assert option("--head") == state["branch"] and option("--base") == "develop"
    assert option("--title") == state["title"] and option("--body") == state["body"]
    journal("pr-create")
    state["preview"] = commit("Private tested preview")
    state["pull"] = {"number": 314, "url": "https://github.com/bendourthe/Nexus-Hub/pull/314",
                     "state": "open", "merged": False, "draft": False, "mergeable": True}
    save(); print(state["pull"]["url"]); raise SystemExit(0)
if args[:1] == ["api"]:
    endpoint = next((arg for arg in args if arg.startswith("repos/")), "")
    method = option("--method", "GET")
    suffix = endpoint[len(prefix):] if endpoint.startswith(prefix) else None
    if suffix == "" and method == "PATCH":
        fields = [args[index + 1] for index, arg in enumerate(args[:-1]) if arg == "--raw-field"]
        assert len(fields) == 1 and fields[0].startswith("description=")
        journal("description-patch")
        if "effect-fails" in modes: raise SystemExit(75)
        if state.get("description_effect_gate"):
            deadline = time.monotonic() + 90
            while not Path(state["description_effect_gate"]).exists():
                if time.monotonic() >= deadline: raise SystemExit(75)
                time.sleep(0.02)
        time.sleep(state.get("effect_delay", 0))
        state["description"] = fields[0].split("=", 1)[1]
        state["description_effects"] = state.get("description_effects", 0) + 1
        save(); emit({"description": state["description"]})
    if suffix == "/pulls/314/merge-async" and method == "PUT":
        assert option("--raw-field") == "sha=" + state["head"]
        assert "merge_method=merge" in args and "merge_action=direct_merge" in args and "bypass_rules=false" in args
        journal("merge-put")
        state["merge_requested"] = True
        if "merge-pending" not in modes:
            merged = commit("Private final merge")
            git("update-ref", "refs/heads/develop", merged, state["base"])
            state["merged_sha"] = merged
            state["pull"].update(state="closed", merged=True)
        save()
        if state.get("response_gate"):
            deadline = time.monotonic() + 90
            while not Path(state["response_gate"]).exists():
                if time.monotonic() >= deadline: raise SystemExit(75)
                time.sleep(0.02)
        if "failed-response-no-uuid" in modes:
            emit({"status": "failed", "details": {}, "message": "Private host rejected this exact merge request"})
        emit({"status": "pending", "details": {
            "uuid": "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42", "merge_method": "merge",
            "merge_action": "direct_merge", "expected_head_sha": state["head"], "bypass_rules": False}})
    if suffix == "/pulls/314/merge-async/630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42":
        assert method == "GET"
        journal("merge-get")
        if "async-get-unavailable" in modes: raise SystemExit(75)
        status = ("merged" if state["pull"]["merged"] else "failed" if "async-get-failed" in modes
                  else "enqueued" if "async-get-enqueued" in modes else "pending")
        emit({"status": status,
              "details": {"uuid": "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42",
                          "merge_method": "merge", "merge_action": "direct_merge",
                          "expected_head_sha": state["head"], "bypass_rules": False}})
    if suffix == "/pulls/314": emit(rest_pr())
    if suffix and suffix.startswith("/git/commits/"):
        sha = suffix.rsplit("/", 1)[1]; value = object_info(sha)
        if sha == state.get("preview") and "wrong-preview-tree" in modes: value["tree"]["sha"] = "f" * 40
        if sha == state.get("preview") and "wrong-preview-parents" in modes: value["parents"].reverse()
        if sha == state.get("merged_sha") and "wrong-final-tree" in modes: value["tree"]["sha"] = "f" * 40
        emit(value)
    if suffix == "/branches/develop/protection":
        if "rules-unavailable" in modes: raise SystemExit(75)
        emit({"required_status_checks": {"strict": "strict-false" not in modes, "contexts": [],
               "checks": [{"context": name, "app_id": 123} for name in state["required"]]},
              "enforce_admins": {"enabled": True},
              "required_pull_request_reviews": {"bypass_pull_request_allowances":
                 {"users": [{"login": "private-bypass"}] if "bypass" in modes else [], "teams": [], "apps": []}}})
    if suffix == "/rules/branches/develop":
        if modes & {"unbound-ruleset", "conflicting-app"}:
            emit([{"ruleset_id": 7, "type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [{"context": name, "integration_id":
                    456 if "conflicting-app" in modes else None} for name in state["required"]]}}])
        emit([{"ruleset_id": 7, "type": "pull_request"}] if "ruleset-bypass" in modes else [])
    if suffix == "/rulesets/7?includes_parents=true":
        emit({"id": 7, "target": "branch", "enforcement": "active",
              "bypass_actors": [{"actor_id": 1}] if "ruleset-bypass" in modes else [],
              "rules": [{"type": "pull_request"}]})
    if suffix and suffix.endswith("/check-runs?per_page=100"):
        emit({"total_count": len(state["required"]), "check_runs": [
            {"name": name, "head_sha": "f" * 40 if "wrong-check-sha" in modes else state["preview"],
             "status": "in_progress" if "stale-check" in modes else "completed",
             "conclusion": None if "stale-check" in modes else "success",
             "app": {"id": 456 if "wrong-app" in modes else 123}}
            for name in state["required"]]})
    if suffix and suffix.endswith("/status"): emit({"sha": state["preview"], "statuses": []})
    if suffix and suffix.startswith("/compare/"):
        merged = state.get("merged_sha")
        emit({"base_commit": {"sha": merged}, "merge_base_commit": {"sha": merged}, "status": "identical"})
result = subprocess.run([os.environ["BRIDGE_TEST_ORIGINAL_GH"], *args], capture_output=True, creationflags=flags)
sys.stdout.buffer.write(result.stdout)
sys.stderr.buffer.write(result.stderr)
raise SystemExit(result.returncode)
"""


class PrivateHost:
    """Own only the disposable fixture host state and transport executables."""

    def __init__(self, fx, monkeypatch):
        self.fx = fx
        self.path = fx.tmp / "authority-host.json"
        self.journal = fx.tmp / "authority-host-calls.jsonl"
        original_gh, real_git = shutil.which("gh"), shutil.which("git")
        assert original_gh and real_git
        assert Path(original_gh).resolve().parent == GH_STUB.resolve(), "Only the existing inert gh may be forwarded"
        self.state = {"description": "Before", "description_effects": 0, "release": None, "pull": None,
                      "remote": str(fx.remote), "modes": [], "required": ["ci-required"]}
        self.save()
        directory = fx.tmp / "authority-tools"
        directory.mkdir()
        gh_program, git_program = directory / "host.py", directory / "git-tool.py"
        gh_program.write_text(_HOST, encoding="utf-8")
        git_program.write_text(_GIT, encoding="utf-8")
        make_stub(directory, "gh", gh_program)
        git_stub = make_stub(directory, "git", git_program)
        entries = {"BRIDGE_TEST_HOST_FILE": str(self.path), "BRIDGE_TEST_JOURNAL": str(self.journal),
                   "BRIDGE_TEST_ORIGINAL_GH": original_gh, "BRIDGE_TEST_REAL_GIT": real_git, "BRIDGE_TEST_GIT_STUB": str(git_stub),
                   "BRIDGE_TEST_LOCAL_REMOTE": str(fx.remote),
                   "BRIDGE_TEST_SIGNED_REMOTE": fx.record()["approvals"]["push_remote_url"],
                   "PATH": str(directory) + os.pathsep + fx.env["PATH"]}
        for key, value in entries.items():
            monkeypatch.setenv(key, value)
        fx.env.update(entries)
        git_stub_fastpath.install(monkeypatch.setattr)
        self.real_git = real_git

    def save(self):
        self.path.write_text(json.dumps(self.state), encoding="utf-8")

    def load(self):
        self.state = json.loads(self.path.read_text(encoding="utf-8"))
        return self.state

    def mode(self, *modes):
        self.load()
        self.state["modes"] = list(modes)
        self.save()

    def calls(self, kind):
        if not self.journal.exists():
            return []
        return [row for row in map(json.loads, self.journal.read_text().splitlines()) if row["kind"] == kind]

    def git(self, cwd, *args, input=None):
        result = subprocess.run([self.real_git, "-C", str(cwd), *args], input=input,
                                capture_output=True, text=True, env=self.fx.env, creationflags=FLAGS)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout.strip()

    def actor(self):
        actor = self.fx.tmp / "publication-actor"
        self.git(self.fx.work, "worktree", "add", "-q", "-b", cm.AUTHORITY_BRIDGE_BRANCH,
                 str(actor), "origin/develop")
        relative = "src/private-maintenance.txt"
        target = actor / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Private bounded contribution.\n", encoding="utf-8")
        self.git(actor, "add", "--", relative)
        self.git(actor, "commit", "-q", "-m", "private bounded maintenance")
        head = self.git(actor, "rev-parse", "HEAD")
        self.load()
        self.state.update(branch=cm.AUTHORITY_BRIDGE_BRANCH, head=head,
                          tree=self.git(actor, "rev-parse", "HEAD^{tree}"),
                          base=self.git(actor, "rev-parse", "origin/develop"),
                          title="Private maintenance", body="Private exact body.")
        self.save()
        return actor, {"head": head, "write_paths": [relative], "pr_title": self.state["title"],
                       "pr_body": self.state["body"]}

    def install_attribution(self, actor):
        prefix = [sys.executable, "-B", str(ROOT / "scripts/nexus_hub_cli.py"), "attribution"]
        result = subprocess.run(prefix + ["install", "--workspace"], cwd=actor, env=self.fx.env,
                                capture_output=True, text=True, timeout=45, creationflags=FLAGS)
        assert result.returncode == 0, result.stdout + result.stderr
        check = subprocess.run(prefix + ["check"], cwd=actor, env=self.fx.env,
                               capture_output=True, text=True, timeout=45, creationflags=FLAGS)
        assert check.returncode == 0, check.stdout + check.stderr
        return Path(self.git(actor, "config", "--path", "--get", "core.hooksPath"))

    def complete_pending_merge(self):
        self.load()
        result = subprocess.run([self.real_git, "-C", str(self.fx.remote), "-c", "user.name=Private Host",
            "-c", "user.email=host@example.invalid", "commit-tree", self.state["tree"],
            "-p", self.state["base"], "-p", self.state["head"]], input="Private final merge\n",
            capture_output=True, text=True, env=self.fx.env, creationflags=FLAGS)
        assert result.returncode == 0, result.stderr
        merged = result.stdout.strip()
        self.git(self.fx.remote, "update-ref", "refs/heads/develop", merged, self.state["base"])
        self.state.update(merged_sha=merged)
        self.state["pull"].update(state="closed", merged=True)
        self.save()
        return merged


def receipt_id(entry):
    return hashlib.sha256(binding.canonical(entry)).hexdigest()


def assert_original_approvals_and_exact_capture_append(original, record, appended, resumes, runs):
    current = record["approvals"]
    assert {key: value for key, value in current.items() if key != "transcript_decisions"} == {
        key: value for key, value in original["approvals"].items() if key != "transcript_decisions"}
    prefix = original["approvals"].get("transcript_decisions", [])
    history = current.get("transcript_decisions", [])
    assert history[:len(prefix)] == prefix
    assert [(row["action"], row["session_id"]) for row in history[len(prefix):]] == appended
    assert binding.transcript_decisions_valid(record)
    prior = original.get("continuations", [])
    continuations = record["continuations"]
    assert continuations[:len(prior)] == prior
    captured = continuations[len(prior):]
    assert [(row["from_session"], row["to_session"]) for row in captured] == [pair[:2] for pair in resumes]
    for row, (_, session, transcript) in zip(captured, resumes):
        assert row["record_nonce"] == original["nonce"]
        assert row["capture"]["origin"] == "codex-host-transcript"
        assert row["capture"]["session_id"] == session
        assert Path(row["capture"]["transcript_path"]).resolve() == transcript.resolve()
        assert row["capture"]["transcript_proof"]["action"] == "resume"
        assert binding.consumed_capture_valid(runs, row["capture"], row["rendered_at"])
    assert binding.continuation_history_valid(record)


def execute(fx, entry, operation, *, session=CODEX_SESSION):
    return fx.run("record", "execute-v415-authority", "--minor", "v4.15", "--repo", str(fx.work),
                  "--session", session, "--receipt", receipt_id(entry), "--operation", operation)


def command(fx, entry, operation):
    return [sys.executable, "-B", str(DECLARED_CHECKER), "record",
            "execute-v415-authority", "--minor", "v4.15", "--repo", str(fx.work),
            "--session", CODEX_SESSION, "--receipt", receipt_id(entry), "--operation", operation]


def operation_rows(fx, entry, operation):
    identity = cm._bridge_operation_id(entry, operation)
    return [row for row in fx.record()["v415_publication_operations"] if row["operation_id"] == identity]


def execute_admitted_dependency(fx, host):
    """Execute the real declared fixture task; derive work from native predicates."""
    worker = fx.worker("v4.15.0")
    member = fx.member("v4.15.0")
    plan = worker / member["plan_path"]
    declaration = json.loads(plan.read_text(encoding="utf-8").split("```json\n", 1)[1].split("\n```", 1)[0])
    claims = fx.tmp / "native-dependent-claims.json"
    claims.write_text(json.dumps(declaration), encoding="utf-8")
    admitted = fx.run("record", "member-implement-start", "--minor", "v4.15", "--session", CODEX_SESSION,
        "--member", "v4.15.0", "--worktree", str(worker), "--head", host.git(worker, "rev-parse", "HEAD"),
        "--claims", str(claims))
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    source = worker / next(path for path in declaration["write_paths"] if path.startswith("src/"))
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("Private dependent task executed after verified merge.\n", encoding="utf-8")
    measured = fx.run("check-member", "--minor", "v4.15", "--session", CODEX_SESSION,
                      "--member", "v4.15.0", "--json")
    assert measured.returncode == 1, measured.stdout + measured.stderr
    predicates = json.loads(measured.stdout.splitlines()[-1])["predicates"]
    assert predicates["implementation.identity"] == "met" and predicates["task.T001"] == "unmet"
    return [{"id": "native-dependent-task", "title": "Finish the admitted v4.15.0 task.T001",
        "authorized": predicates["implementation.identity"] == "met", "feasible": source.is_file(),
        "evidence": "Native implementation.identity=met, task.T001=unmet; admitted source executed."}]


def native_job_frame(fx, checked, previous=None, work=None):
    """Exercise the native owner producer and controller, preserving real handles."""
    (fx.tmp / "last-native-checker.json").write_text(json.dumps({"returncode": checked.returncode,
        "stdout": checked.stdout, "stderr": checked.stderr}, indent=2), encoding="utf-8")
    scope = argparse.Namespace(minor=True, label="v4.15", repo_root=fx.work,
                               observer_session=CODEX_SESSION)
    _, current = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION,
                                             minor_protocol=1, execution_protocol=1)
    facts = run_plan.native_owner_observation(scope, fx.record_path(), current, previous,
                                              remaining_tasks=3)
    if work is not None:
        facts["work"] = work
    frame = run_plan.reconcile_observation(scope, fx.record_path(), current, facts,
        checked.returncode, checked.stdout, previous, readonly=True)
    run_plan.save_continuation(fx.record_path(), frame)
    return frame


def native_snapshot_reports(fx):
    """Run the matching source snapshot CLI and both actual renderer modes."""
    driver = fx.tmp / "operations-snapshot.py"
    driver.write_text("import runpy,sys\n" + f"sys.path.insert(0,{str(ROOT)!r})\n"
        "from tests.validators.member_declarations import install\n"
        "class Patch:\n    def setattr(self,obj,key,value): setattr(obj,key,value)\n"
        "install(Patch())\n" +
        f"sys.argv[0]={str(ROOT / 'catalog/skills/workflow/implement-phase/scripts/status_snapshot.py')!r}\n"
        "runpy.run_path(sys.argv[0],run_name='__main__')\n", encoding="utf-8")
    result = subprocess.run([sys.executable, "-B", str(driver), "--repo", str(fx.work),
        "--scope", "v4.15", "--record", str(fx.record_path()), "--runs-dir", str(fx.runs),
        "--observer-session", CODEX_SESSION], cwd=fx.work, env=fx.env,
        capture_output=True, text=True, timeout=90, creationflags=FLAGS)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    report = run_plan.reporting_module("status_report")
    reports = {mode: report.render(data, mode) for mode in ("compact", "full")}
    (fx.tmp / "last-native-snapshot.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    (fx.tmp / "last-native-reports.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    return data, reports


def cut_driver(fx, phase):
    """Cut the actual dispatch seam in a child; no native reader/writer stubs."""
    path = fx.tmp / ("cut-" + phase + ".py")
    source = (
        "import os,sys\n"
        f"sys.path[:0] = [{str(ROOT)!r}, {str(ROOT / 'scripts')!r}]\n"
        "from tests.validators.member_declarations import install\n"
        "class Patch:\n    def setattr(self,obj,key,value): setattr(obj,key,value)\n"
        "install(Patch())\n"
        "import check_plan_completion as ck\nimport run_plan\n"
        "original=run_plan.dispatch_authority_operation\n"
        "def cut(*args,**kwargs):\n"
        + ("    os._exit(81)\n" if phase == "before" else
           "    original(*args,**kwargs)\n    os._exit(82)\n")
        + "run_plan.dispatch_authority_operation=cut\n"
        "raise SystemExit(ck.main())\n"
    )
    path.write_text(source, encoding="utf-8")
    return path


def run_cut(fx, entry, operation, phase):
    argv = command(fx, entry, operation)
    argv[2] = str(cut_driver(fx, phase))
    return subprocess.run(argv, cwd=fx.work, env=fx.env, capture_output=True,
                          text=True, timeout=90, creationflags=FLAGS)


def run_short_observer(fx, entry, operation="green-merge"):
    """Lower only the real dispatch observation budget; never fake its result."""
    driver = fx.tmp / "short-native-observer.py"
    driver.write_text("import sys\n" + f"sys.path[:0]=[{str(ROOT)!r},{str(ROOT / 'scripts')!r}]\n"
        "from tests.validators.member_declarations import install\n"
        "class Patch:\n    def setattr(self,obj,key,value): setattr(obj,key,value)\n"
        "install(Patch())\nimport check_plan_completion as ck\nimport run_plan\n"
        "original=run_plan.dispatch_authority_operation\n"
        "def observe(ctx,*args,**kwargs):\n"
        "    budget=ctx.budget\n    ctx.budget=ck.Budget(0.2)\n"
        "    try: return original(ctx,*args,**kwargs)\n"
        "    finally: ctx.budget=budget\n"
        "run_plan.dispatch_authority_operation=observe\nraise SystemExit(ck.main())\n", encoding="utf-8")
    argv = command(fx, entry, operation)
    argv[2] = str(driver)
    return subprocess.run(argv, cwd=fx.work, env=fx.env, capture_output=True,
                          text=True, timeout=90, creationflags=FLAGS)

_GIT = r"""
import json, os, subprocess, sys
from pathlib import Path
args = sys.argv[1:]
if "push" in args:
    at = args.index("push")
    if args[at + 1:at + 2] == ["origin"]:
        with Path(os.environ["BRIDGE_TEST_JOURNAL"]).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": "git-push", "argv": args}) + "\n")
        args[at + 1] = os.environ["BRIDGE_TEST_LOCAL_REMOTE"]
    elif args[at + 1:at + 2] != [os.environ["BRIDGE_TEST_LOCAL_REMOTE"]]:
        raise SystemExit("Private Git stand-in refused an unexpected push destination")
if "ls-remote" in args:
    args = [os.environ["BRIDGE_TEST_LOCAL_REMOTE"] if arg == os.environ["BRIDGE_TEST_SIGNED_REMOTE"] else arg for arg in args]
    if any(arg.startswith(("https:", "http:", "ssh:", "git@")) for arg in args):
        raise SystemExit("Private Git stand-in refused an external read destination")
result = subprocess.run([os.environ["BRIDGE_TEST_REAL_GIT"], *args],
                         capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
sys.stdout.buffer.write(result.stdout)
sys.stderr.buffer.write(result.stderr)
raise SystemExit(result.returncode)
"""


def test_initial_notes_are_prepared_without_a_release_or_tag(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    body = "Private exact initial release notes.\n"
    entry = capture_supplement(fx, log, ".6-release-notes", {"notes": body})
    before_tags = host.git(fx.work, "tag", "--list")
    assert host.load()["release"] is None
    result = execute(fx, entry, "prepare-release-notes")
    assert result.returncode == 0, result.stdout + result.stderr
    artifact = fx.record_path().parent / "release-notes" / (
        fx.record_path().stem + "-" + receipt_id(entry) + "-v4.15.6.md")
    assert artifact.read_bytes() == body.encode("utf-8")
    assert host.load()["release"] is None
    assert host.git(fx.work, "tag", "--list") == before_tags
    assert not host.calls("release-edit")
    row = operation_rows(fx, entry, "prepare-release-notes")[-1]
    assert row["state"] == "completed"
    assert row["evidence"]["proof"] == {
        "path": str(artifact), "notes_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "effect": "prepared", "release_published": False}
    assert execute(fx, entry, "prepare-release-notes").returncode == 0
    context, current = ck.resolve_minor_controller(
        fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    assert ck.project(current, "v4.15.6")["v415_authority"][0]["execution"] == "prepared; release not observed"
    # Published-body verification must never manufacture or edit a release.
    assert execute(fx, entry, "release-notes").returncode != 0
    host.state["release"] = {"tagName": "v4.15.6", "isDraft": False, "body": body}
    host.save()
    assert execute(fx, entry, "release-notes").returncode == 0
    host.state["release"]["body"] = "Subsequent owner edit."
    host.save()
    assert execute(fx, entry, "release-notes").returncode != 0
    assert host.load()["release"]["body"] == "Subsequent owner edit."
    assert not host.calls("release-edit")
    artifact.write_text("Later private owner edit.\n", encoding="utf-8")
    assert execute(fx, entry, "prepare-release-notes").returncode != 0
    assert artifact.read_text() == "Later private owner edit.\n"


def test_description_concurrency_and_old_receipt_survive_new_capture_and_owner(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    original = copy.deepcopy(fx.record())
    resume(fx, log)
    notes = capture_supplement(fx, log, ".6-release-notes", {"notes": "Private initial notes.\n"})
    entry = capture_supplement(fx, log, ".6-repo-description", {"expected": "Before", "value": "Exact description"})
    host.state["effect_delay"] = 0.15
    host.save()
    argv = command(fx, entry, "repo-description")
    before = fx.record_path().read_bytes()
    for extra in (["--operation-id", "f" * 64], ["--retry"]):
        invalid = subprocess.run(argv + extra, cwd=fx.work, env=fx.env, capture_output=True,
                                 text=True, timeout=90, creationflags=FLAGS)
        assert invalid.returncode != 0 and fx.record_path().read_bytes() == before
        assert not host.calls("description-patch")
    processes = [subprocess.Popen(argv, cwd=fx.work, env=fx.env, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, creationflags=FLAGS) for _ in range(2)]
    try:
        outputs = [process.communicate(timeout=90) for process in processes]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=15)
    assert any(process.returncode == 0 for process in processes), outputs
    assert execute(fx, entry, "repo-description").returncode == 0
    assert len(host.calls("description-patch")) == 1
    rows = operation_rows(fx, entry, "repo-description")
    assert [row["state"] for row in rows] == ["ambiguous", "completed"]
    assert rows[0]["evidence"]["reason"] == "reserved-before-dispatch"
    old_identity = rows[-1]["operation_id"]
    second_log = Transcript(Path(fx.env["USERPROFILE"]), fx.work, time.time() - 10, session=NEW_OWNER)
    resume(fx, second_log, session=NEW_OWNER)
    assert execute(fx, entry, "repo-description", session=NEW_OWNER).returncode == 0
    assert execute(fx, entry, "repo-description").returncode != 0
    assert operation_rows(fx, entry, "repo-description")[-1]["operation_id"] == old_identity
    assert_original_approvals_and_exact_capture_append(original, fx.record(), [
        (cm.AUTHORITY_BRIDGE_ACTION, CODEX_SESSION), (cm.AUTHORITY_BRIDGE_ACTION, CODEX_SESSION)],
        [(original["session_id"], CODEX_SESSION, log.path), (CODEX_SESSION, NEW_OWNER, second_log.path)], fx.runs)
    assert fx.record()["v415_authority_receipts"][0] == notes
    assert len(host.calls("description-patch")) == 1


@pytest.mark.parametrize("phase", ["before", "after"])
def test_crash_recovery_never_redispatches_description(bridge_case, monkeypatch, phase):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    entry = capture_supplement(fx, log, ".6-repo-description", {"expected": "Before", "value": "Exact description"})
    stopped = run_cut(fx, entry, "repo-description", phase)
    assert stopped.returncode == (81 if phase == "before" else 82), stopped.stdout + stopped.stderr
    rows = operation_rows(fx, entry, "repo-description")
    assert len(rows) == 1 and rows[0]["state"] == "ambiguous"
    assert len(host.calls("description-patch")) == int(phase == "after")
    for _ in range(2):
        recovered = execute(fx, entry, "repo-description")
        assert (recovered.returncode == 0) == (phase == "after")
    assert len(host.calls("description-patch")) == int(phase == "after")
    assert operation_rows(fx, entry, "repo-description")[-1]["state"] == (
        "completed" if phase == "after" else "ambiguous")
    if phase == "before":
        checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
        assert checked.returncode == 1, checked.stdout + checked.stderr
        blocked = native_job_frame(fx, checked)
        state = blocked["disposition"]
        assert state["state"] == "blocked_external" and state["jobs"] == []
        condition_id = "bridge:effect:" + rows[0]["operation_id"]
        condition = next(item for item in state["external_conditions"] if item["id"] == condition_id)
        assert condition["evidence"] and "reconcile" in condition["resume_when"].lower()
        _, reports = native_snapshot_reports(fx)
        for rendered in reports.values():
            assert rendered.startswith("Waiting for " + condition["title"])
            assert "process:" not in rendered and "github-merge:" not in rendered


def test_description_timeout_projects_real_process_and_reconciles_only_matching_effect(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    entry = capture_supplement(fx, log, ".6-repo-description", {"expected": "Before", "value": "Exact description"})
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    gate = fx.tmp / "release-description-effect"
    host.state["description_effect_gate"] = str(gate)
    host.save()
    try:
        result = run_short_observer(fx, entry, "repo-description")
        assert result.returncode != 0, result.stdout + result.stderr
        row = operation_rows(fx, entry, "repo-description")[-1]
        process_result = row["evidence"]["process_result"]
        assert row["state"] == "ambiguous" and process_result["exit_code"] is None
        assert host.load()["description"] == "Before"
        live = native_job_frame(fx, checked)
        job_id = "bridge:process:" + row["operation_id"]
        job = next(job for job in live["disposition"]["jobs"] if job["id"] == job_id)
        assert job["handle"] == process_result["handle"] and job["status"] == "running"
        _, reports = native_snapshot_reports(fx)
        for rendered in reports.values():
            assert rendered.startswith("Waiting for ") and process_result["handle"] in rendered
            assert "github-merge:" not in rendered
    finally:
        gate.write_text("Allow the actual private description effect.\n", encoding="utf-8")
    output = Path(process_result["stdout_path"])
    deadline = time.monotonic() + 20
    while True:
        try:
            raw_response = output.read_bytes()
            assert len(raw_response) <= 32768
            response = json.loads(raw_response)
            break
        except (OSError, ValueError):
            if time.monotonic() >= deadline:
                pytest.fail("The actual description child produced no complete response")
            time.sleep(0.02)
    assert response == {"description": "Exact description"}
    assert host.load()["description"] == "Exact description"
    assert execute(fx, entry, "repo-description").returncode == 0
    completed = operation_rows(fx, entry, "repo-description")[-1]
    assert completed["operation_id"] == row["operation_id"] and completed["state"] == "completed"
    expected_proof = {"field": "description", "value_sha256": hashlib.sha256(b"Exact description").hexdigest()}
    assert completed["evidence"]["proof"] == expected_proof
    assert completed["evidence"]["process_result"]["exit_code"] is None
    resumed = native_job_frame(fx, checked, live, execute_admitted_dependency(fx, host))
    state = resumed["disposition"]
    assert state["state"] == "working" and state["directive"] == "continue"
    assert not any(job["id"] == job_id for job in state["jobs"])
    observed = next(job for job in state["completed_jobs"] if job["id"] == job_id)
    assert observed["status"] == "succeeded" and observed["result_verified"]
    assert observed["exit_code"] is None and observed["result_kind"] == "hosting-effect-observed"
    assert observed["handle"] == process_result["handle"]
    assert observed["native_bridge"] == {"receipt_id": receipt_id(entry), "operation_id": row["operation_id"]}
    assert observed["effect_receipt"] == {"operation_id": row["operation_id"],
        "proof_sha256": hashlib.sha256(json.dumps(expected_proof, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
    assert not any(item["id"] == "bridge:effect:" + row["operation_id"] for item in state["external_conditions"])
    assert execute(fx, entry, "repo-description").returncode == 0
    assert len(host.calls("description-patch")) == 1
    snapshot, reports = native_snapshot_reports(fx)
    assert snapshot["continuation"]["state"] == "working"
    assert snapshot["continuation"]["directive"] == "continue"
    assert all("State: working" in rendered for rendered in reports.values())


def test_description_precondition_and_unknown_effect_keep_finite_identity(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    entry = capture_supplement(fx, log, ".6-repo-description", {"expected": "Before", "value": "Exact description"})
    before = fx.record_path().read_bytes()
    host.state["description"] = "External change"
    host.save()
    denied = execute(fx, entry, "repo-description")
    assert denied.returncode != 0
    assert fx.record_path().read_bytes() == before and not host.calls("description-patch")
    host.state["description"] = "Before"
    host.state["modes"] = ["reads-unavailable"]
    host.save()
    uncertain = execute(fx, entry, "repo-description")
    assert uncertain.returncode != 0
    identity = operation_rows(fx, entry, "repo-description")[-1]["operation_id"]
    assert host.load()["description"] == "Exact description"
    assert len(host.calls("description-patch")) == 1
    host.mode()
    assert execute(fx, entry, "repo-description").returncode == 0
    assert operation_rows(fx, entry, "repo-description")[-1]["operation_id"] == identity
    assert len(host.calls("description-patch")) == 1


def test_captured_t027_budget_never_dispatches_or_changes_global_caps(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    original = copy.deepcopy(fx.record())
    resume(fx, log)
    entry = capture_supplement(fx, log, ".9-t027-budget", {"usd_total": 10, "spawn_total": 6})
    before = fx.record_path().read_bytes()
    result = execute(fx, entry, "t027-budget")
    assert result.returncode != 0 and "inactive" in result.stdout
    assert fx.record_path().read_bytes() == before
    assert_original_approvals_and_exact_capture_append(original, fx.record(), [
        (cm.AUTHORITY_BRIDGE_ACTION, CODEX_SESSION)], [(original["session_id"], CODEX_SESSION, log.path)], fx.runs)
    assert not fx.record()["v415_publication_operations"]
    assert not host.journal.exists()


def test_publication_distinct_actor_real_guard_and_exact_checked_merge(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    before = fx.record_path().read_bytes()
    missing = execute(fx, entry, "push")
    assert missing.returncode != 0 and "attribution" in missing.stderr.lower()
    assert fx.record_path().read_bytes() == before and not host.calls("git-push")
    diagnostic = fx.record_path().parent / "publication-jobs" / (receipt_id(entry) + ".attribution.json")
    condition = json.loads(diagnostic.read_bytes())["condition"]
    assert condition == "guard-inactive"
    assert ck.project(fx.record(), "v4.15.6")["v415_authority"][-1]["enforcement"] == "blocked:attribution:" + condition
    guard_root = host.install_attribution(actor)
    assert guard_root.is_relative_to(fx.work / ".git")
    # A changed guard is also a preflight failure, before any allowance is spent.
    hook = guard_root / "pre-push"
    original_hook = hook.read_bytes()
    hook.write_bytes(original_hook + b"\n# private altered guard\n")
    denied = execute(fx, entry, "push")
    assert denied.returncode != 0 and "attribution" in denied.stderr.lower()
    assert fx.record_path().read_bytes() == before and not host.calls("git-push")
    condition = json.loads(diagnostic.read_bytes())["condition"]
    assert condition in {"guard-missing-or-modified", "hook-missing-or-modified"}
    assert ck.project(fx.record(), "v4.15.6")["v415_authority"][-1]["enforcement"] == "blocked:attribution:" + condition
    hook.write_bytes(original_hook)
    assert execute(fx, entry, "push").returncode == 0
    assert len(host.calls("git-push")) == 1
    assert host.git(fx.remote, "rev-parse", "refs/heads/" + cm.AUTHORITY_BRIDGE_BRANCH) == payload["head"]
    # Historical push completion cannot stand in for the current remote ref.
    host.git(fx.remote, "update-ref", "refs/heads/" + cm.AUTHORITY_BRIDGE_BRANCH,
             host.state["base"], payload["head"])
    before_pr = fx.record_path().read_bytes()
    assert execute(fx, entry, "pr-create").returncode != 0
    assert fx.record_path().read_bytes() == before_pr and not host.calls("pr-create")
    host.git(fx.remote, "update-ref", "refs/heads/" + cm.AUTHORITY_BRIDGE_BRANCH,
             payload["head"], host.state["base"])
    assert execute(fx, entry, "pr-create").returncode == 0
    assert len(host.calls("pr-create")) == 1
    for mode in ("wrong-pr-head", "wrong-pr-base", "wrong-preview-tree", "wrong-preview-parents",
                 "wrong-check-sha", "stale-check", "strict-false", "bypass", "rules-unavailable",
                 "ruleset-bypass", ("unbound-ruleset", "wrong-app"), "conflicting-app"):
        host.mode(*((mode,) if isinstance(mode, str) else mode))
        before_merge = fx.record_path().read_bytes()
        result = execute(fx, entry, "green-merge")
        assert result.returncode != 0, (mode, result.stdout, result.stderr)
        assert fx.record_path().read_bytes() == before_merge, mode
        assert not host.calls("merge-put"), mode
    # An unbound ruleset must retain the legacy app-123 requirement.
    host.mode("unbound-ruleset")
    assert execute(fx, entry, "green-merge").returncode == 0
    state = host.load()
    assert state["merged_sha"] != state["preview"]
    assert host.git(fx.remote, "rev-parse", "develop") == state["merged_sha"]
    assert len(host.calls("merge-put")) == 1
    assert execute(fx, entry, "green-merge").returncode == 0
    assert len(host.calls("git-push")) == len(host.calls("pr-create")) == len(host.calls("merge-put")) == 1


def test_async_acceptance_retains_identity_until_independent_merge_observed(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    assert execute(fx, entry, "push").returncode == 0
    assert execute(fx, entry, "pr-create").returncode == 0
    host.mode("merge-pending")
    result = execute(fx, entry, "green-merge")
    assert result.returncode != 0 and not host.load()["pull"]["merged"]
    rows = operation_rows(fx, entry, "green-merge")
    identity = rows[-1]["operation_id"]
    assert rows[-1]["state"] == "ambiguous"
    assert rows[-1]["evidence"]["host_correlation"] == "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    assert rows[-1]["evidence"]["host_response"]["body"]["details"]["expected_head_sha"] == payload["head"]
    assert host.calls("merge-get")[-1]["argv"][1].endswith(
        "/merge-async/630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42")
    assert execute(fx, entry, "green-merge").returncode != 0
    assert len(host.calls("merge-put")) == 1
    # A real returned pending UUID enters the controller and both reports. Polls
    # may refresh the unsigned observation cache, never append clock-only events.
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    signed_before = fx.record_path().read_bytes()
    pending = native_job_frame(fx, checked)
    job = next(job for job in pending["observation"]["jobs"] if job.get("native_bridge"))
    handle = "github-merge:630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    endpoint = "https://api.github.com/repos/bendourthe/Nexus-Hub/pulls/314/merge-async/630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    assert job["handle"] == handle and job["url"] == endpoint and job["status"] == "pending"
    first_data, _ = native_snapshot_reports(fx)
    reporter = run_plan.reporting_module("status_report")
    receipt = reporter.select_report(first_data, None, "start")["receipt"]
    pending = native_job_frame(fx, checked, pending)
    second_data, _ = native_snapshot_reports(fx)
    first_job = next(job for job in first_data["continuation"]["jobs"] if job.get("native_bridge"))
    second_job = next(job for job in second_data["continuation"]["jobs"] if job.get("native_bridge"))
    assert first_job["handle"] == second_job["handle"] == handle
    assert first_job["status"] == second_job["status"] == "pending"
    assert second_job["observed_at"] > first_job["observed_at"]
    # Advance only the report scheduling clock beyond the interval. Provider
    # timestamps, cache signatures and observations remain the actual poll output.
    after_interval = copy.deepcopy(second_data)
    after_interval["observed_at"] = (dt.datetime.fromisoformat(second_data["observed_at"].replace("Z", "+00:00"))
                                     + dt.timedelta(seconds=601)).isoformat()
    for event in ("checkpoint", "resume", "turn-end"):
        unchanged = reporter.select_report(after_interval, receipt, event, interval=300)
        assert unchanged["mode"] == "none" and unchanged["report"] == ""
    observed_at = next(job for job in pending["observation"]["jobs"] if job.get("native_bridge"))["observed_at"]
    host.mode("merge-pending", "async-get-unavailable")
    unavailable = native_job_frame(fx, checked, pending)
    waiting = next(job for job in unavailable["observation"]["jobs"] if job.get("native_bridge"))
    assert waiting["handle"] == handle and waiting["url"] == endpoint
    assert waiting["status"] == "observation-timeout" and waiting["observed_at"] == observed_at
    assert waiting["observation_attempted_at"] >= observed_at
    assert "unavailable" in waiting["evidence"] and "same returned UUID" in waiting["resume_when"]
    unavailable_data, reports = native_snapshot_reports(fx)
    changed = reporter.select_report(unavailable_data, receipt, "checkpoint")
    assert changed["mode"] == "compact"
    for rendered in reports.values():
        assert rendered.startswith("Waiting for "), rendered
        assert handle in rendered and endpoint in rendered and observed_at in rendered
        assert "observation-timeout" in rendered and "same returned UUID" in rendered
        assert "Nothing running" not in rendered
    assert fx.record_path().read_bytes() == signed_before
    assert len(host.calls("merge-put")) == 1
    assert all(call["argv"][1].endswith("/merge-async/630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42")
               for call in host.calls("merge-get"))
    host.mode("merge-pending")
    refreshed = native_job_frame(fx, checked, unavailable)
    assert next(job for job in refreshed["observation"]["jobs"] if job.get("native_bridge"))["status"] == "pending"
    assert fx.record_path().read_bytes() == signed_before
    merged = host.complete_pending_merge()
    # A mismatching independently observed result cannot complete the reservation.
    host.mode("wrong-final-tree")
    assert execute(fx, entry, "green-merge").returncode != 0
    assert operation_rows(fx, entry, "green-merge")[-1]["state"] == "ambiguous"
    host.mode()
    assert execute(fx, entry, "green-merge").returncode == 0
    row = operation_rows(fx, entry, "green-merge")[-1]
    assert row["operation_id"] == identity and row["state"] == "completed"
    assert row["evidence"]["proof"]["merge_sha"] == merged
    assert len(host.calls("merge-put")) == 1
    # Resume a genuinely admitted unfinished fixture task after the process result.
    # The native declaration and measured predicates provide its authorization.
    terminal = native_job_frame(fx, checked, refreshed, execute_admitted_dependency(fx, host))
    assert terminal["disposition"]["state"] == "working"
    assert terminal["disposition"]["directive"] == "continue"
    assert not any(job.get("handle") == handle for job in terminal["disposition"]["jobs"])
    retired = terminal["disposition"]["completed_jobs"]
    assert any(job["handle"] == handle and job["status"] == "succeeded" and job["result_verified"] for job in retired)
    resumed_data, _ = native_snapshot_reports(fx)
    assert reporter.select_report(resumed_data, changed["receipt"], "checkpoint")["mode"] == "compact"


def test_late_host_response_keeps_process_handle_and_never_redispatches(bridge_case, monkeypatch):
    import psutil

    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    assert execute(fx, entry, "push").returncode == 0
    assert execute(fx, entry, "pr-create").returncode == 0
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    gate = fx.tmp / "release-real-host-response"
    host.mode("merge-pending")
    host.state["response_gate"] = str(gate)
    host.save()
    live_frame = None
    try:
        delayed = run_short_observer(fx, entry)
        assert delayed.returncode != 0, delayed.stdout + delayed.stderr
        row = operation_rows(fx, entry, "green-merge")[-1]
        assert row["state"] == "ambiguous" and "host_correlation" not in row["evidence"]
        process_result = row["evidence"]["process_result"]
        assert process_result["exit_code"] is None
        process = psutil.Process(process_result["process"]["pid"])
        assert abs(process.create_time() - process_result["process"]["created_at"]) < 0.01
        assert process.is_running()
        handle = process_result["handle"]
        assert handle.startswith("process:")
        operation_id = row["operation_id"]
        job_id = "bridge:process:" + operation_id
        scope = argparse.Namespace(minor=True, label="v4.15", repo_root=fx.work, observer_session=CODEX_SESSION)
        _, current = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
        facts = run_plan.native_owner_observation(scope, fx.record_path(), current, None, remaining_tasks=3)
        live_jobs = [job for job in facts["jobs"] if job.get("id") == job_id]
        # An unsigned serialized overlay cannot invent or replace this native job.
        forged = {"observation": copy.deepcopy(facts), "disposition": {}}
        forged["observation"]["jobs"] = [{"id": job_id, "name": "Forged response process",
            "handle": "process:1:1.000000", "status": "running", "observed_at": ck._now(),
            "resume_when": "Invented", "evidence": "Invented",
            "native_bridge": {"receipt_id": receipt_id(entry), "operation_id": operation_id}}]
        projected = run_plan.native_owner_observation(scope, fx.record_path(), current, forged, remaining_tasks=3)
        assert not any(job.get("handle") == "process:1:1.000000" for job in projected["jobs"])
        if live_jobs:
            assert live_jobs[0]["handle"] == handle
            assert live_jobs[0]["status"] in {"running", "observation-timeout"}
            live_frame = native_job_frame(fx, checked)
            _, reports = native_snapshot_reports(fx)
            for rendered in reports.values():
                assert rendered.startswith("Waiting for ") and handle in rendered
                assert "github-merge:" not in rendered
    finally:
        gate.write_text("Allow the real private child to finish its response.\n", encoding="utf-8")
    # Read the actual bounded child output, never infer a host result from exit.
    output = Path(process_result["stdout_path"])
    deadline = time.monotonic() + 20
    while True:
        try:
            raw = output.read_bytes()
            assert len(raw) <= 32768
            response = json.loads(raw)
            break
        except (OSError, ValueError):
            if time.monotonic() >= deadline:
                pytest.fail("The actual delayed private child produced no complete response")
            time.sleep(0.02)
    uuid = "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    assert response["details"]["uuid"] == uuid
    reconciled = execute(fx, entry, "green-merge")
    assert reconciled.returncode != 0 and not host.load()["pull"]["merged"]
    after = operation_rows(fx, entry, "green-merge")[-1]
    assert len(host.calls("merge-put")) == 1
    assert live_jobs, "Native projection concealed the actual live process after observation timeout"
    assert after["operation_id"] == operation_id and after["state"] == "ambiguous"
    assert after["evidence"]["process_result"]["exit_code"] is None
    assert after["evidence"]["host_correlation"] == uuid
    assert after["evidence"]["host_response"]["body"] == response
    resumed = native_job_frame(fx, checked, live_frame)
    completed = next(job for job in resumed["disposition"]["completed_jobs"] if job["id"] == job_id)
    assert completed["handle"] == handle and completed["result_verified"]
    assert completed["exit_code"] is None and completed["result_kind"] == "hosting-response-observed"
    assert completed["response_receipt"] == {"path": str(output), "sha256": hashlib.sha256(raw).hexdigest(),
        "operation_id": operation_id, "command_sha256": after["command_sha256"]}
    assert "exit code remains unobserved" in completed["evidence"]
    assert "merge/effect not verified" in completed["evidence"]
    remote = next(job for job in resumed["disposition"]["jobs"] if job["id"] == "bridge:" + operation_id)
    assert remote["handle"] == "github-merge:" + uuid and remote["status"] == "pending"
    assert host.calls("merge-get") and all(call["argv"][1].endswith("/merge-async/" + uuid)
                                          for call in host.calls("merge-get"))


def test_failed_host_response_without_uuid_reports_verified_external_blocker(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    assert execute(fx, entry, "push").returncode == 0
    assert execute(fx, entry, "pr-create").returncode == 0
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    gate = fx.tmp / "release-failed-host-response"
    host.mode("merge-pending", "failed-response-no-uuid")
    host.state["response_gate"] = str(gate)
    host.save()
    try:
        result = run_short_observer(fx, entry)
        assert result.returncode != 0, result.stdout + result.stderr
        prior = operation_rows(fx, entry, "green-merge")[-1]
        process_result = prior["evidence"]["process_result"]
        assert process_result["exit_code"] is None
        live = native_job_frame(fx, checked)
        process_job_id = "bridge:process:" + prior["operation_id"]
        assert any(job["id"] == process_job_id and job["handle"] == process_result["handle"]
                   for job in live["disposition"]["jobs"])
    finally:
        gate.write_text("Release the actual failed private host response.\n", encoding="utf-8")
    output = Path(process_result["stdout_path"])
    deadline = time.monotonic() + 20
    while True:
        try:
            raw = output.read_bytes()
            assert len(raw) <= 32768
            response = json.loads(raw)
            break
        except (OSError, ValueError):
            if time.monotonic() >= deadline:
                pytest.fail("The private failed-response child produced no complete JSON")
            time.sleep(0.02)
    assert response["status"] == "failed" and response["details"] == {}
    assert execute(fx, entry, "green-merge").returncode != 0
    current = operation_rows(fx, entry, "green-merge")[-1]
    assert current["state"] == "ambiguous" and current["operation_id"] == prior["operation_id"]
    assert "host_correlation" not in current["evidence"]
    assert current["evidence"]["host_response"]["body"] == response
    assert current["evidence"]["process_result"]["exit_code"] is None
    blocked = native_job_frame(fx, checked, live)
    state = blocked["disposition"]
    assert state["state"] == "blocked_external" and state["directive"] == "wait"
    assert state["jobs"] == []
    observed = next(job for job in state["completed_jobs"] if job["id"] == process_job_id)
    assert observed["status"] == "succeeded" and observed["result_verified"]
    assert observed["result_kind"] == "hosting-response-observed" and observed["response_status"] == "failed"
    assert observed["exit_code"] is None
    digest = hashlib.sha256(raw).hexdigest()
    assert observed["response_receipt"] == {"path": str(output), "sha256": digest,
        "operation_id": current["operation_id"], "command_sha256": current["command_sha256"]}
    condition_id = "bridge:failure:" + current["operation_id"]
    condition = next(item for item in state["external_conditions"] if item["id"] == condition_id)
    assert condition["title"] == "Hosting reported failure; merge effect unverified"
    assert digest in condition["evidence"] and current["operation_id"] in condition["evidence"]
    assert "decision" in condition["resume_when"].lower()
    before = fx.record_path().read_bytes()
    data, reports = native_snapshot_reports(fx)
    for rendered in reports.values():
        assert rendered.startswith("Waiting for " + condition["title"])
        assert digest in rendered and "github-merge:" not in rendered
        assert "Nothing running" not in rendered
    # An unsigned serialized resolution cannot erase the native failure proof.
    forged = copy.deepcopy(blocked)
    forged["observation"]["condition_resolutions"] = [{"condition_id": condition_id,
        "verified": True, "evidence": "Invented successful resolution"}]
    retained = native_job_frame(fx, checked, forged)
    assert any(item["id"] == condition_id for item in retained["disposition"]["external_conditions"])
    assert execute(fx, entry, "green-merge").returncode != 0
    assert fx.record_path().read_bytes() == before
    assert len(host.calls("merge-put")) == 1 and not host.calls("merge-get")
    assert not host.load()["pull"]["merged"]
    reporter = run_plan.reporting_module("status_report")
    receipt = reporter.select_report(data, None, "start")["receipt"]
    repeated, _ = native_snapshot_reports(fx)
    repeated["observed_at"] = (dt.datetime.fromisoformat(repeated["observed_at"].replace("Z", "+00:00"))
                               + dt.timedelta(seconds=601)).isoformat()
    assert reporter.select_report(repeated, receipt, "turn-end")["mode"] == "none"
    # A separately performed matching effect can retire the failure condition;
    # the same consumer observes it without dispatching the rejected request again.
    merged = host.complete_pending_merge()
    assert execute(fx, entry, "green-merge").returncode == 0
    completed = operation_rows(fx, entry, "green-merge")[-1]
    assert completed["operation_id"] == prior["operation_id"] and completed["state"] == "completed"
    assert completed["evidence"]["proof"]["merge_sha"] == merged
    resumed = native_job_frame(fx, checked, retained, execute_admitted_dependency(fx, host))
    assert not any(item["id"] == condition_id for item in resumed["disposition"]["external_conditions"])
    assert resumed["disposition"]["state"] == "working" and resumed["disposition"]["directive"] == "continue"
    resumed_data, resumed_reports = native_snapshot_reports(fx)
    assert reporter.select_report(resumed_data, receipt, "checkpoint")["mode"] == "compact"
    assert all(condition["title"] not in rendered for rendered in resumed_reports.values())
    assert len(host.calls("merge-put")) == 1 and not host.calls("merge-get")


def test_get_terminal_failure_stays_retired_until_matching_effect_is_verified(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    assert execute(fx, entry, "push").returncode == 0
    assert execute(fx, entry, "pr-create").returncode == 0
    host.mode("merge-pending")
    assert execute(fx, entry, "green-merge").returncode != 0
    row = operation_rows(fx, entry, "green-merge")[-1]
    uuid = "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    assert row["evidence"]["host_correlation"] == uuid
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    pending = native_job_frame(fx, checked)
    job_id = "bridge:" + row["operation_id"]
    assert any(job["id"] == job_id and job["status"] == "pending" for job in pending["disposition"]["jobs"])
    host.mode("merge-pending", "async-get-failed")
    failed = native_job_frame(fx, checked, pending)
    state = failed["disposition"]
    assert state["state"] == "blocked_external" and state["jobs"] == []
    retired = next(job for job in state["completed_jobs"] if job["id"] == job_id)
    assert retired["handle"] == "github-merge:" + uuid and retired["status"] == "failed" and retired["result_verified"]
    failure_sha = retired["provider_observation"]["first_failure_sha256"]
    condition_id = "bridge:failure:" + row["operation_id"]
    condition = next(item for item in state["external_conditions"] if item["id"] == condition_id)
    assert failure_sha in condition["evidence"]
    data, reports = native_snapshot_reports(fx)
    assert all(rendered.startswith("Waiting for " + condition["title"]) for rendered in reports.values())
    reporter = run_plan.reporting_module("status_report")
    receipt = reporter.select_report(data, None, "start")["receipt"]
    signed_before = fx.record_path().read_bytes()
    previous = failed
    for mode in (None, "async-get-enqueued", "async-get-unavailable"):
        host.mode("merge-pending", *((mode,) if mode else ()))
        current = native_job_frame(fx, checked, previous)
        disposition = current["disposition"]
        assert disposition["state"] == "blocked_external" and disposition["jobs"] == []
        assert [job["id"] for job in disposition["completed_jobs"]].count(job_id) == 1
        retained = next(job for job in disposition["completed_jobs"] if job["id"] == job_id)
        assert retained["handle"] == "github-merge:" + uuid and retained["status"] == "failed"
        assert retained["provider_observation"]["first_failure_sha256"] == failure_sha
        assert any(item["id"] == condition_id and failure_sha in item["evidence"] for item in disposition["external_conditions"])
        repeated, _ = native_snapshot_reports(fx)
        repeated["observed_at"] = (dt.datetime.fromisoformat(repeated["observed_at"].replace("Z", "+00:00"))
                                   + dt.timedelta(seconds=601)).isoformat()
        for event in ("checkpoint", "resume", "turn-end"):
            assert reporter.select_report(repeated, receipt, event)["mode"] == "none"
        assert fx.record_path().read_bytes() == signed_before and len(host.calls("merge-put")) == 1
        previous = current
    host.mode()
    merged = host.complete_pending_merge()
    assert execute(fx, entry, "green-merge").returncode == 0
    completed = operation_rows(fx, entry, "green-merge")[-1]
    assert completed["operation_id"] == row["operation_id"] and completed["state"] == "completed"
    assert completed["evidence"]["proof"]["merge_sha"] == merged
    resumed = native_job_frame(fx, checked, previous, execute_admitted_dependency(fx, host))
    assert resumed["disposition"]["state"] == "working" and resumed["disposition"]["directive"] == "continue"
    assert not any(item["id"] == condition_id for item in resumed["disposition"]["external_conditions"])
    assert not any(job["id"] == job_id for job in resumed["disposition"]["jobs"])
    resumed_data, _ = native_snapshot_reports(fx)
    assert reporter.select_report(resumed_data, receipt, "checkpoint")["mode"] == "compact"
    assert len(host.calls("merge-put")) == 1
    assert all(call["argv"][1].endswith("/merge-async/" + uuid) for call in host.calls("merge-get"))


def test_unused_publication_receipt_cannot_follow_a_changed_actor_head(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    changed = actor / "src/private-maintenance.txt"
    changed.write_text("A later unreviewed private contribution.\n", encoding="utf-8")
    host.git(actor, "add", "--", "src/private-maintenance.txt")
    host.git(actor, "commit", "-q", "-m", "private changed candidate")
    assert host.git(actor, "rev-parse", "HEAD") != payload["head"]
    before = fx.record_path().read_bytes()
    assert execute(fx, entry, "push").returncode != 0
    assert fx.record_path().read_bytes() == before
    assert not host.calls("git-push") and not fx.record()["v415_publication_operations"]


def test_preparation_recovers_only_its_persisted_link_stage(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    body = "Private captured recovery notes.\n"
    entry = capture_supplement(fx, log, ".6-release-notes", {"notes": body})
    artifact = fx.record_path().parent / "release-notes" / (
        fx.record_path().stem + "-" + receipt_id(entry) + "-v4.15.6.md")
    driver = fx.tmp / "cut-notes-link.py"
    driver.write_text(
        "import os,sys\nfrom pathlib import Path\n"
        f"sys.path[:0] = [{str(ROOT)!r}, {str(ROOT / 'scripts')!r}]\n"
        "from tests.validators.member_declarations import install\n"
        "class Patch:\n    def setattr(self,obj,key,value): setattr(obj,key,value)\n"
        "install(Patch())\n"
        "import check_plan_completion as ck\n"
        "original=os.link\n"
        "def cut(src,dst,*args,**kwargs):\n"
        "    result=original(src,dst,*args,**kwargs)\n"
        f"    if Path(dst) == Path({str(artifact)!r}): os._exit(83)\n"
        "    return result\n"
        "os.link=cut\nraise SystemExit(ck.main())\n",
        encoding="utf-8")
    argv = command(fx, entry, "prepare-release-notes")
    argv[2] = str(driver)
    stopped = subprocess.run(argv, cwd=fx.work, env=fx.env, capture_output=True,
                             text=True, timeout=90, creationflags=FLAGS)
    assert stopped.returncode == 83, stopped.stdout + stopped.stderr
    assert artifact.read_bytes() == body.encode("utf-8") and artifact.stat().st_nlink == 2
    old_ids = {row["operation_id"] for row in operation_rows(fx, entry, "prepare-release-notes")}
    assert old_ids == {cm._bridge_operation_id(entry, "prepare-release-notes")}
    resumed = execute(fx, entry, "prepare-release-notes")
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert artifact.read_bytes() == body.encode("utf-8") and artifact.stat().st_nlink == 1
    assert operation_rows(fx, entry, "prepare-release-notes")[-1]["state"] == "completed"
    assert {row["operation_id"] for row in operation_rows(fx, entry, "prepare-release-notes")} == old_ids
    assert not host.calls("release-edit") and host.load()["release"] is None


def test_preparation_refuses_foreign_hardlink_without_removing_it(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    body = "Private same bytes do not establish stage ownership.\n"
    entry = capture_supplement(fx, log, ".6-release-notes", {"notes": body})
    artifact = fx.record_path().parent / "release-notes" / (
        fx.record_path().stem + "-" + receipt_id(entry) + "-v4.15.6.md")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    foreign = fx.tmp / "independent-owner-file.md"
    foreign.write_bytes(body.encode("utf-8"))
    os.link(foreign, artifact)
    result = execute(fx, entry, "prepare-release-notes")
    assert result.returncode != 0
    assert artifact.read_bytes() == foreign.read_bytes() == body.encode("utf-8")
    assert artifact.stat().st_nlink == foreign.stat().st_nlink == 2
    assert not any(row["state"] == "completed" for row in operation_rows(fx, entry, "prepare-release-notes"))
    assert not host.calls("release-edit") and host.load()["release"] is None
