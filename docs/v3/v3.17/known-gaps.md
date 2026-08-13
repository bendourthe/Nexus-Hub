# Known Gaps - v3.17

**Project**: Nexus-Hub
**Status**: v3.17.0 `agent-autonomy-toggle` is IN FLIGHT on `develop`. Phase 1 (permission-baseline hardening and cross-platform merge parity) is COMPLETE; Phases 2-6 are not started.
**Last updated**: 2026-08-13 (v3.17.0 Phase 1 append)

> **File-lifecycle note**: this ledger is opened by the v3.17.0 Phase 1 append. Each subsequent v3.17.N version-implementation phase **appends** its own `## v3.17.N - <slug>` section rather than replacing this file, keeping its own `DF-#` / `NI-#` / `BG-#` / `WN-#` / `MT-#` / `QG-#` numbering. Note that the v3.17.0 plan itself lives in this directory while its *predecessor* ledger entries sit in [../v3.16/known-gaps.md](../v3.16/known-gaps.md), an artifact of the v3.16-line re-stamp the plan's version-numbering note records.

---

## v3.17.0 - agent-autonomy-toggle

**Status**: Phase 1 COMPLETE (2026-08-13). 6 open (NI-1, NI-2, DF-1, DF-2, DF-3, WN-1), 3 closed (BG-1, BG-2, BG-3), 0 release blockers. Plan: [plans/v3.17.0-agent-autonomy-toggle.md](plans/v3.17.0-agent-autonomy-toggle.md).

### NI-1 - OPEN: output redirection under an explicit allow rule is UNVERIFIED

- **Target file**: [development/permission-matcher-findings.md](development/permission-matcher-findings.md) (Finding 2), `scripts/validate_permission_baseline.py` (the `redirect` rule)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1
- **Plan reference**: 1.1 required determining empirically "whether Claude Code's matcher treats a redirected command as matching the bare pattern"
- **Reason it is open**: the official permissions documentation demonstrably models redirects, but states it only for the BUILT-IN read-only command set, never for explicit `allow` rules. Redirection operators are also absent from the enumerated command-separator list, so a redirected command is one subcommand rather than two, and a wildcard "matches any sequence of characters including spaces". Per this plan's evidence discipline, absence of a statement is recorded as UNVERIFIED rather than as absence of the behavior.
- **Why it is load-bearing**: `> file` truncates its target regardless of what the command emits (`Write-Host x > f` writes nothing to the file and still truncates it). If the native matcher admits redirects under allow rules, then EVERY baseline pattern carrying a trailing wildcard is a file-destruction primitive, and no per-entry rescoping repairs that. This is a global property of the matcher, not a defect of any individual entry, which is why Phase 1.1 did not attempt to fix it per-entry.
- **Suggested next step**: the empirical probe named in Finding 2 -- add a single `Bash(echo *)` allow rule to a throwaway project config against a real Claude Code build and observe whether `echo x > /tmp/probe` prompts. Cheap, decisive, and needs a live build rather than documentation. Phase 4.1 already schedules hands-on verification against a real build for the hook-independence question, so this probe should ride that session.

### NI-2 - OPEN: whether Gemini's matcher splits compound commands at all

- **Target file**: `configs/permissions/gemini-permissions.json`, [development/permission-matcher-findings.md](development/permission-matcher-findings.md) (Finding 1)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1
- **Reason it is open**: Finding 1 VERIFIED compound-command splitting for Claude Code, quoted from its documentation, for both the Bash and the PowerShell matcher. No equivalent statement was located for Gemini's `run_shell_command`, and the file's own shipped comment records the opposite direction ("piped commands bypass allowlists (upstream issue)"). Gemini entries are therefore treated as PREFIX matches with no separator awareness, which is the conservative reading and is what `validate_permission_baseline.py` implements via its `prefix` match mode.
- **Why it matters**: under prefix semantics with no splitting, `run_shell_command(git status)` would admit `git status; rm -rf .`. The validator's conservative mode does not make that safe; it only stops Nexus-Hub from shipping patterns that depend on splitting.
- **Suggested next step**: verify against current Gemini CLI documentation during Phase 2.2, which already runs a documentation sweep across the roster, and record a MATCH / DRIFT / UNVERIFIED verdict in the read-contract alongside the autonomy-lever verdicts. If splitting is confirmed absent, the Gemini baseline needs a separate hardening pass under prefix-without-splitting assumptions -- a Phase 5.3 or later item, not a Phase 1 rescope.

