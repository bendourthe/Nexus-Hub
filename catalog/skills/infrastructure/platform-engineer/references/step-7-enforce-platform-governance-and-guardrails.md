### Step 7: Enforce Platform Governance and Guardrails

Governance ensures that self-service does not mean uncontrolled. Policy-as-code enables the platform team to enforce organizational standards (cost tagging, security baselines, resource limits) automatically, without bottlenecking teams with manual reviews.

**OPA/Gatekeeper Policy for Required Labels**:

```yaml
# policies/required-labels-template.yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: object
                properties:
                  key:
                    type: string
                  allowedRegex:
                    type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels

        violation[{"msg": msg}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_].key}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Missing required labels: %v", [missing])
        }

        violation[{"msg": msg}] {
          label := input.parameters.labels[_]
          label.allowedRegex != ""
          value := input.review.object.metadata.labels[label.key]
          not re_match(label.allowedRegex, value)
          msg := sprintf("Label '%v' value '%v' does not match pattern '%v'", [label.key, value, label.allowedRegex])
        }
---
# policies/required-labels-constraint.yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-platform-labels
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: ["apps"]
        kinds: ["Deployment", "StatefulSet", "DaemonSet"]
    excludedNamespaces:
      - kube-system
      - istio-system
      - monitoring
  parameters:
    labels:
      - key: "app.kubernetes.io/name"
      - key: "app.kubernetes.io/owner"
        allowedRegex: "^team-[a-z-]+$"
      - key: "platform.example.com/cost-center"
        allowedRegex: "^CC-[0-9]{4}$"
```

**Kyverno Policy for Resource Quotas**:

```yaml
# policies/kyverno-resource-limits.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
  annotations:
    policies.kyverno.io/title: Require Resource Limits
    policies.kyverno.io/description: >-
      All containers must specify CPU and memory requests and limits.
      This prevents noisy-neighbor issues and enables accurate capacity planning.
spec:
  validationFailureAction: Enforce
  background: true
  rules:
    - name: check-resource-limits
      match:
        any:
          - resources:
              kinds:
                - Pod
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - istio-system
      validate:
        message: >-
          All containers must have CPU and memory requests and limits defined.
          See https://platform.internal/docs/resource-limits for guidance.
        pattern:
          spec:
            containers:
              - resources:
                  requests:
                    memory: "?*"
                    cpu: "?*"
                  limits:
                    memory: "?*"
                    cpu: "?*"
    - name: enforce-max-limits
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: >-
          Container memory limit cannot exceed 8Gi and CPU limit cannot exceed 4 cores.
          Request a quota increase at https://platform.internal/quota-request if needed.
        deny:
          conditions:
            any:
              - key: "{{ request.object.spec.containers[].resources.limits.memory }}"
                operator: GreaterThan
                value: "8Gi"
              - key: "{{ request.object.spec.containers[].resources.limits.cpu }}"
                operator: GreaterThan
                value: "4"
```

**Cost Tagging Enforcement with Terraform Sentinel**:

```python
# sentinel/enforce-cost-tags.sentinel
import "tfplan/v2" as tfplan

required_tags = ["CostCenter", "Environment", "Owner", "ManagedBy"]

taggable_resources = [
  "aws_instance",
  "aws_s3_bucket",
  "aws_db_instance",
  "aws_rds_cluster",
  "aws_elasticache_cluster",
  "aws_eks_cluster",
  "aws_lambda_function",
]

all_taggable = filter tfplan.resource_changes as _, rc {
  rc.type in taggable_resources and
  rc.change.actions contains "create" or rc.change.actions contains "update"
}

deny_missing_tags = rule {
  all all_taggable as _, resource {
    all required_tags as tag {
      resource.change.after.tags contains tag
    }
  }
}

main = rule {
  deny_missing_tags
}
```

**Platform SLOs**:

Define SLOs for the platform itself so teams can depend on it with confidence:

| Platform Capability | SLO Target | Measurement |
|---------------------|-----------|-------------|
| **CI/CD pipeline availability** | 99.9% | Percentage of pipeline runs that start within 2 minutes of trigger |
| **Build time (p95)** | < 10 minutes | 95th percentile of build duration across all services |
| **Deployment success rate** | > 99% | Percentage of deployments that complete without rollback |
| **Secret rotation latency** | < 5 minutes | Time from Vault secret update to pod receiving new value |
| **Service catalog freshness** | < 15 minutes | Time from push to main until Backstage catalog reflects the change |
| **Self-service provisioning** | < 30 minutes | Time from PR merge to resource fully provisioned |

**Compliance Automation**:

```yaml
# compliance/cis-benchmark-scan.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cis-benchmark-scan
  namespace: platform-compliance
spec:
  schedule: "0 2 * * 1"  # Weekly Monday 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: compliance-scanner
          containers:
            - name: kube-bench
              image: aquasec/kube-bench:v0.7.0
              command: ["kube-bench", "run", "--json"]
              volumeMounts:
                - name: results
                  mountPath: /results
            - name: report-uploader
              image: platform/compliance-reporter:latest
              command: ["upload-results"]
              env:
                - name: REPORT_BUCKET
                  value: "s3://compliance-reports/kube-bench"
                - name: SLACK_CHANNEL
                  value: "#platform-compliance"
          volumes:
            - name: results
              emptyDir: {}
          restartPolicy: Never
```
