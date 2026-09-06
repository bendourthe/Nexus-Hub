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
    assert "pip_audit" in text and 'exit "$status"' in text
    assert "if-no-files-found: warn" in text


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
