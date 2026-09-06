# Nexus-Hub v2.3.0 Release Notes

**Release date**: 2026-05-29
**Type**: Minor (SemVer) - additive, local, zero new outbound calls / credentials / third-party data processors
**Plan**: [adoption-ecc-cybersec-skills](plans/adoption-ecc-cybersec-skills.md)
**Predecessor**: [v2.2.0](../v2.2.0/RELEASE_NOTES.md)

## Overview

v2.3.0 adopts every in-scope capability from the two v2.2.0 cross-project comparisons - the ECC multi-harness operator OS and a 754-skill cybersecurity content library - as local, zero-outbound Nexus-Hub content, and carries forward and resolves all 12 open v2.2.0 known-gaps. Adoption was sequenced strictly by the MCP Registry Policy decision tree (reverse-engineer-first): skill-native replacements shipped first, then `re-full` / `re-partial` internal builds; `drop-outright` and vendor-intrinsic items never entered the active phases (they are recorded in the plan's "Items explicitly NOT adopted" appendix). Every adopted item is local and outbound-call-free. The release adds zero new third-party data processors, zero new API keys, and only local tree-sitter grammar dependencies.

The catalog grows to **227 skills across 23 categories** (a new `security-operations` category with 15 re-authored defensive skills).

## Highlights by phase

1. **Skill-native foundations** - `context-modes` (dev/review/research working modes) and `security-framework-mapping` skills, plus an optional security-framework-mapping frontmatter convention (`mitre_attack` / `atlas_techniques` / `d3fend_techniques` / `nist_csf` / `nist_ai_rmf`).
2. **Security and quality CI validators** - four local, read-only, zero-outbound static validators (`validate_no_personal_paths.py`, `validate_unicode_safety.py`, `scan_supply_chain_iocs.py`, `validate_workflow_security.py`) wired into `make validate`, both installers, and CI.
3. **Runtime learning** - local-only memory-persistence session hooks (a project-scoped context digest) and a `continuous-learning` skill + `learning-capture` hook, with the external-observer egress trap explicitly out of scope.
4. **Installer lifecycle and selective install** - an additive install-state manifest, `doctor` / `repair` / `list-installed` subcommands, selective-install profiles/modules, a `nexus-hub consult` natural-language advisor, and a deterministic `harness_audit.py` scorer.
5. **Skill quality tooling** - a `skill-stocktake` audit skill, a `skill-create` git-history-driven generator skill, and a non-blocking quality-heuristics pass in `validate_skills.py`.
6. **Framework coverage + defensive security content** - `build_framework_coverage.py` over the framework-mapping frontmatter, plus 15 re-authored defensive skills under the new `security-operations` category (DFIR, threat hunting, incident response, cloud / endpoint / phishing detection), each framework-tagged and re-authored from public MITRE / NIST knowledge (no third-party text, no source attribution in the artifact).
7. **Installer instruction-file parity** - the Python registry runner reached byte parity with the legacy bash `render_template`; both installers now share a single instruction-file renderer. Closes v2.2.0 DF-001 / MT-1 / MT-2.
8. **Code-graph quality + extractor expansion** - Go / Rust / Java / C# tree-sitter extractors, `instantiates` / `overrides` edges for Python/TypeScript, name-scoped FTS search (aggregate eval precision 63.3% -> 96.2%, recall held at 100%), and the `pathspec` deprecation fix. Closes v2.2.0 WN-1 / WN-5 / WN-6 / WN-7 / DF-002.
9. **Live-environment verification** - verified the deferred Antigravity CLI assumptions against Google's now-public documentation and re-ran the cross-OS installer smoke. Closes v2.2.0 WN-2 / WN-3 / WN-4 / WN-8.

## Phase 9 in detail (Antigravity CLI corrections + cross-OS smoke)

The v2.2.0 probe had *inferred* the Antigravity CLI on-disk conventions by analogy to Gemini CLI. With the Antigravity CLI documentation now public (ahead of the 2026-06-18 Gemini CLI sunset), Phase 9 verified them against Google's primary docs + official codelabs and corrected several:

- **Binary name**: `agy` (installs to `~/.local/bin/agy`), not the inferred `antigravity`. This fixed a silent-failure bug - the diff-review hook fails open when the binary is absent, so the wrong name had made the entire Antigravity pre-commit review a no-op on every machine.
- **Per-project directory**: `.agents/` (plural), not `.agent/`.
- **Instruction file**: `AGENTS.md`, not `AGENT.md`. Written to `.agents/AGENTS.md` to avoid clobbering the codex-managed root `AGENTS.md` shared marker block.
- **Global directory**: `~/.gemini/antigravity-cli/`, not `~/.agent/`.
- **Workflow format**: Markdown under `.agents/workflows/` (the inferred value was correct); YAML frontmatter honored; workflow name derived from filename.

The cross-OS smoke was re-run: Windows is empirically green (936 pytest cases, eval recall 100% / precision 96.2%, installer probes clean), the Linux Python test suite is empirically green via CI on ubuntu-latest (replacing the v2.2.0 PASS-by-parity inference), and macOS plus the Linux installer-probe/eval portion are deferred to a packaged-binary release.

## Known gaps carried forward

All 12 ingested v2.2.0 known-gaps are resolved or re-deferred with evidence. Remaining open items in [`docs/archives/v2/v2.3/known-gaps.md`](known-gaps.md) are pre-existing catalog-quality debt and two new low-priority Phase 9 residuals - none is a source-release blocker:

- **WN-v23-5** - Antigravity CLI conventions are docs-verified, not live-VM-verified; four residuals (`.agent/` vs `.agents/` codelab dissent, exact global subpath, `subagents/`/`rules/` subdirs, root-vs-`.agents/` instruction file) await a live `agy` probe.
- **DF-v23-6** - the macOS full installer smoke and the Linux installer-probe/eval portion are deferred to a pre-packaged-binary release.

## Upgrade notes

v2.3.0 is a **source release**. Downstream consumers (Nexus, Claude Code, Antigravity, Codex, Cursor, etc.) re-verify on their own target OS during adoption. Re-running the installer picks up the new skills, validators, hooks, lifecycle commands, and the corrected Antigravity paths. No breaking changes; default behavior is preserved for every integration. Users of the opt-in Antigravity diff-review hook should note it now invokes the `agy` binary.
