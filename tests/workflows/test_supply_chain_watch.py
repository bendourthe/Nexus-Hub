"""v4.7.0 Phase 6: the scheduled supply-chain watch and the attested release artifact.

- The watch triggers on `schedule` and `workflow_dispatch` only and produces NO required
  status check (a schedule-triggered required check would sit Pending forever on a PR).
- The release workflow's artifact job scopes `id-token: write` and `attestations: write` to
  itself, pins the attestation action by SHA, and adds no secret beyond the repository token.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.ci import profiles as audit_profiles

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WATCH = REPO_ROOT / ".github" / "workflows" / "supply-chain-watch.yml"
RELEASE = REPO_ROOT / ".github" / "workflows" / "release.yml"
MANIFEST = REPO_ROOT / "docs" / "policy" / "required-checks.json"
ON_KEY = True


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_watch_is_event_scoped_to_schedule_and_dispatch() -> None:
    triggers = _load(WATCH)[ON_KEY]
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert triggers["schedule"] and "cron" in triggers["schedule"][0]


def test_watch_produces_no_required_check() -> None:
    contexts = {
        c
        for b in json.loads(MANIFEST.read_text(encoding="utf-8"))["branches"].values()
        for c in b["contexts"]
    }
    jobs = set(_load(WATCH)["jobs"])
    assert not (jobs & {c.split(" (", 1)[0] for c in contexts}), (
        "the watch must never enter the required set"
    )


def test_watch_fails_visibly_rather_than_passing_on_no_data() -> None:
    text = WATCH.read_text(encoding="utf-8")
    assert "--only pip-audit --reports-dir reports" in text and "audit_upload_path" in text
    assert "if-no-files-found: warn" in text


def test_watch_installs_patched_setuptools_before_audit() -> None:
    steps = _load(WATCH)["jobs"]["audit"]["steps"]
    install = next(
        step["run"]
        for step in steps
        if step.get("name") == "Install the declared dependency set"
    )
    pin = re.search(
        r"(?m)^\s*python -m pip install --quiet --upgrade pip pip-audit 'setuptools==(\d+\.\d+\.\d+)'$",
        install,
    )
    assert pin is not None
    assert tuple(map(int, pin.group(1).split("."))) >= (83, 0, 0)


def test_watch_skips_editable_projects_without_dropping_installed_dependencies() -> None:
    steps = _load(WATCH)["jobs"]["audit"]["steps"]
    install = next(step["run"] for step in steps if step.get("name") == "Install the declared dependency set")
    audit = next(step["run"] for step in steps if step.get("name") == "Audit against known advisories")
    assert 'for ext in extensions/*/pyproject.toml' in install
    assert 'python -m pip install --quiet -e "${dir}[${extras}]"' in install
    assert audit.strip() == "python -B scripts/ci/run.py --profile full --only pip-audit --reports-dir reports"
    scenario = (REPO_ROOT / "scripts/ci/verify_scenarios.py").read_text(encoding="utf-8")
    assert '"--skip-editable", "--progress-spinner", "off", "--format", "json", "--output"' in scenario
    assert '"--ignore-vuln"' not in scenario


def test_release_artifact_job_is_scoped_and_pinned() -> None:
    data = _load(RELEASE)
    job = data["jobs"]["publish-artifact"]
    assert job["permissions"] == {
        "contents": "write",
        "id-token": "write",
        "attestations": "write",
    }
    assert data["permissions"] == {"contents": "read"}, (
        "workflow-level default stays least privilege"
    )
    uses = [step["uses"] for step in job["steps"] if "uses" in step]
    for ref in uses:
        assert re.search(r"@[0-9a-f]{40}$", ref), f"unpinned action: {ref}"
    assert any(u.startswith("actions/attest-build-provenance@") for u in uses)
    text = RELEASE.read_text(encoding="utf-8")
    secrets = set(re.findall(r"secrets\.([A-Za-z_]+)", text))
    assert secrets <= {"GITHUB_TOKEN"}, f"new secret referenced: {secrets}"
    assert "--clobber" in text and "SHA256SUMS" in text


# v4.13.11 Phase 6 (WN-39): PyJWT <= 2.14.0 lets a deeply nested payload raise
# RecursionError before signature checks (GHSA-42vr-xj54-vc7v; also
# GHSA-x33g-cr3x-6449). Fixed in 2.15.0.
PYJWT_FLOOR = (2, 15, 0)
CONSTRAINTS = REPO_ROOT / "scripts" / "ci" / "requirements-py311.txt"


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", text)[:3])


def test_ci_constraints_pin_a_fixed_pyjwt() -> None:
    pins = re.findall(r"^pyjwt==([\d.]+)", CONSTRAINTS.read_text(encoding="utf-8"), re.M)
    assert len(pins) == 1, pins
    assert _version(pins[0]) >= PYJWT_FLOOR, f"pyjwt=={pins[0]} is affected by GHSA-42vr-xj54-vc7v"


def test_every_extension_that_pulls_mcp_declares_the_pyjwt_floor() -> None:
    """The CI pin protects only CI; a user's environment already holding 2.14.0
    satisfies mcp's own `pyjwt>=2.10.1` and would not upgrade without this floor."""
    tomllib = pytest.importorskip("tomllib")
    checked = 0
    for pyproject in sorted((REPO_ROOT / "extensions").glob("*/pyproject.toml")):
        project = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]
        groups = [project.get("dependencies", [])] + list(project.get("optional-dependencies", {}).values())
        for group in groups:
            if not any(re.match(r"mcp\b", dep) for dep in group):
                continue
            checked += 1
            floors = [dep for dep in group if re.match(r"pyjwt\s*>=", dep, re.I)]
            assert floors, f"{pyproject.parent.name}: a group with mcp lacks a pyjwt floor"
            assert _version(floors[0].split(">=", 1)[1]) >= PYJWT_FLOOR, floors[0]
    assert checked >= 4, "expected the four MCP-serving extensions to be checked"



