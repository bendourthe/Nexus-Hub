### Step 7: Reduce Toil Through Automation

Toil is repetitive, manual, automatable work that scales linearly with service growth. SRE teams should measure toil, prioritize automation by ROI, and build self-healing systems that handle routine operational tasks without human intervention.

**Toil Measurement Framework**:

| Characteristic | Question | Score (1-5) |
|---------------|----------|-------------|
| **Manual** | Does it require a human to perform? | |
| **Repetitive** | Does it recur regularly? | |
| **Automatable** | Could a machine do it? | |
| **Tactical** | Is it reactive rather than strategic? | |
| **No lasting value** | Does the system return to its previous state? | |
| **Scales linearly** | Does effort grow with service size? | |

```
Toil score = sum of all characteristics / 30
Toil > 0.5: High priority for automation
Toil 0.3-0.5: Medium priority
Toil < 0.3: Low priority or may not be true toil
```

**Automation ROI Calculation**:

```
Time saved per occurrence:     T_save = T_manual - T_automated
Occurrences per month:         N
Development cost (one-time):   T_dev (hours to build automation)
Maintenance cost (monthly):    T_maint (hours to maintain)

Monthly savings:   S_monthly = (T_save * N) - T_maint
Break-even point:  T_dev / S_monthly = months to ROI

Example: Certificate renewal
  T_manual = 2 hours (per renewal, including verification)
  T_automated = 0.1 hours (monitoring check)
  N = 12 per month (across all services)
  T_dev = 40 hours
  T_maint = 2 hours/month

  S_monthly = (1.9 * 12) - 2 = 20.8 hours/month
  Break-even = 40 / 20.8 = 1.9 months
```

**Self-Healing with Kubernetes Operators**:

```yaml
# self-healing-rules.yaml - Custom operator configuration
apiVersion: remediation.sre.io/v1
kind: RemediationRule
metadata:
  name: restart-on-oom
  namespace: production
spec:
  selector:
    matchLabels:
      app: checkout-api
  triggers:
    - type: event
      event:
        reason: OOMKilled
        count: 2
        window: 10m
  actions:
    - type: restart
      params:
        strategy: rolling
        maxUnavailable: 1
    - type: notify
      params:
        channel: "#sre-alerts"
        message: "Auto-restarted {{ .PodName }} after repeated OOM kills. Investigate memory leak."
    - type: ticket
      params:
        project: SRE
        type: bug
        title: "Repeated OOM kills on {{ .Deployment }}"
        labels: ["auto-generated", "memory-leak"]
---
apiVersion: remediation.sre.io/v1
kind: RemediationRule
metadata:
  name: scale-on-queue-depth
  namespace: production
spec:
  selector:
    matchLabels:
      app: order-processor
  triggers:
    - type: metric
      metric:
        query: "avg(sqs_queue_depth{queue='orders'})"
        threshold: 1000
        for: 5m
  actions:
    - type: scale
      params:
        replicas: "+50%"
        maxReplicas: 30
        cooldown: 10m
    - type: notify
      params:
        channel: "#sre-alerts"
        message: "Auto-scaled order-processor due to queue depth {{ .MetricValue }}. Current replicas: {{ .CurrentReplicas }} -> {{ .NewReplicas }}"
```

**GitOps for Infrastructure (Flux)**:

```yaml
# flux-system/kustomization.yaml - GitOps reconciliation
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: production-apps
  namespace: flux-system
spec:
  interval: 5m
  retryInterval: 2m
  timeout: 10m
  sourceRef:
    kind: GitRepository
    name: infrastructure
  path: ./clusters/production
  prune: true
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: checkout-api
      namespace: production
    - apiVersion: apps/v1
      kind: Deployment
      name: order-processor
      namespace: production
  patches:
    - patch: |
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: all
        spec:
          template:
            metadata:
              annotations:
                sidecar.istio.io/inject: "true"
      target:
        kind: Deployment
        namespace: production
---
# flux-system/alerts.yaml - GitOps failure notifications
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata:
  name: deployment-failures
  namespace: flux-system
spec:
  providerRef:
    name: slack-provider
  eventSeverity: error
  eventSources:
    - kind: Kustomization
      name: "*"
    - kind: HelmRelease
      name: "*"
  summary: "GitOps reconciliation failure detected"
```

