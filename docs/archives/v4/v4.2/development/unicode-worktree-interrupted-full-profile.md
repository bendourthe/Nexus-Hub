# Interrupted v4.2 follow-up full-profile run

The original report bundle is [`unicode-worktree-interrupted-full-profile.zip`](unicode-worktree-interrupted-full-profile.zip), SHA-256 `e917c70b45784a6e90f46c20a7e4e49f44ba4c2191a0599926ef7195fb86f742`. It contains the 15 generated `reports/` files, including `summary.json`, `summary.md`, and per-group JUnit. The report started at 2026-09-23 04:47:12 UTC and finished at 05:32:47 UTC with 45 passed and 16 failed commands.

This is not a product regression verdict. The v4.2 follow-up worktree was removed while the full profile was still running. Subsequent commands failed because test directories such as `tests/ci` no longer existed; extension groups were recorded as missing. The output must remain failed evidence, not be counted as a completed full-profile pass. PR #242's hosted and post-merge results and its focused local tests are separate evidence for the published Unicode repair.
