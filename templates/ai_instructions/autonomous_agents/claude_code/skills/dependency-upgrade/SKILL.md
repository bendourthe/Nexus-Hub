---
template_id: SKILL
template_name: Dependency-Upgrade - Generic
version: 1.0.0
last_updated: 2025-12-03
language: Generic
category: skills
phase: dependency-upgrade
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tags:
  - skills
  - generic
---
# dependency-upgrade

---
category: migration-refactoring
priority: MEDIUM
languages: [python, javascript, typescript, java, csharp, go, rust]
requires_user_input: true
estimated_duration: 1-4 hours
---

## Overview

Safely upgrade project dependencies to newer versions, handling breaking changes, testing compatibility, and maintaining stability throughout the upgrade process.

## When to Use This Skill

- Security vulnerabilities in current dependencies
- Need access to new features in updated packages
- Dependencies reaching end-of-life
- Performance improvements in newer versions
- Compatibility issues with other updated packages
- Regular maintenance and keeping dependencies current

## Prerequisites

- Comprehensive test suite
- Version control with clean working directory
- Backup or ability to rollback
- Understanding of semantic versioning
- CI/CD pipeline for automated testing
- Staging environment for validation

## Step-by-Step Instructions

### Phase 1: Assessment

#### Step 1: Audit Current Dependencies

**Python:**

```bash
# List all installed packages
pip list

# Show outdated packages
pip list --outdated

# Check for security vulnerabilities
pip-audit

# Generate current requirements
pip freeze > requirements.txt.backup

# Use pip-outdated for detailed analysis
pip install pip-outdated
pip-outdated
```

**JavaScript/TypeScript:**

```bash
# List outdated packages
npm outdated

# Check for security vulnerabilities
npm audit

# Check for major updates
npx npm-check-updates

# Detailed dependency tree
npm list --all
```

**Create dependency audit report:**

```markdown
## Dependency Audit Report
Date: 2025-10-21

### Critical Updates (Security)
| Package | Current | Latest | Severity | CVE |
|---------|---------|--------|----------|-----|
| requests | 2.25.0 | 2.31.0 | HIGH | CVE-2023-32681 |
| pillow | 8.3.0 | 10.0.0 | CRITICAL | CVE-2023-44271 |

### Major Version Updates
| Package | Current | Latest | Breaking Changes |
|---------|---------|--------|------------------|
| fastapi | 0.68.0 | 0.104.0 | Yes - Router changes |
| sqlalchemy | 1.4.0 | 2.0.0 | Yes - API changes |

### Minor/Patch Updates
| Package | Current | Latest | Risk Level |
|---------|---------|--------|------------|
| pydantic | 1.10.0 | 1.10.13 | LOW |
| uvicorn | 0.17.0 | 0.24.0 | LOW |

### Deprecated Packages
| Package | Status | Replacement |
|---------|--------|-------------|
| flask-cors | Deprecated | flask-cors-extended |

**Recommendation Priority:**
1. Security updates (IMMEDIATE)
2. Deprecated packages (HIGH)
3. Major versions (MEDIUM - test thoroughly)
4. Minor/patch versions (LOW - low risk)
```

#### Step 2: Check Breaking Changes

**Research each major update:**

```python
# check_breaking_changes.py
"""
Script to check for breaking changes in dependency updates.
"""
import requests
from packaging import version

def check_changelog(package_name, current_version, target_version):
    """
    Check changelog and release notes for breaking changes.
    """
    print(f"\n{package_name}: {current_version} -> {target_version}")
    print("=" * 60)

    # Get release notes from PyPI
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    data = response.json()

    # Parse versions between current and target
    releases = []
    for ver in data['releases'].keys():
        if version.parse(current_version) < version.parse(ver) <= version.parse(target_version):
            releases.append(ver)

    releases.sort(key=lambda x: version.parse(x))

    print(f"\nVersions to review: {len(releases)}")
    for rel in releases:
        release_info = data['releases'][rel]
        if release_info:
            upload_time = release_info[0]['upload_time']
            print(f"  - {rel} (released {upload_time[:10]})")

    # Check for major version bump
    current_major = version.parse(current_version).major
    target_major = version.parse(target_version).major

    if target_major > current_major:
        print(f"\n⚠️  MAJOR VERSION CHANGE: {current_major}.x -> {target_major}.x")
        print("   Review migration guide and breaking changes carefully!")

    print(f"\nChangelog: https://github.com/search?q=repo:org/{package_name}+releases")
    print(f"Migration guide: https://{package_name}.readthedocs.io/en/latest/migration/")

# Example usage
packages_to_check = [
    ('fastapi', '0.68.0', '0.104.0'),
    ('sqlalchemy', '1.4.0', '2.0.0'),
    ('pydantic', '1.10.0', '2.4.0')
]

for pkg, current, target in packages_to_check:
    check_changelog(pkg, current, target)
```

