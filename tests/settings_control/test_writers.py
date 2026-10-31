"""Lossless, atomic writers (v4.14.6 Phase 3, T018): one case per failure mode.

Every test writes inside `tmp_path`. No real tool configuration is read or written.
"""
from __future__ import annotations

import json
import os
import random
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lib.settings_control import writers as w

NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
HIGH = ("modelSettings", "claude-opus-5-5", "effortLevel")

JSON_SOURCES = {
    "pretty": '{\n  "model": "opus",\n  "permissions": {\n    "allow": [\n      "Bash(ls:*)",\n      "Read"\n    ]\n  }\n}\n',
    "compact": '{"model":"opus","permissions":{"allow":["Bash(ls:*)","Read"]}}',
    "tabs-crlf": '{\r\n\t"model": "opus",\r\n\t"permissions": {\r\n\t\t"allow": ["x", "y"]\r\n\t}\r\n}\r\n',
    "empty-object": "{}\n",
    "spaced": '{ "model" : "opus" , "env" : { "A" : "1" } , "list" : [ 1 , 2 ] }',
    "four-space": '{\n    "env": {"KEEP": "yes"},\n    "n": 1.50,\n    "u": "caf\u00e9 \\u00e9"\n}',
    "bom": '\ufeff{\n  "model": "opus"\n}\n',
}
KEY_PATHS = [HIGH, ("permissions", "defaultMode"), ("model",), ("env", "CLAUDE_CODE_EFFORT_LEVEL"), ("a", "b", "c", "d")]


def _put(path: Path, text: str) -> bytes:
    path.write_bytes(text.encode("utf-8"))
    return path.read_bytes()


def _undo(path: Path, change: w.Change, writer=w.write_json_keys) -> None:
    value = change.previous if change.previous_present else w.ABSENT
    writer(path, [w.Edit(change.key_path, value, created_depth=change.created_depth)])


# --- Round trip --------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(JSON_SOURCES))
@pytest.mark.parametrize("key_path", KEY_PATHS, ids=lambda p: ".".join(p))
def test_json_set_then_reset_is_byte_identical(tmp_path: Path, name: str, key_path: tuple[str, ...]) -> None:
    target = tmp_path / "settings.json"
    before = _put(target, JSON_SOURCES[name])

    plan = w.write_json_keys(target, [w.Edit(key_path, "high")])
    assert plan.changes[0].new == "high"
    changed = json.loads(target.read_bytes().decode("utf-8-sig"))
    assert w.lookup(changed, key_path) == (True, "high")
    _undo(target, plan.changes[0])

    assert target.read_bytes() == before


