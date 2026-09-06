### Step 4: Configure Commit Message Validation

#### Conventional Commits Standard

**Format**: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat(auth): add OAuth2 authentication
fix(api): resolve null pointer exception in user endpoint
docs(readme): update installation instructions
test(user): add unit tests for user service
```

#### Using commitlint

```bash
# Install commitlint
npm install --save-dev @commitlint/cli @commitlint/config-conventional

# Create configuration
echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js

# Install commit-msg hook
npx husky add .husky/commit-msg 'npx --no -- commitlint --edit $1'
```

**commitlint.config.js** (custom rules):

```javascript
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'fix',
        'docs',
        'style',
        'refactor',
        'test',
        'chore',
        'revert'
      ]
    ],
    'subject-case': [2, 'never', ['upper-case']],
    'subject-max-length': [2, 'always', 100],
    'body-max-line-length': [2, 'always', 200]
  }
};
```

#### Using Pre-commit Framework

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: []
```

**Install commit-msg hook**:

```bash
pre-commit install --hook-type commit-msg
```
