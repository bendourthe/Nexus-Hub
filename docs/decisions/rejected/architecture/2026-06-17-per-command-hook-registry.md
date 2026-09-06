# Decision: Adopt a Spec Kit-style per-command `before_` / `after_` hook registry

Status: rejected - it presupposes a third-party extension runtime that Nexus-Hub declined; the same need is met by matcher-keyed events on the existing surface

## Problem

Workflow commands (`/plan`, `/implement`, `/spec`) have phase boundaries where automation is useful: validating an artifact when a plan file is written, running a check before a commit, seeding state at the start of a session. Nexus-Hub had no declared way to run something at those boundaries.

## Proposal

Import the per-command hook registry pattern observed in the v3.6.0 Spec Kit comparison: a registry mapping each command to `before_<command>` and `after_<command>` handlers, invoked by the harness around command execution.

## Alternatives considered

- **Key `PreToolUse` / `PostToolUse` matchers on the tool call the phase boundary actually produces**, and let the hook inspect the tool input. This is the alternative that won.
- **Add new harness event types** for workflow phases. Rejected: it invents runtime surface that no platform implements, so the events would never fire.
- **Do nothing.** Rejected: the need is real and recurring.

## Risks

Stated at the time as the coupling between Nexus-Hub's command set and a registry that would need updating on every command rename.

## Verdict

Rejected on a more fundamental ground than the stated risk. A per-command registry presupposes an extension runtime that invokes commands through a dispatch layer Nexus-Hub can hook. **That runtime is itself a declined candidate** (v3.6.0 comparison, candidate N1b). Adopting the registry would have meant adopting the runtime by implication, which is structure with no call site, against the scope-fit rule in the `Boundaries` section of AGENTS.md.

The winning alternative works because a phase boundary is not an abstract event, it is a specific tool call. Match `Write`/`Edit` and gate on `tool_input.file_path` (a plan artifact under `docs/**/plans/`, a `spec.md`, a `CHANGELOG.md`), or match `Bash` and gate on `tool_input.command` (a `git commit`). Use `SessionStart` / `Stop` for session-level setup and teardown. This is a usage pattern on the existing surface rather than a new runtime, and it ships as `catalog/hooks/workflow-phase-notice.sh`.

The general form of the error is worth keeping: **importing a pattern also imports its assumed runtime.** When an external project's pattern looks adoptable, check what has to exist for it to work before adopting the shape.
