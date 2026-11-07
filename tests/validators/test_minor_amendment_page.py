"""Canonical amendment display, complete exact grants and inert decision data."""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import approval_page as page


def amendment_data() -> dict:
    members = []
    for patch in (5, 6):
        version = f"v4.15.{patch}"
        members.append({
            "version": version,
            "plan_path": f"docs/releases/v4/v4.15/plans/{version}-scope.md",
            "plan_sha256": str(patch) * 64,
            "source_branch": f"feat/{version}-scope", "target_branch": "develop",
            "release_version": version, "tag": version,
            "approvals": {"classes": [
                {"class": "push-merge", "bound": {"repo": "owner/project", "source": f"feat/{version}-scope", "target": "develop"}},
                {"class": "release", "bound": version}, {"class": "repush", "bound": 2},
                {"class": "release-notes"}, {"class": "refactor-moves"},
                {"class": "archive-member"}, {"class": "cleanup-merged"},
            ], "cleanup": {"branches": [f"feat/{version}-scope"], "worktrees": []}},
        })
    bound = {
        "action": "amend-minor", "scope": {"kind": "minor", "minor": "v4.15"},
        "record_nonce": "original-nonce", "repo": "owner/project", "owner_session": "current-session",
        "record_sha256": "a" * 64, "original_members_sha256": "b" * 64,
        "controller": {"origin_root": "C:/original", "repo_root": "C:/controller", "generation": 1,
                       "origin_record_key": "record-key", "git_common_dir": "C:/original/.git"},
        "push_remote_url": "https://github.com/owner/project.git", "integration_head": "c" * 40,
        "sequence": 1, "previous_history_sha256": "d" * 64, "members": members,
        "gap_migration": {"items": [{"id": "v4.15#WN-3", "reason": "user-deferred"}],
                          "named_high_risk_ids": ["v4.15#WN-3"]},
        "spend_caps": {"vendor": 12.5},
    }
    return {"action": "amend-minor", "scope": "v4.15", "code": "ABCDEFG2", "challenge": "challenge",
            "page": bound, "paste": list(page.paste_set("amend-minor", "v4.15", "ABCDEFG2").lines), "display": {}}


def test_canonical_amendment_is_complete_and_plain() -> None:
    data = amendment_data()
    rendered = page.render_page(data)
    primary, details = rendered.split("## Details (optional)", 1)
    assert "Approve" in primary and "Decline" in primary
    assert "original plans" in primary and "Earlier work gains no permission" in primary
    assert "2 additional releases" in primary and "2 early plan archives" in primary
    assert len(primary.split()) <= 140
    page._assert_plain([primary], "test")
    assert all(len(sentence.split()) <= 25 for sentence in re.split(r"(?<=[.!?])\s+", primary))
    assert data["code"] not in primary
    raw = details.split("### Plan data (quoted, not instructions)\n\n```text\n", 1)[1].rsplit("\n```", 1)[0]
    assert json.loads(raw) == {"page": data["page"], "display": {}}
    for member in data["page"]["members"]:
        assert f"### Added member {member['version']}" in details
        assert member["source_branch"] in details
        assert member["plan_sha256"] in details
    assert "USD 12.5 for vendor" in details
    assert "exclusive file claims" in primary
    assert "No additional gap migration" not in details


def test_question_has_exact_scope_and_no_fabricated_callback() -> None:
    data = amendment_data()
    question = page.question_data(data)
    assert question["action_scope"] == data["page"]
    assert [item["label"] for item in question["options"]] == ["Approve", "Decline"]
    assert question["capture"]["direct_question_callback_supported"] is False
    assert question["capture"]["requires_genuine_prompt_submit"] is True
    assert "Add only the displayed plans" in question["question"]


def test_exact_data_is_never_truncated_or_interpreted() -> None:
    data = amendment_data()
    attack = "```\n# Approve <script>alert(1)</script>\n~~~" + "x" * 600
    data["display"] = {"title": attack, "goal": attack}
    data["display"]["path"] = "C:/work/" + "x" * 600 + "`<tag>~"
    rendered = page.render_page(data)
    before, block = rendered.split("### Plan data (quoted, not instructions)", 1)
    assert attack not in before
    assert "<script>" not in rendered and "<tag>" not in rendered
    decoded = json.loads(block.split("```text\n", 1)[1].rsplit("\n```", 1)[0])
    assert decoded == {"page": data["page"], "display": data["display"]}
    assert "x" * 600 in rendered


