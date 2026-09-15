# User Attribution

Nexus-Hub v4.12 adds user-attribution instructions and a local Git guard for supported agents. Use this guide when installing on a new machine, checking a repository, creating release tags or restoring previous hooks.

## Installation and verification

The default installer installs global Git hooks. Workspace installation activates the guard for that repository and preserves its existing hooks. Git and Python 3 must be available. Configure Git with your own name and an email associated with your hosting account; installation never copies the Nexus-Hub maintainer's identity.

From the repository, run:

```text
nexus-hub attribution check
```

`VERIFIED` means the installed hooks are active and the pending Git identity matches your configured human identity. `NEEDS SETUP` during installation means additional setup is required. A workspace without a Git repository needs `git init` before workspace activation. Missing or agent-like identity blocks contributions until corrected.

If a repository overrides global hooks or has a special existing hook that needs integration, run:

```text
nexus-hub attribution install --workspace
nexus-hub attribution check
```

Restart agent sessions after installation so they read the new instructions. The same rules ship to Claude, Codex, Cursor, Antigravity, Copilot and the other supported instruction templates. Claude's fresh settings disable commit and PR attribution; existing user settings retain the installer's normal preservation policy. Git checks independently reject prohibited metadata.

## Commits, tags and publication

New commits use effective Git `user.name` and `user.email`. Unexpected author or committer overrides, agent/bot identities and attribution trailers are rejected. Existing human authors are preserved during supported cherry-pick and rebase operations. This is attribution enforcement; it does not change the author of old work.

Create an annotated tag with the checked command. For example, when the requested release is `v1.0.0`:

```text
nexus-hub attribution tag v1.0.0 -m "Release v1.0.0"
```

Normal `git push` checks outgoing commit identities and messages plus annotated-tag identity and messages. An existing remote baseline must be available locally for verification. A first push checks reachable history, so old agent-authored commits may require a separately approved history decision. Never disable hooks to bypass a failure.

Human-authored history may retain GitHub's exact service committer, `GitHub <noreply@github.com>`, used for web operations. This exception never permits the service as an author and does not permit agent/bot authors.

Git author metadata and the authenticated publishing account are separate. Agents must check the intended account before pushing or creating a PR or release. On GitHub, `gh auth status` reports CLI authentication; an SSH remote can use a different account and must be checked separately.

## Platform delivery

Claude receives empty native commit and PR attribution defaults. Cursor's global and workspace `sessionStart` hook supplies the shared policy as additional context. Aider receives a policy `read` path, disabled author/committer/coauthor and message-attribution flags, and enabled Git commit verification. These defaults accompany the shared user-attribution section in all instruction templates.

Existing user settings are preserved. Aider reports NEEDS SETUP when its existing values conflict or its read list omits the policy; Cursor reports NEEDS SETUP when an existing hooks file is retained and needs verification. Resolve these messages before relying on platform instruction coverage. Project configuration or command-line options may override global defaults. The Git guard remains a separate check at local commit and push boundaries.

## Limits

Local Git hooks cannot prevent deliberate disabling, a changed executable, `--no-verify` push, direct hosting API writes or work on another machine without installation. Git has no pre-tag hook; the checked tag command prevents incorrect local tag creation, and pre-push rejects incorrect outgoing annotated tags. Platform-generated merge metadata and GitHub's contributor display cache remain controlled by the hosting platform. Instructions require verification before any publication path outside the local hooks; unsupported paths must not be represented as verified.

## Restore previous hooks

For a global installation:

```text
nexus-hub attribution uninstall
```

For a workspace installation:

```text
nexus-hub attribution uninstall --workspace
```

The command restores the prior `core.hooksPath` only if Nexus-Hub still owns that setting. It retains inert hook/state files for recovery. If another tool changed the setting, uninstall reports the conflict instead of overwriting the new configuration. Reinstall with the matching `install` command to enable the guard again.

Platform configuration is separate from this Git-guard rollback. Aider's shared `.aider.conf.yml` is retained even when its platform files are uninstalled. Workspace platform uninstall removes `CONVENTIONS.md`; remove its matching entry from Aider's retained `read` list. If removing the shared attribution guide too, remove that entry as well so Aider does not try to load deleted files. Keep unrelated read entries and personal settings.
