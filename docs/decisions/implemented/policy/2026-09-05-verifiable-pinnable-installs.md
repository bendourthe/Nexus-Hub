# Decision: Release installs verify the project's own published artifact and can be pinned or rolled back

Status: implemented - the release workflow attaches a deterministic tarball, a SHA256SUMS file, and a build-provenance attestation to every GitHub Release; both bootstrap installers download that tarball for a tagged ref, verify it fail-closed, and accept a `--ref` pin; `nexus-hub upgrade` refuses to move a pinned install unless told where

## Problem

Nexus-Hub installs by downloading a tarball into `~/.nexus-hub/src` and running the installer from it. Before v4.7.0 the bootstrap downloaded GitHub's generated branch archive (`archive/refs/heads/<ref>.tar.gz`) for every ref, so a tagged ref built a URL that does not exist; verification existed only as an env-var pin or a repo-tracked `checksums.txt` fetched from the tag, which cannot contain the tag's own archive hash and therefore held one historical entry; and a missing checksum for a tag produced a warning and an unverified install. The project published no artifact of its own, no checksum file, and no provenance. A user could not verify that what they downloaded was what the project published, could not install a specific version, and could not roll back.

## Decision

- **The release publishes its own artifact.** `release.yml` gains a `publish-artifact` job (permissions `contents: write`, `id-token: write`, `attestations: write`, scoped to that job) that builds `Nexus-Hub-<version>.tar.gz` with `git archive` under pinned LF line endings, writes a GNU-format `SHA256SUMS`, waits for the Release object `/update release` creates, uploads both with `--clobber` (idempotent, backfillable through `workflow_dispatch` with `ref`), and records a GitHub-native build-provenance attestation. No package registry and no new secret: attestation is reachable with the repository's own token.
- **Tagged installs verify fail-closed.** For a ref matching `vX.Y.Z`, both bootstraps download the published tarball and `SHA256SUMS` from the Release, compute the digest, and abort with a non-zero exit on a mismatch (naming both digests), on a missing or unfetchable `SHA256SUMS` (a network failure is reported as such, not as tampering), or on an unresolvable ref (naming the ref and where to list versions). They never fall back to an unverified install for a tag. A branch ref (the default `main`) has no publishable digest because every commit changes the archive; it keeps the pre-existing behavior (env-var pin, checksums file, or a stated warning) and is documented as the unverifiable path, with the pinned path as the verifiable one.
- **Pinning and rollback.** `install.sh --ref <tag>` / `install.ps1 -Ref <tag>` (and `NEXUS_HUB_REF`) install a specific version; the bootstrap records `~/.nexus-hub/PINNED_REF` for a tag and removes it for a branch. `nexus-hub upgrade` on a pinned install refuses to move (exit 3) and prints the three options; `--latest` re-pins to the newest release tag, `--ref <tag>` moves to any tag, which is also rollback. Unpinned installs behave as before.

## Alternatives considered

- **Publish to a package registry (npm) for versioned, checksummed installs.** Rejected: it creates a commercial relationship with a vendor that is not the intrinsic data destination, which the MCP Registry Policy requires justifying on three grounds, and the same properties are reachable with GitHub-native features the repository already holds.
- **Trust GitHub's generated tag archive and publish its hash.** Rejected: the bytes are GitHub's, not the project's; their stability is a vendor promise the project cannot test, and the repository-tracked `checksums.txt` approach could not hold a tag's own hash without a second commit after tagging.
- **Fail closed on branch installs too.** Rejected: no digest can be published for a moving branch, so failing closed would make the default one-line install impossible. The honest boundary is stated instead: branch installs are unverifiable by construction, tagged installs are the verifiable path.
- **`upgrade` silently moves a pinned install to tip.** Rejected: a user who asked to pin and was unpinned by an operation they expected to be scope-preserving loses the guarantee without noticing. A refusal with three explicit options costs one command.
- **A required status check for the supply-chain watch.** Rejected: a `schedule`-triggered workflow never fires on a pull request, and a required check from an untriggered workflow stays Pending forever (the v3.17.5 failure). The watch is advisory by construction and asserted absent from the required set.

## Consequences

- Tags published before v4.7.0 carry no artifact set, so `--ref v4.5.0` fails closed with the remediation (use a newer tag, or supply `NEXUS_HUB_TARBALL` plus `NEXUS_HUB_EXPECTED_SHA256`). Backfilling older tags is possible through `workflow_dispatch` and is the maintainer's call.
- The release flow now depends on the Release object existing within ten minutes of the tag push; `/update release` creates it seconds later, and the job's failure message names the backfill command.
- The default `main` install is unchanged and remains unverifiable; the README states this next to the pinned path.
- Every new opt-in surface (`--ref` / `-Ref`, `upgrade --latest` / `--ref`) carries the five capability elements in the release notes.
