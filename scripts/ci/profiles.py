"""Profile definitions: what each profile runs, expressed as data.

A profile is an ordered list of groups; a group is an ordered list of commands.
Nothing here executes anything -- `run.py` does that -- so a test can assert the
CONTENTS of a profile in microseconds without paying for a real run. That
separation is the reason `--list` exists and is cheap.

Two rules govern what may appear here:

1. **Reuse, never reimplement.** Every command must already be a repository
   command a developer can run by hand. A profile that reimplements a validator
   has created a second source of truth, which is the exact defect the engine
   exists to remove.
2. **Host differences are explicit.** A command that only makes sense on one
   platform declares it in `platforms`, rather than being silently skipped by a
   `shutil.which` check somewhere. A skip nobody can see is indistinguishable
   from a pass.
"""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

#: Host classes a command can be scoped to. `posix` is the union of linux and
#: macos, kept because most shell tooling cares about that boundary rather than
#: about the specific kernel.
PLATFORMS = ("linux", "macos", "windows")

#: The interpreter running this engine. Using `sys.executable` rather than the
#: bare string "python" matters on Windows, where "python" can resolve to the
#: Microsoft Store shim, and inside a virtualenv, where it can resolve outside
#: the environment that has the test dependencies installed.
PY = sys.executable

#: PowerShell interpreter, preferring cross-platform pwsh 7 and falling back to
#: Windows PowerShell 5.1. Resolving the INTERPRETER is not the same thing as
#: skipping a check: when neither is present the name below stays unresolvable
#: and the command reports MISSING, which is a visible failure rather than a
#: silent pass. The platform profile genuinely requires a PowerShell.
PWSH = "pwsh" if shutil.which("pwsh") else "powershell"


@dataclass(frozen=True)
class Command:
    """One executable step.

    `argv` is a list, never a shell string: the engine never invokes a shell, so
    a path containing a space cannot be re-split and a value cannot be
    interpreted as an operator. Nexus-Hub lives under a OneDrive path with a
    space in it, so this is a live concern rather than a theoretical one.
    """

    name: str
    argv: Sequence[str]
    #: Working directory relative to the repository root. "." is the root.
    cwd: str = "."
    #: Seconds. A command that hangs must FAIL, not wait forever.
    timeout: int = 900
    #: Restrict to these host classes. Empty means every host.
    platforms: tuple[str, ...] = ()
    #: A failure is reported but does not fail the group or the run.
    advisory: bool = False
    #: An unavailable optional vendor CLI is a visible skip, never a silent pass.
    skip_if_missing: bool = False
    #: Extra environment for this command only.
    env: Mapping[str, str] = field(default_factory=dict)

    def runs_on(self, platform: str) -> bool:
        return not self.platforms or platform in self.platforms


@dataclass(frozen=True)
class Group:
    """An ordered set of commands sharing a change-scope key.

    `scope_key` names the `change_scope` group that makes this group relevant.
    `None` means always relevant. A group is only ever SKIPPED with a recorded
    reason; it is never silently dropped.
    """

    name: str
    commands: Sequence[Command]
    scope_key: str | None = None
    #: When true, a failure here stops the profile. Use for cheap gates whose
    #: failure makes every later result meaningless (a catalog that will not
    #: parse, say). Everything else keeps running so one run reports every
    #: independent failure instead of only the first.
    blocking: bool = False


def _py(name: str, *args: str, **kw) -> Command:
    """A repository Python script, run with the current interpreter."""
    script = args[0] if args and args[0].endswith(".py") else f"scripts/{name}.py"
    argv = [PY, script, *args[1:]] if args and args[0].endswith(".py") else [PY, script, *args]
    return Command(name=name, argv=argv, **kw)


def _pytest(name: str, target: str, *extra: str, cwd: str = ".", **kw) -> Command:
    return Command(name=name, argv=[PY, "-m", "pytest", target, "-q", *extra], cwd=cwd, **kw)


def _local_src_env(*paths: str) -> dict[str, str]:
    """Build an isolated, host-correct import path for a src-layout command."""
    return {"PYTHONPATH": os.pathsep.join(paths)}


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------

