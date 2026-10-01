# Copilot Native Skills Surface - Compatibility Probe and Seeding Design (2026-07-08)

**Cycle**: adoption-spec-kit Phase 5 (S3)
**Decision**: **GO**

## Compatibility probe (primary sources)

GitHub Copilot's project-scoped Agent Skills surface is confirmed from primary GitHub / VS Code documentation:

- [Adding agent skills for GitHub Copilot - GitHub Docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [Use Agent Skills in VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills)

Confirmed contract:

- **Location**: a skill is a directory `.github/skills/<name>/` containing a `SKILL.md`. Directory names are lowercase with hyphens.
- **Frontmatter (YAML)**: `name` (required) and `description` (required); `license` (optional). **The `name` value MUST match the parent directory name.**
- **Injection**: when Copilot chooses a skill, its `SKILL.md` is injected into the agent context.
- **Portability**: Agent Skills is an open standard shared by Copilot in VS Code, the Copilot CLI, and the cloud agent.

Known upstream failure modes to avoid (from the comparison): a non-standard frontmatter key such as `mode:` is rejected, and non-ASCII frontmatter can be mangled. Our catalog skills already use lowercase-hyphen names, so `name` matches the directory cleanly.

## Seeding design

1. **Wrapper, not verbatim (RECOMMENDED, chosen).** Seed thin wrapper `SKILL.md` files that carry ONLY the Copilot-recognized `name` + `description` frontmatter and a short body pointing at the installed `~/.nexus-hub/` catalog content, rather than copying full catalog bodies into the user's repo. Rationale: (a) avoids repo-bloat and a commit-visible duplicate of the catalog; (b) sidesteps the frontmatter-compatibility risk (our rich `summary_l0`/`overview_l1`/framework-tag frontmatter is not in Copilot's accepted set and could trip the `mode:`-style rejection); the wrapper carries only the two safe keys.
2. **Curated default set.** Seed the `core-developer` bundle from `data/bundles.json` (10 skills: plan-before-code, test-driven-development, code-commit-workflow, debug-with-logs, refactoring-expert, unit-tests, code-quality, strategic-comments, pre-commit-checklist, research-plan-implement) rather than all 265 skills. A bundle name that does not resolve to a catalog skill dir is skipped-with-note.
3. **Opt-in mechanism.** Seeding happens ONLY when the opt-in env var `NEXUS_HUB_COPILOT_SKILLS` is truthy, never by default, because `.github/skills/` is commit-visible in the user's repo. This reuses the Phase 7.3 `NEXUS_HUB_NO_AUTOSEED` env-var pattern and requires NO `scripts/installer.sh` / `installer.ps1` edit and NO new `InstallContext` field (the "ask first" installer surface is left untouched). `nexus-hub init` invokes `wire_project_surfaces`; the override reads the env var itself.
4. **Collision policy.** Never overwrite an existing file under `.github/skills/`; skip-with-note. All writes are recorded through the existing manifest machinery so `doctor` / `repair` see them.

## Notes

- ASCII-only: the wrapper `name`/`description`/body are ASCII-sanitized before write.
- Because the surface is opt-in and off by default, a plain `nexus-hub init` does not create `.github/skills/`; the row in the AGENTS.md distribution-channels table documents the opt-in.
- The `name`-matches-directory rule is honored: the wrapper is written to `.github/skills/<name>/SKILL.md` with `name: <name>`.
