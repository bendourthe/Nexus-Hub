# Decision: Install completion plugins by default on plugin-only platforms

Status: implemented - OpenCode, OpenClaw, Pi, and Hermes receive a small user-global completion plugin when the platform is detected, unless `NEXUS_HUB_COMPLETION_PLUGINS=0`.

## Problem

Nexus-Hub has so far refused to write executable plugin code (known gap DF-4, and the adapter docstrings in `opencode.py`, `openclaw.py`, and `pi.py`). Hooks on those four platforms are typed plugins in TypeScript or Python, not shell commands, so none of the catalog's hooks reached them.

The v4.13.2 completion gate needs a turn-end lever on every platform that has one. On these four, the only documented lever is a plugin event (`session.idle` with an SDK prompt on OpenCode, `before_agent_finalize` on OpenClaw, `agent_before_settle` on Pi, `pre_verify` on Hermes). Without a plugin, a full run on them continues only through the `nexus-hub run-plan` runner after each session ends.

## Decision

Nexus-Hub installs one thin plugin per detected platform, at user-global scope only, never in a project directory a repository controls. Each plugin does one thing: on the platform's turn-end event it runs the installed gate core (`~/.nexus-hub/scripts/completion_gate.py stop`) as an argument array with no shell, sends the payload on stdin, and asks for another turn only when the core says the run is incomplete. It uses no third-party package. It is manifest-owned, so uninstall and repair remove exactly what was installed. `NEXUS_HUB_COMPLETION_PLUGINS=0` opts out before install.

This was the user's resolved decision 11 for v4.13.2 (2026-09-24). A plugin whose lever is not VERIFIED at implementation time is not shipped; that platform relies on the runner and the gap is recorded.

## Alternatives considered

**Default-on with an opt-out (chosen).** Full runs keep going on these platforms without a setup step, which is the point of the plan. The cost is executable code in the user's config directory; it is bounded by being user-global, dependency-free, thin, and removable through the manifest.

**Opt-in.** Safer by default and consistent with DF-4. Most users would never enable it, so the full-by-default driver would still stall on these platforms, and the opt-in would need its own discovery surface. Rejected.

**Skip plugins and rely on the runner.** No executable code at all. The runner only acts after a session ends, so an agent that stops mid-plan in an interactive session is not continued. Kept as the fallback for any platform whose lever is unverified.

## Consequences

- DF-4's stance changes for this one purpose: executable plugins are allowed when they are thin wrappers over an installed Nexus-Hub script, user-global, and opt-out-able. Other hooks still do not reach these platforms through plugins.
- Plugin behavior depends on vendor APIs that are only partly documented (OpenCode's continuation is two documented primitives composed; Hermes' `pre_verify` fires only on code-editing turns). The runner remains the primary layer on both.
- The capability usage gate in the CHANGELOG entry states activation, validation, the opt-out, the authority boundary, and the documentation link.
