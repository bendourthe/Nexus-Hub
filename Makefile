.PHONY: all validate lint build-catalog test scan eval trigger-evals compress-eval benchmark clean help

all: validate lint ## Run validation and linting

validate: ## Validate all JSON catalog files and skill bundles
	@echo "Validating JSON catalogs..."
	@python -c "import json; d = json.load(open('data/skills.json', encoding='utf-8')); print(f'  skills.json OK -- {len(d[\"skills\"])} skills')"
	@python -c "import json; d = json.load(open('data/bundles.json', encoding='utf-8')); print(f'  bundles.json OK -- {len(d[\"bundles\"])} bundles')"
	@python -c "import json; d = json.load(open('data/workflows.json', encoding='utf-8')); print(f'  workflows.json OK -- {len(d[\"workflows\"])} workflows')"
	@python -c "import json; d = json.load(open('data/templates.json', encoding='utf-8')); print(f'  templates.json OK')"
	@echo "Auditing per-skill bundled resources (scripts/, references/, assets/) for orphans..."
	@python scripts/validate_skills.py --bundles-only
	@echo "Running non-blocking skill quality-heuristics pass (warnings only)..."
	@python scripts/validate_skills.py --quality
	@echo "Running trigger-and-routing eval (description near-collision + routing hard gate)..."
	@python scripts/run_trigger_evals.py --gate
	@echo "Running v2.3.0 CI validators (no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security)..."
	@python scripts/validate_no_personal_paths.py
	@python scripts/validate_unicode_safety.py
	@python scripts/scan_supply_chain_iocs.py
	@python scripts/validate_workflow_security.py
	@echo "Validating solution-doc frontmatter parser-safety (docs/solutions; no-op when absent)..."
	@python scripts/validate_solution_frontmatter.py
	@echo "Checking version sync across all version-carrying surfaces..."
	@python scripts/check_version_sync.py
	@echo "Checking base-*.md lockstep parity (claude/codex/cursor/gemini/opencode)..."
	@python scripts/check_base_template_parity.py
	@echo "Checking per-model prompting profile layer (structural schema gate)..."
	@python scripts/verify_model_prompting_profiles.py
	@echo "Checking platform read-contract alignment (code vs docs/policy/platform-read-contracts.md)..."
	@python scripts/verify_platform_contracts.py
	@echo "Checking platform read-contract freshness (re-verified for the release being cut)..."
	@python scripts/check_platform_contract_freshness.py
	@echo "Running compression accuracy-regression gate (v3.2.0 Phase 5)..."
	@cd extensions/nexus-context-compressor && python -m evals --check
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
	@cd extensions/nexus-context-compressor && python -m evals --check --out ../../docs/v3/v3.2/compression-eval-baseline.md
	@echo "Compress-eval complete. Report: docs/v3/v3.2/compression-eval-baseline.md"

benchmark: ## Benchmark internal MCP servers
	@echo "Benchmarking internal MCPs..."
	@python scripts/nexus_mcp_benchmark.py --append --quiet
	@echo "Benchmark complete. Results: data/benchmarks/mcp.json"

clean: ## Remove build artifacts and caches
	@echo "Cleaning..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