**Runbook Automation Script**:

```bash
#!/usr/bin/env bash
set -euo pipefail

# runbook-db-failover.sh - Automated database failover runbook
# Executes pre-validated steps for RDS failover with safety checks

log_info()  { printf "[INFO]  %s\n" "$*" >&2; }
log_error() { printf "[ERROR] %s\n" "$*" >&2; }

readonly DB_CLUSTER="${1:?Usage: runbook-db-failover.sh <cluster-identifier>}"
readonly REGION="${AWS_REGION:-us-east-1}"
readonly MAX_WAIT_SECONDS=300

preflight_checks() {
    log_info "Running preflight checks"

    # Verify cluster exists and has a replica
    local reader_count
    reader_count=$(aws rds describe-db-clusters \
        --db-cluster-identifier "${DB_CLUSTER}" \
        --region "${REGION}" \
        --query "DBClusters[0].DBClusterMembers[?IsClusterWriter==\`false\`] | length(@)" \
        --output text)

    if [[ "${reader_count}" -lt 1 ]]; then
        log_error "No read replicas found for cluster ${DB_CLUSTER}. Cannot failover."
        return 1
    fi

    log_info "Found ${reader_count} read replica(s). Preflight passed."
    return 0
}

execute_failover() {
    log_info "Initiating failover for cluster ${DB_CLUSTER}"

    aws rds failover-db-cluster \
        --db-cluster-identifier "${DB_CLUSTER}" \
        --region "${REGION}"

    log_info "Failover initiated. Waiting for cluster to become available."

    local elapsed=0
    while [[ "${elapsed}" -lt "${MAX_WAIT_SECONDS}" ]]; do
        local status
        status=$(aws rds describe-db-clusters \
            --db-cluster-identifier "${DB_CLUSTER}" \
            --region "${REGION}" \
            --query "DBClusters[0].Status" \
            --output text)

        if [[ "${status}" == "available" ]]; then
            log_info "Cluster ${DB_CLUSTER} is available after failover"
            return 0
        fi

        log_info "Cluster status: ${status}. Waiting... (${elapsed}s / ${MAX_WAIT_SECONDS}s)"
        sleep 10
        elapsed=$((elapsed + 10))
    done

    log_error "Cluster did not become available within ${MAX_WAIT_SECONDS}s"
    return 1
}

verify_failover() {
    log_info "Verifying failover success"

    local new_writer
    new_writer=$(aws rds describe-db-clusters \
        --db-cluster-identifier "${DB_CLUSTER}" \
        --region "${REGION}" \
        --query "DBClusters[0].DBClusterMembers[?IsClusterWriter==\`true\`].DBInstanceIdentifier" \
        --output text)

    log_info "New writer instance: ${new_writer}"

    # Verify application connectivity
    log_info "Checking application health endpoint"
    local health_status
    health_status=$(curl --max-time 10 --connect-timeout 5 -s -o /dev/null -w "%{http_code}" \
        "https://api.example.com/health")

    if [[ "${health_status}" == "200" ]]; then
        log_info "Application health check passed (HTTP ${health_status})"
        return 0
    else
        log_error "Application health check failed (HTTP ${health_status})"
        return 1
    fi
}

main() {
    log_info "=== Database Failover Runbook ==="
    log_info "Cluster: ${DB_CLUSTER}"
    log_info "Region: ${REGION}"

    preflight_checks
    execute_failover
    verify_failover

    log_info "=== Failover Complete ==="
}

main
```
