# Nexus-Hub documentation

This tree splits **living** docs (edited in place, describing current `main`) from **versioned** docs (frozen per minor) and **archive**.

## Living

- [DEVLOG.md](DEVLOG.md) -- one index line per release
- [todos.md](todos.md) -- forward dashboard (may lag the branch; see v3.21 known-gaps)
- [decisions/](decisions/README.md) -- ADRs; never release-scoped
- [guides/](guides/) -- user guides: [usage-limit handoff](guides/usage-limit-handoff.md), [repository-native CI profiles](guides/repository-native-ci-profiles.md), [user attribution](guides/user-attribution.md), and [host-agent disk writes](guides/host-agent-disk-writes.md)
- [handbooks/](handbooks/README.md) -- markdown source of truth plus generated HTML. This catalog has no product atlas HTML yet; do not invent one
- [policy/](policy/) -- installer, platform-contract, and MCP policy

There is no `docs/testing/` or `docs/validation/` tree. Those paths are self-gated and are not invented here.

## Versioned

Plans, comparisons, development history, and known-gaps live under `releases/v<MAJOR>/v<MAJOR>.<MINOR>/`. The current application-security audit implementation is in [v4.9](archives/v4/v4.9/plans/v4.9.0-adoption-visa-vulnerability-agentic-harness.md). Separately owned guide work remains in [v4.4](archives/v4/v4.4/); the [dashboard](todos.md) records concurrent and queued plans. Existing 3.x records remain under [releases/v3/](archives/v3/).

## Archive

Older per-version `development/` subtrees and the pre-index DEVLOG body live under [archive/](archives/).
