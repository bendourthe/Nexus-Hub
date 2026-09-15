# Decision: Portable user attribution

Status: implemented - Local implementation is complete; integration and release qualification are separate gates.

Use configured human Git identities for generated work on every supported local agent platform. This decision covers install-time Git hooks, existing-hook preservation, activation, rollback and the limits of local enforcement.

**Status**: Implemented; integration pending
**Date**: 2026-09-14
**Author**: Ben Dourthe
**Template**: Nygard

## Problem

Nexus-Hub's repository-specific history repair does not protect users installing the catalog on another machine. Its checker deliberately names one maintainer and is excluded from distribution.

Agents can add their own author identities or attribution trailers even when the user's Git configuration is correct. Shared instructions establish intent, but do not verify the metadata Git writes.

Users need the same normal-Git behavior across platforms without adopting the Nexus-Hub maintainer's identity. Existing hooks and legitimate human commit authors must survive installation. Installation must not rewrite project history or select an authentication account.

## Decision

Ship a separate standard-library Python guard and expose it through `nexus-hub attribution`. Both installers copy the helper and activate global hooks by default or repository hooks for workspace installs. Derive the identity from effective `user.name` and `user.email`; require valid human values and reject agent/bot identities, unexpected pending author/committer overrides and attribution trailers. Preserve human authors during supported replay operations. Validate outgoing commits and annotated tags before normal pushes. Provide a checked tag command because Git has no pre-tag hook.

Chain original hooks and retain their arguments, input and exit status. Preserve special hook absence when Git assigns meaning to presence. Worktree configuration requires activation at that scope. A non-Git workspace reports setup pending; missing identity installs a guard that blocks contributions until configured. A check reports active coverage or actionable failure. Rollback restores only the configuration still owned by Nexus-Hub and retains recovery files.

All instruction templates require user authorship, no agent footers, preflight verification and publication using the intended user's hosting account. Claude's documented empty attribution settings are seeded from the canonical platform-defaults source. Cursor's sessionStart context response loads the shared policy where no global instruction file exists. Aider's adapter seeds its documented attribution flags, Git verification and policy read list for both installation scopes. Existing conflicting user configuration is preserved and reported as NEEDS SETUP.

## Alternatives considered

| Option | Benefits | Costs and decision |
|---|---|---|
| Instructions and native settings only | Small, portable and easy to install | Agents can ignore instructions or emit unexpected trailers. Keep these as guidance, with Git checks providing enforcement. |
| A Git executable wrapper or per-agent shell parser | Could intercept tag creation and some commands before execution | Absolute Git paths, APIs and platform-specific execution paths bypass wrappers; replacing Git introduces broad compatibility risk. Rejected. |
| Shared Git hooks with explicit checked commands | Uses Git's normal commit and push boundaries across agent platforms; preserves existing hooks | Requires Python and Git, careful hook forwarding and clear bypass limits. Selected. |

## Consequences

Fresh default installations protect normal local Git commits and pushes independently of the agent. Configured identities stay user-specific. Existing repositories with overriding or special hooks may need workspace activation. Hooks add process overhead to Git operations, and outgoing history scans can take time on large first pushes.

Local hooks are not a security boundary against a user or agent with permission to disable them. Direct hosting API writes, cloud machines without installation, platform-generated merge metadata, hosting authentication and GitHub contributor caches remain outside this guard. Rules require verification before using those publication paths. No release may describe this as an unconditional guarantee against every possible execution path.

## Verification

Both installers deliver an active guard in a configured Git repository. Real commits and pushes reject agent identities and prohibited trailers, preserve existing hooks and human replay authors, and rollback restores the previous configuration. Installed instruction templates expose the check and recovery commands. Fresh local evidence and integration checks pass before release.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Existing hooks or configuration override activation | Medium | High | Check effective activation, preserve original hooks and provide workspace setup plus rollback. |
| New platform changes attribution defaults | Medium | Medium | Seed only documented levers, refresh source evidence and keep Git checks independent. |
| Old agent-authored history is pushed to a new remote | Medium | Medium | Reject with diagnostics; installation never rewrites or reattributes history automatically. |

Integration and release qualification remain pending. User operation details are in [the attribution guide](../../../guides/user-attribution.md).
