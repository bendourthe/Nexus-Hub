# Decision: Record prompting-claim evidence scope without family inheritance

Status: implemented - source applicability is explicit while model profiles remain direct lookups
Date: 2026-09-27
Author: Ben Dourthe
Template: Nygard

## Problem

The prompting-profile index stores claims under model IDs because the research and installed-reference readers select one model at a time. The v4.9 sweep recorded Google Gemini 3 family guidance and Cursor Start-plan constraints under each applicable model. A reader comparing those entries could mistake repeated source-level facts for separate model-specific findings.

The existing `scope` field does not answer that question. It controls whether a claim may leave the profile layer for a shared catalog body; both a model-specific instruction and a family-wide fact can correctly have `scope: model-specific` when neither is safe to publish for every platform. Free-text notes explain the distinction to a careful reader, but tools cannot reliably classify their wording.

The source set is small and mixed. Gemini repeats one positive family recommendation across four models; Cursor's Start-plan facts vary by model, and its negative statements establish only what the cited pricing page omits. A shared family store would need inheritance, precedence, and writer behavior for claims that are not all interchangeable.

## Decision

Add optional `evidence_scope` to each claim in schema 1.2.0, with `model`, `model-family`, `provider-plan`, and `cited-page` values. The field describes the applicability of the cited evidence, not the routing permission represented by `scope`. The validator rejects other values, the deterministic writer preserves it, and generated per-model mirrors display it. Absence means the evidence scope was not recorded, not that the source was model-specific.

Annotate the already-reviewed Cursor, Gemini, and GPT-5.6 family or plan claims through the writer without refreshing the roster or per-model verification dates. Per-model lookup remains unchanged. This decision does not add a family inheritance tier, assert that a cited-page negative result covers all vendor documentation, or qualify a live model roster.

## Alternatives considered

- **Keep prose notes only.** This changes no schema and keeps the current mirrors short, but it leaves source applicability invisible to machine readers and allows two differently worded notes to express the same scope without a checked contract.
- **Move shared claims into family or plan entries.** This removes duplicated text and creates one update point, but it requires new inheritance and conflict rules in the writer, validator, research planner, and installed readers. Cursor's differing plan constraints and page-limited negatives would still need model-level exceptions.
- **Add optional evidence scope to model claims.** This preserves direct lookup and existing consumers while making the source boundary testable. It retains some duplicate claim text and requires future authors to classify source applicability when they use the field.

## Consequences

- A profile mirror can distinguish model evidence from family guidance, plan constraints, and a negative result limited to one page without treating those as separate per-model experiments.
- Existing indexes and readers continue to work because the field is optional and per-model claims remain in place. Writers that know schema 1.2.0 can round-trip the new metadata; older strict validators must be upgraded with the index.
- The field does not prove the source is current or that a family claim applies to an unlisted future model. New models still need source review and a fresh roster qualification.

## Related

- [v4.9 WN-1](../../../archives/v4/v4.9/known-gaps.md) - the source-scope warning this decision addresses
- [Prompting profile schema](../../../../catalog/skills/ai-development/model-prompting-research/references/schema.md) - the versioned claim contract
