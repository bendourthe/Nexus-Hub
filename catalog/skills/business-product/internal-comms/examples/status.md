# Team Phoenix - Weekly Status, week of 2026-04-27

## TL;DR

Phoenix shipped the new ingest schema to staging and unblocked Aurora's Phase-3 cutover; downstream teams should plan their schema-consumer updates by 2026-05-08.

## Shipped

- New ingest event schema deployed to staging; consumer SDK v3.4 published (link).
- Idempotency keys on the retry handler; duplicate-row rate dropped to 0 in shadow.
- Per-tenant lag metric on the Aurora dashboard; on-call now reads it in <60s.

## In Flight

- Production cutover for the new ingest schema, ETA 2026-05-06.
- Integration tests for the retry handler (coverage 62% currently, target 85% by EOW).
- SEV2 post-mortem from the 2026-04-23 Apex Logistics incident; first draft circulating internally.
- Schema-registry credential rotation cadence; coordinating with SRE on-call this week.

## Risks and Asks

- Cutover window 2026-05-06 conflicts with the marketing launch; need exec sign-off by 2026-05-01 or we slip the cutover.
- Downstream consumers on schema v2 must update before 2026-05-15 (deprecation date); please confirm your team's migration plan in #aurora-schema by 2026-05-03.

## Metrics

| Metric | Last week | This week | Trend |
|---|---|---|---|
| Ingest p99 lag (s) | 18 | 12 | down |
| Duplicate-row rate (per million) | 47 | 0 | down |
| On-call pages | 4 | 1 | down |
