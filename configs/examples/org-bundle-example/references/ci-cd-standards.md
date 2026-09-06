# CI/CD Standards

Load this reference when changing a build, test, deployment, or release workflow.

## Required gates

- Run validation, lint, build, and tests before integration.
- Keep required branch checks stable so protection rules do not depend on matrix job names.
- Cache immutable dependencies and cancel superseded runs where the CI provider supports it.
- Run expensive operating-system or matrix coverage at merge or release boundaries unless the change is platform-sensitive.

## Release boundary

Publish only after the integration branch is green. Derive release notes from the actual diff and obtain approval before tagging or publishing.
