# Merge-Readiness Contract Convention

A **merge-readiness contract** is a single, named, machine-checkable gate that says when a change is allowed to merge. It binds the checks a project already runs (CI, review, PR hygiene) into one verifiable statement, so "ready to merge" is a checklist backed by evidence rather than a reviewer's feeling.

The gate itself (the required criteria R1-R6 and the optional collaborator rules) ships as the `merge-ready` gate in the [`quality-gate-definitions`](../skills/orchestration/quality-gate-definitions/SKILL.md) skill. This guide documents the CONFIGURABLE collaborator-rule options that a project tunes to its team size and risk. It is installed at `~/.nexus-hub/style-guides/merge-readiness-contract.md`.

## The fixed core (always required)

These required criteria hold for every project; they are not configurable, only satisfied or not:

- **CI is green on the current head** - verified against the head commit's status rollup this turn, not a remembered pass.
- **Review is clean, or every finding is addressed** - an APPROVED decision with zero unresolved threads.
- **The PR is one concern wide** - a single stated intent, no drive-by changes.
- **An issue is linked, or partiality is stated** - `Fixes #N` / `Closes #N`, or an explicit "partial: ..." note.
- **Evidence discipline** - every gate above is verified against LIVE current-head GitHub state, per the `verification-before-completion` skill. A usage-limit or missing-review result is MISSING EVIDENCE, not approval.
- **Project review trapdoors checked** - the project's curated recurring-blocker list (see `review-trapdoors.md`) was applied.

## The configurable collaborator rules

These are policy choices. Adopt the subset that fits your team; document which are in force in the project's `CONTRIBUTING.md` or constitution.

### No self-merge (default: on)

A change is merged by someone other than its author. A second pair of eyes is the cheapest defense against the blind spots of the person who wrote the code.

- **When to keep it on**: any team of two or more. This is the default.
- **When it cannot apply**: a solo maintainer has no second person; the rule is vacuous and disabled (rely on the fixed-core criteria plus, ideally, a cross-model review to stand in for the second reader).
- **Escape hatch**: see the bus-factor rule below.

### Net-lines / one-concern ceiling (default: a soft cap you set)

A configurable ceiling on how large a single PR may be before it must be split or earns extra scrutiny. Express it as whichever the team can measure: a net-lines number (for example, net change over ~400 lines needs justification or a split), or purely "one concern" with no numeric cap. Large PRs get reviewed worse; the ceiling makes that failure mode explicit.

- Keep the cap SOFT: it triggers a split-or-justify conversation, not an automatic block, because some changes (a generated file, a mechanical rename) are legitimately large.
- Pair it with the one-concern rule: a PR under the line cap that still mixes two concerns should be split anyway.

### Bus-factor self-merge escape hatch (default: off)

A time-boxed exception to no-self-merge for teams small enough that a change can otherwise sit forever waiting for a reviewer who is unavailable.

- **Shape**: if no reviewer responds within a configured window (for example, 24-48 hours) AND the change is small and low-risk AND CI is green, the author may self-merge with a recorded note stating the window elapsed.
- **Guardrails**: it applies ONLY to small, low-risk changes; never to security-sensitive, schema, or public-API changes. The self-merge is recorded (in the PR, and ideally in the changelog or a decision log) so it is auditable.
- **Keep it off** on teams where a reviewer is reliably available; it exists for the bus-factor-of-one case, not as a convenience.

## Choosing a profile

| Team shape | No self-merge | Net-lines ceiling | Bus-factor escape hatch |
|---|---|---|---|
| Solo maintainer | Off (vacuous); use cross-model review as the second reader | Soft cap, self-enforced | N/A |
| Small team (2-4) | On | Soft cap | On (time-boxed, small/low-risk only) |
| Larger team (5+) | On | On, with a numeric cap | Off |

## Self-check for a project's contract

- [ ] The fixed-core required criteria are all enforced (CI, review, one-concern, issue link, evidence discipline, trapdoors).
- [ ] Which collaborator rules are in force is written down in `CONTRIBUTING.md` or the constitution, not left implicit.
- [ ] The net-lines ceiling (if adopted) is a soft split-or-justify trigger, not a hard block on legitimately large mechanical changes.
- [ ] The bus-factor escape hatch (if adopted) is time-boxed, limited to small low-risk changes, and records each use.
- [ ] Every gate is verified against live current-head state, never a stale approval or a remembered green check.
