# Development Log: Skills-Craft and Prime Agent Phase 5 - Claude Plugin Marketplace

**Date**: 2026-08-24
**Operator**: Ben
**Assisted by**: Cursor Grok 4.6
**Objective**: Make `.claude-plugin/` strictly valid against the current Claude Code schema, decide skill exposure, draft the official-directory submission, and document the plugin as a subscribe-style alternative with the trailing-pin caveat.
**Outcome**: `claude plugin validate . --strict` passes. Full catalog is exposed via 23 category paths. Submission draft is ready. External form not sent. Ready for Phase 6.

---

## 1. Starting State

- **Branch**: `feat/v3.20.3-skills-craft-and-prime-agent`
- **Starting tag/commit**: `4383ed9b` (Phase 4 invocation policy)
- **Environment**: Windows 11, PowerShell, Claude Code CLI 2.1.156
- **Prior session reference**: [`2026-08-24_skills-craft-phase-4-invocation-policy.md`](2026-08-24_skills-craft-phase-4-invocation-policy.md)
- **Plan reference**: [`docs/releases/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md`](../../plans/v3.20.3-skills-craft-and-prime-agent.md)

Context: Phase 4 shipped command-skill invocation policy. Phase 5 is the vendor-intrinsic marketplace listing (A7). Plan recommended standard/medium; this session stayed on Grok 4.6 (frontier). No downshift.

---

## 2. Chronological Steps

### 2.1 Audit manifests and skill-exposure decision (5.1)

**Plan specification**: Audit plugin.json and marketplace.json against current schema; version-sync already covers plugin.json; decide full catalog vs bundle; validate --strict; draft submission; README trailing-pin; do not open the external PR.

**What happened**: Pre-change `claude plugin validate . --strict` failed: marketplace.json was a leftover v2 stats blob (`displayName`, `stats`, `install`) with no `owner` or `plugins`. Rewrote it to the 2026 marketplace schema. Rewrote plugin.json component paths: `commands` from the missing `./.claude/commands` to `./catalog/commands`; `skills` from the nested `./catalog/skills` (one-level scan would miss every skill) to the 23 category directories; added `./catalog/agents`. Omitted marketplace `version` so plugin.json remains the only pin.

Skill exposure: **full catalog**. Bundles stay an installer selector. Hooks and MCP stay off the plugin.

Live Anthropic process is the [plugin directory submission form](https://clau.de/plugin-directory-submission). In-app submit forms go to the community marketplace, not official. Documented; did not send.

**Key files changed**: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/v3/v3.20/development/claude-marketplace-submission.md`, `README.md`, `AGENTS.md`

---

### 2.2 Testing and stabilization (5.2)

**Plan specification**: validate --strict, make validate/lint/test, session history.

**What happened**: Vendor CLI is not a CI dependency. Added `tests/validators/test_claude_plugin_manifests.py` so ubuntu `tests` and `tests-windows` (already run `tests/validators`) prove schema shape and category-path parity without `claude`.

**Key files changed**: `tests/validators/test_claude_plugin_manifests.py`

---

## 3. Verification Gate

| Check | Result |
|---|---|
| `claude plugin validate . --strict` | PASS (Claude Code 2.1.156) |
| `python scripts/check_version_sync.py` | run at commit time (plugin.json still 3.20.2) |
| pytest `test_claude_plugin_manifests.py` | run at commit time |
| Unicode `--strict` on Phase 5 Markdown | run at commit time |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| Official directory listing not submitted | P2 | Deferred as DF-2. Maintainer sends the form. |
| Plan named a PR to claude-plugins-official | P2 | Documented. Live process is the form. |
| README headline counts still say 321 | P2 | Left for `/update release` docs scope. plugin.json description says 324. |

---

## 5. Plan Discrepancies

- Submission artifact lives at `docs/v3/v3.20/development/` not `docs/v3/v3.17/`.
- Did not open a PR. Did not submit the form.
- Did not extend `check_version_sync.py`: plugin.json was already canonical; marketplace.json carries no version.
- Did not add `claude plugin validate` to CI (Claude CLI is not installed on runners). Structural pytest is the gate.

---

## 6. Assumptions Made

- **One-level skill scan**: listing `./catalog/skills` would not recurse into categories. If Claude later recurses, the explicit category list remains valid.
- **`source: "./"` marketplace-root exception**: plugin.json `skills` subdirectories replace the default `skills/` scan. There is no top-level `skills/` directory, so that is what we want.

---

## 7. Testing Summary

### Automated Tests

- `claude plugin validate . --strict`: passed.
- New validator tests: run before commit.

### Manual Testing Performed

- Compared official plugins-reference path rules against nested `catalog/skills/<category>/<name>/SKILL.md`.

### Manual Testing Still Needed

- [ ] Maintainer submits the form and confirms the official install line.
- [ ] A Claude Code user adds `bendourthe/Nexus-Hub` and installs `nexus-hub@nexus-hub` after this branch is on a reachable ref.

---

## 8. TODO Tracker

### Completed This Session

- [x] 5.1 Manifests, exposure decision, validate --strict, submission draft, README caveat
- [x] 5.2 Structural tests, session history

### Remaining (Not Started or Partially Done)

- [ ] Phase 6: refactor, known-gaps, CI/CD, then commit and push
- [ ] `/update release` when CI is green

### Out of Scope (Deferred)

- [ ] Sending https://clau.de/plugin-directory-submission (DF-2)
- [ ] Opening a PR on anthropics/claude-plugins-official

---

## 9. Summary and Next Steps

The Claude Code plugin path is schema-valid and documents itself as a subscribe alternative with a SHA-lag warning. The full catalog is listed per category. Hooks stay on the installer. The maintainer still has to send the form.

**Next session should**:
1. Implement Phase 6 (refactor, known-gaps, CI), commit, and push.
2. When CI is green, run `/update release`.
