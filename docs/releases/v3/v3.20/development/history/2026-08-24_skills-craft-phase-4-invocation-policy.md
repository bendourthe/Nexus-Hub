# Development Log: Skills-Craft and Prime Agent Phase 4 - Invocation Policy

**Date**: 2026-08-24
**Operator**: Ben
**Assisted by**: Cursor Grok 4.6
**Objective**: Command-derived skills carry `disable-model-invocation: true` at emission time, with a documented convention, a validator warning, per-platform native mapping only where vendor docs exist, and tests on POSIX and Windows.
**Outcome**: Shared `_synthesize_skill` emits the flag. Codex sidecar mapping now runs after command-skill synthesis. Validator warns on a `Run the /X command` catalog skill without the flag. Ready for Phase 5.

---

## 1. Starting State

- **Branch**: `feat/v3.20.3-skills-craft-and-prime-agent`
- **Starting tag/commit**: `97c97ee9` (Phase 3 loop disciplines)
- **Environment**: Windows 11, PowerShell, Python 3 (no `make`; OneDrive host)
- **Prior session reference**: [`2026-08-24_skills-craft-phase-3-loop-disciplines.md`](2026-08-24_skills-craft-phase-3-loop-disciplines.md)
- **Plan reference**: [`docs/releases/v3/v3.20/plans/v3.20.3-skills-craft-and-prime-agent.md`](../../plans/v3.20.3-skills-craft-and-prime-agent.md)

Context: Phases 1-3 landed catalog skills and loop-discipline enrichments. Phase 4 is the cross-cutting installer/emission build. Plan recommended frontier/high; this Cursor session stayed on Grok 4.6 (frontier). No downshift. The user authorized installer-scope work in the original implement request.

---

## 2. Chronological Steps

### 2.1 Define the invocation-policy convention (4.1)

**Plan specification**: Document user-invoked vs model-invoked in AGENTS.md and the read-contracts. Research each platform's current lever. Do not invent a surface.

**What happened**: Combined 4.1 with 4.2 in one pass (the convention is the emission contract). New AGENTS.md section `Command-derived skills and invocation policy`: default model-invoked; command-skills user-invoked; routing invariant (user-invoked may delegate to model-invoked, never to another user-invoked). Per-platform do-not-invent note.

Vendor re-check 2026-08-24:

- Claude: still documents `disable-model-invocation` (code.claude.com/docs/en/skills).
- Cursor: still documents it (cursor.com/docs/skills); no `user-invocable`.
- Qwen: both fields (page last updated 2026-08-07).
- Codex learn.chatgpt.com timed out; 2026-08-18 survey retained (`policy.allow_implicit_invocation` inverted sidecar).
- Antigravity, OpenCode, Kimi, Hermes, Nexus-AI: none documented; field emitted and ignored.

Did not add invocation keys to `platform-read-contracts.json`. That file's schema is consumed by discovery-path guards (`verify_platform_contracts.py`). Invocation lives in `skill-invocation-policy-levers.md`. The human-readable contracts file gained an `Invocation-policy emission (v3.20.3)` table. Did not re-stamp `meta.verified_for_version` (still 3.20.2 until `/update release`).

**Key files changed**: `AGENTS.md`, `docs/policy/platform-read-contracts.md`, `docs/policy/skill-invocation-policy-levers.md`, `.cursor/rules/nexus-hub.mdc`

---

### 2.2 Implement emission and validation (4.2)

**Plan specification**: Emit the flag wherever a command becomes a skill. Native equivalent only where SUPPORTED. Validator warning for `Run the /X command` without the flag. Tests under the existing layout.

**What happened**: Emission lives in shared Python `scripts/lib/integrations/_catalog_adapters.py` `_synthesize_skill`. Neither installer copies a second synthesizer; no `.sh` / `.ps1` copy-step edit.

Critical order fix in `scripts/lib/integrations/codex.py`: `codex_invocation_policy` previously ran before `commands_to_skills`, so generated flags never got a sidecar. Order is now flatten -> `commands_to_skills` -> `codex_invocation_policy`. Catalog skills still emit no sidecar unless they declare the field (`test_the_shipped_catalog_declares_no_manual_only_skill` still asserts the catalog has none).

`validate_skills.py` gained `warn_slash_dispatcher_without_policy()`: warning, not error, when description matches `^Run the /[A-Za-z0-9][A-Za-z0-9_-]* command\b` and `disable-model-invocation` is not `true`. Printed only with `--verbose`.

**Key files changed**: `scripts/lib/integrations/_catalog_adapters.py`, `scripts/lib/integrations/codex.py`, `scripts/validate_skills.py`

**Troubleshooting**:
- **Problem**: Codex command-skills would have shipped the SKILL.md flag with no `agents/openai.yaml` sidecar.
- **Root cause**: sidecar pass walked the tree before synthesis wrote the files.
- **Resolution**: move `codex_invocation_policy` after `commands_to_skills`.

---

### 2.3 Testing, CI, and dry-run (4.3)

**Plan specification**: `make validate` / `make lint` / `make test`, dry-run install, Windows leg coverage, contract freshness, session history.

**What happened**: This host has no `make`. Ran the Python equivalents. Integration installs into pytest `tmp_path` were the dry-run (Cursor, Codex, Antigravity, Kimi, Qwen, Hermes, cross-platform flatten). A second cheap dry-run synthesized `/implement` via `_synthesize_skill` and confirmed `loop-engineering` has no flag.