CATALOG_PARSE = Group(
    name="catalog-parse",
    blocking=True,  # nothing downstream means anything if the catalog will not load
    commands=(
        Command(
            name="skills.json parses",
            argv=[PY, "-c", "import json;json.load(open('data/skills.json',encoding='utf-8'))"],
            timeout=60,
        ),
        Command(
            name="bundles.json parses",
            argv=[PY, "-c", "import json;json.load(open('data/bundles.json',encoding='utf-8'))"],
            timeout=60,
        ),
        Command(
            name="workflows.json parses",
            argv=[PY, "-c", "import json;json.load(open('data/workflows.json',encoding='utf-8'))"],
            timeout=60,
        ),
        Command(
            name="templates.json parses",
            argv=[PY, "-c", "import json;json.load(open('data/templates.json',encoding='utf-8'))"],
            timeout=60,
        ),
    ),
)

HYGIENE = Group(
    name="hygiene",
    commands=(
        _py("check_commit_attribution", "--all-refs", "--root", ".", timeout=120),
        _py("validate_unicode_safety", "--strict", timeout=300),
        _py("validate_no_personal_paths", timeout=300),
        _py("check_merge_conflict_markers", timeout=120),
        _py("check_docs_conventions", timeout=300),
        _py("validate_doc_budgets", timeout=120),
        _py("check_memory_integration_budget", timeout=120),
    ),
)

CATALOG = Group(
    name="catalog",
    scope_key="catalog",
    commands=(
        _py("validate_skills", "--bundles-only", timeout=600),
        _py("check_agentskills_conformance", timeout=300),
        _py("build_framework_coverage", "--check", timeout=300),
        _py("run_trigger_evals", "--gate", timeout=600),
        _py("check_registry_entries", "--check", "--strict", timeout=300),
        _py("scan_skill_security", "catalog/skills", "catalog/mcp-configs", "--fail-on", "high", timeout=600),
    ),
)

SECURITY = Group(
    name="security",
    commands=(
        _py("scan_supply_chain_iocs", timeout=300),
        _py("validate_permission_baseline", timeout=120),
        _py("check_no_outbound", timeout=120),
    ),
)

WORKFLOWS = Group(
    name="workflows",
    scope_key="workflows",
    commands=(
        _py("validate_workflow_security", timeout=300),
        _py("check_required_check_coverage", timeout=120),
    ),
)

CLAUDE_PLUGIN = Group(
    name="claude-plugin",
    commands=(
        Command(
            name="claude plugin validate",
            argv=["claude", "plugin", "validate", "."],
            timeout=120,
            skip_if_missing=True,
        ),
    ),
)

PLATFORM_CONTRACTS = Group(
    name="platform-contracts",
    scope_key="platforms",
    commands=(
        _py("check_installer_parity", timeout=300),
        _py("check_base_template_parity", timeout=120),
        _pytest("instruction-contracts", "tests/validators/test_communication_contract_rollout.py", timeout=120),
        _py("verify_platform_contracts", timeout=300),
        _py("check_platform_contract_freshness", timeout=120),
        _py("sync_platform_defaults", "--check", timeout=120),
        _py("verify_model_prompting_profiles", timeout=300),
    ),
)

DOCS = Group(
    name="docs",
    scope_key="docs",
    commands=(
        _py("check_doc_colocation", timeout=300),
        _py("validate_solution_frontmatter", timeout=120),
        _py("check_incident_notes", timeout=120),
        _py("validate_decision_records", timeout=120),
        # v4.4.2: the guide may not carry a hand-typed catalog count; every count is a
        # data-count marker stamped from data/ and catalog/, and this is the drift gate.
        _py("stamp_guide_counts", "--check", timeout=120),
        _py("check_memory_provenance", timeout=120),
        # v4.11.0: the living handbooks are generated, so an edit to the builder
        # silently invalidates them - the same sources stop producing the same
        # bytes. This is read-only and hash-only: it launches no browser and
        # runs in about a second, so it costs the docs group nothing and is a
        # hard gate. It was unwired until Phase 7, and in that window both
        # repository handbooks went stale against two Phase 6 builder fixes
        # without anything reporting it.
        Command(
            name="check_handbooks",
            argv=[
                PY,
                "catalog/skills/documentation/technical-documentation/scripts/check_handbooks.py",
            ],
            timeout=300,
        ),
        # Advisory by design: archiving repairs references repo-wide, so it
        # belongs in a reviewed pass. A hard gate here would stop an unrelated
        # release the moment a minor version aged out.
        _py("check_docs_retention", advisory=True, timeout=120),
    ),
)

VERSION = Group(
    name="version",
    commands=(_py("check_version_sync", timeout=120),),
)

