# Cross-Provider Plan Routing Contract

**Version**: v3.15.9
**Status**: Normative for plans generated after v3.15.9 Phase 1
**Last updated**: 2026-08-03

## Purpose

Plan routing must survive a change of agentic platform and must not freeze a host-local model name into a long-lived plan. A generated plan therefore records generic capability intent in each phase and keeps concrete model names in one dated, cited map that is refreshed when `/plan` runs.

This contract applies to new plans. Historical plans retain their original format and remain valid inputs to `/implement`.

## Required Phase Columns

Every new `## Phases at a Glance` table MUST use these exact columns:

| Phase | Title | Outcome | Recommended model tier | Recommended effort level |
|-------|-------|---------|------------------------|--------------------------|
| 1 | Example phase | Example outcome | strong | high |

`Recommended model tier` MUST be exactly one of:

- `frontier`
- `strong`
- `standard`
- `fast`

`Recommended effort level` MUST be exactly one of:

- `low`
- `medium`
- `high`
- `max`

The two columns contain only generic values. Concrete model ids such as `gpt-5.6-sol`, `claude-opus-5`, or `gemini-3.6-flash` belong only in the Current model map.

## Required Per-Phase Fields

Every phase MUST repeat the recommendation in three separate fields immediately after its stability gate:

```markdown
**Recommended model tier**: strong
**Recommended effort level**: high
**Rationale**: The phase crosses several modules and requires careful integration reasoning.
```

The rationale explains the complexity assessment. It MUST NOT make a concrete provider model authoritative for the phase.

## Current Model Map

Every new plan MUST contain an H2 heading named exactly `## Current model map` before `## Phases at a Glance`.

The map MUST have this exact shape:

| Tier | Anthropic | OpenAI | Google | Cursor |
|------|-----------|--------|--------|--------|
| frontier | `<current-model-id>` | `<current-model-id>` | `<current-model-id>` | `<current-model-id>` |
| strong | `<current-model-id>` | `<current-model-id>` | `<current-model-id>` | `<current-model-id>` |
| standard | `<current-model-id>` | `<current-model-id>` | `<current-model-id>` | `<current-model-id>` |
| fast | `<current-model-id>` | `<current-model-id>` | `<current-model-id>` | `<current-model-id>` |

The map is a portability lookup, not a claim that every account or region can select every listed model. Provider access restrictions remain authoritative.

## Freshness and Sources

On every `/plan` invocation that produces a full plan, the planner MUST use web search and official provider documentation to refresh all 16 map cells. Host-platform enumeration MAY inform availability on the current host, but it MUST NOT limit the plan to that provider or replace the four-provider map.

A fresh map uses this status line:

```markdown
**Model map status**: fresh as of YYYY-MM-DD; sources cited below.
```

The plan MUST include a `### Model map sources` subsection with at least one public URL for each provider:

- Anthropic
- OpenAI
- Google
- Cursor

Prefer official model catalogs, release notes, and platform model-picker documentation. Search-result snippets are discovery evidence, not sufficient final citations when an official page is reachable.

## Offline Fallback

Network failure never blocks plan generation, but it must be visible. Use exactly one fallback.

### Dated Snapshot

When a bundled last-known map is available, retain its concrete cells and emit:

```markdown
**Model map status**: offline fallback; stale as of YYYY-MM-DD.
```

The date is the snapshot's verification date, not the current date. Keep the snapshot's source URLs in `### Model map sources`.

### No Usable Snapshot

When no verified snapshot is available, fill all 16 provider cells with `assess at implementation time` and emit:

```markdown
**Model map status**: unavailable; assess at implementation time.
```

Never invent a model id, silently reuse an undated map, or collapse the map to the current host provider.

## Implementation-Time Reconfirmation

`/implement` reads the target phase's generic tier and effort, refreshes or revalidates the Current model map when web access is available, selects the matching cell for the user's implementation provider, and then checks that model against the provider's current platform surface. If the selected model is unavailable, `/implement` uses the nearest available model at the same or stronger tier. It never silently downshifts.

Direct `/route` switching remains host-native: it enumerates and switches only models that the current platform can actually use. The plan map supplies cross-provider intent; it does not grant cross-provider switching capability.

## Before and After

### Rejected Host-Locked Format

```markdown
| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Design | Contract approved | `gpt-5.5`, xhigh |

**Recommended model**: `gpt-5.5`, xhigh.
```

This format goes stale and is unusable when implementation moves from Codex to Claude Code, Gemini, or Cursor.

### Required Cross-Provider Format

```markdown
## Current model map

**Model map status**: fresh as of 2026-08-03; sources cited below.

| Tier | Anthropic | OpenAI | Google | Cursor |
|------|-----------|--------|--------|--------|
| frontier | `claude-fable-5` | `gpt-5.6-sol` | `gemini-3.1-pro` | `cursor-grok-4.5-high` |
| strong | `claude-opus-5` | `gpt-5.6-terra` | `gemini-3.6-flash` | `cursor-grok-4.5` |
| standard | `claude-sonnet-5` | `gpt-5.5` | `gemini-3.5-flash` | `composer-2.5` |
| fast | `claude-haiku-4-5` | `gpt-5.6-luna` | `gemini-3.5-flash-lite` | `composer-2.5-fast` |

## Phases at a Glance

| Phase | Title | Outcome | Recommended model tier | Recommended effort level |
|-------|-------|---------|------------------------|--------------------------|
| 1 | Design | Contract approved | frontier | max |

## Phase 1: Design

**Goal**: Approve the contract.
**Prerequisites**: None.
**Stability Gate**: Contract tests pass.
**Recommended model tier**: frontier
**Recommended effort level**: max
**Rationale**: The contract controls every later planning and implementation phase.
```

The concrete ids above are examples, not a permanent catalog. `/plan` replaces them with the websearch-verified current map.

## Verification

- [ ] The glance table contains the two exact recommendation columns.
- [ ] Every phase uses an allowed tier and effort value in both the glance table and per-phase fields.
- [ ] `## Current model map` contains four provider columns and four tier rows.
- [ ] A fresh map has a dated status and at least one cited URL per provider.
- [ ] An offline map uses one exact fallback marker.
- [ ] Concrete model ids appear only in the map, not as authoritative phase recommendations.
- [ ] `/implement` preserves the tier or upshifts when the mapped model is unavailable.
