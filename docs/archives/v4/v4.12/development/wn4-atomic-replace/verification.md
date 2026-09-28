# v4.12 WN-4 Windows settings replacement qualification

**Scope**: The installer-facing `scripts/merge_permissions.py` settings write on Windows. **Status**: published and qualified within the reproduced failure class.

## Historical boundary

The original Windows installer/validator command passed 2,069 tests and failed `test_sibling_keys_and_user_content_survive` with `WinError 5` while replacing its temporary settings file. Five isolated reruns passed. The process that held or denied the destination during that original run was not observed, and this qualification does not identify it or convert the failed run into a pass.

## Reproduced failure class and repair

On this Windows host, a test-owned reader held `settings.json` open for 0.3 seconds while the unmodified helper attempted `settings.json.tmp` replacement. The focused failing-first run had three failures: the held-handle test raised `WinError 5`, the permanent-denial test left the predictable temporary file behind, and the concurrent-edit test received `PermissionError` because the original helper had no retry or retry-specific change guard. This demonstrates a real failure class compatible with the historical error, not the historical process identity.

The candidate writes a uniquely named temporary file beside the destination, makes a bounded Windows-only retry after a replacement denial, and removes the temporary file whether replacement succeeds or fails. It compares the destination with the bytes read for the merge before each attempt; if a user edit has changed those bytes, it stops rather than knowingly replacing the edit. A persistent denial still surfaces as an error. The ordinary no-content-change path remains a no-op.

## Local verification

- `python -m pytest tests/validators/test_merge_permissions.py tests/installer/test_permission_scope_parity.py tests/installer/test_strict_permissions.py -q --tb=line`: 71 passed, two skipped on the final code, including the real Windows held-handle test and installer-facing CLI flow.
- `python -m pytest tests/installer -q --tb=line`: 479 passed, 43 skipped on the final helper code. The validator-test timing guard was tightened during this run and passed its own 31-test rerun afterward; it does not change installer behavior.
- `python scripts/ci/run.py --profile fast --quiet`: 17 of 17 checks passed on the final code.
- `python scripts/ci/run.py --profile full --only docs --quiet`: eight of eight checks passed on the final code.
- `python scripts/check_docs_retention.py --quiet` and `git diff --check`: both passed on the final code and documentation.

The byte comparison is a retry guard, not an interprocess lock: another writer could change the file between the final comparison and rename. This repair does not claim general transactional concurrency or explain every possible Windows access denial.

## First hosted attempt

PR #326's first hosted run 36215080561 passed the Windows test job but failed the Linux test job: `test_wn4_retry_refuses_a_concurrent_user_edit` expected a retry on Linux even though the new retry is Windows-only. The Linux partition reported 1 failed, 1,984 passed, and 49 skipped; its aggregate report failed with it. The test was then marked Windows-only, matching the behavior it asserts. This was a test-scope correction, not a reinterpretation of the failed hosted result. The corrected Windows validator suite passed 31 tests with one skip, and the fast profile passed 17 of 17 locally before the new hosted head ran.

## Publication gate

PR #326's corrected head `b3ae4c1c` passed 24 hosted checks with one intentional skip; GitHub reported `CLEAN` before merging. The PR merged to `develop` as `5fd7f985`, and [post-merge run 36217288553](https://github.com/bendourthe/Nexus-Hub/actions/runs/36217288553) passed both smoke and provenance on that SHA. The source ledger closes WN-4 only for the tested transient held-handle failure class and retains the original unexplained failure.
