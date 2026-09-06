# Session History -- v3.0.0 Phase 7: scanner optional modules (re-partial)

**Date**: 2026-06-04
**Plan**: [`docs/releases/v3/v3.0/plans/command-consolidation-skill-security.md`](../../plans/command-consolidation-skill-security.md)
**Phase**: 7 of 10 -- scanner optional modules (re-partial)
**Outcome**: complete; all sub-tasks (T033-T035) closed, all applicable quality gates green. Recovered from an interrupted prior session whose network drop lost the conversation but left the working-tree changes intact.

## Goal

Add the two optional, default-off modules that complete the `nexus-skill-scanner` detection surface: the class-14 signature engine (T033) and the live portion of class 4, the OSV.dev dependency-vulnerability lookup (T034). The Phase 7 stability gate is behavioral, not feature-count: both modules must degrade gracefully when their input is absent, the default scan (modules off) must be byte-identical to Phase 6, and no new default outbound call may be introduced. The only network surface allowed anywhere in v3.0.0 is the opt-in `--osv` query, which sends only a package-coordinate tuple and ships an offline fallback.

## Recovery context

The phase was begun in a prior session that was lost to a network interruption. The working tree carried the in-progress footprint: tracked edits to `pyproject.toml`, `analyzers/__init__.py`, `cli.py`, and `scanner.py` (the opt-in wiring), and untracked `analyzers/dependencies.py`, `analyzers/signatures.py`, `data/osv_offline.json`, `data/signature_rules/{cryptominers,exploits,webshells}.yar`, and `tests/test_dependencies.py`. Recovery assessment found T034 complete (module + offline DB + 16 tests, all green) and T033 functionally complete (module + 12 rules) but missing its test file, plus a stale scanner `README.md`. This session closed those two gaps and ran the post-phase sequence.

## Subtasks completed

1. **T033 -- Optional signature module (recovered + completed).** `analyzers/signatures.py` is a self-contained pure-Python rule engine: it parses a deliberately small subset of the YARA rule grammar (named literal/regex strings with `any of them` / `all of them` / `N of them` / `$a and/or/not $b` conditions and a recursive-descent condition evaluator) and runs the bundled rules over each file unit. It is fence-aware (a payload inside a Markdown fenced block is suppressed exactly as the text analyzers suppress theirs) and degrades gracefully (no rules loadable -> reports itself `skipped`, no findings, scan unaffected). Twelve re-authored rules ship across three files: `cryptominers.yar` (stratum / XMRig / browser-miner), `exploits.yar` (bash-`/dev/tcp`, netcat, python-pty reverse shells + PowerShell download cradle), `webshells.yar` (PHP eval/obfuscated/system, JSP `Runtime.exec`, ASP `Eval(Request)`). This session added the missing `tests/test_signatures.py` (18 tests).
2. **T034 -- Optional offline-first OSV.dev lookup (recovered, verified).** `analyzers/dependencies.py` extracts pinned `(ecosystem, package, version)` coordinates from `requirements.txt` / `pyproject.toml` / `package.json`, matches them against a bundled offline advisory DB (`data/osv_offline.json`, 5 well-documented public advisories), and -- only when `--osv` is passed -- supplements with a live OSV.dev query via stdlib `urllib`. Any network/parse failure sets `network_degraded` and the offline result stands. The live call sends ONLY the coordinate tuple (no source, prompt, or query text). Verified complete with its 16 tests green (constraint matching, manifest extraction, offline match, injected-fetcher live merge, the coordinate-only privacy assertion, network-failure degrade, default-OFF wiring).
3. **T035 -- Testing and stabilization.** Authored `tests/test_signatures.py`, ran the full package suite, refreshed the stale README options list, and ran the emulated `make validate` gate. All green.

## Key decisions

