# Nexus-Hub documentation

This tree splits **living** docs (edited in place, describing current `main`) from **versioned** docs (frozen per minor) and **archive**.

## Living

- [DEVLOG.md](DEVLOG.md) -- one index line per release
- [todos.md](todos.md) -- forward dashboard (may lag the branch; see v3.21 known-gaps)
- [decisions/](decisions/README.md) -- ADRs; never release-scoped
- [handbooks/](handbooks/README.md) -- markdown source of truth plus generated HTML. This catalog has no product atlas HTML yet; do not invent one
- [policy/](policy/) -- installer, platform-contract, and MCP policy

There is no `docs/testing/` or `docs/validation/` tree. Those paths are self-gated and are not invented here.

## Versioned

Plans, comparisons, development history, and known-gaps live under `v<MAJOR>/v<MAJOR>.<MINOR>/`. The active 3.x minor is [v3/v3.21/](releases/v3/v3.21/). The active 4.x minor in progress is [v4/v4.4/](releases/v4/v4.4/).

## Archive

Older per-version `development/` subtrees and the pre-index DEVLOG body live under [archive/](archives/).