def test_json_unrelated_text_is_untouched_by_a_set(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    source = '{\n  "permissions": {\n    "allow": ["a",   "b"]\n  },\n  "model":   "opus"\n}\n'
    _put(target, source)

    w.write_json_key(target, ("effortLevel",), "high")

    after = target.read_text(encoding="utf-8")
    assert after.startswith(source[: source.rindex("\n}")])
    assert '["a",   "b"]' in after and '"model":   "opus"' in after


@pytest.mark.parametrize("fmt_writer", ["json", "toml"])
def test_repeated_set_keeps_the_first_previous_value_and_reset_restores_it(tmp_path: Path, fmt_writer: str) -> None:
    target = tmp_path / ("c.toml" if fmt_writer == "toml" else "c.json")
    writer = w.write_toml_keys if fmt_writer == "toml" else w.write_json_keys
    original = 'model = "x"\nkey = "orig"\n' if fmt_writer == "toml" else '{\n  "key": "orig"\n}\n'
    before = _put(target, original)

    first = writer(target, [w.Edit(("key",), "one")]).changes[0]
    second = writer(target, [w.Edit(("key",), "two")]).changes[0]

    assert (first.previous, second.previous) == ("orig", "one")
    writer(target, [w.Edit(("key",), first.previous)])
    assert target.read_bytes() == before


def test_toml_round_trip_keeps_comments_for_a_commented_config(tmp_path: Path) -> None:
    target = tmp_path / "config.toml"
    source = (
        '# Codex config\nmodel = "gpt-6.1-sol"   # chosen by hand\napproval_policy = "on-request"\n\n'
        '[windows]\nsandbox = "unelevated"  # needed on Windows\n\n# features\n[features]\nhooks = true\n'
    )
    before = _put(target, source)

    plan = w.write_toml_keys(target, [w.Edit(("sandbox_mode",), "workspace-write"), w.Edit(("approval_policy",), "never")])
    text = target.read_text(encoding="utf-8")
    assert '# chosen by hand' in text and '# needed on Windows' in text and 'approval_policy = "never"' in text
    assert text.index("sandbox_mode") < text.index("[windows]")

    for change in reversed(plan.changes):
        _undo(target, change, w.write_toml_keys)
    assert target.read_bytes() == before


def test_toml_keeps_crlf_newlines(tmp_path: Path) -> None:
    target = tmp_path / "config.toml"
    _put(target, 'model = "x"\r\n\r\n[a]\r\nx = 1\r\n')

    w.write_toml_key(target, ("sandbox_mode",), "workspace-write")

    raw = target.read_bytes()
    assert raw.count(b"\n") == raw.count(b"\r\n")


# --- Malformed or absent input ----------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"a": 1,}', "not valid JSON (line 1)"),
        ("{\n  \"a\": 1\n  \"b\": 2\n}", "not valid JSON (line 3)"),
        ("", "not valid JSON"),
        ("[1, 2]", "not a JSON object"),
        ('{"a": 1, "a": 2}', "duplicate key"),
        ('{"a": NaN}', "not valid JSON"),
    ],
)
def test_a_malformed_json_file_is_refused_untouched(tmp_path: Path, text: str, expected: str) -> None:
    target = tmp_path / "settings.json"
    before = _put(target, text)

    with pytest.raises(w.WriterRefusal, match=re.escape(expected)):
        w.write_json_key(target, ("model",), "opus")

    assert target.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


def test_a_malformed_toml_file_is_refused_with_its_line(tmp_path: Path) -> None:
    target = tmp_path / "config.toml"
    before = _put(target, 'model = "x"\nbroken = \n')

    with pytest.raises(w.WriterRefusal, match=r"not valid TOML \(line 2\)"):
        w.write_toml_key(target, ("sandbox_mode",), "workspace-write")

    assert target.read_bytes() == before


