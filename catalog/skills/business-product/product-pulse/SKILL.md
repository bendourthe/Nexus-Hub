---
name: product-pulse
description: Generate a time-windowed product-pulse report - usage, performance, errors, and open followups - from local data sources the user points the skill at. Make sure to use this skill whenever the user asks for a "product pulse", "usage report", "how is the product doing", "weekly product health", "monthly product report", "error trends", "performance over time", "product metrics summary", or wants a single-page timeline of product outcomes built from their own logs or exported analytics, even if they never say the word "pulse". The skill reads ONLY local files the user supplies and introduces no outbound call and no new data processor. SKIP, do NOT use for, live interactive dashboards with filtering (build a dashboard), real-time monitoring or alerting (use observability-setup), one-off ad-hoc log greps, or any flow that sends product data to an external analytics service.
summary_l0: "Generate a time-windowed product-pulse report from local usage, performance, and error data"
overview_l1: "This skill produces a single-page, time-windowed product-pulse report covering four outcome dimensions - usage, performance, errors, and open followups - rendered as a browseable timeline and saved to docs/pulse-reports/<window>.md. It reads ONLY the local data sources the user explicitly points it at (application or access log files, exported analytics CSV/JSON, local metrics dumps, a prior pulse report); it never reaches out to a network service and never introduces a new data processor or credential. The report normalizes each source into the four dimensions, computes simple counts and deltas versus the previous window when an earlier report exists, and surfaces a short Highlights block plus a prioritized followups list. Use it for recurring product-health summaries built from data the user already owns. Trigger phrases: product pulse, usage report, product health, weekly product report, monthly product report, error trends, performance over time, product metrics summary, product outcomes timeline."
---

# Product Pulse

Turn data the user already owns into a recurring, single-page read on how the product is doing. A pulse report is not a dashboard and not a monitoring system: it is a point-in-time, time-windowed narrative across four dimensions (usage, performance, errors, followups), written to a Markdown file the user can keep, diff, and skim as a timeline. Every input is a local file the user hands the skill; the skill adds no outbound call, no hosted analytics, and no new credential.

## When to Use This Skill

Use this skill when the user wants to:

- Produce a recurring product-health summary (weekly, monthly, per-release) from their own logs or exported analytics
- Roll local usage, performance, and error data up into one page they can share or archive
- See how the current window compares to the previous one (deltas, regressions, new error classes)
- Keep a browseable timeline of product outcomes under version control alongside the code

**Trigger phrases**: "product pulse", "usage report", "how is the product doing", "weekly product report", "monthly product report", "product health", "error trends", "performance over time", "product metrics summary", "product outcomes timeline".

**When NOT to use**:

- No telemetry is available - the skill has nothing to read. Stand up logging or analytics first (`infrastructure/observability-setup`), then return.
- The user wants a live, interactive dashboard with filtering controls - build a dashboard instead; a pulse report is a static snapshot.
- The user wants real-time monitoring or alerting on thresholds - that is `infrastructure/observability-setup` (metrics, traces, SLO alerts), not a periodic narrative.
- A one-off ad-hoc question over a single log file - just grep it; the pulse format is overhead for a single number.
- The data lives in a third-party analytics service and the user wants the skill to query it directly - this skill does not introduce outbound calls. The user must export the data locally first, then point the skill at the export.

## Instructions

The skill reads only the local paths the user provides. If at any step a required source is missing, report exactly which source is absent and what to export, and continue with the dimensions you can cover rather than failing the whole report.

### 1. Confirm the local data sources

In one consolidated turn (batch, not ping-pong), ask the user for:

1. The local data sources to read, by path - application/access logs, exported analytics (CSV/JSON), local metrics dumps, error logs. The skill reads only what is listed here.
2. The time window - a relative window (last 7 days, last 30 days, this release) or an explicit date range.
3. Whether a prior pulse report exists under `docs/pulse-reports/` to diff against (optional).

State explicitly, here and in the report header, that no source outside this list is read and that no data leaves the machine.

### 2. Derive the window slug

Compute a filesystem-safe `<window>` slug for the output filename: a relative window becomes a dated slug (e.g. `2026-05_last-30d`), an explicit range becomes `<start>_<end>` (e.g. `2026-05-01_2026-05-31`). The output path is `docs/pulse-reports/<window>.md`.

### 3. Normalize each source into the four dimensions

Parse each supplied source and bucket the facts into:

- **Usage** - active users / sessions / requests / feature invocations over the window; top entities by volume.
- **Performance** - latency (p50/p95/p99 where available), throughput, slow paths; only metrics the sources actually contain.
- **Errors** - error counts by class/code, new error classes versus the prior window, the top offenders.
- **Followups** - open items implied by the data (a spiking error, a degraded path, a dropped usage segment) plus any TODO/incident markers the user points at.

