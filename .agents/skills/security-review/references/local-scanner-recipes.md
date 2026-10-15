# Local Scanner Recipes

Optional local scanners for application static analysis and secret scanning. This file is the recipe owner for Semgrep and gitleaks. It does not install tools, fetch hosted rulesets, or print secret values.

Use these recipes when `security-review` runs a full security-audit workflow (schema v2). A focused review may skip them only with an explicit scoped-coverage statement.

## Shared rules

1. Discover the tool with a local command (`semgrep --version`, `gitleaks version`, or the platform equivalent). If the binary is absent, record `UNAVAILABLE` and stop. Never auto-install. Never switch to a hosted scanning service.
2. Prefer a repository-provided config (for example `.semgrep.yml`, `.semgrep/`, `.gitleaks.toml`) over implicit default rules.
3. If a repository config or ruleset flag would fetch rules over the network, disclose that outbound fetch and obtain authorization before running. If authorization is declined, record `DECLINED` with that reason.
4. Record `scanner_version`, exact `command`, `target_scope` (paths plus fingerprint), `config_fingerprint`, integer `exit_code`, timestamps, and `artifact_path`.
5. Capture scanner output to a local artifact. Do not paste raw secret matches into the report, chat, or commit.

## Semgrep (application SAST)

Semgrep owns local static analysis for this workflow. It is applicable when the target contains source the repository config or a locally available ruleset can parse (commonly Python, JavaScript/TypeScript, Go, Java, or similar).

Discovery:

```bash
semgrep --version
```

If missing, write a `UNAVAILABLE` receipt with applicability evidence (the languages or files that made it applicable) and do not install it.

Run only against the recorded target scope. Prefer `--config` pointing at a repository file. Write JSON or SARIF to `artifact_path`. A non-zero exit that still produced an artifact is `FAILED` only when the tool did not complete; findings in a completed run belong in the findings list, not in the receipt state.

Do not pass a hosted policy identifier that silently downloads rules. If the user explicitly authorizes a named local pack already on disk, record that path in `config_fingerprint`.

## gitleaks (secrets)

gitleaks owns secrets scanning for this workflow. It is applicable when the requested scope is a git working tree, an explicit path set, or git history.

Discovery:

```bash
gitleaks version
```

If missing, write `UNAVAILABLE`. Never auto-install and never add gitleaks as a repository dependency from this recipe.

Record the exact scope: working tree, staged files, or history range. A history-wide scan is a different `target_scope` from a working-tree scan. Prefer `.gitleaks.toml` when present.

Redaction is mandatory. The report and any pasted output may include file paths, line numbers, rule IDs, and commit SHAs. They must not include matched secret values, decoded tokens, or private key bodies. Replace any leaked value in captured artifacts with `[REDACTED]` before the artifact is cited.

`pre-commit-checklist` may point at gitleaks as a fast hook. Full repository or history audit scope, and the schema-v2 receipt, stay with `security-review`.