def _audit_workflow(name):
    return _load(REPO_ROOT / ".github/workflows" / name)


def test_audit_events_names_permissions_and_matrices_are_preserved():
    npm, pip, codeql = _audit_workflow("npm-audit.yml"), _audit_workflow("supply-chain-watch.yml"), _audit_workflow("codeql.yml")
    for workflow in (npm, pip):
        trigger = workflow.get("on", workflow.get(True))
        assert set(trigger) == {"schedule", "workflow_dispatch"}
        assert workflow["permissions"] == {"contents": "read"}
    assert npm["name"] == "npm-audit" and pip["name"] == "Supply-chain watch" and codeql["name"] == "CodeQL Security Scan"
    assert npm.get("on", npm.get(True))["schedule"] == [{"cron": "17 6 * * 1"}]
    assert pip.get("on", pip.get(True))["schedule"] == [{"cron": "0 6 * * 1"}]
    trigger = codeql.get("on", codeql.get(True))
    assert set(trigger) == {"pull_request", "schedule", "workflow_dispatch"}
    assert trigger["pull_request"] == {"branches": ["main", "develop"], "paths": ["scripts/**/*.py", "infrastructure/**/*.py", "extensions/**/*.ts", "extensions/**/*.js"]}
    assert trigger["schedule"] == [{"cron": "0 0 * * 0"}]
    assert npm["jobs"]["audit"]["strategy"]["matrix"]["extension"] == list(audit_profiles.AUDIT_NPM_PACKAGES)
    assert codeql["jobs"]["analyze"]["strategy"]["matrix"]["language"] == list(audit_profiles.AUDIT_CODEQL_LANGUAGES)
    assert codeql["jobs"]["analyze"]["name"] == "Analyze (${{ matrix.language }})"
    assert codeql["jobs"]["analyze"]["permissions"] == {"security-events": "write"}
    assert [npm["jobs"]["audit"]["timeout-minutes"], pip["jobs"]["audit"]["timeout-minutes"], codeql["jobs"]["analyze"]["timeout-minutes"]] == [15, 20, 60]
    assert npm["concurrency"] == {"group": "${{ github.workflow }}", "cancel-in-progress": True}
    assert pip["concurrency"] == {"group": "${{ github.workflow }}-${{ github.ref }}", "cancel-in-progress": False}
    assert codeql["concurrency"] == {"group": "${{ github.workflow }}-${{ github.ref }}", "cancel-in-progress": True}


