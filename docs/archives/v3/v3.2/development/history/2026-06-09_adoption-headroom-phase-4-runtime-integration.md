# Session History -- v3.2.0 adoption-headroom Phase 4: Runtime integration + retire rtk

**Date**: 2026-06-09
**Plan**: [`docs/releases/v3/v3.2/plans/adoption-headroom.md`](../../plans/adoption-headroom.md)
**Phase**: 4 of 7 -- Runtime integration + retire rtk (re-full)
**Branch**: `feat/adoption-headroom` (continuing from Phase 3)
**Outcome**: complete; all four sub-tasks (T012-T015) closed, all quality gates green (GO).

## Goal

Wire the deterministic engine (Phases 1-3) into a live agent session and supersede the external `rtk` recommendation: a PreToolUse hook that compresses Bash output before it enters context, an internal MCP server exposing `context_compress` + `context_retrieve`, and a rewrite of the rtk guide that points users at the owned engine with a migration note. All local, zero new outbound, no credential.

## Branch correction (pre-work)

The session opened on `develop` with `HEAD` at a loop-engineering docs commit; only stale `.pyc`/`.coverage` artifacts of the compressor were present on disk (gitignored, left behind by a prior checkout), with no tracked source -- confirming Phases 1-3 lived elsewhere. `git ls-files` showed the full Phase 1-3 source on `feat/adoption-headroom` (in sync with its remote, `a4aeaef`). Switched to `feat/adoption-headroom` (clean tree, safe) before any Phase 4 work, keeping the headroom feature isolated on its own branch per the develop+main model.

## Subtasks completed

