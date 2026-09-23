#!/usr/bin/env python3
"""Install and verify portable user-attribution Git hooks without rewriting history."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

HOOKS = [
    "applypatch-msg",
    "pre-applypatch",
    "post-applypatch",
    "pre-commit",
    "pre-merge-commit",
    "prepare-commit-msg",
    "commit-msg",
    "post-commit",
    "pre-rebase",
    "post-checkout",
    "post-merge",
    "pre-push",
    "pre-receive",
    "update",
    "proc-receive",
    "post-receive",
    "post-update",
    "reference-transaction",
    "push-to-checkout",
    "pre-auto-gc",
    "post-rewrite",
    "sendemail-validate",
    "fsmonitor-watchman",
    "p4-changelist",
    "p4-prepare-changelist",
    "p4-post-changelist",
    "p4-pre-submit",
    "post-index-change",
]
AGENT = re.compile(
    r"(?:^|[^a-z0-9])(?:claude|anthropic|codex|openai|cursor(?:agent)?|"
    r"copilot|gemini|antigravity|aider|windsurf|devin|dependabot|renovate|"
    r"chatgpt|gpt|deepseek|qwen|kimi|opencode|openclaw|hermes|"
    r"github-actions|bot)(?:$|[^a-z0-9])|\[bot\]",
    re.IGNORECASE,
)
TRAILER = re.compile(
    r"^\s*(?:co-authored-by|made-with|generated-by|ai-generated|claude-session)\s*:",
    re.IGNORECASE | re.MULTILINE,
)


class GuardError(Exception):
    """An attribution operation could not be verified."""


def git(*args: str, ok: tuple[int, ...] = (0,), input: bytes | None = None) -> str:
    result = subprocess.run(
        ["git", "--no-replace-objects", *args],
        input=input,
        capture_output=True,
        check=False,
    )
    if result.returncode not in ok:
        raise GuardError(
            result.stderr.decode("utf-8", "replace").strip() or "Git command failed"
        )
    return result.stdout.decode("utf-8", "replace").strip()


def human(name: str, email: str) -> None:
    if not name.strip() or not re.fullmatch(r"[^\s<>@]+@[^\s<>@]+", email):
        raise GuardError(
            "Set your own git user.name and user.email before creating contributions."
        )

    # Product words inside a person's full name or mailbox are not evidence
    # of agent authorship (for example Claude Martin or claude.martin).
    def agent_label(value: str) -> bool:
        label = re.sub(
            r"(?:[-_ ]*(?:code|agent|bot|assistant|cli|ide))+$",
            "",
            value.strip(),
            flags=re.IGNORECASE,
        )
        return bool(AGENT.fullmatch(value.strip()) or AGENT.fullmatch(label)) or (
            label.casefold() == "ai"
        )

    mailbox, _, domain = email.casefold().partition("@")
    vendor_bot = mailbox in {"noreply", "no-reply", "bot", "agent"} and domain in {
        "anthropic.com",
        "claude.ai",
        "openai.com",
        "chatgpt.com",
        "cursor.com",
        "cursor.sh",
        "github.com",
    }
    if (
        any(c in name + email for c in "\r\n\x00<>")
        or "[bot]" in (name + email).casefold()
        or agent_label(name)
        or agent_label(mailbox.rsplit("+", 1)[-1])
        or vendor_bot
    ):
        raise GuardError(
            "Agent/bot identities are not permitted; configure your own Git identity."
        )


def identity() -> tuple[str, str]:
    name = git("config", "--get", "user.name", ok=(0, 1))
    email = git("config", "--get", "user.email", ok=(0, 1))
    human(name, email)
    return name, email


def parsed_ident(value: str) -> tuple[str, str]:
    match = re.fullmatch(r"(.*?) <([^<>]+)> \d+ [+-]\d{4}", value)
    if not match:
        raise GuardError("Cannot verify Git identity metadata.")
    return match[1], match[2]


def pending() -> None:
    expected = identity()
    committer = parsed_ident(git("var", "GIT_COMMITTER_IDENT"))
    author = parsed_ident(git("var", "GIT_AUTHOR_IDENT"))
    human(*author)
    if committer != expected:
        raise GuardError(
            "Committer differs from your configured Git identity; remove identity overrides."
        )
    # Replaying a human's existing commit preserves its author. New work and
    # ordinary amend operations must use the configured user as author.
    replay = any(
        Path(git("rev-parse", "--git-path", name)).exists()
        for name in ("CHERRY_PICK_HEAD", "rebase-merge", "rebase-apply")
    )
    if author != expected and not replay:
        raise GuardError("Author differs from your configured Git identity.")


def message(value: str) -> None:
    if TRAILER.search(value):
        raise GuardError(
            "Remove attribution trailers (including Co-Authored-By and Made-With)."
        )
    for line in value.splitlines():
        if re.match(
            r"^\s*(?:[^\w\s]+\s*)?(?:generated|made|authored|written)\s+(?:by|with)\b",
            line,
            re.IGNORECASE,
        ) and (AGENT.search(line) or re.search(r"\bAI\b", line, re.IGNORECASE)):
            raise GuardError("Remove the agent-generated attribution footer.")


def scan_push(payload: bytes, remote_url: str) -> None:
    identity()
    remote_commits: list[str] | None = None
    for line in payload.decode("utf-8", "strict").splitlines():
        fields = line.split()
        if len(fields) != 4:
            raise GuardError("Cannot verify malformed pre-push update.")
        _local_ref, new, remote_ref, old = fields
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", new) or not re.fullmatch(
            r"[0-9a-f]{40}|[0-9a-f]{64}", old
        ):
            raise GuardError("Cannot verify push object IDs.")
        if not new.strip("0"):
            continue
        kind = git("cat-file", "-t", new)
        if remote_ref.startswith("refs/tags/") and kind == "tag":
            raw = git("cat-file", "tag", new)
            header, _, body = raw.partition("\n\n")
            tagger = next(
                (x[7:] for x in header.splitlines() if x.startswith("tagger ")), ""
            )
            if parsed_ident(tagger) != identity():
                raise GuardError(
                    "Outgoing tag was not created by your configured Git identity."
                )
            message(body)
        # A tag to a tree/blob has no commits; its annotated metadata was checked.
        commit = subprocess.run(
            ["git", "rev-parse", "--verify", new + "^{commit}"],
            capture_output=True,
            check=False,
        )
        if commit.returncode:
            if remote_ref.startswith("refs/tags/"):
                continue
            raise GuardError("Outgoing branch does not resolve to a commit.")
        revs = [new]
        if old.strip("0"):
            git("cat-file", "-e", old)  # missing remote baseline must not silently pass
            revs.append("^" + old)
        else:
            # A new ref has no old-object baseline. Exclude only commits
            # advertised by this push destination, never refs from other remotes
            # or stale local tracking refs.
            if remote_commits is None:
                remote_commits = []
                seen_objects: set[str] = set()
                for line in git("ls-remote", "--refs", remote_url).splitlines():
                    fields = line.split("\t")
                    if len(fields) != 2 or not re.fullmatch(
                        r"[0-9a-f]{40}|[0-9a-f]{64}", fields[0]
                    ):
                        raise GuardError("Cannot verify push destination refs.")
                    if fields[0] in seen_objects:
                        continue
                    seen_objects.add(fields[0])
                    resolved = git(
                        "rev-parse", "--verify", fields[0] + "^{commit}", ok=(0, 1, 128)
                    )
                    if resolved:
                        remote_commits.append(resolved)
            revs.extend("^" + commit for commit in remote_commits)
        records = git(
            "log",
            "--stdin",
            "--format=%an%x00%ae%x00%cn%x00%ce%x00%B%x00",
            input=("\n".join(revs) + "\n").encode("ascii"),
        ).split("\x00")
        for index in range(0, len(records) - 1, 5):
            record = records[index : index + 5]
            if len(record) != 5:
                raise GuardError("Cannot parse outgoing commit metadata.")
            an, ae, cn, ce, body = record
            human(an.lstrip("\n"), ae)
            # GitHub records its service as committer for human-authored web
            # operations. This does not make it an author or an AI contributor.
            if (cn, ce) != ("GitHub", "noreply@github.com"):
                human(cn, ce)
            message(body)


SPECIAL_HOOKS = {"push-to-checkout", "proc-receive", "fsmonitor-watchman"}


def original_directory(
    fallback: str | None, seen: set[Path] | None = None
) -> Path | None:
    if fallback:
        directory = Path(os.path.expanduser(fallback)).resolve()
        state_path = directory / "state.json"
        if state_path.is_file():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("owner") == "nexus-hub-attribution":
                seen = set() if seen is None else seen
                if directory in seen:
                    raise GuardError("Recursive hook chain detected.")
                seen.add(directory)
                return original_directory(state["fallback"], seen)
        return directory
    # init can invoke a hook before rev-parse considers the repository valid.
    common = os.environ.get("GIT_COMMON_DIR") or os.environ.get("GIT_DIR")
    if common:
        commondir = Path(common) / "commondir"
        if commondir.is_file():
            common = str(Path(common) / commondir.read_text().strip())
    else:
        common = git("rev-parse", "--git-common-dir", ok=(0, 128))
    return Path(common) / "hooks" if common else None


def needed_hooks(state: dict) -> list[str]:
    directory = original_directory(state["fallback"])
    return [
        hook
        for hook in HOOKS
        if hook not in SPECIAL_HOOKS
        or (
            directory is not None
            and (directory / hook).is_file()
            and os.access(directory / hook, os.X_OK)
        )
    ]


def check_coverage(root: Path, state: dict) -> None:
    for hook in needed_hooks(state):
        if not (root / hook).is_file():
            raise GuardError(
                f"Existing {hook} needs workspace hook integration. Run nexus-hub attribution install --workspace."
            )


def root_for(scope: str) -> Path:
    if scope == "global":
        return (
            Path(os.environ.get("NEXUS_HUB_HOME", str(Path.home() / ".nexus-hub")))
            / "git-hooks"
        )
    return (
        Path(
            git(
                "rev-parse",
                "--path-format=absolute",
                "--git-dir" if scope == "worktree" else "--git-common-dir",
            )
        )
        / "nexus-attribution-hooks"
    )


def wrapper(script: Path, root: Path, hook: str, python: str | None = None) -> str:
    return (
        "#!/bin/sh\nexec "
        + " ".join(
            shlex.quote(x)
            for x in (
                python or Path(sys.executable).as_posix(),
                script.as_posix(),
                "hook",
                "--hooks-root",
                root.as_posix(),
                hook,
            )
        )
        + ' "$@"\n'
    )


def install(scope: str) -> int:
    if scope == "local":
        probe = subprocess.run(
            ["git", "rev-parse", "--git-dir"], capture_output=True, check=False
        )
        if probe.returncode:
            print(
                "NEEDS SETUP: Workspace is not a Git repository. After git init, run nexus-hub attribution install --workspace."
            )
            return 0
        if git("config", "--bool", "extensions.worktreeConfig", ok=(0, 1)) == "true":
            scope = "worktree"
    root = root_for(scope).resolve()
    state_path = root / "state.json"
    script = Path(__file__).resolve()
    durable_script = root / "guard.py"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        current = git("config", "--" + scope, "--get", "core.hooksPath", ok=(0, 1))
        if current not in (root.as_posix(), state["previous"] or ""):
            raise GuardError(
                "Hook configuration changed since installation; uninstall the old guard before reinstalling."
            )
    else:
        if root.exists() and any(root.iterdir()):
            raise GuardError("Refusing to replace an unrecognized hooks directory.")
        previous = git("config", "--" + scope, "--get", "core.hooksPath", ok=(0, 1))
        fallback = previous
        if not fallback:
            fallback = git(
                "config",
                "--system"
                if scope == "global"
                else ("--local" if scope == "worktree" else "--global"),
                "--get",
                "core.hooksPath",
                ok=(0, 1),
            )
        if not fallback and scope != "global":
            fallback = git("config", "--get", "core.hooksPath", ok=(0, 1))
        state = {
            "owner": "nexus-hub-attribution",
            "scope": scope,
            "previous": previous or None,
            "fallback": fallback or None,
        }
    root.mkdir(parents=True, exist_ok=True)
    if durable_script.is_symlink():
        raise GuardError("Refusing to replace a symlinked attribution guard.")
    selected = needed_hooks(state)
    for hook in set(state.get("hooks", [])) - set(selected):
        path = root / hook
        recognized = {wrapper(durable_script, root, hook, state.get("python"))}
        if "script_sha256" not in state:
            recognized.add(wrapper(script, root, hook, state.get("python")))
        if path.is_file() and path.read_text(encoding="utf-8") in recognized:
            path.unlink()
        elif path.exists():
            raise GuardError(
                f"Obsolete hook was modified: {hook}. Restore it before reinstalling."
            )
    state["hooks"] = selected
    state["python"] = Path(sys.executable).as_posix()
    script_bytes = script.read_bytes()
    durable_script.write_bytes(script_bytes)
    state["script_sha256"] = hashlib.sha256(script_bytes).hexdigest()
    for hook in selected:
        path = root / hook
        path.write_text(
            wrapper(durable_script, root, hook), encoding="utf-8", newline="\n"
        )
        path.chmod(0o755)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    git("config", "--" + scope, "core.hooksPath", root.as_posix())
    if (
        scope != "global"
        and Path(git("config", "--path", "--get", "core.hooksPath")).resolve() != root
    ):
        raise GuardError(
            "A higher-precedence Git configuration overrides activation. Remove that override and reinstall."
        )
    print(f"Attribution hooks installed ({scope}). Existing hooks are chained.")
    try:
        identity()
    except GuardError as exc:
        print(
            f"NEEDS SETUP: {exc} Hooks block contributions until identity is configured."
        )
    return 0


def check() -> int:
    expected = identity()
    pending()
    active = git("config", "--path", "--get", "core.hooksPath", ok=(0, 1))
    if not active:
        raise GuardError(
            "No attribution guard active. Run nexus-hub attribution install --workspace."
        )
    root = Path(active).resolve()
    if not (root / "state.json").is_file():
        raise GuardError(
            "Repository overrides the guard. Run nexus-hub attribution install --workspace."
        )
    state = json.loads((root / "state.json").read_text(encoding="utf-8"))
    durable_script = root / "guard.py"
    if (
        not durable_script.is_file()
        or durable_script.is_symlink()
        or hashlib.sha256(durable_script.read_bytes()).hexdigest()
        != state.get("script_sha256")
    ):
        raise GuardError("Attribution guard missing or modified. Reinstall the guard.")
    source = Path(__file__).resolve()
    if (
        source != durable_script
        and hashlib.sha256(source.read_bytes()).hexdigest() != state["script_sha256"]
    ):
        raise GuardError("Attribution guard version differs. Reinstall the guard.")
    try:
        interpreter = subprocess.run(
            [state["python"], "-c", "pass"],
            capture_output=True,
            check=False,
            timeout=10,
        )
        if interpreter.returncode:
            raise GuardError("Installed Python is unavailable. Reinstall the guard.")
    except (OSError, subprocess.SubprocessError) as exc:
        raise GuardError(
            "Installed Python is unavailable. Reinstall the guard."
        ) from exc
    check_coverage(root, state)
    for hook in state["hooks"]:
        path = root / hook
        if (
            not path.is_file()
            or path.read_text(encoding="utf-8")
            != wrapper(durable_script, root, hook, state["python"])
            or not os.access(path, os.X_OK)
        ):
            raise GuardError(
                f"Attribution hook missing or modified: {hook}. Reinstall the guard."
            )
    print(
        f"VERIFIED: Git hooks active for {expected[0]} <{expected[1]}>. Direct API writes are outside this guard."
    )
    return 0


def uninstall(scope: str) -> int:
    if (
        scope == "local"
        and git("config", "--bool", "extensions.worktreeConfig", ok=(0, 1)) == "true"
    ):
        scope = "worktree"
    root = root_for(scope).resolve()
    state = json.loads((root / "state.json").read_text(encoding="utf-8"))
    if (
        git("config", "--" + scope, "--get", "core.hooksPath", ok=(0, 1))
        != root.as_posix()
    ):
        raise GuardError(
            "Hook configuration changed; refusing to overwrite it during uninstall."
        )
    if state["previous"] is None:
        git("config", "--" + scope, "--unset-all", "core.hooksPath")
    else:
        git("config", "--" + scope, "core.hooksPath", state["previous"])
    # Keep the inert files as recovery evidence; no recursive deletion of hooks.
    print(
        "Attribution hooks disabled; previous hooksPath restored. Hook files retained."
    )
    return 0


def hook_run(root: Path, hook: str, args: list[str]) -> int:
    state = json.loads((root / "state.json").read_text(encoding="utf-8"))
    payload = (
        sys.stdin.buffer.read()
        if hook
        in (
            "pre-push",
            "pre-receive",
            "post-receive",
            "post-rewrite",
            "reference-transaction",
        )
        else None
    )
    if hook in ("pre-commit", "pre-merge-commit", "prepare-commit-msg", "commit-msg"):
        check_coverage(root, state)
        pending()
    if hook == "commit-msg":
        message(Path(args[0]).read_text(encoding="utf-8", errors="replace"))
    if hook == "pre-push":
        check_coverage(root, state)
        if len(args) < 2:
            raise GuardError("Cannot verify push destination.")
        scan_push(payload or b"", args[1])
    directory = original_directory(state["fallback"])
    previous = directory / hook if directory is not None else None
    if previous is not None and previous.resolve() == (root / hook).resolve():
        raise GuardError("Recursive hook chain detected.")
    if previous is not None and previous.is_file() and os.access(previous, os.X_OK):
        # Git hooks are executable files with a shebang; Git for Windows uses sh.
        command = [str(previous.resolve()), *args]
        if os.name == "nt":
            command = ["sh", "-c", 'exec "$@"', "nexus-attribution", *command]
        result = subprocess.run(command, input=payload, check=False).returncode
        if result:
            return result
    if hook == "commit-msg":
        message(Path(args[0]).read_text(encoding="utf-8", errors="replace"))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("install", "uninstall"):
        child = sub.add_parser(name)
        child.add_argument(
            "--workspace",
            action="store_true",
            help="Wrap this repository's hooks instead of global hooks.",
        )
    sub.add_parser("check")
    sub.add_parser(
        "context", help="Emit installed attribution rules for Cursor sessionStart."
    )
    tag = sub.add_parser(
        "tag", help="Create an annotated tag using verified user identity."
    )
    tag.add_argument("name")
    tag.add_argument("-m", "--message", required=True)
    tag.add_argument("--target", default="HEAD")
    hook = sub.add_parser("hook")
    hook.add_argument("--hooks-root", type=Path, required=True)
    hook.add_argument("name", choices=HOOKS)
    hook.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            return install("local" if args.workspace else "global")
        if args.command == "uninstall":
            return uninstall("local" if args.workspace else "global")
        if args.command == "check":
            return check()
        if args.command == "context":
            guide = (
                Path(__file__).resolve().parent.parent
                / "style-guides/git-attribution.md"
            )
            print(json.dumps({"additional_context": guide.read_text(encoding="utf-8")}))
            return 0
        if args.command == "tag":
            check()
            message(args.message)
            git("tag", "-a", "-m", args.message, "--", args.name, args.target)
            return 0
        return hook_run(args.hooks_root, args.name, args.args)
    except (GuardError, OSError, ValueError, KeyError, IndexError) as exc:
        print(f"Attribution BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
