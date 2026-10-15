# Apex Logistics ingestion vendor - Leadership Update, 2026-04-27

## Decision or Recommendation

Approve switching Apex Logistics from Vendor A to Vendor B for tenant ingestion, effective 2026-06-01.

## Context (60 seconds)

- Apex Logistics is our largest ingestion-volume tenant (38% of total events).
- Vendor A's contract auto-renews 2026-07-01 at a 22% price increase.
- Vendor B has been in shadow-mode evaluation since 2026-02-15; matches Vendor A on throughput and beats it on p99 latency by 35%.
- Our internal switching cost is approximately 3 engineer-weeks.

## Options

1. **Switch to Vendor B (recommended)** - one-time 3 engineer-week cost; ongoing cost down 18% vs. renewal price.
2. **Renew Vendor A at the 22% increase** - zero engineering cost; ongoing cost up 22%.
3. **Negotiate Vendor A renewal** - 1-2 engineer-weeks of vendor management; expected outcome 5-10% reduction off the increase.

## Recommendation

Option 1. Vendor B's shadow-mode results are stable across all measured tenants; switching cost is fully amortized within 14 months at current volume; our SRE oncall has reviewed Vendor B's incident-response posture and rated it equivalent. Tradeoff accepted: 3 weeks of engineering during Q2, displacing two lower-priority items in the Aurora backlog by approximately one sprint.

## Risks

- Vendor B's incident-response runbook is still untested in our environment; mitigation: 2-week parallel-run window before cutover, with rollback automation in place.
- Apex Logistics' security team must re-approve the new vendor; mitigation: review packet has been pre-circulated to Apex security; sign-off path opens 2026-05-04.

## Appendix

Linked: Vendor B shadow evaluation summary, throughput/latency comparison, contract redlines, SRE review notes.
