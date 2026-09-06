# Platform Read-Contracts (living)

This is the durable, sourced source of truth for where every supported platform READS each surface (instruction file, slash commands, skills, agents, rules, hooks) and where the Nexus-Hub installer WRITES it. It supersedes the point-in-time snapshot at `docs/v3/v3.11/platform-read-contracts.md` (which resolved the v3.11.0 Phase 7 audit but left the Codex and Antigravity contracts flagged as unverified).

**Last verified**: 2026-09-04, stamped for v4.5.0 (re-stamp for a release that changes no adapter, installer, or discovery path; the live re-fetch is the same-day v4.4.5 pass below, and `verify_platform_contracts.py` reports OK for all 13 platforms at the release tree). Previous: 2026-09-04, stamped for v4.4.5 (re-verification pass, no correction required: 12 of 13 platforms re-fetched from live first-party vendor docs and classified MATCH with zero discovery-path drift; Nexus-AI remains UNVERIFIED because its source is private; the same visit found a Claude Code LEVER drift recorded in the lever contract). Previous: 2026-09-01, stamped for v4.4.0 (re-verification pass, no correction required: 11 of 13 platforms re-fetched from live first-party vendor docs and classified MATCH with zero drift; gemini carried forward with its `~/.gemini/` root independently corroborated; Nexus-AI remains UNVERIFIED because its source is private. Several platforms have added cross-agent `~/.agents/skills` alias roots alongside the declared native paths -- additional surfaces, not drift, so no adapter changed).

## Invocation-policy emission (v3.20.3)

This is not a discovery-path change. Command-skills synthesized at install time now carry `disable-model-invocation: true` so slash-command bodies are not model-auto-invoked where the platform honors the field. Dated re-check 2026-08-24:

