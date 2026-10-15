# Incident 2026-04-23-0017 - Apex Logistics tenant ingest stalled for 47 minutes

## Summary

On 2026-04-23, between 14:12 and 14:59 UTC, ingest for the Apex Logistics tenant stalled at the schema-registry layer, causing 47 minutes of zero throughput for the tenant. Root cause: a credential rotation completed mid-batch, but the in-flight batch held a stale token and entered a retry loop the rate limiter did not break out of. The ingest path was restored after a manual force-rotation of the in-flight batch. No data was lost; replay completed by 16:24 UTC.

## Impact

- Users affected: Apex Logistics tenant (38% of total event volume).
- Duration: 14:12 - 14:59 UTC (47 minutes).
- Severity: SEV2.
- Detection: 14:18 UTC by per-tenant lag metric on the Aurora dashboard (time-to-detect 6 minutes).

## Timeline (UTC)

| Time | Event |
|---|---|
| 14:10 | Routine schema-registry credential rotation begins. |
| 14:12 | In-flight batch B-29841 enters retry loop with stale token. |
| 14:18 | Per-tenant lag metric crosses alert threshold; on-call paged. |
| 14:21 | On-call confirms incident; opens #incident-2026-04-23. |
| 14:30 | Theory 1 (downstream consumer slow) ruled out via consumer logs. |
| 14:39 | Theory 2 (rate limiter saturation) confirmed via stale-token trace in registry logs. |
| 14:46 | Manual force-rotation of batch B-29841 begins. |
| 14:59 | Ingest resumes at full throughput; alert clears. |
| 16:24 | Replay completes; no data loss confirmed. |

## Root Cause

The credential rotation runbook assumed in-flight batches would naturally drain before the rotation took effect, but the schema-registry's grace window (60s) is shorter than the retry handler's max backoff (300s). Batches that hit a 5xx during the rotation window stayed in retry past the grace, then re-authenticated with a stale token cached at batch-start time. The rate limiter's behavior on auth-failure was to back off, not break out, so the loop never escalated to a hard failure that would have triggered an alert directly.

Contributing: the per-tenant lag alert threshold was set at 5 minutes, which means time-to-detect was 6 minutes after the actual stall began. A tighter threshold would have detected sooner.

## What Went Well

- The per-tenant lag metric (shipped 2026-04-21, two days before the incident) was the primary detection signal; without it, time-to-detect would likely have been 20-30 minutes via downstream alerts.
- On-call communication in #incident-2026-04-23 was clear, time-stamped, and avoided speculation in the channel.
- Replay tooling worked end-to-end; no data was lost.

## What Went Wrong

- Time-to-detect 6 minutes is slow for a SEV2 with a known-good metric in place; alert threshold needs revisit.
- Theory 1 took 12 minutes to rule out because consumer logs were spread across three log destinations.
- Credential rotation runbook had no test for the "in-flight batch with stale token" case.

## Action Items

| Item | Owner | Due | Type |
|---|---|---|---|
| Lower per-tenant lag alert threshold from 5 min to 2 min. | SRE on-call lead | 2026-05-02 | detect |
| Update credential rotation runbook to drain in-flight batches before rotating. | Platform team | 2026-05-09 | prevent |
| Add break-out logic in retry handler when auth failure persists past grace window. | Phoenix team | 2026-05-16 | prevent |
| Consolidate consumer logs into single log destination. | Observability team | 2026-05-30 | respond |
| Schedule chaos test for credential-rotation-during-batch scenario. | SRE on-call lead | 2026-06-15 | prevent |
