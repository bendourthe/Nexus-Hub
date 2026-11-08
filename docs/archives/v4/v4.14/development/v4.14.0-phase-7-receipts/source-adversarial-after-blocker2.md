# Actual Source Adversarial Retest

**Date**: 2026-10-16. **Implementation**: current actual v4.14.0 installer after the approved strict patch and hook repair. **Exact tested installer SHA-256**: `9be0ae34d1eb0632af691dab24c8f559c40c99bf5919b4e2950d01793b6fdc9b`. Both runtime directories retain the tested installer bytes. This is a bounded independent assessment, not full qualification or a completion claim.

## Scope and Safety

Applicable instructions and the prior adversarial procedure remain in force. The current native-hook permanent tests were inspected, and these probes deliberately cover different inputs. Direct native helpers and the real hook-conversion and permission Python boundaries run against fresh Temp profiles. No tracked source, prior candidate, guard, approval, repair counter, Git state, real profile, installed dependency or remote service was changed. No paid model/API call, global installation, full installer, whole suite, publication or network model call was started.

The helper sequence is actual hook installation, core settings, actual allow-permission merge, strict overlay and MCP registration. File-copy helpers are no-ops; minimal Temp packages and controlled dependency success expose the real MCP reader/writer without downloading or installing dependencies. Exact arguments, outputs, settings before every stage and check results are retained in `ps51/results.json` and `ps7/results.json`. All findings below are observed against the named source hash.

## Confirmed Findings

### AF-4: JSON readers coerce opaque strings into dates (P2)

**Verifier**: deterministic. **Boundary**: Read-JsonDocument and any subsequent settings writer. Strings that happen to match a recognized date representation are not always retained as opaque strings. This can change existing user environment values and custom MCP arguments or environment values during an otherwise unrelated installer update.

In a complete PowerShell 7.6.7 sequence, the string `2030-01-02T03:04:05+05:30` becomes `2030-01-01T13:34:05-08:00`. This was observed independently in four locations: a user env value, a custom MCP argument, that server's env value and an unrelated custom field. Native exit is 0. The first change is already visible after the first hook write. `date-offset-proof.py` exits 1 on the preservation assertion after recording both runtimes; `date-offset-results.json` retains exact native argv and results. PowerShell 5.1 preserves those tested ISO strings.

Separate direct-reader tests isolate value parsing from key parsing:

| Value shape | Windows PowerShell 5.1 | PowerShell 7.6.7 |
|---|---|---|
| `2030-01-02T03:04:05Z` | Same value | Same final value |
| `2030-01-02T03:04:05.120Z` | Same value | Becomes `2030-01-02T03:04:05.12Z` |
| `2030-01-02T03:04:05+05:30` | Same value | Becomes `2030-01-01T13:34:05-08:00` |
| `2030-01-02T03:04:05-04:00` | Same value | Becomes `2030-01-01T23:04:05-08:00` |
| `2030-01-02T03:04:05+00:00` | Same value | Becomes `2030-01-01T19:04:05-08:00` |
| Date-only or prefixed date text | Same value | Same value |

Identical date-shaped object keys were separately tested and preserved on both runtimes. Nine-fraction UTC strings used in the initial broad input were also unchanged; no fractional-precision loss is claimed for those values. Offset normalization and fractional formatting are observed string changes, even where the represented instant is equivalent. Environment/argument strings are opaque data; the installer should not reinterpret them.

Microsoft-date-shaped strings expose a second reader-specific coercion. The escaped input was constructed from exact bytes, not double-escaped through a JSON encoder:

```text
Raw escaped fixture: {"opaque":"\/Date(0)\/"}
Hex: 7b226f7061717565223a225c2f446174652830295c2f227d
```

That fixture has exactly one backslash before each slash. Before writing, PowerShell 5.1's reader returns `System.DateTime` for this escaped form and `System.String` for the unescaped `/Date(0)/` form. Its real writer happens to serialize the zero-date case back to the same decoded `/Date(0)/` string. That final-value equality is not evidence the reader kept the value opaque. PowerShell 7 returns `System.DateTime` for both forms and writes `1970-01-01T00:00:00Z`, changing the decoded value.

Evidence: `reader-results.json`, `microsoft-date-results.json`, and especially `microsoft-native-type-results.json`, which includes exact raw hex, native type before writing, raw output and argv. Candidate guidance only: preserve JSON string types in both reader branches and test native types as well as final values; the accidental PowerShell 5.1 zero-date round trip would otherwise mask coercion. No other Microsoft-date variants or impacts are asserted.

### AF-5: Duplicate permission entries cause false strict success with all managed entries absent (P2)

**Verifier**: deterministic. **Boundary**: Merge-StrictPermissions on both runtimes. The existing strings are accepted by the function's string-array validation, but duplicate count changes cancel the number of newly added values. The function returns the success-like up-to-date message without persisting the required overlay.

Concrete pre-existing input lists:

```python
deny = ["Edit(user-denied)"] * 23
ask = ["Write(user-ask)"] * 13
```

The shipped overlay has 22 distinct deny and 12 distinct ask strings, none equal to those user values. The real sequence and a separate strict-focused proof both reproduce the result on Windows PowerShell 5.1 and PowerShell 7.6.7: all 22 shipped deny and all 12 shipped ask entries remain absent, native exit is 0, and output says `[OK] Strict deny/ask entries already up to date (0 new)`.

Root cause: after Select-Object -Unique, deny has 23 members and ask has 13, exactly matching the original lengths that included duplicates. The code calculates `merged.Count - current.Count`, sums zero and returns before writing either merged list. It measures net length change, not whether required strings were missing. This is not a claim that every duplicate list causes a failure; the exact reproducer is recorded.

