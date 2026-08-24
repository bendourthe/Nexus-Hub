## Common Pitfalls and Solutions

### Pitfall 1: Hooks Too Slow

**Problem**: Pre-commit takes >30 seconds, frustrating developers.

**Solution**:
- Run only quick tests (< 5 seconds total)
- Use `lint-staged` to check only changed files
- Offload comprehensive checks to CI/CD
- Parallelize independent checks

### Pitfall 2: False Positives Block Commits

**Problem**: Legitimate code flagged incorrectly.

**Solution**:
- Tune linting rules to reduce noise
- Add exclusions for generated code
- Update secret detection baseline

```yaml
# Exclude generated files
- id: flake8
  exclude: ^(migrations/|generated/|.*_pb2\.py$)
```

### Pitfall 3: Developers Bypassing Hooks

**Problem**: Team uses `--no-verify` frequently.

**Solution**:
- Investigate why hooks are being bypassed
- Fix underlying issues (speed, false positives)
- Enforce checks in CI/CD (safety net)
- Educate team on importance

### Pitfall 4: Hooks Not Installed

**Problem**: New team members forget to install hooks.

**Solution**:
- Add setup to onboarding documentation
- Include in README prominently
- Add installation check to CI/CD
- Use `husky` which auto-installs for JavaScript projects