| Platform | Lever | What Nexus-Hub emits |
|---|---|---|
| Claude Code | `disable-model-invocation` in SKILL.md | Field on generated command-skills. Vendor documents it ([code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills), re-fetched 2026-08-24). |
| Cursor | `disable-model-invocation` in SKILL.md (no `user-invocable`) | Field on generated command-skills. Vendor documents it ([cursor.com/docs/skills](https://cursor.com/docs/skills), re-fetched 2026-08-24). |
| Qwen Code | both fields in SKILL.md | Field on generated command-skills. Vendor documents it ([qwen-code-docs skills](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/), page last updated 2026-08-07, re-fetched 2026-08-24). |
| GitHub Copilot | both fields in SKILL.md | Unchanged from the 2026-08-18 survey. Opt-in `.github/skills/` wrappers copy SKILL.md verbatim; command-skills are not that surface unless `NEXUS_HUB_COPILOT_SKILLS` is on. |
| Codex / ChatGPT | `policy.allow_implicit_invocation` in `agents/openai.yaml` (inverted) | After command-skill write, `codex_invocation_policy` emits `allow_implicit_invocation: false`. Re-fetched 2026-08-24; mapping unchanged. |
| Antigravity 2.0, OpenCode, Kimi, Hermes, Nexus-AI | none documented | The SKILL.md field is still emitted and ignored. Honest gap; no invented mapping. |

The living per-skill lever survey remains [`skill-invocation-policy-levers.md`](skill-invocation-policy-levers.md). `meta.verified_for_version` is 4.1.2.

**v4.1.2 pass (targeted, superseded by the 2026-08-30 full correction below).** Construction-discipline catalog release; no discovery-path, adapter write-target, or `contract_checks` change. Re-fetch: Claude MATCH ([code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)), Cursor MATCH ([cursor.com/docs/skills](https://cursor.com/docs/skills), recursive `.cursor/skills` and `.agents/skills` at project and user scope, plus `disable-model-invocation`). Codex **DRIFT (low)** carried forward ([learn.chatgpt.com/docs/build-skills](https://learn.chatgpt.com/docs/build-skills)): documents the `.agents/skills` ladder including `$HOME/.agents/skills`; still omits `~/.codex/skills`. The later full correction removed that undocumented duplicate. Remaining public platforms were not re-fetched in the targeted pass. Nexus-AI remained UNVERIFIED.

**v3.21.0 pass (targeted).** Plan/implement lifecycle and living-docs release; no discovery-path, adapter write-target, or `contract_checks` change. Re-fetch: Claude MATCH ([code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)), Cursor MATCH ([cursor.com/docs/skills](https://cursor.com/docs/skills)). Codex **timeout this cycle**; low non-breaking DRIFT carried forward (ninth consecutive; documents the `.agents/skills` ladder including `$HOME/.agents/skills`; still omits `~/.codex/skills`). OpenCode MATCH, Gemini CLI MATCH, Antigravity, Gemini Code Assist, Kimi, and Qwen were not re-fetched this cycle and are carried forward from the 2026-08-24 MATCH, not assumed. Nexus-AI remains UNVERIFIED.

**v3.20.3 pass (targeted).** Skills-craft release; no discovery-path, adapter write-target, or `contract_checks` change. Same-day re-fetch: Claude MATCH ([code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)), Cursor MATCH ([cursor.com/docs/skills](https://cursor.com/docs/skills)), OpenCode MATCH ([opencode.ai/docs/skills/](https://opencode.ai/docs/skills/)), Gemini CLI MATCH ([geminicli.com/docs/cli/using-agent-skills/](https://geminicli.com/docs/cli/using-agent-skills/)). Codex **DRIFT (low), eighth consecutive cycle**: documents the `.agents/skills` ladder including `$HOME/.agents/skills`; still omits `~/.codex/skills` ([learn.chatgpt.com/docs/build-skills](https://learn.chatgpt.com/docs/build-skills), re-fetched 2026-08-24). Nexus-AI remains UNVERIFIED. Antigravity, Gemini Code Assist, Kimi, and Qwen were not re-fetched this cycle and are carried forward from the prior MATCH, not assumed.

**v3.17.4 pass (full).** All ten contract platforms and all sixteen defaults-lever platforms were re-fetched from live first-party documentation. Every public discovery page returned HTTP 200 and retained the path marker used by Nexus-Hub. The read-path contract remains functional: eight MATCH, one non-breaking Codex DRIFT, and one UNVERIFIED Nexus-AI surface. Cursor and Claude retain their distinct hook response protocols, and Org Knowledge writes only the existing instruction and rules destinations, so no adapter path changes in this release.

| Platform | Verdict | Evidence |
|---|---|---|
| Claude Code | **MATCH** | Personal `~/.claude/skills/<skill-name>/SKILL.md` and project `.claude/skills/<skill-name>/SKILL.md` confirmed, with enterprise > personal > project precedence on name collisions. The commands surface remains supported. [Source](https://code.claude.com/docs/en/skills) |
| Codex / ChatGPT | **DRIFT (low), seventh consecutive cycle** | Discovery still documents the `.agents/skills` ladder and still omits `~/.codex/skills`. Nexus-Hub writes both paths, so delivery remains functional through the confirmed user-level `.agents/skills` path. The redundant write is retained until first-party removal evidence replaces repeated omission. [Source](https://learn.chatgpt.com/docs/build-skills) |
| Antigravity 2.0 + CLI | **MATCH** | Global `~/.gemini/config/skills/<name>/SKILL.md` and project `.agents/skills/<name>/SKILL.md` remain documented. [Source](https://codelabs.developers.google.com/getting-started-with-antigravity-skills) |
| Cursor | **MATCH** | Recursive discovery still covers `.cursor/skills` and `.agents/skills` at project and user scope. [Source](https://cursor.com/docs/skills) |
| Gemini Code Assist | **MATCH** | The IDE still consumes `~/.gemini/GEMINI.md`; its shared skills surface remains aligned with the Gemini family contract. [Source](https://docs.cloud.google.com/gemini/docs/codeassist/use-agentic-chat-pair-programmer) |
| Gemini CLI | **MATCH** | User `~/.gemini/skills` and workspace `.gemini/skills` remain documented, with `.agents/skills` also supported. [Source](https://geminicli.com/docs/cli/using-agent-skills/) |
| Kimi Code CLI | **MATCH** | User `~/.kimi-code/skills` and project `.kimi-code/skills` remain documented. [Source](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html) |
| Nexus-AI | **UNVERIFIED** | The private repository still exposes no publicly auditable read-path contract. The existing local contract remains guarded without being promoted to MATCH. |
| OpenCode | **MATCH** | Global `~/.config/opencode/skills` and project `.opencode/skills` remain documented alongside compatible `.agents/skills` and `.claude/skills` paths. [Source](https://opencode.ai/docs/skills/) |
| Qwen Code | **MATCH** | User `~/.qwen/skills` and project `.qwen/skills` remain documented. [Source](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) |

**Codex finding, handling.** Unchanged and still non-breaking. The full pass evaluated removal and retained `~/.codex/skills`: repeated omission is weaker evidence than an explicit deprecation, while the confirmed `~/.agents/skills` write guarantees delivery.

**Last verified**: 2026-08-14 for v3.16.8.

**v3.16.8 pass (targeted, sixth consecutive).** Two platforms were re-fetched from live first-party documentation; the remaining eight carry forward from the 2026-08-08 full pass and are explicitly **not re-verified this cycle** rather than assumed to match. v3.16.8 changes no platform discovery surface, verified by diff rather than asserted: filtering `git diff --name-only origin/main..HEAD` for installer / integrations / `base-*.md` / `platform-read-contracts` / `platform-defaults` returns zero matches. The changed set is one repo-level script (`scripts/validate_unicode_safety.py`, which carries no read path), two `catalog/commands/` files, one `catalog/skills/` SKILL.md, `tests/`, and `docs/`, plus the version constants in both installers.

| Platform | Verdict | Evidence |
|---|---|---|
| Claude Code | **MATCH** | Personal `~/.claude/skills/<skill-name>/SKILL.md` and project `.claude/skills/<skill-name>/SKILL.md` confirmed verbatim, with enterprise > personal > project precedence on collisions, `.claude/commands/` files still working, and a skill taking precedence over a same-named command. Two ADDITIONS observed, neither affecting what Nexus-Hub writes: skills now also load from nested `.claude/skills/` directories below the working directory (a monorepo affordance, additive to discovery), and the folder name `synced` is now RESERVED in all three locations for claude.ai-synced skills. Nexus-Hub ships no skill named `synced` (checked against all 271), so the reservation is a non-issue. [Source](https://code.claude.com/docs/en/skills) |
| Codex / ChatGPT | **DRIFT (low), seventh consecutive cycle** | The documented ladder is `$CWD/.agents/skills`, `$CWD/../.agents/skills`, `$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, `/etc/codex/skills`, plus bundled skills; `~/.codex/skills` is still absent. Folder-per-skill `SKILL.md` with optional `scripts/` / `references/` / `assets/` confirmed, and CLI invocation is `$skill`. [Source](https://learn.chatgpt.com/docs/build-skills) |

**Codex finding, handling.** Unchanged and still non-breaking: `$HOME/.agents/skills` is explicitly confirmed and Nexus-Hub writes it, so delivery reaches Codex regardless. This is the SEVENTH stable cycle, one past the point the v3.16.7 pass called conclusive and declared the deliberate-removal proposal **owed** at v3.17.0. It should not be deferred an eighth time.

**Redirect check (the rebrand tripwire).** Both fetched source URLs resolved directly, with no cross-host redirect, so no vendor reorganization or rename signal this cycle.

**v3.16.7 pass (targeted, fifth consecutive).** Two platforms were re-fetched from live first-party documentation; the remaining eight carry forward from the 2026-08-08 full pass. v3.16.7 changes no platform discovery surface, and that was verified by diff rather than asserted: filtering `git diff --name-only develop..HEAD` for installer / integrations / `base-*.md` / `platform-read-contracts` returns zero matches. The changed set is one skill bundle (plus its new `references/content-intent.md`), its command file, `scripts/generate_manifest.py` (release tooling, no read path), `tests/`, and `docs/`, plus the version constants in both installers.

| Platform | Verdict | Evidence |
|---|---|---|
| Claude Code | **MATCH** | Personal `~/.claude/skills/<skill-name>/SKILL.md` and project `.claude/skills/<skill-name>/SKILL.md` confirmed, with enterprise > personal > project precedence on name collisions. Custom commands remain merged into skills, existing `.claude/commands/` files keep working, and a skill takes precedence over a same-named command - so the commands write stays valid. [Source](https://code.claude.com/docs/en/skills) |
| Codex / ChatGPT | **DRIFT (low), sixth consecutive cycle** | Discovery documents the ladder `$CWD/.agents/skills`, `$CWD/../.agents/skills`, `$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, `/etc/codex/skills`, plus bundled system skills; `~/.codex/skills` is still absent. The page also states that `~/.codex/config.toml` is separate from discovery and governs only enable/disable, which does not change the read-path picture. [Source](https://learn.chatgpt.com/docs/build-skills) |

**Codex finding, handling.** Unchanged and still non-breaking; `$HOME/.agents/skills` is explicitly confirmed and Nexus-Hub writes it, so delivery reaches Codex regardless. The retained `~/.codex/skills` write stays on the recorded reasoning (writing a directory a platform ignores is harmless; removing one it does read would silently drop coverage). Six stable cycles is conclusive rather than suggestive, so the deliberate-removal proposal is now **owed** at v3.17.0 and should not be deferred a seventh time.

**A full pass is owed at v3.17.0.** Five consecutive targeted passes have now deferred it.

---

**Prior entry, retained for the record** -- Last verified 2026-08-11 for v3.16.5.

**v3.16.5 pass (targeted).** Two platforms were re-fetched from live first-party documentation; the remaining eight carry forward from the 2026-08-08 full pass. v3.16.5 changes no platform discovery surface: the changed set is confined to one skill bundle, its command file, the two `data/` registries, `tests/`, one workflow file, and `docs/` (no read path, no adapter, no installer, no `base-*.md`).

| Platform | Verdict | Evidence |
|---|---|---|
| Claude Code | **MATCH** | Personal `~/.claude/skills/<skill-name>/SKILL.md` and project `.claude/skills/<skill-name>/SKILL.md` confirmed verbatim. The page still states custom commands are merged into skills and that existing `.claude/commands/` files keep working, so the commands write remains supported. [Source](https://code.claude.com/docs/en/skills) |
| Codex / ChatGPT | **DRIFT (low), fourth consecutive cycle** | Discovery lists `$CWD/.agents/skills`, `$CWD/../.agents/skills`, `$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, and `/etc/codex/skills`. `~/.codex/skills` is still absent. [Source](https://learn.chatgpt.com/docs/build-skills.md) |

**Codex finding, handling.** Unchanged and still non-breaking: Nexus-Hub writes both `~/.codex/skills` and `~/.agents/skills`, and the latter is explicitly documented, so delivery reaches Codex. The retained write stays on the recorded reasoning (writing an ignored directory is harmless; removing a read one would silently drop coverage). Four cycles of a stable omission is now strong enough evidence that a deliberate removal should be **proposed** at the next minor rather than deferred again. It is not done here because v3.16.5 touches no installer, and changing a write path inside a release that otherwise touches no delivery code would be the wrong place for it.

**One bookkeeping finding, recorded rather than quietly fixed.** The stamp this pass replaced read v3.16.3, so **v3.16.4 shipped without re-stamping the contract** and its freshness gate went unanswered. Nothing broke (v3.16.4 touched no read path either), but the gate exists to be answered once per release, and skipping it silently is precisely the failure mode it guards against. Separately, this `.md` had fallen a further step behind the JSON: the v3.16.3 pass updated only the machine-readable file. The two are back in step here.

**A full pass is owed.** Three consecutive targeted passes have deferred it; the next minor release should re-fetch all ten platforms.

---

**Prior entry, retained for the record** -- Last verified 2026-08-09 for v3.16.2.

**v3.16.2 pass.** Official vendor documentation was fetched for five platforms; the remaining entries carry forward from the same-day v3.16.1 pass, and this release changed no integration adapter, no contract file, and no instruction template (34 files, all docs, tests, and the new installer subcommand).

| Platform | Verdict | Evidence |
|---|---|---|
| Claude Code | **MATCH** | `~/.claude/skills/<name>/SKILL.md` folder-per-skill confirmed; `.claude/commands/*.md` still honored, with custom commands now formally merged into skills so both produce `/name`. [Source](https://code.claude.com/docs/en/skills) |
| Codex / ChatGPT | **DRIFT (low)** | `~/.codex/AGENTS.md` + project `AGENTS.md` confirmed. But user-scope skill discovery is documented as `$HOME/.agents/skills` **only**; `~/.codex/skills` is no longer listed as a discovery path. Repo scope scans `.agents/skills` from cwd up to the repo root. [Source](https://learn.chatgpt.com/docs/build-skills.md) |
| Cursor | **MATCH** | `~/.cursor/skills/` and `~/.agents/skills/` both documented user-level, project `.cursor/skills/` and `.agents/skills/`, walked **recursively**. [Source](https://cursor.com/docs/skills) |
| Antigravity 2.0 | **MATCH** | `~/.gemini/config/skills/` global (shared across Antigravity, IDE, and CLI) and `<project>/.agents/skills/` project, folder-per-skill `SKILL.md`. [Source](https://codelabs.developers.google.com/getting-started-with-antigravity-skills) |
| GitHub Copilot | **DRIFT (new surface)** | Copilot now documents **personal** skills at `~/.copilot/skills` or `~/.agents/skills`, and project skills at `.github/skills`, `.claude/skills`, **or** `.agents/skills`. [Source](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) |

**Codex finding, handling.** Nexus-Hub writes BOTH `~/.codex/skills` and `~/.agents/skills`, so coverage is unaffected: the path Codex actually reads is populated. The `~/.codex/skills` write is now **redundant rather than load-bearing**. It is retained deliberately, following the precedent set for Cursor's commands directory in v3.15.10: writing a directory the platform ignores is harmless, whereas removing one that is still read would silently drop coverage. Flagged for removal once a second cycle confirms it is genuinely unread.

**Copilot finding, handling.** This is an opportunity rather than a breakage: Copilot gained a documented user-global skills read-path that Nexus-Hub does not populate (it currently treats Copilot as behavioral-guardrails-only, plus the opt-in `.github/skills/` project wrapper behind `NEXUS_HUB_COPILOT_SKILLS`). Note also that Copilot reads project `.agents/skills`, which `nexus-hub init` already seeds for Antigravity, so some coverage may already exist incidentally. Promoting Copilot to a full skills-bearing integration is a **feature for a future cycle**, not a release-blocking fix, and is recorded as a known gap rather than implemented inside a release.

---

**Prior entry, retained for the record** -- Last verified 2026-08-09 for v3.16.1.

For v3.16.1 specifically: a **targeted** pass, and it is labeled as such on purpose. The v3.16.0 full pass below ran one day earlier and its per-platform evidence is **carried forward unchanged**. Two platforms were re-fetched from live first-party documentation this cycle: **Codex**, the one platform that drifted last cycle, whose current skills page still lists the five `.agents/skills` paths plus `/etc/codex/skills` and still does **not** list `~/.codex/skills` -- the v3.16.0 finding reproduces exactly, so the retained write stays on the reasoning already recorded; and **Claude**, the highest-traffic platform, which still reads `~/.claude/skills` and `.claude/skills` (plus `.claude/commands`, now documented as merged into skills). The other **eight were not re-fetched**. v3.16.1 changed no integration adapter, no installer read path, and no platform surface, and a full re-fetch one day after a complete pass buys evidence one day fresher at real cost. This paragraph exists so nobody mistakes a carry-forward for a fresh check. **The next MINOR release should run a full pass.**

**Prior stamp**: 2026-08-08 for v3.16.0 (full pass, ten platforms). For v3.16.0 specifically: a **full** pass -- all ten platforms were re-checked against live first-party documentation this cycle, none carried forward. The release changes no discovery surface (it touches the two installers for an optional-dependency check and three `scripts/lib/integrations/` files for install-time defaults seeding; no diff line touches a read path, subdir name, or global/workspace dir). **Eight MATCH**: Claude (`~/.claude/skills/<name>/SKILL.md`), Cursor (`~/.cursor/skills` plus `~/.agents/skills`, recursive), OpenCode (`~/.config/opencode/skills/<name>/SKILL.md`), Kimi (`~/.kimi-code/skills`, `/skill:<name>`), Qwen (`~/.qwen/skills`), Gemini CLI (`~/.gemini/skills`, with `~/.agents/skills` taking precedence within a tier), Gemini (same path, same source), and Antigravity 2.0 (global `~/.gemini/config/skills/<folder>/`, project `.agents/skills` with `.agent/skills` retained for backward support).

**One DRIFT, non-breaking -- Codex.** The current first-party skills page lists `$CWD/.agents/skills`, `$CWD/../.agents/skills`, `$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, and `/etc/codex/skills`, and does **not** list `~/.codex/skills`. Nexus-Hub writes BOTH `~/.codex/skills` and `~/.agents/skills`; the latter is explicitly confirmed, so delivery still reaches Codex and nothing is broken. The `~/.codex/skills` write is **retained unchanged** on the same reasoning already recorded above for Cursor's `~/.cursor/commands`: writing a directory a platform ignores is harmless, while removing one it does read would silently drop coverage. Flagged for deliberate removal once a first-party page states the path is gone rather than merely omitting it. Note that a web search for this key returned the opposite claim (`$CODEX_HOME/skills`), which is exactly why the finding rests on the fetched vendor page instead.

**One UNVERIFIED -- Nexus-AI.** The project's repository is private, so no publicly-citable document exists, and an authenticated code search for its catalog read path returned no hits. Recorded as unverified this cycle rather than assumed correct.

**Prior stamp**: 2026-08-08 for v3.15.14. The machine-readable half of this contract (`platform-read-contracts.json`, `meta.verified_for_version_note`) carries the full per-release scope statement and is what the three guards actually read; this line is its human summary. **Note on drift**: this heading had said "2026-08-04 for v3.15.9" while the JSON had been re-stamped through v3.15.10, v3.15.11, v3.15.12, and v3.15.13, so the human half was four releases behind the machine half. Corrected here. Keep them in step: a reader who trusts this line and not the JSON was, until now, reading a stale claim.

For v3.15.14 specifically: the release changes no platform discovery surface (verified mechanically by `git diff --name-only v3.15.13..HEAD`, which touches no installer path, no `scripts/lib/integrations/` file, no `base-*.md`, and no contract doc; the only installer edit is the version constant). Two platforms were re-checked against live first-party documentation rather than carried forward. **Cursor** (`cursor.com/docs/hooks`): `~/.cursor/hooks.json` and `<project-root>/.cursor/hooks.json` confirmed, the `{"version": 1, "hooks": {...}}` schema confirmed, and both events Nexus-Hub registers (`beforeShellExecution`, `stop`) still documented. **Claude** (`code.claude.com/docs/en/skills`): the read-path table still gives `~/.claude/skills/<skill-name>/SKILL.md` and `.claude/skills/<skill-name>/SKILL.md`, flat, one level per skill. New finding worth recording: Claude's docs now state custom commands have been **merged into** skills, with `.claude/commands/<name>.md` and `.claude/skills/<name>/SKILL.md` both creating `/<name>` and existing command files continuing to work (the skill wins a name collision). Nexus-Hub writes both surfaces, so this confirms the `commands/` write remains valid; re-examine only if a future doc announces removal rather than merger. The other eight platforms carry forward from the v3.15.12 and v3.15.13 checks.

**Prior entry, retained for the record** -- Last verified 2026-08-04 for v3.15.9. This release changed no platform read path; the only delivery-code change was source-side, in the shared `flatten_skills` adapter, which now skips a `catalog/skills/<category>/<name>/` directory carrying no `SKILL.md` instead of publishing it. Two platforms were re-checked against live documentation because that change affects every skills-bearing platform. **Hermes**: discovery lists every direct subdirectory of the tap path and probes each for `SKILL.md`, confirming the recorded contract and independently validating the fix (it also ignores directories beginning with `.` or `_`, which the current delivery already satisfies). **Cursor**: the project path `.cursor/skills/<name>/SKILL.md` is confirmed, and multiple current sources state Cursor exposes no personal/global skills directory, which corroborates and extends known gap **DF-1** (previously scoped to the unverified global `~/.cursor/commands/`) to the global `~/.cursor/skills/` path. Those are secondary sources, not an official Cursor doc page, so DF-1 stays OPEN and the globally-written Cursor surfaces are retained unchanged pending first-party confirmation in a v3.15.10 follow-on. All other platforms carry forward from the 2026-08-02 / 2026-08-03 audits below and were not re-checked this cycle.

**Prior stamp**: 2026-08-02 for v3.15.7.

## Correction (2026-08-04): the v3.15.9 Cursor global-skills claim was wrong

The v3.15.9 stamp above records that "multiple current sources state Cursor exposes no personal/global skills directory" and extended known gap DF-1 to `~/.cursor/skills/` on that basis. **That is disproven.** [cursor.com/docs/skills](https://cursor.com/docs/skills) documents four skills read-paths, two of them user-level: `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/` (global), and `~/.cursor/skills/` (global), plus backward-compatible `.claude/skills/` and `.codex/skills/`. Discovery walks the root **recursively**.

So Nexus-Hub's global `~/.cursor/skills` write is correct and load-bearing, and the DF-1 extension is **withdrawn**. The v3.15.9 text is left in place as the dated record of what was believed at the time, which is what a verification log is for. The lesson is the one the repo already encodes elsewhere: secondary sources are a reason to go read the first-party page, not a finding.

The **commands** half of DF-1 resolves differently. Cursor's docs no longer document a commands directory at all; Cursor 2.4 ships a `/migrate-to-skills` skill that converts both user-level and workspace-level commands into skills with `disable-model-invocation: true`; and a community bug report titled "Commands are not detected in the global cursor directory" reports the global path simply does not work. Nexus-Hub already delivers every command as a command-skill through the verified skills path, so the global `~/.cursor/commands` write is **redundant rather than load-bearing**. It is retained unchanged for now (writing a directory Cursor ignores is harmless; removing one it does read would silently drop coverage) and flagged for deliberate removal in a later release.

## End-of-task notification coverage (v3.15.10 historical snapshot)

This table records what was known and shipped in v3.15.10; it is not the current surface contract. Copilot's "impossible" finding was superseded on 2026-08-30 by GitHub's documented native hook surface and the adapter delivery recorded below. Two triggers were considered: Trigger A = the agent is blocked on the human, and Trigger B = the agent finished responding.

| Platform | Trigger A (attention) | Trigger B (complete) | Shipped in v3.15.10 |
|---|---|---|---|
| Claude Code | `Notification` | `Stop` | **both** |
| Cursor | none exists | `stop` | **trigger B** |
| Qwen | none exists | `Stop` (verified) | deferred to a later release |
| Gemini CLI | none documented | `AfterAgent` (renamed) | deferred; enterprise-only opt-in |
| Codex | unverified (`PermissionRequest` is secondary-source only) | likely `Stop` | nothing, pending first-party proof |
| Kimi Code CLI | event set never enumerated | event set never enumerated | nothing, pending verification |
| GitHub Copilot | **impossible** | **impossible** | permanent non-coverage |
| OpenCode | **impossible** | **impossible** | permanent non-coverage |

Three findings worth carrying:

- **Trigger A is nearly unique to Claude Code.** Only its `Notification` event means "waiting on the human". Cursor's documented 21-event set has nothing equivalent: `beforeShellExecution` can return an `ask` status but fires before *every* shell command, so notifying there would recreate the storm v3.15.10 removed. Approximating a trigger is worse than omitting it.
- **Gemini CLI renamed everything.** `Stop` does not exist there; the completion event is `AfterAgent`. Writing `Stop` would have shipped a silently dead hook.
- **At v3.15.10, Copilot and OpenCode were recorded as notification non-coverage.** The Copilot half is now superseded: current GitHub documentation defines native hook files and Nexus-Hub writes them at both personal and repository scope. OpenCode's JS/TS plugin boundary remains distinct from the shell/Python hook catalog.

## How this doc is maintained

The machine-readable source of truth is the sibling `docs/policy/platform-read-contracts.json`; this `.md` is the human-readable table plus narrative and mirrors it. The JSON carries three sections: `contract_checks` (per-platform expected read-paths, consumed by `verify_platform_contracts.py`), `install_verify` (post-install surface checks, consumed by `runner.py`'s verify path), and `meta` (`last_verified` + `verified_for_version`, consumed by the release freshness gate). When a platform's row changes, edit the JSON entry first, then mirror it into the table below.

`/update release` runs a Nexus-Hub-specific "Platform read-contract re-verification" step before every version bump (see the `platform-contract-verification` skill). For each platform below it runs targeted web searches for that platform's CURRENT skill/command/rule/hook discovery format, diffs the findings against the JSON, and on any drift updates the JSON entry (mirrored here, plus its source URL and the Last-verified date), the corresponding integration adapter under `scripts/lib/integrations/`, and both installers. Three automated guards keep the release honest:

- `scripts/verify_platform_contracts.py` (run by `make validate`) asserts each integration's config and the installer copy targets match the `contract_checks` paths declared in the JSON (code-vs-contract).
- `nexus-hub verify` (`runner.py cmd_verify`) asserts, after an install, that each detected platform's read-paths (from the JSON's `install_verify`) are actually populated (install-vs-reality).
- `scripts/check_platform_contract_freshness.py` (run by `make validate` and CI) fails the build when the JSON's `meta.verified_for_version` does not match the version being released, so a release cannot ship on a contract that was not re-verified for it (freshness-vs-release).

The catalog itself is never reorganized per platform. Each integration is an adapter that materializes the canonical catalog into the shape below via the shared helpers in `scripts/lib/integrations/_catalog_adapters.py` (`flatten_skills`, `commands_to_skills`, `commands_to_slash`).

## Re-verification log

**v4.3.0 cut (re-stamp, no new pass).** The 2026-08-30 full correction pass below is the verification behind the v4.3.0 stamp. It ran while the canonical version still read 4.1.2, and nothing between that pass and this cut changed a discovery path, an adapter write-target, or a `contract_checks` entry, so the stamp moves without a new fetch rather than a new pass being claimed. `scripts/verify_platform_contracts.py` exits 0 on the cut tree.

### 2026-08-30 (v4.1.2 - full platform-contract correction)

All public platforms affected by the correction bundle were re-fetched from current first-party documentation. The enforced contract now distinguishes verified native discovery from compatibility writes and removes paths or gates that the current vendor documentation does not support:

- Antigravity MATCH for shared `~/.gemini/GEMINI.md`, IDE agents at `~/.gemini/config/agents`, workspace root `AGENTS.md`, workspace agents at `.agents/agents`, CLI skills at `~/.gemini/antigravity-cli/skills`, and CLI `agentMode`. Loose CLI workflow, agent, and hook directories remain UNVERIFIED and are not emitted. IDE `PreToolUse` hooks run through a compatibility bridge that translates the documented camelCase `toolCall` input and emits Antigravity's top-level `decision` schema. [Agents](https://www.antigravity.google/docs/cli/commands/agents) [subagents](https://antigravity.google/docs/cli/subagents/) [modes](https://www.antigravity.google/docs/cli/modes/) [settings](https://www.antigravity.google/docs/cli/settings) [hooks](https://www.antigravity.google/docs/hooks/)
- OpenClaw MATCH for the configured workspace, root `AGENTS.md` / `SOUL.md` / `IDENTITY.md`, and native `<workspace>/skills/<name>/SKILL.md`. The adapter parses documented JSON5, resolves documented `$include` strings and ordered lists relative to the including file within the config root or an explicit `OPENCLAW_INCLUDE_ROOTS` root, honors `OPENCLAW_HOME`, `OPENCLAW_STATE_DIR`, and `OPENCLAW_CONFIG_PATH`, and resolves the workspace through `agents.defaults.workspace`, then `OPENCLAW_WORKSPACE_DIR`, then `<stateDir>/workspace`. A malformed, missing, cyclic, or unsafe include, or a malformed or missing explicitly selected config, produces no fallback write. Lifecycle hooks exist natively, but Nexus-Hub installs none because they cannot intercept or deny tool calls; tool-interception guardrail parity is **NOT COVERED**. A future typed plugin using `api.on(...)` is owned by the platform integration maintainer and is outside this correction bundle. [configuration](https://docs.openclaw.ai/configuration) [environment](https://docs.openclaw.ai/help/environment) [multi-agent paths](https://docs.openclaw.ai/concepts/multi-agent) [workspace](https://docs.openclaw.ai/agent-workspace) [skills](https://docs.openclaw.ai/skills) [lifecycle hooks](https://docs.openclaw.ai/automation/hooks) [plugin hooks](https://docs.openclaw.ai/plugins/hooks)
- Windsurf MATCH on the current Devin Desktop / Cascade surfaces: user rules, skills, global workflows, and hooks under `~/.codeium/windsurf/`; workspace root `AGENTS.md`, `.devin/rules/`, and `.windsurf/{skills,workflows,hooks.json,hooks}`. `.windsurfrules` remains a compatibility instruction surface. Requests to `docs.windsurf.com` redirect with HTTP 307 to the current `docs.devin.ai/desktop/...` host. [memories](https://docs.devin.ai/desktop/cascade/memories) [skills](https://docs.devin.ai/desktop/cascade/skills) [workflows](https://docs.devin.ai/desktop/cascade/workflows) [hooks](https://docs.devin.ai/desktop/cascade/hooks)
- Copilot MATCH for personal instructions and native personal agents/hooks under `~/.copilot/`, plus repository instructions and native agents/hooks under `.github/`. The compatibility bridge maps native or Claude-compatible input into the catalog handler contract and returns top-level `permissionDecision`, `permissionDecisionReason`, and `modifiedArgs`; a nonzero `PreToolUse` child cannot be overridden by permissive stdout. [personal instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions) [custom agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/invoke-custom-agents) [hooks](https://docs.github.com/en/copilot/reference/hooks-reference)
- OpenCode MATCH for workspace-root `AGENTS.md`; the old `.opencode/AGENTS.md` claim was removed. [rules](https://opencode.ai/docs/rules/)
- Codex MATCH after removing the undocumented `.codex/skills` duplicate and retaining the documented `$HOME/.agents/skills` ladder. Hooks are enabled by default; `hooks = false` disables them, so Nexus-Hub no longer writes a mandatory `hooks = true` feature gate. The former `developers.openai.com/codex/skills` and `/hooks` URLs redirect to the current Learn ChatGPT pages. [skills](https://learn.chatgpt.com/docs/build-skills) [hooks](https://learn.chatgpt.com/docs/hooks)
- Hermes MATCH for native `.hermes/skills`. Shared `.agents/skills` is read only when the user explicitly configures `skills.external_dirs`; Nexus-Hub no longer claims automatic shared-global discovery. [skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)
- Cursor MATCH for the native skills path. Legacy `.cursor/commands` writes are retained for compatibility but remain UNVERIFIED; every command is also emitted as a skill through the verified skills surface. [skills](https://cursor.com/docs/skills)
- Gemini Code Assist MATCH only for the documented `GEMINI.md` instruction hierarchy. IDE-specific workflow, skill, agent, rule-directory, and hook discovery remains UNVERIFIED and is excluded from the enforced install check. [instructions](https://docs.cloud.google.com/gemini/docs/codeassist/use-agentic-chat-pair-programmer)
- Nexus-AI remains UNVERIFIED because its read contract is not publicly auditable.

### 2026-08-28 (v4.1.1 release - targeted re-verification)

v4.1.1 adds the local security-audit scanner-receipt contract. It changes no discovery path. Public skill-discovery pages for Claude Code, Cursor, and Codex were re-fetched; remaining platforms are unchanged from the same-day v4.1.0 full pass:

- Claude MATCH: personal `~/.claude/skills/<name>/SKILL.md` and project `.claude/skills/<name>/SKILL.md`. [Source](https://code.claude.com/docs/en/skills)
- Cursor MATCH: `.cursor/skills/`, `.agents/skills/`, `~/.cursor/skills/`, `~/.agents/skills/`, recursive. [Source](https://cursor.com/docs/skills)
- Codex DRIFT (low), continues: documents the `.agents/skills` ladder including `$HOME/.agents/skills`; still omits `~/.codex/skills`. Nexus-Hub writes the confirmed shared path, so delivery remains functional. [Source](https://learn.chatgpt.com/docs/build-skills)
- Other platforms: carried forward from the v4.1.0 full MATCH the same calendar day, not assumed. Nexus-AI remains UNVERIFIED.

No adapter, installer path, `contract_checks` row, or `install_verify` row changed.

### 2026-08-28 (v4.1.0 release - full re-verification)

All nine public contract platforms were re-fetched from current first-party documentation. Claude Code, Antigravity, Cursor, Gemini Code Assist, Gemini CLI, Kimi, OpenCode, and Qwen remain MATCH. Codex retains low non-breaking DRIFT because its current documentation names the shared `.agents/skills` ladder, including `$HOME/.agents/skills`, but omits the redundant `~/.codex/skills` path; Nexus-Hub writes the confirmed shared path, so delivery remains functional. Nexus-AI remains UNVERIFIED because its source is private.

The companion behavioral-defaults pass re-fetched all thirteen public source pages across the sixteen registered integrations. The outcome remains 13 VERIFIED and 3 UNVERIFIED, with no documented key rename, config-path move, or new cross-host redirect. No adapter, installer path, `contract_checks` row, `install_verify` row, or seeded default changed.
### 2026-08-25 (v4.1.0 - Pi added to the roster)

### 2026-08-23 (v3.20.1 release - catalog-only, same-day re-fetch)

v3.20.1 adds forty independently authored cybersecurity skills, F3/Navigator/conformance tooling, and an 800-line SKILL.md body cap. It changes no discovery path (installer diffs vs v3.20.0 are version constants only). Public skill-discovery pages for Claude and Cursor were re-fetched; remaining platforms are unchanged from the v3.20.0 same-day pass:

- Claude MATCH: personal `~/.claude/skills/<name>/SKILL.md` and project `.claude/skills/<name>/SKILL.md`. [Source](https://code.claude.com/docs/en/skills)
- Cursor MATCH: `.cursor/skills/`, `.agents/skills/`, `~/.cursor/skills/`, `~/.agents/skills/`, recursive. [Source](https://cursor.com/docs/skills)
- Other platforms: unchanged from the v3.20.0 same-day pass below (OpenCode MATCH; Gemini CLI MATCH; Qwen MATCH; Antigravity MATCH; Codex DRIFT unchanged; Kimi MATCH; Nexus-AI UNVERIFIED).

No adapter, installer path, `contract_checks` row, or `install_verify` row changed.

### 2026-08-23 (v3.20.0 release - catalog-only, same-day re-fetch)

v3.20.0 adds `agent-execution-isolation` and cross-links in existing skills. It changes no discovery path (installer diffs vs v3.19.2 are version constants only). Public skill-discovery pages for Claude and Cursor were re-fetched; remaining platforms are unchanged from the v3.19.2 same-day pass:

- Claude MATCH: personal `~/.claude/skills/<name>/SKILL.md` and project `.claude/skills/<name>/SKILL.md`. [Source](https://code.claude.com/docs/en/skills)
- Cursor MATCH: `.cursor/skills/`, `.agents/skills/`, `~/.cursor/skills/`, `~/.agents/skills/`, recursive. [Source](https://cursor.com/docs/skills)
- Other platforms: unchanged from the v3.19.2 same-day pass below (OpenCode MATCH; Gemini CLI MATCH; Qwen MATCH; Antigravity MATCH; Codex DRIFT unchanged; Kimi MATCH; Nexus-AI UNVERIFIED).

No adapter, installer path, `contract_checks` row, or `install_verify` row changed.

### 2026-08-23 (v3.19.2 release - same-day re-fetch)

v3.19.2 changes no discovery path (installer diffs vs v3.19.1 are version constants only). Public skill-discovery pages were re-fetched anyway so the freshness stamp is evidence, not a carry-forward:

- Claude MATCH: personal `~/.claude/skills/<name>/SKILL.md` and project `.claude/skills/<name>/SKILL.md` still documented. [Source](https://code.claude.com/docs/en/skills)
- Cursor MATCH: `.cursor/skills/`, `.agents/skills/`, `~/.cursor/skills/`, `~/.agents/skills/`, recursive. [Source](https://cursor.com/docs/context/skills)
- OpenCode MATCH: `~/.config/opencode/skills`, `.opencode/skills`, plus `.claude/skills` and `.agents/skills` aliases. [Source](https://opencode.ai/docs/skills)
- Gemini CLI MATCH: `~/.gemini/skills/` and `.gemini/skills/`, with `.agents/skills` alias. [Source](https://geminicli.com/docs/cli/using-agent-skills/)
- Qwen MATCH: `~/.qwen/skills/` and `.qwen/skills/`. [Source](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/)
- Antigravity MATCH: global `~/.gemini/config/skills/` and project `.agents/skills/`. [Source](https://codelabs.developers.google.com/getting-started-with-antigravity-skills)
- Codex DRIFT (low, unchanged): documents the `.agents/skills` ladder including `$HOME/.agents/skills`; still omits `~/.codex/skills`. Delivery remains functional through the confirmed user path. [Source](https://learn.chatgpt.com/docs/build-skills)
- Kimi MATCH: user `~/.kimi-code/skills` and project `.kimi-code/skills` (plus `.agents/skills` aliases). Current page: [kimi-code-cli skills](https://www.kimi.com/coding/docs/en/kimi-code-cli/customization/skills.html)
- Nexus-AI UNVERIFIED (private source)

No adapter, installer path, `contract_checks` row, or `install_verify` row changed.

### 2026-08-22 (v3.19.0 release - full re-verification)

All nine public contract platforms were re-fetched from current first-party documentation. Read-path outcomes remain eight MATCH, one non-breaking Codex DRIFT, and one UNVERIFIED Nexus-AI contract. Codex continues to document the shared `.agents/skills` ladder while omitting Nexus-Hub's redundant native write; Kimi now documents `.agents/skills` as an additive alias alongside its native `.kimi-code/skills` paths. Neither finding breaks delivery or requires an adapter change.

The companion behavioral-defaults pass also re-fetched all sixteen registered integrations. It remains 13 VERIFIED and 3 UNVERIFIED: Antigravity IDE and Windsurf/Devin document UI controls without a writable defaults file, while Nexus-AI remains privately auditable only.

### 2026-08-16 (v3.17.3 release - full re-verification)

All ten machine-checked platform contracts and all sixteen defaults-lever platforms were re-fetched from current first-party documentation. Read-path outcomes remain eight MATCH, one non-breaking Codex DRIFT, and one UNVERIFIED Nexus-AI contract; defaults remain 13 VERIFIED and 3 UNVERIFIED.

The release-specific finding is protocol compatibility rather than path drift. Cursor still documents `~/.cursor/hooks.json` and project `.cursor/hooks.json`, with hook responses expressed as one JSON object containing a permission decision. Claude Code still treats exit 0 with no stdout as success and reserves structured JSON for advanced control. Nexus-Hub therefore keeps the native hook implementations unchanged and installs a Cursor-only compatibility adapter; Windows invokes PowerShell siblings, while macOS and Linux retain Bash.

### 2026-08-15 (v3.17.2 release - full re-verification)

All ten machine-checked platform contracts and all sixteen defaults-lever platforms were re-fetched from current first-party documentation. Read-path outcomes remain eight MATCH, one non-breaking Codex DRIFT, and one UNVERIFIED Nexus-AI contract. Qwen continues to document its native `.qwen/skills` paths, while the shared `.agents/skills` alias is no longer documented there; Nexus-Hub already delivers to Qwen's native path, so no delivery change is required.

Defaults remain 13 VERIFIED and 3 UNVERIFIED. Current docs add or clarify granular approval controls for Codex, Cursor, Antigravity CLI, Hermes, and Copilot CLI, but every existing seeded key and path remains valid. These findings do not justify a replacement autonomy controller: v3.17.2 removes that unsupported surface and limits migration behavior to restoring recorded pre-controller state.

### 2026-08-15 (v3.17.0 release - full re-verification)

All ten machine-checked platform contracts and all sixteen defaults-lever platforms were re-fetched from current first-party documentation. Read-path outcomes are eight MATCH, one non-breaking Codex DRIFT, and one UNVERIFIED Nexus-AI contract. The pass corrected two defaults-lever records: Hermes moved its global reasoning key to `agent.reasoning_effort`, and Gemini Code Assist documented `geminicodeassist.agentYoloMode` in VS Code user settings. No installer read path was removed.

### 2026-08-02 (v3.15.7 release - full re-verification)

The release audit re-read current official documentation across the supported roster. Existing v3.15.7 write paths remain functional, so no `contract_checks`, `install_verify`, adapter, or installer path changed. The release classification is `RELEASE_WITH_DOCUMENTED_DRIFT`, not an all-MATCH claim.

- **MATCH or functionally aligned**: Claude, Cursor, OpenCode's supported surfaces, Aider, Nexus-AI's local contract, and Hermes's existing flattened skill children. Hermes now documents category-nested skill directories, but its recursive discovery still accepts the delivered flattened layout.
- **DRIFT-ADDITIVE, deferred to v3.15.8**: Codex custom TOML agents and native hooks; Gemini CLI and Qwen native hooks; Kimi custom agents and TOML hooks; Copilot custom agents and hooks. These are new upstream capabilities, not broken v3.15.7 delivery paths.
- **UNVERIFIED or partial**: Antigravity's exact global hook and `agy` workflow paths, Gemini IDE-specific skill discovery, Windsurf, and OpenClaw. Existing detection-gated or best-effort behavior is retained without promoting those rows to MATCH.

Primary sources: [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Claude features](https://code.claude.com/docs/en/features-overview), [Claude hooks](https://code.claude.com/docs/en/hooks), [Gemini CLI skills](https://geminicli.com/docs/cli/using-agent-skills/), [Gemini CLI context](https://geminicli.com/docs/cli/gemini-md/), [Qwen skills](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/), [Qwen hooks](https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/), [Kimi skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html), [Kimi agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html), [Kimi hooks](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html), [Copilot skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills), [Copilot agents](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents), [Copilot hooks](https://docs.github.com/en/copilot/concepts/agents/hooks), [OpenCode skills](https://opencode.ai/docs/skills/), [OpenCode commands](https://opencode.ai/docs/commands/), [OpenCode agents](https://opencode.ai/docs/agents), [Aider conventions](https://aider.chat/docs/usage/conventions.html), [Antigravity skills](https://codelabs.developers.google.com/getting-started-with-antigravity-skills), and [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills).

### 2026-07-21 (v3.15.0 Phase 4 - Qwen + Kimi reclassification)

Direct re-read of both platforms' official docs before reclassifying them from instruction-file-only to skills-bearing integrations (acting on Phase 1's GO verdicts; resolving DF-2 and DF-3).

- **Qwen Code - reclassified.** [qwenlm.github.io/qwen-code-docs](https://qwenlm.github.io/qwen-code-docs/) confirms skills at `~/.qwen/skills/` (global) + `.qwen/skills/` (project, folder-per-skill `SKILL.md`), agents at `~/.qwen/agents/<name>.md`, and commands at `~/.qwen/commands/` where **Markdown is the primary format and TOML is deprecated** (Qwen shows a migration prompt on TOML). So the integration delivers flattened skills + agents + **Markdown** commands (not TOML), preserving `QWEN.md`. **DF-2**: the docs only document "restart to load"; the auto-load bug is GitHub issue #2343 (not documented). Skills are delivered to BOTH scopes (global `~/.qwen/skills/` is the reliable path), which mitigates it. No `~/.agents/skills` alias for Qwen, so only native paths are written.
- **Kimi - reclassified + migrated (resolves DF-3).** [kimi.com/code/docs](https://www.kimi.com/code/docs/) confirms the current product is **Kimi Code CLI** (`MoonshotAI/kimi-code`, data root `~/.kimi-code/`) - a DIFFERENT product from the older "Kimi CLI" (`~/.kimi/`, moonshotai.github.io/kimi-cli) the prior integration targeted. Kimi Code CLI reads skills at `~/.kimi-code/skills/` + `~/.agents/skills/` (each auto-registering as `/skill:<name>`; no separate command format), AGENTS.md at `~/.kimi-code/AGENTS.md`, has no user-definable agents, and takes hooks as `config.toml` `[[hooks]]` (out of scope). Per the maintainer decision, the integration FULLY MIGRATED to `~/.kimi-code/` (AGENTS.md + native `~/.kimi-code/skills`), dropping the old `~/.kimi/` writes and the `.kimi/agent.yaml` companion. Native skills path only (not the shared `~/.agents/skills`), to avoid a teardown conflict with codex.

Source docs read: [Qwen skills](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/), [Qwen commands](https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/), [Kimi Code CLI data-locations](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/data-locations.html), [Kimi Code CLI skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html).

### 2026-07-21 (v3.15.0 Phase 3 - OpenCode agents + plugins/hooks decision)

Targeted re-read of OpenCode's official docs to finalize the two Phase 3 items:

- **Agents - DELIVERED.** [opencode.ai/docs/agents](https://opencode.ai/docs/agents/) confirms OpenCode reads custom agents from `~/.config/opencode/agents/` (global) and `.opencode/agents/` (project) as Markdown files with YAML frontmatter, the filename being the agent id. The `mode` field is OPTIONAL and defaults to `all`, so the catalog's `agents/*.md` personas (which carry `name`/`description`/`tools` frontmatter, not `mode`) load as-is - OpenCode uses `description` + the filename and ignores the non-native keys, exactly as Cursor consumes the same files. Delivered via a config-only `agents_subdir: "agents"` addition (the base `_mirror_catalog` does the verbatim tree copy). Contract JSON `contract_checks.opencode` + `install_verify` updated with the agents path.
- **Plugins / hooks - OUT OF SCOPE (documented non-gap, resolves DF-4).** [opencode.ai/docs/plugins](https://opencode.ai/docs/plugins/) confirms plugins are JavaScript/TypeScript modules loaded by Bun, each exporting plugin functions that subscribe to events (`tool.execute.before`, `file.edited`, ...); the docs state a plugin must be a JS/TS module and that a `.sh`/`.py` script cannot be dropped into `plugins/` and run. Nexus-Hub's shell/py hooks therefore cannot be delivered without authoring a JS/TS wrapper per hook, so OpenCode hooks stay out of scope (`hooks_supported: False`).

Source docs read: [Agents | OpenCode Docs](https://opencode.ai/docs/agents/), [Plugins | OpenCode Docs](https://opencode.ai/docs/plugins/).

### 2026-07-21 (v3.15.0 Phase 2 - Cursor DF-1 resolution)

Targeted re-read of Cursor's official docs to close the two Cursor items Phase 1.2 left UNVERIFIED (known-gap DF-1) before finalizing the Cursor integration:

- **`hooks.json` schema - RESOLVED.** [cursor.com/docs/hooks](https://cursor.com/docs/hooks) confirms the top-level shape `{"version": 1, "hooks": {<event>: [{...}]}}`; each entry's fields `type` / `timeout` / `loop_limit` / `failClosed` / `matcher` are optional. `beforeShellExecution` is a documented event; exit code `2` (or `{"permission":"deny"}`) blocks. Cursor reads both `~/.cursor/hooks.json` (user) and `<project>/.cursor/hooks.json` (project). Nexus-Hub registers Git guardrails with `failClosed: true`, routes the hook through `cursor-hook-compat.py` so successful stdout is exactly one JSON object, and invokes `.ps1` through PowerShell on Windows or `.sh` through Bash on macOS and Linux. Cursor also imports Claude-compatible hooks from `.claude/settings.json`; both installers route Nexus-Hub-owned entries through the same launcher while preserving Claude Code's silent-success behavior.
- **Global `~/.cursor/commands/` path - still UNVERIFIED (kept, tracked).** Project `.cursor/commands/<name>.md` is officially documented (custom slash commands, Cursor 1.6+) and confirmed. The user-global `~/.cursor/commands/` dir has NO reachable official doc (the dedicated commands page 404s / redirects to Skills); [forum.cursor.com](https://forum.cursor.com/t/personal-custom-slash-commands/133386) reports it as an open feature-request, not a built-in. Per plan sub-task 2.3 ("keep the global mirror unchanged") and the contract's negative-only-evidence caution, the global write is RETAINED (harmless if unread; removing a possibly-live path on negative evidence could break delivery) and recorded as the DF-1 residual for a future direct-confirmation cycle. Cursor read-paths that ARE confirmed this cycle: skills (recursive `SKILL.md`), subagents (plain `.md`), rules (`.mdc`), project commands, and the `hooks.json` schema.

Source docs read: [Hooks | Cursor Docs](https://cursor.com/docs/hooks), [Slash commands | Cursor Docs](https://cursor.com/docs/cli/reference/slash-commands), [Rules | Cursor Docs](https://cursor.com/docs/rules), [Cursor community: personal custom slash commands](https://forum.cursor.com/t/personal-custom-slash-commands/133386).

### 2026-07-20 (v3.15.0 platform-parity, Phase 1.2)

Web re-verification of the five platforms the v3.14.5 log deferred to v3.15.0 (the additive-surface parity targets), confirming exact read-paths against current official docs before wiring them in Phases 2-6. The findings are also recorded machine-readably in the sibling JSON's `parity_verification_v3_15_0` block. This cycle records READ-paths only; the installer WRITE side, the JSON `contract_checks` / `install_verify` rows, and the surface table below are updated per phase as each integration lands (adding a `contract_checks` row before its integration writes the surface would fail `verify_platform_contracts.py`). Classifications: MATCH (unchanged), DRIFT (gained a surface or the framing is stale), GAINED (a previously-unused surface confirmed), UNVERIFIED (not confirmable from reachable docs).

**Cursor (DRIFT - gained Skills, Subagents, and Hooks in Cursor 2.4):**

- Skills: reads `~/.cursor/skills/`, `~/.agents/skills/`, `~/.claude/skills/` (global) and `.cursor/skills/`, `.agents/skills/`, `.claude/skills/` (project); folder-per-skill `SKILL.md`, and discovery is RECURSIVE (nested and flattened both register).
- Subagents: `~/.cursor/agents/` / `.cursor/agents/` (also reads `.claude/agents/`); plain `.md` with YAML frontmatter, NOT `.agent.md` (correcting the pre-scout guess).
- Hooks: `~/.cursor/hooks.json` / `<project>/.cursor/hooks.json`; schema `{"version":1,"hooks":{<event>:[{"command":...}]}}`; events include `beforeShellExecution`, `afterShellExecution`, `afterFileEdit`, `preToolUse`, `postToolUse`, `sessionStart`, `stop`; exit 0 = ok, 2 = block, any other = fail-open; a `matcher` field is supported. A direct human read of the hooks doc is recommended before Phase 2 emits optional fields, to lock exact spelling.
- Commands: project `.cursor/commands/<name>.md` (flat `.md`, `/name`) CONFIRMED; the baseline global `~/.cursor/commands/` path is UNVERIFIED against reachable docs (kept, not removed, pending a direct check).
- Rules: `.cursor/rules/*.mdc` MATCH (root `AGENTS.md` also read).

**OpenCode (DRIFT - gained an agents folder; a plugins/hooks mechanism exists but on an incompatible runtime):**

- Agents: `~/.config/opencode/agents/` / `.opencode/agents/`; `.md` + YAML frontmatter (filename becomes the agent name).
- Plugins/hooks: `~/.config/opencode/plugins/` / `.opencode/plugins/`; JS/TS modules on a Bun runtime, NOT a Claude-style shell/python hook model. Nexus-Hub's `.sh`/`.py` hooks cannot be dropped in; delivering hooks here would require a JS/TS wrapper. Phase 3.2 recommendation: document as out-of-scope unless a wrapper is warranted.
- Skills and Commands MATCH; Rules MATCH (no `rules/` folder; `AGENTS.md` + an `instructions[]` array).

**Qwen Code (Gemini-CLI-class: YES; Phase 4 decision: GO):**

- Qwen Code is an open-source Gemini CLI fork and reproduces the full surface family under `~/.qwen` / `.qwen`.
- Skills: `~/.qwen/skills/<name>/SKILL.md` (global), `.qwen/skills/<name>/SKILL.md` (project); folder-per-skill one level, `name` + `description` frontmatter.
- Commands: `~/.qwen/commands/<name>.{md,toml}`; Markdown primary, TOML (`description` + `prompt`) deprecated-but-supported and identical to Gemini CLI's format.
- Agents: `~/.qwen/agents/<name>.md`. Rules: `QWEN.md` context file; no `rules/` folder.
- Caveat: open issue #2343 reports project-scoped skills may not auto-load on some builds; Phase 4 should live-smoke-test skill discovery before shipping.

**Kimi Code CLI (Gemini-CLI-class: YES; Phase 4 decision: GO) - with a product disambiguation:**

- The current product is Kimi Code CLI (`MoonshotAI/kimi-code`, data root `~/.kimi-code/`), the Node.js successor to the deprecated Python Kimi CLI (`~/.kimi/`) that the current baseline targets. Migration preserves `~/.kimi/`, so both coexist, but the new product reads `~/.kimi-code/`.
- Skills: `~/.kimi-code/skills/` + `~/.agents/skills/` (global), `.kimi-code/skills/` + `.agents/skills/` (project); folder-per-skill `SKILL.md` (or flat `<name>.md`), one level. The new product does NOT scan `~/.claude/skills`.
- Commands: no standalone command format; every skill auto-registers as `/skill:<name>` (the docs' `commands.html` returns 404). Commands are skills.
- Agents: not a distribution surface (three fixed built-in subagents). The baseline `.kimi/agent.yaml` is unsupported in the new product and should be dropped.
- Hooks: a `[[hooks]]` TOML array in `~/.kimi-code/config.toml` (config-merge, not a folder copy).
- Phase 4 note: resolve the old `~/.kimi/` vs new `~/.kimi-code/` vs the cross-tool `.agents/skills/` path choice before wiring.

**Copilot (DRIFT - skills are now native and default-on; agents and hooks are new):**

- Skills: `.github/skills/<name>/SKILL.md` is the native canonical path (also reads `.claude/skills/`, `.agents/skills/`; global `~/.copilot/skills/`, `~/.agents/skills/`, and in VS Code `~/.claude/skills/`); folder-per-skill one level, now DEFAULT-ON. The `.github/skills` PATH matches the baseline; the "opt-in / env-gated / off-by-default" FRAMING is stale.
- Agents: `.github/agents/*.agent.md` (project), `~/.copilot/agents/` (global).
- Hooks: `.github/hooks/*.json` (Preview), Claude-compat `.claude/settings.json`.
- Instruction: `.github/copilot-instructions.md` MATCH (`AGENTS.md` / `CLAUDE.md` additively supported behind settings). Prompts: `.github/prompts/*.prompt.md` MATCH.
- Phase 5 note: `.github/skills/` is commit-visible, so Nexus-Hub keeps the never-overwrite-existing-file guarantee even though Copilot no longer technically requires opt-in.

**Reclassification go/no-go (the Phase 4 gate, sub-task 1.3):**

- Qwen: GO - reclassify from instruction-file-only to skills + commands (+ agents) at the verified `~/.qwen` / `.qwen` paths.
- Kimi: GO - reclassify to skills + skills-as-commands, resolving the `~/.kimi-code/` (new) vs `.agents/skills/` (cross-tool) path in Phase 4; drop the unsupported `.kimi/agent.yaml`.

**Sources (fetched 2026-07-20):**

- Cursor skills: <https://cursor.com/docs/skills>
- Cursor subagents: <https://cursor.com/docs/subagents>
- Cursor hooks: <https://cursor.com/docs/hooks>
- Cursor rules / commands: <https://cursor.com/docs/rules>, <https://cursor.com/docs/customize-cursor>
- OpenCode agents / plugins / skills / commands / rules: <https://opencode.ai/docs/agents/>, <https://opencode.ai/docs/plugins/>, <https://opencode.ai/docs/skills/>, <https://opencode.ai/docs/commands/>, <https://opencode.ai/docs/rules/>
- Qwen Code skills / commands / sub-agents / settings: <https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/>, <https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/>, <https://qwenlm.github.io/qwen-code-docs/en/users/features/sub-agents/>, <https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/>
- Kimi Code CLI skills / slash-commands / agents / hooks / data-locations / migration: <https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/reference/slash-commands.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/data-locations.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/guides/migration.html>
- Copilot Agent Skills / custom agents / hooks / instructions / prompts: <https://docs.github.com/en/copilot/concepts/agents/about-agent-skills>, <https://docs.github.com/en/copilot/reference/custom-agents-configuration>, <https://code.visualstudio.com/docs/agent-customization/hooks>, <https://code.visualstudio.com/docs/agent-customization/custom-instructions>, <https://code.visualstudio.com/docs/copilot/customization/prompt-files>

### 2026-07-20 (v3.14.7 release - reaffirmed, no re-verification)

v3.14.7 is a cosmetic usage-monitor fix release: it changed only the two VS Code usage-monitor extensions' status-bar label rendering (an icon-to-text spacing gap), touching no platform read-paths, integration adapters, or installer copy targets. The 2026-07-19 full 13-platform web re-verification therefore still holds, so the contract is reaffirmed and the freshness marker re-stamped to 3.14.7 without a fresh web-search cycle. The additive drift recorded below remains deferred to v3.15.0.

### 2026-07-20 (v3.14.6 release - reaffirmed, no re-verification)

v3.14.6 is a usage-monitor + installer-log fix release: it changed no platform read-paths, integration adapters, or installer copy targets (only the two VS Code usage-monitor extensions and the installer's console output). The 2026-07-19 full 13-platform web re-verification therefore still holds, so the contract is reaffirmed and the freshness marker re-stamped to 3.14.6 without a fresh web-search cycle. The additive drift recorded below remains deferred to v3.15.0.

### 2026-07-19 (v3.14.5 release)

A full web re-verification of all supported platforms against current official docs. Dead-path bugs (our installer wrote where the platform no longer reads) were fixed in this release; additive drift (platforms that GAINED skills/agents/hooks surfaces we do not yet use) is deferred to v3.15.0 (platform parity), tracked in `docs/v3/v3.14/known-gaps.md`.

**Fixed in v3.14.5:**

- **OpenCode** - canonical global dir moved from `~/.opencode/` to `~/.config/opencode/` (XDG). The instruction file + commands were never reaching OpenCode at the old path (skills still did, via the `~/.claude/skills` + `~/.agents/skills` aliases). Adapter + contract + install-verify updated.
- **Kimi** - the instruction file moved from `.kimi/system.md` to `.kimi/AGENTS.md`. Kimi Code CLI auto-injects the merged `AGENTS.md` (including `.kimi/AGENTS.md`); `.kimi/system.md` is only loaded via `--agent-file`, so the old surface never reached Kimi. Resolves the v3.11.0-deferred Kimi known-gap.
- **OpenClaw** - global trio moved from `~/.openclaw/` to `~/.openclaw/workspace/` (the single global workspace dir OpenClaw actually reads).

**Deferred to v3.15.0 (additive - platforms gained surfaces; not breakage):**

- **Copilot** now natively reads Agent Skills (on by default: `.github/skills/`, `~/.copilot/skills/`, and `~/.claude/skills/`), custom agents (`.github/agents/*.agent.md`), and hooks.
- **Cursor** gained Agent Skills (`.cursor/skills/`, `~/.cursor/skills/`, `.agents/skills/`), subagents, and hooks (`hooks.json`).
- **Codex** gained a hooks system (`~/.codex/hooks.json` / `[hooks]` in `config.toml`). Also: one source reports `~/.codex/skills` is no longer read (only `~/.agents/skills` is); Nexus-Hub still writes both, so skills reach Codex regardless - the redundant `~/.codex/skills` write is kept pending a second confirmation (removing a possibly-live path on single-source evidence could break delivery). **Delivered in v3.15.8 Phase 5** - see the Codex native surfaces section below.
- **OpenCode** supports agents (`~/.config/opencode/agents/`) and plugin-based hooks; its commands ARE a TUI slash surface and it has no `rules/` dir (uses `AGENTS.md` + an `instructions[]` array).

**Unverified this cycle (official docs unreachable / undocumented):**

- **Antigravity 2.0** global-workflows dir is community-reported as `~/.gemini/antigravity/global_workflows/` (vs the contract's `~/.gemini/config/global_workflows/`); the official docs are a client-rendered SPA that could not be fetched, so this is NOT changed pending an authoritative source. Its `.agents/subagents/` static dir appears obsolete (subagents are now dynamic).
- **Gemini IDE** per-tool read-paths (`~/.gemini/workflows`, `agents/`, `rules/`) are undocumented in official sources; the IDE was also sunset for free/Pro/Ultra on 2026-06-18 (enterprise-only), like the CLI.

**Notes:** Windsurf rebranded to "Devin Desktop"; the legacy `.windsurfrules` + `~/.codeium/windsurf/memories/global_rules.md` surfaces are still served (a `.devin/rules/` surface is now preferred - optional future adoption). Claude, Aider, Qwen verified clean.

## Read/write surface table

Formats: skills = folder-per-skill `SKILL.md`. "flattened" means one level deep (`skills/<name>/SKILL.md`), which requires dropping the catalog's `<category>/` layer; "nested" means the catalog `<category>/<name>/` tree is copied verbatim. commands = `.md` verbatim unless noted. Every command additionally surfaces as a skill (`skills/<command>/SKILL.md`, invoked `$command`) on platforms whose reusable-action surface is skills.

| Platform (key) | Scope | Instruction file | Commands / slash surface | Skills | Agents | Rules | Hooks |
|---|---|---|---|---|---|---|---|
| Claude (`claude`) | global | `~/.claude/CLAUDE.md` (marker-merged) | `~/.claude/commands/*.md` (slash) | flattened `~/.claude/skills/<name>/` (+ command-skills) | `~/.claude/agents/` | `~/.claude/rules/` | `~/.claude/hooks/` + settings.json |
| Claude | workspace | `<project>/CLAUDE.md` (root) | `<project>/.claude/commands/*.md` | flattened `.claude/skills/<name>/` (+ command-skills) | `.claude/agents/` | `.claude/rules/` | `.claude/hooks/` |
| Codex (`codex`) | global | `~/.codex/AGENTS.md` (marker-merged) | `~/.codex/prompts/*.md` (flat, `/prompts:name`, deprecated) + skills below (`$name`) | flattened `~/.agents/skills/<name>/` (+ one per command) | `~/.codex/agents/<name>.toml` (transformed from `catalog/agents/*.md`) | not read | `~/.codex/hooks.json` (structured merge) + `~/.codex/hooks/`; enabled by default and disabled only by an existing `hooks = false` setting |
| Codex | workspace | `<project>/AGENTS.md` (root) | `<project>/.codex/prompts/*.md` + skills below | flattened `.agents/skills/<name>/` (+ one per command) | `.codex/agents/<name>.toml` | not read | `.codex/hooks.json` + `.codex/hooks/` |
| Antigravity 2.0 IDE (`antigravity2`) | global | `~/.gemini/GEMINI.md` (shared instruction) | `~/.gemini/config/global_workflows/<name>.md` (slash) + skills below | flattened `~/.gemini/config/skills/<name>/` (+ one per command) | `~/.gemini/config/agents/` | `~/.gemini/GEMINI.md` | `~/.gemini/config/hooks/` + `hooks.json` |
| Antigravity `agy` CLI (`antigravity2`) | global | shared `~/.gemini/GEMINI.md` | UNVERIFIED; not emitted | flattened `~/.gemini/antigravity-cli/skills/<name>/` | UNVERIFIED; not emitted | shared `~/.gemini/GEMINI.md` | UNVERIFIED; not emitted |
| Antigravity 2.0 | workspace | `<project>/AGENTS.md` (root) | `<project>/.agents/workflows/*.md` (slash) + skills below | flattened `.agents/skills/<name>/` (+ one per command) | `.agents/agents/` | `.agents/rules/` | `.agents/hooks/` + hooks.json |
| Gemini IDE (`gemini`) | global | `~/.gemini/GEMINI.md` | UNVERIFIED compatibility write | UNVERIFIED compatibility write | UNVERIFIED compatibility write | UNVERIFIED compatibility write | UNVERIFIED |
| Gemini CLI (`gemini-cli`, enterprise) | global | `~/.gemini/GEMINI.md` | `~/.gemini/commands/*.toml` (TOML, slash) | flattened `~/.gemini/skills/<name>/` (also reads `~/.agents/skills`) | `~/.gemini/agents/` | `~/.gemini/rules/` | `~/.gemini/settings.json` `hooks` key (structured merge) + `~/.gemini/hooks/`; renamed events, regex tool matchers |
| Gemini CLI | workspace | `<project>/.gemini/GEMINI.md` | `.gemini/commands/*.toml` (TOML, slash) | flattened `.gemini/skills/<name>/` | `.gemini/agents/` | `.gemini/rules/` | `.gemini/settings.json` `hooks` key + `.gemini/hooks/`; commands resolve via `$GEMINI_PROJECT_DIR` |
| Copilot (`copilot`) | global | `~/.copilot/copilot-instructions.md` (marker-merged) | VS Code `<user>/prompts/<name>.prompt.md` (slash) | opt-in selector writes native skill folders | `~/.copilot/agents/<name>.agent.md` | none | `~/.copilot/hooks/nexus-hub.json` + owned scripts |
| Copilot | workspace | `<project>/.github/copilot-instructions.md` | project prompt files are not seeded | opt-in `.github/skills/<name>/SKILL.md` | `.github/agents/<name>.agent.md` | none | `.github/hooks/nexus-hub.json` + owned scripts |
| Cursor (`cursor`) | global | none | `~/.cursor/commands/<name>.md` compatibility write, UNVERIFIED; commands also emit as skills | flattened `~/.cursor/skills/<name>/` (+ command-skills) | `~/.cursor/agents/*.md` | none | `~/.cursor/hooks.json` + `~/.cursor/hooks/` (git-guardrails) |
| Cursor | workspace | `<project>/AGENTS.md` (marker-merged) | `<project>/.cursor/commands/<name>.md` compatibility write, UNVERIFIED; commands also emit as skills | flattened `.cursor/skills/<name>/` (+ command-skills) | `.cursor/agents/*.md` | `<project>/.cursor/rules/*.mdc` (flattened) | `.cursor/hooks.json` + `.cursor/hooks/` |
| OpenCode (`opencode`) | global | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/commands/*.md` (slash in the TUI) | flattened `~/.config/opencode/skills/<name>/`; also reads `~/.claude/skills` + `~/.agents/skills` | `~/.config/opencode/agents/*.md` | via AGENTS.md + `instructions[]` | plugins require JS/TS; shell/py hooks incompatible |
| OpenCode | workspace | `<project>/AGENTS.md` (root) | `.opencode/commands/` | flattened `.opencode/skills/<name>/` (also `.claude/skills`, `.agents/skills`) | `.opencode/agents/*.md` | via AGENTS.md + `instructions[]` | plugins require JS/TS; shell/py hooks incompatible |
| Aider (`aider`) | workspace | `<project>/CONVENTIONS.md` (root) | none (skills via embedded SKILL_INDEX) | none | none | none | none |
| Devin Desktop / Windsurf (`windsurf`) | global | `~/.codeium/windsurf/memories/global_rules.md` | `~/.codeium/windsurf/global_workflows/*.md` | flattened `~/.codeium/windsurf/skills/<name>/` (+ command-skills) | none | via global rules | `~/.codeium/windsurf/hooks.json` + `hooks/` |
| Devin Desktop / Windsurf | workspace | `<project>/AGENTS.md` (root) + `.windsurfrules` compatibility | `.windsurf/workflows/*.md` | flattened `.windsurf/skills/<name>/` (+ command-skills) | none | `.devin/rules/nexus-hub.md` | `.windsurf/hooks.json` + `.windsurf/hooks/` |
| Kimi (`kimi`) | global | `~/.kimi-code/AGENTS.md` | skills register as `/skill:<name>` | flattened `~/.kimi-code/skills/<name>/` (+ command-skills) | `~/.kimi-code/agents/<name>.md` (verbatim catalog Markdown) | via AGENTS.md | `[[hooks]]` in `~/.kimi-code/config.toml` (marker-managed block) + `~/.kimi-code/hooks/` |
| Kimi | workspace | `<project>/.kimi-code/AGENTS.md` | skills register as `/skill:<name>` | flattened `.kimi-code/skills/<name>/` (+ command-skills) | `.kimi-code/agents/<name>.md` (verbatim catalog Markdown) | via AGENTS.md | none - the project config is `local.toml` and documents only `[workspace]`, so no project hook path exists |
| Qwen (`qwen`) | global | `~/.qwen/QWEN.md` | `~/.qwen/commands/*.md` | flattened `~/.qwen/skills/<name>/` (+ command-skills) | `~/.qwen/agents/*.md` | via QWEN.md | `~/.qwen/settings.json` `hooks` key (structured merge) + `~/.qwen/hooks/`; Claude-style events, regex tool matchers, `shell` field |
| Qwen | workspace | `<project>/QWEN.md` | `.qwen/commands/*.md` | flattened `.qwen/skills/<name>/` (+ command-skills) | `.qwen/agents/*.md` | via QWEN.md | `.qwen/settings.json` `hooks` key + `.qwen/hooks/`; commands resolve via `$QWEN_PROJECT_DIR` |
| OpenClaw (`openclaw`) | configured workspace | `<workspace>/AGENTS.md` + `SOUL.md` + `IDENTITY.md`; workspace comes from `agents.defaults.workspace`, then `OPENCLAW_WORKSPACE_DIR`, then the active state directory's `workspace` default | skills below | flattened `<workspace>/skills/<name>/` (+ command-skills) | none | via root identity files | lifecycle hooks exist natively, but Nexus-Hub installs none; typed-plugin interception NOT COVERED |
| Nexus-AI (`nexus-ai`) | global | `~/.nexus-ai/catalog/NEXUS_AI.md` (dedicated) | `~/.nexus-ai/catalog/commands/` | flattened `~/.nexus-ai/catalog/skills/<name>/` (+ command-skills) | `~/.nexus-ai/catalog/agents/` | `~/.nexus-ai/catalog/rules/` | `~/.nexus-ai/catalog/hooks/` |
| Hermes (`hermes`) | global | none (skills-native; no instruction file) | none (skills are the action surface) | flattened `~/.hermes/skills/<name>/` (+ command-skills); shared `~/.agents/skills/` requires explicit `skills.external_dirs` configuration | none | none | not supported |
| Hermes | workspace | none | none | flattened `.hermes/skills/<name>/` (+ command-skills); shared `.agents/skills/` requires explicit configuration | none | none | none |
| Pi (`pi`) | global | `~/.pi/agent/AGENTS.md` (marker-merged) | `~/.pi/agent/prompts/*.md` (prompt templates, `/name`) | flattened `~/.pi/agent/skills/<name>/` (+ one per command) | not read | not read | not supported (extensions are TypeScript) |
| Pi | workspace | not claimed (Codex owns project-root `AGENTS.md`; Pi reads it from cwd) | `<project>/.pi/prompts/*.md` | flattened `.pi/skills/<name>/` (+ one per command) | not read | not read | not supported |

### Codex native agents and hooks (v3.15.8 Phase 5)

Re-verified 2026-08-02 against the official [subagents](https://developers.openai.com/codex/subagents) and [hooks](https://developers.openai.com/codex/hooks) references. Both surfaces are now delivered; neither is a verbatim catalog copy.

**Custom agents.** Codex reads standalone TOML files from `~/.codex/agents/` (personal) and `<project>/.codex/agents/` (project-scoped, loaded only when the project is trusted). Every file must define `name`, `description`, and `developer_instructions`; `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config` are optional. Nexus-Hub's catalog agents are Markdown with `name` / `description` / `tools` frontmatter, so the integration transforms each into one TOML file, mapping the body to `developer_instructions`. Codex has no equivalent of the `tools` allowlist; it is preserved as a comment, and an agent whose tools are all non-mutating (`Read`, `Glob`, `Grep`, `LS`, `WebFetch`, `WebSearch`, `NotebookRead`) additionally gets `sandbox_mode = "read-only"`. That inference can only constrain an agent, never widen it. Agent files are manifest-owned: an existing file Nexus-Hub does not own is a user-authored agent and is never overwritten.

**Hooks.** Codex discovers hooks beside an active config layer, as either `hooks.json` or an inline `[hooks]` table in `config.toml`. Nexus-Hub writes `hooks.json` at `~/.codex/` and `<project>/.codex/`, because a single layer holding both representations makes Codex warn at startup, and because `config.toml` already carries the user's own settings. The file is a **structured merge**, not a wholesale write: a handler is Nexus-Hub-owned when its command points into the installed hooks directory, so user handlers survive an install and teardown removes only ours. A malformed `hooks.json` is never rewritten.

Codex event names line up with `catalog/hooks/settings.json` (`SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `PreCompact`, `Stop`), but its matcher vocabulary is narrower: only `Bash`, `apply_patch` (aliases `Edit` / `Write`), MCP tool names, and other local function tools are recognized. Nexus-Hub's `PowerShell`, `MultiEdit`, and `Skill` matchers have no Codex equivalent - Codex routes every shell call through `Bash` - so those groups are dropped rather than mapped onto an approximation Codex would never fire.

Each handler carries `commandWindows`, the official Windows-only command override. This maps directly onto the repo's `.sh` / `.ps1` sibling convention: the POSIX command runs the `.sh` and `commandWindows` runs the `.ps1`, so a Windows user gets the same guardrail from the same registration.

Two upstream behaviors bound what an install can promise:

- The hook engine is enabled by default. A user or administrator can explicitly disable it with `hooks = false`; Nexus-Hub respects that choice and does not edit `config.toml` to force `hooks = true`.
- Non-managed hooks are inert until trusted. Codex requires each hook to be reviewed via `/hooks` and records trust against the hook's hash, so installing a hook does not arm it. The install summary says so rather than claiming a guardrail the user does not yet have.

Teardown prunes owned handlers from `hooks.json`, deletes the file only when nothing else remained, and removes owned agent and script files. It never edits the user's global hook enablement setting.

### Gemini CLI and Qwen native hooks (v3.15.8 Phase 6)

Re-verified 2026-08-02 against the upstream [Gemini CLI hooks reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/index.md) and the [Qwen Code hooks documentation](https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/). Both platforms read hooks from a `hooks` key inside their main `settings.json` - `~/.gemini/settings.json` and `.gemini/settings.json`, `~/.qwen/settings.json` and `.qwen/settings.json` - using the same nested `{event: [{matcher, hooks: [handler]}]}` shape. Qwen Code is a Gemini CLI fork, so the delivery choreography is shared; three differences are not.

**Event names.** Qwen kept the Claude-style names `catalog/hooks/settings.json` already uses. Gemini CLI renamed all of them, so its mapping is a real translation: `PreToolUse` becomes `BeforeTool`, `PostToolUse` becomes `AfterTool`, `UserPromptSubmit` becomes `BeforeAgent`, `Stop` becomes `AfterAgent`, and `PreCompact` becomes `PreCompress`. Both maps are written out explicitly rather than derived, so an upstream rename shows up as a diff instead of passing through silently.

**Matchers are regular expressions over each platform's own tool ids**, not Claude's tool names and not literals. `Bash` becomes `^(run_shell_command)$`, `Write` becomes `^(write_file)$`, and `Edit` / `MultiEdit` both become `^(replace)$`. `Skill` has no equivalent on either platform and is dropped. Only the tool events (`BeforeTool` / `AfterTool`, `PreToolUse` / `PostToolUse`) carry a matcher; the lifecycle events either always fire or match on something that is not a tool - a session source, a compact trigger - so emitting a tool matcher there would produce a registration that never matches.

**There is no `commandWindows`.** Codex's schema has an explicit Windows override slot; neither of these platforms does, and both funnel every shell call through a single `run_shell_command` tool, which collapses Nexus-Hub's separate `Bash` and `PowerShell` matchers onto one tool id. A registration therefore has to commit to one command string, so the installer picks it from the **installing host**: a Windows install registers the `.ps1` sibling and the PowerShell-flavored guardrails, a POSIX install registers the `.sh` and the Bash-flavored ones. Both siblings are copied either way, so re-running the installer on the other OS re-points the registration without touching the scripts. Qwen additionally accepts a `shell` field (`bash` | `powershell`) and a `statusMessage`, which are emitted there and omitted for Gemini CLI.

**Ownership is the handler `name`.** Both schemas carry an optional `name` for logging, so every Nexus-Hub handler is named `nexus-hub:<script-stem>`. That identity survives a path change, and it is what Gemini CLI fingerprints project hooks on, so a stable name also avoids re-triggering its untrusted-hook warning on every install. The installed hooks directory is checked as a second signal, so a handler the user renamed by hand is still recognized as ours rather than duplicated.

Because `settings.json` holds the user's entire CLI configuration rather than just hooks, the merge is more conservative than Codex's dedicated `hooks.json`: every unrelated key is preserved, the previous content is backed up beside the file, the write goes through a temp file, and a **malformed file is never rewritten**. Losing a user's model, theme, and MCP settings to a transient syntax error would be far worse than skipping the registration and logging why. Workspace-scope commands resolve through the platform's own `$GEMINI_PROJECT_DIR` / `$QWEN_PROJECT_DIR` variable (in PowerShell's `$env:` form on Windows) so a committed project `settings.json` does not carry one developer's absolute path.

Neither platform needs a feature switch - hooks are enabled by default, unlike Codex. What both have is a user-set kill switch (Qwen's top-level `disableAllHooks`, Gemini CLI's `/hooks disable-all`), so the install summary reports when `disableAllHooks` is already on rather than claiming an armed guardrail. Gemini CLI's exit-code contract also makes a broken hook non-fatal: only exit 2 blocks, and any other non-zero exit is a warning that lets the interaction proceed.

Existing gates are inherited unchanged. Gemini CLI remains enterprise-only and opt-in behind `--enterprise` after the 2026-06-18 sunset, and Qwen's global scope stays detection-gated on `~/.qwen`, so hooks ship exactly where each platform already installs. Teardown prunes owned handlers from `settings.json`, untracks the file before the manifest sweep so the user's configuration is never deleted, removes owned scripts, and drops the `hooks/` directory only if it ends up empty.

One documented second read path is deliberately unused: Gemini CLI extensions can carry hooks in `~/.gemini/extensions/<name>/hooks/hooks.json`, with `${extensionPath}` and `${/}` substitution that would solve the absolute-path and separator problems outright. It is recorded as a follow-on rather than adopted because the reference documents only `gemini extensions install` for populating that directory, it has no project scope, and shipping a directly-written extension would be an inferred write path rather than a verified one.

### Kimi custom agents and TOML hooks (v3.15.8 Phase 7)

Re-verified 2026-08-02 against the Kimi Code CLI [agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html), [hooks](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html), [built-in tools](https://www.kimi.com/code/docs/en/kimi-code-cli/reference/tools.html), and [configuration](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/config-files) references. This supersedes the pre-v3.15.8 claim that Kimi had only fixed built-in sub-agents and no reachable hook surface.

**Custom agents are a verbatim copy, not a transform.** Kimi discovers agent files as Markdown with YAML frontmatter, scanning `~/.kimi-code/agents/` (global) and `.kimi-code/agents/` (project) recursively. It explicitly accepts the shape the catalog already ships: `description` is the only required field, `name` falls back to the filename, the comma-separated `tools` form is supported specifically to "keep Claude Code-style agent files loadable", and unknown fields are ignored so foreign or newer fields do not break loading. Nexus-Hub therefore copies each `catalog/agents/*.md` unchanged, which means an agent behaves identically on Kimi and Claude. Only validation is applied: a file with no `description`, no body, or a non-kebab-case resolved name is skipped rather than shipped for Kimi to reject at load time. Files are manifest-owned, so a user-authored agent at the same path is never overwritten.

Kimi also reads the cross-tool shared `~/.agents/agents/` and project `.agents/agents/` directories. Nexus-Hub deliberately does not write either, matching the rule the Kimi integration already follows for skills: no other integration currently claims those paths, and claiming them here would create the teardown conflict the shared-path ownership rule exists to prevent.

One upstream caveat is documented rather than worked around. Kimi notes that a custom agent delegated as a sub-agent runs without the built-in "your final message is the entire handoff" framing, and suggests stating that in the agent body. Injecting a generated paragraph would make the delivered agent diverge from its catalog source, so the copy stays verbatim.

**Hooks need a comment-preserving merge, and are global-scope only.** Kimi's hooks are a `[[hooks]]` array of tables in `~/.kimi-code/config.toml` - the same file that holds the user's providers, models, permission rules, and tool switches. Three schema properties drive the implementation:

- **Only four fields are permitted** (`event`, `matcher`, `command`, `timeout`), and per the docs "extra fields will cause the config file to fail to load". There is consequently no `name` slot to carry ownership the way Gemini CLI and Qwen do, and emitting one would break the user's entire configuration.
- **Each entry holds exactly one command**, where `catalog/hooks/settings.json` groups several commands under one matcher, so one catalog group expands into several entries sharing an event and matcher. Kimi already runs identical commands only once, and the builder additionally suppresses duplicate event-matcher-command triples so the user's config is not padded.
- **`timeout` is in seconds** (1-600, default 30), not the milliseconds the Gemini-CLI-class platforms use.

Ownership is a **marker-delimited managed block** (`# >>> NEXUS_HUB_HOOKS_START >>>` to `# <<< NEXUS_HUB_HOOKS_END <<<`) appended to `config.toml`, reusing the marker-merge convention Nexus-Hub already applies to instruction files. The user's TOML is never parsed and re-emitted - only that region is spliced - so comments, table order, and whitespace outside the block survive byte-for-byte, which is what makes this viable without a non-stdlib TOML round-tripper. The merged result is validated with `tomllib` before it is committed and the write rolls back on a parse failure, and a file that was *already* invalid before the merge is left untouched so our block cannot be mistaken for the cause. `[[hooks]]` is an absolute array-of-tables header, so appending at end of file is valid regardless of what precedes it.

Event names need no translation: every event the catalog registers (`SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `PreCompact`) exists in Kimi under the same name. Matchers are regexes over Kimi's built-in tool names, which match Claude's exactly for the ones that matter - `Bash`, `Write`, `Edit`, `Skill` - so the mapping is near-identity. `MultiEdit` folds into `Edit`, because Kimi's `Edit` covers repeated replacement through `replace_all` rather than exposing a second tool, and `PowerShell` is dropped because Kimi routes every shell call through `Bash` on every platform, so the Bash-matched guardrails already cover Windows. As with Gemini CLI and Qwen there is no `commandWindows` slot, so the installing host selects the `.sh` or `.ps1` sibling while both are copied.

**Workspace scope carries agents but not hooks.** Kimi's project-local configuration file is `.kimi-code/local.toml`, and it documents only a `[workspace]` table holding `additional_dir`; the upstream docs place `[[hooks]]` exclusively in `~/.kimi-code/config.toml`. Writing hooks into a project file would therefore be an invented path, so the workspace hook row stays finding-only. Kimi hooks are also **fail-open by design** - a hook that errors or times out allows the action - which the install summary states so the guardrail is not mistaken for a hard barrier.

Teardown splices the managed block out of `config.toml`, untracks the file before the manifest sweep so the user's configuration is never deleted, removes owned agent and script files, and drops the `agents/` and `hooks/` directories only if they end up empty. The deprecated `~/.kimi/` product paths and the Nexus-Hub-invented `.kimi/agent.yaml` companion remain unwritten, as they have been since the v3.15.0 Phase 4 migration.

### Copilot native instructions, agents, and hooks

Re-verified 2026-08-30 against GitHub's current [personal-instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions), [custom-agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/invoke-custom-agents), and [hooks](https://docs.github.com/en/copilot/reference/hooks-reference) documentation.

Copilot has native personal and repository surfaces, so the adapter no longer depends on Claude-owned files for coverage. Global installs marker-merge `~/.copilot/copilot-instructions.md`, copy catalog agents to `~/.copilot/agents/<name>.agent.md`, and write one owned version-1 hook definition at `~/.copilot/hooks/nexus-hub.json` with its scripts under the same directory. Workspace installs use `.github/copilot-instructions.md`, `.github/agents/<name>.agent.md`, and `.github/hooks/nexus-hub.json`. User-authored same-name files are preserved; structured or manifest ownership limits teardown to Nexus-Hub content.

The existing VS Code user-profile prompt export remains a compatibility command surface. The `NEXUS_HUB_COPILOT_SKILLS` selector is also unchanged: it remains off by default, accepts a bundle id or `all`, and never overwrites a committed `.github/skills/` file.

### Hermes and the shared `.agents/skills/` path (v3.15.2 Phase 5)

Hermes is a skills-native agent: it discovers folder-per-skill `SKILL.md` directly and needs no instruction file. Its native roots are `~/.hermes/skills/` globally and `.hermes/skills/` per project. The shared `~/.agents/skills/` or `.agents/skills/` roots are **not automatic discovery paths**: the official [skills documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/) requires users to list them explicitly in `skills.external_dirs`. Nexus-Hub therefore writes only the native Hermes roots and makes no automatic shared-global coverage claim.

**Layout compatibility re-verified (v3.15.8 Phase 8).** The upstream skills doc states the discovery rule outright: "Hermes discovers skills by listing every subdirectory of the tap path and probing each for `SKILL.md`", each skill directory's name becomes its install slug, bundled `references/` / `templates/` / `scripts/` / `assets/` subdirectories ride along, and directories whose name starts with `.` or `_` are ignored. That settles the v3.15.2 ambiguity in the opposite direction from what a category-nested upstream *example* suggested: the flattened one-level layout Nexus-Hub already writes is **required**, not merely tolerated, because a category layer would put every `SKILL.md` at depth 2 where Hermes never probes. No migration was performed, and a regression test now asserts both halves -- every direct child of the skills root has a `SKILL.md`, and no `SKILL.md` exists below depth 1.

That test immediately earned its place by catching a pre-existing catalog defect: `catalog/skills/code-review/references/` held four checklist files at the *category* level, so `flatten_skills` presented `references` as a skill (with no `SKILL.md`) on every flattened platform, and the three sibling skills citing `references/<file>.md` had relative paths that did not resolve. The checklists were relocated into each citing skill's own `references/` directory per the per-skill bundling convention, and the category-level directory removed.

Wiring status: the `hermes` integration is registered in `_register_builtins()` and installs on demand via `scripts/lib/integrations/runner.py install --integrations hermes` (detection-gated on `~/.hermes` at global scope), consistent with the extended-platform tier (aider / windsurf / openclaw). It is intentionally NOT in the JSON `contract_checks` block or the installers' default `should_install` / `known_platform_keys` wiring yet; promoting Hermes to a first-class default-installed platform (with a `contract_checks` entry + installer `invoke_registry_platform` blocks) is a tracked follow-on (see the v3.15.2 known-gaps).

## Sources (corrected rows, verified 2026-08-30)

- Codex skills discovery, one-level-deep `SKILL.md`, the `.agents/skills` ladder, and `$name` invocation: <https://learn.chatgpt.com/docs/build-skills>
- Codex hooks, including enabled-by-default behavior and the `hooks = false` disable lever: <https://learn.chatgpt.com/docs/hooks>
- Codex custom prompts deprecated, `~/.codex/prompts/*.md` top-level only, `/prompts:name`: <https://learn.chatgpt.com/docs/custom-prompts>
- Codex AGENTS.md (`~/.codex/AGENTS.md` + repo root): <https://developers.openai.com/codex/guides/agents-md>
- New ChatGPT desktop app merges Chat + Work + Codex; skills work in the desktop app, CLI, and IDE extension: <https://openai.com/index/introducing-the-codex-app/>
- Antigravity agents and workspace root: <https://www.antigravity.google/docs/cli/commands/agents> and <https://antigravity.google/docs/cli/subagents/>
- Antigravity CLI modes and `agentMode`: <https://www.antigravity.google/docs/cli/modes/>
- Antigravity CLI settings file: <https://www.antigravity.google/docs/cli/settings>
- Antigravity hook input and decision schemas: <https://www.antigravity.google/docs/hooks/>
- Claude Code skills one level deep (`~/.claude/skills/<name>/SKILL.md`, "a directory that contains a SKILL.md file"): <https://code.claude.com/docs/en/skills>
- OpenCode skills one level deep; reads `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` (and `.opencode/skills`, `.claude/skills`, `.agents/skills` per project): <https://opencode.ai/docs/skills/>
- OpenCode workspace-root instruction discovery: <https://opencode.ai/docs/rules/>
- Gemini CLI skills one level deep; reads `~/.gemini/skills` and the `~/.agents/skills` alias: <https://geminicli.com/docs/cli/skills/>
- Gemini Code Assist `GEMINI.md` instruction hierarchy: <https://docs.cloud.google.com/gemini/docs/codeassist/use-agentic-chat-pair-programmer>
- Copilot personal instructions, agents, and native hooks: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions>, <https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/invoke-custom-agents>, and <https://docs.github.com/en/copilot/reference/hooks-reference>
- Cursor verified skills discovery: <https://cursor.com/docs/skills>
- Devin Desktop / Cascade rules, skills, workflows, and hooks: <https://docs.devin.ai/desktop/cascade/memories>, <https://docs.devin.ai/desktop/cascade/skills>, <https://docs.devin.ai/desktop/cascade/workflows>, and <https://docs.devin.ai/desktop/cascade/hooks>
- OpenClaw JSON5 configuration, path overrides, workspace precedence, skills, lifecycle hooks, and typed plugin hooks: <https://docs.openclaw.ai/configuration>, <https://docs.openclaw.ai/help/environment>, <https://docs.openclaw.ai/concepts/multi-agent>, <https://docs.openclaw.ai/agent-workspace>, <https://docs.openclaw.ai/skills>, <https://docs.openclaw.ai/automation/hooks>, and <https://docs.openclaw.ai/plugins/hooks>
- Hermes native skills and explicit `skills.external_dirs`: <https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/>

## Defects to resolve in this release (v3.12.0)

- **Codex flattening**: the installer copies `catalog/skills` verbatim to `~/.codex/skills`, preserving the `<category>/<name>/` tree, so skill folders sit two levels deep and Codex discovers none. Fix: `flatten_skills` to `~/.codex/skills` AND `~/.agents/skills` (Phase 2).
- **Codex commands invisible in the desktop app**: commands ship only as deprecated prompts (`/prompts:name`). Fix: also emit `commands_to_skills` so `$name` works, keep prompts for CLI back-compat (Phase 2).
- **Antigravity wrong global paths**: the installer writes global content to `~/.gemini/antigravity/`, which the IDE does not read. Fix: `~/.gemini/config/skills/`, `~/.gemini/config/global_workflows/`, `~/.gemini/GEMINI.md` (Phase 3).

## Residual live-verification gaps

The 2026-08-30 audit leaves only the following contract gaps open. They are deliberately excluded from MATCH claims and enforced install checks:

1. Antigravity CLI loose workflow, agent, and lifecycle-hook directories remain undocumented. Nexus-Hub emits only the verified CLI skills directory and shared instruction file.
2. Cursor legacy `.cursor/commands` discovery remains undocumented in the current official skills reference. Compatibility writes remain, while every command is also available through the verified command-skill path.
3. Gemini Code Assist documents the `GEMINI.md` instruction hierarchy, but IDE-specific skill, workflow, agent, rule-directory, and hook discovery remains UNVERIFIED.
4. OpenClaw native lifecycle hooks cannot intercept or deny tool calls. Tool-interception guardrail parity is **NOT COVERED**. Next step owner: platform integration maintainer, for a separately scoped typed plugin using the documented `api.on(...)` hook surface.
5. Nexus-AI remains UNVERIFIED because its source is private and no publicly auditable read contract exists.

## Platform coverage tiers (relocated from AGENTS.md, 2026-08-21)

Relocated verbatim from the `AGENTS.md` "Platform coverage caveats (current state)" subsection during the v3.18.0 AGENTS.md ratchet-down (MT-1). It is the narrative companion to the read/write surface table above: that table says *where* each platform reads from, this says *how much* of the catalog each one receives and why. `AGENTS.md` keeps a pointer here.

### Platform coverage caveats (current state)

> **Gemini CLI sunset**: per the 2026-05-21 Google Developers Blog announcement, Gemini CLI stops serving free / Google AI Pro / Ultra / GitHub-installed users on 2026-06-18. The standalone `gemini-cli` integration is now opt-in via the `--enterprise` installer flag (Bash: `scripts/installer.sh --enterprise`; PowerShell: `scripts/installer.ps1 -Enterprise`) and installs only when the user explicitly requests it. Non-enterprise users transition to Antigravity CLI, which is covered by the `antigravity2` integration (the desktop IDE and CLI share a backend per the same announcement; see [docs/archives/v2/v2.2/antigravity-cli-probe.md](../archives/v2/v2.2/antigravity-cli-probe.md)).

The installer uses platform-specific adapters, so coverage is surface-by-surface rather than one uniform file-tree promise:

- **Original 4**: Claude Code, Gemini/Antigravity 1.0, Codex, and GitHub Copilot. Each now installs through the integration registry. Copilot receives personal and repository instructions plus native agents and hooks; its hook adapter translates Claude-compatible handler output into Copilot's top-level `permissionDecision`, `permissionDecisionReason`, and `modifiedArgs` fields.

> **Correction (v3.16.0 Phase 3)**: this list previously described the Original 4 as installing via "legacy installer copy blocks" *instead of* the integration registry. That is no longer accurate and was corrected after being verified directly against both installers. **Every** platform is now invoked through the registry runner: `invoke_registry_platform` (bash) and `Invoke-RegistryPlatform` (PowerShell) each call `scripts/lib/integrations/runner.py install --integrations <key>`, at global and workspace scope, for all fourteen default-installed keys. What still differs is how much each call does: several platforms are invoked with `instruction_only`, so the registry renders only the marker-merged instruction file while the installer's own `safe_folder_copy` blocks handle the catalog tree (the DF-001 legacy-block replacement path). The practical consequence, and the reason this matters beyond bookkeeping: a hook added to `IntegrationBase` reaches **every** platform with no installer edit. That is what let v3.16.0 Phase 3 add install-time defaults seeding without touching either installer.
- **Extended 4 (v2.2.0+, via integration registry)**: Antigravity 2.0 + CLI (Google -- single integration covers both surfaces; the CLI ships as the `agy` binary and uses the `.agents/` per-project convention with global content under `~/.gemini/antigravity-cli/`, verified 2026-05-29 against Google's public Antigravity CLI docs), Antigravity CLI (Google -- transition target for Gemini CLI before 2026-06-18; covered by the `antigravity2` integration), Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18, opt-in via `--enterprise` installer flag), Nexus-AI (https://github.com/bendourthe/Nexus-AI).
- **User-global slash commands (v3.3.4)**: GitHub Copilot in VS Code uses the documented user-profile `prompts/<name>.prompt.md` surface. Cursor's legacy global and project `.cursor/commands/` writes are retained only for compatibility and remain UNVERIFIED against current official documentation; every catalog command is also emitted through Cursor's verified skills discovery path.
- **Antigravity 2.0 verified and compatibility surfaces**: Antigravity IDE reads global skills from `~/.gemini/config/skills/`, global agents from `~/.gemini/config/agents/`, shared instructions from `~/.gemini/GEMINI.md`, and workspace-root `AGENTS.md` plus `.agents/{skills,agents}`. The CLI reads `~/.gemini/antigravity-cli/skills` and its documented `agentMode` setting. Loose CLI workflow, agent, and lifecycle-hook directories remain UNVERIFIED; compatibility workflow writes are not evidence of native CLI discovery. Verified IDE `PreToolUse` guardrails run through the Antigravity compatibility bridge, which translates camelCase host input and returns the documented top-level decision schema.
- **Skills-bearing integrations (v3.15.0 platform parity)**: OpenCode, Qwen Code, and Kimi Code CLI now receive a flattened skills file-tree (and more), not just an instruction file. **OpenCode** (`~/.config/opencode/` global, `.opencode/` project): skills + commands + rules + agents (agents added v3.15.0 Phase 3); its `plugins/` hooks are a JS/TS Bun runtime, out of scope for Nexus-Hub's shell/py hooks (DF-4). **Qwen Code** (`~/.qwen/` global, detection-gated; `.qwen/` project): flattened skills + subagents + Markdown commands (TOML is deprecated in Qwen, so Markdown is used) + the `QWEN.md` instruction file (v3.15.0 Phase 4). **Kimi Code CLI** (`~/.kimi-code/` global, detection-gated; `.kimi-code/` project): flattened skills (each auto-registers as `/skill:<name>`; no separate command format) + `AGENTS.md` (v3.15.0 Phase 4 -- migrated from the older, separate "Kimi CLI" `~/.kimi/` product; that path and the invented `.kimi/agent.yaml` companion are dropped, and a user still on the old product no longer receives a surface). All three still embed the `{{SKILL_INDEX}}` block in their instruction file. (Qwen + Kimi were added v3.4.0 as guardrails-only via the `qwen` / `kimi` subclasses and reclassified in v3.15.0 Phase 4; OpenCode has installed skills/commands/rules since v3.12.0.)
- **Hermes (v3.15.2 Phase 5, registry-registered)**: `hermes` is a skills-native integration (`~/.hermes/skills/` global, detection-gated on `~/.hermes`; `.hermes/skills/` project) that discovers folder-per-skill `SKILL.md` directly and needs no instruction file. Shared `.agents/skills` directories are not automatic Hermes discovery surfaces; a user must name each shared directory explicitly in `skills.external_dirs`. Nexus-Hub therefore claims only the native `.hermes/skills` delivery by default.
- **Aider behavioral guardrails**: Aider receives project-root `CONVENTIONS.md`; it has no verified global instruction surface, so a global install is a no-op.
- **Devin Desktop / Cascade**: the `windsurf` adapter installs native user and workspace skills, workflows, rules, and hooks on the current `~/.codeium/windsurf/`, `.devin/`, and `.windsurf/` surfaces while retaining `.windsurfrules` compatibility. Hook merge and teardown ownership is limited to the generated `cascade-hook-compat.py` wrapper invocation, so unrelated user commands under the native hooks directory are preserved.
- **OpenClaw**: the adapter installs `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, and native `skills/<name>/SKILL.md` into OpenClaw's configured workspace, not a project-local `.openclaw/` pseudo-workspace. OpenClaw provides native lifecycle hooks, but Nexus-Hub installs none because those hooks cannot intercept tool calls; tool-interception guardrail parity remains NOT COVERED pending the separately scoped typed plugin named in the residual gaps.
- **Pi (v4.1.0, registry-registered, detection-gated)**: `pi` receives flattened skills (`~/.pi/agent/skills/` global, `.pi/skills/` project) plus one prompt template per catalog command (`~/.pi/agent/prompts/*.md` global, `.pi/prompts/*.md` project), which IS Pi's slash surface: the filename becomes `/name`. Pi implements the agentskills.io specification Nexus-Hub already conforms to, so no new emission format was needed. Only the GLOBAL instruction file `~/.pi/agent/AGENTS.md` is written: Pi reads project-root `AGENTS.md` from the working directory, and Codex already owns that file, so writing it twice would create two owners for zero added coverage. No agents folder and no Claude-style hook registry are documented, and `.pi/extensions/` is executable TypeScript that Nexus-Hub deliberately does not write into. **Trust caveat**: Pi loads project-local `.pi` resources only after the user trusts the folder, so workspace writes stay inert until they answer Pi's own prompt; the global surfaces are not trust-gated. Global scope is detection-gated on `~/.pi`.

> **Historical roster note (2026-07-08; superseded by the 2026-08-30 correction)**: the earlier audit retained Windsurf's compatibility surfaces and the legacy Kimi layout because current primary documentation was not then available. Do not use that dated finding as the current read contract; the current Devin Desktop / Cascade and Kimi Code CLI surfaces are stated above and in the 2026-08-30 re-verification log.

Each platform above has a corresponding `IntegrationBase` subclass under `scripts/lib/integrations/`, and all current installer paths invoke those registry adapters. Older references to the original four continuing through legacy-only copy blocks are historical and superseded.

If your change is a new slash command, call out in the CHANGELOG which platforms get a verified slash or command-skill surface. Cursor's global and project `.cursor/commands/` paths and Antigravity CLI loose workflow directories are compatibility writes with UNVERIFIED discovery; do not present them as confirmed command surfaces. OpenCode receives commands through its current adapter surfaces rather than only through an instruction-file body.

If broader per-file distribution to a new platform is needed, add a new subclass under `scripts/lib/integrations/` (not a new lock-step `base-*.md` template).