Only report dimensions the data supports. Mark a dimension `No data in supplied sources` rather than inventing numbers.

### 4. Compute deltas versus the previous window

If a prior `docs/pulse-reports/` report was supplied, compute the change for each headline number (absolute and percentage) and flag regressions. If no prior report exists, note that this is the baseline window.

### 5. Write the single-page report

Write `docs/pulse-reports/<window>.md` as a browseable timeline-style page. Recommended structure:

```markdown
# Product Pulse - <window>

**Generated**: <date>
**Sources**: <list of local files read>  (local-only; no data left the machine)
**Compared against**: <prior window or "baseline">

## Highlights

- <3-5 bullets: the most important movements this window>

## Usage

<counts, top entities, delta vs prior window>

## Performance

<latency / throughput figures present in the sources, delta vs prior window>

## Errors

<error classes by count, new classes flagged, delta vs prior window>

## Followups

1. <prioritized item> - why it matters, suggested owner/next step
2. ...
```

Follow the Markdown style guide (blank line around lists/tables/code/headings, ASCII-only English Markdown, single continuous lines).

### 6. Summarize in chat

Report the output path, the window, the headline numbers, and the top followup. Do not paste the whole report into chat - point the user at the file.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just have the skill hit the analytics API directly - it is faster" | This skill is local-only by contract. An outbound call introduces a new data processor and (usually) a credential, which is exactly what the MCP Registry Policy forbids for catalog content. The user exports the data locally, then the skill reads the export - the data-flow surface stays at zero. |
| "There's no prior report, so I'll skip the deltas section" | The first window is the baseline that every future delta is measured against. Skipping it means the next run has nothing to compare to. Write the baseline numbers explicitly and label the window as the baseline. |
| "One source is missing, so I'll abort the report" | A pulse with three of four dimensions covered is useful; a missing source is a followup, not a failure. Mark the absent dimension `No data in supplied sources`, name what to export, and ship the rest. |
| "I'll estimate the p95 latency since the log only has averages" | Reporting a percentile the source does not contain manufactures a number the user will act on. Report only metrics the sources actually carry, and list the missing metric as a followup. |
| "This is basically a dashboard, I'll add interactive filters" | A dashboard is a live, stateful surface; a pulse is a static, archivable snapshot the user diffs over time. Conflating them produces a half-built dashboard. If the user wants filtering, build a dashboard; if they want a recurring read they can keep in git, write the pulse. |
| "I'll write the report to the chat so the user sees it immediately" | The value is the persisted, diffable timeline under `docs/pulse-reports/`. A chat-only report cannot be compared next window and is lost when the session ends. Write the file; summarize in chat. |

## Verification

Binary checklist - each item must describe an observable artifact or state.

- [ ] `docs/pulse-reports/<window>.md` exists with a filesystem-safe `<window>` slug derived from the requested window.
- [ ] The report header lists every local source read and states that the report is local-only (no outbound call, no new data processor).
- [ ] All four dimension sections (Usage, Performance, Errors, Followups) are present; any dimension without data is explicitly marked `No data in supplied sources` rather than populated with invented numbers.
- [ ] When a prior report was supplied, each headline number shows a delta versus the previous window; when none was supplied, the window is labelled the baseline.
- [ ] The Followups section is a prioritized list with a why and a suggested next step per item.
- [ ] No network call was made: the skill read only the paths the user supplied and wrote only the report file (and nothing under any cache or temp dir that implies an upload).
- [ ] The report passes the Markdown style guide (blank line around lists/tables/code/headings, ASCII-only, single continuous lines per paragraph/bullet).

"The numbers look about right" is not a valid verification criterion - every reported figure must trace to a supplied source.

## Related Skills

- `infrastructure/observability-setup` - the upstream skill that stands up the logging, metrics, and tracing this skill reads from; use it first when no telemetry exists, and for real-time alerting (the pulse is periodic, not real-time).
- `business-product/product-manager` - consumes the pulse: the Followups and usage trends feed prioritization and now/next/later sequencing.
- `business-product/internal-comms` - turn a pulse window into a leadership update or weekly status; the pulse is the data, internal-comms is the audience-shaped message.
- `developer-experience/analysis-logic` - structured analytical presentation (decision matrices, data framing) for the deeper analysis a single pulse window may surface.
- `workflow/known-gaps-tracker` - record recurring followups that span multiple windows as tracked gaps rather than re-deriving them each pulse.
