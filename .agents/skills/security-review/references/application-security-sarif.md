# Application-Security SARIF Export

This contract describes the local normalized-envelope to SARIF boundary for agents and maintainers exporting application findings. It covers accepted fields, canonical relative locations, integrity checks, dispositions, secrecy and deterministic stdout; it adds no source reads or upload path.

## Input and authority

`scripts/emit-sarif.py` accepts one bounded UTF-8 JSON document from stdin: exactly `nexus.application-audit-envelope/v1`, schema version 1 and decoder `nexus.strict-json/v1`. The shared `_normalized_audit.py` validator checks field shapes, references and the canonical envelope fingerprint. It never recomputes health, re-adjudicates findings or accepts raw schema-v2. A matching fingerprint proves internal integrity, not authenticity, process execution or absence of hidden retries.

## Mapping

The serialization follows the [OASIS SARIF 2.1.0 standard](https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html). The driver is `nexus-application-security`. Rules use canonical application vulnerability IDs and fixed titles; custom rules retain their namespaced opaque IDs. No skill-scanner taxonomy or runtime package is imported.

| Envelope field | SARIF field |
|---|---|
| `critical`, `high` | Result `level: error` |
| `medium` | Result `level: warning` |
| `low`, `info` | Result `level: note` |
| `release_blocking` | Result property, unchanged; high/critical must be true |
| `confirmed`, `needs-live-validation` | Active result, with disposition preserved |
| `corrected`, `rejected` | No active alert; retained in run disposition counts and finding ledger |
| Finding ID | `partialFingerprints.applicationFinding/v1` |
| Relative location | `physicalLocation.artifactLocation.uri` and line region |
| Explicit locationless marker | Result with no `locations` property |
| Evidence IDs and qualified source/sink | Result properties, with receipt references intact |
| Target, scope, routing, artifact and run fingerprints | Run properties, unchanged |
| Health, provenance and limitation codes | Run properties, unchanged |

Rules sort by rule ID and results by rule ID then finding ID. Duplicate finding or receipt IDs, contradictory titles for a rule, invalid evidence references, mismatched envelope fingerprint and inconsistent disposition counts reject the entire input. The validator checks integrity and shape without converting degraded/failed health into complete.

## Field and path constraints

Object fields use exact allowlists. IDs are `sha256:` plus 64 lowercase hexadecimal characters; digests are 64 lowercase hexadecimal characters and revisions are exactly 40 or 64. Enum fields use the closed sets from the envelope contract. Titles are the canonical fixed labels. Clock fields retain their UTC syntax and duration checks. Reason identifiers use at most 128 ASCII letters or underscores. Numeric fields are finite and bounded, and booleans cannot substitute for integers. Arbitrary properties, commands, snippets, prompts and environment objects are rejected.

Locations are at most 1,024 characters and must already be canonical relative slash-separated paths. Reject absolute paths, drive/device/UNC forms, schemes or authorities, backslashes, empty or dot segments, percent signs (including encoded and double-encoded traversal), controls and Unicode format characters. The shared canonical-path identity rejects unsafe names, non-NFC aliases and case/normalization collisions. Encode each accepted segment once with UTF-8 percent encoding. A filename containing spaces or ordinary Unicode is portable; a Windows path must first be recorded as its canonical repository-relative path. Never normalize an unsafe input into an accepted path.

Inspect every input and output string recursively for inline credential patterns and current secret environment values using the envelope's longest-first semantics. Unknown or unsafe fields are errors, not text to redact into a different finding identity. Error diagnostics are fixed identifiers and never echo the rejected value.

## Operation and verification

From the repository root:

```bash
python catalog/skills/code-review/security-review/scripts/closure-gate.py tests/fixtures/security-audit/application-audit-complete.json --summary | python catalog/skills/code-review/security-review/scripts/emit-sarif.py
```

The emitter writes one sorted, indented JSON document with a final newline to stdout. Valid serialization exits 0 even when preserved audit health is failed. Invalid or missing stdin exits 2 with a concise fixed stderr error and no partial SARIF. Callers own persistence and must check the closure producer's exit separately. There is no default output file, referenced-file access, external schema fetch, retry, dependency installation, hosted validation, code-scanning integration or upload. Bundled scripts and this reference distribute recursively with the owning skill.
