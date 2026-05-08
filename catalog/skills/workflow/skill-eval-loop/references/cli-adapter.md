# CLI-agnostic adapter design

The eval loop must work on whichever AI CLI the user has installed. DevAI-Hub supports four: `claude`, `gemini`, `codex`, `opencode`. The shape of "load a skill and run a prompt" differs per CLI, but the loop's bookkeeping (paired runs, grading, aggregation) does not. This file documents the design rationale, the per-CLI invocation patterns, and the parity-test specification.

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
def invoke_cli(cli: str, prompt: str, skill_path: str | None) -> dict:
    if cli == "claude":
        cmd = ["claude", "-p", prompt]
        if skill_path is not None:
            cmd.extend(["--skill", skill_path])
        return _run(cmd)
    if cli == "gemini":
        cmd = ["gemini", "--workflow", prompt]
        if skill_path is not None:
            cmd.extend(["--skill-file", skill_path])
        return _run(cmd)
    if cli == "codex":
        cmd = ["codex", "exec", prompt]
        if skill_path is not None:
            cmd.extend(["--prompt", skill_path])
        return _run(cmd)
    if cli == "opencode":
        cmd = ["opencode", "run", prompt]
        if skill_path is not None:
            cmd.extend(["--skill", skill_path])
        return _run(cmd)
    raise AssertionError(f"unsupported cli: {cli}")
```

Pros: ~50 lines of CLI-specific code per script (vs ~150 lines of duplication x 4 = 600); one bug-fix in the loop logic ships to all four CLIs at once. Cons: the parity invariant needs an explicit test (since deletion-safety no longer falls out of structure). The test exists at `catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter`.

**Selection**: Option B. The duplication ratio (50:150) is too high to justify Option A's deletion-safety affordance for files of this size. A single 50-line pytest module preserves the parity invariant at much lower maintenance cost.

## Per-CLI invocation patterns

The exact CLI flag surface evolves; this file documents the pattern as of v1.1.5. The dispatcher should treat each branch as the source of truth and update it when a CLI changes its flag scheme.

### Claude Code

```bash
claude -p "<prompt>" --skill <path/to/SKILL.md>
```

- Skill loading: `--skill <path>` (the file path, not the directory).
- Prompt: `-p "<text>"` for one-shot non-interactive mode.
- Token / duration capture: Claude Code prints these to stderr at the end of a session; the dispatcher parses the trailing `tokens used: N | duration: M ms` line. If absent, estimate.

### Gemini / Antigravity

```bash
gemini --workflow "<prompt>" --skill-file <path>
```

- Skill loading: `--skill-file <path>`.
- Prompt: `--workflow "<text>"` (Gemini's name for the one-shot input).
- Token / duration capture: Gemini emits a JSON line on stderr when `--telemetry json` is set; without it, estimate.

### Codex

```bash
codex exec "<prompt>" --prompt <path/to/SKILL.md>
```

- Skill loading: `--prompt <path>` (Codex treats skills as prompt overlays).
- Prompt: positional after `exec`.
- Token / duration capture: Codex prints `usage: input=N output=M total=K` on success; parse and capture.

### OpenCode

```bash
opencode run "<prompt>" --skill <path>
```

- Skill loading: `--skill <path>`.
- Prompt: positional after `run`.
- Token / duration capture: OpenCode does not currently emit tokens reliably; default to estimation.

## Parity-test specification

`catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter` enforces the no-cross-CLI-bleed invariant by inspecting each dispatcher script's source directly (the same technique as `test_diff_review_hooks.py::TestPlatformIndependence`). For each `if cli == "X":` branch, the test asserts:

1. The branch's `subprocess.run(...)` / `subprocess.Popen(...)` calls have `argv[0]` equal to `"X"` (the same CLI name as the branch).
2. No other CLI binary name appears anywhere within the branch's body.

The test is parametrized over the cross product of (script, cli), so any cross-CLI bleed introduced in any of the three dispatcher scripts produces a single targeted failure pinpointing the script and the offending branch.

## Why the parity invariant matters

The v1.1.3 four-hook precedent was reverse-engineered from a real bug: a hook that fell through to a different CLI when its primary was missing, silently doing the wrong thing (and producing outputs the user attributed to the primary CLI). The parity invariant prevents that bug class. For the eval loop specifically, the failure mode would be even worse: the with_skill run nominally on Claude, the without_skill run nominally on Claude, but one of them silently fell through to Gemini - the resulting `benchmark.json` would compare apples to oranges and the user would optimize the skill against the wrong CLI's behavior. The parity test costs ~50 lines of pytest and catches the entire class.
