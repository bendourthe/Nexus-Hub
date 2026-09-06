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
from dataclasses import dataclass, field
from typing import Mapping, Sequence

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
        _py("validate_unicode_safety", "--strict", timeout=300),
        _py("validate_no_personal_paths", timeout=300),
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

PLATFORM_CONTRACTS = Group(
    name="platform-contracts",
    scope_key="platforms",
    commands=(
        _py("check_installer_parity", timeout=300),
        _py("check_base_template_parity", timeout=120),
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
        _pytest("hook-tests", "catalog/hooks/tests", timeout=1800),
        # The Windows suite has a measured 3341.7s passing baseline. A 3600s
        # limit left only 7.7% variance and timed out a subsequent green-path
        # run, so retain enough host/filesystem headroom to report assertions.
        _pytest("repo-tests", "tests", timeout=4500),
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
_PS_AST_PARSE = " ".join(
    [
        "$f=$false;",
        "@(Get-ChildItem catalog/hooks -Filter *.ps1 -File) +",
        "@(Get-ChildItem scripts -Filter *.ps1 -File) +",
        "@(Get-ChildItem . -Filter install.ps1 -File) | ForEach-Object {",
        "$e=$null;",
        "$null=[System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$null,[ref]$e);",
        'if ($e -and $e.Count -gt 0) { Write-Host "FAIL $($_.Name)"; $f=$true }',
        'else { Write-Host "OK   $($_.Name)" } };',
        "if ($f) { exit 1 }",
    ]
)

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
            platforms=("windows",),
            timeout=1800,
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
    "fast": (CATALOG_PARSE, HYGIENE, INTERPRETERS, WORKFLOWS, VERSION),
    # Everything provable on this host.
    "full": (
        CATALOG_PARSE,
        HYGIENE,
        INTERPRETERS,
        CATALOG,
        SECURITY,
        WORKFLOWS,
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
