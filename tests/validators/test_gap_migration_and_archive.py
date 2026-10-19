"""Gap migration, the bounded minor gap scope, and the closed-minor archive.

Covers v4.13.6 Phase 4 (T029-T034):

- `minor_close.py migrate`: a listed gap to a new and to an existing target, a
  double migration, a re-run that never duplicates an entry, and the refusals
  (unlisted id, security item not named, gap created during the run, concurrent edit);
- `gaps.minor` in `completion_minor.py`: the scope stops at the run's minor, a
  migrated copy never reopens it, a hand-written marker pair is not accepted, and a
  ledger another run owns or an unmerged branch changes is excluded and reported;
- `gaps.version` of a minor member accepts only a verified migration;
- `minor_close.py archive`: every reference class repaired with zero newly broken
  links, each refusal condition, a failed link check and a locked directory leaving
  the tree unmoved, the record re-frozen, `archive.minor`, and `members` still
  resolving the archived plans.

Every repository is a throwaway with a local bare remote and the committed `gh`
stand-in; no case touches the network.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from .test_check_plan_completion import (  # noqa: F401  (autouse fixture re-exported)
    _git,
    _isolated_git_config,
)
from .test_completion_minor_record import (  # noqa: F401  (autouse fixture re-exported)
    SESSION,
    Minor,
    _no_transport_overrides,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
CLOSE = SCRIPTS / "minor_close.py"
sys.path.insert(0, str(SCRIPTS))
import check_plan_completion as ck
import completion_minor as cm
import minor_close as mc

V05 = "docs/releases/v0/v0.5"
V06 = "docs/releases/v0/v0.6"
GAPS05 = f"{V05}/known-gaps.md"
GAPS06 = f"{V06}/known-gaps.md"
LINK_CHECKER = REPO_ROOT / "catalog" / "skills" / "code-cleanup" / "docs-layout-refactor" / "scripts" / "link-baseline.py"


def ledger(minor: str, sections: str, status: str = "in-progress", open_items: int | None = None) -> str:
    extra = f"**Open items**: {open_items}\n" if open_items is not None else ""
    return (
        f"# Known Gaps - {minor}\n\n**Project**: demo\n**Status**: {status}\n"
        f"**Last updated**: 2026-09-01\n{extra}\n{sections}"
    )


def section(version: str, wn_open: int, items: str, bg_open: int = 0) -> str:
    return (
        f"## {version}\n\n### Summary\n\n| Category | Open | Resolved |\n|---|---|---|\n"
        f"| Bugs / regressions (BG) | {bg_open} | 0 |\n| Warnings (WN) | {wn_open} | 0 |\n\n"
        f"### Open Items\n\n{items}### Resolved\n\n| ID | Title | Resolved in | Notes |\n|---|---|---|---|\n"
    )


WN3 = (
    "#### WN-3: The probe flakes on a cold cache\n\n"
    "- **Source phase**: Phase 2\n- **Plan reference**: [plan](plans/v0.5.2-alpha.md)\n"
    "- **Reason**: vendor API missing\n- **Suggested next step**: wait for the vendor\n\n"
)
BG2 = (
    "#### BG-2: Security token is logged at debug level\n\n"
    "- **Source phase**: Phase 1\n- **Reason**: needs the vendor's redaction hook\n\n"
)


class Close(Minor):
    """The Phase 2 two-plan v0.5 fixture plus known-gaps ledgers and forged records."""

    def write(self, rel: str, text: str) -> None:
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def read(self, rel: str) -> str:
        return (self.work / rel).read_text(encoding="utf-8")

    def head(self) -> str:
        return _git(self.work, "rev-parse", "HEAD").strip()

    def forge(self, token: str = "v0.5", bound: tuple[str, ...] = ("v0.5#WN-3",), named: tuple[str, ...] = (),
              archive: bool = True, start_head: str | None = None) -> dict:
        """A signed schema-2 record for `token`, as `record create` would write it."""
        rctx = self.rctx()
        major, minor = cm.parse_minor(ck, token)
        members = [
            {
                "version": p.version, "plan_path": p.rel, "plan_sha256": ck.plan_hash_text(p.text),
                "source_branch": f"feat/{p.version}-{p.slug}", "target_branch": "develop",
                "release_version": p.version, "tag": p.version,
                "approvals": {"classes": [{"class": "push-merge"}], "cleanup": {"branches": [], "worktrees": []}},
            }
            for p in cm.scan_plans(rctx.root, major, minor)
        ]
        classes = [{"class": "gap-migration", "bound": list(bound), "named": list(named)}]
        if archive:
            classes.append({"class": "archive-minor"})
        record = {
            "schema": ck.SCHEMA_MINOR, "scope": "minor", "minor": token, "repo_root": str(rctx.root),
            "remote_url": rctx.remote_url, "repo": "acme/demo", "session_id": SESSION,
            "worktree": str(rctx.root), "start_head": start_head or self.head(), "nonce": "nonce-" + token,
            "created": ck._now(), "members": members, "excluded": [],
            "approvals": {
                "remote_url": rctx.remote_url, "push_remote_url": rctx.push_remote_url, "repo": "acme/demo",
                "target_branch": "develop", "classes": classes, "spend_caps": {}, "page_sha256": "0" * 64,
            },
            "blockers": [], "pause": None, "completed": None,
        }
        record["approvals_hmac"] = ck._sign(record, ck._secret(create=True) or b"")
        path = rctx.scoped_record_path("minor:" + token)
        with ck.minor_creation_lease(rctx, token):
            raw = path.read_bytes() if path.exists() else None
            expected = hashlib.sha256(raw).hexdigest() if raw is not None else None
            with ck.minor_lease(path, expected, rctx):
                ck._write_record(path, record)
        return record

    def close(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(CLOSE), *args, "--repo", str(self.work)],
            cwd=self.work, env=self.env, capture_output=True, text=True, check=False,
        )

    def migrate(self, gap: str = "v0.5#WN-3", token: str = "v0.5", *extra: str) -> subprocess.CompletedProcess:
        return self.close("migrate", "--minor", token, "--id", gap, "--reason", "vendor-feature",
                          "--evidence", "the vendor has not shipped the API", "--date", "2026-09-29", *extra)

    def gaps_minor(self, token: str = "v0.5") -> tuple[str, list[str]]:
        rctx = self.rctx()
        return cm.gaps_minor_status(ck, rctx, token, cm.load_minor(ck, rctx, token, None).record)

    def standard(self, items: str = WN3, wn_open: int = 1, bg_open: int = 0) -> None:
        self.write(GAPS05, ledger("v0.5", section("v0.5.2", wn_open, items, bg_open)))
        self.commit("ledgers")
        self.integrate()

    def integrate(self) -> None:
        """Fast-forward develop to main and publish both, as a merged release would."""
        _git(self.work, "branch", "-f", "develop", "main")
        self.publish("main", "develop")


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Close:
    return Close(tmp_path, monkeypatch)


# --------------------------------------------------------------------------- migrate


def test_migrate_creates_target_from_template_with_provenance(repo: Close) -> None:
    repo.standard()
    repo.forge()
    result = repo.migrate()
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == f"MIGRATED v0.5#WN-3 -> v0.6#WN-1 (v0.6.0) {GAPS06}"
    target = repo.read(GAPS06)
    assert "**Status**: in-progress" in target and "## v0.6.0" in target
    assert "#### WN-1: The probe flakes on a cold cache" in target
    assert "- **Migrated from**: v0.5#WN-3 on 2026-09-29 (reason: vendor-feature)" in target
    # The copied body's relative link is re-expressed from the target's directory.
    assert "[plan](../v0.5/plans/v0.5.2-alpha.md)" in target
    assert "| Warnings (WN) | 1 | 0 |" in target and "**Open items**: 1" in target
    source = repo.read(GAPS05)
    assert "#### WN-3: The probe flakes on a cold cache - MIGRATED to v0.6.0" in source
    assert "| Warnings (WN) | 0 | 0 |" in source and "**Open items**: 0" in source
    assert repo.gaps_minor() == ("met", [])


@pytest.mark.parametrize("label", ["`plan`", "a `plan` link", "``plan``"])
def test_migration_repoints_code_formatted_link_labels(repo: Close, label: str) -> None:
    repo.standard(WN3.replace("[plan]", f"[{label}]"))
    repo.forge()
    result = repo.migrate()
    assert result.returncode == 0, result.stdout + result.stderr
    target = repo.read(GAPS06)
    assert f"[{label}](../v0.5/plans/v0.5.2-alpha.md)" in target
    assert (repo.work / V06 / "../v0.5/plans/v0.5.2-alpha.md").is_file()
    assert repo.gaps_minor() == ("met", [])


def test_reference_definition_with_code_label_is_repointed() -> None:
    text = "[`plan`]: plans/alpha.md\n"
    fixed, count = mc.rewrite_links(text, V05, V06, lambda path: path)
    assert fixed == "[`plan`]: ../v0.5/plans/alpha.md\n"
    assert count == 1


def test_link_repair_preserves_code_examples_and_label_literals() -> None:
    example = "``[`plan`](plans/alpha.md)``\n"
    fence = "```md\n[`plan`](plans/alpha.md)\n```\n"
    label = f"[`{V05}`](plans/alpha.md)\n"
    text = example + fence + label
    fixed, count = mc.rewrite_links(text, V05, V06, lambda path: path)
    assert fixed == example + fence + label.replace("(plans/", "(../v0.5/plans/")
    assert count == 1
    mentioned, mentions = mc.rewrite_mentions(text, V05, "docs/archives/v0/v0.5", markdown=True)
    assert mentioned == text and mentions == 0


def test_migrate_into_existing_target_takes_the_next_id(repo: Close) -> None:
    repo.write(GAPS06, ledger("v0.6", section("v0.6.0", 1, "#### WN-1: Existing warning\n\n- **Reason**: r\n\n")))
    repo.standard()
    repo.forge()
    result = repo.migrate()
    assert result.returncode == 0, result.stdout
    target = repo.read(GAPS06)
    assert "#### WN-1: Existing warning" in target and "#### WN-2: The probe flakes" in target
    assert target.index("WN-1: Existing") < target.index("WN-2: The probe") < target.index("### Resolved")
    assert "| Warnings (WN) | 2 | 0 |" in target and "**Open items**: 2" in target


def test_double_migration_adds_a_second_provenance_line(repo: Close) -> None:
    repo.plan("v0.6.0", "gamma", folder=f"{V06}/plans")
    repo.standard()
    repo.forge()
    assert repo.migrate().returncode == 0
    repo.commit("migrate v0.5")
    repo.forge(token="v0.6", bound=("v0.6#WN-1",))
    result = repo.migrate("v0.6#WN-1", "v0.6")
    assert result.returncode == 0, result.stdout
    target = repo.read("docs/releases/v0/v0.7/known-gaps.md")
    assert target.count("#### WN-1:") == 1
    assert "- **Migrated from**: v0.5#WN-3 on 2026-09-29 (reason: vendor-feature)" in target
    assert "- **Migrated from**: v0.6#WN-1 on 2026-09-29 (reason: vendor-feature)" in target
    assert "- MIGRATED to v0.7.0" in repo.read(GAPS06)


def test_rerun_after_a_partial_write_never_duplicates_the_entry(repo: Close) -> None:
    repo.standard()
    repo.forge()
    before = repo.read(GAPS05)
    assert repo.migrate().returncode == 0
    migrated_target = repo.read(GAPS06)
    repo.write(GAPS05, before)  # the source write was lost; the target copy exists
    result = repo.migrate()
    assert result.returncode == 0, result.stdout
    assert "v0.6#WN-1" in result.stdout
    assert repo.read(GAPS06) == migrated_target
    assert "- MIGRATED to v0.6.0" in repo.read(GAPS05)



RETAINED_WARNING = WN3 + (
    "- **Origin**: v0.4#WN-2\n"
    "- **Owner**: repository maintainer\n"
    "- **Acceptance**: keep both the cold-cache and retry obligations\n"
    "- **Proving command**: `pytest -q tests/test_probe.py`\n\n"
)


def _damaged_copy(text: str, damage: str) -> str:
    """Damage one real generated copy without changing the source."""
    copy = cm.parse_ledger(text)[0]
    body = RETAINED_WARNING.split("\n", 1)[1].strip("\n").rstrip().replace(
        "(plans/v0.5.2-alpha.md)", "(../v0.5/plans/v0.5.2-alpha.md)"
    )
    provenance = "- **Migrated from**: v0.5#WN-3 on 2026-09-29 (reason: vendor-feature)"
    if damage == "stub":
        return text.replace(body + "\n\n", "")
    if damage in {"origin", "owner", "acceptance", "command"}:
        names = {"origin": "Origin", "owner": "Owner", "acceptance": "Acceptance", "command": "Proving command"}
        line = next(line for line in text.splitlines(keepends=True) if f"**{names[damage]}**:" in line)
        return text.replace(line, "")
    if damage == "altered-command":
        return text.replace("`pytest -q tests/test_probe.py`", "`pytest -q tests/test_probe.py` && true")
    if damage == "title":
        return text.replace("#### WN-1: The probe flakes on a cold cache", "#### WN-1: A different obligation")
    if damage == "wrong-section":
        return text.replace("## v0.6.0", "## v0.6.1")
    if damage == "duplicate":
        duplicate = text[copy.start:copy.end].replace("#### WN-1:", "#### WN-2:", 1)
        return (text[:copy.end] + duplicate + text[copy.end:]).replace(
            "**Open items**: 1", "**Open items**: 2"
        ).replace("| Warnings (WN) | 1 |", "| Warnings (WN) | 2 |")
    if damage == "duplicate-provenance":
        return text.replace(provenance, provenance + "\n" + provenance)
    if damage == "malformed":
        return text.replace("### Resolved", "```\n### Resolved")
    if damage == "reason":
        return text.replace("(reason: vendor-feature)", "(reason: unreviewed)")
    if damage == "comment":
        return text.replace(body, "<!--\n" + body + "\n-->")
    if damage == "fence":
        return text.replace(body, "~~~\n" + body + "\n~~~")
    if damage == "provenance-comment":
        return text.replace(provenance, "<!--\n" + provenance + "\n-->")
    if damage == "provenance-fence":
        return text.replace(provenance, "~~~\n" + provenance + "\n~~~")
    if damage == "provenance-inline":
        return text.replace(provenance, "- Example: `" + provenance + "`")
    if damage == "provenance-multiline":
        return text.replace(provenance, "`\n" + provenance + "\n`")
    if damage == "item-comment":
        return text[:copy.start] + "<!--\n" + text[copy.start:copy.end] + "-->\n" + text[copy.end:]
    if damage == "item-comment-cr":
        return text[:copy.start].replace("\n", "\r") + "<!--\r" + text[copy.start:copy.end] + "-->\n" + text[copy.end:]
    if damage == "section-comment":
        return text.replace("## v0.6.0", "## v0.6.1\n\n<!--\n## v0.6.0\n-->")
    raise AssertionError(damage)


@pytest.mark.parametrize(
    ("damage", "reason"),
    [
        ("stub", "migration-body-not-preserved"),
        ("origin", "migration-body-not-preserved"),
        ("owner", "migration-body-not-preserved"),
        ("acceptance", "migration-body-not-preserved"),
        ("command", "migration-body-not-preserved"),
        ("altered-command", "migration-body-not-preserved"),
        ("title", "migration-title-not-preserved"),
        ("wrong-section", "migration-target-wrong-section"),
        ("duplicate", "migration-target-ambiguous"),
        ("duplicate-provenance", "migration-target-ambiguous"),
        ("malformed", "migration-target-malformed"),
        ("reason", "migration-reason-invalid"),
        ("comment", "migration-body-not-preserved"),
        ("fence", "migration-body-not-preserved"),
        ("provenance-comment", "migration-provenance-hidden"),
        ("provenance-fence", "migration-provenance-hidden"),
        ("provenance-inline", "migration-provenance-hidden"),
        ("provenance-multiline", "migration-provenance-hidden"),
        ("item-comment", "migration-target-hidden"),
        ("item-comment-cr", "migration-target-hidden"),
        ("section-comment", "migration-target-hidden"),
    ],
)
def test_incomplete_reuse_refuses_before_either_write_and_never_verifies(
    repo: Close, damage: str, reason: str,
) -> None:
    repo.standard(RETAINED_WARNING)
    repo.forge()
    open_source = repo.read(GAPS05)
    assert repo.migrate().returncode == 0
    migrated_source = repo.read(GAPS05)
    target = _damaged_copy(repo.read(GAPS06), damage)
    repo.write(GAPS05, open_source)  # simulate loss of only the source write
    repo.write(GAPS06, target)
    before = [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)]
    result = repo.migrate()
    assert result.returncode == 3, result.stdout + result.stderr
    refused = "ledger-unparsed" if damage == "malformed" else reason
    assert result.stdout.startswith(f"REFUSED: {refused} "), result.stdout
    assert [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)] == before

    # A forged source marker must not turn the same damaged destination into proof.
    repo.write(GAPS05, migrated_source)
    status, notices = repo.gaps_minor()
    assert status == ("cannot-verify" if damage == "malformed" else "unmet")
    assert f"gaps.minor migration v0.5#WN-3 {reason}" in notices

    # Plan-mode provenance is exact to the source patch, but content proof is shared.
    if damage != "reason":  # historical plan reason policy is unchanged
        repo.write(GAPS06, target.replace("v0.5#WN-3", "v0.5.2#WN-3"))
        ledgers, _ = cm.load_ledgers(repo.work)
        source = next(ledger for ledger in ledgers if ledger.rel == GAPS05)
        assert not cm.plan_migration_met(ledgers, source, source.items[0])


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_complete_reconciled_copy_is_idempotent_with_added_evidence(repo: Close, newline: str) -> None:
    repo.standard(RETAINED_WARNING.replace("\n", newline))
    repo.forge()
    open_source = (repo.work / GAPS05).read_bytes()
    assert repo.migrate().returncode == 0
    path = repo.work / GAPS06
    target = path.read_bytes().decode("utf-8")
    target = target.replace(
        "### Resolved", "- **Later evidence**: retained independently on a second date" + newline + newline + "### Resolved"
    )
    path.write_bytes(target.encode("utf-8"))
    target_before = path.read_bytes()
    (repo.work / GAPS05).write_bytes(open_source)
    result = repo.migrate()
    assert result.returncode == 0, result.stdout + result.stderr
    assert path.read_bytes() == target_before
    assert repo.gaps_minor() == ("met", [])
    for field in ("Origin", "Owner", "Acceptance", "Proving command"):
        assert f"**{field}**:" in target


def test_unmatched_ticks_do_not_hide_later_paragraph_provenance(repo: Close) -> None:
    warning = RETAINED_WARNING + (
        "- **Literal text**: unmatched ` and a different `` run stay literal.\n\n"
        "```text\n` and `` are only examples inside a fence.\n```\n\n"
    )
    repo.standard(warning)
    repo.forge()
    open_source = repo.read(GAPS05)
    assert repo.migrate().returncode == 0
    target = repo.read(GAPS06).replace(
        "### Resolved", "- **Later evidence**: `pytest -q tests/test_probe.py`\n\n### Resolved"
    )
    repo.write(GAPS05, open_source)
    repo.write(GAPS06, target)
    result = repo.migrate()
    assert result.returncode == 0, result.stdout + result.stderr
    assert repo.read(GAPS06) == target and repo.gaps_minor() == ("met", [])


def test_consolidated_owner_requires_an_explicit_complete_original_source_block(repo: Close) -> None:
    repo.standard(RETAINED_WARNING)
    repo.forge()
    open_source = repo.read(GAPS05)
    assert repo.migrate().returncode == 0
    target = repo.read(GAPS06).replace(
        "#### WN-1: The probe flakes on a cold cache",
        "#### AR-1: Several related residual obligations",
    )
    repo.write(GAPS05, open_source)
    repo.write(GAPS06, target + "\nThe earlier title was WN-3: The probe flakes on a cold cache.\n")
    rejected = repo.migrate()
    assert rejected.returncode == 3 and "migration-title-not-preserved" in rejected.stdout
    callout = "##### Original source: WN-3: The probe flakes on a cold cache\n\n"
    target = target.replace("- **Source phase**: Phase 2", callout + "- **Source phase**: Phase 2")
    for spoof in (
        target.replace("##### Original source:", "##### Earlier heading:"),
        target.replace(callout, "<!--\n" + callout + "-->\n"),
        target.replace(callout, "~~~\n" + callout + "~~~\n"),
    ):
        repo.write(GAPS06, spoof)
        before = [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)]
        rejected = repo.migrate()
        assert rejected.returncode == 3 and "migration-title-not-preserved" in rejected.stdout
        assert [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)] == before
    entry = cm.parse_ledger(target)[0]
    hidden = target[:entry.start] + "<!--\n" + target[entry.start:entry.end] + "-->\n" + target[entry.end:]
    repo.write(GAPS06, hidden)
    before = [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)]
    rejected = repo.migrate()
    assert rejected.returncode == 3 and "migration-target-hidden" in rejected.stdout
    assert [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)] == before
    repo.write(GAPS06, target)
    result = repo.migrate()
    assert result.returncode == 0, result.stdout + result.stderr
    assert repo.read(GAPS06) == target and repo.gaps_minor() == ("met", [])
    # H3 source owners with H4 nested source blocks must retain their body on a second migration.
    target = target.replace("#### AR-1:", "### AR-1:").replace("##### Original source:", "#### Original source:")
    repo.write(GAPS06, target)
    repo.commit("complete consolidated owner")
    repo.plan("v0.6.0", "gamma", folder=f"{V06}/plans")
    repo.commit("next minor plan")
    record = repo.forge(token="v0.6", bound=("v0.6#AR-1",))
    onward = repo.migrate("v0.6#AR-1", "v0.6")
    assert onward.returncode == 0, onward.stdout + onward.stderr
    assert "#### Original source: WN-3: The probe flakes on a cold cache" in repo.read(
        "docs/releases/v0/v0.7/known-gaps.md"
    )
    ledgers, _ = cm.load_ledgers(repo.work)
    current = next(ledger for ledger in ledgers if ledger.rel == GAPS06)
    earlier = next(ledger for ledger in ledgers if ledger.rel == GAPS05)
    assert cm.verify_migration(repo.rctx(), record, "v0.6", ledgers, current, current.items[0]) == (
        "met", "approved-migration"
    )
    assert cm.verify_migration(repo.rctx(), record, "v0.6", ledgers, earlier, earlier.items[0]) == (
        "met", "in-scope-copy"
    )


def test_verification_follows_explicit_patch_carry_but_reuse_stays_at_minor_start(repo: Close) -> None:
    warning = RETAINED_WARNING.replace("WN-3: The probe", "WN-3 (v0.5.2): The probe")
    repo.standard(warning)
    repo.forge()
    open_source = repo.read(GAPS05)
    assert repo.migrate().returncode == 0
    text = repo.read(GAPS06)
    copy = cm.parse_ledger(text)[0]
    moved, _ = mc.carry_within(text, copy, "v0.6.1", "v0.6.0", "2026-10-09")
    repo.write(GAPS06, moved)
    assert "(v0.6.1): The probe" in moved and "**Carried from**: v0.6.0#WN-1" in moved
    assert repo.gaps_minor() == ("met", [])
    ledgers, _ = cm.load_ledgers(repo.work)
    source = next(ledger for ledger in ledgers if ledger.rel == GAPS05)
    qualified = moved.replace("v0.5#WN-3", "v0.5.2#WN-3")
    repo.write(GAPS06, qualified)
    assert cm.plan_migration_met(cm.load_ledgers(repo.work)[0], source, source.items[0])
    repo.write(GAPS06, moved.replace("- **Carried from**: v0.6.0#WN-1 on 2026-10-09\n", ""))
    assert "migration-target-wrong-section" in repo.gaps_minor()[1][0]
    carried_line = "- **Carried from**: v0.6.0#WN-1 on 2026-10-09\n"
    for opening, closing in (("<!--\n", "-->\n"), ("~~~\n", "~~~\n")):
        repo.write(GAPS06, moved.replace(carried_line, opening + carried_line + closing))
        assert "migration-target-wrong-section" in repo.gaps_minor()[1][0]
    for bad_lineage in (
        carried_line.replace("#WN-1", "#DF-999"),
        "- Example: `" + carried_line.rstrip() + "`\n",
        "`\n" + carried_line + "`\n",
    ):
        repo.write(GAPS06, moved.replace(carried_line, bad_lineage).replace("v0.5#WN-3", "v0.5.2#WN-3"))
        assert "migration-target-wrong-section" in repo.gaps_minor()[1][0]
        assert not cm.plan_migration_met(cm.load_ledgers(repo.work)[0], source, source.items[0])
    repo.write(GAPS06, moved)
    repo.write(GAPS05, open_source)
    before = [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)]
    result = repo.migrate()
    assert result.returncode == 3 and "migration-target-wrong-section" in result.stdout
    assert [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)] == before


def test_later_target_archive_preserves_proved_repairs_and_refuses_unproved_moves(repo: Close) -> None:
    old = "docs/archives/v0/v0.4/known-gaps.md"
    archive = "docs/archives/v0/v0.6"
    warning = RETAINED_WARNING + (
        "See docs/releases/v0/v0.6/plans/future.md and docs/releases/v0/v0.5/plans/current.md.\n\n"
    )
    repo.write(old, ledger("v0.4", section("v0.4.0", 1, warning)))
    repo.standard("")
    repo.forge(bound=("v0.4#WN-3",))
    assert repo.migrate("v0.4#WN-3").returncode == 0
    old_before = repo.read(old)
    repairs = mc.plan_repairs(
        repo.work, [(old, old, old), (GAPS06, GAPS06, f"{archive}/known-gaps.md")], V06, archive,
    )
    for repair in repairs:
        repo.write(repair.new_rel, repair.repaired)
    (repo.work / GAPS06).unlink()
    assert repo.read(old) == old_before  # archived plain mentions remain historical
    assert "See docs/archives/v0/v0.6/plans/future.md" in repo.read(f"{archive}/known-gaps.md")
    assert repo.gaps_minor() == ("met", [])
    target = repo.read(f"{archive}/known-gaps.md").replace(
        "docs/releases/v0/v0.5/plans/current.md", "docs/archives/v0/v0.5/plans/current.md"
    )
    repo.write(f"{archive}/known-gaps.md", target)
    assert "migration-body-not-preserved" in repo.gaps_minor()[1][0]


def test_active_and_archived_target_ledgers_refuse_before_either_write(repo: Close) -> None:
    repo.standard(RETAINED_WARNING)
    repo.forge()
    source = repo.read(GAPS05)
    assert repo.migrate().returncode == 0
    target = repo.read(GAPS06)
    repo.write(GAPS05, source)
    archived = "docs/archives/v0/v0.6/known-gaps.md"
    repo.write(archived, target)
    before = [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06, archived)]
    result = repo.migrate()
    assert result.returncode == 3 and "target-ledger-ambiguous" in result.stdout
    assert [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06, archived)] == before



def test_unlisted_id_is_refused_and_nothing_is_written(repo: Close) -> None:
    repo.standard(WN3 + "#### WN-4: Another warning\n\n- **Reason**: r\n\n", wn_open=2)
    repo.forge()
    before = repo.read(GAPS05)
    result = repo.migrate("v0.5#WN-4")
    assert result.returncode == 3
    assert result.stdout.strip() == "REFUSED: migration-not-approved (v0.5#WN-4)"
    assert repo.read(GAPS05) == before and not (repo.work / GAPS06).exists()


def test_security_item_needs_individual_naming(repo: Close) -> None:
    repo.standard(WN3 + BG2, bg_open=1)
    repo.forge(bound=("v0.5#WN-3", "v0.5#BG-2"))
    refused = repo.migrate("v0.5#BG-2")
    assert refused.returncode == 3 and refused.stdout.strip() == "REFUSED: security-not-named (v0.5#BG-2)"
    repo.forge(bound=("v0.5#WN-3", "v0.5#BG-2"), named=("v0.5#BG-2",))
    assert repo.migrate("v0.5#BG-2").returncode == 0
    assert "#### BG-1: Security token is logged" in repo.read(GAPS06)


HIGH_WN5 = (
    "#### WN-5: Cache key collides across tenants\n\n"
    "- **Severity**: high\n- **Reason**: needs the vendor fix\n\n"
)


def test_lowering_the_severity_after_approval_does_not_lift_naming(repo: Close) -> None:
    """BG-2 (ADV-2): sensitivity is judged at the record's start too, not only on the
    current text, so editing `**Severity**: high` to low during the run cannot let an
    unnamed high-severity gap migrate."""
    repo.standard(WN3 + HIGH_WN5, wn_open=2)
    repo.forge(bound=("v0.5#WN-3", "v0.5#WN-5"))  # frozen, not named; start_head = the high text
    repo.write(GAPS05, repo.read(GAPS05).replace("**Severity**: high", "**Severity**: low"))
    before = repo.read(GAPS05)
    refused = repo.migrate("v0.5#WN-5")
    assert refused.returncode == 3 and refused.stdout.strip() == "REFUSED: security-not-named (v0.5#WN-5)"
    assert repo.read(GAPS05) == before and "WN-5" not in (repo.read(GAPS06) if (repo.work / GAPS06).exists() else "")


def test_the_verify_path_uses_the_same_baseline(repo: Close) -> None:
    """The minor verdict's gate reads the start text: a named-free migration of a gap that
    was high-severity at the start never verifies, even after its text was lowered."""
    repo.standard(WN3 + HIGH_WN5, wn_open=2)
    record = repo.forge(bound=("v0.5#WN-3", "v0.5#WN-5"))
    rctx = repo.rctx()
    lowered = cm.parse_ledger(repo.read(GAPS05).replace("**Severity**: high", "**Severity**: low"))
    item = next(i for i in lowered if i.gid == "WN-5")
    assert not item.sensitive()
    assert cm.migration_gate(rctx, record, (0, 5), "WN-5", item) == ("unmet", "security-not-named")
    named = repo.forge(bound=("v0.5#WN-3", "v0.5#WN-5"), named=("v0.5#WN-5",))
    assert cm.migration_gate(rctx, named, (0, 5), "WN-5", item) == ("met", "approved")


def test_a_gap_resolved_at_the_start_never_migrates(repo: Close) -> None:
    """An id that was already RESOLVED when the run was approved cannot be reused for a
    gap reopened or created during the run."""
    repo.standard(WN3.replace("#### WN-3: The probe flakes on a cold cache",
                              "#### WN-3: The probe flakes on a cold cache - RESOLVED"), wn_open=0)
    repo.forge(bound=("v0.5#WN-3",))
    repo.write(GAPS05, repo.read(GAPS05).replace(" - RESOLVED", ""))
    refused = repo.migrate("v0.5#WN-3")
    assert refused.returncode == 3 and refused.stdout.strip() == "REFUSED: not-open-at-start (v0.5#WN-3)"


def test_gap_created_during_the_run_never_migrates(repo: Close) -> None:
    repo.standard()
    repo.forge(bound=("v0.5#WN-3", "v0.5#WN-9"))
    text = repo.read(GAPS05).replace("### Resolved", "#### WN-9: Found mid-run\n\n- **Reason**: r\n\n### Resolved")
    repo.write(GAPS05, text.replace("| Warnings (WN) | 1 |", "| Warnings (WN) | 2 |"))
    repo.commit("mid-run gap")
    result = repo.migrate("v0.5#WN-9")
    assert result.returncode == 3 and result.stdout.strip() == "REFUSED: created-during-run (v0.5#WN-9)"


def test_concurrent_edit_of_the_source_writes_nothing(repo: Close) -> None:
    repo.standard()
    record = repo.forge()
    rctx = repo.rctx()
    plan = mc.plan_migration(rctx, "v0.5", record, "v0.5#WN-3", "user-deferred", "e", "2026-09-29")
    repo.write(GAPS05, repo.read(GAPS05) + "\nconcurrent edit\n")
    with pytest.raises(mc.Refused) as refused:
        mc.apply_migration(plan)
    assert refused.value.reason == "source-changed"
    assert not (repo.work / GAPS06).exists()


def test_migrate_without_a_record_is_not_covered(repo: Close) -> None:
    repo.standard()
    result = repo.migrate()
    assert result.returncode == 3 and result.stdout.startswith("REFUSED: approval-not-covered")


# --------------------------------------------------------------------------- gaps.minor


def test_scope_covers_earlier_versions_and_stops_at_the_run_minor(repo: Close) -> None:
    repo.write("docs/archives/v0/v0.4/known-gaps.md", ledger("v0.4", section("v0.4.1", 1, "#### WN-1: Old\n\n")))
    repo.write(GAPS06, ledger("v0.6", section("v0.6.0", 1, "#### WN-1: Later\n\n")))
    repo.standard("")
    repo.forge(bound=())
    status, notices = repo.gaps_minor()
    assert status == "unmet"
    assert notices == ["gaps.minor open v0.4#WN-1"]


OLD04 = "docs/releases/v0/v0.4/known-gaps.md"


def _old_ledger(repo: Close, items: str = "#### WN-1: Old\n\n", wn_open: int = 1) -> None:
    repo.write(OLD04, ledger("v0.4", section("v0.4.1", wn_open, items)))


def test_stale_unmerged_branch_excludes_nothing(repo: Close) -> None:
    _old_ledger(repo)
    repo.standard("")
    _git(repo.work, "checkout", "-q", "-b", "fix/v0.4-gap")
    repo.write(OLD04, repo.read(OLD04) + "\nedit\n")
    repo.commit("edit old ledger")
    _git(repo.work, "checkout", "-q", "main")
    repo.forge(bound=())
    assert repo.gaps_minor() == ("unmet", ["gaps.minor open v0.4#WN-1"])


def test_ledger_changed_on_a_live_branch_with_open_items_cannot_be_verified(repo: Close, tmp_path: Path) -> None:
    _old_ledger(repo)
    repo.standard("")
    _git(repo.work, "branch", "fix/v0.4-gap")
    live = tmp_path / "live"
    _git(repo.work, "worktree", "add", "-q", str(live), "fix/v0.4-gap")
    (live / OLD04).write_text(repo.read(OLD04) + "\nedit\n", encoding="utf-8")
    _git(live, "commit", "-q", "-am", "edit old ledger")
    repo.forge(bound=())
    status, notices = repo.gaps_minor()
    assert status == "cannot-verify"
    assert notices == [f"gaps.minor excluded {OLD04} (changed-on-live-branch)",
                       f"gaps.minor excluded {OLD04} still holds open items"]


def test_ledger_of_a_minor_a_live_run_owns_is_excluded(repo: Close) -> None:
    _old_ledger(repo, "#### WN-1: Old - RESOLVED 2026-09-01\n\n", wn_open=0)
    rel = repo.plan("v0.4.1", "legacy", folder="docs/releases/v0/v0.4/plans")
    repo.standard("")
    rctx = repo.rctx()
    path = ck.plan_record_paths(rctx.root, rctx.key_repo, rctx.remote_url, rel)[0]
    ck._write_record(path, {"schema": ck.SCHEMA, "plan": rel, "repo_root": str(rctx.root),
                            "created": ck._now(), "nonce": "other-run"})
    repo.forge(bound=())
    assert repo.gaps_minor() == ("met", [f"gaps.minor excluded {OLD04} (owned-by-another-run)"])


def test_run_own_minor_is_never_excluded(repo: Close, tmp_path: Path) -> None:
    repo.standard()
    _git(repo.work, "branch", "scratch")
    live = tmp_path / "live"
    _git(repo.work, "worktree", "add", "-q", str(live), "scratch")
    (live / GAPS05).write_text(repo.read(GAPS05) + "\nnote\n", encoding="utf-8")
    _git(live, "commit", "-q", "-am", "touch")
    repo.forge(bound=())
    assert repo.gaps_minor() == ("unmet", ["gaps.minor open v0.5#WN-3"])


def test_migrated_copy_in_a_later_minor_never_reopens_the_verdict(repo: Close) -> None:
    repo.standard()
    repo.forge()
    assert repo.migrate().returncode == 0
    assert "#### WN-1:" in repo.read(GAPS06)  # the copy is open in v0.6
    assert repo.gaps_minor() == ("met", [])
    assert repo.gaps_minor("v0.6")[0] == "unmet"  # and stays open in its own minor


def test_hand_written_marker_pair_is_not_accepted(repo: Close) -> None:
    repo.standard(WN3 + "#### WN-4: Unlisted\n\n- **Reason**: r\n\n", wn_open=2)
    repo.forge()
    text = repo.read(GAPS05).replace("#### WN-4: Unlisted", "#### WN-4: Unlisted - MIGRATED to v0.6.0")
    repo.write(GAPS05, text)
    repo.write(GAPS06, ledger("v0.6", section("v0.6.0", 1, (
        "#### WN-1: Unlisted\n\n- **Migrated from**: v0.5#WN-4 on 2026-09-29 (reason: user-deferred)\n\n"
    ))))
    status, notices = repo.gaps_minor()
    assert status == "unmet"
    assert "gaps.minor migration v0.5#WN-4 migration-not-approved" in notices


def test_marker_without_its_target_entry_is_unmet(repo: Close) -> None:
    repo.standard()
    repo.forge()
    repo.write(GAPS05, repo.read(GAPS05).replace("cold cache\n", "cold cache - MIGRATED to v0.6.0\n", 1))
    status, notices = repo.gaps_minor()
    assert status == "unmet" and "gaps.minor migration v0.5#WN-3 migration-target-missing" in notices


def test_unreadable_ledger_cannot_be_verified(repo: Close) -> None:
    repo.standard()
    (repo.work / "docs/archives/v0/v0.3").mkdir(parents=True)
    (repo.work / "docs/archives/v0/v0.3/known-gaps.md").write_bytes(b"\xff\xfe\x00bad")
    repo.forge()
    status, notices = repo.gaps_minor()
    assert status == "cannot-verify"
    assert notices == ["gaps.minor unreadable docs/archives/v0/v0.3/known-gaps.md"]


def test_parser_states_and_the_closed_marker() -> None:
    text = (
        "## v0.5.0\n\n### Open Items\n\n#### WN-1: Open\n\n#### WN-2: Done - RESOLVED 2026-09-01\n\n"
        "#### Warnings\n\n##### WN-3 - OPEN: Reconciled - CLOSED 2026-09-29\n\n"
        "#### NI-4 - CLOSED: status prefix\n\n"
        "#### WN-4: Moved - MIGRATED to v0.6.0\n\n```\n#### WN-5: inside a fence\n```\n\n"
        "### WN-7 - Level three item\n\n###### WN-8: Level six\n\n#### WN-D: Letter id\n\n#### DF-v24: Versioned id\n\n"
        "#### WN-10: Sockets - closed handles leak\n\n#### WN-11: Retry -- Resolved-path lookup fails\n\n"
        "#### WN-12: A - RESOLVED word mid-title stays open\n\n"
        "### Resolved\n\n#### WN-6: Listed under Resolved\n\n## Notes\n\n#### AR-1: Outside Open Items\n"
    )
    items, problems = cm.parse_ledger_full(text)
    assert problems == []
    assert {i.gid: i.state for i in items} == {
        "WN-1": "open", "WN-2": "resolved", "WN-3": "resolved", "NI-4": "resolved", "WN-4": "migrated",
        "WN-7": "open", "WN-8": "open", "WN-D": "open", "DF-v24": "open", "WN-10": "open", "WN-11": "open",
        "WN-12": "open", "WN-6": "resolved", "AR-1": "open",
    }


def test_commonmark_fences() -> None:
    # A backtick fence whose info string holds a backtick is not a fence; a longer fence
    # is not closed by a shorter one; an indented line is not an opener.
    text = (
        "Run ```` ``` `x` ```` like this:\n\n``` `inline` ```\n\n#### WN-7: Visible\n\n"
        "#### WN-1: open\n\n````\n```\n#### WN-2: inside a four-tick fence\n````\n\n#### WN-8: after\n\n"
        "~~~\n#### WN-3: inside tildes\n```\n~~~\n#### WN-9: after tildes\n"
    )
    assert [i.gid for i in cm.parse_ledger(text)] == ["WN-7", "WN-1", "WN-8", "WN-9"]
    assert cm.parse_ledger_full("#### WN-1: a\n\n```\n#### WN-2: hidden\n")[1] == ["unclosed-fence"]


def test_crlf_bom_and_closing_hashes() -> None:
    text = "\ufeff" + ledger("v0.5", section("v0.5.2", 1, WN3)).replace("\n", "\r\n")
    assert [(i.gid, i.state) for i in cm.parse_ledger(text)] == [("WN-3", "open")]
    trailing = cm.parse_ledger("#### WN-9: trailing closing hashes - MIGRATED to v0.6.0 ####\n")
    assert [(i.gid, i.state, i.target) for i in trailing] == [("WN-9", "migrated", "v0.6.0")]


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("## WN-3: an item at level two\n", "line 1 heading"),
        ("### Open Items\n\n- WN-4: an item written as a list row\n", "line 3 row"),
        ("### Open Items\n\n| WN-5 | an item written as a table row |\n", "line 3 row"),
        ("**Open items**: 2\n\n## v0.5.0\n\n#### WN-1: only one open\n", "open-items-count"),
    ],
)
def test_ledger_problems(text: str, problem: str) -> None:
    assert problem in cm.parse_ledger_full(text)[1]


def test_rows_under_resolved_and_inside_items_are_not_problems() -> None:
    text = ("### Open Items\n\n#### WN-1: open\n\n- WN-2 is related\n\n"
            "### Resolved\n\n| ID | Title |\n|---|---|\n| WN-3 | fixed |\n")
    assert cm.parse_ledger_full(text)[1] == []


def test_unparsed_ledger_cannot_be_verified(repo: Close) -> None:
    repo.standard("- WN-7: a row that looks like an item\n\n", wn_open=0)
    repo.forge(bound=())
    status, notices = repo.gaps_minor()
    assert status == "cannot-verify"
    assert notices == [f"gaps.minor unparsed {GAPS05} (line 18 row)"]


def test_a_repeated_id_on_unresolved_work_is_ambiguous() -> None:
    assert cm.parse_ledger_full("### Open Items\n\n#### WN-3: first\n\n#### WN-3: second\n")[1] == [
        "duplicate-id WN-3"]
    same_section = "## v0.5.0\n\n#### WN-3: open\n\n#### WN-3: done - RESOLVED\n"
    assert cm.parse_ledger_full(same_section)[1] == ["duplicate-id WN-3"]
    # Patch sections reuse short ids: `v0.5.0#WN-3` and `v0.5.1#WN-3` are distinct items the
    # carry tooling addresses by section, so a repeat across sections is never ambiguous.
    across_sections = "## v0.5.0\n\n#### WN-3: open\n\n## v0.5.1\n\n#### WN-3: also open\n"
    assert cm.parse_ledger_full(across_sections)[1] == []
    resolved_twice = "## v0.5.0\n\n#### WN-3: a - RESOLVED\n\n## v0.5.1\n\n#### WN-3: b - RESOLVED\n"
    assert cm.parse_ledger_full(resolved_twice)[1] == []


def test_a_gap_heading_that_lost_its_id_is_unparsed() -> None:
    template = "### Open Items\n\n" + WN3.replace("WN-3: ", "", 1)
    assert cm.parse_ledger_full(template)[1] == ["line 3 heading-without-id"]
    contract = "### Installer and CLI\n\n### No live smoke\n\n- **Owner**: installer owner\n- **Severity**: low\n"
    assert cm.parse_ledger_full(contract)[1] == ["line 3 heading-without-id"]
    migrated = "### Open Items\n\n#### Moved on - MIGRATED to v0.6.0\n"
    assert cm.parse_ledger_full(migrated)[1] == ["line 3 heading-without-id"]


def test_grouping_and_closed_headings_without_an_id_are_not_problems() -> None:
    text = (
        "## v0.5.0\n\n### Summary\n\n**Status**: shipped\n\n### Installer and CLI\n\n" + WN3
        + "### Notes\n\n- **Reason**: one field alone is prose\n\n```\n- **Owner**: x\n- **Severity**: low\n```\n\n"
        "#### Old finding - RESOLVED 2026-09-01\n\n- **Source phase**: 1\n- **Reason**: fixed\n\n"
        "#### ~~NI-4~~ (RESOLVED in Phase 6.1) - closed\n\n- **Source phase**: 1\n- **Reason**: x\n\n"
        "### Resolved\n\n#### Fixed without an id\n\n- **Source phase**: 1\n- **Reason**: x\n"
    )
    assert cm.parse_ledger_full(text)[1] == []


def test_duplicate_id_is_reported_and_refuses_migration(repo: Close) -> None:
    repo.standard(WN3 + "#### WN-3: An older copy - RESOLVED 2026-09-01\n\n")
    repo.forge()
    status, notices = repo.gaps_minor()
    assert status == "unmet"
    assert notices == [f"gaps.minor unparsed {GAPS05} (duplicate-id WN-3)", "gaps.minor open v0.5#WN-3"]
    before = repo.read(GAPS05)
    result = repo.migrate()
    assert result.returncode == 3, result.stdout + result.stderr
    assert result.stdout.startswith(f"REFUSED: ledger-unparsed ({GAPS05} duplicate-id WN-3)"), result.stdout
    assert repo.read(GAPS05) == before and not (repo.work / GAPS06).exists()


def test_a_gap_that_lost_its_id_keeps_the_minor_from_closing(repo: Close) -> None:
    repo.standard(WN3.replace("WN-3: ", "", 1), wn_open=0)
    repo.forge(bound=())
    status, notices = repo.gaps_minor()
    assert status == "cannot-verify"
    assert notices == [f"gaps.minor unparsed {GAPS05} (line 18 heading-without-id)"]


def test_self_migration_marker_is_not_accepted(repo: Close) -> None:
    prov = "- **Migrated from**: v0.5#WN-3 on 2026-09-29 (reason: user-deferred)\n\n"
    repo.standard("#### WN-3: The probe flakes - MIGRATED to v0.5.0\n\n" + prov, wn_open=0)
    repo.forge(bound=())
    status, notices = repo.gaps_minor()
    assert status == "unmet" and notices == ["gaps.minor migration v0.5#WN-3 migration-not-forward"]


def test_migration_cycle_between_two_in_scope_minors_is_not_accepted(repo: Close) -> None:
    repo.write(OLD04, ledger("v0.4", section("v0.4.0", 0, (
        "#### WN-3: Copy - MIGRATED to v0.5.0\n\n- **Migrated from**: v0.5#WN-3 on 2026-09-29 (reason: user-deferred)\n\n"))))
    repo.standard("#### WN-3: Real open work - MIGRATED to v0.4.0\n\n"
                  "- **Migrated from**: v0.4#WN-3 on 2026-09-29 (reason: user-deferred)\n\n", wn_open=0)
    repo.forge(bound=())
    status, notices = repo.gaps_minor()
    assert status == "unmet"
    assert "gaps.minor migration v0.5#WN-3 migration-not-forward" in notices


def test_an_earlier_run_forward_migration_is_judged_by_its_copy(repo: Close) -> None:
    body = (
        "- **Origin**: v0.3#WN-1\n- **Owner**: repository maintainer\n"
        "- **Acceptance**: the vendor feature must pass the cold-cache probe\n"
        "- **Proving command**: `pytest -q tests/test_probe.py`\n\n"
    )
    repo.write(OLD04, ledger("v0.4", section("v0.4.0", 0, "#### WN-2: Moved on - MIGRATED to v0.5.0\n\n" + body)))
    copy = "#### WN-3: Moved on\n\n" + body + (
        "- **Migrated from**: v0.4#WN-2 on 2026-09-01 (reason: user-deferred)\n"
        "- **Carried from**: v0.5.0#WN-3 on 2026-09-02\n\n"
    )
    repo.standard(copy)
    repo.forge(bound=())
    assert repo.gaps_minor() == ("unmet", ["gaps.minor open v0.5#WN-3"])  # the copy is open work
    repo.write(GAPS05, repo.read(GAPS05).replace("#### WN-3: Moved on", "#### WN-3: Moved on - RESOLVED 2026-09-29"))
    assert repo.gaps_minor() == ("met", [])


def test_duplicate_versions_in_a_historical_minor_do_not_block_the_scope(repo: Close) -> None:
    old = "docs/archives/v0/v0.4"
    repo.write(f"{old}/known-gaps.md", ledger("v0.4", section("v0.4.0", 0, "")))
    repo.plan("v0.4.0", "first", folder=f"{old}/plans")
    repo.plan("v0.4.0", "second", folder=f"{old}/plans")
    repo.standard("")
    repo.forge(bound=())
    assert repo.gaps_minor() == ("met", [])


def test_member_gaps_version_accepts_only_a_verified_migration(repo: Close) -> None:
    repo.standard()
    record = repo.forge()
    assert repo.migrate().returncode == 0
    ctx = ck.Context(str(repo.work / "docs/releases/v0/v0.5/plans/v0.5.2-alpha.md"), ck.Budget(60))
    assert ck._gaps_status(ctx, ck.project(record, "v0.5.2")) == ("met", 0)
    # The same marker in a per-plan run has no migration to verify.
    assert ck._gaps_status(ctx, None)[0] == "unmet"


def test_named_list_must_be_inside_bound(repo: Close) -> None:
    spec = repo.tmp / "spec.json"
    spec.write_text(json.dumps({"classes": [{"class": "gap-migration", "bound": ["v0.5#WN-3"], "named": ["v0.5#BG-2"]}]}))
    with pytest.raises(ck.Malformed):
        cm.minor_spec(ck, str(spec))


# --------------------------------------------------------------------------- archive


def closed_minor(repo: Close) -> None:
    """A v0.5 whose two plans shipped and whose one gap migrated, with every reference class."""
    for version, slug in (("v0.5.2", "alpha"), ("v0.5.10", "omega")):
        rel = f"{V05}/plans/{version}-{slug}.md"
        repo.write(rel, (
            f"# Plan -- {slug}\n\n**Version**: {version}\n**Slug**: {slug}\n**Status**: complete\n\n"
            f"Evidence lives in {V05}/development/evidence.md.\n\n"  # class 1: body prose
            f"## Phase 1: Build\n\n- [x] T001 Build part {V05}/development/evidence.md\n"  # class 4
        ))
    repo.write(f"{V05}/development/evidence.md", (  # class 7: evidence under the tree
        "# Evidence\n\n[policy](../../../../policy/rules.md) and [next](../../v0.6/known-gaps.md)\n"
    ))
    repo.write(f"{V05}/development/capture.json", json.dumps({"path": f"{V05}/development/evidence.md"}) + "\n")
    repo.write("docs/policy/rules.md", "# Rules\n")
    repo.write(f"{V06}/plans/v0.6.0-gamma.md", (  # class 2: a relative link from a sibling tree
        "# Plan -- gamma\n\n**Version**: v0.6.0\n**Slug**: gamma\n**Status**: queued\n\n"
        "Follows [alpha](../../v0.5/plans/v0.5.2-alpha.md).\n\n## Phase 1\n\n- [ ] T001 Build src/g.txt\n"
    ))
    repo.write("docs/todos.md", (
        f"# Todos\n\n## {V05} status\n\n"  # class 6: tracker prose and headings
        "| Minor | Plan |\n|---|---|\n| v0.5 | [alpha](releases/v0/v0.5/plans/v0.5.2-alpha.md) |\n\n"  # class 5
        "See [the omega plan][omega].\n\n"
        "[omega]: releases/v0/v0.5/plans/v0.5.10-omega.md\n"  # class 3: a link-reference definition
    ))
    repo.write("scripts/tool.py", f'LEDGER = "{GAPS05}"\n')
    repo.write(GAPS05, ledger("v0.5", section("v0.5.2", 1, WN3), status="finalized"))
    repo.commit("closed minor")
    repo.integrate()
    repo.forge()
    assert repo.migrate().returncode == 0
    text = repo.read(GAPS05)
    repo.write(GAPS05, text)
    for version in ("v0.5.2", "v0.5.10"):
        repo.ship(version)
    _git(repo.work, "checkout", "-q", "-b", "chore/close-v0.5")
    repo.commit("migrate v0.5#WN-3")


def archive(repo: Close, *extra: str) -> subprocess.CompletedProcess:
    return repo.close("archive", "--minor", "v0.5", "--link-checker", str(LINK_CHECKER), *extra)


@pytest.mark.parametrize("line,unchecked", [
    ("Historical `- [ ]` notation remains evidence.", False),
    ("- [ ] Perform a manual check", True),
    ("  - [ ] Perform a nested manual check", True),
])
def test_archive_register_distinguishes_quoted_checkbox_syntax(repo: Close, line: str, unchecked: bool) -> None:
    closed_minor(repo)
    record = repo.load(None).record
    text = repo.read(GAPS05).replace("\n## ", "\n" + line + "\n\n## ", 1)
    repo.write(GAPS05, text)
    refusals = mc.register_refusals(repo.rctx(), "v0.5", record, V05)
    matches = [r for r in refusals if r.line().startswith("REFUSED: register-unchecked-box")]
    assert bool(matches) is unchecked, [r.line() for r in refusals]


def test_archive_accepts_a_live_released_plan_outside_the_frozen_members(repo: Close) -> None:
    closed_minor(repo)
    record = repo.load(None).record
    assert record is not None
    record = {**record, "members": [m for m in record["members"] if m["version"] != "v0.5.2"]}
    rel = f"{V05}/plans/v0.5.2-alpha.md"
    repo.write(rel, repo.read(rel).replace("**Status**: complete", "**Status**: Released."))
    refusals = mc.plan_refusals(repo.rctx(), "v0.5", record)
    assert refusals == [], [r.line() for r in refusals]


def test_archive_repairs_every_reference_class(repo: Close) -> None:
    closed_minor(repo)
    dry = archive(repo)
    assert dry.returncode == 0, dry.stdout + dry.stderr
    assert dry.stdout.startswith(f"WOULD ARCHIVE v0.5 {V05} -> docs/archives/v0/v0.5 ")
    capture = repo.read(f"{V05}/development/capture.json")
    result = archive(repo, "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith(f"ARCHIVED v0.5 {V05} -> docs/archives/v0/v0.5 commit=")
    assert result.stdout.strip().endswith("newly_broken=0")
    assert not (repo.work / V05).exists()
    new = "docs/archives/v0/v0.5"
    plan = repo.read(f"{new}/plans/v0.5.2-alpha.md")
    assert f"Evidence lives in {new}/development/evidence.md." in plan
    assert f"- [x] T001 Build part {new}/development/evidence.md" in plan
    evidence = repo.read(f"{new}/development/evidence.md")
    assert "[policy](../../../../policy/rules.md)" in evidence
    assert "[next](../../../../releases/v0/v0.6/known-gaps.md)" in evidence
    assert repo.read(f"{new}/development/capture.json") == capture  # point-in-time evidence
    assert "[alpha](../../../../archives/v0/v0.5/plans/v0.5.2-alpha.md)" in repo.read(f"{V06}/plans/v0.6.0-gamma.md")
    todos = repo.read("docs/todos.md")
    assert f"## {new} status" in todos
    assert "[alpha](archives/v0/v0.5/plans/v0.5.2-alpha.md)" in todos
    assert "[omega]: archives/v0/v0.5/plans/v0.5.10-omega.md" in todos
    assert repo.read("scripts/tool.py") == f'LEDGER = "{new}/known-gaps.md"\n'
    assert _git(repo.work, "status", "--porcelain").strip() == ""
    assert _git(repo.work, "log", "-1", "--format=%s").strip() == "docs(archives): archive closed minor v0.5"
    # The record re-froze its members at the archived paths and still verifies.
    state = repo.load(None)
    assert state.forced is None and state.record is not None
    assert {m["plan_path"] for m in state.record["members"]} == {
        f"{new}/plans/v0.5.2-alpha.md", f"{new}/plans/v0.5.10-omega.md"}
    # The source ledger's migration still verifies after its ledger moved.
    assert repo.gaps_minor() == ("met", [])


def test_members_still_resolve_archived_plans(repo: Close) -> None:
    closed_minor(repo)
    assert archive(repo, "--apply").returncode == 0
    out, err, code = repo.members()
    assert code == 1 and out == ["No queued plans in v0.5"]
    assert sorted(err) == ["v0.5.10 status-complete", "v0.5.2 status-complete"]
    rels = [p.rel for p in cm.scan_plans(repo.work, 0, 5)]
    assert rels == ["docs/archives/v0/v0.5/plans/v0.5.2-alpha.md", "docs/archives/v0/v0.5/plans/v0.5.10-omega.md"]


def test_archive_minor_predicate_reads_the_integration_branch(repo: Close) -> None:
    closed_minor(repo)
    rctx = repo.rctx()
    assert cm.archive_minor_status(ck, rctx, "v0.5", repo.load(None).record) == "unmet"
    assert archive(repo, "--apply").returncode == 0
    assert cm.archive_minor_status(ck, rctx, "v0.5", repo.load(None).record) == "unmet"  # not merged yet
    _git(repo.work, "checkout", "-q", "develop")
    _git(repo.work, "merge", "-q", "--no-ff", "-m", "close v0.5", "chore/close-v0.5")
    repo.publish("develop")
    assert cm.archive_minor_status(ck, rctx, "v0.5", repo.load(None).record) == "met"
    # BG-3: a minor completes only once archived, so a missing approval is unmet, never n/a.
    assert cm.archive_minor_status(ck, rctx, "v0.5", None) == "unmet"


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        ("open-gap", "REFUSED: open-gap (v0.5#WN-8)"),
        ("not-finalized", f"REFUSED: register-not-finalized ({GAPS05})"),
        ("unreleased", "REFUSED: unreleased-member (v0.5.10)"),
        ("queued-outside", "REFUSED: queued-plan-outside-members (v0.5.20)"),
        ("unchecked", "REFUSED: unchecked-task (v0.5.2)"),
        ("worktree", "REFUSED: live-worktree (feat/v0.5.2-alpha)"),
        ("remote-branch", "REFUSED: unmerged-branch-touches-tree (fix/touch-v0.5)"),
        ("dirty", "REFUSED: dirty-worktree (commit or stash first; rollback needs a clean tree)"),
        ("branch", "REFUSED: not-on-closing-branch (main)"),
        ("collision", "REFUSED: archive-collision (docs/archives/v0/v0.5/known-gaps.md)"),
    ],
)
def test_archive_refusals(repo: Close, tmp_path: Path, setup: str, expected: str) -> None:
    closed_minor(repo)
    if setup == "open-gap":
        repo.write(GAPS05, repo.read(GAPS05).replace("### Resolved", "#### WN-8: New\n\n### Resolved"))
        repo.commit("open gap")
    elif setup == "not-finalized":
        repo.write(GAPS05, repo.read(GAPS05).replace("**Status**: finalized", "**Status**: released"))
        repo.commit("status")
    elif setup == "unreleased":
        repo.state["releases"].pop("v0.5.10")
        repo.save_state()
    elif setup == "queued-outside":
        repo.plan("v0.5.20", "late", folder=f"{V05}/plans")
        repo.commit("late plan")
    elif setup == "unchecked":
        rel = f"{V05}/plans/v0.5.2-alpha.md"
        repo.write(rel, repo.read(rel).replace("- [x] T001", "- [ ] T001"))
        repo.commit("untick")
    elif setup == "worktree":
        _git(repo.work, "worktree", "add", "-q", "-b", "feat/v0.5.2-alpha", str(tmp_path / "wt"))
    elif setup == "remote-branch":
        _git(repo.work, "checkout", "-q", "-b", "fix/touch-v0.5", "main")
        repo.write(f"{V05}/development/late.md", "late\n")
        repo.commit("touch")
        repo.publish("fix/touch-v0.5")
        _git(repo.work, "checkout", "-q", "chore/close-v0.5")
    elif setup == "dirty":
        repo.write("scratch.txt", "uncommitted\n")
    elif setup == "branch":
        _git(repo.work, "checkout", "-q", "main")
        _git(repo.work, "merge", "-q", "chore/close-v0.5")
    elif setup == "collision":
        repo.write("docs/archives/v0/v0.5/known-gaps.md", "old\n")
        repo.commit("collide")
    tree_before = _git(repo.work, "ls-files")
    result = archive(repo, "--apply")
    assert result.returncode == 3, result.stdout + result.stderr
    assert expected in result.stdout.splitlines()
    assert _git(repo.work, "ls-files") == tree_before


def test_archive_without_an_approval_is_not_covered(repo: Close) -> None:
    closed_minor(repo)
    repo.forge(archive=False)
    result = archive(repo, "--apply")
    assert result.returncode == 3 and result.stdout.startswith("REFUSED: approval-not-covered")
    assert (repo.work / V05).is_dir()


def test_failed_link_check_leaves_the_tree_unmoved(repo: Close, tmp_path: Path) -> None:
    closed_minor(repo)
    stub = tmp_path / "broken-checker.py"
    stub.write_text(
        "import json, pathlib, sys\n"
        "if sys.argv[1] == 'baseline':\n"
        "    pathlib.Path(sys.argv[sys.argv.index('--out') + 1]).write_text('')\n"
        "else:\n"
        "    print(json.dumps({'totals': {'newly_broken': 1}})); sys.exit(1)\n",
        encoding="utf-8",
    )
    head = repo.head()
    todos = repo.read("docs/todos.md")
    result = repo.close("archive", "--minor", "v0.5", "--apply", "--link-checker", str(stub))
    assert result.returncode == 3 and result.stdout.strip() == "REFUSED: link-check-failed (1 newly broken)"
    assert (repo.work / V05).is_dir() and not (repo.work / "docs/archives/v0/v0.5").exists()
    assert repo.read("docs/todos.md") == todos and repo.head() == head
    assert _git(repo.work, "status", "--porcelain").strip() == ""


def test_locked_directory_stops_with_the_tree_unmoved(repo: Close, monkeypatch: pytest.MonkeyPatch) -> None:
    closed_minor(repo)
    monkeypatch.setattr(mc, "_git_mv", lambda rctx, src, dst: False)
    args = mc.build_parser().parse_args(
        ["archive", "--minor", "v0.5", "--apply", "--link-checker", str(LINK_CHECKER), "--repo", str(repo.work)]
    )
    with pytest.raises(mc.Refused) as refused:
        mc.cmd_archive(args)
    assert refused.value.line() == f"REFUSED: locked-directory ({V05})"
    assert (repo.work / V05).is_dir()
    assert _git(repo.work, "status", "--porcelain").strip() == ""


def test_archive_merges_into_an_existing_archive_directory(repo: Close) -> None:
    closed_minor(repo)
    repo.write("docs/archives/v0/v0.5/development/old-notes.md", "# Old\n")
    repo.commit("existing archive content")
    result = archive(repo, "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (repo.work / V05).exists()
    assert (repo.work / "docs/archives/v0/v0.5/development/old-notes.md").is_file()
    assert (repo.work / "docs/archives/v0/v0.5/known-gaps.md").is_file()


def test_status_prints_both_predicates(repo: Close) -> None:
    repo.standard()
    repo.forge()
    result = repo.close("status", "--minor", "v0.5")
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["gaps.minor unmet", "archive.minor unmet"]
    assert result.stderr.splitlines() == ["gaps.minor open v0.5#WN-3"]


# --------------------------------------------------------------------------- adversarial review regressions


def test_archive_leaves_urls_code_and_other_archives_byte_exact(repo: Close) -> None:
    closed_minor(repo)
    notes = ("[pinned](https://github.com/acme/demo/blob/0123abc/docs/releases/v0/v0.5/known-gaps.md)\n\n"
             "```bash\ngit log -- docs/releases/v0/v0.5/known-gaps.md\n```\n\n"
             "Inline `docs/releases/v0/v0.5/known-gaps.md` code.\n")
    repo.write("docs/README.md", notes)
    repo.write("docs/archives/v0/v0.4/development/capture.json", '{"path": "docs/releases/v0/v0.5/known-gaps.md"}\n')
    repo.write("docs/archives/v0/v0.4/development/table.csv", "path\ndocs/releases/v0/v0.5/x\n")
    repo.write("docs/archives/v0/v0.4/development/notes.md", "Earlier: docs/releases/v0/v0.5/known-gaps.md\n")
    repo.write("CHANGELOG.md", "Moved docs/releases/v0/v0.5/known-gaps.md.\n")
    repo.commit("more refs")
    result = archive(repo, "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    assert repo.read("docs/README.md") == notes
    assert repo.read("docs/archives/v0/v0.4/development/capture.json") == '{"path": "docs/releases/v0/v0.5/known-gaps.md"}\n'
    assert repo.read("docs/archives/v0/v0.4/development/table.csv") == "path\ndocs/releases/v0/v0.5/x\n"
    assert repo.read("docs/archives/v0/v0.4/development/notes.md") == "Earlier: docs/releases/v0/v0.5/known-gaps.md\n"
    assert repo.read("CHANGELOG.md") == "Moved docs/releases/v0/v0.5/known-gaps.md.\n"


def test_a_failure_mid_repair_restores_the_tree(repo: Close, monkeypatch: pytest.MonkeyPatch) -> None:
    closed_minor(repo)
    real = mc._write_atomic
    calls = {"n": 0}

    def flaky(path: Path, text: str) -> None:
        calls["n"] += 1
        if calls["n"] == 2:
            raise PermissionError("locked by another process")
        real(path, text)

    monkeypatch.setattr(mc, "_write_atomic", flaky)
    head = repo.head()
    args = mc.build_parser().parse_args(
        ["archive", "--minor", "v0.5", "--apply", "--link-checker", str(LINK_CHECKER), "--repo", str(repo.work)]
    )
    with pytest.raises(mc.Refused) as refused:
        mc.cmd_archive(args)
    assert refused.value.line() == "REFUSED: rolled-back (PermissionError)"
    assert (repo.work / V05).is_dir() and not (repo.work / "docs/archives/v0/v0.5").exists()
    assert repo.head() == head
    assert _git(repo.work, "status", "--porcelain") == ""


def test_confirmed_cannot_override_a_record_without_archive_minor(repo: Close) -> None:
    closed_minor(repo)
    repo.forge(archive=False)
    result = archive(repo, "--apply", "--confirmed")
    assert result.returncode == 3
    assert result.stdout.strip() == "REFUSED: approval-not-covered (the minor record does not carry archive-minor)"
    assert (repo.work / V05).is_dir()
    assert repo.load(None).forced is None  # the record still verifies


def test_archive_refuses_to_rewrite_a_plan_another_live_run_froze(repo: Close) -> None:
    closed_minor(repo)
    _git(repo.work, "checkout", "-q", "main")
    repo.forge(token="v0.6", bound=())
    _git(repo.work, "checkout", "-q", "chore/close-v0.5")
    result = archive(repo, "--apply")
    assert result.returncode == 3
    assert f"REFUSED: plan-bound-by-another-run ({V06}/plans/v0.6.0-gamma.md)" in result.stdout.splitlines()
    assert (repo.work / V05).is_dir()


def test_register_status_and_zero_line_are_read_from_the_header_only(repo: Close) -> None:
    closed_minor(repo)
    text = repo.read(GAPS05)
    text = text.replace("**Status**: finalized", "**Status**: released").replace("**Open items**: 0\n", "")
    text += "\n## Notes\n\n**Status**: finalized\n**Open items**: 0\n"
    repo.write(GAPS05, text)
    repo.commit("status quoted below the header")
    result = archive(repo, "--apply")
    assert result.returncode == 3
    lines = result.stdout.splitlines()
    assert f"REFUSED: register-not-finalized ({GAPS05})" in lines
    assert f"REFUSED: open-items-not-zero ({GAPS05})" in lines


@pytest.mark.parametrize("ending", ["-->", "--!>"], ids=["standard-end", "bang-end"])
@pytest.mark.parametrize("hidden", [False, True], ids=["visible-provenance", "hidden-provenance"])
def test_migration_comment_endings_preserve_visible_only_provenance(repo: Close, ending: str, hidden: bool) -> None:
    """Both HTML endings close comments; a marker inside either comment is never proof."""
    repo.standard(RETAINED_WARNING)
    repo.forge()
    open_source = repo.read(GAPS05)
    assert repo.migrate().returncode == 0
    migrated_source = repo.read(GAPS05)
    provenance = "- **Migrated from**: v0.5#WN-3 on 2026-09-29 (reason: vendor-feature)"
    target = repo.read(GAPS06)
    assert target.count(provenance) == 1
    replacement = ("<!--\n" + provenance + "\n" + ending) if hidden else ("<!-- retained documentation\n" + ending + "\n" + provenance)
    repo.write(GAPS06, target.replace(provenance, replacement))
    repo.write(GAPS05, open_source)  # The generated destination survived a lost source write.
    before = [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)]
    result = repo.migrate()
    if hidden:
        assert result.returncode == 3 and result.stdout.startswith("REFUSED: migration-provenance-hidden "), result.stdout + result.stderr
        assert [(repo.work / rel).read_bytes() for rel in (GAPS05, GAPS06)] == before
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "v0.6#WN-1" in result.stdout
        assert (repo.work / GAPS06).read_bytes() == before[1]
    repo.write(GAPS05, migrated_source)
    status, notices = repo.gaps_minor()
    assert status == ("unmet" if hidden else "met"), notices
    if hidden:
        assert "gaps.minor migration v0.5#WN-3 migration-provenance-hidden" in notices
