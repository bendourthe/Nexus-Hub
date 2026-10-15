---
name: config-consistency-checker
description: Detects configuration drift and inconsistencies across environments by comparing dev, staging, and production configs, validating schemas, and reporting missing keys and type mismatches. Use when auditing environment configurations, debugging environment-specific failures, or enforcing configuration standards.
summary_l0: "Detect configuration drift across environments with schema validation and diff reporting"
overview_l1: "This skill detects, reports, and resolves configuration drift across deployment environments by comparing configuration files, environment variables, secret references, and infrastructure parameters across dev, staging, and production. Use it when auditing environment configurations, debugging environment-specific failures, enforcing configuration standards, validating configuration schemas, or integrating configuration checks into CI/CD pipelines. Key capabilities include cross-environment comparison (YAML, JSON, TOML, .env, Kubernetes ConfigMaps), missing key detection, type mismatch identification, schema validation, secret reference verification, actionable diff reporting with resolution guidance, and CI/CD pipeline integration for continuous enforcement. The expected output is a configuration consistency report with identified discrepancies, severity levels, and resolution steps. Trigger phrases: configuration drift, config consistency, environment mismatch, missing config, config audit, environment variables, config comparison, schema validation."
---

# Config Consistency Checker

Specialized skill for detecting, reporting, and resolving configuration drift across deployment environments. This skill compares configuration files, environment variables, secret references, and infrastructure parameters across dev, staging, and production to find missing keys, type mismatches, value inconsistencies, and schema violations. It produces actionable reports that identify exactly what differs, why it matters, and how to resolve each discrepancy. The approach works with any configuration format (YAML, JSON, TOML, .env, Kubernetes ConfigMaps) and integrates into CI/CD pipelines for continuous enforcement.

## When to Use This Skill

Use this skill for:

- Comparing configuration across environments (dev, staging, production) to find drift
- Detecting missing configuration keys that exist in one environment but not another
- Validating configuration files against a JSON Schema or custom schema definition
- Finding type mismatches where the same key holds different data types across environments
- Auditing secret references to ensure all required secrets are defined in every environment
- Generating drift reports for compliance audits or change review processes
- Integrating configuration validation into CI/CD pipelines as a pre-deployment check
- Debugging failures that only occur in specific environments due to configuration differences
- Enforcing configuration standards across microservices in a platform team context

**Trigger phrases**: "config drift", "configuration consistency", "environment comparison", "config validation", "missing config", "config mismatch", "environment variables check", "config audit", "schema validation", "config diff", "environment parity"

## What This Skill Does

This skill follows a structured methodology for configuration consistency:

1. **Config Discovery**: Locates all configuration sources for each environment, including files (YAML, JSON, TOML, .env), environment variables, Kubernetes ConfigMaps/Secrets, cloud provider parameter stores, and CI/CD variables.

2. **Normalization**: Converts all configuration sources into a common key-value representation with metadata (source file, environment, data type, whether it is a secret reference).

3. **Cross-Environment Comparison**: Compares normalized configuration across environments to identify keys that are missing, added, or have different values or types.

4. **Schema Validation**: Validates each environment's configuration against a defined schema (JSON Schema, custom rules) to catch constraint violations such as invalid URLs, out-of-range numbers, or malformed connection strings.

5. **Secret Reference Audit**: Checks that all secret references (environment variable placeholders, Vault paths, cloud secret ARNs) point to secrets that actually exist in the target secret store.

6. **Report Generation**: Produces a structured report (Markdown, JSON, or terminal output) that categorizes each finding by severity (critical, warning, info) with specific remediation guidance.

## Instructions

### Step 1: Define the Configuration Inventory

Full walkthrough: [step-1-define-the-configuration-inventory.md](references/step-1-define-the-configuration-inventory.md) (load this step when you reach it).

### Step 2: Build the Configuration Parser

Full walkthrough: [step-2-build-the-configuration-parser.md](references/step-2-build-the-configuration-parser.md) (load this step when you reach it).

### Step 3: Implement Cross-Environment Comparison

Full walkthrough: [step-3-implement-cross-environment-comparison.md](references/step-3-implement-cross-environment-comparison.md) (load this step when you reach it).

### Step 4: Implement Schema Validation

Full walkthrough: [step-4-implement-schema-validation.md](references/step-4-implement-schema-validation.md) (load this step when you reach it).

### Step 5: Implement Secret Reference Validation

Full walkthrough: [step-5-implement-secret-reference-validation.md](references/step-5-implement-secret-reference-validation.md) (load this step when you reach it).

### Step 6: Generate Drift Reports

Full walkthrough: [step-6-generate-drift-reports.md](references/step-6-generate-drift-reports.md) (load this step when you reach it).

### Step 7: Integrate into CI/CD

Full walkthrough: [step-7-integrate-into-ci-cd.md](references/step-7-integrate-into-ci-cd.md) (load this step when you reach it).

## Best Practices

