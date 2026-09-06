.PHONY: all validate lint build-catalog test scan eval trigger-evals compress-eval benchmark clean help \n        ci-fast ci-full ci-platform ci-report ci-release

all: validate lint ## Run validation and linting

validate: ## Validate all JSON catalog files and skill bundles
	@echo "Validating JSON catalogs..."
	@python -c "import json; d = json.load(open('data/skills.json', encoding='utf-8')); print(f'  skills.json OK -- {len(d[\"skills\"])} skills')"
	@python -c "import json; d = json.load(open('data/bundles.json', encoding='utf-8')); print(f'  bundles.json OK -- {len(d[\"bundles\"])} bundles')"
	@python -c "import json; d = json.load(open('data/workflows.json', encoding='utf-8')); print(f'  workflows.json OK -- {len(d[\"workflows\"])} workflows')"
	@python -c "import json; d = json.load(open('data/templates.json', encoding='utf-8')); print(f'  templates.json OK')"
	@echo "Auditing per-skill bundled resources (scripts/, references/, assets/) for orphans..."
	@python scripts/validate_skills.py --bundles-only
	@echo "Checking agentskills.io open-standard conformance..."
	@python scripts/check_agentskills_conformance.py
	@echo "Checking committed framework-coverage map is fresh..."
	@python scripts/build_framework_coverage.py --check
	@echo "Running non-blocking skill quality-heuristics pass (warnings only)..."
	@python scripts/validate_skills.py --quality
	@echo "Running trigger-and-routing eval (description near-collision + routing hard gate)..."
	@python scripts/run_trigger_evals.py --gate
	@echo "Checking the shipped permission baseline is read-only at the side-effect level..."
	@python scripts/validate_permission_baseline.py
	@echo "Checking cross-installer capability and fallback parity..."
	@python scripts/check_installer_parity.py
	@echo "Running v2.3.0 CI validators (no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security)..."
	@python scripts/validate_no_personal_paths.py
	@python scripts/validate_unicode_safety.py --strict
	@python scripts/scan_supply_chain_iocs.py
	@python scripts/validate_workflow_security.py
	@echo "Checking every required status check is produced by an unconditionally-triggered workflow..."
	@python scripts/check_required_check_coverage.py
	@echo "Checking comparison / adoption-plan co-location across every docs/v<MAJOR> tree..."
	@python scripts/check_doc_colocation.py
	@echo "Validating solution-doc frontmatter parser-safety (docs/solutions; no-op when absent)..."
	@python scripts/validate_solution_frontmatter.py
	@echo "Checking incident notes carry a Public-Safe Shape and a linked Durable fix (docs/incidents; no-op when absent)..."
	@python scripts/check_incident_notes.py
	@echo "Reporting per-version docs due for archival (advisory; never fails)..."
	@python scripts/check_docs_retention.py
	@echo "Checking always-loaded instruction docs stay under their word ceilings..."
	@python scripts/validate_doc_budgets.py
	@echo "Checking the memory integration prose stays under its token budget..."
	@python scripts/check_memory_integration_budget.py
	@echo "Checking decision records (structure, header, mandatory alternatives)..."
	@python scripts/validate_decision_records.py
	@echo "Checking per-skill registry entries against the catalog (structure and text, strict)..."
	@python scripts/check_registry_entries.py --check --strict
	@echo "Checking version sync across all version-carrying surfaces..."
	@python scripts/check_version_sync.py
	@echo "Checking the context compressor makes no outbound calls..."
	@python scripts/check_no_outbound.py
	@echo "Checking docs conventions (relative-link integrity, kebab-case dirs)..."
	@python scripts/check_docs_conventions.py
	@echo "Checking memory provenance templates (source required, changelog, no-delete)..."
	@python scripts/check_memory_provenance.py
	@echo "Checking base-*.md lockstep parity (claude/codex/cursor/gemini/opencode)..."
	@python scripts/check_base_template_parity.py
	@echo "Checking per-model prompting profile layer (structural schema gate)..."
	@python scripts/verify_model_prompting_profiles.py
# NOTE: scripts/check_model_prompting_freshness.py is deliberately NOT run here.
# The layer's STRUCTURE is a hard gate (above); its FRESHNESS is advisory, because
# models ship on the vendor's clock and gating that would let a model released on a
# Tuesday wedge every release until someone ran a research swarm. It runs as an
# advisory step in /update release (governance step 5). Do not add it to this target.
	@echo "Checking platform read-contract alignment (code vs docs/policy/platform-read-contracts.md)..."
	@python scripts/verify_platform_contracts.py
	@echo "Checking platform read-contract freshness (re-verified for the release being cut)..."
	@python scripts/check_platform_contract_freshness.py
	@echo "Checking derived artifacts against configs/platform-defaults.json (v3.16.0 Phase 1)..."
	@python scripts/sync_platform_defaults.py --check
	@echo "Running compression accuracy-regression gate (v3.2.0 Phase 5)..."
	@cd extensions/nexus-context-compressor && python -m evals --check
	@echo "Checking guide data-count markers against the catalog (v4.4.2 Phase 1)..."
	@python scripts/stamp_guide_counts.py --check
	@echo "All catalogs valid."

