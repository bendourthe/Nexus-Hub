# Nexus-Hub v2.1.0 -- Spec-Driven Development Adoption

**Release date**: 2026-05-20
**Type**: SemVer **minor** (additive; no breaking changes)
**Plan**: [`plans/adoption-spec-kit.md`](plans/adoption-spec-kit.md)
**CHANGELOG block**: [`CHANGELOG.md` -> `## [2.1.0]`](../../CHANGELOG.md)

## Highlights

v2.1.0 makes Spec-Driven Development (SDD) a first-class workflow in Nexus-Hub. The release adopts 11 capabilities surfaced by the v2.0.0 cross-project comparison (see [`docs/archives/v2/v2.0/comparison-spec-kit.md`](../v2.0.0/comparison-spec-kit.md)) -- from constitution-as-governance to a cross-artifact spec analyzer to a sequential 5-question clarification loop. All adoption items are classified `skill-native` under the MCP Registry Policy: no new outbound calls, no new credentials, no new third-party data processors, no new runtime dependencies.

The release ships:

- **3 new skills** under `catalog/skills/`
- **4 new slash commands** under `catalog/commands/`
- **3 new templates** under `catalog/templates/`
- **2 new repo-level helper scripts** under `scripts/` (cross-platform `.sh + .ps1` pair) with installer registration in both `installer.sh` and `installer.ps1`
- **Discipline updates to 5 existing skills** (`spec-driven-development`, `ambiguity-detector`, `idea-refine`, `implementation-plan`, and the `/generate-plan` command flow)
- **A rebaselined `data/skills.json` statistics block** that closes a pre-existing drift between `statistics.total_skills` and the actual array length

Every change is additive. Users upgrading from v2.0.0 rerun the installer to pick up the new artifacts; pre-existing behavior is preserved.

## Spec-Driven Development adoption -- the narrative

Nexus-Hub already had overlapping primitives for SDD: a `spec-driven-development` skill, an `idea-refine` skill, an `ambiguity-detector` skill, a `/generate-plan` command, and a `quality-gate-definitions` skill. What it lacked was the **gating discipline** that turns those primitives into a workflow you cannot accidentally skip:

- No project-level governance file declaring MUST / SHOULD principles every plan checks against.
- No standardized marker convention for surfacing uncertainty during spec authoring.
- No cross-artifact consistency check that catches drift between `spec.md`, `plan.md`, and `tasks.md`.
- No sequential clarification loop that forces one-question-at-a-time resolution with Recommended options.
- No strict task-line format that supports per-story labeling and parallel markers.

v2.1.0 closes each of these gaps. The result is that the existing skills are still individually invocable for one-off use, but when they are composed into a feature workflow they now have a spine that holds them together.

## What's new

### New slash commands

| Command | Adoption candidate | What it does |
|---|---|---|
| `/constitution` | G1 | Author / amend the project constitution at `docs/<version>/constitution.md`. Emits a Sync Impact Report HTML-comment block at the top of every amendment. SemVer-aware (MAJOR / MINOR / PATCH bumps per principle change semantics). |
| `/analyze-spec` | G4 | Read-only cross-artifact analyzer. Runs six detection passes (Duplication / Ambiguity / Underspecification / Constitution Alignment / Coverage Gaps / Inconsistency) over `spec.md + plan.md + tasks.md`. Emits a severity-tagged Findings table, a Coverage Summary, and a Metrics block. Deterministic finding IDs across reruns. |
| `/clarify-spec` | G3 | Sequential 5-question ambiguity-reduction loop using a 10-category taxonomy. Each question presents a Recommended option at the top, then a Markdown table of all options. Accepted answers are integrated atomically back into the spec under a `## Clarifications` section. |
| `/tasks-to-issues` | G10 | Convert strict-format `- [ ] T### [P?] [US?] file_path` task lines into linked GitHub issues via the local `gh` CLI. Supports `--dry-run` to preview the `gh issue create` invocations, and `--execute` for sequential filing with idempotency markers (`[gh#<num>]`) appended to the source. |