Evidence: duplicate-lists rows in both full sequence result files and the independent `strict-duplicate-results.json`. The latter runs actual core and the unchanged Python allow merger before two real strict calls. Both calls falsely report zero new entries. `extras.py` exits 1 on the recorded preservation/application assertions. Candidate guidance only: count missing overlay memberships or otherwise distinguish newly required entries from existing duplicate collapse. Any new correction to a permission writer requires its own concrete review and approval; this verifier changed none.

### AF-6: Case-distinct metadata inside a custom hook still prevents managed hook application (P2, bounded application gap)

**Verifier**: deterministic. **Boundary**: the hook-only PSCustomObject projection in the three repaired hook writers. The outer document can now retain exact-case keys, but serializing the entire hooks value and reparsing it through ConvertFrom-Json reintroduces the case-insensitive representation limit inside that subtree.

The concrete custom hook is:

```json
{"matcher":"Custom","hooks":[{"type":"command","command":"echo keep-user-hook","metadata":{"VAR":"one","var":"two"}}]}
```

On both runtimes, each native hook writer logs a parse warning and skips. The custom hook and metadata survive, but no git-guardrails registration is added. Core Sonnet, strict entries and MCP registration still succeed. This is an application failure with preserved user data; it is not observed data loss or a model-runtime exploit.

The nested metadata is valid JSON and is handled by the existing canonical Bash merger. Both its jq route and forced stdlib Python fallback were executed independently with this same input. Each returned 0, retained the original custom hook exactly, and added the managed guardrail. The initial fallback harness used a colliding local variable and returned 127; a corrected harness and a fresh fixture then passed. That initial error is a test-harness issue, not a product finding.

Evidence: hook-case-metadata rows in both full sequence result files; `canonical-merge-results.json` for jq; `canonical-python-fallback-result.json` for the successful Python fallback. This establishes installer merger parity and the metadata-preserving merge possibility. It does not independently certify that Claude's current public settings schema assigns runtime meaning to this custom metadata field, and no model session was launched.

## Canonical Merger Options

The closest existing implementation is `scripts/installer.sh`'s merge_managed_claude_hooks. Its jq path and stdlib Python fallback use the same event/matcher/type/script-stem association while retaining ordinary dictionaries and unknown metadata. The observed fallback proof demonstrates reuse is possible without an external package or paid service; it is not an instruction to duplicate a second algorithm.

`scripts/lib/integrations/_settings_hooks.py` also contains a dictionary settings-hook merger, but it is specific to Gemini CLI/Qwen event maps and named ownership/pruning semantics. Its merge_settings_hooks is not a drop-in Claude replacement. Reusing it unchanged could alter ownership or hook-selection behavior. The parent should prefer the current Claude canonical merge contract when preparing a correction. No new helper, installer copy step or source refactor was authored here.

## Considered but Rejected

| Candidate | Observed reason not reported |
|---|---|
| Date-shaped object keys are coerced | Separate key-only fixtures preserve every tested key on both runtimes. The observed coercion is of recognized values. |
| Every ISO-looking string changes | UTC without fractional formatting, date-only strings, prefixed text and the tested nine-fraction UTC string remained unchanged. The finding names only actual transformations. |
| Current core/MCP fails whenever keys resemble dictionary methods | Full sequences with Keys, Count, Values and GetEnumerator metadata, and an MCP server named Keys, pass all preservation/application checks on both runtimes. |
| Literal profile syntax is executed or misresolved | Both runtimes preserve the method-key fixture under a path containing brackets, dollar, backtick, semicolon, spaces and Unicode; core, hooks, strict and MCP all apply. Installed hook execution itself was not tested. |
| Nested metadata is deleted | Both full sequences retain the complete custom hook and its metadata. The observed failure is skipped managed registration. |
| Microsoft zero-date final equality proves reader opacity on 5.1 | Direct native type inspection contradicts that counter-hypothesis for the exact escaped fixture; it returns DateTime before serializing back to the same final value. |

## Proving Commands and Artifacts

Use the private Python interpreter `C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe`, running from this Temp report directory:

```powershell
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 run.py ps51
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 run.py ps7
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 date-offset-proof.py
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 extras.py
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 fallback-proof.py
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 microsoft-date-proof.py
& 'C:/Users/[redacted:user]/AppData/Local/Temp/nexus-v4140-full-py311/Scripts/python.exe' -X utf8 microsoft-native-type-proof.py
```

`run.py` is observational and exits 0 while explicitly recording failed boundaries. `date-offset-proof.py` and `extras.py` fail their desired preservation/application assertions after saving the actual native results. `fallback-proof.py` passes. Each driver creates unique fresh fixture directories and will refuse directory reuse; retain the evidence and use a fresh copy/root for another run. Exact fully resolved native command arrays appear in the JSON records. `source-hashes.json` records the actual source installer, Bash installer, settings template, hook converter and Python permission helper hashes.

No whole-suite or full-installer outcome follows from these probes. Parent-owned earlier focused test counts are not substituted for final qualification, and no outcome is inferred from the cancelled obsolete installer run. A source correction requires new evidence at its resulting hash.

## Overall Assessment

Three bounded findings are observed: date coercion, false strict up-to-date reporting on the concrete duplicate lists, and skipped hook application for the nested exact-case metadata fixture. The first two have independent failing preservation/application proofs; the third has actual native skip evidence and an executed canonical-merger control. No source fixes were made. Full qualification, all seven plan DoD items, required remote checks and publication remain outside this receipt.

**Verdict: FAIL at installer SHA-256 9be0ae34d1eb0632af691dab24c8f559c40c99bf5919b4e2950d01793b6fdc9b.**