### Phase 2: Upgrade Strategy

#### Step 3: Plan Upgrade Approach

**Strategy 1: Incremental upgrades (recommended)**

```bash
# Upgrade one package at a time
# Test after each upgrade

# 1. Upgrade security-critical packages first
pip install --upgrade requests==2.31.0
python -m pytest tests/
git commit -m "Security: Upgrade requests to 2.31.0"

# 2. Upgrade minor/patch versions
pip install --upgrade pydantic==1.10.13
python -m pytest tests/
git commit -m "Upgrade pydantic to 1.10.13"

# 3. Upgrade major versions (one at a time)
pip install --upgrade sqlalchemy==2.0.0
# Fix breaking changes
python -m pytest tests/
git commit -m "Upgrade SQLAlchemy to 2.0.0"
```

**Strategy 2: Batch minor updates**

```bash
# Update all minor/patch versions at once
pip install --upgrade $(pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1)

# Test everything
python -m pytest tests/ -v

# If tests fail, identify problematic package
# Rollback and upgrade individually
```

**Strategy 3: Use dependency management tools**

```python
# pyproject.toml with flexible versioning
[project]
dependencies = [
    "fastapi>=0.68.0,<1.0.0",      # Allow minor updates
    "pydantic>=1.10.0,<2.0.0",      # Pin major version
    "requests>=2.31.0",             # Minimum version for security
]

# Or use poetry for better dependency resolution
[tool.poetry.dependencies]
python = "^3.9"
fastapi = "^0.104.0"  # ^0.104.0 means >=0.104.0,<1.0.0
pydantic = "^2.4.0"
```

#### Step 4: Handle Breaking Changes

**Example: SQLAlchemy 1.4 → 2.0 migration**

```python
# BEFORE (SQLAlchemy 1.4)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://localhost/mydb')
Session = sessionmaker(bind=engine)
session = Session()

# Query using legacy API
users = session.query(User).filter(User.age > 18).all()

# Execute raw SQL
result = session.execute("SELECT * FROM users WHERE age > :age", {"age": 18})

# AFTER (SQLAlchemy 2.0)
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine('postgresql://localhost/mydb')
SessionLocal = sessionmaker(bind=engine)

# Use context manager
with Session(engine) as session:
    # Query using 2.0 style select
    stmt = select(User).where(User.age > 18)
    users = session.execute(stmt).scalars().all()

    # Execute with text()
    from sqlalchemy import text
    result = session.execute(
        text("SELECT * FROM users WHERE age > :age"),
        {"age": 18}
    )

# Migration helper for gradual transition
from sqlalchemy.orm import Session as LegacySession

# Enable future mode in 1.4 to prepare for 2.0
engine = create_engine('postgresql://localhost/mydb', future=True)
```

**Example: Pydantic 1.x → 2.x migration**

```python
# BEFORE (Pydantic 1.x)
from pydantic import BaseModel, validator

class User(BaseModel):
    name: str
    age: int

    @validator('age')
    def age_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('age must be positive')
        return v

    class Config:
        orm_mode = True

# AFTER (Pydantic 2.x)
from pydantic import BaseModel, field_validator, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # replaces orm_mode

    name: str
    age: int

    @field_validator('age')
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError('age must be positive')
        return v

# Use bump-pydantic tool for automatic migration
# pip install bump-pydantic
# bump-pydantic src/
```

**Example: FastAPI major update**

