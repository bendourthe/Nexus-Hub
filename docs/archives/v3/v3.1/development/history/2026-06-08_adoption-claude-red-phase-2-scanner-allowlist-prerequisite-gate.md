# Session History -- v3.1.0 adoption-claude-red Phase 2: Scanner allowlist prerequisite gate

**Date**: 2026-06-08
**Plan**: [`docs/releases/v3/v3.1/plans/adoption-claude-red.md`](../../plans/adoption-claude-red.md)
**Phase**: 2 of 5 -- scanner allowlist prerequisite gate
**Branch**: `feat/adoption-claude-red` (continued from Phase 1 tip `3c815fe`)
**Outcome**: complete; both sub-tasks (T005-T006) closed, all quality gates green.

## Goal

Tune the `nexus-skill-scanner` so authorized red-team payloads inside `catalog/skills/security/` skill bodies are capped below the HIGH/CRITICAL CI gate, WITHOUT weakening detection of genuinely malicious skills. This is the prerequisite gate for the payload-bearing Phase 3-4 fold-ins (web AppSec + JWT/OAuth attack methodology); per the plan it must reuse the existing fence-aware/prose-capping mechanism (not a blanket suppression), scope strictly to the `security` category and prose/fenced contexts, never relax exfiltration / excessive-agency / live-malware classes, and never apply to third-party `/skills import` scans.

## Root-cause analysis (before any code)

Traced exactly what produces a HIGH/CRITICAL finding on a markdown `security` skill body in the default CI gate (`--fail-on high`, no `--yara`, no `--osv`):

- **Text patterns** (`text_patterns.py`): hard-capped at MEDIUM and suppressed inside markdown fences. Cannot produce HIGH/CRITICAL.
- **Behavioral AST** (`behavioral_ast.py`): `if unit.suffix != ".py": return []` -- only parses real Python scripts, never markdown fenced examples. A SKILL.md gets nothing.
- **MCP / supply-chain / workflow analyzers**: config / manifest / `.github/workflows` only; markdown is skipped.
- **Secret analyzer** (subsumes `validate_skills.py` `scan_text_for_secrets`): high-confidence credential formats (`Bearer <50+ chars>`, `sk-...`, `AKIA...`, `ghp_...`, `github_pat_...`) are flagged HIGH **even inside a fence** by design ("a genuinely leaked key must never be suppressed"). Only the low-confidence "Generic secret assignment" is fence-exempt.

Conclusion: the one residual HIGH path on a markdown security skill body is the secret analyzer firing on a fenced example token -- exactly what a JWT/OAuth attack-methodology skill (Phase 4) legitimately shows. That is the precise gap the allowlist closes. The executable-payload paths (AST exec/exfil) come from `.py` scripts, not markdown, and the plan forbids relaxing them.

## Subtasks completed

1. **T005 -- producer-catalog allowlist.** Added `extensions/nexus-skill-scanner/src/nexus_skill_scanner/allowlist.py`: `is_trusted_security_skill_body(path, repo_root)` and `apply_allowlist(findings, path, repo_root)`. It is a policy layer, not a detection change -- analyzers keep reporting the real class/severity, and the cap is applied at one choke point (`scanner.scan_file`, the single place that knows both the file path and the repo root). A finding is lowered to MEDIUM only when ALL three rules hold: (1) trusted producer catalog (real Nexus-Hub `repo_root` AND the file resolves under `<repo_root>/catalog/skills/security/`); (2) prose/fenced context only (Markdown skill body; bundled `.py`/`.sh`/`.ps1` scripts are never capped); (3) not a never-relax class (`{2, 5, 12, 13, 14}` -- exfiltration, excessive agency, dynamic code execution, taint-to-sink injection, signature/live-malware). The cap only lowers, never raises. Helpers exported from `__init__.py`; the scoping rule + rationale documented in a new "Security-category allowlist" subsection of the package `README.md`.
2. **T006 -- regression tests.** Added `tests/test_allowlist.py` (15 tests: unit tests for `is_trusted_security_skill_body` and `apply_allowlist`, the four plan assertions, and the headline malicious-script safety test) and two launcher-subprocess regressions in `tests/validators/test_scan_skill_security.py`. High-confidence tokens are assembled at runtime (`"Bearer " + "A"*64`) so the test sources carry no credential literal.

## Key decisions

