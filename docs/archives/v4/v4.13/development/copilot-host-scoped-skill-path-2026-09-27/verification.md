# Copilot host-scoped skill read-path qualification

This v4.13.3 follow-up qualifies the personal `~/.claude/skills` read-path fact for GitHub Copilot in VS Code without extending that claim to Copilot CLI or weakening the shared Skill-Index Pointer fallback. It addresses [WN-2](../../../../../releases/v4/v4.13/known-gaps.md) and does not perform a release-wide platform-contract re-verification.

## Evidence and boundary

- [VS Code's first-party Agent Skills page](https://code.visualstudio.com/docs/agent-customization/agent-skills) lists `~/.claude/skills/` among personal locations for Copilot in VS Code. The [Copilot CLI skill-location reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) lists `~/.copilot/skills/` and `~/.agents/skills/` as personal locations but omits `~/.claude/skills/`. The omission is not proof of rejection; CLI discovery at that path remains unverified.
- The machine-readable Copilot fact now carries `host: vscode` and a VS Code source. The shared `~/.copilot/copilot-instructions.md` output uses only unscoped VERIFIED paths for pointer eligibility; a host-only path cannot replace the full index for a CLI user. A host-specific caller can query the VS Code fact explicitly without changing the shared output.
- The contract validator rejects unsupported host labels. No installer line, installed user config, full-platform `last_verified`, or release freshness marker changed.

## Verification

- Baseline: the existing pointer and contract suites passed 39 tests before edits.
- Negative control: the new host-selection and invalid-host cases failed against the baseline for the expected missing API and missing validation; after implementation the focused set passed 8 tests.
- The full pointer and contract suites passed 42 tests. `python scripts/verify_platform_contracts.py --quiet` exited 0.
- A redirected-home runner install with only `~/.claude/skills` populated wrote the full skill index to Copilot's personal instruction file. The existing shared `~/.agents/skills` provider test still qualifies a pointer when that verified common path is populated.

Actual Copilot CLI discovery was not exercised. This is a contract and installer-behavior qualification for the current candidate, not a release-wide platform freshness stamp or a claim that the CLI rejects the VS Code-only path.
