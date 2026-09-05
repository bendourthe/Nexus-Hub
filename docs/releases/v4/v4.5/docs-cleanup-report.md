# Docs cleanup audit - v4.5

Audit-mode report written by the phase 8.6 step of each v4.5.0 phase. Nothing moves as a result of this report; proposals need explicit approval.

## Phase 1 (2026-09-04)

- Scope inspected: `docs/releases/v4/v4.5/` after phase 1.
- New files this phase created: `development/writing-discipline-block.md` (the block's source of truth, kept because phases 2 and 3 read it), `development/history/2026-09-04_v4.5.0-anti-cliche-and-agent-security-phase-1-writing-discipline-rule.md`, `known-gaps.md`, and this report. All are release-scoped by the lifespan admission test (none changes after v4.5.0 closes), so they sit correctly under the active release tree.
- Scratch docs proposed for cleanup: none. The block file is load-bearing, not scratch.
- `python scripts/check_docs_conventions.py`: OK (relative links resolve, directory names kebab-case).
- `python scripts/check_docs_retention.py`: nothing due for archival.
- Stray comparison reports outside `comparisons/`: none.
