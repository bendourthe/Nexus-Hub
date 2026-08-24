### Step 3: Implement Secret Detection

**Prevent accidental credential commits:**

#### Using detect-secrets (Recommended)

```bash
# Install
pip install detect-secrets

# Generate baseline (initial scan)
detect-secrets scan > .secrets.baseline

# Add to pre-commit config
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package-lock.json
```

**Workflow**:
1. Initial scan creates baseline of existing "secrets" (false positives)
2. Pre-commit hook compares new changes against baseline
3. New secrets are blocked
4. Update baseline when adding legitimate patterns

**Update baseline** when adding legitimate patterns:

```bash
# Audit and update baseline
detect-secrets audit .secrets.baseline

# Mark false positives
# Press 'y' for true positives, 'n' for false positives

# Regenerate baseline
detect-secrets scan --baseline .secrets.baseline
```

**Common Secret Patterns to Detect**:

```regex
# API Keys
api[_-]?key.*["\'][a-zA-Z0-9]{32,}["\']

# AWS Keys
AKIA[0-9A-Z]{16}

# Private Keys
-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----

# Passwords
password.*["\'][^"\']{8,}["\']

# Tokens
(access|auth|bearer)[_-]?token.*["\'][a-zA-Z0-9\-_]{20,}["\']

# Database URLs with credentials
(postgres|mysql|mongodb):\/\/[^:]+:[^@]+@
```
