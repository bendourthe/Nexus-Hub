### Step 6: Manage Secrets and Configuration

A platform-grade secrets strategy ensures that no team stores credentials in Git, environment variables are managed consistently across environments, and configuration promotion from dev to production is auditable and safe.

**HashiCorp Vault Integration with Kubernetes**:

```hcl
# vault/terraform/kubernetes-auth.tf
# Configure Vault Kubernetes auth method
resource "vault_auth_backend" "kubernetes" {
  type = "kubernetes"
  path = "kubernetes/production"
}

resource "vault_kubernetes_auth_backend_config" "production" {
  backend            = vault_auth_backend.kubernetes.path
  kubernetes_host    = var.kubernetes_api_url
  kubernetes_ca_cert = var.kubernetes_ca_cert
}

# Create a policy for the payment service
resource "vault_policy" "payment_service" {
  name = "payment-service"
  policy = <<-EOT
    path "secret/data/payment-service/*" {
      capabilities = ["read"]
    }
    path "database/creds/payment-service-readonly" {
      capabilities = ["read"]
    }
    path "transit/encrypt/payment-service" {
      capabilities = ["update"]
    }
    path "transit/decrypt/payment-service" {
      capabilities = ["update"]
    }
  EOT
}

# Bind the Kubernetes service account to the Vault policy
resource "vault_kubernetes_auth_backend_role" "payment_service" {
  backend                          = vault_auth_backend.kubernetes.path
  role_name                        = "payment-service"
  bound_service_account_names      = ["payment-service"]
  bound_service_account_namespaces = ["payments"]
  token_policies                   = [vault_policy.payment_service.name]
  token_ttl                        = 3600
  token_max_ttl                    = 86400
}
```

**External Secrets Operator Configuration**:

```yaml
# external-secrets/cluster-secret-store.yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.internal.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes/production"
          role: "external-secrets"
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets
---
# external-secrets/payment-service-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: payment-service-secrets
  namespace: payments
spec:
  refreshInterval: 5m
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: payment-service-secrets
    creationPolicy: Owner
    template:
      engineVersion: v2
      data:
        DATABASE_URL: "postgresql://{{ .db_username }}:{{ .db_password }}@payments-db:5432/payments?sslmode=require"
        STRIPE_API_KEY: "{{ .stripe_key }}"
  data:
    - secretKey: db_username
      remoteRef:
        key: secret/data/payment-service/database
        property: username
    - secretKey: db_password
      remoteRef:
        key: secret/data/payment-service/database
        property: password
    - secretKey: stripe_key
      remoteRef:
        key: secret/data/payment-service/stripe
        property: api_key
```

**Environment Promotion Pattern (Config-as-Code)**:

```
config/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── configmap.yaml
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   ├── configmap-patch.yaml    # DEV-specific config
│   │   └── replicas-patch.yaml     # replicas: 1
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   ├── configmap-patch.yaml    # STAGING-specific config
│   │   └── replicas-patch.yaml     # replicas: 2
│   └── production/
│       ├── kustomization.yaml
│       ├── configmap-patch.yaml    # PROD-specific config
│       ├── replicas-patch.yaml     # replicas: 3, minAvailable: 2
│       └── hpa-patch.yaml          # autoscaling enabled
```

```yaml
# config/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: payments
resources:
  - ../../base
patches:
  - path: configmap-patch.yaml
  - path: replicas-patch.yaml
  - path: hpa-patch.yaml
configMapGenerator:
  - name: payment-service-config
    behavior: merge
    literals:
      - LOG_LEVEL=warn
      - ENABLE_DEBUG_ENDPOINTS=false
      - RATE_LIMIT_RPS=1000
      - CACHE_TTL_SECONDS=300
```

**Sealed Secrets for GitOps**:

```yaml
# Encrypted secret safe to commit to Git
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: payment-service-sealed
  namespace: payments
spec:
  encryptedData:
    STRIPE_KEY: AgBy3i4OJSWK+PiTySYZZA9rO...truncated
    DB_PASSWORD: AgCtr8cVnFlSh2+PjGMDwE4O...truncated
  template:
    metadata:
      name: payment-service-secrets
      namespace: payments
    type: Opaque
```

Sealed secrets allow you to store encrypted secrets in Git alongside application manifests. The Sealed Secrets controller running in the cluster holds the private key and decrypts them at deploy time. This is ideal for GitOps workflows where all configuration (including secrets) should be version-controlled.
