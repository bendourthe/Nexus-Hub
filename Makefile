.PHONY: all validate lint build-catalog test eval benchmark clean help

all: validate lint ## Run validation and linting

validate: ## Validate all JSON catalog files and skill bundles
	@echo "Validating JSON catalogs..."
	@python -c "import json; d = json.load(open('data/skills.json', encoding='utf-8')); print(f'  skills.json OK -- {len(d[\"skills\"])} skills')"
	@python -c "import json; d = json.load(open('data/bundles.json', encoding='utf-8')); print(f'  bundles.json OK -- {len(d[\"bundles\"])} bundles')"
	@python -c "import json; d = json.load(open('data/workflows.json', encoding='utf-8')); print(f'  workflows.json OK -- {len(d[\"workflows\"])} workflows')"
	@python -c "import json; d = json.load(open('data/templates.json', encoding='utf-8')); print(f'  templates.json OK')"
	@echo "Auditing per-skill bundled resources (scripts/, references/, assets/) for orphans..."
	@python scripts/validate_skills.py --bundles-only
	@echo "Running v2.3.0 CI validators (no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security)..."
	@python scripts/validate_no_personal_paths.py \
	    --exclude docs/v2.0.0 \
	    --exclude docs/v2.1.0 \
	    --exclude docs/v2.2.0 \
	    --exclude catalog/hooks/tests
	@python scripts/validate_unicode_safety.py \
	    --exclude docs/v2.0.0 \
	    --exclude docs/v2.1.0 \
	    --exclude docs/v2.2.0 \
	    --exclude templates/ai-instructions
	@python scripts/scan_supply_chain_iocs.py
	@python scripts/validate_workflow_security.py
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
	@if [ -d tests ]; then python -m pytest -q tests; else echo "  (no tests/ directory -- skipping repo-level suite)"; fi
	@echo "Tests complete."

eval: ## Run the nexus-code-search synthetic-codebase eval harness
	@echo "Running nexus-code-search eval harness..."
	@cd extensions/nexus-code-search && python -m nexus_code_search.eval --out ../../docs/v2.2.0/eval-baseline.md
	@echo "Eval complete. Report: docs/v2.2.0/eval-baseline.md"

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
