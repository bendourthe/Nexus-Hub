# v4.7 Supply-Chain Watch and Release Artifact Verification

This frozen record verifies the hosted observations originally missing from v4.7 MT-1. It separates the passing manual watch on `develop` from the still-failing scheduled watch on `main`; it does not certify the default-branch schedule.

## Hosted watch

- On 2026-09-24, [manual run 36034068237](https://github.com/bendourthe/Nexus-Hub/actions/runs/36034068237) completed successfully on `develop` at `d34eda9d`. Its `audit` job installed all six extension packages with optional extras, completed `pip-audit`, and uploaded `pip-audit-report` with expiry 2026-10-24. The report listed 143 installed dependencies, no vulnerable packages, and `setuptools` 84.0.0.
- The watch has only `schedule` and `workflow_dispatch` triggers. Its `audit` job is absent from the required-check manifest; `tests/workflows/test_supply_chain_watch.py` guards that separation. This manual run did not create a required pull-request context.
- The [scheduled `main` runs 34119799603, 34842748631, and 35599558573](https://github.com/bendourthe/Nexus-Hub/actions/workflows/supply-chain-watch.yml) failed. The latest retained `pip-audit-report` found `setuptools` 79.0.1 with two entries for the same `PYSEC-2026-3447` advisory. The [upstream advisory](https://github.com/advisories/GHSA-h35f-9h28-mq5c) identifies versions below 83.0.0 as affected and 83.0.0 as patched. Current `main` has no `scripts/ci/requirements-py311.txt` constraint, while current `develop` pins 84.0.0; the next release or a protected release-branch repair must prove the scheduled default-branch run green without suppressing the advisory.

## Published v4.7.0 artifact

- [Release run 34020950499](https://github.com/bendourthe/Nexus-Hub/actions/runs/34020950499) completed `release-readiness` and `publish-artifact` on 2026-09-06. Its log records a repository [attestation 45543670](https://github.com/bendourthe/Nexus-Hub/attestations/45543670) for `Nexus-Hub-4.7.0.tar.gz`; GitHub attestations are not a third Release asset.
- On 2026-09-24, both [v4.7.0 Release](https://github.com/bendourthe/Nexus-Hub/releases/tag/v4.7.0) assets were downloaded. The tarball SHA-256 was `a396482129ecb7db7f8ddc48126392b17b4c904f3939857fbda444aaf78b4847`, matching its published `SHA256SUMS` entry. `gh attestation verify <downloaded tarball> -R bendourthe/Nexus-Hub --format json` exited zero and verified the release-workflow identity and subject digest.

MT-1's missing hosted observations and release round trip are resolved. Scheduled `main` audit health remains open separately; a manual `develop` pass is not evidence that the schedule has recovered.