### New skills

| Skill | Category | Adoption candidate |
|---|---|---|
| [`project-constitution`](../../catalog/skills/workflow/project-constitution/SKILL.md) | workflow | G1 |
| [`cross-artifact-analyzer`](../../catalog/skills/code-review/cross-artifact-analyzer/SKILL.md) | code-review | G4 |
| [`tasks-to-issues`](../../catalog/skills/workflow/tasks-to-issues/SKILL.md) | workflow | G10 |

### New templates

| Template | Adoption candidate | Used by |
|---|---|---|
| [`catalog/templates/constitution-template.md`](../../catalog/templates/constitution-template.md) | G1 | `/constitution` |
| [`catalog/templates/spec-template.md`](../../catalog/templates/spec-template.md) | G7 | `/generate-plan --specs-layout`, `spec-driven-development` skill |
| [`catalog/templates/spec-quality-checklist.md`](../../catalog/templates/spec-quality-checklist.md) | G9 | `spec-driven-development` skill |

### New repo-level helper scripts

- **`scripts/new-feature.sh + scripts/new-feature.ps1`** -- resolve the `--specs-layout` prefix (sequential or timestamp from `.specify/init-options.json`), create the `specs/<NNN>-<slug>/` directory, persist `.specify/feature.json`. Registered in BOTH `scripts/installer.sh` and `scripts/installer.ps1`. Both pass parser checks.

### Updated existing skills (5)

| Skill | What changed |
|---|---|
| [`spec-driven-development`](../../catalog/skills/developer-experience/spec-driven-development/SKILL.md) | New subsections: "Marking uncertainty with `[NEEDS CLARIFICATION]`" (3-marker hard cap, priority `scope > security/privacy > UX > technical`), "Spec template", "User stories with priorities" (P1 / P2 / P3 with Independent Test criteria + MVP rule), "Auto-validating the spec". New Common Rationalizations rebuttals for "I'll just use bullet points" and "this feature only has one user story". |
| [`ambiguity-detector`](../../catalog/skills/developer-experience/ambiguity-detector/SKILL.md) | Output aligned with the standardized `[NEEDS CLARIFICATION: <specific question>]` marker convention; emits the marker instead of free-form prose. |
| [`idea-refine`](../../catalog/skills/developer-experience/idea-refine/SKILL.md) | 3-marker cap subsection added; new "Boundary with `/clarify-spec`" subsection distinguishing vague-idea-to-problem-statement (this skill) from already-written-spec ambiguity reduction (`/clarify-spec`). |
| [`implementation-plan`](../../catalog/skills/workflow/implementation-plan/SKILL.md) | Constitution Check + Complexity Tracking template sections + `[[project-constitution]]` cross-link. |
| `/generate-plan` command flow | Step 0d gains `--specs-layout`; Step 3 enforces strict task-line format + phase organization; Step 4 emits Constitution Check + Complexity Tracking; Step 5 adds Format Validation. |

## Adoption candidate map (G1 -- G11)

| ID | Title | Shipped artifact(s) | Phase |
|---|---|---|---|
| **G1** | Constitution-as-governance | `/constitution` command + `project-constitution` skill + `constitution-template.md` | Phase 1 |
| **G2** | `[NEEDS CLARIFICATION]` marker discipline | Body updates in `spec-driven-development`, `ambiguity-detector`, `idea-refine` | Phase 1 |
| **G3** | Sequential 5-question clarification loop | `/clarify-spec` command | Phase 5 |
| **G4** | Cross-artifact spec analyzer | `/analyze-spec` command + `cross-artifact-analyzer` skill | Phase 3 |
| **G5** | Opt-in `specs/<NNN>-<slug>/` layout | `/generate-plan --specs-layout` flag + `scripts/new-feature.{sh,ps1}` | Phase 7 |
| **G6** | Strict task-line format `[P]/[US#]` | `/generate-plan` Step 3 + Step 5 updates | Phase 6 |
| **G7** | Spec template with user-story priorities + FR/SC IDs | `catalog/templates/spec-template.md` + `spec-driven-development` body | Phase 4 |
| **G8** | (Folded into G7 -- not a separate artifact) | -- | -- |
| **G9** | Spec quality checklist | `catalog/templates/spec-quality-checklist.md` + skill subsection | Phase 5 |
| **G10** | Tasks to GitHub issues | `/tasks-to-issues` command + skill + helper scripts + auth runbook | Phase 7 |
| **G11** | Constitution Check + Complexity Tracking in plans | `/generate-plan` Step 4 + `implementation-plan` skill | Phase 2 |

