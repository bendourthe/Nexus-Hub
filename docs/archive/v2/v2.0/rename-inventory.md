# Rename Inventory -- DevAI-Hub to Nexus-Hub

**Phase**: v2.0.0 Phase 1 sub-task 1.2
**Captured**: 2026-05-19 on Windows 11 / Python 3.12 (PYTHONUTF8=1)
**Source plan**: `docs/archive/v2/v2.0/plans/nexus-hub-rename.md`
**Purpose**: Authoritative enumeration of every directory, file, identifier, and string variant that must change as part of the v2.0.0 rename. Downstream phases reference this file as the source of truth for what to replace and what NOT to replace.

This inventory captures the **pre-rename state** of the repository at the `v1.4.0` head. Every count and path is reproducible from the commands recorded in each section.

---

## 1. Directory renames

Command run: `find . -type d -iname "*devai*" -not -path "./node_modules/*" -not -path "./.git/*"`

| Old path | New path | Notes |
|---|---|---|
| `catalog/skills/workflow/using-devai-hub/` | `catalog/skills/workflow/using-nexus-hub/` | Phase 5 sub-task 5.3 -- also re-registers in `data/`. |
| `extensions/devai-skill-server/` | `extensions/nexus-skill-server/` | Phase 4 sub-task 4.1 -- use `git mv` to preserve history. |
| `extensions/devai-skill-server/src/devai_skill_server/` | `extensions/nexus-skill-server/src/nexus_skill_server/` | Nested Python package; `pyproject.toml` package name updated. |
| `extensions/devai-code-search/` | `extensions/nexus-code-search/` | Phase 4 sub-task 4.1. |
| `extensions/devai-code-search/src/devai_code_search/` | `extensions/nexus-code-search/src/nexus_code_search/` | Nested Python package. |
| `extensions/devai-web-fetch/` | `extensions/nexus-web-fetch/` | Phase 4 sub-task 4.1. |
| `extensions/devai-web-fetch/src/devai_web_fetch/` | `extensions/nexus-web-fetch/src/nexus_web_fetch/` | Nested Python package. |

Total: 7 directory renames (4 top-level, 3 nested packages).

---

## 2. File renames

Command run: `find . -type f -iname "*devai*" -not -path "./node_modules/*" -not -path "./.git/*"`

| Old path | New path | Notes |
|---|---|---|
| `scripts/devai_mcp_benchmark.py` | `scripts/nexus_mcp_benchmark.py` | Phase 4 sub-task 4.3; installer copy lines in both `installer.sh` and `installer.ps1` MUST also be updated since the installer copies scripts by explicit name. |
| `scripts/Install-DevAI-Permissions.ps1` | `scripts/Install-Nexus-Hub-Permissions.ps1` | Phase 4 sub-task 4.3; same installer-copy update applies. |
| `.cursor/rules/devai-hub.mdc` | `.cursor/rules/nexus-hub.mdc` | Phase 5 sub-task 5.4. |

Total: 3 file renames. Excluded: `scripts/__pycache__/devai_mcp_benchmark.cpython-312.pyc` (build artifact, regenerated on next run).

---

## 3. String-variant table

Apply each variant in the exact order listed (longer-before-shorter prevents the shorter variants from over-matching the longer ones).

| Order | Old variant | New variant | Notes |
|---|---|---|---|
| 1 | `DevAI-Hub` | `Nexus-Hub` | Display, prose, Markdown headings. |
| 2 | `DEVAI-HUB` | `NEXUS-HUB` | ASCII-banner wordmark, all-caps emphasis. |
| 3 | `DEVAI_HUB` | `NEXUS_HUB` | Environment-variable prefix, shell variables. |
| 4 | `DevAI Hub` | `Nexus Hub` | UI/marketing two-word form (with space). |
| 5 | `devai-hub` | `nexus-hub` | kebab id, plugin name, npm-style identifiers. |
| 6 | `devai_hub` | `nexus_hub` | snake id, Python identifiers, env-var middles. |
| 7 | `devai-skill-server` | `nexus-skill-server` | MCP server key. Phase 4. |
| 8 | `devai-code-search` | `nexus-code-search` | MCP server key. Phase 4. |
| 9 | `devai-web-fetch` | `nexus-web-fetch` | MCP server key. Phase 4. |
| 10 | `devai_skill_server` | `nexus_skill_server` | Python package id. |
| 11 | `devai_code_search` | `nexus_code_search` | Python package id. |
| 12 | `devai_web_fetch` | `nexus_web_fetch` | Python package id. |
| 13 | `devai_mcp_benchmark` | `nexus_mcp_benchmark` | Script filename and module id. |
| 14 | `Install-DevAI-Permissions` | `Install-Nexus-Hub-Permissions` | PowerShell script filename. |
| 15 | `using-devai-hub` | `using-nexus-hub` | Skill directory name and registry entries. |