TESTS = Group(
    name="tests",
    scope_key="tests",
    commands=(
        # These are enforceable CI safety bounds, not local performance SLOs.
        # A contended workstation may exceed them; do not tune shared limits
        # from that observation. Recalibrate only from quiet CI measurements.
        _pytest("hook-tests", "catalog/hooks/tests", timeout=1800),
        # Keep the repository corpus complete but split it at stable ownership
        # boundaries. The former monolith could time out after an hour while
        # naming only a percentage; these partitions retain every collected
        # root/domain target and identify the slow owner without raising a cap.
        _pytest("repo-tests-skills", "tests/skills", timeout=2700),
        _pytest("repo-tests-installer", "tests/installer", timeout=1800),
        _pytest(
            "repo-tests-integrations-platform-a",
            "tests/integrations/test_aider_windsurf.py",
            "tests/integrations/test_antigravity.py",
            "tests/integrations/test_antigravity_commands.py",
            "tests/integrations/test_codex.py",
            "tests/integrations/test_codex_invocation_policy.py",
            "tests/integrations/test_codex_native.py",
            "tests/integrations/test_consult.py",
            timeout=1800,
        ),
        _pytest(
            "repo-tests-integrations-platform-b",
            "tests/integrations/test_copilot_hermes_native.py",
            "tests/integrations/test_copilot_skills_surface.py",
            "tests/integrations/test_cursor.py",
            "tests/integrations/test_hermes.py",
            "tests/integrations/test_kimi_native.py",
            "tests/integrations/test_kimi_qwen_openclaw.py",
            "tests/integrations/test_opencode.py",
            timeout=1800,
        ),
        _pytest(
            "repo-tests-integrations-adapter-contracts",
            "tests/integrations/test_base_writeresult.py",
            "tests/integrations/test_catalog_adapters.py",
            "tests/integrations/test_contract.py",
            "tests/integrations/test_cross_platform_flatten.py",
            "tests/integrations/test_global_command_surface.py",
            "tests/integrations/test_owned_root_preflight.py",
            timeout=1800,
        ),
        _pytest(
            "repo-tests-integrations-repository-contracts",
            "tests/integrations/test_harness_audit.py",
            "tests/integrations/test_nexus_ai_version.py",
            "tests/integrations/test_registry.py",
            "tests/integrations/test_result.py",
            "tests/integrations/test_runner_target_root.py",
            timeout=1800,
        ),
        _pytest(
            "repo-tests-integrations-install",
            "tests/integrations/test_hooks_supported_gate.py",
            "tests/integrations/test_install_summary.py",
            "tests/integrations/test_install_workspace.py",
            "tests/integrations/test_legacy_cleanups.py",
            "tests/integrations/test_markdown_integration.py",
            "tests/integrations/test_owned_file_modes.py",
            "tests/integrations/test_parity_with_legacy_installer.py",
            timeout=1800,
        ),
        _pytest(
            "repo-tests-integrations-lifecycle",
            "tests/integrations/test_lifecycle.py",
            "tests/integrations/test_lifecycle_block_rendering.py",
            "tests/integrations/test_selective_install.py",
            "tests/integrations/test_settings_hooks.py",
            "tests/integrations/test_teardown.py",
            timeout=1800,
        ),
        _pytest("repo-tests-plans", "tests/plans", timeout=900),
        _pytest("repo-tests-ci", "tests/ci", timeout=900),
        _pytest("repo-tests-guides", "tests/guides", timeout=1800),
        _pytest(
            "repo-tests-governance",
            "tests/validators",
            "tests/verification",
            "tests/workflows",
            "tests/test_git_attribution.py",
            "tests/test_removed_autonomy_surface.py",
            timeout=2700,
        ),
    ),
)

