# v4.15.9 Phase 1 (reduced): living agent classification

Started 2026-11-17T23:51Z. Worktree `v4.15.9` under the centralized worktree root, base `4d6316cc0`.

## Done

- T001: `docs/reference/agent-classification.md` created from the archived v4.14 rationale, with new "Fast-tier agents" (empty) and "Effort" sections. The Effort section states the D1 decision and that the declaration is not yet applied.
- T002: `tests/validators/test_agent_model_pinning.py` now reads the living file, the duplicated archive fallback is removed, and the unpinned section ends at "Fast-tier agents".

## Deferred (after v4.15.5 merges)

T003 to T008. Adding `effort: high` without the shared Claude-only key list would leak the key to platforms that do not read it. Listed in the lane delta file.

## Verification

- `pytest tests/validators/test_agent_model_pinning.py`: 2 passed. With the `planner` row removed the roster test fails; the row was restored.
- `python scripts/ci/run.py --profile fast --quiet`: 18 passed, 0 failed.
- Verification Expectation (fresh install showing `effort: high`) is not exercisable until T003 lands.

## CI impact

No new commands, dependencies, or test paths.

## Completion pass (2026-11-21)

v4.15.5 shipped, so the deferred tasks ran on a branch refreshed from `origin/develop` at `b3c678a95` (merge `af448b52a`).

- T003: `effort: high` added after `model: opus` in all 23 opus agents. `log-reader` (haiku) declares none; its fast-tier row records why.
- T004: dated subagent-effort paragraph added under `### claude - VERIFIED` in `docs/policy/platform-defaults-levers.md`. The fetched sub-agents page matched every statement the plan expected (options, session fallback, precedence), so nothing stopped the task. Effort is model-gated; Haiku 5.5 is listed.
- T005: `CLAUDE_ONLY_AGENT_KEYS = ("model", "effort")` in `_catalog_adapters.py`, used at the base mirror, Cursor, Copilot, and Antigravity sites. Codex is unchanged (its TOML renderer names its fields).
- T006: Kimi strips `effort` (`KIMI_DROPPED_AGENT_KEYS`) and keeps `model`; the fetched Kimi agents page documents neither and says Claude Code's `model` and unknown fields are ignored. Decision and URL in the classification file.
- T007: the delivery test roster is derived from the registry (declared `agents_subdir` or an `_install_agents` method), adding `kimi` and `nexus-ai`; the probe carries both keys.
- T008: `tests/validators/test_agent_effort_ceiling.py` added.

## Plan delta

No delta. Evidence: both vendor pages matched the plan's assumptions; the only adjustment was the roster rule, since Kimi delivers agents through `_install_agents` without declaring `agents_subdir`. Consequence for remaining phases: none.

## Verification (completion pass)

- `pytest tests/validators/test_agent_effort_ceiling.py tests/validators/test_agent_model_pinning.py tests/integrations/test_agent_model_delivery.py`: all passed (25 delivery cases). Probe: reverting the Copilot site to `("model",)` failed 2 cases; restored. The ceiling test fails naming `security-reviewer` when its `effort:` is removed or set to `max`.
- `python -B scripts/ci/run.py --profile fast --quiet`: 18 passed, 0 failed.
- Verification Expectation, real catalog installed into a throwaway home: Claude `doc-updater.md` shows `model: opus` and `effort: high`; Kimi shows `model: opus` only (recorded decision); Antigravity 2.0, Codex (TOML), Copilot, Cursor, Gemini, Gemini CLI, Nexus-AI, OpenCode, and Qwen show neither key.
- Known open failure: `test_claude_plugin_manifests.py` until Phase 2's T012 lists `log-reader`.

## CI impact (completion pass)

New test path `tests/validators/test_agent_effort_ceiling.py`; no new command, dependency, or environment variable. The existing `tests/validators` quarter for `test_a*` to `test_c*` in `scripts/ci/profiles.py` already collects it, so the pipeline needs no change.
