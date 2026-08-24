### Step 2: Build Self-Service Infrastructure

Self-service infrastructure enables developers to provision resources without filing tickets or waiting for a platform team member. The key is packaging infrastructure modules as reusable, versioned products with clear interfaces, sensible defaults, and built-in compliance.

**Terraform Module as a Product**:

```hcl
# modules/rds-postgresql/main.tf
# A self-service PostgreSQL module with opinionated defaults

variable "name" {
  description = "Database instance name"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,28}$", var.name))
    error_message = "Name must be lowercase alphanumeric with hyphens, 3-29 characters."
  }
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "size" {
  description = "T-shirt size for the database (small, medium, large)"
  type        = string
  default     = "small"
  validation {
    condition     = contains(["small", "medium", "large"], var.size)
    error_message = "Size must be small, medium, or large."
  }
}

locals {
  instance_class = {
    small  = "db.t4g.medium"
    medium = "db.r6g.large"
    large  = "db.r6g.2xlarge"
  }
  storage_gb = {
    small  = 50
    medium = 200
    large  = 1000
  }
  # Enforce cost tags and compliance automatically
  required_tags = {
    ManagedBy   = "platform-team"
    Environment = var.environment
    Service     = var.name
    CostCenter  = var.cost_center
    Provisioner = "self-service-terraform"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "${var.name}-${var.environment}"
  engine         = "postgres"
  engine_version = "16.2"
  instance_class = local.instance_class[var.size]

  allocated_storage     = local.storage_gb[var.size]
  max_allocated_storage = local.storage_gb[var.size] * 2
  storage_encrypted     = true
  kms_key_id            = var.kms_key_arn

  multi_az               = var.environment == "production" ? true : false
  backup_retention_period = var.environment == "production" ? 30 : 7
  deletion_protection     = var.environment == "production" ? true : false

  db_subnet_group_name   = var.subnet_group_name
  vpc_security_group_ids = [aws_security_group.db.id]

  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = var.monitoring_role_arn

  tags = local.required_tags
}

output "connection_string_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the connection string"
  value       = aws_secretsmanager_secret.connection.arn
}

output "endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
}
```

**Crossplane Composition for Self-Service**:

```yaml
# crossplane/composition-postgresql.yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: postgresql.databases.platform.example.com
  labels:
    provider: aws
spec:
  compositeTypeRef:
    apiVersion: databases.platform.example.com/v1alpha1
    kind: PostgreSQLInstance
  resources:
    - name: rds-instance
      base:
        apiVersion: rds.aws.crossplane.io/v1alpha1
        kind: DBInstance
        spec:
          forProvider:
            engine: postgres
            engineVersion: "16"
            storageEncrypted: true
            publiclyAccessible: false
            performanceInsightsEnabled: true
          providerConfigRef:
            name: aws-provider
      patches:
        - fromFieldPath: spec.parameters.size
          toFieldPath: spec.forProvider.dbInstanceClass
          transforms:
            - type: map
              map:
                small: db.t4g.medium
                medium: db.r6g.large
                large: db.r6g.2xlarge
        - fromFieldPath: spec.parameters.environment
          toFieldPath: spec.forProvider.multiAZ
          transforms:
            - type: map
              map:
                dev: "false"
                staging: "false"
                production: "true"
    - name: connection-secret
      base:
        apiVersion: kubernetes.crossplane.io/v1alpha1
        kind: Object
        spec:
          forProvider:
            manifest:
              apiVersion: v1
              kind: Secret
              metadata:
                namespace: default
---
# Developer-facing claim (simple interface)
apiVersion: databases.platform.example.com/v1alpha1
kind: PostgreSQLInstance
metadata:
  name: orders-db
  namespace: team-orders
spec:
  parameters:
    size: medium
    environment: production
  compositionSelector:
    matchLabels:
      provider: aws
```

**PR-Based Self-Service Workflow**:

```
Developer creates PR          Platform CI validates         Merge triggers provisioning
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  infra-requests/  │         │  Terraform plan  │         │  Terraform apply │
│  orders-db.yaml  │────────►│  Policy check    │────────►│  Register in     │
│                  │         │  Cost estimate   │         │  service catalog │
└──────────────────┘         └──────────────────┘         └──────────────────┘
```

A PR-based workflow lets developers request infrastructure by committing a YAML or HCL file to a designated repository. Automated checks run `terraform plan`, validate against policies, estimate costs, and require platform team approval only when thresholds are exceeded.
