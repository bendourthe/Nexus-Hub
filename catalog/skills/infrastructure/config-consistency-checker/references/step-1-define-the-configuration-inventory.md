### Step 1: Define the Configuration Inventory

Before checking consistency, document what configuration sources exist for each environment:

```yaml
# config-inventory.yaml
environments:
  dev:
    config_files:
      - path: config/dev.yaml
        format: yaml
      - path: .env.dev
        format: dotenv
    kubernetes:
      namespace: app-dev
      configmaps:
        - app-config
      secrets:
        - app-secrets
    secret_store:
      type: aws-secrets-manager
      prefix: dev/

  staging:
    config_files:
      - path: config/staging.yaml
        format: yaml
      - path: .env.staging
        format: dotenv
    kubernetes:
      namespace: app-staging
      configmaps:
        - app-config
      secrets:
        - app-secrets
    secret_store:
      type: aws-secrets-manager
      prefix: staging/

  production:
    config_files:
      - path: config/production.yaml
        format: yaml
      - path: .env.production
        format: dotenv
    kubernetes:
      namespace: app-production
      configmaps:
        - app-config
      secrets:
        - app-secrets
    secret_store:
      type: aws-secrets-manager
      prefix: prod/

schema:
  path: config/schema.json
  format: json-schema

ignore_keys:
  - DATABASE_HOST
  - DATABASE_PORT
  - LOG_LEVEL
  - REPLICA_COUNT
```
