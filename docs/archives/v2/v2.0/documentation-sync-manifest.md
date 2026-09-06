# Documentation Sync Manifest -- v2.0.0 Phase 7.1

**Date**: 2026-05-20
**Phase**: 7.1 (run `/update-documentation` for stale brand references)
**Plan**: [`docs/archives/v2/v2.0/plans/nexus-hub-rename.md`](plans/nexus-hub-rename.md)

## Purpose

Audit every documentation surface outside the `catalog/`, `templates/`, `extensions/`, and `scripts/` directories that were already renamed in Phases 2-6. Rebrand active surfaces; preserve historical snapshots.

## Files edited

| File | Reason | Variant replacements |
|---|---|---|
| `docs/CATALOG-COVERAGE.md` | Active current-state matrix; references to renamed extensions and scripts must point at the new names. | `DevAI-Hub` -> `Nexus-Hub`; `devai-code-search` -> `nexus-code-search`; `devai-web-fetch` -> `nexus-web-fetch`; `devai_mcp_benchmark.py` -> `nexus_mcp_benchmark.py`; `.cursor/rules/devai-hub.mdc` -> `.cursor/rules/nexus-hub.mdc`. |
| `docs/permissions-setup.md` | Active operator guide referencing the brand, installer script names, and trusted-domains config path. | `DevAI-Hub` -> `Nexus-Hub`; `Install-DevAI-Permissions.ps1` -> `Install-Nexus-Hub-Permissions.ps1`. |
| `guides/CLAUDE_CODE_PROJECT_SETUP.md` | Active project-setup guide. | `DevAI-Hub` -> `Nexus-Hub` (global). |
| `guides/CONTRIBUTING.md` | Active contributor guide; clone URLs. | `devai-hub` -> `nexus-hub` (clone URL + cd target). |
| `guides/RTK_CONTEXT_COMPRESSION.md` | Active guide. | `DevAI-Hub` -> `Nexus-Hub`. |
| `guides/CLAUDE_CODE_SETTINGS_REFERENCE.md` | Active reference. | `DevAI-Hub` -> `Nexus-Hub`. |
| `guides/TOKEN_OPTIMIZATION.md` | Active reference; documented env-var prefixes. | `DevAI-Hub` -> `Nexus-Hub`; `DEVAI_DISABLED_HOOKS` -> `NEXUS_DISABLED_HOOKS`; `DEVAI_HOOK_PROFILE` -> `NEXUS_HOOK_PROFILE`. |
| `guides/SUBAGENTS_GUIDE.md` | Active guide footer cross-link. | `[DevAI-Hub]` -> `[Nexus-Hub]`. |
| `guides/SESSION_LIFECYCLE_DECISIONS.md` | Active guide; "DevAI-Hub comparison notes" attribution line. | `DevAI-Hub` -> `Nexus-Hub`. |
| `guides/MCP_DEVELOPMENT_SERVERS.md` | Active MCP catalog guide. | Internal MCP names (`devai-skill-server`, `devai-code-search`, `devai-web-fetch`); Python module names (`devai_skill_server`, `devai_code_search`); env var (`DEVAI_HUB_ROOT`); index path `.devai/` -> `.nexus/`; all prose references. |

## Files intentionally NOT edited (historical snapshots)

| File | Reason |
|---|---|
| `docs/security/penetration-test-2026-04-27.md` | Dated security assessment of v1.0.0 release candidate; reflects the codebase state at 2026-04-27 with the old artifact names. Falsifying historical security findings would break audit chain-of-custody. Treated like frozen `docs/archive/v1/v1.0/` content. |
| `docs/git/gitignore-audit-2026-04-22.md` | Dated gitignore audit; same rationale. |
| `docs/v0.*/*` | Historical version directories; per the plan, frozen and not edited. |
| `docs/v1.*/*` | Same. |
| `docs/archive/*` (if present) | Same. |
| `docs/archive/v2/v2.0/baselines/*` | Pre-rename validator baselines captured at Phase 1.1; intentionally contain the old names to document the starting state. |
| `docs/archive/v2/v2.0/installer-smoke-pre.txt` | Pre-migration smoke capture. |
| `docs/archive/v2/v2.0/rename-inventory.md` | The rename inventory itself; the "from" column needs the old names. |
| `docs/archive/v2/v2.0/rename-decisions.md` | The naming canon decision record; documents both old and new names by construction. |
| `docs/archive/v2/v2.0/rename-manifest.txt` | Output of `scripts/apply_rename.py` from Phase 5.1. |
| `docs/archive/v2/v2.0/plans/nexus-hub-rename.md` | The plan document; references the old name when describing the rename surface. |
| `docs/archive/v2/v2.0/development/history/*` | Phase-by-phase history records; intentional historical narrative. |
| `CHANGELOG.md` | Historical entries for prior versions intentionally reference the old name. The v2.0.0 entry being written in Phase 7.5 will introduce the new name with explicit "Renamed from DevAI-Hub" framing. |
| `README.md` | Already updated in Phase 6; carries the "Renamed from DevAI-Hub" callout intentionally. |
| `docs/permissions-research.md` | No DevAI brand strings to update (verified). |

## Files flagged for follow-up review (NOT edited)

None. Every file in scope for this sub-task was either edited or explicitly classified as historical.

