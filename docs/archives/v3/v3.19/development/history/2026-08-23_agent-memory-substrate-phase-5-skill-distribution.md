# Session History - Agent-Memory Substrate Phase 5: Skill, Distribution, and Registration

**Date**: 2026-08-23
**Branch**: `feat/v3.19.1-agent-memory-substrate`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md`](../../plans/v3.19.1-agent-memory-substrate.md)
**Phase**: 5 - Skill, distribution, and registration
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest
**Outcome**: The `agent-memory` skill is registered, trigger-routed, and installer-copied. The package lands at `~/.nexus-hub/nexus-memory` so it does not collide with the default store root. It is not an MCP server.

## 1. Starting State and Routing

- **Starting commit**: `4e6c0e76` (Phase 4)
- **Plan recommendation**: strong reasoning tier, medium effort
- **Implementation route**: stayed on the current Cursor session; no downshift

## 2. What Was Implemented

### 5.1 / 5.2 - Skill and routing evals

Authored `catalog/skills/workflow/agent-memory/SKILL.md` (108 lines) with a pushy description, SKIP clause naming all four existing memory-adjacent skills plus `ai-agent-development`, and the required body sections. `evals/trigger-cases.json` has four positives and three near-misses (session-query, context-pack-builder, continuous-learning). `scripts/run_trigger_evals.py --gate` reports 0 routing failures.

### 5.3 - Registry

Hand-edited `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`. Catalog count is 273 to 274; workflow is 44 to 45. Did not run `build_skills_catalog.py`.

`# DEVIATION:` also added `agent-memory` to the `workflow` module in `data/bundles.json`. `check_registry_entries.py --strict` treats a skill in no module and no bundle as unreachable, so the three-file rule alone would fail `make validate`.

### 5.4 - Installer and matrix

Both installers copy `extensions/nexus-memory/` to `~/.nexus-hub/nexus-memory` and editable-install it into the shared venv. No MCP registration. Matrix row classified `already-local`; rationale records that the capability was reverse-engineered rather than adopted. Dry-run verification is the installer-path contract in `tests/skills/test_agent_memory.py` (both copy blocks, dest names, and the absence of an MCP key), not a live install into a throwaway home.

## 3. Tests

`tests/skills/test_agent_memory.py`: 12 passed (frontmatter, SKIP names, no placeholders, no upstream product name, trigger-case shape, three-file count agreement, installer copy, matrix row). Trigger-eval gate PASS. Registry `--strict` PASS.

## 4. Next Steps

Phase 6: layout refactor, whole-tree policy audit, known-gaps reconciliation, then `/update release`.
