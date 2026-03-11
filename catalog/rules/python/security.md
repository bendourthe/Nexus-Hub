---
title: Python Security Rules
category: python
priority: critical
---

# Python Security Rules

## Input Validation

- Validate all external input (HTTP requests, CLI args, file contents, environment variables) at the system boundary using Pydantic or a dedicated validation library.
- Never use `eval()`, `exec()`, or `compile()` on user-supplied input.
- Sanitize file paths with `pathlib.Path.resolve()` and verify they remain within an expected root to prevent path traversal.

## SQL and Database

- Always use parameterized queries or ORM methods. Never concatenate user input into SQL strings.
- SQLAlchemy: use `text()` with bound parameters, never raw f-strings in queries.
- Django ORM: use `.filter(field=value)` not `.extra(where=[user_input])`.

## Secrets and Configuration

- Load secrets from environment variables using `python-environ`, `pydantic-settings`, or `os.environ`. Never hardcode secrets in source files.
- Do not log secrets, tokens, or PII. Sanitize log messages before emitting them.
- Rotate secrets immediately if accidentally committed; invalidate compromised tokens at the source.

## Dependency Security

- Pin all dependencies in `requirements.txt` or `pyproject.toml` with exact versions in production.
- Run `pip audit` or `safety check` in CI to detect known CVEs.
- Review transitive dependencies before adding a new package.

## Deserialization

- Never use `pickle.loads()` on data from untrusted sources. Prefer JSON, MessagePack, or Protocol Buffers.
- When using `yaml.load()`, always pass `Loader=yaml.SafeLoader` to prevent arbitrary code execution.

## HTTP and Network

- Use `httpx` or `requests` with timeouts on every call; never make unbounded network requests.
- Validate and whitelist URLs before making outbound requests to prevent SSRF.
- Set `verify=True` (the default) on all HTTPS requests; never disable certificate verification in production.