G12 (Integration Registry pattern re-full refactor) is scheduled for v2.2.0 as a separate Python refactor of the installer template logic.

## What's out of scope here (tracked separately)

- **G12 -- Integration Registry refactor** (Phase 10 of the plan). Replaces the lock-step per-platform `base-*.md` template editing with a Python class hierarchy. Targets v2.2.0; ADR-001 will land first.
- ~~**P3 polish items** (Phase 9 of the plan)~~: shipped against the v2.1.0 baseline rather than deferred. See Phase 9 entry in `docs/DEVLOG.md`. Items landed: the `docs/archive/v2/v2.1/spec-driven-methodology.md` essay (2679 words), the `.devcontainer/` first-touch setup with `devcontainer.json` and `post-create.sh`, the `catalog/style-guides/markdownlint-cli2.jsonc` config (auto-distributed alongside `markdown.md`), and the `tests/installer/test_registrar_path_traversal.py` defensive test (19 assertions; OS-agnostic).
- **Cross-OS installer matrix carry-overs from v1.1.5** (DF-003 / DF-005 / DF-006 in `docs/archive/v1/v1.1/known-gaps.md`). Orthogonal to spec-kit adoption; remain tracked for a future CI-matrix plan.

## Migration

No migration steps required. v2.1.0 is fully additive. Users upgrading from v2.0.0:

```bash
# macOS / Linux
bash scripts/installer.sh

# Windows
pwsh scripts/installer.ps1
```

The installer copies the new commands, skills, templates, and helper scripts under `~/.nexus-hub/`. Existing skill behavior, command behavior, and installed catalog content are unchanged unless you opt into one of the new flags (`--specs-layout`).

## Verification (Phase 8.1 results)

| Check | Result |
|---|---|
| `python scripts/validate_skills.py --bundles-only` | 0 errors, 0 warnings across 210 skill bundles |
| `extensions/nexus-skill-server` pytest | 37 passed |
| `extensions/nexus-code-search` pytest | 36 passed + 1 skipped |
| `extensions/nexus-web-fetch` pytest | 23 passed |
| `catalog/hooks/tests/` pytest | 370 passed + 3 skipped |
| `data/SKILL_INDEX.md` row count | 208 (= v2.0.0 baseline 205 + 3) |
| `data/skills.json` array length | 206 (= v2.0.0 baseline 203 + 3) |
| `data/marketplace.json` category sum | 203 (= v2.0.0 baseline 200 + 3) |
| `data/skills.json` statistics drift (WN-1) | Resolved (rebaselined to 206) |
| Bash + PowerShell parser checks on new scripts | All pass |
| Upstream-attribution leak scan | 1 found and fixed: `spec-kit-task` label renamed to `spec-driven-task` |

## Known carry-overs

See [`known-gaps.md`](known-gaps.md) for the full v2.1.0 gap log. With Phase 9 P3 polish now landed against the v2.1.0 baseline, no items are open at v2.1.0 ship.

## Coordinated follow-up

- **Push the `v2.1.0` tag** to the remote. Cut locally at the close of Phase 8 sub-task 8.3; the push is deferred to explicit user action per the CLAUDE.md global rule that destructive / remote-mutating git operations require user confirmation.
- ~~**Phase 9 P3 polish**~~ shipped against the v2.1.0 baseline; no separate patch release needed. See the Phase 9 DEVLOG entry for the rationale.
- ~~**Phase 10 G12 re-full refactor**~~ pulled forward to v2.1.0 (additive integration registry; legacy installer copy paths retained for the original 4 platforms). Byte-identical parity migration of the original 4 platforms into the registry is deferred to v2.2.0 as DF-001 in known-gaps.

