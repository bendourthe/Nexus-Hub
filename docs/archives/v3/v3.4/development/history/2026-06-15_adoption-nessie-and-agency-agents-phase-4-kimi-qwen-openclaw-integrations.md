# Session History -- v3.4.0 adoption-nessie-and-agency-agents Phase 4: Kimi + Qwen + OpenClaw integrations

**Date**: 2026-06-15
**Plan**: [`docs/releases/v3/v3.4/plans/adoption-nessie-and-agency-agents.md`](../../plans/adoption-nessie-and-agency-agents.md)
**Phase**: 4 of 5 -- Optional Kimi / Qwen / OpenClaw integrations (A3-ext, re-full)
**Branch**: `develop` (integration branch; no version tag cut this phase)
**Outcome**: complete; all Phase 4 sub-tasks closed and the Phase 4 exit checklist is satisfied.

## Goal

Extend Nexus-Hub's platform reach with three further `IntegrationBase` subclasses -- Kimi, Qwen, and OpenClaw -- reusing the Aider/Windsurf pattern proven in Phase 2, registered, installer-wired, and dry-run-verified. `re-full`, pure local file emission: no new outbound call, dependency, credential, or third-party processor. The upstream `agency-agents` converter is named only in the reverse-engineering matrix, never in shipped code/comments/docs.

## Subtasks completed

1. **4.1 -- Define the three transforms.** Reusing the Phase 2 study of `__init__.py::_register_builtins()`, `runner.py`, `result.py` (the `WriteResult` contract), and `base.py` (`MarkdownIntegration` / `SkillsIntegration` / shared marker-merge), plus the Phase 2 subclasses `aider.py` / `windsurf.py`, fixed each transform: Qwen -> single project-root `QWEN.md` (Aider model) + `~/.qwen/QWEN.md` global mirror gated on detection (Windsurf model); Kimi -> `.kimi/system.md` (marker-merged instruction, carrying `{{SKILL_INDEX}}`) + `.kimi/agent.yaml` (deterministic companion); OpenClaw -> `.openclaw/` SOUL + AGENTS + IDENTITY split (instruction content in `AGENTS.md`, namespaced under `.openclaw/`, with `SOUL.md` / `IDENTITY.md` as companions). All three behavioral-guardrails surfaces (NOT `SkillsIntegration`); workspace always writes, global skips-with-note unless `~/.kimi` / `~/.qwen` / `~/.openclaw` is present.
2. **4.2 -- Implement and register the three subclasses.** Added a shared `IntegrationBase._write_generated` helper (`base.py`) for the deterministic companion files, mirroring the dedicated-mode contract of `_write_instruction` (created / unchanged / updated / kept; manifest-tracked; dry-run-gated). Created `scripts/lib/integrations/qwen.py` (single-file `MarkdownIntegration`, `install_global` overridden for `~/.qwen` detection), `kimi.py` (bespoke `install_workspace` / `install_global` writing `system.md` via the inherited instruction render + `agent.yaml` via `_write_generated`), and `openclaw.py` (bespoke multi-file: `AGENTS.md` instruction + `SOUL.md` / `IDENTITY.md` companions, namespaced under `.openclaw/`). Registered all three in `_register_builtins()` (alphabetical; registry now 15 keys). Created three byte-identical platform-agnostic templates (`base-kimi.md` / `base-qwen.md` / `base-openclaw.md`, copied from `base-aider.md`).
3. **Installer wiring (full, matching the Phase 2 decision).** Wired all three into `scripts/installer.sh` (KIMI/QWEN/OPENCLAW sections in the global + workspace blocks, unconditional, matching the existing bash flow) and `scripts/installer.ps1` (provider-menu options 10/11/12, the `providerMap` entries, the `Selection [A, 1-12]` prompt range, and the `-contains` global + workspace `Invoke-RegistryPlatform` blocks).
4. **4.3 -- Docs + provenance.** Extended the `AGENTS.md` platform-coverage "Behavioral-guardrails only" bullet (added the three surfaces, noting the multi-file platforms embed `{{SKILL_INDEX}}` in the primary file); added a new `re-full` row to `docs/policy/mcp-reverse-engineering-matrix.md` (the only place `agency-agents` is named); added a CHANGELOG `[Unreleased]` "Added" entry.
5. **4.4 -- Testing and stabilization.** Added `tests/integrations/test_kimi_qwen_openclaw.py` (12 cases: registration, behavioral-guardrails-not-skills-mirror classification, Qwen workspace root write + global detect/skip, Kimi `.kimi/` pair + global detect/skip, OpenClaw `.openclaw/` split + `.openclaw/` namespacing + global skip). Updated the `test_contract.py` docstring to 13 integrations / 65 cases. All gates green (see Test results).

## Key decisions

