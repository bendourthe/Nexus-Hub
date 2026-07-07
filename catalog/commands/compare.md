---
description: Compare this project to an external source (a Git repo, a web article, or a local path) and produce a gap analysis plus a prioritized adoption plan. Use to "compare this repo to X", "what can we learn from this project", "gap analysis against this article", "benchmark us against this codebase", "what are we missing vs this tool". SKIP - reviewing this project on its own (use /review) or researching a topic with no specific source to compare against (use /research).
---

# /compare Command

Compare the current project to an external knowledge source and turn the differences into an actionable plan. `/compare` detects whether the source is a Git repository, a web article, or a local path, analyzes it against this project, writes a structured gap analysis with a prioritized adoption plan, and chains directly into `/plan from-comparison` so the highest-value gaps become a real implementation plan.

This is a thin dispatcher over the retained `compare-project` skill, following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive comparison logic - source detection, the mandatory Security and Reverse-Engineering assessment sections, and the adoption-plan synthesis - lives in the skill; this file resolves the source type and delegates.

## Scope resolution (auto-inferred from the source)

`/compare` infers its scope from the source argument rather than prompting, because the source type is almost always unambiguous. Recognized scopes: `repo`, `article`, `local`.

- `/compare <github-url>` or any Git remote URL infers `repo`.
- `/compare <http(s)-article-url>` infers `article`.
- `/compare <local-path>` infers `local`.
- `/compare` (bare) - ask for the source (URL or path), then infer the scope from what is supplied.

When the source type is genuinely ambiguous (for example a URL that could be either a repo or an article), state the detected type and confirm before analyzing.

## Delegation

Dispatch the resolved scope to the retained skill:

      repo     -> compare-project (clone / fetch the repository, compare structure, dependencies, and patterns)
      article  -> compare-project (fetch and extract the article, compare claims and recommendations)
      local    -> compare-project (compare against the local path on disk)

Pass the source argument and any remaining arguments through unchanged. Heavy logic stays in the `compare-project` skill; this file only detects the source type and delegates.

## Mandatory assessment sections (preserved)

The `compare-project` skill produces a Security assessment and a Reverse-Engineering assessment for every adoption candidate, per Nexus-Hub's MCP Registry Policy (reverse-engineer-first). These sections are not optional - do not skip them when delegating. Each proposed adoption must be classified against the policy decision tree (local-only / skill-native / reverse-engineer into an internal MCP / trusted-vendor wrapper / drop) before it lands in the adoption plan.

## Output and the /plan chain

The comparison report is written to `docs/v<MAJOR>/v<MAJOR>.<MINOR>/comparisons/comparison-<name>.md` per the `compare-project` skill (see the `docs-layout-refactor` Version-directory resolution for the scheme). After the report is written, offer to chain into `/plan from-comparison`, which ingests the report's prioritized adoption plan and produces a phased implementation plan with reverse-engineer-first ordering.

## Notes

- This command replaces `/compare-project` (removed in v3.2.0).
- Keep this dispatcher thin. The comparison procedure lives entirely in the `compare-project` skill; this file owns only source detection, delegation, and the `/plan from-comparison` hand-off.
