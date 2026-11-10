# Settings 0.3.1 Delivery

This record covers the local correction to effort mapping, native Codex defaults, compatibility messages and the taskbar hover. It records installed behavior and the remaining native-client limits for maintainers reviewing Settings 0.3.1.

## Behavior

Nexus Ultra now enables Claude Ultracode with native `xhigh` effort and `ultracode: true`. Max remains native `max` with Ultracode off. Lower choices also disable Ultracode. Existing project mode keys synchronize when present. [Native consumer proof](settings-ultracode-proof.md) records bundled Claude 2.1.318 reporting `Ultracode on`, with no model turn or API charge.

Codex's bundled 0.164.0-alpha.11.1 app-server read the saved Medium value from the actual user configuration and workspace. Existing composer drafts hold their own model settings, and the installed webview caches user configuration. The Settings footer and hover offer New Codex agent through the public `chatgpt.newCodexPanel` command. In a real installed VS Code window, clicking the Settings footer action opened a new Codex panel showing `GPT-6.1 Sol Medium`, matching Nexus. Existing chats and drafts are preserved; this does not force their session settings to change. Max and Ultra retain the compatible Codex `xhigh` mapping because the shared CLI 0.136.0 does not accept raw `ultra`.

Unsupported Copilot effort is compatibility information, not a recurring synchronization failure. The bottom note lists automatic effort for Claude Code and Codex new agents, and manual effort for GitHub Copilot, native Cursor and native Antigravity agents. Real write failures still produce an actionable notice. The installed panel was observed without the old persistent warning, with the footer and native-agent action visible.

The compact native Markdown hover now contains an effort scale, a two-column effort and guardrail summary, named guardrail states and Settings/native-agent links. It uses native theme icons and no simulated form controls. Its contents and command allowlist passed the extension and installed-host tests; a pixel capture of the open native hover was not obtained.

## Verification

- Settings engine and catalog suite: 434 passed, three existing platform skips. Mapping coverage includes all six choices, drift repair, existing project keys, Ultracode toggling and reset.
- Extension suite: 307 passed, one existing skip; 98.61 percent line coverage and 91.22 percent branch coverage. Includes trust and capability checks, refused arbitrary commands, launch failure feedback, footer/action behavior and the real CLI agreement flow.
- Browser flow: seven persisted actions and six screenshots across 320, 420 and 900 pixels in dark and light themes, with no horizontal overflow or page errors. The flow exercises the real settings CLI and guardrail hook consumer.
- Packaged version 0.3.1 compiled successfully and passed the 19-file package check. VS Code, Cursor and Antigravity each passed actual trusted and untrusted installed-host checks.
- All three active editor registrations are version 0.3.1. Each of the 19 installed payload files matches the VSIX, excluding only the editor-added installation metadata in the manifest. VSIX SHA-256: `45c5351dccb0c91de621b11a0b519c73bf4b26faaa0c4ca3abf44375f6521c22`.
- Four changed settings-engine runtime files were backed up to `~/.nexus-hub/backups/settings-native-fix-20261105-0.3.1/`, delivered and verified against source. The installed engine reports Medium in effect for Nexus, Claude and Codex, with both native defaults matching. Existing guardrail choices were retained.

Reports are retained in the sibling `settings-native-fix-20261105-artifacts` directory. Browser output is under Documents `nx-settings-031-browser`; editor reports are under `nx-settings-031-code`, `nx-settings-031-cursor` and `nx-settings-031-antigravity`.

## Limits

Automatic effort for Copilot and native Cursor/Antigravity agents still requires a verified writable vendor control. Use their native effort pickers meanwhile. Existing conversations and drafts use native session controls. Guardrail enforcement continues through the installed platform hook adapters and the existing switches; this correction does not add a new native hook integration. Current editor windows that loaded 0.3.0 require one reload to activate the 0.3.1 UI; a separate real VS Code window has already activated and exercised 0.3.1. This is local delivery, with no remote publication or Nexus-Hub release claim.
