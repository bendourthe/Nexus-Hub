# Session History - Agent Security Layers Phase 1: New Skill

**Date**: 2026-08-23
**Branch**: `feat/v3.20.0-adoption-agent-security-layers`
**Plan**: [`docs/releases/v3/v3.20/plans/v3.20.0-adoption-agent-security-layers.md`](../../plans/v3.20.0-adoption-agent-security-layers.md)
**Phase**: 1 - New skill: agent-execution-isolation
**Environment**: Windows 11, PowerShell, Python 3, pytest
**Outcome**: Shipped `agent-execution-isolation` under security-operations with OS-sandbox and egress-boundary references, trigger evals, three-file registry plus bundles.json membership, and a one-sentence `/review security` hook. Catalog count 274 to 275. Ready for Phase 2.

## 1. Starting State and Routing

- **Starting commit**: `838d0227` (`origin/develop`, merge of v3.19.2 checksums)
- **Plan recommendation**: frontier model, high effort
- **Implementation route**: stayed on the current Cursor session (Grok 4.6 / frontier). Cursor cannot script a model switch; no downshift.
- **Installer edit**: none. The skill lives under `catalog/skills/`, which both installers copy recursively. No `scripts/` file was added.

## 2. What Was Implemented

### 1.1 - SKILL.md and references

Created `catalog/skills/security-operations/agent-execution-isolation/` with:

- `SKILL.md`: three-layer model (infrastructure / runtime / network), three-question triage, applicability gate for `/review security`, SKIP fencing against `agentic-endpoint-hardening`, `egress-redaction`, and `containerization`. No vendor or source-article names in the body.
- `references/os-sandboxing.md`: Landlock, seccomp, netns, ephemeral containers, mount allowlist.
- `references/egress-boundary.md`: out-of-process proxy, static rules, LLM judge, SSRF/RFC-1918, HITL, credential injection.
- `references/standards.md`: ATT&CK T1611 / T1552 / T1071, D3FEND D3-NTA / D3-PA / D3-FA, NIST CSF PR.AC / PR.DS / DE.CM.

### 1.2 - Trigger evals

`evals/trigger-cases.json`: five positives (sandbox SSH keys, egress proxy, keys out of container, Landlock/seccomp, isolate container) and three near-miss negatives (config-write escape, redact-before-send, generic Dockerfile). `run_trigger_evals.py --gate` passed at margin 1.15 with 0 routing failures.

### 1.3 - Registry

Hand-edited `data/SKILL_INDEX.md`, `data/skills.json` (HIGH, 100/100/95), `data/marketplace.json` (security-operations 16 to 17, total 275). Also `data/bundles.json` security-operations module (reachability gate), `.claude-plugin/plugin.json` count, `tests/skills/test_agent_memory.py` hardcoded 274, AGENTS.md and README headline counts. Did not run a catalog rebuild.

### 1.4 - /review security hook

One conditional sentence on the security coverage contract in `catalog/commands/review.md`. Dispatcher stays thin; applicability lives in the skill.

## 3. Tests

- `python scripts/validate_skills.py --bundles-only`: PASS
- `python scripts/run_trigger_evals.py --gate`: PASS (0 collisions, 0 routing failures)
- `python scripts/check_registry_entries.py --check --strict`: PASS
- `python -m pytest tests/validators/test_registry_consistency.py tests/skills/test_agent_memory.py tests/skills/test_eval_pipeline_audit.py`: 80 passed
- Full validate script equivalent of `make validate` (Windows, no `make`): PASS, including installer parity, unicode --strict, compressor evals

## 4. Deviations

- Plan text still says 271 to 272. Live catalog was 274; registered 275.
- `data/bundles.json` was not in the plan's three-file list; `check_registry_entries.py` requires module membership, so the skill was added to the security-operations module.
- `tests/skills/test_agent_memory.py` hard-coded 274 and had to move with the census.
- DEVLOG index line deferred until `/update release` (one line per released version, not per phase).

## 5. Next Steps

Phase 2: fold credential brokering into `agentic-endpoint-hardening`, content-vs-network distinction into `egress-redaction`, and the triage cross-link into `ai-agent-governance`.