EXTENSION_TESTS = Group(
    name="extension-tests",
    scope_key="extensions",
    # Target `tests` explicitly, never `.`.
    #
    # Every extension declares `testpaths = ["tests"]` in its pyproject.toml. A
    # BARE `pytest` honors that; an explicit `pytest .` OVERRIDES it and walks
    # the whole package, which pulls in benchmark fixture corpora that import
    # modules deliberately absent from the environment. `make test` runs bare
    # pytest and was fine; this profile passed `.` and was not, so the two
    # looked equivalent and were not. Naming the configured path keeps them so.
    commands=(
        _pytest(
            "skill-server",
            "tests",
            cwd="extensions/nexus-skill-server",
            timeout=900,
            env=_local_src_env("src"),
        ),
        _pytest(
            "code-search",
            "tests",
            cwd="extensions/nexus-code-search",
            timeout=900,
            env=_local_src_env("src"),
        ),
        _pytest(
            "web-fetch",
            "tests",
            cwd="extensions/nexus-web-fetch",
            timeout=900,
            env=_local_src_env("src"),
        ),
        _pytest(
            "skill-scanner",
            "tests",
            cwd="extensions/nexus-skill-scanner",
            timeout=900,
            env=_local_src_env("src"),
        ),
        _pytest(
            "context-compressor",
            "tests",
            cwd="extensions/nexus-context-compressor",
            timeout=900,
            env=_local_src_env("src", "../nexus-code-search/src"),
        ),
        _pytest(
            "memory",
            "tests",
            cwd="extensions/nexus-memory",
            timeout=900,
            env=_local_src_env("src"),
        ),
        Command(
            name="compression-accuracy-gate",
            argv=[PY, "-m", "evals", "--check"],
            cwd="extensions/nexus-context-compressor",
            timeout=900,
            env=_local_src_env("src", "../nexus-code-search/src"),
        ),
    ),
)

# --- platform-scoped -------------------------------------------------------

SHELL_LINT = Group(
    name="shell-lint",
    commands=(
        Command(
            name="shellcheck catalog",
            argv=["bash", "-c", "find catalog -name '*.sh' -print0 | xargs -0 shellcheck --severity=warning"],
            platforms=("linux", "macos"),
            timeout=300,
        ),
        Command(
            name="shellcheck installers",
            argv=["shellcheck", "--severity=warning", "scripts/installer.sh", "install.sh"],
            platforms=("linux", "macos"),
            timeout=300,
        ),
    ),
)

#: The PowerShell AST-parse one-liner, assembled with an EXPLICIT join.
#:
#: Written as adjacent string literals this reads as implicit concatenation,
#: which CodeQL flags as a possible missing comma in a list -- a fair warning,
#: because in an argv list that mistake silently merges two arguments into one
#: and the failure appears far from its cause. Joining explicitly says the
#: concatenation is intended.
_PS_AST_PARSE_PARTS = (
    "$f=$false;",
    "@(Get-ChildItem catalog/hooks -Filter *.ps1 -File) +",
    "@(Get-ChildItem scripts -Filter *.ps1 -File) +",
    "@(Get-ChildItem . -Filter install.ps1 -File) | ForEach-Object {",
    "$e=$null;",
    "$null=[System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$null,[ref]$e);",
    'if ($e -and $e.Count -gt 0) { Write-Host "FAIL $($_.Name)"; $f=$true }',
    'else { Write-Host "OK   $($_.Name)" } };',
    "if ($f) { exit 1 }",
)
_PS_AST_PARSE = " ".join(_PS_AST_PARSE_PARTS)

POWERSHELL_PARSE = Group(
    name="powershell-parse",
    commands=(
        # The v3.11.0 lesson: a .ps1 sibling shipped with a parse error and was
        # dead on Windows for four minor versions because nothing parsed catalog
        # PowerShell. This is the unconditional syntax floor.
        Command(
            name="powershell AST parse",
            argv=[PWSH, "-NoProfile", "-NonInteractive", "-Command", _PS_AST_PARSE],
            # Deliberately NOT scoped to windows. The v3.11.0 defect (a .ps1
            # sibling that would not parse, dead on Windows for four minor
            # versions) is catchable anywhere a PowerShell exists, and the
            # ubuntu leg is where it is cheapest to catch. The Windows-only
            # coverage that pwsh 7 CANNOT provide is the 5.1 BEHAVIOR leg
            # below, which is a different claim.
            timeout=600,
        ),
    ),
)