lint: ## Lint shell scripts with ShellCheck
	@echo "Linting shell scripts..."
	@command -v shellcheck >/dev/null 2>&1 && shellcheck --severity=warning scripts/installer.sh install.sh || echo "  shellcheck not installed — skipping (install with: apt install shellcheck)"
	@echo "Lint complete."

build-catalog: ## Rebuild skills.json and templates.json from source
	@echo "Building catalogs..."
	@python infrastructure/tools/build_skills_catalog.py
	@python infrastructure/tools/build_templates_catalog.py
	@echo "Catalogs rebuilt."

test: ## Run MCP skill server + repo-level pytest suites
	@echo "Running tests..."
	@cd extensions/nexus-skill-server && python -m pytest -q
	@cd extensions/nexus-code-search && python -m pytest -q
	@cd extensions/nexus-web-fetch && python -m pytest -q
	@cd extensions/nexus-skill-scanner && python -m pytest -q
	@cd extensions/nexus-context-compressor && python -m pytest -q
	@cd extensions/nexus-memory && python -m pytest -q
	@if [ -d tests ]; then python -m pytest -q tests; else echo "  (no tests/ directory -- skipping repo-level suite)"; fi
	@echo "Tests complete."

scan: ## Scan the catalog for skill-security findings (fails on any HIGH/CRITICAL)
	@echo "Scanning catalog with nexus-skill-scanner (gate: HIGH/CRITICAL)..."
	@python scripts/scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high
	@echo "Catalog scan clean (no HIGH/CRITICAL findings)."

eval: ## Run the nexus-code-search synthetic-codebase eval harness
	@echo "Running nexus-code-search eval harness..."
	@cd extensions/nexus-code-search && python -m nexus_code_search.eval --out ../../docs/v3/v3.0/eval-baseline.md
	@echo "Eval complete. Report: docs/v3/v3.0/eval-baseline.md"

trigger-evals: ## Detect skill-description trigger-vocabulary near-collisions (warning-only; --gate to enforce)
	@echo "Running trigger-and-routing eval (skill-description near-collision detector)..."
	@python scripts/run_trigger_evals.py --verbose

compress-eval: ## Run the context-compressor accuracy-regression harness + gate
	@echo "Running context-compressor accuracy-regression harness..."
	@cd extensions/nexus-context-compressor && python -m evals --check --out ../../docs/releases/v3/v3.2/compression-eval-baseline.md
	@echo "Compress-eval complete. Report: docs/releases/v3/v3.2/compression-eval-baseline.md"

benchmark: ## Benchmark internal MCP servers
	@echo "Benchmarking internal MCPs..."
	@python scripts/nexus_mcp_benchmark.py --append --quiet
	@echo "Benchmark complete. Results: data/benchmarks/mcp.json"

# --- Repository-native CI profiles (v4.0.0) --------------------------------
#
# These delegate to scripts/ci/run.py. They do NOT copy its command list: the
# profiles are defined once, in scripts/ci/profiles.py, and both a developer and
# .github/workflows/ call the same definition. Duplicating the list here would
# recreate exactly the drift the engine was built to remove.
#
# `validate`, `lint`, and `test` above are retained and unchanged. Their
# relationship to the profiles is explicit: `ci-full` runs a superset of
# `validate` plus `test`, so a green `ci-full` implies a green `validate`, while
# `validate` on its own stays the fastest way to check catalog integrity alone.
#
# Where make is unavailable (a plain Windows shell), call the script directly:
#   python scripts/ci/run.py --profile fast --reports-dir reports

ci-fast: ## Cheapest useful signal (seconds): parses, hygiene, workflows, version
	@python scripts/ci/run.py --profile fast --reports-dir reports

ci-full: ## Everything provable on this host (minutes): validators, catalog, tests
	@python scripts/ci/run.py --profile full --reports-dir reports

ci-platform: ## Only what differs by host (shell lint, PowerShell parse, Windows hooks)
	@python scripts/ci/run.py --profile platform --reports-dir reports

ci-report: ## Re-render reports from the last run without re-running any check
	@python scripts/ci/run.py --profile report --reports-dir reports

ci-release: ## Packaging and publication readiness. Never a validation re-run
	@python scripts/ci/run.py --profile release --reports-dir reports

clean: ## Remove build artifacts and caches
	@echo "Cleaning..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