```python
# BEFORE (FastAPI 0.68.0)
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

@router.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

app.include_router(router)

# AFTER (FastAPI 0.104.0) - mostly compatible
# Main changes are in dependencies and new features

from fastapi import FastAPI, APIRouter, Depends
from typing import Annotated  # Use Annotated for better type hints

app = FastAPI()
router = APIRouter()

async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

@router.get("/items/{item_id}")
async def read_item(
    item_id: int,
    token: Annotated[str, Depends(get_token_header)]
):
    return {"item_id": item_id}

app.include_router(router)
```

### Phase 3: Testing

#### Step 5: Comprehensive Testing

```python
# test_upgrade_compatibility.py
"""
Test suite for dependency upgrade compatibility.
"""
import pytest
import sys
import importlib

def test_package_imports():
    """Test that all required packages can be imported."""
    required_packages = [
        'fastapi',
        'pydantic',
        'sqlalchemy',
        'requests',
        'pytest'
    ]

    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError as e:
            pytest.fail(f"Failed to import {package}: {e}")

def test_package_versions():
    """Verify package versions meet minimum requirements."""
    from packaging import version

    version_requirements = {
        'fastapi': '0.104.0',
        'pydantic': '2.4.0',
        'sqlalchemy': '2.0.0'
    }

    for package, min_version in version_requirements.items():
        mod = importlib.import_module(package)
        actual_version = mod.__version__

        assert version.parse(actual_version) >= version.parse(min_version), \
            f"{package} version {actual_version} < required {min_version}"

def test_api_compatibility():
    """Test that API interfaces still work as expected."""
    from pydantic import BaseModel

    # Test Pydantic 2.x API
    class User(BaseModel):
        name: str
        age: int

    user = User(name="Alice", age=30)
    assert user.name == "Alice"
    assert user.age == 30

    # Test serialization
    user_dict = user.model_dump()  # Pydantic 2.x method
    assert user_dict == {"name": "Alice", "age": 30}

def test_database_operations():
    """Test SQLAlchemy 2.0 compatibility."""
    from sqlalchemy import create_engine, select, text
    from sqlalchemy.orm import Session

    engine = create_engine('sqlite:///:memory:')

    with Session(engine) as session:
        # Test text execution
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1

def test_backward_compatibility():
    """Ensure backward compatibility where expected."""
    # Test that old code patterns still work if compatibility mode enabled
    pass

# Run upgrade test suite
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**Integration testing:**

```bash
# Run full test suite
python -m pytest tests/ -v --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v

# Test in isolated environment
python -m venv test_venv
source test_venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/

# Performance regression testing
python -m pytest tests/performance/ --benchmark-only
```

### Phase 4: Deployment

#### Step 6: Staged Rollout

```yaml
# .github/workflows/dependency-upgrade.yml
name: Dependency Upgrade

on:
  pull_request:
    paths:
      - 'requirements.txt'
      - 'package.json'
      - 'pyproject.toml'

jobs:
  test-upgrade:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml

    - name: Check code style
      run: |
        pip install black flake8
        black --check src/ tests/
        flake8 src/ tests/

    - name: Security scan
      run: |
        pip install bandit safety
        bandit -r src/
        safety check

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

**Deployment strategy:**

```bash
# 1. Deploy to development environment
git checkout development
git merge feature/upgrade-dependencies
# Deploy and test

# 2. Deploy to staging environment
git checkout staging
git merge development
# Deploy and test with production-like data

# 3. Canary deployment (if supported)
# Deploy to 10% of production servers
# Monitor error rates and performance

# 4. Full production deployment
git checkout main
git merge staging
# Deploy to all production servers

# 5. Monitor closely for 24-48 hours
# Watch error rates, performance metrics, user reports
```

#### Step 7: Rollback Plan

```bash
# Prepare rollback before upgrade
git tag pre-upgrade-backup

# Document current state
pip freeze > requirements.pre-upgrade.txt
npm list --json > package-lock.pre-upgrade.json

# If issues occur, rollback immediately
git revert HEAD
git push origin main

# Or use tag to rollback
git reset --hard pre-upgrade-backup
git push --force origin main

# Rollback database migrations if needed
alembic downgrade -1

# Notify team
echo "Rolled back dependency upgrade due to issues"
```

### Phase 5: Documentation

#### Step 8: Update Documentation

