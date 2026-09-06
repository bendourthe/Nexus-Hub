# Integration Roster Verification - Windsurf and Kimi (2026-07-08)

**Cycle**: adoption-spec-kit Phase 3 (S4)
**Standard**: primary sources (vendor announcements, official docs, official blogs), matching the AGENTS.md Gemini-CLI-sunset evidence standard. Third-party changelogs are noted but not treated as authoritative.

## Windsurf

**Signal**: Was Windsurf absorbed into Cognition Devin, and is the standalone editor (its `.windsurfrules` project file and `~/.codeium/windsurf/memories/global_rules.md` global surface) discontinued?

**Primary evidence** - [Cognition blog: "Cognition's acquisition of Windsurf"](https://cognition.com/blog/windsurf), dated **2025-07-14**:

- Cognition acquired Windsurf (the agentic IDE, its IP, trademark, and team).
- Quoted: *"In the immediate term, the Windsurf team will continue to operate as they have been."*
- Quoted intent: *"Over the coming months, we'll be investing heavily in integrating Windsurf's capabilities and unique IP into Cognition's products."*
- The IDE is **preserved as a distinct product with its own brand** and user base at acquisition time.

**Third-party signal (NOT primary)**: multiple outlets (digitalapplied, aitooltier, medium, chatforest) report that on **2026-06-02** the Windsurf editor was silently rebranded to **"Devin Desktop"**, with existing accounts, plans, extensions, and keybindings preserved. No primary Cognition announcement of the rebrand was reachable for this note.

**Assessment**: the standalone editor **surface is still served** (whether branded Windsurf or Devin Desktop, the editor still loads its config; keybindings/extensions intact). The primary source confirms preservation as a distinct product, not discontinuation. The rebrand is credible but only third-party-confirmed.

**Recommended action**: **deprecate-with-note** (not delete). Add a dated note to `scripts/lib/integrations/windsurf.py` recording the acquisition and the third-party-reported Devin Desktop rebrand, keep the integration registered and its writes detection-gated (they already degrade gracefully on an absent platform), and add a dated caveat to AGENTS.md. Do NOT remove the integration - the surface still works for existing users, and deletion would be a user-breaking change unsupported by a primary discontinuation notice.

## Kimi

**Signal**: Has the Kimi CLI surface migrated to "Kimi Code CLI", and did its config conventions change from the `.kimi/system.md` + `.kimi/agent.yaml` layout `scripts/lib/integrations/kimi.py` writes?

**Primary evidence** - [Kimi Code CLI migration guide](https://www.kimi.com/code/docs/en/kimi-code-cli/guides/migration.html) and the [MoonshotAI/kimi-cli repository](https://github.com/MoonshotAI/kimi-cli):

- Kimi CLI was rebuilt as **Kimi Code CLI**: *"Rebuilt on Node.js - no Python environment needed"* (a full Python/uv -> TypeScript/Node.js rewrite, v0.1.0 in May 2026).
- Migration is **non-destructive to the legacy layout**: *"Migration never modifies or deletes any of the old data under `~/.kimi/`"* - the old and new installs **coexist**.
- Config carries over: *"Config, MCP servers, and session history all carry over seamlessly."* (OAuth credentials and plugins do not migrate.)
- The migration guide **does not detail a project-local layout change** away from the `.kimi/` conventions; it documents global config carry-over, not a break of the project-local `.kimi/system.md` + `.kimi/agent.yaml` files an external writer emits.

**Assessment**: the migration is real, but the legacy `~/.kimi/` layout is **explicitly preserved and coexists**, and no primary source confirms that the project-local `.kimi/system.md` + `.kimi/agent.yaml` output `kimi.py` writes is now rejected. The surface is still served.

**Recommended action**: **refresh-note** (not a layout rewrite). Add a dated note to `scripts/lib/integrations/kimi.py` and the AGENTS.md caveat recording the Kimi Code CLI migration and that the written `.kimi/` layout targets the legacy convention (preserved and coexisting per the vendor migration guide). Do NOT rewrite what `kimi.py` writes in this cycle: `scripts/lib/integrations/` is an "ask first" surface, the old layout is not confirmed broken, and a speculative rewrite risks breaking existing installs. Record the eventual Kimi-Code-CLI project-local convention refresh as a follow-up in `known-gaps.md` pending maintainer confirmation of the exact external-writer convention.

## Summary

| Platform | Signal confirmed? | Surface still served? | Action |
|---|---|---|---|
| Windsurf | Acquisition: yes (primary). Rebrand: third-party only. | Yes | Deprecate-with-note; keep registered; dated AGENTS.md caveat |
| Kimi | Migration to Kimi Code CLI: yes (primary). Layout break: not confirmed. | Yes (`~/.kimi/` preserved) | Refresh-note; no layout rewrite; follow-up deferred to known-gaps |
