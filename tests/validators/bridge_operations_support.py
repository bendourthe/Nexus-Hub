"""Shared helpers for the v4.15 authority bridge operations tests; never live permission or hosting proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from tests.fixtures.gh_stub.launcher import make_stub
from .test_v415_authority_bridge import (
    ROOT, CODEX_SESSION, binding, cm, ck,
    run_plan,
)
from . import git_stub_fastpath
from .member_declarations import DECLARED_CHECKER
from .test_completion_minor_record import GH_STUB

FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
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
