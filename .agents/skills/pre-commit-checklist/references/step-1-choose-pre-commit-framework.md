### Step 1: Choose Pre-Commit Framework

#### Option A: Pre-commit Framework (Recommended for Multi-language)

```bash
# Install pre-commit (Python-based but supports all languages)
pip install pre-commit

# Verify installation
pre-commit --version

# Create .pre-commit-config.yaml in repository root
pre-commit sample-config > .pre-commit-config.yaml

# Install hooks
pre-commit install

# Test on all files (optional)
pre-commit run --all-files
```

**Advantages**:
- Multi-language support
- Large plugin ecosystem
- Automatic tool installation
- Easy configuration
- Active community

#### Option B: Husky (JavaScript/TypeScript Projects)

```bash
# Install husky
npm install --save-dev husky

# Initialize husky
npx husky-init && npm install

# Add pre-commit hook
npx husky add .husky/pre-commit "npm test"

# Make executable
chmod +x .husky/pre-commit
```

#### Option C: Manual Git Hooks

```bash
# Navigate to git hooks directory
cd .git/hooks

# Create pre-commit hook
cat > pre-commit << 'EOF'
#!/bin/bash
echo "Running pre-commit checks..."

# Run linting
if ! npm run lint; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

# Run tests
if ! npm test; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "All checks passed!"
exit 0
EOF

# Make executable
chmod +x pre-commit
```