WINDOWS_HOOKS = Group(
    name="windows-hooks",
    commands=(
        # NEXUS_TEST_POWERSHELL pins the EDITION. The Windows image carries both
        # 5.1 and 7, the fixture prefers 7, and the defect class this leg exists
        # for (Add-Content -Encoding utf8 emitting a BOM) reproduces only on 5.1.
        _pytest(
            "hook-tests (Windows PowerShell 5.1)",
            "catalog/hooks/tests",
            platforms=("windows",),
            timeout=1800,
            env={"NEXUS_TEST_POWERSHELL": "powershell"},
        ),
        _pytest(
            "installer + validators (Windows)",
            "tests/installer",
            "tests/validators",
            "tests/test_git_attribution.py",
            platforms=("windows",),
            timeout=1800,
            env={"NEXUS_TEST_POWERSHELL": "powershell"},
        ),
        # Exercise the native Windows evidence boundaries before merge (QG-1).
        _pytest(
            "security-audit evidence (Windows)",
            "tests/validators/test_validate_unicode_safety.py",
            "tests/skills/test_safe_artifact.py",
            "tests/skills/test_target_manifest.py",
            "tests/skills/test_strict_json.py",
            "tests/skills/test_security_scanner_contract.py",
            "tests/skills/test_graph_receipts.py",
            "tests/skills/test_application_audit_envelope.py",
            "tests/skills/test_security_review_sarif.py",
            "tests/skills/test_security_audit_benchmark.py",
            "tests/skills/test_security_audit_benchmark_lifecycle.py",
            "tests/skills/test_security_audit_contract_e2e.py",
            platforms=("windows",),
            timeout=1200,
            env={"NEXUS_TEST_POWERSHELL": "powershell"},
        ),
        _pytest(
            "native integrations (Windows)",
            "tests/integrations/test_codex_native.py",
            "tests/integrations/test_copilot_hermes_native.py",
            "tests/integrations/test_kimi_native.py",
            "tests/integrations/test_settings_hooks.py",
            "tests/integrations/test_catalog_adapters.py",
            "tests/integrations/test_codex_invocation_policy.py",
            "--junitxml=reports/junit/windows-native.xml",
            platforms=("windows",),
            timeout=1200,
            env={"NEXUS_TEST_POWERSHELL": "powershell"},
        ),
    ),
)

RELEASE_CHECKS = Group(
    name="release-checks",
    commands=(
        _py("check_version_sync", timeout=120),
        _py("check_platform_contract_freshness", timeout=120),
        _py("check_release_preconditions", "--branches", "--repo-settings", advisory=True, timeout=300),
    ),
)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

INTERPRETERS = Group(
    name="interpreters",
    commands=(
        _py("check_python_floor", timeout=120),
        # Nexus-Hub registers hooks as `bash <script>` and the HOST performs that
        # launch, so a host whose `bash` cannot execute a script leaves every hook
        # silently inert. No other group can see this: they all run Python
        # directly rather than through the interpreter the hooks actually use.
        # v4.3.0 Phase 5 went red twice on a Windows runner for this reason while
        # the full local suite was green.
        _py("check_interpreter_resolution", "--gate", timeout=300),
    ),
)


PROFILES: dict[str, tuple[Group, ...]] = {
    # Cheapest useful signal. No test suite, no install, no network.
    # CATALOG adds the complete skill and security scans, so keep it in full.
    # The one cheap registry census command closes the fast-profile drift gap
    # without turning this profile into a pytest suite.
    "fast": (
        CATALOG_PARSE,
        HYGIENE,
        INTERPRETERS,
        Group(
            name="registry-consistency",
            scope_key="catalog",
            commands=(_py("check_registry_entries", "--check", "--strict", timeout=300),),
        ),
        WORKFLOWS,
        VERSION,
    ),
    # Everything provable on this host.
    "full": (
        CATALOG_PARSE,
        HYGIENE,
        INTERPRETERS,
        CATALOG,
        SECURITY,
        WORKFLOWS,
        CLAUDE_PLUGIN,
        PLATFORM_CONTRACTS,
        DOCS,
        VERSION,
        TESTS,
        EXTENSION_TESTS,
    ),
    # Only what differs by host. Deliberately small: a leg that runs everywhere
    # belongs in `full`, where it is paid for once.
    "platform": (SHELL_LINT, POWERSHELL_PARSE, INTERPRETERS, WINDOWS_HOOKS),
    # Aggregation only. Reads what the other profiles wrote; never re-runs a
    # check, which is what makes it safe to call after a failure.
    "report": (),
    # Packaging and publication readiness. Never a validation re-run.
    "release": (RELEASE_CHECKS,),
}


def groups_for(profile: str) -> tuple[Group, ...]:
    if profile not in PROFILES:
        raise KeyError(f"unknown profile {profile!r}; expected one of {sorted(PROFILES)}")
    return PROFILES[profile]


def detect_platform() -> str:
    """Map `sys.platform` onto the host classes commands are scoped to."""
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"