1. **Runtime seam (enabling work for T012/T013).** Added `compress_output(text, *, persist=True, store=None, config=None) -> RouteResult` to `__init__.py` -- the single-blob entry the hook (via the CLI) and the MCP tool call. It runs `ContentRouter`, opens the default CCR store when `persist` so drops are reversible, and adds two runtime-boundary guarantees the raw `route()` lacks: **never expand** (if reserializing a sub-threshold JSON array would grow it, return the original verbatim) and **never lose output** (a missing/unwritable cache dir degrades to non-persisting compression rather than raising). Rewired `compress(messages)` to route each message's content (no longer the Phase 1 no-op; identity on prose, so the scaffold tests stay green). Added `cli.py` (`compress` reads stdin, `retrieve` resolves a marker, `serve` launches the MCP server; `compress` is fail-open) and pointed `__main__.py` at it while preserving the bare-invocation identity print.
2. **T012 -- PreToolUse compression hook** (`catalog/hooks/compress-output.sh`). Opt-in / default-off (inert unless `NEXUS_CONTEXT_COMPRESS=1`, mirroring git-guardrails' protected-branch guard). When enabled it reads the PreToolUse JSON, and -- gated on `jq` and on the engine importing cleanly (so output is never piped into a missing compressor) -- emits a `hookSpecificOutput.updatedInput` that rewrites the command to `{ <ORIG> ; } | python -m nexus_context_compressor compress; exit ${PIPESTATUS[0]}`, piping stdout through the engine while preserving the original exit status and leaving stderr untouched. Registered in `catalog/hooks/settings.json` (PreToolUse Bash, after the guards) and copied by both installers. Windows path is CLAUDE.md-injected instructions (hooks need a Unix shell), exactly as the prior rtk integration documented. pytest suite at `catalog/hooks/tests/test_compress_output_hook.py` (inert paths run everywhere; rewrite-path tests run when `jq` + an importable engine are present, skip gracefully otherwise).
3. **T013 -- internal MCP server** (`server.py`). Exposes `context_compress(payload, persist)` and `context_retrieve(marker)` over stdio, modeled on `nexus-web-fetch`. `mcp` is an optional `[mcp]` extra and is imported lazily inside `run_server`, so the module (and its pure `do_compress` / `do_retrieve` handlers + `SERVER_INSTRUCTIONS`) import and test without the extra. Registered in `catalog/mcp-configs/mcp-servers.json` (`re-full`, full 5-question audit), with a reverse-engineering matrix row, auto-registered + `[mcp]`-installed by both installers, and a CI step added (the compressor extension suite was not previously CI-gated).
4. **T014 -- supersede rtk** (`guides/RTK_CONTEXT_COMPRESSION.md`, `templates/ai-instructions/base-claude.md`). Rewrote the guide to lead with the internal engine (no Rust, local-first, reversible), with platform table, enable/Windows paths, a "Migrating from rtk" section, and the preserved cross-platform output-minimization guidance. Updated the Claude template's one rtk reference line. Honest about scope: the engine reaches rtk parity on **structured** output (JSON/code) today; free-text/log compression is the optional Phase 6 ML module.
5. **T015 -- tests + stabilization.** Ran the full battery (see Test results). All green; iterated on two real defects caught during stabilization (below).

## Key decisions

- **`compress_output()` is the runtime seam; `route()` stays a pure Phase 3 strategy.** The hook/MCP need "compress a blob, persist drops, never make it worse". Putting the never-expand / never-lose-output policy in `compress_output` (the integration boundary) rather than in `route()` kept the 130 Phase 1-3 tests untouched and the strategy predictable.
- **Rewired `compress(messages)` without breaking the scaffold.** `route()` no-ops on prose, so routing each message's content leaves all-prose input byte-identical and `transforms_applied == []` -- the Phase 1 identity test still passes. This resolved DF-v32hr-7 (the no-op deferral) without a test rewrite.
- **Hook is opt-in, jq-gated, and import-gated -- output can never be lost.** Three guards before any rewrite (env flag, jq present, engine importable) plus the CLI's own fail-open contract mean the worst case is "no compression", never "lost output". Exit code preserved via `PIPESTATUS`; stderr left untouched.
- **`mcp` as an optional extra with a lazy import.** Unlike `nexus-web-fetch` (an MCP-only package with `mcp` as a hard dep), this package is primarily an engine + CLI, so `mcp` is optional and imported only inside `run_server`. The installer installs the `[mcp]` extra and registers the server; the engine still works air-gapped without it.
- **Honest rtk parity, not overclaim.** The deterministic engine compresses structured output and passes free-text through; rtk also compressed logs. Rather than claim full parity, T014 documents the scope and defers free-text to Phase 6 (DF-v32hr-10). The reversible CCR store is led as the real differentiator over (lossy) rtk.
- **Closed a CI gap found mid-phase.** CI ran the other four extension suites but not the compressor's (a Phase 1-3 oversight). Added the step so the new runtime/MCP tests actually gate.

## Test results

- Package suite: **159 passed** (29 added in Phase 4: runtime, CLI, MCP handlers).
- `catalog/hooks` suite: **434 passed** (incl. 8 new hook tests; rewrite-path exercised with `jq` on PATH).
- `tests/validators` **136**, `tests/installer` **70**, `tests/integrations` **197** -- all passed (no regressions from the settings.json / installer edits).
- `make validate` validators (bundles, version-sync, no-personal-paths, unicode-safety, supply-chain-iocs, workflow-security): **0 errors** (the unicode WARNs are pre-existing legacy templates). Skill-security scan gate: **exit 0** (no new HIGH/CRITICAL; the new MCP entry uses `python -m`).
- `make lint` (ShellCheck): `compress-output.sh` **clean** (one intentional `SC2016` disabled -- `${PIPESTATUS[0]}` must reach the target shell literally); `installer.sh` **clean** at `--severity=warning`. `installer.ps1` parses clean.
- Installer dry-run: a throwaway venv `pip install -e "extensions/nexus-context-compressor[mcp]"` then `import nexus_context_compressor, mcp` and `python -m nexus_context_compressor serve` -- engine + mcp import OK, server started and shut down cleanly on EOF (exit 0).

## CI/CD edits

- `.github/workflows/ci.yml`: added an "Install context-compressor engine (v3.2.0+)" + "Context-compressor tests" step pair (mirroring the other extensions), closing the gap where the compressor suite was never CI-gated.
- `scripts/installer.sh` and `scripts/installer.ps1`: copy `compress-output.sh` alongside `git-guardrails.sh`; install the compressor with the `[mcp]` extra; register `nexus-context-compressor` (`python -m nexus_context_compressor serve`) in the auto-merged `mcpServers` block. ShellCheck caught `SC1087` -- `"$dest[mcp]"` is array-subscript syntax to bash -- fixed to `"${dest}[mcp]"` so the editable-with-extras install is correct.

## Deviations

- **Hook event/mechanism.** The plan says "PreToolUse ... pipes tool output through the compressor, at the same hook point rtk uses". PreToolUse cannot see output, so (as rtk does) the hook rewrites the command to pipe its stdout through the engine via `hookSpecificOutput.updatedInput`. The repo's settings reference documents only the exit-code hook contract, so this relies on Claude Code honoring `updatedInput`; the hook is fail-safe (a no-op if unsupported) and the dependency is logged as WN-v32hr-1.
- **Methodology-skill cross-links not touched.** T014's "supersede the rtk recommendation" was scoped to the guide + Claude template; `context-optimization/SKILL.md` still documents rtk setup. Cross-linking the engine into the three methodology skills is Phase 7's T021, so it was intentionally deferred (DF-v32hr-11) to respect the phase boundary.
- **Auto-prune still unwired (DF-v32hr-4).** The runtime now exists, but neither the hook nor the MCP invokes `store.prune(...)`; the prune policy choice was deferred rather than guessed.

## Troubleshooting / environment notes

- **Hook `set -e` + grep-fallback bug.** The first hook draft used a jq-with-grep/sed fallback to read the command; on a no-command payload `grep` exits 1, which `pipefail` + `set -e` turned into a hook exit 1. Since the rewrite needs `jq` anyway, dropped the grep fallback and gated the whole hook on `jq` up front -- simpler and the test (`test_non_bash_tool_is_passthrough`) goes green.
- **Tiny-JSON expansion.** A sub-threshold JSON array (`[1,2,3]`) round-tripped through the router gets pretty-printed (indent=2) and *grows* (7 -> 14 tokens). Added the never-expand guard in `compress_output` so the runtime never enlarges a payload.
- **`jq` absent on the Windows dev host.** Downloaded a throwaway `jq.exe` onto PATH to exercise the hook's rewrite-path tests end-to-end (build the rewrite, execute it, confirm compression + exit-code preservation on both a passing and a failing command). Logged as WN-v32hr-2; CI (ubuntu) has jq.
- `make` is not on PATH (WN-v32-2 root class); every target was emulated by invoking the underlying validator / scanner / pytest directly.

## Known gaps

Logged in [`docs/releases/v3/v3.2/known-gaps.md`](../../known-gaps.md): DF-v32hr-7 resolved (compress wired + hook/MCP shipped); new DF-v32hr-9 (CacheAligner not wired into the runtime path), DF-v32hr-10 (free-text/log compression deferred to Phase 6), DF-v32hr-11 (methodology-skill cross-links deferred to Phase 7), WN-v32hr-1 (hook relies on `updatedInput`), WN-v32hr-2 (partial local verification); DF-v32hr-4 (auto-prune) refined and kept open.

## Next steps

- **Phase 5 (Accuracy-regression harness)**: build `evals/` measuring compression ratio vs. a deterministic accuracy proxy (CCR round-trip completeness, signature-preservation rate), and wire a CI fidelity gate. This is the gate Phases 1-3's deferred refinements (near-dup fingerprinting, adaptive sizing, error/outlier preservation) wait on before they ship.