- **Define a reference environment**: Always compare against one authoritative environment (typically production). This avoids ambiguity about which environment has the "correct" value when they differ.

- **Maintain an ignore list**: Some keys are expected to differ across environments (database hostnames, replica counts, log levels). Maintain an explicit ignore list so these expected differences do not generate noise in drift reports.

- **Use a schema from day one**: Defining a configuration schema is not overhead; it is documentation that validates itself. Start with required keys and basic type constraints, then add value constraints (min/max, regex patterns, enums) as you learn from production issues.

- **Run checks on every config change**: Integrate the consistency check into your CI pipeline so that every pull request modifying configuration files is automatically validated before merge.

- **Schedule weekly drift scans**: Configuration can drift outside of pull requests (through manual changes, infrastructure automation, or secret store updates). A weekly scheduled check catches drift that bypasses your CI pipeline.

- **Track drift over time**: Store drift reports as artifacts and track the trend. Increasing drift over time indicates process problems that need attention beyond fixing individual findings.

- **Validate secret references, not secret values**: Never compare actual secret values across environments (they should be different). Instead, validate that secret references (ARNs, Vault paths, SSM parameter names) resolve to existing secrets.

- **Version the schema alongside the application**: When the application adds a new required configuration key, update the schema in the same pull request. This keeps the schema in sync with the code that depends on it.

## Common Pitfalls

- **Comparing values that should differ**: Database hostnames, API URLs, and replica counts are expected to differ across environments. Comparing them produces false positives that train the team to ignore drift reports. Use an ignore list or mark these keys as "environment-specific" in the schema.

- **Not accounting for format differences**: The same logical value can be represented differently across formats. The integer `8080` in YAML becomes the string `"8080"` in a .env file. Your comparison logic must normalize types before comparing, or you will report false type mismatches on every dotenv-sourced key.

- **Ignoring configuration sources outside version control**: If production configuration is partially managed through a cloud console, Terraform state, or a parameter store, your drift check must include those sources. Checking only files in the repository misses a significant class of drift.

- **Treating all findings as equal severity**: A missing database connection string is critical; an extra debug flag is informational. Without severity classification, teams either fix everything (wasting time on noise) or ignore everything (missing critical issues).

- **Running checks only in CI**: CI checks catch drift introduced by pull requests, but not drift caused by manual changes, infrastructure automation, or secret rotation. Complement CI checks with scheduled scans that query live configuration.

- **Hardcoding environment names**: If your checker only works with "dev", "staging", and "production", it will break when a team adds "qa" or "performance" environments. Design the tool to work with any set of environment names defined in the inventory file.

- **Not handling missing files gracefully**: If a configuration file does not exist for an environment (perhaps because that environment uses only environment variables), the tool should report the missing file as a finding rather than crashing.

- **Comparing secret values across environments**: Production secrets should not match dev secrets. If your checker flags "API_KEY differs between dev and production" as a finding, it is generating noise. Compare secret presence and reference validity, not secret values.

- **Letting the ignore list grow unchecked**: An ignore list that grows over time without review becomes a way to sweep real issues under the rug. Periodically audit the ignore list to ensure every entry has a documented justification and is still relevant.

- **Generating reports that nobody reads**: A drift report is only useful if someone acts on it. Assign ownership of drift findings, set SLAs for resolution, and track closure rates. An unread report is the same as no report at all.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The configs all look the same, a manual eyeball is enough" | A single missing key or a type that is `8080` in one env and `"8080"` in another is exactly what the eye skips and what breaks only in the environment that differs; a normalized programmatic diff catches what manual review misses. |
| "I'll just compare the values directly across environments" | Database hostnames, URLs, and replica counts are supposed to differ; comparing raw values floods the report with false positives that train the team to ignore it. Compare key presence, types, and schema, not environment-specific values. |
| "Checking the files in the repo covers our config" | Production config partially managed in a cloud console, parameter store, or Terraform state is a major drift source the repo never sees; the check must include those live sources. |
| "Every difference is a problem to fix" | Without severity classification a missing connection string and an extra debug flag look equal; the team then either burns time on noise or ignores the report entirely. |

## Verification

- [ ] All configuration sources per environment are inventoried, including non-repo sources (parameter store, ConfigMaps, console-managed values).
- [ ] Values are normalized by type before comparison so format differences (int vs string) do not produce false type mismatches.
- [ ] Environment-specific keys (hostnames, URLs, replica counts) are on a documented ignore list, not flagged as drift.
- [ ] Secret references are validated for presence and resolution, never compared by value.
- [ ] Findings carry a severity level, and the report identifies an owner or resolution step per discrepancy.

## Related Skills

- [[platform-engineer]] -- enforces config standards across services that this checker audits
- [[cicd-architect]] -- integrates the drift check as a pre-deployment gate in the pipeline
- [[database-design]] -- the connection-string and schema parameters this checker frequently validates
- [[security-review]] -- audits the secret references this checker verifies for existence
