---
description: Run a multi-agent persona code review over the current diff, branch, or PR - parallel reviewer lenses merged through a confidence-anchored dedup and gating pipeline.
---

# Review Changes Command

Run a persona-fanout code review of a code change. This command is a thin entry point to the `multi-agent-code-review` skill; the skill holds the full pipeline (scope resolution, intent discovery, per-diff persona selection, bounded parallel dispatch, confidence-anchored merge, validation pass, model tiering).

## Usage

```
/review-changes                      # review uncommitted work (standalone mode)
/review-changes branch               # current branch vs its merge base
/review-changes pr <number>          # a specific pull request
/review-changes <ref-a>..<ref-b>     # an explicit commit range
/review-changes --mode report-only   # write a report artifact instead of in-chat findings
/review-changes --mode autofix       # apply safe fixes, propose the rest
```

Modes: `interactive` (default), `autofix`, `report-only`, `headless`. See the skill's Modes table for what each changes.

## What it does

1. Resolves the diff scope from the argument (standalone / branch / PR / base range).
2. Discovers the change's intent from branch name, commits, and any linked plan/issue.
3. Selects reviewer personas per-diff: always-on (correctness, maintainability, testing, project-standards) plus conditional lenses (security, performance, api-contract, reliability, adversarial, agent-native) that match the diff.
4. Dispatches the selected `catalog/agents/*-reviewer` agents in bounded parallel; each returns structured JSON findings.
5. Merges findings with the confidence-anchored-scoring discipline: fingerprint dedup, cross-reviewer promotion, mode-aware demotion, late confidence gate.
6. In externalizing modes, runs an independent refutation pass per finding.
7. Emits a ranked headline list with a suppressed-findings appendix.

## Invocation

Invoke the `multi-agent-code-review` skill with the resolved scope and mode. Everything runs locally over the local diff and local agent definitions; no outbound call is made.

See [catalog/skills/code-review/multi-agent-code-review/SKILL.md](../skills/code-review/multi-agent-code-review/SKILL.md) for the full pipeline and verification checklist.