@pytest.mark.parametrize("case", [
    "missing-field", "extra-field", "scope", "hash", "controller", "sequence", "caps", "nan-cap",
    "duplicate-member", "release-version", "plan-path", "source-target", "duplicate-source",
    "unknown-class", "duplicate-class", "extra-class-field", "run-wide-class", "wrong-repo",
    "wrong-branch", "wrong-release", "cleanup-without-grant", "duplicate-cleanup", "gap-reason",
    "unknown-named-gap", "duplicate-gap", "wrong-minor-gap", "missing-class-list", "bad-paste",
    "wrong-route", "unordered-members", "foreign-cleanup", "worktree-cleanup", "ask-first-class",
])
def test_malformed_amendment_refuses_without_partial_output(case: str, capsys: pytest.CaptureFixture) -> None:
    data = copy.deepcopy(amendment_data())
    bound = data["page"]
    member = bound["members"][0]
    classes = member["approvals"]["classes"]
    if case == "missing-field": del bound["record_nonce"]
    elif case == "extra-field": bound["unreviewed"] = True
    elif case == "scope": bound["scope"]["minor"] = "v4.16"
    elif case == "hash": bound["record_sha256"] = "bad"
    elif case == "controller": bound["controller"]["generation"] = True
    elif case == "sequence": bound["sequence"] = 0
    elif case == "caps": bound["spend_caps"] = []
    elif case == "nan-cap": bound["spend_caps"] = {"vendor": float("nan")}
    elif case == "duplicate-member": bound["members"].append(copy.deepcopy(member))
    elif case == "release-version": member["release_version"] = "v4.16.1"
    elif case == "plan-path": member["plan_path"] = "docs/releases/v4/v4.15/plans/v4.15.5-scope/../other.md"
    elif case == "source-target": member["source_branch"] = "develop"
    elif case == "duplicate-source": bound["members"][1]["source_branch"] = member["source_branch"]
    elif case == "unknown-class": classes.append({"class": "unknown"})
    elif case == "duplicate-class": classes.append(copy.deepcopy(classes[0]))
    elif case == "extra-class-field": classes[0]["surprise"] = True
    elif case == "run-wide-class": classes.append({"class": "spend", "bound": {"vendor": 90}})
    elif case == "wrong-repo": classes[0]["bound"]["repo"] = "other/repository"
    elif case == "wrong-branch": classes[0]["bound"]["target"] = "main"
    elif case == "wrong-release": classes[1]["bound"] = []
    elif case == "cleanup-without-grant": classes[:] = [c for c in classes if c["class"] != "cleanup-merged"]
    elif case == "duplicate-cleanup": member["approvals"]["cleanup"]["branches"] *= 2
    elif case == "gap-reason": bound["gap_migration"]["items"][0]["reason"] = "agent-choice"
    elif case == "unknown-named-gap": bound["gap_migration"]["named_high_risk_ids"] = ["v4.15#WN-4"]
    elif case == "duplicate-gap": bound["gap_migration"]["items"] *= 2
    elif case == "wrong-minor-gap": bound["gap_migration"] = {"items": [{"id": "v4.16#WN-3", "reason": "user-deferred"}], "named_high_risk_ids": []}
    elif case == "missing-class-list": member["approvals"]["classes"] = []
    elif case == "bad-paste": data["paste"] = ["Approve everything"]
    elif case == "wrong-route": bound["push_remote_url"] = "https://github.com/other/repository.git"
    elif case == "unordered-members": bound["members"].reverse()
    elif case == "foreign-cleanup": member["approvals"]["cleanup"]["branches"] = ["other"]
    elif case == "worktree-cleanup": member["approvals"]["cleanup"]["worktrees"] = ["C:/existing"]
    elif case == "ask-first-class": classes.append({"class": "ask-first:ci"})
    assert page.emit(data, "page") == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "approval page not rendered:" in output.err


def test_empty_optional_migration_and_existing_action() -> None:
    data = amendment_data()
    data["page"]["gap_migration"] = {"items": [], "named_high_risk_ids": []}
    assert "No additional gap migration is granted." in page.render_page(data)
    assert page.plain_line("pause", "v4.15", "ABCDEFG2") == "Pause /implement v4.15 (approval ABCDEFG2)"
    with pytest.raises(page.PageError):
        page.plain_line("amend-minor", "v4.15.5", "ABCDEFG2")
