"""Typed execution grants through disposable native captures and real Git trees.

These are private test decisions, never live user authority. Hosting uses the
existing local gh fixture; no test contacts a provider or installed native home.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from .test_completion_minor_record import (
    Minor, SESSION, REPO_ROOT, CHECKER, ck, cm, _git,
    _isolated_git_config, _no_transport_overrides,
)
from .test_completion_minor_verdict import EVIDENCE_SECTIONS, GREEN
import approval_page as approval_display

# Importing an autouse fixture is what activates it for this module: these two
# keep every test away from the user's git config and transport overrides.
AUTOUSE_FIXTURES = (_isolated_git_config, _no_transport_overrides)


BASELINE = "1dc21b92db664347d18ff591e02e1e73c0d8c867"
TOKEN = "v4.15"
PLAN_DIR = "docs/releases/v4/v4.15/plans"
REGISTRY = "catalog/hooks/settings.json"
WORKFLOW_PATHS = [
    ".github/workflows/ci.yml", ".github/workflows/post-merge.yml",
    ".github/workflows/release.yml", ".github/workflows/nexus-hub-settings.yml",
    ".github/workflows/claude-usage-monitor.yml", ".github/workflows/codex-usage-monitor.yml",
    ".github/workflows/copilot-usage-monitor.yml", ".github/workflows/cursor-usage-monitor.yml",
    ".github/workflows/gemini-usage-monitor.yml",
]
RECIPES = {
    "v4.15.5": {"hooks": {
        "PostToolUse": [{"matcher": "Bash|Edit|Write|MultiEdit", "hooks": [
            {"type": "command", "command": "bash .claude/hooks/stuck-turn-notice.sh"}]}],
        "PostToolUseFailure": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": "bash .claude/hooks/stuck-turn-notice.sh"}]}],
    }},
    "v4.15.6": {"hooks": {
        "PreToolUse": [{"matcher": "Bash|PowerShell", "hooks": [
            {"type": "command", "command": "bash .claude/hooks/worktree-policy.sh"}]}],
    }},
}
SETTINGS = {"model": "fixture-model", "effortLevel": "high", "env": {"FIXTURE": "1"},
            "attribution": {"commit": ""}, "modelSettings": {"fixture": True},
            "hooks": {"PreToolUse": [{"matcher": "Read", "hooks": [
                {"type": "command", "command": "bash .claude/hooks/existing-read-guard.sh"}]}],
                "PostToolUse": [{"matcher": "Read", "hooks": [
                    {"type": "command", "command": "bash .claude/hooks/existing-after-read.sh"}]},
                    {"matcher": "Edit", "hooks": [{"type": "command",
                        "command": "bash .claude/hooks/existing-after-edit.sh"}]}]}}


@pytest.fixture(autouse=True)
def _private_native_home(tmp_path, monkeypatch):
    home = tmp_path / "private-home"
    for key, suffix in (("HOME", ""), ("USERPROFILE", ""), ("APPDATA", "appdata"),
                        ("LOCALAPPDATA", "localappdata"), ("NEXUS_HUB_HOME", ".nexus-hub"),
                        ("CODEX_HOME", ".codex")):
        target = home / suffix
        target.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(key, str(target))
    monkeypatch.delenv("NEXUS_RUNNER_CHECKER", raising=False)


class ExecutionMinor(Minor):
    """Reuse the existing Git/capture fixture without relaxing the v4.15 table."""

    def __init__(self, tmp, monkeypatch):
        self.permission_mode = "bypassPermissions"
        self._monkeypatch = monkeypatch
        super().__init__(tmp, monkeypatch)
        _git(self.work, "remote", "set-url", "--push", "origin",
             "https://github.com/bendourthe/Nexus-Hub.git")
        for patch in (1, 2, 3):
            self.plan(f"v4.15.{patch}", f"original-{patch}")
        for rel, text in [(REGISTRY, json.dumps(SETTINGS)),
                          *[(name, "name: fixture\n") for name in WORKFLOW_PATHS],
                          (".pre-commit-config.yaml", "repos: []\n")]:
            target = self.work / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        self.commit("complete private original five-member fixture")
        self.integrate()

    def plan(self, version, slug, status="queued", folder=PLAN_DIR):
        initial = {"v0.5.2": ("v4.15.0", "original-0"),
                   "v0.5.10": ("v4.15.4", "original-4")}
        version, slug = initial.get(version, (version, slug))
        rel = f"{folder}/{version}-{slug}.md"
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        worker_paths = [rel, f"src/{slug}.txt", f"tests/test_{slug.replace('-', '_')}.py",
                        f"docs/releases/v4/v4.15/development/{version}-last-phase-evidence.md"]
        if version in RECIPES:
            worker_paths.append(REGISTRY)
        elif version == "v4.15.7":
            worker_paths += WORKFLOW_PATHS[:2] + [".pre-commit-config.yaml"]
        text = (f"# Plan - {slug}\n\n**Version**: {version}\n**Slug**: {slug}\n"
                f"**Status**: {status}\n\n## Implementation dependencies and ownership\n\n"
                "```json\n" + json.dumps({"depends_on": [], "read_paths": [],
                                            "write_paths": worker_paths}) + "\n```\n")
        if version in {"v4.15.5", "v4.15.6", "v4.15.7", "v4.15.8"}:
            text += "\n### Coordinator Proposed Outputs\n\n```json\n" + json.dumps(
                {"write_paths": ([*WORKFLOW_PATHS, "CHANGELOG.md"] if version == "v4.15.8" else ["CHANGELOG.md"])}) + "\n```\n"
        if version in RECIPES:
            text += "\n### Native Execution Registration Recipe\n\n```json\n" + json.dumps(
                RECIPES[version]) + "\n```\n"
        text += f"\n## Phase 1: Build\n\n- [ ] T001 Implement src/{slug}.txt\n"
        path.write_text(text, encoding="utf-8")
        return rel

    def integrate(self):
        _git(self.work, "branch", "-f", "develop", "HEAD")
        self.publish("develop")

    def run(self, *args):
        return subprocess.run([sys.executable, str(CHECKER), *args], cwd=self.work,
                              env=self.env, capture_output=True, text=True, check=False,
                              timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def approvals(self, *extra):
        value = {"repo": "bendourthe/Nexus-Hub", "target_branch": "develop", "classes": [
            {"class": "push-merge"}, {"class": "release"}, {"class": "cleanup-merged"},
            {"class": "archive-member"}, {"class": "archive-minor"},
            {"class": "minor-close-pr", "bound": 3}, *extra]}
        path = self.tmp / "original-approvals.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def render(self, session, *args):
        return self.run("record", "render", "--minor", TOKEN, "--session", session, *args)

    def paste(self, session, *args):
        self.capture(session, "/implement v4.15", at=0.0)
        rendered = self.render(session, *args)
        assert rendered.returncode == 0, rendered.stdout + rendered.stderr
        line = rendered.stdout.splitlines()[0]
        self.capture(session, line)
        return line

    def capture(self, session, *texts, at=None):
        if at is not None:
            super().capture(session, *texts, at=at)
            return
        import completion_gate as gate
        for prompt in texts:
            payload = {"session_id": session, "prompt": prompt, "cwd": str(self.work)}
            if self.permission_mode is not None:
                payload["permission_mode"] = self.permission_mode
            with self._monkeypatch.context() as patch:
                patch.setattr(gate, "_runs_dir", lambda: self.runs)
                patch.setattr(gate, "_read_payload", lambda: payload)
                assert gate.cmd_capture() == 0

    def create(self):
        approvals = str(self.approvals())
        self.paste(SESSION, "--approvals", approvals)
        return self.run("record", "create", "--minor", TOKEN, "--session", SESSION,
                        "--approvals", approvals)

    def record_path(self):
        return self.rctx().scoped_record_path("minor:v4.15")

    def member(self, version):
        return next(m for m in cm.effective_members(ck, self.record()) if m["version"] == version)

    def add_members(self, versions=("v4.15.5", "v4.15.6", "v4.15.7", "v4.15.8"), *, transform=None):
        members = []
        for version in versions:
            slug = "execution-" + version.rsplit(".", 1)[-1]
            rel = self.plan(version, slug)
            if transform is not None:
                plan = self.work / rel
                plan.write_text(transform(version, plan.read_text(encoding="utf-8")), encoding="utf-8")
            members.append({"version": version, "plan_path": rel,
                "plan_sha256": ck.plan_hash_text((self.work / rel).read_text(encoding="utf-8")),
                "source_branch": f"feat/{version}-{slug}", "target_branch": "develop",
                "release_version": version, "tag": version, "approvals": {"classes": [
                    {"class": "push-merge"}, {"class": "release", "bound": version},
                    {"class": "archive-member"}], "cleanup": {"branches": [], "worktrees": []}}})
        self.commit("integrate private added-member plans")
        self.integrate()
        path = self.tmp / "membership.json"
        path.write_text(json.dumps({"members": members}), encoding="utf-8")
        self.paste(SESSION, "--action", "amend-minor", "--amendment", str(path))
        result = self.run("record", "amend-minor", "--minor", TOKEN, "--session", SESSION,
                          "--amendment", str(path))
        assert result.returncode == 0, result.stdout + result.stderr

    def worker(self, version):
        path = self.tmp / ("worker-" + version)
        _git(self.work, "worktree", "add", "-q", "-b", self.member(version)["source_branch"],
             str(path), "origin/develop")
        return path

    def paths(self, version):
        return ([REGISTRY] if version in RECIPES else WORKFLOW_PATHS[:2] + [".pre-commit-config.yaml"]
                if version == "v4.15.7" else WORKFLOW_PATHS[:1])

    def request(self, version, value=None):
        path = self.tmp / ("execution-" + version + ".json")
        path.write_text(json.dumps(value if value is not None else {"write_paths": self.paths(version)}),
                        encoding="utf-8")
        return path

    def grant(self, version, path=None):
        path = path or self.request(version)
        self.paste(SESSION, "--action", "permit-member-execution-paths", "--member", version,
                   "--execution", str(path))
        result = self.run("record", "permit-member-execution-paths", "--minor", TOKEN,
                          "--session", SESSION, "--member", version, "--execution", str(path))
        assert result.returncode == 0, result.stdout + result.stderr
        return self.record()["minor_execution_permissions"][-1]

    def admit(self, version, worker, *, sensitive=True, depends=()):
        member = self.member(version)
        slug = "execution-" + version.rsplit(".", 1)[-1]
        value = {"depends_on": list(depends), "read_paths": [], "write_paths": [member["plan_path"],
                 f"src/{slug}.txt", f"tests/test_{slug.replace('-', '_')}.py",
                 f"docs/releases/v4/v4.15/development/{version}-last-phase-evidence.md"]}
        if sensitive and version != "v4.15.8":
            value["write_paths"] += self.paths(version)
        path = self.tmp / ("claims-" + version + ".json")
        path.write_text(json.dumps(value), encoding="utf-8")
        return self.run("record", "member-implement-start", "--minor", TOKEN, "--session", SESSION,
                        "--member", version, "--repo", str(self.work), "--worktree", str(worker),
                        "--head", _git(worker, "rev-parse", "HEAD"), "--claims", str(path))

    def project(self, version):
        result = self.run("check-member", "--minor", TOKEN, "--session", SESSION,
                          "--member", version, "--repo", str(self.work), "--json")
        return result, json.loads(result.stdout.splitlines()[-1])

    def publication(self, version, coordinator_paths=()):
        args = ["record", "member-start", "--minor", TOKEN, "--session", SESSION, "--member", version,
                "--head", _git(self.work, "rev-parse", "origin/develop")]
        if coordinator_paths:
            path = self.tmp / ("publication-" + version + ".json")
            path.write_text(json.dumps({"write_paths": list(coordinator_paths)}), encoding="utf-8")
            args += ["--coordinator-claims", str(path)]
        return self.run(*args)

    def released_fixture_member(self, version, worker=None):
        """Real commits/tags/tests plus local hosting observations, never a real release."""
        member = self.member(version)
        slug = (Path(member["plan_path"]).stem.removeprefix(version + "-"))
        root = worker or self.work
        rel, source = member["plan_path"], f"src/{slug}.txt"
        test = f"tests/test_{slug.replace('-', '_')}.py"
        evidence = f"docs/releases/v4/v4.15/development/{version}-last-phase-evidence.md"
        outputs = {
            rel: (root / rel).read_text(encoding="utf-8").replace("- [ ] T001", "- [x] T001"),
            source: slug + "\n",
            test: "from pathlib import Path\n\ndef test_private_source():\n    assert (Path(__file__).resolve().parents[1] / "
                  + repr(source) + ").read_text() == " + repr(slug + "\n") + "\n",
        }
        for name, text in outputs.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        if version in RECIPES:
            add_registration(root, version)
            outputs[REGISTRY] = (root / REGISTRY).read_text(encoding="utf-8")
        elif version == "v4.15.7":
            for name in self.paths(version):
                text = "repos: []\n# private changed pre-commit fixture\n" if name.startswith(".pre-") else "name: private changed workflow\n"
                (root / name).write_text(text, encoding="utf-8")
                outputs[name] = text
        elif version == "v4.15.8":
            text = "name: private coordinator workflow\n"
            (root / WORKFLOW_PATHS[0]).write_text(text, encoding="utf-8")
            outputs[WORKFLOW_PATHS[0]] = text
        tested = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=root,
                                env={**self.env, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True,
                                text=True, check=False, timeout=90,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        assert tested.returncode == 0, tested.stdout + tested.stderr
        body = "".join(f"## {heading}\n\nPrivate native-mechanics fixture; not a production release.\n\n" for heading in EVIDENCE_SECTIONS)
        body += f"## Full-suite testing and stabilization\n\n`pytest -q`: {tested.stdout.strip()}, including {test}.\n"
        outputs[evidence] = "# Private Last-Phase Evidence\n\n" + body
        changelog = root / "CHANGELOG.md"
        outputs["CHANGELOG.md"] = (changelog.read_text(encoding="utf-8") if changelog.exists() else "# Changelog\n") + f"\n## [{version.removeprefix('v')}] - 2026-11-07\n"
        for name in (evidence, "CHANGELOG.md"):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(outputs[name], encoding="utf-8")
        _git(root, "add", "--", *outputs)
        _git(root, "commit", "-q", "-m", "complete private native member fixture")
        if worker is not None:
            _git(self.work, "merge", "-q", "--no-ff", "-m", "merge private member fixture", member["source_branch"])
        head = _git(self.work, "rev-parse", "HEAD")
        _git(self.work, "tag", version)
        self.publish("main", version)
        self.state["releases"][version] = False
        self.state.setdefault("pr_by_branch", {})[member["source_branch"]] = {
            "state": "MERGED", "checks": GREEN, "merge_commit": head}
        self.save_state()
        self.integrate()
        if worker is not None:
            assert worker.resolve().is_relative_to(self.tmp.resolve())
            _git(self.work, "worktree", "remove", str(worker))
        return head


@pytest.fixture
def execution(tmp_path, monkeypatch):
    fixture = ExecutionMinor(tmp_path, monkeypatch)
    result = fixture.create()
    assert result.returncode == 0, result.stdout + result.stderr
    fixture.original = fixture.record()
    fixture.add_members()
    return fixture


def add_registration(root, version, mutate=None):
    value = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
    for event, groups in RECIPES[version]["hooks"].items():
        value["hooks"].setdefault(event, []).extend(copy.deepcopy(groups))
    if mutate is not None:
        mutate(value)
    (root / REGISTRY).write_text(json.dumps(value), encoding="utf-8")
    return value


def unchanged_original(fx):
    current = fx.record()
    assert current["members"] == fx.original["members"]
    for key in ("nonce", "created", "start_head"):
        assert current[key] == fx.original[key]
    assert current["approvals"] == fx.original["approvals"]


def execution_display_data(tmp_path, version):
    """Synthetic display data only; never passed to native permission consumption."""
    hook = version in RECIPES
    role = "coordinator" if version == "v4.15.8" else "implementation"
    root = tmp_path / "controller"
    branch = f"feat/{version}-display"
    paths = ([REGISTRY] if hook else WORKFLOW_PATHS[:2] + [".pre-commit-config.yaml"]
             if version == "v4.15.7" else WORKFLOW_PATHS)
    page = {
        "action": "permit-member-execution-paths", "scope": {"kind": "minor", "minor": TOKEN},
        "record_nonce": "private-display-fixture", "repo": "bendourthe/Nexus-Hub", "owner_session": SESSION,
        "record_sha256": "a" * 64, "controller": {"repo_root": str(root)}, "member": version,
        "plan_path": f"{PLAN_DIR}/{version}-display.md", "plan_sha256": "b" * 64,
        "source_branch": branch, "target_branch": "develop", "amendment_sha256": "c" * 64,
        "worker_identity": {"worktree": str(tmp_path / "worker"), "branch": branch, "base_head": "d" * 40},
        "implementation_sha256": "e" * 64 if role == "coordinator" else None,
        "start_head": None, "integration_head": "d" * 40,
        "push_remote_url": "https://github.com/bendourthe/Nexus-Hub.git", "sequence": 1,
        "previous_history_sha256": hashlib.sha256(b"[]").hexdigest(),
        "capability_kind": "hook-registration" if hook else "ci-execution", "role": role,
        "write_paths": sorted(paths), "hook_recipe": copy.deepcopy(RECIPES.get(version)),
        "git_common_dir": str(root / ".git"),
    }
    return {"action": page["action"], "scope": TOKEN, "code": "ABCDEFG2", "challenge": "private-display-only",
            "page": page, "paste": list(approval_display.paste_set(page["action"], TOKEN, "ABCDEFG2").lines),
            "display": {}}


@pytest.mark.parametrize("version", ["v4.15.5", "v4.15.6", "v4.15.7", "v4.15.8"])
def test_renderer_explains_real_capability_before_exact_reply(tmp_path, version):
    data = execution_display_data(tmp_path, version)
    rendered = approval_display.render_page(data)
    reply_at = rendered.index(data["paste"][0])
    explanation = rendered[:reply_at]
    if version == "v4.15.5":
        assert "nonblocking advisory notice" in explanation
        assert "repeats failing commands" in explanation
        assert "repeatedly changes one file" in explanation
    elif version == "v4.15.6":
        assert "configured location policy" in explanation
        assert "can block commands that violate it" in explanation
    else:
        assert "access tokens" in explanation
        if version == "v4.15.7":
            assert "commit" in explanation.lower()
    for path in data["page"]["write_paths"]:
        assert path in rendered


@pytest.mark.parametrize("change", ["missing-paths", "wrong-member", "wrong-role", "wrong-kind", "extra-field", "bad-hash", "bool-sequence", "wrong-recipe"])
def test_renderer_refuses_partial_or_mismatched_execution_data(tmp_path, change, capsys):
    data = execution_display_data(tmp_path, "v4.15.5")
    page = data["page"]
    if change == "missing-paths":
        page.pop("write_paths")
    elif change == "wrong-member":
        page["member"] = "v4.15.9"
    elif change == "wrong-role":
        page["role"] = "coordinator"
    elif change == "wrong-kind":
        page["capability_kind"] = "ci-execution"
    elif change == "extra-field":
        page["unexpected"] = True
    elif change == "bad-hash":
        page["plan_sha256"] = "unverified"
    elif change == "bool-sequence":
        page["sequence"] = True
    else:
        page["hook_recipe"] = RECIPES["v4.15.6"]
    assert approval_display.emit(data, "page") == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert "not rendered" in captured.err




@pytest.mark.parametrize("version", ["v4.15.5", "v4.15.6", "v4.15.7"])
def test_native_captured_grant_admits_only_the_exact_worker_scope(execution, version):
    fx = execution
    root = fx.worker(version)
    before = fx.record_path().read_bytes()
    denied = fx.admit(version, root)
    assert denied.returncode != 0
    assert fx.record_path().read_bytes() == before
    entry = fx.grant(version)
    assert entry["page"]["member"] == version
    assert entry["page"]["role"] == "implementation"
    assert entry["page"]["write_paths"] == sorted(fx.paths(version))
    assert entry["page"]["hook_recipe"] == RECIPES.get(version)
    assert entry["accepted"]["authorization_context"]["origin"] == "host-hook-capture"
    unchanged_original(fx)
    result = fx.admit(version, root)
    assert result.returncode == 0, result.stdout + result.stderr
    assert fx.member(version)["implementation"]["worktree"] == str(root.resolve())
    assert fx.member(version)["approvals"].get("autonomy_policy") is None
    assert fx.record()["minor_execution_permissions"] == [entry]


@pytest.mark.parametrize("version", ["v4.15.5", "v4.15.6"])
def test_exact_registration_is_valid_through_real_worker_projection(execution, version):
    root = execution.worker(version)
    execution.grant(version)
    assert execution.admit(version, root).returncode == 0
    add_registration(root, version)
    for stage in ("unstaged", "index", "commit"):
        if stage == "index":
            _git(root, "add", "--", REGISTRY)
        if stage == "commit":
            _git(root, "commit", "-q", "-m", "private exact registration")
        _, body = execution.project(version)
        assert body["predicates"]["implementation.identity"] == "met", stage


@pytest.mark.parametrize("stage", ["unstaged", "index", "commit"])
def test_registration_grant_never_authorizes_other_settings(execution, stage):
    version = "v4.15.5"
    root = execution.worker(version)
    execution.grant(version)
    assert execution.admit(version, root).returncode == 0
    before_text = (root / REGISTRY).read_text(encoding="utf-8")
    valid = add_registration(root, version)
    record, member = execution.record(), execution.member(version)
    assert cm.execution_registration_delta(ck, record, member, before_text, json.dumps(valid))
    for field in ("model", "effortLevel", "env", "attribution", "modelSettings", "extra"):
        invalid = copy.deepcopy(valid)
        invalid[field] = "unapproved"
        assert not cm.execution_registration_delta(ck, record, member, before_text, json.dumps(invalid)), field
    invalid = copy.deepcopy(valid)
    invalid["env"] = {"UNAPPROVED": "1"}
    (root / REGISTRY).write_text(json.dumps(invalid), encoding="utf-8")
    if stage in {"index", "commit"}:
        _git(root, "add", "--", REGISTRY)
    if stage == "commit":
        _git(root, "commit", "-q", "-m", "private forbidden settings change")
    if stage in {"index", "commit"}:
        # A valid working copy cannot hide an invalid staged or committed blob.
        (root / REGISTRY).write_text(json.dumps(valid), encoding="utf-8")
    if stage == "commit":
        _git(root, "add", "--", REGISTRY)
    _, body = execution.project(version)
    assert body["predicates"]["implementation.identity"] == "unmet"


def test_registry_structure_cannot_hide_unrelated_changes(execution):
    version = "v4.15.5"
    root = execution.worker(version)
    execution.grant(version)
    assert execution.admit(version, root).returncode == 0
    before_text = (root / REGISTRY).read_text(encoding="utf-8")
    valid = add_registration(root, version)
    record, member = execution.record(), execution.member(version)
    cases = ("remove-existing", "change-existing", "reorder", "wrong-command", "extra-group-field",
             "duplicate-key", "duplicate-nested-key", "malformed")
    for case in cases:
        value = copy.deepcopy(valid)
        if case == "remove-existing":
            value["hooks"]["PostToolUse"].pop(0)
        elif case == "change-existing":
            value["hooks"]["PostToolUse"][0]["matcher"] = "Write"
        elif case == "reorder":
            value["hooks"]["PostToolUse"][:2] = reversed(value["hooks"]["PostToolUse"][:2])
        elif case == "wrong-command":
            value["hooks"]["PostToolUse"][-1]["hooks"][0]["command"] += " --surprise"
        elif case == "extra-group-field":
            value["hooks"]["PostToolUse"][-1]["timeout"] = 99
        text = json.dumps(value)
        if case == "duplicate-key":
            text = text.replace('"model":', '"model": "hidden", "model":', 1)
        elif case == "duplicate-nested-key":
            text = text.replace('"matcher":', '"matcher": "hidden", "matcher":', 1)
        elif case == "malformed":
            text = text[:-1]
        assert not cm.execution_registration_delta(ck, record, member, before_text, text), case
        if case == "wrong-command":
            (root / REGISTRY).write_text(text, encoding="utf-8")
            _, body = execution.project(version)
            assert body["predicates"]["implementation.identity"] in {"unmet", "cannot-verify"}

    plain = {"model": "legacy-baseline"}
    complete = {**plain, "hooks": copy.deepcopy(RECIPES[version]["hooks"])}
    partial = {**plain, "hooks": {"PostToolUse": copy.deepcopy(RECIPES[version]["hooks"]["PostToolUse"])}}
    for baseline in (plain, {**plain, "hooks": {}}, partial):
        assert cm.execution_registration_delta(ck, record, member, json.dumps(baseline), json.dumps(complete))
    assert cm.execution_registration_delta(ck, record, member, json.dumps(complete), json.dumps(complete, indent=2))
    duplicate = copy.deepcopy(complete)
    duplicate["hooks"]["PostToolUse"].extend(copy.deepcopy(RECIPES[version]["hooks"]["PostToolUse"]))
    assert not cm.execution_registration_delta(ck, record, member, json.dumps(complete), json.dumps(duplicate))
    invalid_baselines = [
        ("malformed", "{", json.dumps(valid)), ("null-root", "null", json.dumps(valid)),
        ("array-root", "[]", json.dumps(valid)),
        ("duplicate-top", before_text.replace('"model":', '"model":"hidden","model":', 1), json.dumps(valid)),
        ("duplicate-nested", before_text.replace('"matcher":', '"matcher":"hidden","matcher":', 1), json.dumps(valid)),
    ]
    for label, hooks in (("null-hooks", None), ("array-hooks", []),
                         ("event-not-list", {"PostToolUse": {}}), ("group-not-object", {"PostToolUse": [None]})):
        invalid_baselines.append((label, json.dumps({**plain, "hooks": hooks}), json.dumps(complete)))
    for label, baseline, candidate in invalid_baselines:
        assert not cm.execution_registration_delta(ck, record, member, baseline, candidate), label
    opaque = copy.deepcopy(SETTINGS)
    opaque["hooks"]["PostToolUse"][0]["future_group_option"] = {"preserve": True}
    preserved = copy.deepcopy(opaque)
    for event, groups in RECIPES[version]["hooks"].items():
        preserved["hooks"].setdefault(event, []).extend(copy.deepcopy(groups))
    assert cm.execution_registration_delta(ck, record, member, json.dumps(opaque), json.dumps(preserved))
    preserved["hooks"]["PostToolUse"][0]["future_group_option"]["preserve"] = False
    assert not cm.execution_registration_delta(ck, record, member, json.dumps(opaque), json.dumps(preserved))

    # Audit actual unpublished merge resolutions. These are no release claims.
    (root / REGISTRY).write_text(json.dumps(valid), encoding="utf-8")
    _git(root, "add", "--", REGISTRY)
    _git(root, "commit", "-q", "-m", "private approved worker registration")
    inherited = copy.deepcopy(SETTINGS)
    inherited["model"] = "verified inherited integration model"
    (execution.work / REGISTRY).write_text(json.dumps(inherited), encoding="utf-8")
    execution.commit("private integration settings before merge audits")
    execution.integrate()
    integration = _git(execution.work, "rev-parse", "HEAD")
    expected = copy.deepcopy(inherited)
    for event, groups in RECIPES[version]["hooks"].items():
        expected["hooks"].setdefault(event, []).extend(copy.deepcopy(groups))
    for label, verdict in (("valid", "met"), ("invalid", "unmet")):
        _git(execution.work, "checkout", "-q", "-b", "private-" + label + "-merge-audit", integration)
        _git(execution.work, "merge", "-q", "--no-ff", "--no-commit", "-X", "ours", member["source_branch"])
        resolved = copy.deepcopy(expected)
        if verdict == "unmet":
            resolved["env"]["UNAPPROVED_RESOLUTION"] = "1"
        (execution.work / REGISTRY).write_text(json.dumps(resolved), encoding="utf-8")
        _git(execution.work, "add", "--", REGISTRY)
        _git(execution.work, "commit", "-q", "-m", "private " + label + " merge resolution")
        merged = _git(execution.work, "rev-parse", "HEAD")
        assert len(_git(execution.work, "rev-list", "--parents", "-n", "1", merged).split()) == 3
        before_record = execution.record_path().read_bytes()
        assert cm._historical_claim_status(execution.rctx(), member, merged, record, ck) == verdict
        assert execution.record_path().read_bytes() == before_record
        assert _git(root, "branch", "--show-current") == member["source_branch"]


INVALID_REQUESTS = [
    {"write_paths": []}, {"write_paths": [".github/"]},
    {"write_paths": [".github/workflows/other.yml"]},
    {"write_paths": [".github/workflows/../ci.yml"]},
    {"write_paths": [".GITHUB/workflows/ci.yml"]},
    {"write_paths": [".github/workflows/ci.yml", ".github/workflows/ci.yml"]},
    {"write_paths": [REGISTRY]}, {"write_paths": [".env"]},
    {"write_paths": [".github/workflows/ci.yml"], "role": "coordinator"},
    {"write_paths": [".github/workflows/ci.yml"], "hook_recipe": RECIPES["v4.15.5"]},
]


def test_invalid_execution_scope_refuses_without_native_mutation(execution):
    version = "v4.15.7"
    execution.worker(version)
    before = execution.record_path().read_bytes()
    for value in INVALID_REQUESTS:
        path = execution.request(version, value)
        result = execution.render(SESSION, "--action", "permit-member-execution-paths",
                                  "--member", version, "--execution", str(path))
        assert result.returncode != 0, value
        assert "Traceback" not in result.stderr
        assert execution.record_path().read_bytes() == before
    raw_values = ('null', '[]', '"paths"', '{"write_paths":true}', '{"write_paths":',
                  '{"write_paths":[".github/workflows/ci.yml"],"write_paths":[".github/workflows/post-merge.yml"]}')
    path = execution.tmp / "malformed-execution-request.json"
    for raw in raw_values:
        path.write_text(raw, encoding="utf-8")
        result = execution.render(SESSION, "--action", "permit-member-execution-paths",
                                  "--member", version, "--execution", str(path))
        assert result.returncode != 0, raw
        assert "Traceback" not in result.stderr
        assert execution.record_path().read_bytes() == before


def test_permission_cannot_legalize_retrospective_sensitive_writes(execution):
    version = "v4.15.7"
    root = execution.worker(version)
    path = root / WORKFLOW_PATHS[0]
    original = path.read_bytes()
    before = execution.record_path().read_bytes()
    for stage in ("unstaged", "index", "commit"):
        path.write_text("name: unapproved earlier write\n", encoding="utf-8")
        if stage in {"index", "commit"}:
            _git(root, "add", "--", WORKFLOW_PATHS[0])
        if stage == "commit":
            _git(root, "commit", "-q", "-m", "private retrospective CI edit")
        result = execution.render(SESSION, "--action", "permit-member-execution-paths",
                                  "--member", version, "--execution", str(execution.request(version)))
        assert result.returncode != 0, stage
        assert execution.record_path().read_bytes() == before
        if stage != "commit":
            path.write_bytes(original)
            _git(root, "add", "--", WORKFLOW_PATHS[0])


def test_native_capture_is_required_and_consumption_is_idempotent(execution):
    version = "v4.15.7"
    execution.worker(version)
    paths = sorted(execution.paths(version), reverse=True)
    assert paths != sorted(paths)
    path = execution.request(version, {"write_paths": paths})
    rendered = execution.render(SESSION, "--action", "permit-member-execution-paths",
                                "--member", version, "--execution", str(path))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    before = execution.record_path().read_bytes()
    args = ("record", "permit-member-execution-paths", "--minor", TOKEN, "--session", SESSION,
            "--member", version, "--execution", str(path))
    denied = execution.run(*args)
    assert denied.returncode != 0
    assert execution.record_path().read_bytes() == before
    execution.capture(SESSION, rendered.stdout.splitlines()[0])
    accepted = execution.run(*args)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    after = execution.record_path().read_bytes()
    repeat = execution.run(*args)
    assert execution.record_path().read_bytes() == after
    assert repeat.returncode == 0, repeat.stdout + repeat.stderr
    assert len(execution.record()["minor_execution_permissions"]) == 1
    for changed_paths in (paths[:1], paths + paths[:1], [paths[0], 1]):
        path.write_text(json.dumps({"write_paths": changed_paths}), encoding="utf-8")
        refused = execution.run(*args)
        assert refused.returncode != 0
        assert "Traceback" not in refused.stdout + refused.stderr
        assert execution.record_path().read_bytes() == after


def test_dormant_permission_is_recaptured_after_the_worker_moves(execution):
    """A moved worker re-binds a dormant grant by appending; paths never widen."""
    version = "v4.15.7"
    root = execution.worker(version)
    first = execution.grant(version)
    moved = root.parent / (root.name + "-moved")
    _git(execution.work, "worktree", "move", str(root), str(moved))
    second = execution.grant(version)
    history = execution.record()["minor_execution_permissions"]
    assert [entry["page"]["member"] for entry in history] == [version, version]
    assert second["page"]["write_paths"] == first["page"]["write_paths"]
    assert second["page"]["worker_identity"]["worktree"] == str(moved.resolve())
    assert second["page"]["sequence"] == 2
    after = execution.record_path().read_bytes()
    args = ("record", "permit-member-execution-paths", "--minor", TOKEN, "--session", SESSION,
            "--member", version, "--execution", str(execution.request(version)))
    repeat = execution.run(*args)
    assert repeat.returncode == 0, repeat.stdout + repeat.stderr
    assert "already captured" in repeat.stdout
    assert execution.record_path().read_bytes() == after
    widened = execution.request(version, {"write_paths": execution.paths(version)[:1]})
    refused = execution.run("record", "permit-member-execution-paths", "--minor", TOKEN, "--session", SESSION,
                            "--member", version, "--execution", str(widened))
    assert refused.returncode != 0
    assert "minor-execution-member-already-permitted" in refused.stdout + refused.stderr
    assert execution.record_path().read_bytes() == after
    assert execution.admit(version, moved).returncode == 0


def test_coordinator_grant_is_not_a_worker_permission_or_early_publication(execution):
    version = "v4.15.8"
    root = execution.worker(version)
    admitted = execution.admit(version, root, sensitive=False)
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    original_implementation = copy.deepcopy(execution.member(version)["implementation"])
    entry = execution.grant(version)
    assert entry["page"]["role"] == "coordinator"
    assert entry["page"]["capability_kind"] == "ci-execution"
    assert entry["page"]["write_paths"] == WORKFLOW_PATHS[:1]
    assert execution.member(version)["implementation"] == original_implementation
    assert "start_head" not in execution.member(version)
    before = execution.record_path().read_bytes()
    claim = execution.tmp / "coordinator-claims.json"
    claim.write_text(json.dumps({"write_paths": WORKFLOW_PATHS[:1]}), encoding="utf-8")
    premature = execution.run("record", "member-start", "--minor", TOKEN, "--session", SESSION,
                              "--member", version, "--head", _git(execution.work, "rev-parse", "origin/develop"),
                              "--coordinator-claims", str(claim))
    assert premature.returncode != 0
    assert execution.record_path().read_bytes() == before
    (root / WORKFLOW_PATHS[0]).write_text("name: premature worker CI\n", encoding="utf-8")
    _, body = execution.project(version)
    assert body["predicates"]["implementation.identity"] == "unmet"


@pytest.mark.parametrize("version", ["v4.15.5", "v4.15.6", "v4.15.7", "v4.15.8"])
def test_native_page_discloses_exact_capability_before_capture(execution, version):
    root = execution.worker(version)
    if version == "v4.15.8":
        assert execution.admit(version, root, sensitive=False).returncode == 0
    request = execution.request(version)
    before = execution.record_path().read_bytes()
    shown = execution.render(SESSION, "--action", "permit-member-execution-paths", "--member", version,
                             "--execution", str(request), "--page")
    assert shown.returncode == 0, shown.stdout + shown.stderr
    text = shown.stdout.lower()
    for required in (version, "approve", "doing nothing", "blocked", "permission", "secret", "unchanged"):
        assert required in text
    assert text.index("doing nothing") < text.index("## approval reply")
    for path in execution.paths(version):
        assert path in shown.stdout
    if version in RECIPES:
        for event, groups in RECIPES[version]["hooks"].items():
            assert event in shown.stdout
            for group in groups:
                assert group["matcher"] in shown.stdout
                assert group["hooks"][0]["command"] in shown.stdout
        assert "hook" in text and "event" in text
        raw = execution.render(SESSION, "--action", "permit-member-execution-paths", "--member", version,
                               "--execution", str(request))
        assert raw.returncode == 0, raw.stdout + raw.stderr
        reply = raw.stdout.splitlines()[0]
        before_reply = shown.stdout[:shown.stdout.index(reply)]
        if version == "v4.15.5":
            assert "nonblocking advisory notice" in before_reply
        else:
            assert "can block commands that violate it" in before_reply
    else:
        assert "workflow" in text and "token" in text
        # Granted CI files are limited by path only; the page must not promise content checks.
        assert "does not check what goes into them" in text
        assert "remain excluded" not in text
        if version == "v4.15.7":
            assert "commit" in text
    assert "recommend" in text
    assert execution.record_path().read_bytes() == before


@pytest.mark.parametrize("version", ["v4.15.5", "v4.15.7"])
def test_exact_execution_authorization_respects_current_host_mode(execution, version):
    root = execution.worker(version)
    execution.grant(version)
    assert execution.admit(version, root).returncode == 0
    for mode in ("bypassPermissions", None, "unknown", "default"):
        execution.permission_mode = "bypassPermissions"
        execution.capture(SESSION, "Restore full access for this private host-mode trial.")
        previous = copy.deepcopy(execution.record())
        execution.permission_mode = mode
        execution.capture(SESSION, "Continue the exact private fixture work.")
        result = execution.run("record", "authorize", "--minor", TOKEN, "--session", SESSION,
                               "--member", version, "--approval-class", "ci-security-change", "--request",
                               json.dumps({"paths": execution.paths(version)[:1]}))
        if mode == "bypassPermissions":
            assert result.returncode == 0, result.stdout + result.stderr
            assert "AUTHORIZED" in result.stdout
        else:
            assert result.returncode != 0, mode
        current = execution.record()
        assert current["minor_execution_permissions"] == previous["minor_execution_permissions"]
        assert current["members"] == previous["members"]
        for key in ("classes", "spend_caps", "autonomy_policy"):
            assert current["approvals"].get(key) == previous["approvals"].get(key)
        assert execution.member(version)["approvals"].get("autonomy_policy") is None


INVALID_AUTHORIZATION_REQUESTS = [
    {"paths": WORKFLOW_PATHS[:1] + [WORKFLOW_PATHS[2]]},
    {"paths": [REGISTRY]}, {"paths": [".github/workflows/"]},
    {"paths": WORKFLOW_PATHS[:1], "capability_kind": "hook-registration"},
]


def test_authorization_never_mixes_or_expands_captured_scope(execution):
    version = "v4.15.7"
    root = execution.worker(version)
    execution.grant(version)
    assert execution.admit(version, root).returncode == 0
    before = execution.record_path().read_bytes()
    for authorization_request in INVALID_AUTHORIZATION_REQUESTS:
        result = execution.run("record", "authorize", "--minor", TOKEN, "--session", SESSION,
                               "--member", version, "--approval-class", "ci-security-change", "--request", json.dumps(authorization_request))
        assert result.returncode != 0, authorization_request
        assert execution.record_path().read_bytes() == before


def test_dormant_permission_cannot_authorize_implementation_before_admission(execution):
    for version in ("v4.15.5", "v4.15.6", "v4.15.7"):
        execution.worker(version)
        execution.grant(version)
        before = execution.record_path().read_bytes()
        result = execution.run("record", "authorize", "--minor", TOKEN, "--session", SESSION,
                               "--member", version, "--approval-class", "ci-security-change", "--request",
                               json.dumps({"paths": execution.paths(version)[:1]}))
        assert result.returncode != 0, version
        assert execution.record_path().read_bytes() == before


def test_one_members_registration_cannot_admit_another_member(execution):
    first, second = "v4.15.5", "v4.15.6"
    execution.worker(first)
    second_root = execution.worker(second)
    execution.grant(first)
    before = execution.record_path().read_bytes()
    result = execution.admit(second, second_root)
    assert result.returncode != 0
    # The refusal must be the sensitive-path rule, not an unrelated gate refusing first.
    assert "sensitive-implementation-path" in result.stdout + result.stderr, result.stdout + result.stderr
    assert execution.record_path().read_bytes() == before


def test_overlapping_registration_reservations_remain_serialized(execution):
    first, second = "v4.15.5", "v4.15.6"
    first_root, second_root = execution.worker(first), execution.worker(second)
    execution.grant(first)
    execution.grant(second)
    assert execution.admit(first, first_root).returncode == 0
    before = execution.record_path().read_bytes()
    result = execution.admit(second, second_root)
    assert result.returncode != 0
    # The refusal must be the overlapping-claim rule, not an unrelated gate refusing first.
    assert "conflict" in (result.stdout + result.stderr).lower(), result.stdout + result.stderr
    assert execution.record_path().read_bytes() == before


def test_hidden_index_flags_cannot_hide_retrospective_or_active_changes(execution):
    version = "v4.15.7"
    root = execution.worker(version)
    path = root / WORKFLOW_PATHS[0]
    original = path.read_bytes()
    for flag in ("assume-unchanged", "skip-worktree"):
        before = execution.record_path().read_bytes()
        try:
            _git(root, "update-index", "--" + flag, "--", WORKFLOW_PATHS[0])
            path.write_text("name: hidden unapproved edit\n", encoding="utf-8")
            assert not _git(root, "status", "--porcelain")
            denied = execution.render(SESSION, "--action", "permit-member-execution-paths", "--member", version,
                                      "--execution", str(execution.request(version)))
            assert denied.returncode != 0, flag
            assert execution.record_path().read_bytes() == before
        finally:
            _git(root, "update-index", "--no-" + flag, "--", WORKFLOW_PATHS[0])
            path.write_bytes(original)
    execution.grant(version)
    assert execution.admit(version, root).returncode == 0
    for flag in ("assume-unchanged", "skip-worktree"):
        try:
            _git(root, "update-index", "--" + flag, "--", WORKFLOW_PATHS[0])
            path.write_text("name: hidden active edit\n", encoding="utf-8")
            assert not _git(root, "status", "--porcelain")
            _, body = execution.project(version)
            assert body["predicates"]["implementation.identity"] in {"unmet", "cannot-verify"}, flag
        finally:
            _git(root, "update-index", "--no-" + flag, "--", WORKFLOW_PATHS[0])
            path.write_bytes(original)






@pytest.mark.parametrize("fault", ["missing", "duplicate-section", "duplicate-key", "wrong-event", "wrong-command", "extra-group-field"])
def test_frozen_recipe_must_be_unambiguous_and_exact(tmp_path, monkeypatch, fault):
    execution = ExecutionMinor(tmp_path, monkeypatch)
    assert execution.create().returncode == 0
    version = "v4.15.5"
    heading = "### Native Execution Registration Recipe"

    def malformed(_version, text):
        before, recipe = text.split(heading, 1)
        if fault == "missing":
            return before + "### Unbound Recipe" + recipe
        if fault == "duplicate-section":
            return text + "\n" + text[text.index(heading):text.index("## Phase 1:")]
        if fault == "duplicate-key":
            recipe = recipe.replace('"hooks":', '"hooks": {}, "hooks":', 1)
        elif fault == "wrong-event":
            recipe = recipe.replace("PostToolUseFailure", "SessionStart")
        elif fault == "wrong-command":
            recipe = recipe.replace("stuck-turn-notice.sh", "unrelated-program.sh")
        else:
            recipe = recipe.replace('"matcher":', '"timeout": 999, "matcher":', 1)
        return before + heading + recipe

    # Bind these exact malformed bytes by a genuine fixture amendment first;
    # the refusal must come from recipe validation, not post-freeze hash drift.
    execution.add_members((version,), transform=malformed)
    execution.worker(version)
    before = execution.record_path().read_bytes()
    result = execution.render(SESSION, "--action", "permit-member-execution-paths", "--member", version,
                              "--execution", str(execution.request(version)))
    assert result.returncode != 0
    assert execution.record_path().read_bytes() == before


@pytest.fixture(scope="module")
def execution_baseline_scripts(tmp_path_factory):
    exists = subprocess.run(["git", "cat-file", "-e", f"{BASELINE}:scripts/check_plan_completion.py"],
                            cwd=REPO_ROOT, capture_output=True, check=False, timeout=30,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if exists.returncode:
        # A shallow CI checkout lacks this historical object; full-history runs prove it.
        pytest.skip(f"historical helper compatibility requires Git object {BASELINE}")
    archived = subprocess.run(["git", "archive", "--format=zip", BASELINE, "scripts"],
                              cwd=REPO_ROOT, capture_output=True, check=True, timeout=30,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    root = tmp_path_factory.mktemp("execution-old-bundle")
    with zipfile.ZipFile(io.BytesIO(archived.stdout)) as archive:
        archive.extractall(root)
    return root / "scripts"


EXECUTION_CONSUMER_PROBE = r'''
import json, sys
from pathlib import Path
import check_plan_completion as ck
import completion_minor as cm
import run_plan as runner
import completion_gate as gate
import cleanup_merged as cleanup
import minor_close as archive
path, session = Path(sys.argv[1]), sys.argv[2]
record = json.loads(path.read_text(encoding='utf-8'))
ctx, runner_record = runner._verified_runner_minor(path, record)
gate_root, gate_record = gate._verified_minor_root(path, record, session)
assert gate_root == ctx.root
args = cleanup.build_parser().parse_args(['--minor', 'v4.15', '--session', session])
receipt = cleanup._record_for_receipt(args, cleanup.Host(ctx.root, 'develop'))
assert isinstance(receipt, tuple), receipt
cleanup_path, cleanup_record, scope = receipt
assert cleanup_path == path and scope == 'minor:v4.15'
archive_record, archive_path = archive._record(ctx, 'v4.15', session)
assert archive_path == path
history = record['minor_execution_permissions']
for observed in (runner_record, gate_record, cleanup_record, archive_record):
    assert observed['minor_execution_permissions'] == history
    assert observed['session_id'] == session
    assert cm._verified(ck, ctx, 'v4.15', observed, minor_protocol=1, execution_protocol=1)
print(json.dumps({'readers': ['runner', 'gate', 'cleanup', 'archive'], 'history': history}))
'''

OLD_EXECUTION_CONSUMER_PROBE = r'''
import json, sys
from pathlib import Path
import check_plan_completion as ck
path, session, reader = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
record = json.loads(path.read_text(encoding='utf-8'))
if reader == 'run_plan.py':
    import run_plan as owner
    try:
        owner._verified_runner_minor(path, record)
    except owner.RunnerError as error:
        print('CONTROLLED REFUSAL runner:', error)
        sys.exit(3)
elif reader == 'completion_gate.py':
    import completion_gate as owner
    try:
        owner._verified_minor_root(path, record, session)
    except ValueError as error:
        print('CONTROLLED REFUSAL gate:', error)
        sys.exit(3)
elif reader == 'cleanup_merged.py':
    import cleanup_merged as owner
    result = owner.main(['--apply', '--receipt', '--minor', 'v4.15', '--session', session, '--repo', str(Path.cwd())])
    if result == owner.EXIT_USAGE:
        print('CONTROLLED REFUSAL cleanup')
        sys.exit(3)
elif reader == 'minor_close.py':
    import minor_close as owner
    result = owner.main(['archive', '--minor', 'v4.15', '--session', session, '--dry-run', '--repo', str(Path.cwd())])
    if result == owner.EXIT_REFUSED:
        print('CONTROLLED REFUSAL archive')
        sys.exit(3)
raise AssertionError('old consumer accepted execution-extended record: ' + reader)
'''


@pytest.fixture
def execution_discovery(tmp_path, monkeypatch):
    """A real Git boundary and disposable records, without an accepted verdict stub."""
    root = tmp_path / "discovery-repo"
    root.mkdir()
    _git(root, "init", "-q")
    store = tmp_path / "discovery-records"
    store.mkdir()
    monkeypatch.setenv("NEXUS_HUB_RUNS_DIR", str(store))
    paths = [store / ("owner-" + str(number) + ".json") for number in range(2)]
    for number, path in enumerate(paths):
        path.write_text(json.dumps({"schema": 1, "state": "completed", "value": number}), encoding="utf-8")
    return ck.RepoContext(root, ck.Budget(20)), paths


def _stub_ownership(monkeypatch, outcomes):
    """Drive _owned_member's typed path with a reader that drifts per `outcomes` entry."""
    from contextlib import contextmanager
    calls = []

    @contextmanager
    def reader(_ck, _rctx):
        calls.append(1)
        if outcomes[min(len(calls), len(outcomes)) - 1] == "drift":
            raise cm.ObservationUnavailable("record.provenance")
        yield [], (lambda path: None), "common"

    monkeypatch.setattr(cm, "_execution_ownership_reader", reader)
    monkeypatch.setattr(cm, "_sleep", lambda seconds: None)
    monkeypatch.setattr(cm, "effective_members", lambda _ck, _record: [])
    monkeypatch.setattr(cm, "_feat_heads", lambda _ck, _rctx: {})
    monkeypatch.setattr(cm, "_integration_ref", lambda _rctx, _target: None)
    monkeypatch.setattr(cm, "parse_minor", lambda _ck, _token: (4, 15))
    monkeypatch.setattr(cm, "scan_plans", lambda _root, _major, _minor: [])
    record = {"minor": "v4.15", "approvals": {}, "minor_execution_format": 1}
    return calls, record