**Standalone `devai` -- DO NOT blind-replace.** Audit every match manually after applying the variants above. The remaining post-sweep occurrences of `devai` (lowercase) flagged for manual review:

- `.gitignore` lines `.devai/` (devai-code-search local index dir) and `.devaiignore` (its ignore file) -- both must be renamed in Phase 5 (`.nexus/` and `.nexusignore`) and the indexer source updated to match.
- `.git/hooks/pre-commit.devai-backup-<timestamp>` reference in `catalog/commands/install-pre-commit-review-hook.md` -- backup filename pattern, becomes `pre-commit.nexus-backup-<timestamp>`.
- No `devai` substrings inside English words (e.g. "individual", "advisor") -- audited and clear.

---

## 4. Reference counts (informational)

Commands used:

```
grep -rln "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" \
  --exclude-dir=node_modules --exclude-dir=.git \
  --exclude-dir=__pycache__ --exclude-dir="*.egg-info" .

grep -rn  "DevAI-Hub\|DevAI Hub\|devai-hub\|devai_hub\|DEVAI_HUB\|DEVAI-HUB" \
  --exclude-dir=node_modules --exclude-dir=.git \
  --exclude-dir=__pycache__ --exclude-dir="*.egg-info" .
```

| Metric | Count |
|---|---|
| Files containing at least one DevAI variant | 174 |
| Total line-level references | 1520 |

Top-level directory distribution (by file count):

| Directory | Files |
|---|---|
| `catalog/` | 61 |
| `docs/` | 54 |
| `extensions/` | 15 |
| `scripts/` | 8 |
| `guides/` | 8 |
| `templates/` | 5 |
| `infrastructure/` | 4 |
| `data/` | 4 |
| `.claude-plugin/` | 2 |
| root single files (CLAUDE.md, AGENTS.md, README.md, CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, GEMINI.md, SECURITY.md, README_zh.md, llms.txt, .pr_agent.toml) | 11 |
| `.github/` | 1 |
| `.cursor/` | 1 |

The pre-rename reference total of approximately **174 files / 1520 references** is the workload Phase 5's catalog sweep and Phase 2's metadata edits must process. Phases 7-8 will re-run these grep commands and the post-rename count must be 0 outside `docs/archive/`, frozen `docs/v0.*` / `docs/v1.*` directories, and intentional "renamed from DevAI-Hub" callouts in `README.md` and `CHANGELOG.md`.

---

## 5. Cross-link targets

The sibling Nexus repo at `C:\Users\bdour\Documents\Projects\Development\Nexus-AI` carries two outbound links to this repo that will become stale after the GitHub repo is renamed:

- `Nexus-AI/README.md` line 37: `[bendourthe/DevAI-Hub](https://github.com/bendourthe/DevAI-Hub)`.
- `Nexus-AI/README.md` line 50: prose comparison against "DevAI-Hub" in the v1.0.0 docs context.

Action: out of scope for this plan. After this rename completes and GitHub's automatic redirect is in place, a follow-up commit on the `Nexus-AI` repo must update both lines to point at `bendourthe/Nexus-Hub`. Tracked as a downstream task; not blocking v2.0.0.

In the other direction, this repo's `README.md` will add a prominent cross-link to `https://github.com/bendourthe/Nexus-AI` as part of Phase 6 sub-task 6.2 (the new "How Nexus-Hub fits with Nexus" block).

---