def test_invalid_utf8_and_a_directory_are_refused(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    target.write_bytes(b'{"a": "\xff"}')
    with pytest.raises(w.WriterRefusal, match="not valid UTF-8"):
        w.write_json_key(target, ("model",), "opus")
    folder = tmp_path / "folder.json"
    folder.mkdir()
    with pytest.raises(w.WriterRefusal, match="not a regular file"):
        w.write_json_key(folder, ("model",), "opus")


def test_a_scalar_parent_refuses_instead_of_replacing_it(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    before = _put(target, '{"permissions": "locked"}\n')

    with pytest.raises(w.WriterRefusal, match="permissions is not an object"):
        w.write_json_key(target, ("permissions", "defaultMode"), "default")

    assert target.read_bytes() == before


@pytest.mark.parametrize("fmt", ["json", "toml"])
def test_an_absent_file_is_created_with_only_the_key_and_reported(tmp_path: Path, fmt: str) -> None:
    target = tmp_path / "new" / f"file.{fmt}"
    writer = w.write_toml_keys if fmt == "toml" else w.write_json_keys

    plan = writer(target, [w.Edit(("model",), "opus")])

    assert plan.file_created and plan.changes[0].previous_present is False
    expected = {"model": "opus"}
    parsed = json.loads(target.read_text(encoding="utf-8")) if fmt == "json" else __import__("tomllib").loads(target.read_text(encoding="utf-8"))
    assert parsed == expected


def test_a_created_file_with_nested_keys_is_valid_json(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"

    w.write_json_keys(target, [w.Edit(HIGH, "high"), w.Edit(("model",), "opus")])

    assert json.loads(target.read_text(encoding="utf-8")) == {"modelSettings": {"claude-opus-5-5": {"effortLevel": "high"}}, "model": "opus"}


def test_missing_tomlkit_refuses_a_toml_write_with_an_install_hint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "config.toml"
    before = _put(target, 'model = "x"\n')
    monkeypatch.setitem(sys.modules, "tomlkit", None)

    with pytest.raises(w.WriterRefusal, match="pip install tomlkit"):
        w.write_toml_key(target, ("sandbox_mode",), "workspace-write")

    assert target.read_bytes() == before


# --- Conflicting operations -------------------------------------------------


def test_a_file_changed_between_read_and_commit_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    _put(target, '{\n  "a": 1\n}\n')
    plan = w.plan_edits(w.load(target, "json"), [w.Edit(("model",), "opus")])
    changed = _put(target, '{\n  "a": 1,\n  "user": "edit"\n}\n')

    with pytest.raises(w.WriterRefusal, match="changed while Nexus-Hub was preparing"):
        w.commit(plan)

    assert target.read_bytes() == changed


def test_a_file_changed_during_the_write_is_refused_and_leaves_no_temp_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "settings.json"
    _put(target, '{"a": 1}')
    plan = w.plan_edits(w.load(target, "json"), [w.Edit(("model",), "opus")])
    real_write = w._write_temp

    def write_then_interfere(parent: Path, payload: bytes) -> Path:
        temp = real_write(parent, payload)
        target.write_bytes(b'{"a": 1, "user": true}')
        return temp

    monkeypatch.setattr(w, "_write_temp", write_then_interfere)

    with pytest.raises(w.WriterRefusal, match="changed while Nexus-Hub was writing"):
        w.commit(plan)

    assert target.read_bytes() == b'{"a": 1, "user": true}'
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


def test_a_failed_replace_never_leaves_a_partial_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "settings.json"
    before = _put(target, '{"a": 1}')
    monkeypatch.setattr(os, "replace", lambda *_: (_ for _ in ()).throw(PermissionError(13, "denied")))

    with pytest.raises(w.WriterRefusal, match="could not be written"):
        w.write_json_key(target, ("model",), "opus")

    assert target.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]


def test_a_file_that_appears_during_creation_is_not_overwritten(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    plan = w.plan_edits(w.load(target, "json"), [w.Edit(("model",), "opus")])
    target.write_text('{"user": true}', encoding="utf-8")

    with pytest.raises(w.WriterRefusal, match="changed while Nexus-Hub was preparing"):
        w.commit(plan)

    assert json.loads(target.read_text(encoding="utf-8")) == {"user": True}


# --- File properties ---------------------------------------------------------


def _symlink(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except OSError as exc:  # Windows without Developer Mode cannot create links
        pytest.skip(f"symlinks cannot be created here: {exc}")


def test_a_symlinked_file_is_written_through_and_the_link_survives(tmp_path: Path) -> None:
    real = tmp_path / "dotfiles" / "settings.json"
    real.parent.mkdir()
    before = _put(real, '{\n  "permissions": {"allow": ["Read"]}\n}\n')
    link = tmp_path / "settings.json"
    _symlink(link, real)

    w.write_json_key(link, ("model",), "opus")

    assert link.is_symlink() and link.resolve() == real.resolve()
    assert json.loads(real.read_text(encoding="utf-8")) == {"permissions": {"allow": ["Read"]}, "model": "opus"}
    assert [p.name for p in real.parent.iterdir()] == ["settings.json"]
    assert before != real.read_bytes()


def test_a_resolved_link_is_written_beside_the_real_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Link resolution is `os.path.realpath`; emulate it so this holds on hosts that cannot create links."""
    real = tmp_path / "dotfiles" / "settings.json"
    real.parent.mkdir()
    _put(real, '{"a": 1}\n')
    link = tmp_path / "settings.json"
    seen: list[Path] = []
    original = w._write_temp
    monkeypatch.setattr(w.os.path, "realpath", lambda p: str(real) if Path(p) == link else str(p))
    monkeypatch.setattr(w, "_write_temp", lambda parent, payload: (seen.append(parent), original(parent, payload))[1])

    w.write_json_key(link, ("model",), "opus")

    assert seen == [real.parent] and not link.exists()
    assert json.loads(real.read_text(encoding="utf-8")) == {"a": 1, "model": "opus"}


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits")
def test_mode_bits_are_preserved(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    _put(target, '{"a": 1}')
    target.chmod(0o640)

    w.write_json_key(target, ("model",), "opus")

    assert stat.S_IMODE(target.stat().st_mode) == 0o640


@pytest.mark.skipif(os.name != "nt", reason="Windows access lists")
def test_a_protected_owner_only_acl_is_preserved(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    _put(target, '{"a": 1}')
    assert w.owner_only_windows(target)

    def acl() -> str:
        done = subprocess.run(["icacls", str(target)], capture_output=True, text=True, creationflags=NOWIN, check=True)
        return done.stdout.replace(str(target), "").strip().splitlines()[0]

    before = acl()
    w.write_json_key(target, ("model",), "opus")

    assert acl() == before and "OWNER RIGHTS" in before


@pytest.mark.parametrize("name", sorted(JSON_SOURCES))
def test_indent_newline_and_bom_are_preserved(tmp_path: Path, name: str) -> None:
    target = tmp_path / "settings.json"
    source = JSON_SOURCES[name]
    raw = _put(target, source)

    w.write_json_key(target, ("added",), "yes")

    after = target.read_bytes()
    assert after.startswith(b"\xef\xbb\xbf") == raw.startswith(b"\xef\xbb\xbf")
    assert (b"\r\n" in after) == (b"\r\n" in raw)
    if name == "tabs-crlf":
        assert b'\t"added": "yes"' in after
    if name == "four-space":
        assert b'    "added": "yes"' in after


# --- Keys --------------------------------------------------------------------


def test_a_dotted_model_id_is_one_key_never_split(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    _put(target, "{}\n")

    w.write_json_key(target, ("modelSettings", "claude-3.5-sonnet.v2", "effortLevel"), "high")

    assert json.loads(target.read_text(encoding="utf-8")) == {"modelSettings": {"claude-3.5-sonnet.v2": {"effortLevel": "high"}}}


@pytest.mark.parametrize("segment", ["", "has space", "../escape", 'quo"te', "new\nline", "-leading", "x" * 129, 7])
def test_an_invalid_key_segment_is_refused(tmp_path: Path, segment: object) -> None:
    target = tmp_path / "settings.json"
    before = _put(target, "{}\n")

    with pytest.raises(w.WriterRefusal, match="not a valid name"):
        w.write_json_key(target, ("modelSettings", segment, "effortLevel"), "high")  # type: ignore[arg-type]

    assert target.read_bytes() == before


def test_a_no_op_edit_does_not_reformat_the_file(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    before = _put(target, '{ "model" : "opus" ,\n "b":[1,2] }')

    plan = w.write_json_keys(target, [w.Edit(("model",), "opus")])

    assert plan.changed is False and target.read_bytes() == before


def test_removing_an_absent_key_changes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    before = _put(target, '{"a": 1}\n')

    plan = w.write_json_keys(target, [w.Edit(("env", "X"), w.ABSENT)])

    assert plan.changed is False and target.read_bytes() == before


def test_a_value_that_json_cannot_hold_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    before = _put(target, "{}\n")

    with pytest.raises(w.WriterRefusal, match="cannot be written"):
        w.write_json_key(target, ("n",), float("nan"))

    assert target.read_bytes() == before


# --- Randomized lossless check ----------------------------------------------


def _random_json(rng: random.Random, depth: int = 0) -> object:
    roll = rng.random()
    if depth > 2 or roll < 0.4:
        return rng.choice([1, 2.5, True, None, "text", "caf\u00e9", ""])
    if roll < 0.6:
        return [_random_json(rng, depth + 1) for _ in range(rng.randint(0, 3))]
    return {f"k{i}": _random_json(rng, depth + 1) for i in range(rng.randint(0, 3))}


def _random_text(rng: random.Random, value: object) -> str:
    style = rng.choice(["pretty2", "pretty4", "tabs", "compact", "spaced"])
    if style == "compact":
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    if style == "spaced":
        return json.dumps(value, separators=(" , ", " : "), ensure_ascii=False)
    indent = {"pretty2": 2, "pretty4": 4, "tabs": "\t"}[style]
    return json.dumps(value, indent=indent, ensure_ascii=False) + rng.choice(["", "\n"])


def test_random_documents_round_trip_and_keep_unrelated_data(tmp_path: Path) -> None:
    rng = random.Random(20261030)
    target = tmp_path / "settings.json"
    attempted = exact = 0
    for _ in range(300):
        value = {"top": _random_json(rng), "env": {"A": "1"}, "x": _random_json(rng)}
        source = _random_text(rng, value)
        before = _put(target, source)
        path = rng.choice([("model",), ("env", "NEW"), ("deep", "er", "key"), ("top", "inner")])
        try:
            plan = w.write_json_keys(target, [w.Edit(path, "v")])
        except w.WriterRefusal as exc:
            assert "is not an object" in str(exc)  # a scalar or list sits on the path
            assert target.read_bytes() == before
            continue
        attempted += 1
        produced = json.loads(target.read_text(encoding="utf-8"))
        expected = json.loads(source)
        node = expected
        for part in path[:-1]:
            node = node.setdefault(part, {})
        node[path[-1]] = "v"
        assert produced == expected
        _undo(target, plan.changes[0])
        exact += target.read_bytes() == before
        assert json.loads(target.read_text(encoding="utf-8")) == json.loads(source)
    assert attempted > 150 and exact == attempted


# --- Exact undo of a removal (restore hint) -----------------------------------


@pytest.mark.parametrize("victim", ["first", "middle", "last"])
@pytest.mark.parametrize("layout", ["pretty", "compact", "crlf"])
def test_a_removed_member_is_put_back_in_place_byte_for_byte(tmp_path: Path, victim: str, layout: str) -> None:
    body = {"first": ["b", "c"], "middle": ["a", "c"], "last": ["a", "b"]}[victim]
    keys = {"first": "a", "middle": "b", "last": "c"}[victim]
    members = [("a", "1"), ("b", '"two"'), ("c", "[3, 4]")]
    if layout == "compact":
        text = '{"env":{' + ",".join(f'"{k}":{v}' for k, v in members) + '},"z":1}'
    else:
        nl = "\r\n" if layout == "crlf" else "\n"
        inner = ("," + nl).join(f'    "{k}": {v}' for k, v in members)
        text = "{" + nl + '  "env": {' + nl + inner + nl + "  }," + nl + '  "z": 1' + nl + "}" + nl
    target = tmp_path / "settings.json"
    before = _put(target, text)
    assert body and keys

    removed = w.write_json_keys(target, [w.Edit(("env", keys), w.ABSENT)]).changes[0]
    assert removed.removal is not None and keys not in json.loads(target.read_bytes())["env"]
    w.write_json_keys(target, [w.Edit(("env", keys), removed.previous, restore=removed.removal)])

    assert target.read_bytes() == before


def test_a_sole_member_removal_is_undone_exactly(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    before = _put(target, '{\n  "permissions": { "disable": "yes" },\n  "z": 1\n}\n')

    removed = w.write_json_keys(target, [w.Edit(("permissions", "disable"), w.ABSENT)]).changes[0]
    w.write_json_keys(target, [w.Edit(("permissions", "disable"), "yes", restore=removed.removal)])

    assert target.read_bytes() == before


def test_a_hint_whose_neighbor_moved_falls_back_to_a_plain_insertion(tmp_path: Path) -> None:
    target = tmp_path / "settings.json"
    _put(target, '{"env": {"a": 1, "b": 2, "c": 3}}')
    removed = w.write_json_keys(target, [w.Edit(("env", "b"), w.ABSENT)]).changes[0]
    _put(target, '{"env": {"a": 1, "x": 9}}')

    w.write_json_keys(target, [w.Edit(("env", "b"), 2, restore=removed.removal)])

    assert json.loads(target.read_text(encoding="utf-8")) == {"env": {"a": 1, "x": 9, "b": 2}}


@pytest.mark.parametrize(
    "hint",
    [{"kind": "before", "text": ', "evil": 1,', "anchor": "c"}, {"kind": "nope", "text": "x"}, {"kind": "tail", "text": ""}, "text", {"kind": "whole", "text": "{" * 70000}],
)
def test_a_garbled_or_hostile_hint_never_corrupts_the_file(tmp_path: Path, hint: object) -> None:
    target = tmp_path / "settings.json"
    _put(target, '{"env": {"a": 1, "c": 3}}')

    w.write_json_keys(target, [w.Edit(("env", "b"), 2, restore=hint)])  # type: ignore[arg-type]

    assert json.loads(target.read_text(encoding="utf-8")) == {"env": {"a": 1, "c": 3, "b": 2}}
