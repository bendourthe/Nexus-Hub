### Step 4: Measure Developer Experience

Platform engineering succeeds only when it measurably improves developer productivity and satisfaction. DORA metrics provide a baseline, but a complete picture requires supplementing them with qualitative signals like cognitive load and developer satisfaction.

**DORA Metrics Dashboard Configuration (Prometheus + Grafana)**:

```yaml
# prometheus-rules/dora-metrics.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: dora-metrics
  namespace: monitoring
spec:
  groups:
    - name: dora.deployment_frequency
      interval: 1h
      rules:
        - record: dora:deployment_frequency:rate7d
          expr: |
            sum(
              increase(deployment_total{environment="production"}[7d])
            ) by (team)
        - record: dora:deployment_frequency:daily
          expr: |
            sum(
              increase(deployment_total{environment="production"}[1d])
            ) by (team)

    - name: dora.lead_time
      interval: 1h
      rules:
        - record: dora:lead_time_seconds:p50
          expr: |
            histogram_quantile(0.5,
              sum(rate(lead_time_seconds_bucket{environment="production"}[7d])) by (le, team)
            )
        - record: dora:lead_time_seconds:p95
          expr: |
            histogram_quantile(0.95,
              sum(rate(lead_time_seconds_bucket{environment="production"}[7d])) by (le, team)
            )

    - name: dora.change_failure_rate
      interval: 1h
      rules:
        - record: dora:change_failure_rate:ratio7d
          expr: |
            sum(increase(deployment_rollback_total{environment="production"}[7d])) by (team)
            /
            sum(increase(deployment_total{environment="production"}[7d])) by (team)

    - name: dora.mttr
      interval: 1h
      rules:
        - record: dora:mttr_seconds:avg7d
          expr: |
            avg(incident_resolution_seconds{severity=~"sev1|sev2"}) by (team)
```

**DORA Maturity Levels**:

| Metric | Elite | High | Medium | Low |
|--------|-------|------|--------|-----|
| **Deployment Frequency** | On-demand (multiple/day) | Weekly-daily | Monthly-weekly | Monthly+ |
| **Lead Time for Changes** | < 1 hour | 1 day - 1 week | 1 week - 1 month | 1 month+ |
| **Change Failure Rate** | < 5% | 5-10% | 10-15% | 15%+ |
| **MTTR** | < 1 hour | < 1 day | < 1 week | 1 week+ |

**Developer Experience Survey Template**:

Track these dimensions quarterly to complement quantitative metrics:

- **Flow state**: "How often do you get into a state of deep focus during your workday?" (1-5 scale)
- **Feedback loops**: "How quickly can you see the result of a code change in a staging environment?" (minutes/hours/days)
- **Cognitive load**: "How much mental effort is required to deploy a change to production?" (1-5 scale)
- **Tool satisfaction**: "Rate your satisfaction with the following platform capabilities" (CI/CD, monitoring, provisioning, docs)
- **Toil assessment**: "What percentage of your time is spent on repetitive manual tasks?" (0-100%)
- **Golden path adoption**: "Do you use the platform-provided templates for new services?" (always/sometimes/never)

**Platform Adoption Tracking**:

```sql
-- Track golden path adoption over time
SELECT
  date_trunc('month', created_at) AS month,
  COUNT(*) FILTER (WHERE scaffold_template IS NOT NULL) AS golden_path_repos,
  COUNT(*) FILTER (WHERE scaffold_template IS NULL) AS custom_repos,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE scaffold_template IS NOT NULL)
    / COUNT(*), 1
  ) AS adoption_pct
FROM repositories
WHERE created_at >= NOW() - INTERVAL '12 months'
GROUP BY 1
ORDER BY 1;

-- Measure time-to-first-deploy for new services
SELECT
  scaffold_template,
  PERCENTILE_CONT(0.5) WITHIN GROUP (
    ORDER BY EXTRACT(EPOCH FROM first_deploy_at - created_at) / 3600
  ) AS median_hours_to_first_deploy
FROM repositories
WHERE first_deploy_at IS NOT NULL
GROUP BY scaffold_template;
```
