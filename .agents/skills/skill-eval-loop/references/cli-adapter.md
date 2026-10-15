# CLI-agnostic adapter design

The eval loop must work on whichever AI CLI the user has installed. Nexus-Hub supports four: `claude`, `gemini`, `codex`, `opencode`. The shape of "load a skill and run a prompt" differs per CLI, but the loop's bookkeeping (paired runs, grading, aggregation) does not. This file documents the design rationale, the per-CLI invocation patterns, and the parity-test specification.

## The two design options

### Option A: four parallel scripts (rejected)

```
scripts/eval_loop_claude.py
scripts/eval_loop_gemini.py
scripts/eval_loop_codex.py
scripts/eval_loop_opencode.py
```

This is the v1.1.3 four-hook precedent applied verbatim: each script is fully self-contained, no shared library, no cross-CLI fallback. Pros: trivially obvious that no script can call the wrong CLI; deletion-safe (removing one CLI's support means deleting one file). Cons: ~150 lines of duplication per script (workspace layout, JSON I/O, paired-run plumbing) - 600 lines of duplicated code for ~50 lines of CLI-specific logic.

The v1.1.3 hooks were 80 lines each; duplication was acceptable. The eval-loop dispatchers are ~250-400 lines each; duplication is not.

### Option B: single dispatcher with `--cli` flag (selected)

```
scripts/skill_eval_viewer.py        # one file, dispatches on --cli
scripts/aggregate_benchmark.py      # one file, dispatches on --cli
scripts/optimize_skill_description.py  # one file, dispatches on --cli
```

Each script has a hard `assert cli in {"claude", "gemini", "codex", "opencode"}` near the top, then a per-CLI dispatch branch:

```python
def build_cli_command(cli, prompt, skill_path, model, project_dir=None) -> list[str]:
    assert cli in {"claude", "gemini", "codex", "opencode"}
    if cli == "claude":
        if skill_path is None:
            return ["claude", "-p", prompt, "--setting-sources", "", "--model", model]
        return ["claude", "-p", prompt, "--model", model,
                "--output-format", "stream-json", "--verbose",
                "--setting-sources", "project", "--strict-mcp-config",
                "--add-dir", str(project_dir)]
    if cli == "gemini":
        raise RuntimeError("gemini configuration isolation is not documented")
    if cli == "codex":
        cmd = ["codex", "exec", "--ignore-user-config", "--ignore-rules",
               "--ephemeral", "--model", model]
        if skill_path is not None:
            cmd += ["--cd", str(project_dir), "--skip-git-repo-check"]
        return cmd + [prompt]
    if cli == "opencode":
        raise RuntimeError("opencode configuration isolation is not documented")
```

Neither shipped CLI has a flag that loads one skill file. `invoke_cli` therefore copies the SKILL.md under test into a throwaway project directory at the CLI's native project skills root and runs the CLI from there, so the skill is discovered the way a user's project skill is. An earlier version of this file documented `--skill <path>` and `--prompt <path>`; neither flag exists (v4.13 AR-04).

Pros: ~50 lines of CLI-specific code per script (vs ~150 lines of duplication x 4 = 600); one bug-fix in the loop logic ships to all four CLIs at once. Cons: the parity invariant needs an explicit test (since deletion-safety no longer falls out of structure). The test exists at `catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter`.

**Selection**: Option B. The duplication ratio (50:150) is too high to justify Option A's deletion-safety affordance for files of this size. A single 50-line pytest module preserves the parity invariant at much lower maintenance cost.

## Per-CLI invocation patterns

The exact CLI flag surface evolves. The findings below were verified against official vendor documentation on 2026-09-21; the Gemini and OpenCode isolation limitations were rechecked on 2026-09-25. Every provider-backed run requires an explicit model pin; a runner with no documented all-configuration isolation fails closed instead of silently falling back.

### Claude Code

**Runner**: `claude`

**Isolation status**: supported. The no-skill arm uses `--setting-sources ""`, an empty list of user, project, and local setting sources. The skill arm uses `--setting-sources project` from a throwaway project directory, so the staged skill is the only project corpus and the user's catalog stays out; `--strict-mcp-config` with no `--mcp-config` drops every MCP server.

**Model pin**: `--model <model>` is mandatory.

**Official source**: [Claude Code CLI reference](https://code.claude.com/docs/en/cli-usage), verified 2026-09-21; flags re-checked against the installed `claude --help` of Claude Code 2.1.283 on 2026-10-10.

```bash
# cwd = <tmp>, with the skill copied to <tmp>/.claude/skills/<name>/SKILL.md
claude -p "<prompt>" --model <model> --output-format stream-json --verbose \
  --setting-sources project --strict-mcp-config --add-dir <tmp>
```

- Skill loading: the skill is staged in the project skills root and never forced in, so the run measures whether the model selects it. This is the invocation `scripts/run_trigger_pilot.py` used.
- Trigger detection: a `Skill` tool call naming the skill in the stream-json transcript. The phrase heuristic applies only to plain-text output.
- Prompt: `-p "<text>"` for one-shot non-interactive mode.
- Token / duration capture: parse the CLI's trailing usage output when present; otherwise record that the value was estimated.

### Gemini / Antigravity

**Runner**: `gemini`

**Isolation status**: limitation - no all-configuration isolation flag is documented. `-e none` disables extensions, and `GEMINI_CLI_HOME` redirects user-level configuration and storage, but the official configuration reference still describes separate system, project, environment, and command-line layers. The documented home override alone does not establish an isolated baseline. Evals on this runner are refused and are not comparable to isolated runs.

**Model pin**: `--model <model>` is documented, but a model pin alone does not make the run isolated.

**Official source**: [Gemini CLI configuration reference](https://geminicli.com/docs/reference/configuration/), rechecked 2026-09-25.

No invocation is emitted until a documented and tested per-run exclusion covers every configuration source.

### Codex

**Runner**: `codex`

**Isolation status**: supported with `--ignore-user-config --ignore-rules --ephemeral`. The first excludes `$CODEX_HOME/config.toml`, the second excludes user and project execpolicy rules, and the third prevents session persistence.

**Model pin**: `--model <model>` is mandatory.

**Official source**: [OpenAI Codex exec CLI source](https://github.com/openai/codex/blob/main/codex-rs/exec/src/cli.rs), verified 2026-09-21; flags re-checked against the installed `codex exec --help` of codex-cli 0.136.0 on 2026-10-10.

```bash
# the skill is copied to <tmp>/.agents/skills/<name>/SKILL.md
codex exec --ignore-user-config --ignore-rules --ephemeral --model <model> \
  --cd <tmp> --skip-git-repo-check "<prompt>"
```

- Skill loading: the skill is staged under the `.agents/skills` project root that Codex discovers (see `docs/policy/platform-read-contracts.json`). `codex exec` has no skill-file flag.
- Trigger detection: plain-text output, so the phrase heuristic. No live run has yet confirmed that Codex discovers the staged skill from `--cd`.
- Prompt: positional after `exec`.
- Token / duration capture: parse the CLI's usage output on success.

### OpenCode

**Runner**: `opencode`

**Isolation status**: limitation - no all-configuration isolation flag is documented. `--pure` disables external plugins only; the official configuration reference says config sources are merged, a custom config directory is additive, and managed settings take highest priority. Evals on this runner are refused and are not comparable to isolated runs.

**Model pin**: `--model <provider/model>` is documented, but a model pin alone does not make the run isolated.

**Official source**: [OpenCode CLI reference](https://dev.opencode.ai/docs/cli/) and [configuration reference](https://dev.opencode.ai/docs/config/), rechecked 2026-09-25.

No invocation is emitted until a documented and tested per-run exclusion covers every configuration source.

## Model pin and conflict rule

Isolation removes saved model and effort settings. Without an explicit pin, the CLI default can vary by operator and release, and per-token cost varies with it. The run-level `--model` value is therefore mandatory and must be recorded with published results. If an eval entry contains a different `model`, the run fails with a named conflict; the adapter never lets a per-eval value silently replace the run pin.

## Parity-test specification

`catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter` enforces the no-cross-CLI-bleed invariant by inspecting each dispatcher script's source directly (the same technique as `test_diff_review_hooks.py::TestPlatformIndependence`). For each `if cli == "X":` branch, the test asserts:

1. The branch's `subprocess.run(...)` / `subprocess.Popen(...)` calls have `argv[0]` equal to `"X"` (the same CLI name as the branch).
2. No other CLI binary name appears anywhere within the branch's body.
3. The branch either contains the documented isolation flags and one explicit model pin or fails closed with the sourced limitation.
4. The four runner markers in this reference exactly match the runtime branch set.

A second test, `tests/validators/test_eval_harness_cli_flags.py`, checks every flag the builder emits against captured `--help` text in `tests/fixtures/cli-help/`, so a flag the CLI does not accept fails offline. Re-capture those fixtures when a CLI release changes its flags.

The test is parametrized over the cross product of dispatcher and CLI, so any cross-CLI bleed introduced in the runtime command builder produces a single targeted failure pinpointing the script and branch.

## Why the parity invariant matters

The v1.1.3 four-hook precedent was reverse-engineered from a real bug: a hook that fell through to a different CLI when its primary was missing, silently doing the wrong thing (and producing outputs the user attributed to the primary CLI). The parity invariant prevents that bug class. For the eval loop specifically, the failure mode would be even worse: the with_skill run nominally on Claude, the without_skill run nominally on Claude, but one of them silently fell through to Gemini - the resulting `benchmark.json` would compare apples to oranges and the user would optimize the skill against the wrong CLI's behavior. The parity test costs ~50 lines of pytest and catches the entire class.
