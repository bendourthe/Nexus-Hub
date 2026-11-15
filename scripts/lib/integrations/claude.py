"""Claude Code (Anthropic) integration."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from scripts.lib.installer.markers import DEFAULT_END_MARKER, DEFAULT_START_MARKER

from . import _detection
from .base import InstallContext, MarkdownIntegration, SkillsIntegration, long_path
from .result import FileAction, WriteResult


# Claude's install-time behavioral defaults are DECLARED in
# configs/platform-defaults.json and read here at runtime, so this module holds
# no second copy that can drift out of step with the shipped template. See
# configs/README.md for the schema and the do-not-invent rule.
#
# Candidate locations, in priority order. The installers deliberately do NOT
# copy configs/ into ~/.nexus-hub (they only read configs/permissions/ from a
# checkout), so an installed tree finds the file only when the one-line
# bootstrap materialized a full source tree under ~/.nexus-hub/src.
_DEFAULTS_CANDIDATES = (
    Path(__file__).resolve().parents[3] / "configs" / "platform-defaults.json",
    Path.home() / ".nexus-hub" / "src" / "configs" / "platform-defaults.json",
)

# Offline fallback for installed trees that carry no source checkout. Plain
# absence is the EXPECTED case there, so it degrades silently; only a file that
# exists but cannot be read is worth a note. These literals are kept honest by
# `python scripts/sync_platform_defaults.py --check`, which fails the build when
# they drift away from the declared values.
_FALLBACK_SETTINGS = {
    "attribution": {
        "commit": "",
        "pr": "",
    },
    "effortLevel": "high",
    "model": "opus",
    "env": {
        "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    },
    "modelSettings": {
        "claude-opus-5-5": {
            "effortLevel": "high",
        },
        "claude-sonnet-5-5": {
            "effortLevel": "high",
        },
        "claude-haiku-5-5": {
            "effortLevel": "high",
        },
        "claude-fable-5-1": {
            "effortLevel": "high",
        },
    },
}

_STUB_COMMENT = (
    "Project-local Claude Code settings, generated from configs/platform-defaults.json. "
    "Edit freely; nexus-hub init never overwrites an existing settings.json. "
    "modelSettings supplies High effort for the current canonical model IDs; "
    "effortLevel is the fallback for older models. New IDs require refreshed defaults. "
    "Saved values at this scope are user-owned; higher-priority settings can win. "
    "An existing env.CLAUDE_CODE_EFFORT_LEVEL overrides saved /effort choices; "
    "Nexus-Hub no longer seeds that variable. max is not a settings default. "
    "model selects the Opus session baseline. Remove it to use the account default. "
    "env.CLAUDE_CODE_SUBAGENT_MODEL defaults unpinned custom agents to sonnet; "
    "shipped reasoning-sensitive agents retain opus pins. Explore and Plan need a "
    "separate force flag, which is not seeded. An independent force override can "
    "defeat definition pins. Set the subagent env key to inherit to opt out at this scope."
)


_STUB_PERMISSIONS = {
    "allow": [
        "Read",
        "Glob",
        "Grep",
    ]
}


def _load_declared_settings(candidates=_DEFAULTS_CANDIDATES) -> dict:
    """Return Claude's declared install defaults, degrading to the fallback.

    `nexus-hub init` must never fail because a repo-internal source file is
    absent, so every read problem resolves to the built-in fallback. A file that
    is merely missing is the normal installed-tree case and stays silent; a file
    that exists but cannot be parsed is a real defect and gets one line on
    stderr.
    """
    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            settings = data["platforms"]["claude"]["settings"]
            if not isinstance(settings, dict) or not settings:
                raise ValueError("platforms.claude.settings is empty or not an object")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(
                f"note: {path} is unreadable ({exc}); using built-in Claude defaults.",
                file=sys.stderr,
            )
            break
        return copy.deepcopy(settings)
    return copy.deepcopy(_FALLBACK_SETTINGS)


def build_project_settings_stub(candidates=_DEFAULTS_CANDIDATES) -> dict:
    """Compose the `.claude/settings.json` stub that `nexus-hub init` writes.

    Composed at call time rather than at import time so the declared values are
    read from disk on every run, which is what makes editing
    configs/platform-defaults.json change what init writes with no code edit.
    """
    stub: dict = {"_comment": _STUB_COMMENT}
    stub.update(_load_declared_settings(candidates))
    stub["permissions"] = copy.deepcopy(_STUB_PERMISSIONS)
    return stub


def effort_override_note(settings_file: Path | None = None) -> str | None:
    """Describe a persistent effort override without changing settings or ownership."""
    path = (
        settings_file
        if settings_file is not None
        else Path.home() / ".claude/settings.json"
    )
    if not path.is_file():
        return None
    shown_path = json.dumps(str(path), ensure_ascii=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise TypeError("settings root is not an object")
    except (OSError, ValueError, TypeError):
        return f"[doctor] Claude effort settings are unreadable at {shown_path}; no file was changed."
    env = data.get("env", {})
    if not isinstance(env, dict):
        return f"[doctor] Claude env is not an object at {shown_path}; no file was changed."
    if "CLAUDE_CODE_EFFORT_LEVEL" not in env:
        return None
    value = env["CLAUDE_CODE_EFFORT_LEVEL"]
    # An arbitrary user value may contain secrets or control characters.
    shown = (
        value
        if isinstance(value, str)
        and value in {"low", "medium", "high", "xhigh", "max", "auto"}
        else "an unsupported value"
    )
    owned = False
    record_path = path.parent.parent / ".nexus-hub/core-settings-seeds.json"
    try:
        if record_path.is_symlink():
            raise ValueError("linked record")
        record = json.loads(record_path.read_text(encoding="utf-8-sig"))
        values = record.get("values") if isinstance(record, dict) else None
        removed = record.get("removed", []) if isinstance(record, dict) else None
        valid = (
            isinstance(record, dict)
            and isinstance(record.get("schema_version"), (int, float))
            and not isinstance(record["schema_version"], bool)
            and record["schema_version"] == 1
            and record.get("target") == path.parent.name + "/settings.json"
            and isinstance(values, dict)
            and isinstance(removed, list)
            and all(isinstance(key, str) for key in removed)
        )
        if (
            valid
            and "env.CLAUDE_CODE_EFFORT_LEVEL" in values
            and "env.CLAUDE_CODE_EFFORT_LEVEL" not in removed
        ):
            prior = values["env.CLAUDE_CODE_EFFORT_LEVEL"]
            owned = type(prior) is type(value) and prior == value
    except (OSError, ValueError):
        pass
    if owned:
        return f"[doctor] Nexus-Hub-seeded effort override {shown} overrides saved /effort choices; run nexus-hub upgrade to retire the recorded seed."
    return f"[doctor] env.CLAUDE_CODE_EFFORT_LEVEL={shown} overrides saved /effort choices; Remove only env.CLAUDE_CODE_EFFORT_LEVEL from {shown_path} to use saved per-model effort."


# --------------------------------------------------------------------------
# v4.15.2 -- project instruction capability decision
#
# Claude Code can read a repository's AGENTS.md in place of CLAUDE.md. Whether a
# given project session does so depends on facts an installer can only partly see,
# so the decision is conservative: any unknown, conflicting, or unreadable input
# selects CLAUDE.md, the path that cannot lose instructions. The vendor facts below
# come from code.claude.com/docs/en/memory and /settings (fetched 2026-11-15);
# docs/policy/platform-read-contracts.md records them with their dates.
# --------------------------------------------------------------------------

#: Built-in plugin IDs that carry the `instructionFiles` option. Claude Code v2.1.285+
#: reads either; earlier versions read only the legacy ID.
AGENTS_PLUGIN_IDS = ("cc-plugin-agents-md@builtin", "agents-md@builtin")
#: First version that reads AGENTS.md, and the floor for provider surfaces that read
#: CLAUDE.md only before it (Bedrock, Vertex AI, Foundry, gateways, telemetry off).
FLOOR_GENERAL = (2, 1, 277)
FLOOR_HOSTED = (2, 1, 281)
INSTRUCTION_FILES_VALUES = (
    "claude-md-or-agents-md",
    "claude-md-and-agents-md",
    "claude-md",
    "managed-only",
)
FALLBACK_DISABLED_VALUES = ("claude-md", "managed-only")
LEGACY_PROJECT_INSTRUCTIONS = {
    "claude": "claude-md",
    "agents-fallback": "claude-md-or-agents-md",
    "both": "claude-md-and-agents-md",
    "none": "managed-only",
}
DECISION_FILE = Path(".nexus-hub") / "claude-instruction-decision.json"
SIDECAR_FILE = Path(".claude") / "rules" / "nexus-hub-claude.md"
#: Sections of base-claude.md that no other platform template carries. They move to a
#: native `.claude/rules/` sidecar when the project block comes from the shared AGENTS.md.
CLAUDE_ONLY_SECTIONS = (
    "Context References",
    "Agent Registry",
    "Spending Controls",
    "Environment Variables",
    "MCP Integration",
)
_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_TRUTHY = {"1", "true", "yes", "on"}


def parse_version(text: str) -> Optional[tuple[int, int, int]]:
    match = _VERSION_RE.search(text or "")
    return tuple(int(g) for g in match.groups()) if match else None  # type: ignore[return-value]


def provider_surface(env: Mapping[str, str]) -> str:
    """Best-effort provider surface from the environment, most specific first."""
    for name, surface in (
        ("CLAUDE_CODE_USE_BEDROCK", "bedrock"),
        ("CLAUDE_CODE_USE_VERTEX", "vertex"),
        ("CLAUDE_CODE_USE_FOUNDRY", "foundry"),
    ):
        if env.get(name, "").strip().lower() in _TRUTHY:
            return surface
    if env.get("ANTHROPIC_BASE_URL", "").strip():
        return "gateway"
    if env.get("DISABLE_TELEMETRY", "").strip().lower() in _TRUTHY:
        return "telemetry-off"
    return "first-party"


def probe_version(ctx: InstallContext, env: Mapping[str, str]) -> tuple[Optional[tuple[int, int, int]], str]:
    """Installed Claude Code version and where it came from; (None, reason) when unknown."""
    override = env.get("NEXUS_HUB_CLAUDE_VERSION", "").strip()
    if override:
        return parse_version(override), "env:NEXUS_HUB_CLAUDE_VERSION"
    which = ctx.which or _detection.safe_which
    exe = which("claude")
    if not exe:
        return None, "claude is not on PATH"
    try:
        done = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None, "claude --version could not run"
    version = parse_version(done.stdout) if done.returncode == 0 else None
    return version, "claude --version" if version else "claude --version printed no version"


def managed_settings_candidates(env: Mapping[str, str]) -> list[Path]:
    override = env.get("NEXUS_HUB_CLAUDE_MANAGED_SETTINGS", "").strip()
    if override:
        return [Path(override)]
    if os.name == "nt":
        base = env.get("ProgramFiles", r"C:\Program Files")
        return [Path(base) / "ClaudeCode" / "managed-settings.json"]
    return [
        Path("/Library/Application Support/ClaudeCode/managed-settings.json"),
        Path("/etc/claude-code/managed-settings.json"),
    ]


def _read_instruction_value(path: Path) -> tuple[Optional[dict], str]:
    """Read one settings file; ({}, 'absent') when missing, (None, reason) when unreadable."""
    if not path.is_file():
        return {}, "absent"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None, f"{path.name} is unreadable or not JSON"
    if not isinstance(data, dict):
        return None, f"{path.name} root is not an object"
    entries = data.get("pluginConfigs", {})
    enabled = data.get("enabledPlugins", {})
    if not isinstance(entries, dict) or not isinstance(enabled, dict):
        return None, f"{path.name} pluginConfigs or enabledPlugins is malformed"
    found: dict[str, Any] = {"disabled": any(enabled.get(i) is False for i in AGENTS_PLUGIN_IDS)}
    values = set()
    for plugin_id in AGENTS_PLUGIN_IDS:
        options = entries.get(plugin_id, {})
        if not isinstance(options, dict):
            return None, f"{path.name} {plugin_id} entry is malformed"
        options = options.get("options", {})
        if not isinstance(options, dict):
            return None, f"{path.name} {plugin_id} options are malformed"
        value = options.get("instructionFiles")
        if value is None and "projectInstructions" in options:
            value = LEGACY_PROJECT_INSTRUCTIONS.get(options["projectInstructions"], "invalid")
        if value is not None:
            values.add(value)
    if values - set(INSTRUCTION_FILES_VALUES):
        return None, f"{path.name} has an unrecognized instructionFiles or projectInstructions value"
    if len(values) > 1:
        return None, f"{path.name} sets conflicting values under the two plugin IDs"
    found["value"] = next(iter(values)) if values else None
    return found, "present" if values or found["disabled"] else "absent"


def resolve_instruction_files(ctx: InstallContext, env: Mapping[str, str]) -> dict[str, Any]:
    """Effective `instructionFiles` value with the scope it came from.

    Claude Code reads the entry from managed settings, a `--settings` file, and
    `~/.claude/settings.json`, in that precedence order, and ignores project and local
    settings files. An installer cannot see `--settings`, MDM, or server-managed
    sources, so those are reported as not inspected.
    """
    config_dir = env.get("CLAUDE_CONFIG_DIR", "").strip()
    user_path = (Path(config_dir) if config_dir else Path(ctx.global_root) / ".claude") / "settings.json"
    sources = [(path, "managed") for path in managed_settings_candidates(env)] + [(user_path, "user")]
    out: dict[str, Any] = {"value": None, "scope": "default", "disabled": False, "unknown": None,
                           "not_inspected": ["--settings", "mdm", "server-managed"]}
    for path, scope in sources:
        data, status = _read_instruction_value(path)
        if data is None:
            out["unknown"] = status
            return out
        if data.get("disabled"):
            out["disabled"] = True
        if data.get("value") is not None and out["value"] is None:
            out["value"], out["scope"] = data["value"], scope
    return out


def project_claude_files(root: Path, home: Optional[Path] = None) -> list[str]:
    """CLAUDE.md-family files from `root` upward that disable the default AGENTS.md fallback.

    The user's own `~/.claude/CLAUDE.md` does not count, so a `.claude/CLAUDE.md` found in the
    home directory is skipped.
    """
    names = ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md")
    homes = {Path(os.path.expanduser("~")).resolve(), Path.home().resolve()}
    if home is not None:
        homes.add(home)
    found = []
    for directory in (root, *root.parents):
        for name in names:
            if name == ".claude/CLAUDE.md" and directory in homes:
                continue
            if (directory / name).is_file():
                found.append(str(directory / name))
    return found


def classify_project_claude_md(root: Path) -> str:
    """none | managed-only | mixed | user-authored for the project-root CLAUDE.md."""
    path = root / "CLAUDE.md"
    if not path.is_file():
        return "none"
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return "user-authored"
    start, end = DEFAULT_START_MARKER, DEFAULT_END_MARKER
    if start not in text or end not in text:
        return "user-authored"
    head, _, rest = text.partition(start)
    _block, _, tail = rest.partition(end)
    return "mixed" if (head + tail).strip() else "managed-only"


def decide_instruction_path(
    ctx: InstallContext,
    root: Path,
    env: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    """Return the capability decision object for a workspace install at `root`."""
    env = os.environ if env is None else env
    version, version_source = probe_version(ctx, env)
    surface = provider_surface(env)
    files = resolve_instruction_files(ctx, env)
    blockers = project_claude_files(root, Path(ctx.global_root).resolve())
    value = files["value"] or "claude-md-or-agents-md"
    floor = FLOOR_GENERAL if surface == "first-party" else FLOOR_HOSTED
    reason, confidence, path = "supported", "verified-inputs", "AGENTS.md"
    if version is None:
        reason, confidence, path = f"version unknown ({version_source})", "unknown", "CLAUDE.md"
    elif version < floor:
        reason, path = f"below the {'.'.join(map(str, floor))} floor for {surface}", "CLAUDE.md"
    elif files["unknown"]:
        reason, confidence, path = f"settings unreadable: {files['unknown']}", "unknown", "CLAUDE.md"
    elif files["disabled"]:
        reason, path = "built-in AGENTS.md reader disabled", "CLAUDE.md"
    elif value in FALLBACK_DISABLED_VALUES:
        reason, path = f"instructionFiles is {value}", "CLAUDE.md"
    elif blockers and value != "claude-md-and-agents-md":
        reason, path = "a CLAUDE.md in the working directory or above takes precedence", "CLAUDE.md"
    return {
        "schema": "claude-instruction-decision/1",
        "version": ".".join(map(str, version)) if version else None,
        "version_source": version_source,
        "provider_surface": surface,
        "instruction_files": value,
        "instruction_files_scope": files["scope"],
        "not_inspected": files["not_inspected"],
        "precedence_blockers": [Path(b).name for b in blockers[:3]] if blockers else [],
        "evidence_source": "official documentation 2026-11-15 plus local probes",
        "confidence": confidence,
        "effective_path": path,
        "reason": reason,
        "no_load_modes": "--bare, --safe-mode and CLAUDE_CODE_DISABLE_CLAUDE_MDS are out of scope",
    }


def persist_decision(ctx: InstallContext, root: Path, owner_key: str, decision: dict[str, Any]) -> FileAction:
    """Write the decision beside the install manifest records, chaining the prior one."""
    path = root / DECISION_FILE
    prior_id = None
    if path.is_file():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            prior_id = old.get("decision_id")
            # The blockers list is excluded: the CLAUDE.md this install itself writes would
            # otherwise make every repeat install look like a new decision.
            ignored = ("decision_id", "decided_at", "prior_decision", "precedence_blockers")
            comparable = {k: v for k, v in old.items() if k not in ignored}
            if comparable == {k: v for k, v in decision.items() if k not in ignored}:
                ctx.manifest.track(owner_key, str(path))
                return FileAction(path=str(path), action="unchanged")
        except (OSError, ValueError):
            prior_id = "unreadable"
    body = dict(decision)
    body["decided_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body["prior_decision"] = prior_id
    body["decision_id"] = hashlib.sha256(json.dumps(decision, sort_keys=True).encode()).hexdigest()[:16]
    existed = path.is_file()
    if not ctx.dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    ctx.manifest.track(owner_key, str(path))
    return FileAction(path=str(path), action="updated" if existed else "created")


def read_decision(root: Path) -> Optional[dict[str, Any]]:
    """The persisted decision for a project root, or None when absent or unreadable."""
    try:
        data = json.loads((root / DECISION_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("effective_path") in ("AGENTS.md", "CLAUDE.md") else None


def claude_only_sections(rendered: str) -> str:
    """The base-claude.md sections that have no shared-template equivalent."""
    parts = re.split(r"(?m)^(?=## )", rendered)
    keep = [p for p in parts if p.startswith("## ") and p[3:].split("\n", 1)[0].strip() in CLAUDE_ONLY_SECTIONS]
    return "".join(p.rstrip("\n") + "\n\n" for p in keep).rstrip("\n") + "\n"


class ClaudeIntegration(MarkdownIntegration, SkillsIntegration):
    key = "claude"
    display_name = "Claude Code (Anthropic)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.claude",
        "workspace_dir": ".claude",
        # Workspace CLAUDE.md lands at the project root (where Claude Code reads
        # it), not under .claude/; skills/commands/agents/rules still mirror
        # under .claude/. Matches the legacy bash installer (DF-001).
        "instruction_workspace_dir": "",
        "instruction_file": "CLAUDE.md",
        "instruction_template": "templates/ai-instructions/base-claude.md",
        # Claude Code discovers skills one level deep (~/.claude/skills/<name>/
        # SKILL.md), so flatten the catalog's <category>/ layer and surface each
        # command as a skill too (v3.12.0 Phase 4).
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "commands_subdir": "commands",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
    }

    #: Set only while a workspace install on the shared-AGENTS.md path is running, so the
    #: inherited instruction writer skips CLAUDE.md for exactly that install.
    _consume_shared_agents: bool = False

    def _write_instruction(self, dst_dir: Path, ctx: InstallContext):
        if self._consume_shared_agents and ctx.scope == "workspace":
            return None
        return super()._write_instruction(dst_dir, ctx)

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        """Choose the project instruction path from a recorded capability decision.

        Supported sessions consume the shared project AGENTS.md (plus a native
        `.claude/rules/` sidecar for Claude-only guidance) and write no project
        CLAUDE.md. Every unknown, below-floor, fallback-disabled, or precedence-blocked
        case keeps the managed CLAUDE.md. Global scope is unchanged.
        """
        root = ctx.target_root.resolve()
        notes: list[FileAction] = []
        if os.environ.get("NEXUS_HUB_CLAUDE_MIGRATE", "").strip().lower() in _TRUTHY:
            notes += self._migrate_project_claude_md(root, ctx)
        decision = decide_instruction_path(ctx, root)
        self._consume_shared_agents = decision["effective_path"] == "AGENTS.md"
        try:
            result = super().install_workspace(ctx)
        finally:
            self._consume_shared_agents = False
        result.files = notes + list(result.files)
        result.files.append(persist_decision(ctx, root, self.key, decision))
        if decision["effective_path"] == "AGENTS.md":
            shared = self.write_shared_agents(root, ctx)
            if shared is not None:
                result.files.append(shared)
            result.files.append(self._write_sidecar(root, ctx))
        else:
            ctx.manifest.log(self.key, f"project instructions stay on CLAUDE.md: {decision['reason']}")
        return result

    def _migrate_project_claude_md(self, root: Path, ctx: InstallContext) -> list[FileAction]:
        """Explicit, reversible removal of the managed block from the project CLAUDE.md.

        A managed-only file is deleted (the block is regenerated by any later install);
        a mixed file keeps every user byte and stays on CLAUDE.md precedence; a
        user-authored file is never touched.
        """
        from scripts.lib.installer.instruction_merge import remove_marker_section

        state = classify_project_claude_md(root)
        if state not in ("managed-only", "mixed"):
            ctx.manifest.log(self.key, f"migrate: project CLAUDE.md is {state}; nothing removed")
            return []
        action = remove_marker_section(root / "CLAUDE.md", dry_run=ctx.dry_run)
        ctx.manifest.untrack_shared(self.key, str(root / "CLAUDE.md"))
        ctx.manifest.log(self.key, f"migrate: {state} CLAUDE.md -> {action.action}")
        return [action]

    def _write_sidecar(self, root: Path, ctx: InstallContext) -> FileAction:
        """Claude-only guidance on the native project rules surface (`.claude/rules/`)."""
        template = ctx.repo_root / self.config["instruction_template"]
        dst = root / SIDECAR_FILE
        body = claude_only_sections(self._render(template, ctx))
        existed = dst.is_file()
        if existed and dst.read_text(encoding="utf-8") == body:
            ctx.manifest.track(self.key, str(dst))
            return FileAction(path=str(dst), action="unchanged")
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(body, encoding="utf-8")
        ctx.manifest.track(self.key, str(dst))
        return FileAction(path=str(dst), action="updated" if existed else "created")

    def wire_project_surfaces(self, ctx: InstallContext) -> WriteResult:
        """Write a `.claude/settings.json` stub when none exists.

        `nexus-hub init` calls this to bootstrap a Claude project surface from
        a global install. The stub never overwrites an existing settings.json;
        it returns `kept` so the user's customizations survive.
        """
        result = WriteResult()
        claude_dir = (ctx.target_root / self.config["workspace_dir"]).resolve()
        if not ctx.dry_run:
            long_path(claude_dir).mkdir(parents=True, exist_ok=True)
        dst = claude_dir / "settings.json"
        dst_io = long_path(dst)  # AR-11: a deep project root passes MAX_PATH
        if dst_io.exists():
            ctx.manifest.log(self.key, f"skip-existing: {dst}")
            result.files.append(FileAction(path=str(dst), action="kept"))
            return result
        body = json.dumps(build_project_settings_stub(), indent=2) + "\n"
        if not ctx.dry_run:
            dst_io.write_text(body, encoding="utf-8")
        ctx.manifest.track(self.key, str(dst))
        result.files.append(FileAction(path=str(dst), action="created"))
        return result