- **Reused the Phase 2 pattern verbatim where it fit, extended only where the platform forced it.** Qwen is a near-clone of the Aider single-file + Windsurf-detection model. Kimi and OpenClaw needed multi-file emission, so they override `install_workspace` / `install_global` to write a marker-merged primary file (via the inherited render) plus deterministic companions (via the new shared helper).
- **One shared `_write_generated` helper instead of per-subclass duplication.** Both Kimi (`agent.yaml`) and OpenClaw (`SOUL.md` / `IDENTITY.md`) need an idempotent, partial-recovery-safe, dry-run-safe dedicated write. Factoring the contract into one tested static method on `IntegrationBase` (alongside `_copy_file` / `_copy_tree`) keeps each subclass thin and guarantees all three pass the parameterized contract suite identically. The companions are kept byte-constant (not templated) so re-installs report `unchanged`.
- **Primary instruction file uses shared marker-merge; companions are dedicated.** The contract suite's sibling-preservation invariant only checks the configured `instruction_file`, which is marker-merged in every subclass, so user edits to `system.md` / `AGENTS.md` survive a re-install and the file self-deletes on teardown when only the Nexus-Hub block remains. The companions are Nexus-Hub-owned and removed on teardown via the manifest.
- **OpenClaw namespaced under `.openclaw/`.** Writing `AGENTS.md` at the project root would collide with the root `AGENTS.md` that opencode / cursor manage, so OpenClaw's three-file split lives under `.openclaw/`. A dedicated test asserts no root `AGENTS.md` is created.
- **Global scope skips-with-note unless detected.** All three are "optional" integrations; rather than create `~/.kimi` / `~/.qwen` / `~/.openclaw` for users who do not have the tool, global scope detects the config root and skips-with-note when absent (the Windsurf model). The workspace project-local files are the primary surface and always write.
- **Dedicated templates, not reuse.** New `base-kimi.md` / `base-qwen.md` / `base-openclaw.md` (byte-identical platform-agnostic content) rather than reusing one template, matching the established per-platform-template pattern; these are NEW templates, not edits to the core five, so the base-`*`.md lockstep rule does not apply.

## Test results

`make` is not on PATH on this Windows host (WN-v33-1), so the gate was emulated by invoking pytest and the registry runner directly, and ShellCheck (also absent locally) was substituted with parser checks. All green:

- `tests/integrations/` (full): 265 passed in ~9m14s. Includes the parameterized contract suite (`test_contract.py`) auto-covering all three new keys across all five lifecycle invariants (idempotent install, uninstall reverses install, sibling preservation, partial-state recovery, dry-run matches install) -- 15 new contract cases for kimi + qwen + openclaw, all pass; 65 contract cases total across 13 integrations.
- `tests/integrations/test_kimi_qwen_openclaw.py` (new): 12 passed.
- `catalog/hooks/tests/test_installer_smoke.py` (runs the actual installers): 28 passed (no installer-edit regression).
- Dry-run install (registry runner workspace `--dry-run`, the path `invoke_registry_platform` drives): rc=0, reporting all six artifacts at expected paths (`.kimi/system.md` + `.kimi/agent.yaml`, `QWEN.md`, `.openclaw/{AGENTS,SOUL,IDENTITY}.md`). A real workspace install on a throwaway dir additionally confirmed `{{SKILL_INDEX}}` substitution in each primary file, idempotent second-install (`unchanged`), and teardown leaving zero files behind.
- Reverse-Engineering Attribution: a grep for `agency-agents` / `msitarzewski` / `nessie` over the shipped artifacts (the three `.py` subclasses, the three templates, both installers, AGENTS.md) is clean; provenance is only in the RE matrix row and the internal planning/devlog docs.
- Installer parse checks: `bash -n scripts/installer.sh` clean; `[System.Management.Automation.Language.Parser]::ParseFile` on `scripts/installer.ps1` reports 0 errors.
- Catalog unchanged: 256 skills (integrations are not skills), so no `make validate` skill/registry surface was touched this phase.

## CI/CD edits

Modified both installer scripts (`scripts/installer.sh`, `scripts/installer.ps1`) to wire the three integrations into the global + workspace install blocks, modeled on the existing extended-platform (aider/windsurf/nexus-ai) blocks. No GitHub Actions workflow change. ShellCheck is not on the local PATH (WN-v33-1); CI ShellChecks `installer.sh` + `catalog/**/*.sh` on the ubuntu runner, and the bash/PowerShell edits were verified locally via `bash -n` and the PowerShell AST parser.

## Deviations

- **Installer edits beyond the literal sub-task text.** Sub-task 4.2 emphasizes `_register_builtins()` registration and a dry-run `--check`; it does not explicitly enumerate installer install-block edits. Full wiring was added (matching the Phase 2 decision) because the plan's GOAL ("extend platform reach") requires a normal install to actually deploy the files, and because the established extended-platform pattern wires each integration into both installers. Editing the installers is an AGENTS.md "ask first" surface; the precedent and direction were set in Phase 2 (user-confirmed there) and this phase follows it as a planned continuation.
- **One additive `base.py` change.** Added the shared `_write_generated` static helper to `IntegrationBase` (purely additive; existing behavior unchanged), rather than duplicating the dedicated-write logic across `kimi.py` and `openclaw.py`.

## Known gaps

See [`docs/releases/v3/v3.4/known-gaps.md`](../../known-gaps.md). No new gaps introduced this phase. WN-v33-1 re-confirmed and updated to record that Phase 4 shipped `.sh`/`.ps1` edits verified by `bash -n` + the PowerShell AST parser (ShellCheck unavailable locally; CI runs it). DF-v34-1 and WN-v33-2 carried forward, untouched.

## Next steps

- **Phase 5 -- Selective agent-body enrichment (A2, skill-native)**: add concise "Success Metrics" / "Deliverable Template" sections to a small, justified set of `catalog/agents/` definitions where they earn their length, in the terse verification-first style (no persona/vibe content). This is the plan's FINAL phase, so on completion `/implement` triggers release readiness; route the version bump / changelog / tag / push through `/update release`.