```markdown
# UPGRADE.md

## Dependency Upgrade - October 2025

### Summary
Upgraded critical dependencies to address security vulnerabilities and gain access to new features.

### Changes

#### Python Packages
| Package | Old Version | New Version | Reason |
|---------|-------------|-------------|--------|
| requests | 2.25.0 | 2.31.0 | Security (CVE-2023-32681) |
| sqlalchemy | 1.4.0 | 2.0.23 | New features, performance |
| pydantic | 1.10.0 | 2.4.2 | Type checking improvements |
| fastapi | 0.68.0 | 0.104.1 | Bug fixes, new features |

### Breaking Changes

#### SQLAlchemy 2.0
- `session.query()` deprecated, use `select()` instead
- `session.execute()` returns Result object
- Migration guide: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html

**Before:**
```python
users = session.query(User).filter(User.age > 18).all()
```

**After:**
```python
stmt = select(User).where(User.age > 18)
users = session.execute(stmt).scalars().all()
```

#### Pydantic 2.0
- `@validator` replaced with `@field_validator`
- `Config` class replaced with `model_config`
- `.dict()` method replaced with `.model_dump()`

**Before:**
```python
class User(BaseModel):
    name: str
    class Config:
        orm_mode = True
```

**After:**
```python
class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
```

### Migration Steps for Developers

1. Pull latest changes: `git pull origin main`
2. Update virtual environment: `pip install -r requirements.txt`
3. Run migrations: `alembic upgrade head`
4. Run tests: `pytest tests/ -v`
5. Update your code if using deprecated APIs

### Known Issues
- None reported

### Rollback Procedure
If critical issues occur:
```bash
git reset --hard pre-upgrade-backup
pip install -r requirements.pre-upgrade.txt
alembic downgrade -1
```

### Support
Contact: dev-team@company.com
Documentation: https://docs.company.com/dependency-upgrade-2025
```

## Expected Outcomes

After completing this upgrade:

1. **Security improved**
   - All known vulnerabilities patched
   - Dependencies up-to-date

2. **New features available**
   - Access to latest package features
   - Performance improvements

3. **Technical debt reduced**
   - Modern APIs and patterns
   - Better type checking

4. **Stability maintained**
   - All tests passing
   - No regressions introduced

## Success Criteria

- [ ] All dependencies upgraded to target versions
- [ ] Security vulnerabilities resolved
- [ ] All tests passing (100% pass rate)
- [ ] No performance regressions
- [ ] Breaking changes documented
- [ ] Team trained on new APIs
- [ ] Rollback plan documented and tested
- [ ] CI/CD pipeline updated
- [ ] Production deployment successful
- [ ] No increase in error rates post-deployment

## Common Pitfalls

1. **Upgrading too many packages at once**
   - Solution: Upgrade incrementally, test between changes

2. **Not reading changelogs**
   - Solution: Always review breaking changes before upgrading

3. **Insufficient testing**
   - Solution: Run full test suite, including integration tests

4. **No rollback plan**
   - Solution: Always have a tested rollback procedure

5. **Upgrading in production first**
   - Solution: Test in dev/staging before production

## Related Skills

- **migrate-python-2-to-3**: Python 2 to 3 migration
- **refactor-for-testability**: Improve code testability
- **setup-python-project**: Initialize Python projects
- **add-unit-tests**: Add comprehensive tests
- **database-migration**: Migrate databases

## Additional Resources

### Tools
- **Python**: pip-audit, pip-outdated, dependabot
- **JavaScript**: npm-check-updates, Snyk, Renovate
- **Java**: Maven Versions Plugin, Dependabot
- **General**: WhiteSource, Sonatype Nexus Lifecycle

### Semantic Versioning
- [Semantic Versioning 2.0.0](https://semver.org/)
- MAJOR.MINOR.PATCH format
- Breaking changes = major bump

### Security
- [CVE Database](https://cve.mitre.org/)
- [GitHub Advisory Database](https://github.com/advisories)
- [Snyk Vulnerability Database](https://security.snyk.io/)

### Best Practices
- Keep dependencies up-to-date regularly
- Use automated dependency updates (Dependabot/Renovate)
- Pin versions in production
- Use lock files (requirements.txt, package-lock.json)
- Test thoroughly before deploying

---

**Note**: Regular dependency maintenance (monthly/quarterly) is less risky than large infrequent upgrades. Consider automating minor/patch updates with Dependabot or Renovate.