- **Pure-Python RE matcher instead of a native YARA binding (DEVIATION, user-endorsed).** Plan T033 described YARA as "a lazy optional dependency" (i.e. wrap `yara-python`, with a test that "simulates YARA absent"). The recovered implementation instead reverse-engineered the small slice of the rule language Nexus-Hub needs in pure Python, and the `pyproject.toml` change deletes the `yara = ["yara-python>=4.3"]` optional extra. This is a deliberate deviation: it keeps the scanner stdlib-only top to bottom (zero external runtime dependency for any module), aligns with the user's explicit "no external dependencies, prioritize reverse-engineering" direction, and sits one tier higher on the MCP Registry Policy decision tree (tier 3 "reverse-engineer into a local internal" beats tier 4 "trusted vendor wrapper"). The graceful-degrade contract is preserved but re-pointed: "simulate YARA absent" becomes "simulate the bundled rules unavailable" (`SignatureAnalyzer(rules=[])` -> `skipped` note + no findings), which the test asserts at both the analyzer and `Scanner` levels.
- **Fence-specificity is the safety property under test.** A producer catalog that teaches security carries reverse shells and web-shell one-liners inside fenced examples. The new tests lock the exact contract: the same payload is suppressed inside a ```` ```sh ```` block but still caught in Markdown prose (outside any fence), so the module neither false-positives on documentation nor is blinded to a payload smuggled outside a fence.
- **Default-off asserted at the Scanner level.** `test_signatures_off_by_default` / `test_signatures_enabled_detects_payload` exercise the wiring the lost session added (`Scanner(enable_signatures=...)`), so the "default scan is byte-identical to Phase 6" invariant is verified through the public surface, not just the analyzer.

## Test results

- **Package suite**: 72 passed (`extensions/nexus-skill-scanner/tests/`), up from 54 -- the new `test_signatures.py` adds 18 (condition grammar, rule parsing incl. malformed-string skip and nocase, bundled-rule load, reverse-shell -> CRITICAL, cryptominer detect, clean -> none, fence suppress vs prose match, graceful degrade, default-off, scanner integration, and a monkeypatched scanner skip-note surfacing). `test_dependencies.py` (16, from the recovered session) green.
- **Coverage**: `signatures.py` 92%, `dependencies.py` 90%, package total 90% -- above the 80% line gate.
- **Lint**: `ruff check` (0.9.4) clean on `test_signatures.py`, `signatures.py`, `dependencies.py`.
- **Smoke**: 12 rules load; a bash `/dev/tcp` reverse shell in `evil.sh` scores CRITICAL; the same payload fenced in a `SKILL.md` yields 0 findings; the condition grammar (`any`/`all`/`N of them`, `and`/`or`, parens) evaluates correctly.
- **Emulated `make validate`** (`make` not on PATH on the Windows host per WN-v30-4; `ruff` IS installed and ran clean): `skills.json` OK (247 skills), bundle audit PASS (0 errors, 1 pre-existing warning in `catalog/skills`, unrelated to `extensions/`), supply-chain-IOCs / workflow-security / `check_version_sync.py` all exit 0 (version-sync green at 2.4.0 across all six surfaces; the v3.0.0 bump is Phase 10's `/update release`).

## CI/CD edits

- None. `.github/workflows/ci.yml` already pip-installs the scanner editable and runs `pytest extensions/nexus-skill-scanner/tests/` (the `tests` job, added in Phase 6), so the new `test_signatures.py` is auto-discovered with no workflow change. Phase 7 added no new env var and no new dependency (the `yara-python` extra was removed, not added), so the install step is unchanged. 0 workflows touched.

## Deviations

- **Signature module is a pure-Python reverse-engineered matcher, not a `yara-python` wrapper** (see Key decisions). Recorded here rather than in `known-gaps.md` because it removes a dependency the plan would have added and improves policy alignment -- it is a deviation that strengthens the implementation, not an unfinished gap. The graceful-degrade test was re-pointed accordingly.

## Known gaps

See [`docs/releases/v3/v3.0/known-gaps.md`](../../known-gaps.md). Two new open items this phase: DF-v30-3 (the two optional modules ship deliberately minimal starter content -- 12 signature rules, 5-advisory offline seed -- to grow per release, mirroring DF-v30-1's philosophy) and WN-v30-4 (local `make` unavailable on the Windows host, gate emulated directly all-green; no shell surface this phase so no ShellCheck concern; covered by CI). DF-v30-1's note that "class 14 YARA + OSV are Phase 7, not gaps" is now discharged -- both modules have landed. Summary: 7 open (3 DF, 4 WN), 0 resolved.

## Next steps

- **Phase 8 -- Deprecation shims + migration + count reconciliation**: convert the 41 old command files into forwarding deprecation shims (preserving every permanent alias), write `docs/v3/v3.0/command-migration.md` with the old -> new -> scope table and the v4.0.0 removal timeline, add the rename table to `CHANGELOG.md`, and reconcile `marketplace.json` `total_commands` + the AGENTS.md/README count prose + the 5 platform instruction templates in lockstep.
