# v4.15.2 Distribution Handbook Review

This record covers the distribution handbook refresh for the Claude Code project instruction change in v4.15.2. The mapped code inputs `scripts/installer.sh`, `scripts/installer.ps1`, `scripts/lib/integrations/claude.py` and `scripts/lib/integrations/cursor.py` changed after the previous receipt.

## Content Review

Every existing claim was checked against the code at the reviewed revision and none became wrong:

- Installer to runner to adapter routing, the three delivery shapes and the skill-name rules are unchanged. The only installer edits are the version label and a workspace checklist row that accepts the shared project `AGENTS.md` (`scripts/installer.sh` and `scripts/installer.ps1`, `install_workspace`).
- Ownership and core-settings claims are unchanged; `claude.py` adds the instruction decision beside them without touching the recorded-defaults logic.

One topic was missing, so the handbook gained a chapter, "Claude Code project instructions", with its own slide. It states what the code does:

- `decide_instruction_path` in `scripts/lib/integrations/claude.py` selects `AGENTS.md` only for a known version at or above `FLOOR_GENERAL` (2.1.277), or `FLOOR_HOSTED` (2.1.281) on Bedrock, Vertex AI, Foundry, gateways and telemetry-off. An unknown version, unreadable settings, a disabled reader, a fallback-disabling `instructionFiles` value or a blocking CLAUDE.md keeps `CLAUDE.md`.
- `persist_decision` records the result in `.nexus-hub/claude-instruction-decision.json`; `_write_sidecar` writes Claude-only guidance to `.claude/rules/nexus-hub-claude.md` and `install_workspace` skips the project `CLAUDE.md` on that path.
- `IntegrationBase.teardown` in `scripts/lib/integrations/base.py` keeps the shared block while `other_consumers` reports another consumer.
- `NEXUS_HUB_CLAUDE_MIGRATE=1` runs `_migrate_project_claude_md`, which removes only the managed block and leaves a file with user text in place.
- `scripts/lib/integrations/cursor.py` now writes the shared project `AGENTS.md` through `write_shared_agents`; this is covered by the shared-file statement and needed no separate claim.

The chapter is a new slide, so `slide_budget` moved from 5 to 6; existing slide IDs and their saved themes are unchanged and the new slide is light.

## Build and Browser Review

The handbook was rebuilt with its mapped `build_presentation.py` command and passed the read-only `--check` command; see [distribution-handbook-build.json](distribution-handbook-build.json). `measure_handbook.py` measured all six chapters and six slides (240 states) on Chromium 156.0.8078.4 with the functional-verification detector: no errors, no detector findings, and passing no-JavaScript, print, reduced-motion and fullscreen-fallback checks. The report is [handbook-browser-distribution.json](handbook-browser-distribution.json). A capture of the new chapter in the reading view was inspected: the text and the three-step figure fit with no clipping or overlap.