### DF-1 - OPEN: `gemini-permissions.json` ships no PowerShell or `cmd.exe` read-only set

- **Target file**: `configs/permissions/gemini-permissions.json`, `docs/permissions-research.md`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1 (observation only, by instruction)
- **Plan reference**: 1.1 explicitly forbids adding one ("this sub-task rescopes existing entries and deliberately does not expand coverage") and hands the observation to sub-task 5.3
- **Reason it is open**: a Windows Gemini user receives a POSIX-shaped allowlist plus a bare `run_shell_command(dir)`, so their real shell is effectively uncovered. Expanding coverage is a different risk decision from rescoping and belongs with the platform-coverage work.
- **Suggested next step**: sub-task 5.3 documents the gap in `docs/permissions-research.md`. Actually shipping a PowerShell / `cmd.exe` set for Gemini requires NI-2 resolved first, since the safe pattern shape depends on whether the matcher splits.

### DF-2 - OPEN: three of four platforms have no project-scoped permission target

- **Target file**: `scripts/installer.sh` and `scripts/installer.ps1` (`install_permissions` / `Install-Permissions`, workspace branch)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2
- **Reason it is open**: workspace scope is now wired and load-bearing, but only Claude Code has a confirmed target (`.claude/settings.local.json`). The other three skip WITH A NOTE, each for a stated reason: **Gemini** and **Codex** have no project-scoped permission path documented well enough to write, and a guessed path is worse than none because it reads as configured; **Copilot**'s only surface is `.vscode/settings.json`, which is commit-visible and therefore forbidden here without an explicit maintainer decision (the same reasoning that made the v3.11.0 Copilot `.github/skills/` surface opt-in).
- **Suggested next step**: Phase 2.2's documentation sweep should record, per platform, whether a project-scoped permission path exists at all. A documented "no project path" verdict closes the Gemini and Codex halves permanently. The Copilot half needs a maintainer decision about writing to a commit-visible file, not more research.

### DF-3 - OPEN: `Install-Nexus-Hub-Permissions.ps1` still has no cross-platform equivalent

