# Decision: Living docs are `docs/handbooks/` plus `docs/decisions/` on the current path scheme

Status: implemented - required living tree is `docs/handbooks/` (markdown source, generated HTML, atlas, companions) and `docs/decisions/`; `docs/testing/` and `docs/validation/` stay self-gated; versioned plans still use `docs/v<MAJOR>/v<MAJOR>.<MINOR>/`

## Problem

A consuming project that only had the versioned `docs/v*` tree had no place to keep current-`main` handbooks. Agents treated last-phase layout work as optional, and the v4.0 lifespan plan recorded that Nexus-Hub had no `handbooks/` equivalent, which would have delayed living docs until a 700-file container rename.

## Decision

Prescribe a living vs frozen split **on the current path scheme**:

- Frozen, version-scoped artifacts stay under `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` (plans, comparisons, known-gaps, session history).
- Living product docs live at `docs/handbooks/` (`markdown/` is source of truth; generated `html/` is never hand-edited) plus `docs/decisions/` (ADRs, never release-scoped) and living `docs/README.md` / `docs/DEVLOG.md` / `docs/todos.md`.
- `docs/testing/` exists only if the project already tracks tests that way. `docs/validation/` exists only if GxP or signed records exist. Neither is invented on a greenfield library.
- `/setup project` scaffolds missing handbooks and decisions detection-first. `/update docs` refreshes handbook markdown against the code. `/update refactor` canonicalizes a missing tree. `/update release` regenerates HTML and fails if stale when markdown exists, then snapshots `docs/handbooks/markdown/` to `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/handbooks/`.
- HTML walkthroughs use `[[document-to-interactive-html]]` / `/presentify`. A last-phase Goal review still has to prove this architecture landed.

v4.0 owns the later rename to `docs/releases/` + `docs/archives/` and must snapshot `docs/handbooks/` rather than decline the equivalent.

## Alternatives considered

- **Copy `docs/validation/` universally from the rd-data-dev tree.** Rejected: GxP signed protocols are not a greenfield-library concern. Inventing `validation/` would create fake compliance records. The path is self-gated.
- **Wait for the v4.0 container rename before adding any `handbooks/` tree.** Rejected: living docs do not need the container rename. Delaying them would leave `/setup` and `/update` unable to check the architecture this plan already fail-closes on the last phase.
- **Keep only versioned `docs/v*` and treat README as the living surface.** Rejected: README is a catalog index, not a walkthrough. Handbooks need markdown source, generated HTML, an atlas, and per-component companions that a README cannot hold without becoming a second docs tree in one file.

## Consequences

- Consuming projects get `docs/handbooks/` and `docs/decisions/` from `/setup project` without a 700-file migrate.
- Last-phase and `/update release` can fail closed on stale generated HTML when markdown exists.
- Nexus-Hub's own catalog may record an evidenced no-op or known-gap instead of a fake product atlas; that honesty is required, not optional.
- The v4.0 lifespan plan must consume this tree rather than claim there is no equivalent.
