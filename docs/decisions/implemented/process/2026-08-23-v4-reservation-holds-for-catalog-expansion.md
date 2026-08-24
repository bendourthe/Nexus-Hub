# Decision: Keep v4.0.0 reserved for changed-install-behavior; v3.20.1 catalog expansion does not consume it

Status: implemented - two new skill categories and forty skills ship in v3.20.1 because they change nothing about an already-installed Nexus-Hub

## Problem

v3.20.1 adds `ot-security` and `mobile-security` and forty skills. A major bump is the obvious-looking reaction to "large catalog change." Nexus-Hub already decided, on 2026-08-20, that v4.0.0 is reserved for the bundle that changes what an installed copy does (`cost-effective-ci-cd`, `agent-communication-overhaul`, `docs-lifespan-tree-and-enforcement`). Spending the major on an additive catalog release would leave the next genuinely breaking release with no signal.

## Decision

This release stays a patch on 3.20. New categories are additive: they do not rename, move, or remove existing skills. Existing installs that upgrade pick up new files and leave every previous skill path intact. The v4.0.0 reservation in `docs/v3/roadmap-prioritization.md` and `docs/decisions/implemented/process/2026-08-20-roadmap-ordering-and-v4-reservation.md` is unchanged.

## Alternatives considered

- **Cut v4.0.0 because two new categories feel like a major.** Rejected: adding a category breaks nothing. Reorganizing existing skills into new categories would be a different decision and still would not match the changed-install-behavior test unless the installer rewrote live paths.
- **Hold the forty skills until the v4.0.0 bundle ships.** Rejected: they do not belong in that bundle, and parking additive security coverage behind unrelated installer-behavior work delays the only user-visible payoff of this plan.
- **Ship the skills now and also bump major "for visibility."** Rejected: a major that breaks nothing teaches users to ignore majors, which is how the v3.0.0 migration signal gets spent twice.

## Consequences

- Release notes and the capability-usage gate treat v3.20.1 as a no-new-opt-in-surface release.
- A future proposal that relocates existing security skills into `ot-security` or `mobile-security` must argue install-path compatibility separately; this record is not permission to reshape the live tree.
- The three v4.0.0 bundle members remain coupled to each other, not to catalog expansion.