- **Target file**: `scripts/Install-Nexus-Hub-Permissions.ps1`, `scripts/nexus_hub_cli.py`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2 (deferred by that sub-task's own instruction)
- **Reason it is open**: that helper provides install, uninstall, and backup-repair paths for all four platforms and has no bash sibling, so POSIX users have no equivalent repair route. Sub-task 1.2 forbids porting it to bash, and correctly: a second shell script would recreate exactly the dual-implementation drift this phase removed.
- **Suggested next step**: expose install / uninstall / repair through the cross-platform `nexus-hub` CLI, whose `scripts/nexus_hub_cli.py` Phase 5 already extends with an `autonomy` subcommand. One implementation, three operating systems. If Phase 5 ships without it, carry this entry forward rather than closing it.

### WN-1 - OPEN (carried, environmental): `test_bootstrap.py` PowerShell hand-off failure

- **Target file**: `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.4 (confirmed pre-existing, not caused here)
- **Reason it is open**: this fails in the Windows Git-Bash development environment on an environmental `tar` quirk. It is the v3.15.0 WN-1 item, which the v3.17.0 plan's dependency section predicted would recur during installer work. CI is authoritative for this test and passes.
- **Suggested next step**: none in this cycle. Do not treat a local failure of this one test as a regression from Phase 1; the phase touched neither the bootstrap scripts nor the tarball path.

### BG-1 - CLOSED in Phase 1: `installer.ps1` kept mutation-capable entries on upgrade

- **Target file**: `scripts/installer.ps1` (`Install-Permissions`), `scripts/merge_permissions.py`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2 / amendment A3 bug 2
- **What was wrong**: the checkpoint commit converted `installer.sh` to the shared `merge_permissions.py` helper and left `installer.ps1` on its own native union merge. A union cannot retire an entry, so removal propagation -- the fix that strips retired mutation-capable entries from an existing user's config -- worked on macOS and Linux and silently did nothing on Windows. Every entry the Phase 1.1 hardening removed would have stayed auto-approved forever on every already-installed Windows host.
- **Why it is recorded rather than dropped**: this is amendment A2's thesis demonstrated inside the phase that motivated it. The drift was introduced WHILE fixing the original instance of the same class, by a maintainer who cannot routinely exercise the other two operating systems. That is the argument for parity being a standing gate rather than a per-cycle rediscovery.
- **Resolution**: `installer.ps1` ported to `merge_permissions.py`, which is now the only merge implementation in the repository. Both installers are asserted byte-identical for the same input by `tests/installer/test_permission_scope_parity.py::test_both_installers_produce_an_identical_merged_config`, which also asserts the retired entry is gone, the user-added entry survives, and template metadata does not leak. The Copilot scalar key was routed through the same helper, which additionally removed the `jq` dependency that made the new Git-Bash arm reachable.

### BG-2 - CLOSED in Phase 1: the validator passed its own motivating example

- **Target file**: `scripts/validate_permission_baseline.py` (rule 3b, `UNSAFE_SUBCOMMANDS` / `DUAL_MODE_SUBCOMMANDS`)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.4 (found by the tests written for 1.3)
- **What was wrong**: `Bash(gh api *)` -- the entry the validator's docstring cites as its motivating example, and the exact fixture sub-task 1.3's acceptance criterion names -- **passed**. Rule 3 asks only that a dual-mode tool's first argument be pinned to a literal subcommand, and `api` is one; but `gh api` remains dual-mode at the flag level, so no depth of pinning excludes `--method DELETE`. `Bash(gh repo *)` (admits `gh repo delete`) and `Bash(git branch *)` (admits `-D`) had the same hole.
- **Resolution**: data-driven rule 3b, in the module's established one-line-to-extend style. `UNSAFE_SUBCOMMANDS` holds pairs no pinning rescues because the mutating switch is a flag rather than a verb; `DUAL_MODE_SUBCOMMANDS` holds pairs needing one more level of pinning. The shipped baselines pass unchanged, because every shipped entry already pins at depth two (`gh pr view *`, `git branch --list *`, `docker compose config *`).
- **Lesson worth keeping**: an acceptance criterion is not satisfied by a validator that merely exists. This one was verified during 1.3 against an injected fixture that happened to use a different shape, and the named fixture was never actually run until 1.4.

### BG-3 - CLOSED in Phase 1: the hardening broke 14 tests of the bash description hook

- **Target file**: `catalog/hooks/tests/test_format_bash_description.py`
- **Source phase**: v3.17.0 Phase 1.1 (introduced by checkpoint commit `9023e6c9`), found in 1.4's full-suite run
- **What was wrong**: that suite builds its pattern list by parsing the LIVE `configs/permissions/claude-permissions.json`, so the Phase 1.1 removals (`awk`, `find`, `cat`, `echo`) broke 14 of its tests. The breakage was already on `develop`, which means it would have turned CI red for any release cut from `develop` - including a v3.16.7 release that has nothing to do with permissions.
- **Resolution**: split by what each test is actually about. Seven exercise the PARSER's structural handling (if / elif / else, `select`, for-loop bodies, prefix variable assignments) and merely used `echo` as filler; they now measure against a module-level `STRUCTURAL_PATTERNS` list, so catalog policy and parser behavior can no longer break each other. The other seven were genuine policy assertions and are inverted, each with the I6 reasoning recorded inline and a note that little real capability is lost because Claude Code's built-in read-only set already covers `find` / `cat` / `echo` with real redirect analysis (matcher findings 3 and 5). One test was added asserting the rest of the pipeline vocabulary survived, so a future over-broad removal is caught.
- **Lesson worth keeping**: a config change is a code change when a test suite reads that config. The coupling was invisible from the diff of the permission file, and only a full-suite run surfaced it - which is the argument for running the whole suite at the phase gate rather than only the suites a phase's own files live in.

## v3.17 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented by design / unverified (`NI-#`) | 2 (NI-1, NI-2) | 0 |
| Deferred (`DF-#`) | 3 (DF-1, DF-2, DF-3) | 0 |
| Bugs (`BG-#`) | 0 | 3 (BG-1, BG-2, BG-3) |
| Warnings (`WN-#`) | 1 (WN-1, environmental, carried from v3.15.0) | 0 |
| Missing tests (`MT-#`) | 0 | 0 |
| Quality-gate bypasses (`QG-#`) | 0 | 0 |

**Release blockers**: 0. NI-1 is the only item that could change a design decision, and it is scheduled to ride Phase 4.1's live-build session.
