# Project Aurora - Update, 2026-04-27

## Status: At risk

## Current Phase

Phase 2 - building the new ingest path; phase ends when staging cutover completes and integration tests cover 85% of the retry handler.

## Progress This Period

- Shipped per-tenant lag metric to the Aurora dashboard (detection-time win, see incident 2026-04-23-0017).
- Idempotency keys on the retry handler in production; duplicate-row rate at 0 in shadow.
- Closed Phase-3 acceptance criteria with the platform team.
- Coordinated SEV2 incident response on 2026-04-23 (full post-mortem available).

## Next Period

- Production cutover of new ingest schema, ETA 2026-05-06 (subject to leadership sign-off by 2026-05-01).
- Retry handler integration tests to 85% coverage by 2026-05-08.
- Phase 3 design review session, ETA 2026-05-12.

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Cutover window conflicts with marketing launch on 2026-05-06. | High | High | Exec sign-off requested by 2026-05-01; fallback slot 2026-05-13 reserved. |
| Schema-registry credential rotation cadence still weekly. | Med | Med | Ops session scheduled with SRE on-call this week to set monthly cadence. |
| Phase 3 design review has slipped twice. | Med | Med | Locked third slot; sponsor notified; further slip requires re-baseline. |

## Asks

- Sponsor sign-off on cutover window 2026-05-06 by EOD 2026-05-01.
- Confirm Phase 3 design review attendance by 2026-05-09 so we can lock the slot.

## Metrics

| Metric | Target | Current | Trend |
|---|---|---|---|
| Ingest p99 lag (s) | <= 10 | 12 | down |
| Duplicate-row rate (per million) | 0 | 0 | flat |
| Retry-handler test coverage (%) | 85 | 62 | up |
| On-call pages / week | <= 2 | 1 | down |
