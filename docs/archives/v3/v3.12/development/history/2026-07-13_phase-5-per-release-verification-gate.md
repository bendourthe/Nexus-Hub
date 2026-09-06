# Session History - v3.12.1 Phase 5: Per-release verification gate

**Date**: 2026-07-13
**Plan**: `docs/v3/v3.12/plans/v3.12.1-cross-platform-install-adapters.md`
**Phase**: 5 of 6 - Per-release verification gate
**Status**: Complete (stability gate PASS)

## Goal

Institutionalize three verification layers so future installs stay correct: a deterministic offline code-vs-contract checker (`make validate`), the corrected runtime install-vs-reality check (`nexus-hub verify`), and a per-release contract-vs-reality re-verification step in `/update release` (the user's core process request).

## What changed

### 5.1 - Deterministic code-vs-contract checker (`scripts/verify_platform_contracts.py`)

- New stdlib-only, offline checker. For each platform it asserts (a) the integration config declares the contract's paths, (b) skills flatten one level (via the `flatten_skills_layout` flag or the integration's own override), (c) the contract doc mentions the platform's read-paths, and (d) both installers reference the platform key. Exit 0 on agreement, 1 with a per-divergence report otherwise. Structured as a pure `check(doc, sh, ps)` core so tests can inject drift.
- Wired into `make validate` (after `check_base_template_parity.py`). NOT registered in the installers: it is a repo-internal guard (imports the integration registry, cannot run standalone), exactly like `check_version_sync.py` / `check_base_template_parity.py`. This deviates from the plan's 5.1 "register in installers" wording, which was wrong for a repo-internal guard.
- `tests/validators/test_verify_platform_contracts.py` (3 tests): passes on the real repo, flags an empty/drifted contract doc, flags a dropped installer key.

### 5.2 - Corrected the runtime read-path verifier (`runner.py` `_verify_checks`)

- Codex: now checks flattened `~/.codex/skills` + `~/.agents/skills`, legacy `~/.codex/prompts`, and the AGENTS.md SKILL_INDEX (label "Codex / ChatGPT").
- Antigravity: replaced the old `~/.gemini/antigravity/` checks with IDE global (`~/.gemini/config/skills`, `~/.gemini/config/global_workflows`, `~/.gemini/GEMINI.md`), CLI (`~/.gemini/antigravity-cli/skills`), and the project `.agents/` surface; detection keys off our real write targets.
- Updated `tests/installer/test_verify_read_paths.py`: rewrote the Antigravity test for the corrected IDE + CLI labels/paths (with a guard that the old `~/.gemini/antigravity` global label is gone) and added a Codex PASS/NEEDS-ACTION test.

### 5.3 - Per-release web-search re-verification step (`/update release`)

- New skill `catalog/skills/workflow/platform-contract-verification/SKILL.md`: for each platform in the contract doc, run targeted web searches for the CURRENT discovery format, diff against the doc, and on drift update the contract doc + adapter + both installers + CHANGELOG, then re-run `verify_platform_contracts.py`. It SELF-GATES to a repo shipping `docs/policy/platform-read-contracts.md` + `scripts/lib/integrations/` (Nexus-Hub) and is a silent no-op in any other project, so the distributed `/update release` flow stays generic. Degrades gracefully offline; no outbound dependency or credential.
- `catalog/commands/update.md`: added the skill as governance step 4 of the release scope, noting the self-gate.
- Registered the skill in `data/SKILL_INDEX.md`, `data/skills.json` (266 skills), and `data/marketplace.json` (workflow 42 -> 43) via targeted, format-preserving edits.

## The three verification layers (now complete)

1. **contract-vs-reality** (was missing): the `/update release` web-search step (5.3) keeps the contract doc true to each platform's current docs.
2. **install-vs-reality**: `nexus-hub verify` / `runner.py cmd_verify` (5.2), now checking the corrected paths.
3. **code-vs-contract**: `scripts/verify_platform_contracts.py` (5.1), run by `make validate`.

## Verification

- `python scripts/verify_platform_contracts.py`: OK (7 platforms match).
- `python -m pytest tests/installer/test_verify_read_paths.py tests/validators/test_verify_platform_contracts.py tests/validators/test_verify_install.py -q`: 30 passed.
- `python -m pytest tests/integrations/ -q` (full regression gate): 309 passed (unchanged from Phase 4; Phase 5 touched runner/scripts/skill, not integration behavior).
- `make validate` constituents: version-sync clean (3.11.3), base-template parity present, `validate_skills.py --bundles-only` PASS (266 skills), `--quality` PASS (0 errors), unicode-safety 0 errors, JSON integrity OK. (Full-mode `validate_skills.py` reports the pre-existing 250-char description-length flags on 164 skills including this one - the pushy-description convention; that mode is not part of `make validate`.)
- New skill frontmatter has name/description/summary_l0/overview_l1.

## Notes / follow-ups

- The self-gating skill means the generic distributed `/update release` gains the step harmlessly; only Nexus-Hub itself does the web-search work.
- Next: Phase 6 (architecture refactor + known-gaps reconciliation + CI/CD install-smoke update + full validation + release readiness handoff to `/update release`).
