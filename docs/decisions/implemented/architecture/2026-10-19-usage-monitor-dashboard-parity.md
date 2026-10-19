# Decision: Usage monitor dashboards share one layout and default to compact mode

Status: implemented - Claude shows a Limit Resets row that claims no count, Codex, Copilot, and Cursor show Current Model (Copilot and Cursor through one approved read-only state-database key), and all five monitors start in compact status-bar mode

## Problem

The five usage monitors (Claude, Codex, Copilot, Cursor, Antigravity) had drifted apart. The Codex dashboard showed a "Plan" section holding the account tier ("Self Serve Business Prolite"), which tells a user nothing they can act on, while the Claude dashboard showed the current model, which explains its own recommendation ("switch to Sonnet"). The Claude dashboard showed nothing about one-time limit resets even though the claude.ai usage page has a "Limit resets" section, because the v4.13.7 decision ([`v4.13.7-decisions.md`](../../../archives/v4/v4.13/development/v4.13.7-decisions.md), "Usage-limit resets" item 2) chose to render nothing when the usage API serves no reset field. Every monitor also started with the full "X Usage: " status-bar label, which the maintainer runs compact on every host.

A second live read of `api.anthropic.com/api/oauth/usage` on 2026-10-19 (one GET with the maintainer's own credential, redacted to key paths and types) again served no reset count. It added the codenamed keys `granite_teacup` and `starry_waterfall`, both `null` on an account with no reset, and a `weekly_scoped_shares` list. None can be read as a reset count without guessing.

## Decision

- The Claude dashboard renders a **Limit Resets** row in the Codex row's position. It reads "Not reported by the Claude usage API" and never "available" or "none". Its **Open reset page** button sends the existing `openUsagePage` command, so the extension's request and URL surface is unchanged. This supersedes item (3)'s "Claude shows nothing"; item (2)'s finding (the endpoint serves no count) still holds.
- The Codex dashboard replaces **Plan** with **Current Model**: the top-level `model` key of the `config.toml` beside the resolved credential file (so `codexUsage.authPath` and `CODEX_HOME` are honored), read on each refresh, else "Codex default". The id is shown as Codex itself shows it (`gpt-6.1-sol`). The plan label stays in the data model, unrendered.
- The Copilot dashboard drops the **Plan** line and shows **Current Model** after the divider: VS Code's `chat.currentLanguageModel.panel` key (value `copilot/claude-opus-5.5` on the maintainer's install; the `copilot/` prefix is dropped), read read-only from the `state.vscdb` beside the extension's own global storage folder after each successful fetch. The maintainer approved this on 2026-10-19 as the single exception to Copilot decision (1b)'s no-file-read rule; `src/currentModel.ts` is the only file allowed to open the database, and a test pins its one key.
- The Cursor dashboard gains **Current Model**: `aiSettings.modelConfig.composer.modelName` from Cursor's settings record (`grok-4.7` on the maintainer's install), read by a separate one-key reader after each successful live fetch, so it inherits live-access consent. The session adapter's single-key allowlist is unchanged. The consent disclosure names the new read and `CONSENT_SCOPE` moves to `v2`, so a stored grant from the narrower disclosure is asked again rather than silently extended; the privacy boundary test now allows exactly this third state-database reader.
- Compact status-bar mode is the default on all five. Claude, Codex, Copilot, and Antigravity default `compactStatusBar` to `true`. Cursor defaults `showStatusBarLabel` to `false`, because its dashboard "compact" toggle maps to that key; Cursor's `compactStatusBar` additionally abbreviates the pools to C/O and forces the label off, so defaulting it on would leave the dashboard toggle unable to bring the label back.

## Alternatives considered

**Map a null codenamed key to a reset count for Claude.** Rejected: the keys are undocumented and were null on an account with no reset, so any mapping is a guess, which item (2) of the v4.13.7 record already forbids.

**Keep showing nothing for Claude.** Rejected: the maintainer reads the missing row as a missing feature, and the claude.ai page does carry the information, so the row's job is to say where it is.

**Show Current Model on Antigravity too.** Deferred. Antigravity stores only an opaque enum (`last_selected_agent_model: MODEL_PLACEHOLDER_M133` in `~/.gemini/antigravity/antigravity_state.pbtxt`), and no captured `GetUserStatus` response shows how to map it to a model name, so any label would be a guess.

**Keep Copilot's no-file-read rule absolute and show no model there.** Rejected by the maintainer on 2026-10-19: the one key carries no identity data, which is what decision (1b) protects, and the model explains the dashboard's advice.

**Read Cursor's model inside the session adapter.** Rejected: it would widen the reviewed single-key allowlist that guards the credential read; a separate reader keeps the token path unchanged.

**Default Cursor's `compactStatusBar` to `true`.** Rejected for the reason in the Decision: it forces the label off regardless of the dashboard toggle.

## Consequences

- A user who explicitly set a compact or label key keeps that value; only users with no setting see the new default.
- The Claude row cannot tell a user whether they hold a reset; they still check claude.ai. If Anthropic adds a reset count to the usage response, this row is where it belongs.
- The Codex model reflects the persisted picker choice, not a model chosen for a single session without saving, and it updates on the next refresh rather than instantly.
- Cursor users who had allowed live usage see the consent prompt once more, with the model read listed.
- Copilot and Cursor hide Current Model when the key is absent or unreadable (for example Copilot running inside Cursor, or a host without `node:sqlite`); the read never blocks or fails a refresh.
- Antigravity still shows **Plan** until its model mapping can be verified.
