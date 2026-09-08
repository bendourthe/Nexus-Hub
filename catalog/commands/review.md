---
description: Comprehensive, scope-able review of a project - structure, quality, coverage, security, pentest, diff review, dependency and supply-chain, and skill-security scanning. Use to "review the codebase", "do a deep review", "audit security", "run a pentest", "review my changes", "check this PR", "scan a skill", "generate an SBOM", "review before release". SKIP - writing tests (use /test), or fixing findings without reviewing first (review, then act on the report).
---

# /review Command

Run a comprehensive, scope-able review of a project. `/review` is the entry point for read-only structure, quality, test coverage, application security, supplied penetration-test evidence, pending changes, dependency analysis, SBOM content, and skill-security scanning. Bare invocation asks for a scope; `full` orchestrates the documented lenses and synthesizes one verdict.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive review logic lives in the retained skills; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `full`, `structure`, `quality`, `coverage`, `security`, `pentest`, `changes`, `skill-scan`, `sbom`, `deps`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- If `$ARGUMENTS` is a path or target (for example a skill directory for `skill-scan`, or a glob to restrict the lens), route it to the resolved scope and pass it through.
- An unknown explicit scope returns `Unknown review scope` with the recognized scopes and performs no work. Missing or ambiguous scope presents this menu and waits for a selection:

      What scope?
        1. full        (recommended) - run every lens in order and synthesize one verdict
        2. structure   - module boundaries, layering, and dependency map
        3. quality     - SOLID, complexity, maintainability, code smells
        4. coverage    - test-coverage analysis and gap identification
        5. security    - security audit (secrets, auth, input validation, dangerous patterns)
        6. pentest     - assess supplied penetration-test evidence and author a report
        7. changes     - multi-agent persona review of the pending diff
        8. skill-scan  - security-scan a skill (or the whole catalog) before install
        9. sbom        - generate a Software Bill of Materials
       10. deps        - dependency CVE / license / supply-chain scan

      Reply with a number or a scope name.

- `full` runs the focused lenses in order - `structure`, then `quality`, then `coverage`, then `security`, then `changes` - then synthesizes a deduplicated, severity-ranked report with a GO / GO-WITH-CONDITIONS / NO-GO verdict. This is the pre-release deep review.
- Scope can be inferred: a bare `/review` against a working tree with uncommitted changes may suggest `changes`; a skill directory argument infers `skill-scan`. Inference must be unambiguous; otherwise fall back to the menu.

## Delegation

Dispatch the resolved scope to the retained skill(s):

      full        -> context-analysis, code-quality, testing-review, security-review, multi-agent-code-review, final-report
      structure   -> analyze-codebase
      quality     -> code-quality
      coverage    -> testing-review
      security    -> security-review
      pentest     -> security-review, pentest-reporting
      changes     -> multi-agent-code-review
      skill-scan  -> skill-security-scan
      sbom        -> sbom-generation
      deps        -> dependency-security-audit, licensing-compliance

Pass only the remaining read-only target path, scope, and depth arguments. Reject mutation flags and approval payloads before delegation, including a valid-looking approval receipt. Heavy logic stays in the owning skills. Missing delegates are explicitly unavailable; never reconstruct their rules. `pentest-reporting` authors reports from supplied evidence and does not execute penetration tests. SBOM content is returned as a report; this dispatcher does not write to the target.

## Security coverage contract

Application-security routing uses the single [routing manifest](../skills/workflow/agent-presets/references/security-audit-routing.json) through its collector and pure resolver, as explained in [the host routing contract](../skills/workflow/agent-presets/references/security-audit-routing.md). `security-review` remains authoritative. This read-only entry point uses detection, triage, verification, and reporting only; it never enters the preset's remediation stages.

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

## skill-scan scope (pre-install and catalog dogfood)

`skill-scan` is the v3.0.0 addition. It runs the `skill-security-scan` skill over a target skill directory (a skill you are about to import) or over the whole `catalog/skills/` + `catalog/mcp-configs/` tree (catalog dogfood). The skill reads the deterministic findings emitted by `nexus-skill-scanner` (Phase 6) and adjudicates them - filtering false positives (especially fenced-code examples in a producer catalog), explaining intent, and assigning a final verdict. Until the Phase 6 engine lands, the scope adjudicates manually-collected findings. This is the same lens `/skills scan` uses before an import.

## Optional fan-out

For very large read-only audits ("audit every endpoint for missing auth", "scan every skill in the catalog"), offer the dynamic-workflow fan-out path with confirmation and the scope-first token caution: calibrate on a small slice before fanning out across the whole surface. Fall back to single-agent execution when workflows are unavailable. See [[agent-orchestration-primitives]].

## Notes

- All scopes are unconditionally read-only. Never consume an approval receipt, launch remediation, apply a patch, or mutate the target. Recommend a separately authorized `security-patch-advisor` invocation when findings need changes; the separate owning skill must obtain its own trusted, current, exact-patch and scope-bound approval.
- Keep this dispatcher thin. The review procedures live in the retained skills; this file owns only scope resolution and delegation.