def test_native_groups_replace_validation_without_changing_preparation():
    npm = _audit_workflow("npm-audit.yml")["jobs"]["audit"]
    steps = npm["steps"]
    setup = next(s for s in steps if "setup-node@" in s.get("uses", ""))
    assert setup["with"] == {"node-version": "22", "cache": "npm", "cache-dependency-path": "extensions/${{ matrix.extension }}/package-lock.json"}
    assert any(s.get("run") == "npm ci --ignore-scripts" for s in steps)
    native = next(s for s in steps if "--only npm-audit-" in s.get("run", ""))
    assert native["working-directory"] == "."
    assert native["run"] == "python -B scripts/ci/run.py --profile full --only npm-audit-${{ matrix.extension }} --reports-dir reports"
    assert not any(s.get("run") == "npm audit signatures" for s in steps)
    pip = _audit_workflow("supply-chain-watch.yml")["jobs"]["audit"]
    install = next(s["run"] for s in pip["steps"] if s.get("name") == "Install the declared dependency set")
    assert "'setuptools==84.0.0'" in install and "for ext in extensions/*/pyproject.toml" in install
    assert _audit_workflow("supply-chain-watch.yml")["env"]["PIP_CONSTRAINT"] == "${{ github.workspace }}/scripts/ci/requirements-py311.txt"
    raw = next(s for s in pip["steps"] if s.get("with", {}).get("name") == "pip-audit-report")
    assert raw["with"]["retention-days"] == 30
    assert raw["with"]["path"] == "${{ steps.audit_report.outputs.path }}"


def test_codeql_setup_analysis_upload_and_hosted_observations_are_separate():
    steps = _audit_workflow("codeql.yml")["jobs"]["analyze"]["steps"]
    refs = [s["uses"] for s in steps if "uses" in s]
    assert not any("codeql-action/" + name + "@" in ref for name in ("init", "analyze", "autobuild") for ref in refs)
    for name in ("setup-codeql", "upload-sarif"):
        assert "github/codeql-action/" + name + "@24c54180a607b1449ed407dd24f251e4e9147c8d" in refs
    native = next(s for s in steps if s.get("name") == "Perform native CodeQL Analysis")
    assert native["env"] == {"NEXUS_CI_CODEQL": "${{ steps.codeql.outputs.codeql-path }}"}
    upload = next(s for s in steps if s.get("id") == "upload")
    assert upload["with"] == {"sarif_file": "${{ steps.audit_report.outputs.path }}", "category": "/language:${{ matrix.language }}", "wait-for-processing": True}
    text = (REPO_ROOT / ".github/workflows/codeql.yml").read_text()
    assert "audit_upload_path" in text and "manifest_sha256" in text and "Source changed before upload" in text
    assert "ci-codeql-hosted/1" in text and "steps.upload.outputs.sarif-id" in text
    assert "GITHUB_RUN_ID" in text and "GITHUB_RUN_ATTEMPT" in text and "JOB_DISPLAY_NAME" in text
    config = yaml.safe_load((REPO_ROOT / "scripts/ci/codeql-config.yml").read_text())
    assert config == {"queries": [{"uses": "security-and-quality"}], "paths-ignore": [".agents/**", ".cursor/commands/**"]}


def test_reports_are_unconditional_pinned_and_do_not_enter_required_gate():
    for name, job in (("npm-audit.yml", "audit"), ("supply-chain-watch.yml", "audit"), ("codeql.yml", "analyze")):
        data = _audit_workflow(name)
        steps = data["jobs"][job]["steps"]
        summary = next(s for s in steps if s.get("name") == "Publish native profile summary")
        assert summary["if"] == "always()"
        uploads = [s for s in steps if s.get("with", {}).get("name", "").startswith("reports-")]
        assert len(uploads) == 1 and uploads[0]["if"] == "always()"
        assert uploads[0]["with"]["retention-days"] == 7
        for step in steps:
            if "uses" in step:
                assert re.search(r"@[a-f0-9]{40}$", step["uses"])
        assert "ci-required" not in data["jobs"]
