# Phase 2 Evidence -- Private agent traces and observable evidence

**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Candidate**: A6
**Phase**: 2 of 7
**Prior phase commit**: `0f407bc1` (verified ancestor of HEAD)

No model was invoked in this phase. Every emitted record is synthetic and generated locally.

## Upstream verification

The span contract was written against a pinned revision, re-fetched during implementation as the plan requires.

| Item | Value |
|---|---|
| Source | OpenTelemetry semantic conventions, GenAI agent spans |
| Pinned revision | `5ca9052bc796ef1e497200b1d558fd87a201f335` |
| Upstream status | Development |
| Verified on | 2026-09-15 |

Operation names, span kinds, and the Required / Conditionally Required / Recommended / Opt-In attribute tiers were read from that revision and transcribed verbatim.

### Partial verification, recorded rather than guessed

The `execute_tool` operation name is confirmed. **The `gen_ai.tool.*` attribute table could not be retrieved at the pinned revision**: the containing document truncates before that section, and the standalone tool-spans path returns HTTP 404 at that revision.

The contract therefore marks tool attributes unverified and instructs the reader to verify against the sibling specification before naming one. No `gen_ai.tool.*` requirement level was invented to fill the gap, per the plan rule that unavailable data is omitted or explicitly unknown.

## Artifacts added

| Path | Kind | SHA-256 (first 16) |
|---|---|---|
| `catalog/skills/ai-development/ai-agent-development/references/agent-span-contract.md` | pinned contract | `b6e3b2950fff1b12` |
| `catalog/skills/ai-development/ai-agent-development/scripts/trace-example.py` | runnable demonstration | `52efd8d8f2e0057b` |

Both are linked from the owning `SKILL.md`, so the recursive installer delivers them with no installer edit. The bundle audit reports no orphan warning for this skill.

### Script size against the declared ceiling

The plan sets a ceiling of 150 nonblank source lines.

| Measure | Count |
|---|---|
| Source lines of code (excluding comments and docstrings) | **127** |
| All nonblank lines (including comments and docstrings) | 160 |

The executable body is 127 lines, inside the ceiling. The 33 additional lines are the module docstring and inline comments that carry the privacy rationale, which is the part of this file a reader has to understand in order to copy it safely. They are retained deliberately and recorded here rather than silently expanding the budget.

## Verification Expectation

```
$ python catalog/skills/ai-development/ai-agent-development/scripts/trace-example.py --output <fresh-temp-dir>/trace.jsonl
wrote 5 synthetic records to <fresh-temp-dir>/trace.jsonl
payloads, tool arguments, results, instructions and raw exceptions omitted

$ python -m pytest -q tests/skills/test_evidence_driven_improvement.py --no-cov
61 passed in 0.57s

$ python scripts/validate_skills.py --bundles-only
RESULT: PASS (0 errors, 66 warnings)
```

Warning count is unchanged from the Phase 1 baseline of 66, so the new bundles introduced no new warning. Strict ASCII check over the four changed Markdown files and both Python files reported 0 non-ASCII characters.

### Observed record structure

| Property | Observed |
|---|---|
| Records emitted | 5 |
| Root spans | 1 |
| Orphaned parent references | 0 |
| `trace_id` width | 32 hex, all records |
| `span_id` width | 16 hex, all records |
| Timestamps | UTC, `Z`-suffixed |
| Terminal status | every record `OK` or `ERROR` |
| Span kinds present | `CLIENT`, `INTERNAL` |
| Operations present | `invoke_workflow`, `invoke_agent`, `execute_tool` |

The local and remote `invoke_agent` records carry `INTERNAL` and `CLIENT` respectively, which is the distinction the contract exists to preserve.

### Privacy result

The generator holds two sentinel values, so omission is proven against data known to have been present rather than against an empty input:

| Sentinel | Represents | Present in output |
|---|---|---|
| `sk-live-SENTINEL-must-not-appear` | a credential in tool arguments | **no** |
| `PermissionError: /home/real-user/.ssh/id_rsa SENTINEL` | a raw exception string with a path | **no** |

The failed tool call records `error.type: permission_denied`, an allowlisted category derived from the sentinel exception whose text was read and discarded. No Opt-In payload attribute (`gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.system_instructions`, `gen_ai.tool.definitions`) appears anywhere in the output.

### Negative controls observed

| Control | Expected | Observed |
|---|---|---|
| Existing output file | refuse, exit 2, leave file intact | refused; original bytes unchanged |
| Missing parent directory | refuse, exit 2 | refused |
| Payload-enable flag | absent from source | absent |
| Network / environment capture | absent from source | absent |
| Code-block extractor helper | must return real code and no prose | asserted both directions |

The last row guards the test rather than the product: a helper that silently returned an empty string would have made four leak assertions pass vacuously.

## Teaching corrections

The previous observability example leaked three ways. All three are removed from the code block and explained in prose:

| Removed | Why it leaked |
|---|---|
| `str(args)[:200]` | Truncation is not redaction; 200 characters of a prompt is still the prompt |
| `str(result)[:200]` | Same, on the output side |
| `str(e)` | Exception text carries paths, connection strings and row data |
| `uuid.uuid4().hex[:12]` | A shortened trace ID raises collision probability and saves nothing |

`loop-schema.md` was amended only where it claimed `trace_log` records reasoning. It now separates an available summary from unavailable internal reasoning, and a host-observed event from a self-attestation. Existing budgets, `evidence_freshness`, additive-optional field semantics, and owners are untouched, and a test asserts that.

## CI impact record (Phase 2)

Recorded against `[[cicd-architect]]`. No pipeline file changed; CI/CD is not this phase's deliverable.

| Dimension | This phase | Covered by existing profiles |
|---|---|---|
| New commands | `trace-example.py` is invoked by the test suite, not by CI directly | yes, through the existing test selection |
| New dependencies | none (standard library only) | yes |
| New environment variables | none | n/a |
| New test paths | none beyond the Phase 1 module | yes |
| New artifacts | none published by CI; the example writes only to a caller-supplied temp path | n/a |

The test spawns a subprocess with a 60-second timeout and writes only into pytest's `tmp_path`, so it leaves no repository state behind. Nothing from this phase is carried into the terminal reconciliation.

## Phase 2 gate

| Gate element | Result |
|---|---|
| Test failures | 0 (61 passed) |
| Lint errors | 0 new |
| Build | n/a |
| Functional smoke | example executed end-to-end into a fresh temp directory; output parsed and structurally validated |
| Feature matches expected behavior | yes -- valid parent links, correct span kinds, zero sentinel leakage |

**Verdict: GO.**

## Limitations

- The records are fabricated. They demonstrate the shape and the privacy default; they are not evidence that any real integration is correctly instrumented.
- `gen_ai.tool.*` attributes remain unverified at the pinned revision and must be checked before use.
- The upstream convention is at Development status, so these names carry no stability guarantee.
