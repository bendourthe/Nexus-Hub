# CI Latency Rules

Read this before proposing any change whose purpose is a shorter CI wall clock. It backs Step 1a of `SKILL.md` and covers GitHub Actions only, because the bundled audit script reads the GitHub Actions API through the user's own `gh`.

## Measure first

Run `scripts/ci_latency_audit.py` over recent successful runs of the workflow and read three things: the critical-path job (the non-aggregate job that finishes last), the split of each job into queue, setup and work, and the time to the aggregate gate. A re-run attempt is excluded because its jobs mix attempts, and a skipped job is listed, never counted as zero time. Local timings and the audit are estimates of the runner, not proof of it.

## Rules

- **Shorten the critical-path job first.** Time saved on any other job does not move the gate.
- **Split a serial suite across runners, not across workers on one runner, when workers contend.** Concurrent browser or process-heavy workers on one runner starve each other; a runner per shard does not.
- **Choose shard boundaries from measured per-file durations.** Name the heavy files in one constant and send everything else to a catch-all shard, so a new test file lands somewhere by default.
- **Prove every split with a node-ID partition proof.** Collect the real test IDs once unsharded and once per shard, then assert the shard sets are disjoint and their union equals the whole. A shard list kept by hand can drop a file while every job reports green.
- **Keep the aggregate required check and add no leg context.** A matrix leg that a job-level `if:` skips never publishes its own context, so a required leg context can sit Pending forever. See `required-status-checks.md`.
- **Never delete or skip tests to buy speed** without per-test evidence that the test protects nothing.
- **Seed caches from the base branch only after merge.** A pull request cannot write a cache that other pull requests restore; a push to the protected integration branch can.

## Reading the audit

| Observation | Usual cause | First move |
|---|---|---|
| One job near the gate time | Serial suite | Shard it, then re-measure |
| Large queue, small work | Runner pool pressure | Reduce job count, not test time |
| Large setup share | Cold caches or heavy install | Seed caches, restore on pull requests |
| Gate far above the slowest job | A re-run or a chained `needs:` | Check job dependencies |