## 6. Asset transfer

Two image assets will be copied from the sibling Nexus repo into this repo's `assets/` directory in Phase 6 sub-task 6.1:

| Source path | Destination path | Purpose |
|---|---|---|
| `C:\Users\bdour\Documents\Projects\Development\Nexus-AI\assets\nexus_primary.png` | `assets/nexus_primary.png` | README hero image. |
| `C:\Users\bdour\Documents\Projects\Development\Nexus-AI\assets\nexus_monochrome.png` | `assets/nexus_monochrome.png` | Dark-mode preview / alternate branding. |

Source files verified to exist at the listed paths during Phase 1 capture.

Licensing: the author of both repos is Benjamin Dourthe. A `LICENSE-ASSETS.md` note (or append to `LICENSE`) will document the internal reuse.

---

## 7. Authoritative paths affected outside the catalog

The rename touches several files outside the bulk `catalog/` sweep that require dedicated edits:

- `.claude-plugin/plugin.json` -- plugin canonical id, description, homepage, repository (Phase 2 sub-task 2.1).
- `.claude-plugin/marketplace.json` -- marketplace name, displayName, description, URLs (Phase 2 sub-task 2.1).
- `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`, `data/bundles.json` -- catalog registries (Phase 2 sub-task 2.2).
- `.pr_agent.toml`, `Makefile`, `.github/copilot-instructions.md` -- root-level configs (Phase 2 sub-task 2.3).
- `AGENTS.md`, `CLAUDE.md` -- top-level agent instructions (Phase 2 sub-task 2.4).
- `scripts/installer.sh`, `scripts/installer.ps1`, `install.sh`, `install.bat` -- installer entry points (Phase 3).
- `catalog/mcp-configs/mcp-servers.json` -- MCP registry (Phase 4 sub-task 4.2).
- `docs/policy/mcp-reverse-engineering-matrix.md` -- MCP reverse-engineering matrix (Phase 4 sub-task 4.2).
- `templates/ai-instructions/base-claude.md`, `base-codex.md`, `base-cursor.md`, `base-gemini.md`, `base-opencode.md` -- five AI-instruction templates updated in lockstep (Phase 5 sub-task 5.2).
- `.github/dependabot.yml`, `.github/workflows/ci.yml` -- CI references to extension dirs.
- `CHANGELOG.md` -- new v2.0.0 block (Phase 7 sub-task 7.5).
- `README.md` -- full rewrite around Nexus-Hub brand (Phase 6 sub-task 6.2).

---

## 8. Baseline drift notes (informational)

The pre-rename hook-test baseline (`docs/archive/v2/v2.0/baselines/hook-tests-pre.txt`) reports **360 passed, 9 skipped** rather than the **366 passed, 3 skipped** count quoted in `docs/archive/v1/v1.3/known-gaps.md`. The delta is 6 tests that moved from passing to skipped between v1.3.0 and v1.4.0; no new failures. Post-rename phases (Phase 5 sub-task 5.5, Phase 8 sub-task 8.1) MUST match the new pre-rename baseline of 360 passed / 9 skipped, not the v1.3.0 historical count. Extension counts (37 / 36+1s / 23) match the v1.3.0 baseline exactly.

The skill validator reports **207 skills** (the plan body refers to "203+", consistent with the catalog having grown between v1.3.0 and v1.4.0). The 4 framework-specialist orphan-bundle warnings (WN-001) are present in the baseline as expected and are addressed in Phase 8 sub-task 8.3.

---

## 9. Out-of-scope variants

- `docs/archive/**` -- historical artifacts; frozen and intentionally untouched.
- `docs/v0.*/**`, `docs/v1.*/**` -- frozen version snapshots; the `old-version-docs-guard` hook enforces immutability.
- `CHANGELOG.md` historical blocks (`## [1.4.0]` and earlier) -- frozen historical record; only the new `## [2.0.0]` block is added.
- `.git/`, `node_modules/`, `__pycache__/`, `*.egg-info/` -- non-source paths.

These directories are explicitly excluded from the residual-rename grep at Phase 7 sub-task 7.6 and Phase 8 sub-task 8.1.