## Phase 10 addendum: Integration Registry + expanded platform support

The v2.1.0 final release pulls **Phase 10 (G12 Integration Registry refactor)** forward from its original v2.2.0 target. The motivation is the user's request to expand supported platforms from the original 5 to 9+ in a single release, which the lock-step `base-*.md` editing convention could not absorb without 50+ correlated file edits. The ADR-001 architecture (`docs/archive/v2/v2.1/adr/adr-001-integration-registry.md`) introduces a Python class hierarchy under `scripts/lib/integrations/` -- `IntegrationBase` plus four mixin specializations (`MarkdownIntegration`, `TomlIntegration`, `YamlIntegration`, `SkillsIntegration`) -- with one subclass per supported platform.

**Platforms now supported by the installer (v2.1.0 ship state)**:

| Platform | Install path (workspace) | Install path (global) | Path |
|---|---|---|---|
| Claude Code (Anthropic) | `.claude/` | `~/.claude/` | legacy installer + registry subclass |
| Codex (OpenAI) | `.codex/` | `~/.codex/` | legacy installer + registry subclass |
| Cursor | `.cursor/rules/*.mdc` + `AGENTS.md` | n/a | registry subclass |
| Gemini (Google) | `.gemini/` | `~/.gemini/` | legacy installer + registry subclass |
| **Gemini CLI** (Google) | `.gemini/commands/*.toml` | `~/.gemini/commands/*.toml` | **registry subclass (new in v2.1.0)** |
| OpenCode | `.opencode/` | `~/.opencode/` | registry subclass |
| **Windsurf** (Codeium) | `.windsurf/{rules,workflows,skills}` | n/a | **registry subclass (new in v2.1.0)** |
| Antigravity 1.0 (Google) | `.gemini/antigravity/` | `~/.gemini/antigravity/` | legacy installer + registry subclass |
| **Antigravity 2.0** (Google) | `.agent/` | `~/.agent/` | **registry subclass (new in v2.1.0)** |
| GitHub Copilot (Microsoft) | `.github/copilot-instructions.md` | n/a | legacy installer + registry subclass |
| **Nexus-AI** (Local Desktop Studio) | `.nexus-ai/` | `~/.nexus-ai/` | **registry subclass (new in v2.1.0)** |

**Cross-platform seamlessness**: a user who installs Nexus-Hub via `bash scripts/installer.sh` or `pwsh scripts/installer.ps1` now lands the catalog into 11 distinct AI-coding-platform locations. Switching from Claude Code to Antigravity 2.0 (or to Nexus-AI, or to Gemini CLI, etc.) means the same skills, commands, agents, and rules are already on disk in the platform's expected directory layout. No re-install or re-configuration is needed when switching assistants.

The runner CLI is also usable standalone:

```bash
python scripts/lib/integrations/runner.py list
python scripts/lib/integrations/runner.py install --scope workspace --target /path/to/project --integrations windsurf,antigravity2,gemini-cli,nexus-ai
python scripts/lib/integrations/runner.py teardown --target /path/to/project
```

The runner is also installed at `~/.nexus-hub/scripts/lib/integrations/runner.py` after running the installer, so users can re-target additional projects without re-cloning the repo.

## Cross-references

- **Plan**: [`plans/adoption-spec-kit.md`](plans/adoption-spec-kit.md) -- the full 10-phase plan with per-phase Stability Gates and Exit Checklists.
- **CHANGELOG**: [`../../CHANGELOG.md`](../../CHANGELOG.md) -- the `## [2.1.0]` block.
- **Source comparison**: [`../v2.0.0/comparison-spec-kit.md`](../v2.0.0/comparison-spec-kit.md) -- the per-candidate scoring, the MCP Registry Policy classification, and the sequencing rationale.
- **Known gaps**: [`known-gaps.md`](known-gaps.md) -- open items and resolved entries.