Added a Windows CI step for the tiny-fixture tests (`test_catalog_adapters.py`, `test_codex_invocation_policy.py`). The full 324-skill flatten suite stays on ubuntu `tests` (same cost-control as the existing native-only Windows steps). `tests/validators` already ran on Windows, so the new warning tests ride that job.

**Key files changed**: emission and validator tests listed in section 7; `.github/workflows/ci.yml`

---

## 3. Verification Gate

| Check | Result |
|---|---|
| `python scripts/validate_skills.py --bundles-only` | PASS (0 errors, 65 warnings) |
| `python scripts/check_agentskills_conformance.py` | PASS |
| `python scripts/check_platform_contract_freshness.py` | OK: verified for v3.20.2 |
| pytest invocation-policy + emission suite (9 files) | 107 passed in 366.59s |
| Cheap `_synthesize_skill` dry-run (`implement` vs `loop-engineering`) | PASS |
| Unicode `--strict` on Phase 4 Markdown | run at commit time |
| `python scripts/run_trigger_evals.py --gate` | NOT RUN this phase (no catalog skill body/frontmatter change) |
| Full-tree personal-paths scan | NOT RUN (WN-3; scoped paths only) |
| `make lint` | NOT RUN (no new `.sh` files) |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| Antigravity, OpenCode, Kimi, Hermes, Nexus-AI ignore the SKILL.md field | P2 | Accepted and recorded as DF-1. No invented mapping. |
| Codex learn.chatgpt.com timed out this cycle | P2 | Accepted as WN-6. 2026-08-18 survey retained. |
| Full flatten suite not on `tests-windows` | P2 | Accepted. Tiny-fixture emission tests added instead; ubuntu `tests` keeps the flatten suite. |
| Pytest hung on OneDrive tmp teardown after 107 passed | Cosmetic | Killed the process. Results were already printed. |

---

## 5. Plan Discrepancies

- Combined 4.1 (docs only) and 4.2 (code) in one pass. The convention is the emission contract; splitting would have left a docs-only commit with no proof.
- Did not write invocation keys into `platform-read-contracts.json`. Discovery-path guards consume that schema; the living lever survey is `skill-invocation-policy-levers.md`.
- Did not re-stamp `meta.verified_for_version`. Freshness still matches plugin.json 3.20.2; `/update release` owns the re-stamp.
- Plan path still cites `docs/v3/v3.17/`; live path is `docs/v3/v3.20/`.
- Installer `.sh` / `.ps1` copy steps were not needed. Emission is shared Python.

---

## 6. Assumptions Made

- **Shared Python is both installers' emission path**: confirmed by tracing `commands_to_skills` from `_catalog_adapters.py` into Claude, Cursor, Codex, Antigravity, Kimi, Qwen, OpenCode, Hermes, Nexus-AI. If a future installer grew a second synthesizer, it would need the same flag.
- **Ignoring an unknown frontmatter key is safe**: platforms with no lever drop the field. Inventing a second file for them is the v3.15.0 `.kimi/agent.yaml` failure class.
- **Catalog skills stay model-invoked**: `test_the_shipped_catalog_declares_no_manual_only_skill` must remain green.

---

## 7. Testing Summary

### Automated Tests

- `tests/validators/test_invocation_policy.py` plus eight integration files: 107 passed, 0 failed.
- `validate_skills.py --bundles-only`: PASS.
- `check_platform_contract_freshness.py`: OK for v3.20.2.

### Manual Testing Performed

- Synthesized `catalog/commands/implement.md` through `_synthesize_skill`. Frontmatter carries `disable-model-invocation: true`.
- Confirmed `catalog/skills/workflow/loop-engineering/SKILL.md` does not declare the flag.

### Manual Testing Still Needed

- [ ] Maintainer dry-run of `scripts/installer.sh` / `scripts/installer.ps1` on a non-OneDrive host (CI `install-smoke` covers this).

---

## 8. TODO Tracker

### Completed This Session

- [x] 4.1 Document the convention and per-platform support
- [x] 4.2 Emit the flag; Codex sidecar after synthesis; validator warning
- [x] 4.3 Tests, Windows CI step, dry-run inspection, session history

### Remaining (Not Started or Partially Done)

- [ ] Phase 5: official Claude plugin marketplace listing (A7)
- [ ] Phase 6: refactor, known-gaps, CI/CD, then `/update release`

### Out of Scope (Deferred)

- [ ] Native invocation mapping for platforms with no vendor lever (DF-1)
- [ ] Opening the anthropics/claude-plugins-official PR (Phase 5: maintainer-only)

---

## 9. Summary and Next Steps

Phase 4 makes slash-command bodies user-invoked at emission time. Claude, Cursor, Copilot, and Qwen honor `disable-model-invocation`. Codex gets the inverted sidecar after synthesis. Everyone else receives the field and ignores it. Catalog skills are unchanged.

**Next session should**:
1. Implement Phase 5 (plugin validate, submission draft, README trailing-pin caveat). Do not open the external PR.
2. Implement Phase 6 (refactor, known-gaps, CI), commit, and push.
3. When CI is green, run `/update release`.
