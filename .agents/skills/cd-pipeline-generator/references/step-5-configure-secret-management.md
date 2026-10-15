### Step 5: Configure Secret Management

**GitHub Actions with OIDC and AWS Secrets Manager**:

```yaml
  deploy-with-secrets:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Configure AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-deploy
          aws-region: us-east-1

      - name: Fetch deployment secrets
        run: |
          # Retrieve secrets and create Kubernetes secret
          DB_PASSWORD=$(aws secretsmanager get-secret-value \
            --secret-id prod/db-password \
            --query SecretString --output text)

          API_KEY=$(aws secretsmanager get-secret-value \
            --secret-id prod/api-key \
            --query SecretString --output text)

          kubectl create secret generic app-secrets \
            --from-literal=db-password="$DB_PASSWORD" \
            --from-literal=api-key="$API_KEY" \
            -n production \
            --dry-run=client -o yaml | kubectl apply -f -
```

**GitLab CI with Vault**:

```yaml
deploy-production:
  stage: deploy-production
  image: alpine/k8s:1.29.0
  id_tokens:
    VAULT_ID_TOKEN:
      aud: https://vault.example.com
  secrets:
    DATABASE_PASSWORD:
      vault: production/database/password@secret
      file: false
    API_KEY:
      vault: production/api/key@secret
      file: false
  script:
    - kubectl create secret generic app-secrets
        --from-literal=db-password="$DATABASE_PASSWORD"
        --from-literal=api-key="$API_KEY"
        -n $KUBE_NAMESPACE_PROD
        --dry-run=client -o yaml | kubectl apply -f -
    - kustomize build k8s/overlays/production | kubectl apply -f -
  environment:
    name: production
    url: https://app.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```