## Additional active-surface fixes during 7.6 stability gate

The residual-rename grep at the 7.6 stability gate caught additional active surfaces missed by the original 7.1 sweep. All were edited:

| File | Reason | Variant replacements |
|---|---|---|
| `CODE_OF_CONDUCT.md` | Stale GitHub issues URL. | `bendourthe/DevAI-Hub/issues/new` -> `bendourthe/Nexus-Hub/issues/new`. |
| `CONTRIBUTING.md` | Active contributor guide H1 and intro. | `DevAI-Hub` -> `Nexus-Hub` (two occurrences). |
| `GEMINI.md` | Active per-platform AI-instruction file title. | `Gemini CLI Instructions -- DevAI-Hub` -> `Gemini CLI Instructions -- Nexus-Hub`. |
| `SECURITY.md` | Active security posture document; many references to the brand and the three internal MCP names. | Global `DevAI-Hub` -> `Nexus-Hub`; `devai-skill-server` -> `nexus-skill-server`; `devai-code-search` -> `nexus-code-search`; `devai-web-fetch` -> `nexus-web-fetch`. The GitHub URL inside the supply-chain caveat updated by the same global replacement. |
| `data/report_data.json` | Static JSON consumed by `/generate-report` when producing the codebase report; title / subtitle / author / executive_summary fields. | Global `DevAI-Hub` -> `Nexus-Hub`. |
| `llms.txt` | Top-level descriptor consumed by LLM-discovery tooling. | H1 `# DevAI-Hub` -> `# Nexus-Hub`. |
| `scripts/generate_report.py` | Default author string in the report-generation utility. | `"DevAI-Hub Agent"` -> `"Nexus-Hub Agent"`. |
| `scripts/optimize_skill_description.py` | Module docstring and inline prompt template referencing the project name. | Global `DevAI-Hub` -> `Nexus-Hub`. |
| `scripts/package_skill.py` | Module docstring, inline comments, and argparse description. | Global `DevAI-Hub` -> `Nexus-Hub`. |
| `scripts/validate_skills.py` | Module docstring and argparse description. | Global `DevAI-Hub` -> `Nexus-Hub`. |
| `infrastructure/tools/build_skills_catalog.py` | Catalog-builder source-of-truth; four hardcoded literals that previously caused regeneration drift (BG-001). | Two `https://github.com/bendourthe/DevAI-Hub` -> `https://github.com/bendourthe/Nexus-Hub`; one `# DevAI-Hub Skill Index` H1 -> `# Nexus-Hub Skill Index`; one description literal updated. Closes BG-001. |

## Known intentional residuals (not blocking)

The Phase 7.6 stability gate grep (with the documented exclusions) returns residual hits only in these intentional surfaces:

1. **`README_zh.md`** -- the Chinese translation of the README. Lines 9, 13, 15, 61 carry the equivalent of the "Renamed from DevAI-Hub" callout block and the historical "v1.0.0 release notes (when the project was named DevAI-Hub)" framing. These are deliberate -- the Chinese README mirrors the English README's "renamed from" pattern in the localized language. The grep's approved-phrasing filter is English-only (`Renamed from DevAI-Hub` / `previously known as DevAI-Hub` / `formerly DevAI-Hub`) and so does not catch the Chinese equivalents.
2. **`docs/DEVLOG.md`** -- the v2.0.0 Phase 1-7 entries describe the rename effort. Every reference to `DevAI-Hub` / `devai-*` / `DEVAI_*` in those entries is in the explanatory context of what was renamed and why. The DEVLOG is the project's authoritative narrative log; gutting the rename narrative to make the grep pass would destroy its value. The plan's stability gate intent is "no stale brand strings in active user-visible surfaces" -- the DEVLOG is a development log read by future maintainers, not an end-user surface.
3. **`scripts/installer.sh` / `scripts/installer.ps1`** -- the legacy-install migration code (sub-task 3.3) MUST reference the old `~/.devai-hub/` path to detect and rename it. Three references each: a function-header comment, the path literal, and the user-facing migration prompt ("Detected existing DevAI-Hub install at $legacy"). These are operationally required.
4. **`scripts/apply_rename.py`** -- the bulk-rename utility that drove the Phase 5.1 sweep. By construction it carries every old name in its variant tuples; the file is allowlisted as a developer-only utility per the Phase 5 DEVLOG entry.

All four intentional residuals are documented here so the Phase 8 final-validation grep does not chase them.


## Cross-references to other Phase 7 sub-tasks

- `docs/DEVLOG.md` is touched in sub-task 7.3, not here.
- `catalog/hooks/settings.json` and other `settings.json` examples are touched in sub-task 7.2.
- `.gitignore` is audited in sub-task 7.4.
- `CHANGELOG.md` v2.0.0 block and `docs/archive/v2/v2.0/RELEASE_NOTES.md` are authored in sub-task 7.5.

## Verification

After sub-task 7.1, the residual-rename grep over active doc surfaces (excluding the historical exclusions above) returns zero matches:

```
grep -rn "DevAI-Hub\|devai-hub\|devai_hub\|DEVAI_HUB" docs/CATALOG-COVERAGE.md docs/permissions-setup.md docs/permissions-research.md guides/
```

returns no output.
