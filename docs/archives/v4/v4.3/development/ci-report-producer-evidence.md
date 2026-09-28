# v4.3 CI Coverage and SARIF Producer Evidence

**Scope**: Post-release DF-3 follow-up for structured CI reports. This record is release-bound evidence, not a living CI contract.

The existing `repo-tests-ci` command now measures `scripts.ci` and writes `reports/coverage-ci.xml`. This is scoped CI-engine coverage, not whole-repository coverage. The existing catalog security scan retains its high-severity failure threshold and writes `reports/skill-security.sarif`; no new security gate or outbound scan was added. Both files are eligible for the seven-day CI receipt uploads and the aggregate report's hash/type index.

## Local verification

- `python -m pytest tests/ci/test_ci_engine.py tests/ci/test_ci_report_aggregation.py -q`: 76 passed.
- `python -m pytest tests/ci -q --cov=scripts.ci --cov-report=xml:reports/coverage-ci.xml`: 107 passed; coverage XML was 23,267 bytes and reported a 0.8832 line rate for one package.
- `python scripts/scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high --format sarif --output reports/skill-security.sarif`: exit 0; SARIF 2.1.0 was 53,187 bytes with one run and 48 findings below the high-severity failure threshold.
- The aggregate fixture identifies the coverage XML as `coverage` and the scanner file as `sarif`, with SHA-256 hashes for both.

## Publication gate

The producer and aggregate artifact must still run on the hosted PR. Inspect the downloaded aggregate for both files and confirm the same classification and seven-day expiry before marking DF-3 resolved. A skipped test or catalog group is not evidence of either report type.
