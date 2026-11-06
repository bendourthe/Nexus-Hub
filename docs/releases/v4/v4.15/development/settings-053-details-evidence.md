# Nexus Hub 0.5.3 Details Evidence

This record covers the 2026-11-05 Settings notes cleanup, Refresh explanation and outstanding Cursor report. Read it to distinguish the completed UI delivery from unresolved Cursor live synchronization.

## Changes

Behavior, guardrail coverage and native-provider compatibility notes now live inside a collapsed Details element below the effort selector. Version contains only its heading, installed version and upgrade action. The Nexus Hub header no longer has a subtitle. Manual Refresh moved into Details with an explanation: it rereads settings and retries synchronization after external changes. File watchers normally perform this automatically. Read failures and empty reports retain an accessible Refresh action. Expansion state and keyboard focus survive ordinary panel readback.

## Verification

Panel and manifest checks passed 45 tests across two files. The new interaction case verifies default collapse, preserved expansion after readback, Refresh behavior and the clean header/version content. The genuine private VS Code host displayed the collapsed panel, expanded Details, the moved notes and Refresh button. Clicking Refresh completed without losing expansion, and Details collapsed again afterward. No effort level or guardrail switch was clicked. The user's current Extra high preference was observed and was not restored to an earlier baseline.

TypeScript compilation and package verification passed. Official CLIs registered nexus-hub.nexus-hub-settings@0.5.3 in VS Code, Cursor and Antigravity. All 27 payload files matched each installed copy, allowing installer metadata in package.json. All 17 compiled runtime files matched 0.5.2 byte for byte. No pipeline file or native vendor adapter changed. Working editor windows were preserved; they require a reload to display this presentation update.

## Cursor Report

The user's report says Cursor live effort does not update, but does not identify the session provider. An asynchronous question asks whether it is Cursor's built-in Agent, hosted Claude Code/Codex, or both. That answer is pending. No Cursor live-update fix is claimed by 0.5.3.

Current source confirms installNativeUi registers only anthropic.claude-code and openai.chatgpt. There is no Cursor native-agent adapter. The installed Cursor 3.29.9 workbench has internal modelConfigService and per-composer setters; its existing switch-to-model command changes the composer default and selected composer. Read-only inspection did not establish a suitable external all-session setter or qualified effort-value mapping. A targeted read-only check of model-catalog state found no usable catalog entry in the inspected global database. No Cursor application files, user settings or conversations were changed. If the report concerns hosted extensions instead, their installed versions, adapter receipts and current loaded APIs still need a targeted investigation.

## Artifacts

Local artifacts are under C:/Users/BEDOURTHE/Documents/nx-ui053-qualification. install.json records registrations and delivery-verified.json records payload verification. The VSIX SHA256 is 614e94bdd4b2eb938069db888d11bdcebece10f2afd4e1f4a18a7120c97e768e. Additional native-provider support retains the [0.5.1 investigation limits](settings-051-panel-and-platform-evidence.md).
