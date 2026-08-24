### Step 7: Add Deployment Gates

**GitLab CI with Deployment Gate**:

```yaml
approve-production:
  stage: approve-production
  script:
    - echo "Production deployment approved by $GITLAB_USER_LOGIN"
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
      allow_failure: false

deploy-production:
  stage: deploy-production
  needs:
    - job: approve-production
    - job: verify-staging
  script:
    - ./scripts/deploy.sh production
  environment:
    name: production
    url: https://app.example.com
    on_stop: rollback-production
```

**GitHub Actions with Required Reviewers** (configured in repository settings, referenced in workflow):

```yaml
  deploy-production:
    needs: verify-staging
    runs-on: ubuntu-latest
    # The "production" environment must have required reviewers configured
    # in Settings > Environments > production > Required reviewers
    environment:
      name: production
      url: https://app.example.com
    steps:
      - name: Record approval metadata
        run: |
          echo "Deployment approved at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
          echo "Commit: ${{ github.sha }}"
          echo "Triggered by: ${{ github.actor }}"
```
