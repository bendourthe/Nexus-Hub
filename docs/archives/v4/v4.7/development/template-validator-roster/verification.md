# v4.7 DF-3 Template Validator Roster Qualification

This frozen record covers the local v4.7 DF-3 follow-up on the template-validator roster and section-body extraction. It is for release maintainers checking whether four named rule modules still detect missing, divergent, or duplicated instruction blocks. Hosted CI and post-merge behavior are separate gates.

## Change and preservation boundary

The existing `scripts/check_base_template_parity.py` owns the five lockstep filenames and now exposes the dynamic substantive/shim roster and non-empty section-body extraction used by the four rule modules. The four modules retain their own named tests and rule-specific assertions. The production parity CLI still checks only its original five files; its required headings, invariant sections, findings, JSON shape, and exit contract did not change. Construction Discipline now covers `base-pi.md`, which the older hardcoded twelve-file roster omitted.

| Check | Before | After | Verdict |
|---|---|---|---|
| Affected tests | 148 passed | 152 passed, including three helper tests and the added `base-pi.md` case | PASS |
| Parity CLI on the real tree | Five present, zero findings, exit 0 | Five present, zero findings, exit 0 | PASS |
| Public guard interface | `LOCKSTEP_FILES`, `REQUIRED_HEADINGS`, `INVARIANT_SECTIONS`, CLI JSON and exit codes | Unchanged; two read-only helpers added | PASS |
| Side effects | Template reads only | Template reads only; no writes, network calls, or logs added | PASS |
| Line and branch coverage comparison | Not measured | Not measured | NOT VERIFIED |

The shared section helper preserves the old rule-test normalization: CRLF is normalized, blank lines are dropped, trailing whitespace is stripped, and the body stops at the next level-two heading. A fixture proves nested level-three content remains in the body. A second fixture proves newly added substantive templates and include-only shims enter the correct roster. Existing negative fixtures still test missing headings, divergent blocks, and missing autonomy precedence.

## Local verification

- Before the change, `python -m pytest -q tests/validators/test_check_base_template_parity.py tests/validators/test_construction_discipline_rule.py tests/validators/test_writing_discipline_rule.py tests/validators/test_autonomy_block_rule.py tests/validators/test_communication_contract_rule.py` reported `148 passed`.
- After the change, the same command reported `152 passed`.
- `python -m ruff check` on the six changed Python files reported `All checks passed!`.
- `python scripts/check_base_template_parity.py --json` reported `in_parity: true`, five present files, no missing files, and no findings.
- `git diff --check` exited 0. Git printed only the checkout's LF-to-CRLF advisory.
- `python scripts/ci/run.py --profile fast --base origin/develop --quiet` first reported 16 passed and one host interpreter failure because PATH selected `C:\windows\system32\bash.exe`, which could not run a probe script. With `C:\Program Files\Git\bin` prepended for the rerun process, `python scripts/check_interpreter_resolution.py` selected Git Bash and the fast profile reported `17 passed, 0 failed, 0 skipped, 0 advisory`.

An optional run of the whole `tests/validators` directory was interrupted after several minutes in slow Git-fixture cases around 16 percent. It produced no terminal test summary, so it is not counted as a pass. The fast runner saw an empty committed diff and conservatively ran all 17 commands; it did not narrow to changed paths. Hosted checks and the merged result still need their own results before publication can be called verified.

## Verdict

APPROVE WITH CONDITIONS for local behavior preservation: the affected tests and CLI contract pass, and the sole intended coverage expansion is `base-pi.md`. This record does not claim whole-validator-suite coverage, hosted CI, or a merged result.
