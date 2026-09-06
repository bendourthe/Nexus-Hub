---
description: Comprehensive, scope-able review of a project - structure, quality, coverage, security, pentest, diff review, dependency and supply-chain, and skill-security scanning. Use to "review the codebase", "do a deep review", "audit security", "run a pentest", "review my changes", "check this PR", "scan a skill", "generate an SBOM", "review before release". SKIP - writing tests (use /test), or fixing findings without reviewing first (review, then act on the report).
---

# /review Command

Run a comprehensive, scope-able review of a project. `/review` is the single entry point for every read-only review lens Nexus-Hub ships: whole-codebase structure and quality, test-coverage analysis, security audit, penetration test, multi-agent diff review of pending changes, dependency and supply-chain checks, SBOM generation, and skill-security scanning. Bare invocation asks for a scope; `full` orchestrates every lens and synthesizes one verdict.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive review logic lives in the retained skills; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `full`, `structure`, `quality`, `coverage`, `security`, `pentest`, `changes`, `skill-scan`, `sbom`, `deps`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- If `$ARGUMENTS` is a path or target (for example a skill directory for `skill-scan`, or a glob to restrict the lens), route it to the resolved scope and pass it through.
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. full        (recommended) - run every lens in order and synthesize one verdict
        2. structure   - module boundaries, layering, and dependency map
        3. quality     - SOLID, complexity, maintainability, code smells
        4. coverage    - test-coverage analysis and gap identification
        5. security    - security audit (secrets, auth, input validation, dangerous patterns)
        6. pentest     - deep penetration test with proof-of-concept findings
        7. changes     - multi-agent persona review of the pending diff
        8. skill-scan  - security-scan a skill (or the whole catalog) before install
        9. sbom        - generate a Software Bill of Materials
       10. deps        - dependency CVE / license / supply-chain scan

      Reply with a number or a scope name.

- `full` runs the focused lenses in order - `structure`, then `quality`, then `coverage`, then `security`, then `changes` - then synthesizes a deduplicated, severity-ranked report with a GO / GO-WITH-CONDITIONS / NO-GO verdict. This is the pre-release deep review.
- Scope can be inferred: a bare `/review` against a working tree with uncommitted changes may suggest `changes`; a skill directory argument infers `skill-scan`. Inference must be unambiguous; otherwise fall back to the menu.

## Delegation

Dispatch the resolved scope to the retained skill(s):

      full        -> run-deep-review (orchestrates all lenses + release-readiness checks + synthesis)
      structure   -> review-codebase (structure / module-boundary section)
      quality     -> review-codebase (SOLID, complexity, maintainability section)
      coverage    -> review-codebase (test-coverage analysis section)
      security    -> run-security-audit (report-only by default)
      pentest     -> run-penetration-test (deep, OWASP-WSTG-aligned)
      changes     -> review-changes (multi-agent persona diff review)
      skill-scan  -> skill-security-scan (semantic adjudication; backed by nexus-skill-scanner once Phase 6 lands)
      sbom        -> generate-sbom
      deps        -> run-security-audit (dependency CVE / supply-chain portion); pair with generate-sbom for the artifact

Pass any remaining arguments (target path, `--scope` glob, depth flags) through unchanged. Heavy logic stays in the retained skills; this file only resolves scope and delegates.

## Security coverage contract

For `security`, and for the security lens inside `full`, require the delegated `[[security-review]]` report to state its component denominator and the exact line `N of M components covered; O omitted; U UNCOVERED`, followed by the named omissions and uncovered components. Never present a partial assessment as complete. A depth flag may reduce how many components receive review actions, but it never reduces the denominator or the honesty of the coverage statement; unreviewed components remain UNCOVERED. All inventory, altitude, and sink-sweep mechanics stay in the owning skill. When the reviewed project runs or embeds AI agents (it spawns agents, holds agent credentials, or makes agent-driven egress calls), also engage the `agent-execution-isolation` skill and its three-question triage (where does execution happen, what software runs inside the loop, what leaves the boundary).

## Project health (full and structure scopes)

For the `full` and `structure` scopes, `/review` emits the same read-only Project-health block that `[[analyze-codebase]]` produces, so a review surfaces governance gaps consistently with `/describe`. Report each surface as OK or MISSING:

| Surface | Status | Detail |
|---|---|---|
| Git version control | OK / MISSING | repo present? at least one commit? |
| Version number | OK / MISSING | resolved version (tag / CHANGELOG / manifest), or none found |
| Branch model | OK / MISSING | develop + main present? or which model is in use? |
| Baseline docs | OK / MISSING | README / CHANGELOG / DEVLOG present with real content? |
| Per-version docs tree | OK / MISSING | docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/ with plans/ + comparisons/? |

When any surface is MISSING, end the block with the handoff offer, naming the gaps: "Setup needed: <gaps>. Run `/setup project` to bootstrap them." `/review` stays read-only (its contract below) - it detects and recommends but never mutates; remediation is the user's call via `/setup`. Use the exact wording from `[[analyze-codebase]]` so `/describe` and `/review` stay in sync.

> Note: the `full` / `structure` delegates (`run-deep-review`, `review-codebase`) are currently prose-only - their bodies live in git history rather than as SKILL.md files - so this health-block behavior is documented here at the command level until those delegates are reconstituted. It does not change `/review`'s read-only contract.

## skill-scan scope (pre-install and catalog dogfood)

`skill-scan` is the v3.0.0 addition. It runs the `skill-security-scan` skill over a target skill directory (a skill you are about to import) or over the whole `catalog/skills/` + `catalog/mcp-configs/` tree (catalog dogfood). The skill reads the deterministic findings emitted by `nexus-skill-scanner` (Phase 6) and adjudicates them - filtering false positives (especially fenced-code examples in a producer catalog), explaining intent, and assigning a final verdict. Until the Phase 6 engine lands, the scope adjudicates manually-collected findings. This is the same lens `/skills scan` uses before an import.

## Optional fan-out

For very large read-only audits ("audit every endpoint for missing auth", "scan every skill in the catalog"), offer the dynamic-workflow fan-out path with confirmation and the scope-first token caution: calibrate on a small slice before fanning out across the whole surface. Fall back to single-agent execution when workflows are unavailable. See [[agent-orchestration-primitives]].

## Notes

- This command replaces `/review-codebase`, `/review-changes`, `/run-deep-review`, `/run-security-audit`, `/run-penetration-test`, and `/generate-sbom` (removed in v3.2.0).
- All scopes are read-only: `/review` analyzes and reports; remediation goes into a plan (via `/plan from-comparison` or the synthesis report's roadmap), not into the working tree.
- Keep this dispatcher thin. The review procedures live in the retained skills; this file owns only scope resolution and delegation.