- **Centralized policy layer over per-analyzer category awareness.** The cap lives in `scanner.scan_file` (one auditable choke point) rather than threading category context into every analyzer's `analyze(unit)` signature. This keeps each analyzer pure (it reports the true class/severity) and makes the one place that relaxes severity easy to review and test, and it is future-proof: any new analyzer that emits HIGH on a markdown security body is covered automatically.
- **"Fenced/prose contexts" = the whole markdown skill body.** Read the plan's phrase as the markdown documentation surface (prose + fenced), contrasted with executable scripts -- consistent with how the existing text analyzer already caps ALL markdown prose at MEDIUM. The trade-off (a real leaked credential sitting in a `security`-skill body is downgraded HIGH -> MEDIUM) is acceptable because it is still emitted/visible at MEDIUM, scoped only to the reviewed producer catalog's security category, and the never-relax classes keep all genuine attack *behavior* at full severity. Chosen over a fence-line-precise check for simplicity, maintainability, and consistency with the established prose-capping discipline. Surfaced to the user in the pre-flight and confirmed.
- **Markdown-only cap is the safety boundary.** Bundled executable scripts under `catalog/skills/security/` are never capped, so an exfil/exec payload that actually runs is still detected at full severity -- this is what prevents the allowlist from becoming a malicious-skill blind spot, and it is directly asserted by the headline test.
- **Pre-existing F401 left untouched.** The validator test file carries an unused `import pytest` at HEAD; per the "every changed line traces to the request / no out-of-scope cleanup" rule and the absence of any ruff gate in the repo, it was left as-is and recorded as WN-v31cr-4. `ruff format` was likewise not applied (the whole scanner package is non-ruff-format-clean by convention; the new files match the package style).

## Test results

- Scanner package: **87 passed** (`python -m pytest -q`), up from 72 (15 new allowlist tests).
- Repo-level validators: **136 passed** (`pytest tests/validators -q`), including the 2 new launcher-subprocess allowlist regressions and the existing `test_catalog_gate_is_clean` dogfood (the real catalog still produces 0 HIGH/CRITICAL).
- Coverage: `allowlist.py` **100%** line coverage; package **TOTAL 90%** (both above the 80% gate).
- Catalog scanner gate (`scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high`): **exit 0** (only pre-existing LOW MCP moving-ref findings; no regression -- the cap only lowers severities).
- `make validate` emulated (make absent on host): `skills.json` valid (250 skills), bundle audit PASS, `check_version_sync.py` green (no version surface touched).
- Plan assertions proven: (a) malicious fixture still CRITICAL; (b) clean fixture still LOW; (c) authorized-payload security skill below HIGH (secret still detected, capped to MEDIUM); (d) same payload in a non-security category AND as a third-party (no-repo-root) scan still HIGH. Plus: malicious bundled `.py` script under `catalog/skills/security/` still CRITICAL.

## CI/CD edits

- None. The scanner suite is already wired into the CI `tests` job (`ci.yml:126`) via `pytest extensions/nexus-skill-scanner/tests/` and `make test` (`Makefile:42`); the validator tests run at `ci.yml:102`. The phase added no new script command, environment variable, or dependency (stdlib-only), and the scanner package auto-installs editable in CI. 0 workflows touched.

## Deviations

- None. The plan was followed exactly (T005-T006 as written).

## Troubleshooting / environment notes

- `make` and `shellcheck` are unavailable on the Windows dev host (consistent with prior phases' WN-v31cr-2), so `make validate` / `make scan` / `make test` were emulated by invoking pytest, the validators, and the scanner directly. `make lint` (ShellCheck) is not applicable -- the phase added only Python, no shell surface.
- The working-directory of the Bash tool persists between calls; one `cd` into the package dir was reused across runs.

## Known gaps

See [`docs/releases/v3/v3.1/known-gaps.md`](../../known-gaps.md). One new open item this phase: WN-v31cr-4 (pre-existing unused `import pytest` in the validator test file left untouched; the scanner package is non-ruff-format-clean by convention -- both deferred to a dedicated lint-hygiene change, not gated by CI/make). 0 resolved. Carried forward: WN-v31cr-1/-2/-3. Total 4 WN open.

## Next steps

- **Phase 3 -- Web AppSec methodology fold-in**: enrich `catalog/skills/security/advanced-attack-patterns/SKILL.md` (SSRF, SSTI, XXE, deserialization, request-smuggling, IDOR) and `business-logic-abuse/SKILL.md` (pricing/refund abuse, anti-fraud defeat, workflow-step bypass) with re-authored attacker-perspective methodology, fenced so the Phase 2 allowlist applies. Push per-vector detail to `references/` if the body exceeds the 500-line norm. The allowlist landed here is the prerequisite that lets those fenced payloads stay below the gate.
