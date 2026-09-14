# Phase 1 evidence - Cache accounting and baseline

Renumber note, 2026-09-14: this historical cache-track evidence was authored under v4.11.0; its current plan is v4.11.1. Historical test results and phase dates remain unchanged.

Evidence for Phase 1 (T001-T003) of the [v4.11.0 adoption plan](../plans/v4.11.1-adoption-cache-and-diagram-quality.md). Covers the pre-change baseline, the reproduced 900% defect, the corrected three-bucket arithmetic, the regression that executes the shipped snippet, and the installer distribution boundary. Read this to confirm D1 before Phase 2 extends the same owner.

## T001 - Existing-owner baseline

**Baseline commit**: `de7697b3e7165e1775c84c185293bfedba5f8dd9` on `feat/v4.11.0-cache-and-diagram`, branched from `develop` at `c79fc15f`.

**Owner inspected**: `catalog/skills/ai-development/prompt-engineering/references/step-8-optimize-cost-and-latency.md`, 64 lines, one H3 heading, three fenced blocks. A repository-wide search for the cache telemetry fields returned exactly one hit, in this file:

```text
$ grep -rn "cache_creation_input_tokens|cache_read_input_tokens" catalog/ scripts/ tests/
catalog/skills/ai-development/prompt-engineering/references/step-8-optimize-cost-and-latency.md:37
```

No other skill, script, or test consumes these fields, so the correction has a single owner and no downstream caller to migrate.

### Reproduced defect

The pre-change snippet read:

```python
cached_input = getattr(usage, "cache_read_input_tokens", 0)
total_input = usage.input_tokens
savings_pct = (cached_input / total_input) * 100 if total_input else 0
```

The Anthropic usage schema reports input in three disjoint buckets, and `input_tokens` counts only the uncached portion. With uncached = 100 and cache-read = 900 the expression evaluates `900 / 100 * 100`, printing **900% cached**. The defect is worst-case silent: the figure only exceeds 100% when caching is working well, so a healthy system produces the most obviously wrong number and an unhealthy one produces a plausible one.

The pre-change code also labelled the figure `savings_pct` and printed it as a cache hit, conflating a token proportion with money saved.

### Strict D1 cases enumerated

| Uncached | Cache read | Cache created | Required outcome |
|---|---|---|---|
| 100 | 900 | 0 | 90% |
| 0 | 900 | 0 | 100% |
| 100 | 0 | 0 | 0% |
| 100 | 900 | 200 | 75% |
| 0 | 0 | 0 | unknown - no input, not a 0% cache rate |
| missing, negative, fractional, non-numeric, non-finite | | | unknown or error |

### Accepted usage shapes

The example accepts any object exposing the three attributes, which covers the SDK response `usage` object and a synthetic stand-in. `input_tokens` is required; a response missing it yields unknown. The two cache buckets are optional and default to `0`, because a supported no-cache response legitimately omits them. That default is deliberately distinguished from a missing telemetry object, which yields unknown rather than 0%.

### Test and distribution boundary

`scripts/ci/profiles.py` defines the `TESTS` group as `pytest catalog/hooks/tests` plus `pytest tests`. The second command collects `tests/skills/`, so a new module there is already covered by the `full` profile with no profile edit.

`.github/workflows/ci.yml` job `installer-smoke` runs the real platform-native installer on an `ubuntu-latest` / `macos-latest` / `windows-latest` matrix into redirected `HOME`, `USERPROFILE` and `NEXUS_HUB_HOME` roots, then invokes `scripts/check_installer_smoke.py` for shared postconditions. `catalog/hooks/tests/test_installer_smoke.py` is a separate structural suite asserting the installers reference each expected script by name; it is not a real installer run and is kept distinct in this evidence.

## T002 - Corrected cache-share example

The example now sums all three buckets and reports a token proportion. `read_token_bucket` rejects a value that cannot be counted; `cache_read_share` returns a fraction or `None`; `describe_cache_share` renders the log line without asserting a saving. The API-calling function is retained and delegates to the shared helper, so the accounting path is reachable without a client.

Behavioural decisions:

- The denominator is `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`.
- An all-zero request returns `None`, explicitly documented as no input rather than evidence that caching is ineffective.
- A negative, fractional, non-finite, non-numeric or boolean count returns `None`. An untrustworthy number is worse than an absent one because it survives into a cost review unchallenged.
- The word "saved" does not appear in the rendered output, and a test asserts its absence.
- Usage objects stay request-local; no module state accumulates, so concurrent requests cannot mix totals.
- No network access and no SDK install is required at any point.

## T003 - Testing and stabilization

### New regression

`tests/skills/test_cache_share_example.py` extracts the fenced `python` block containing `def cache_read_share` from the shipped Markdown and executes it, rather than copying the formula. Reverting the documentation therefore fails the suite. It asserts the four D1 numeric cases, the specific over-100% regression shape, the unknown outcomes, the optional-field default, six untrustworthy input types, and that the rendered string makes no cost claim.

```text
$ python -m pytest tests/skills/test_cache_share_example.py -q
..................
18 passed in 0.09s
```

### Lint and format

```text
$ python -m ruff check tests/skills/test_cache_share_example.py
All checks passed!

$ python -m ruff format tests/skills/test_cache_share_example.py
1 file reformatted
```

### Native fast profile

```text
$ python scripts/ci/run.py --profile fast
PASS: 13 passed, 0 failed, 0 skipped, 0 advisory in 84.9s
```

### Real installer boundary (Windows host)

Run with the maintainer's explicit approval, using the exact commands from the `installer-smoke` Windows leg, into a short redirected root outside the working tree:

```text
$ powershell -NoProfile -ExecutionPolicy Bypass -File scripts\installer.ps1 -Workspace <temp>\workspace -Platforms claude -Yes
Nexus-Hub v4.9.0 installed (Workspace scope).

$ python scripts\check_installer_smoke.py --home <temp>\home --workspace <temp>\workspace
installer smoke: PASS
```

`USERPROFILE`, `HOME` and `NEXUS_HUB_HOME` were all redirected before the run. The real `~/.nexus-hub` recorded a `LastWriteTime` of 10:52:06 against a run at 11:06:38, confirming the redirect held and the profile was untouched. The temporary root was removed afterwards.

### Limitations

- Linux and macOS installer proof is unavailable on this Windows host. It remains explicitly pending for the existing three-OS matrix at Phase 6 T020/T025, exactly as the plan's platform-proof order requires. This is recorded as uncovered evidence, not as a pass.
- The regression exercises the documented accounting path deterministically. It does not and cannot prove live provider cache behaviour; that claim is out of scope for this plan and belongs to the separate qualified v4.11 evaluation path.

### CI impact

No new command, runtime dependency, environment variable, or artifact. One new test path, `tests/skills/test_cache_share_example.py`, already collected by the existing `TESTS` group's `pytest tests` step in the `full` profile. Coverage was inspected and found sufficient; no profile edit is proposed, and nothing is carried forward to the Phase 6 reconciliation.