def _repo(tmp_path):
    _git(tmp_path, "init", "-q")
    return ck.RepoContext(tmp_path, ck.Budget(5))


def test_typed_ownership_retries_a_changed_record_snapshot(monkeypatch, tmp_path):
    calls, record = _stub_ownership(monkeypatch, ["drift", "stable"])
    assert cm._owned_member(ck, _repo(tmp_path), record, tmp_path / "own.json") is None
    assert len(calls) == 2


def test_typed_ownership_still_fails_closed_on_persistent_drift(monkeypatch, tmp_path):
    calls, record = _stub_ownership(monkeypatch, ["drift"])
    with pytest.raises(cm.ObservationUnavailable):
        cm._owned_member(ck, _repo(tmp_path), record, tmp_path / "own.json")
    assert len(calls) == len(cm._OWNERSHIP_RETRY_DELAYS) + 1


@pytest.mark.parametrize("revision", ["HEAD", "INDEX"])
def test_registration_read_timeout_is_cannot_verify_not_unmet(tmp_path, revision):
    class TimedOut:
        root, git = tmp_path, "git"

        def run(self, _argv):
            return -1, ""

    with pytest.raises(cm.ObservationUnavailable):
        cm._execution_registration_text(TimedOut(), revision)


def test_removed_execution_history_reports_its_own_reason(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_HUB_RUNS_DIR", str(tmp_path))
    path = tmp_path / "plan-record.json"
    path.write_text(json.dumps({"schema": 1, "minor_execution_format": 1, "minor_execution_permissions": []}), encoding="utf-8")
    with pytest.raises(ck.MinorConflict, match="minor-execution-history-removed"):
        ck._write_record(path, {"schema": 1})


@pytest.mark.parametrize("has_minor_module", [True, False], ids=["post-v4.13.6", "pre-v4.13.6"])
def test_stop_gate_refuses_an_older_checker_sibling_instead_of_failing_open(tmp_path, monkeypatch, has_minor_module):
    import completion_gate as gate
    old = tmp_path / "installed" / "check_plan_completion.py"
    old.parent.mkdir()
    minor = ("class _Minor:\n    class ObservationUnavailable(Exception):\n        pass\n\n"
             "def _minor_module():\n    return _Minor\n\n") if has_minor_module else ""
    old.write_text(
        "class Malformed(Exception):\n    pass\n\n" + minor +
        "def resolve_minor_controller(path, session, *, budget_seconds, minor_protocol):\n"
        "    raise AssertionError('an older checker never reaches here')\n",
        encoding="utf-8")
    monkeypatch.setattr(gate, "_checker", lambda: old)
    with pytest.raises(ValueError, match="cannot be verified"):
        gate._verified_minor_root(tmp_path / "record.json", {"repo_root": str(tmp_path / "work")}, SESSION)
