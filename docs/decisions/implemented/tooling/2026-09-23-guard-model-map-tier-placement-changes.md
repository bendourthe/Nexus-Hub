# Decision: Guard model-map tier placement changes against the prior snapshot

Status: implemented - a refreshed map must report known model IDs that move tiers, and `/plan` must explain or restore each move before using the map
Date: 2026-09-23
Author: Ben Dourthe
Template: Nygard

## Problem

The model map assigns provider models to portable capability tiers. `/plan` refreshes it from current vendor information, but `model-map.py validate` checked only its shape: a complete set of non-empty cells passed even if two tiers in one provider column were reversed. The v4.16.3 plan exposed that failure when a refreshed Anthropic column discarded a placement judgment already recorded in `last-known-model-map.json`.

Vendor model lists establish availability and naming; they do not by themselves preserve this repository's comparative tier judgment. A fresh search can therefore produce a syntactically valid map while silently changing which model a future phase selects. The snapshot is useful as a prior judgment, but it cannot be frozen forever because vendors add models and genuine capability changes require reclassification.

The decision must preserve the distinction between a known ID moving to a different tier and a new ID receiving its first placement. It must also work offline, since a failed web refresh should use a dated fallback rather than create an unverified ordering from memory.

## Decision

`model-map.py diff` compares each known model ID's proposed tier with its tier in the last-known snapshot. It exits with code 3 and lists every changed placement; an ID absent from the snapshot is new, not a reclassification. `/plan` runs this check beside `validate` after a refresh and stops on a move until the placement is restored or its reason is stated in the plan. The dated snapshot remains the offline fallback.

This guard does not decide which tier is objectively correct, verify vendor marketing claims, or prohibit a justified change. It makes the change visible at the point where a plan would otherwise silently inherit it.

## Alternatives considered

- **Keep shape validation only.** This allows every new map through as long as its cells are populated, but it cannot detect the demonstrated column inversion. A passing validator would continue to imply more confidence than it earned.
- **Freeze every snapshot placement.** This prevents silent movement, but it also blocks genuine reclassification and forces a separate manual bypass whenever a model changes or a provider retires a tier. It turns a dated prior into an immutable authority.
- **Re-derive all tiers from vendor pages on every invocation.** This keeps names current, but vendor lists do not encode the project's tier policy. The v4.16.3 error occurred on precisely such a successful refresh, so repeating it is not an independent check.

## Consequences

- Known-ID tier moves become reviewable evidence in the plan instead of an invisible side effect of refreshing model names. The regression tests cover matching maps, moved IDs, and new IDs.
- Maintaining the snapshot is now part of changing the tier policy. A legitimate move costs an explicit explanation, and stale snapshots can produce a stop that requires human judgment.
- A clean diff proves continuity with the prior placement, not that the prior placement is correct today. Current vendor verification and the plan's model-map date remain separate obligations.

## Related

- [`model-routing`](../../../../catalog/skills/ai-development/model-routing/SKILL.md) - owns tier selection and the refresh procedure
- [`model-map.py`](../../../../catalog/skills/ai-development/model-routing/scripts/model-map.py) - implements the placement diff
- [`model-routing-in-plan-and-implement.md`](../../../policy/model-routing-in-plan-and-implement.md) - defines portable tiers and the plan/implement handoff
