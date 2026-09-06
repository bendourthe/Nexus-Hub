# Org Knowledge Layer - Deep Research (supporting v3.17.4)

**Date**: 2026-08-13
**Question**: How should a Nexus-Hub user connect the generic catalog (skills, commands, rules, hooks, instruction templates) to their organization's internal practices, conventions, standards, and style, so that org-specific guidance layers over the generic defaults on every supported platform?

## 1. External prior art (verified against official docs)

### Per-platform org mechanisms and precedence

| Platform | Org-level mechanism | Documented precedence | Verified |
|---|---|---|---|
| Claude Code | Managed policy CLAUDE.md (`/etc/claude-code/`, `C:\Program Files\ClaudeCode\`, or `claudeMd` key in `managed-settings.json`); `.claude/rules/` with symlinks explicitly documented for company standards; plugin marketplaces with `extraKnownMarketplaces` + `enabledPlugins` + managed allowlists | Managed layer non-overridable; memory layers CONCATENATE (managed, user `~/.claude/CLAUDE.md`, project `CLAUDE.md`, `CLAUDE.local.md`); settings: Managed > CLI > Local > Project > User | Yes (code.claude.com/docs/en/memory, /settings, /plugin-marketplaces) |
| Cursor | Team Rules (Team/Enterprise dashboard, admin-enforceable); remote `.mdc` import from GitHub into `.cursor/rules/imported/` | Team Rules > Project Rules > User Rules | Yes (cursor.com/docs/context/rules) |
| Codex / AGENTS.md standard | None built in; repo-committed AGENTS.md by convention; `~/.codex/AGENTS.override.md` then `~/.codex/AGENTS.md`; `project_doc_fallback_filenames` | Nearest file to edited code wins; root-down concatenation; 32 KiB combined budget silently truncates | Yes (Codex docs, agents.md) |
| GitHub Copilot | Organization custom instructions (GA April 2026, Business/Enterprise, org settings) | Personal > Repository > Organization (the INVERSE of Claude/Cursor; all sets concatenated, soft priority only) | Yes (docs.github.com + changelog) |
| Gemini CLI / Antigravity | None; hierarchical GEMINI.md / `.agents/rules/` by convention. Known pitfall: both products hardcode `~/.gemini/GEMINI.md` (gemini-cli issue #16058) | General-to-specific tree walk | Yes (geminicli.com, antigravity.google/docs) |

### Cross-platform patterns

- **Single-source fan-out (the Ruler pattern)**: canonical org rules as plain Markdown in one directory or git repo, a sync tool projects them into each assistant's native file with source markers. Validated by `intellectronica/ruler` and `yelmuratoff/agent_sync`. This is exactly Nexus-Hub's problem space, solved as generation rather than hand-maintenance.
- **AGENTS.md as convergence point**: one repo-root AGENTS.md read natively by Codex/Cursor/Copilot/Gemini, imported by Claude via `@AGENTS.md` (officially recommended). Nexus-Hub already uses this.
- **Claude plugin marketplaces**: the most complete org channel in the ecosystem (git-hosted catalog, auto-prompt on folder trust, managed allowlists, release channels). Claude-only.

### Ecosystem-wide constraints

1. The ecosystem has NOT converged on whether org guidance is a ceiling (Claude managed, Cursor Team) or a floor (Copilot). A cross-platform feature must report per platform whether org content lands as "enforced", "default", or "advisory".
2. Always-loaded content is budgeted: Anthropic recommends <200 lines; Codex truncates at 32 KiB combined. The org layer needs a short always-on core plus path-scoped or on-demand detail (the same Tier-1/2/3 discipline the catalog already applies).
3. Instructions are context, not enforcement. Anything that MUST hold belongs in hooks and permissions, not prose.
4. Conflicting instruction sets cause arbitrary picking (Claude docs verbatim); precedence must be stated explicitly in the rendered text, not assumed.

## 2. In-repo integration points (verified against source)

### The primary seam: `IntegrationBase.install()` (`scripts/lib/integrations/base.py:154-194`)

The v3.16.0 `platform_defaults.py` precedent: a step added to the install dispatcher reaches all 16 registered platforms at both scopes with ZERO edits to either installer (AGENTS.md documents this explicitly). Same triad to reuse: seed-if-absent, preserve-what-we-did-not-write, degrade-never-fail; manifest tracking wrapped so it can never break an install.

### Supporting seams

- **Template token**: `MarkdownIntegration._effective_template_vars` (`base.py:528-538`) auto-loads `{{SKILL_INDEX}}`; an `{{ORG_KNOWLEDGE}}` token can be resolved the same way (substitute if the org source is connected, leave literal or strip if not). The claude-only tokens (`{{AGENT_REGISTRY}}` etc.) are the precedent for optional-per-template tokens excluded from the parity guard (`check_base_template_parity.py:115-116`).
- **Second marker block**: `instruction_merge.merge_marker_section` already parameterizes markers (`instruction_merge.py:56-62`); a `<!-- NEXUS_HUB_ORG_START/END -->` block below the Nexus block gives org content an independently replaceable slice with positional precedence.
- **Rules mirroring**: `SkillsIntegration._mirror_catalog` (`base.py:762-844`) with each platform's `rules_subdir` distributes rule FILES; rules are policy infrastructure and are never filtered by selection (`base.py:826-830`).
- **CLI**: `scripts/nexus_hub_cli.py` intercept-before-argparse pattern (`:518-520`, `:551-562`) is the template for a new subcommand; the `--branch` fetch machinery (`sanitize_branch_name`, `~/.nexus-hub/branches/` cache) is the hardened precedent for cloning an org repo by URL; `_safe_resolve` (`base.py:36-54`) for local paths.
- **Declarative config**: `configs/platform-defaults.json` + `configs/README.md` is the model for a repo-internal schema/validator/example with the actual content living outside the repo.
- **Authoring reuse**: `catalog/templates/constitution-template.md` and the `project-constitution` skill already carry the vocabulary an org layer needs (binding scope, Applies to, conflict resolution).

### Constraints that will bite (from AGENTS.md and source)

1. Lockstep parity guard on the five guarded `base-*.md`; 12 substantive templates total, seven unguarded ones are the silent-miss risk.
2. New `scripts/<name>.py` needs explicit-name copy steps in BOTH installers (unless repo-internal, then `DEV_ONLY_SCRIPTS`).
3. Do-not-invent-a-platform-lever (hard rule): no org/priority config key on any platform without a fetched official vendor doc + VERIFIED classification. "No lever documented" is a valid result; the fallback is text and files.
4. New platform READ PATHS belong in `docs/policy/platform-read-contracts.{json,md}`, which hard-gates releases via the freshness check.
5. `rsync --delete` refresh-mode pruning deletes anything materialized INSIDE a synced catalog tree; org files must be staged into the source before copy or written outside the synced tree.
6. Cross-installer parity is a standing release gate (v3.17.0 Amendment A2); the `IntegrationBase.install()` seam sidesteps it by touching neither installer.
7. The catalog is deliberately company-neutral (v1.1 comparison record); org content must live OUTSIDE `catalog/`.
8. Commit-visibility: anything landing in a project repo (e.g. `.claude/rules/org/`) is commit-visible; prefer opt-in + never-overwrite for those surfaces.
9. `InstallContext` additive-field convention; manifest lockstep (track or `doctor`/`repair`/`teardown` will not see the writes); CHANGELOG Unreleased entry mandatory.

### Versioning

v3.17.3 is reserved for the corrective Cursor-hook and usage-monitor release, so **v3.17.4 is the next free slot**. v3.17.0 Amendment A1 touched the `base-*.md` set; v3.17.4 must sequence on top of the released v3.17.0 through v3.17.3 state. Plan format follows AGENTS.md's current model-routing contract (separate tier and effort columns plus a `## Current model map`), not v3.17.0's older single-column shape.

## 3. Design options

### Option A - Connected org source + per-platform projection (recommended)

The user's original idea, upgraded by the research. The organization maintains a directory or git repo of plain-Markdown standards plus a small manifest (`org.json`: name, precedence statement, which docs are always-on vs on-demand, optional per-language rules). A `nexus-hub org connect <path-or-url>` subcommand records the connection in the manifest and materializes it; the `IntegrationBase.install()` seam re-materializes on every install/upgrade so the org layer survives catalog refreshes. Projection per platform: an org marker block in each instruction file (positioned after the Nexus block, with an explicit "org standards take precedence over the generic guidance above" sentence), org rules files mirrored next to catalog rules where the platform has a rules surface, and a per-platform "enforced / default / advisory" report. A guided authoring surface (skill + `/org` command scope or an extension of existing commands) teaches the org how to collect, organize, and budget their documents (constitution-template reuse, <200-line always-on core, on-demand references).

- Pros: works on all 16 platforms; zero installer edits for the core (dispatcher seam); idempotent with `upgrade`; matches every shipped precedence primitive; the Ruler pattern proves the shape.
- Cons: largest scope of the three; needs a read-contract decision if any new per-platform read path is introduced (mitigable by writing only into surfaces Nexus-Hub already owns).

### Option B - Guidance only (skill + templates, no code)

Ship an `org-standards` authoring skill and template pack instructing organizations to use each platform's NATIVE org mechanism (managed CLAUDE.md, symlinked `.claude/rules/`, Cursor Team Rules, Copilot org instructions, repo AGENTS.md sections).

- Pros: tiny, zero code risk, teaches the durable platform-native mechanisms.
- Cons: no automation; nothing survives `nexus-hub upgrade` by construction; per-platform manual work for the org; does not deliver the "connect a directory" experience the user described.

### Option C - Installer-integrated prompt

Ask during `installer.sh` / `installer.ps1` runs whether to connect an org directory.

- Pros: maximum discoverability at install time.
- Cons: violates the v3.7.0 no-prompt install posture; touches both installers, triggering the parity gate; conflates a per-machine choice with a per-org configuration.

### Recommendation

**A**, with B's authoring guidance folded in as one phase (the guided "how to collect and organize your documents" experience the user asked about), and C reduced to a non-interactive pointer: the installer end-of-run summary mentions `nexus-hub org connect` when no org is connected. Enforcement-grade org policy (hooks, permissions, managed settings) is documented as the platform-native escalation path, not implemented in v3.17.4.

## 4. Sources

- https://code.claude.com/docs/en/memory, /settings, /plugin-marketplaces
- https://cursor.com/docs/context/rules
- https://learn.chatgpt.com/docs/agent-configuration/agents-md, https://agents.md/
- https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot and the 2026-04-02 GitHub changelog (org custom instructions GA)
- https://geminicli.com/docs/cli/gemini-md/, https://antigravity.google/docs/rules-workflows, gemini-cli issue #16058
- https://github.com/intellectronica/ruler, https://github.com/yelmuratoff/agent_sync (secondhand, multiply corroborated)
- In-repo: `scripts/lib/integrations/base.py`, `platform_defaults.py`, `instruction_merge.py`, `configs/README.md`, `check_base_template_parity.py`, `AGENTS.md`, `docs/v3/v3.17/plans/v3.17.0-agent-autonomy-toggle.md`
