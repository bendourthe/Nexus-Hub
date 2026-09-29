# Decision: Resolve the hosting repository from a verified host, or not at all

Status: implemented - `scripts/repo_host.py` resolves the GitHub `owner/repo` for `check_plan_completion.py` and is installed beside it in `~/.nexus-hub/scripts/`.

## Problem

The completion checker pins every `gh` hosting call with `--repo owner/repo` and binds a signed push approval to the repository the push URL names. It parsed `owner/repo` with a regex that accepted only a host spelled `github.com`. A developer with several GitHub accounts usually uses an SSH host alias (`git@github-work:owner/repo.git`), which left the repository empty and made every hosting predicate `cannot-verify`, so a full `/implement` run could never finish in such a repository. Widening the regex to accept any host would do worse: it would look up a same-named github.com repository for a GitLab or local remote, and report a merge or a release that never happened on the server the push actually reached.

## Decision

One shared module resolves the repository and refuses to guess. A path is accepted only when the host git contacts equals the host `gh --repo owner/repo` will query: `GH_HOST` when it is set, otherwise `github.com`. An `https://` host is taken literally. An `ssh://` or scp-like host that is not itself accepted is treated as an SSH alias and replaced by the `hostname` that `ssh -G <alias>` reports, and an alias routed through `ProxyCommand` or `ProxyJump` is not accepted. Remotes containing `#`, `?`, or a backslash, and single-letter scp hosts (a Windows drive-relative path to git), are rejected. Without a frozen record repository, the answer is cross-checked with `gh repo view`, and a disagreement yields no repository, because `gh repo set-default` lives in `.git/config`, which an agent can write. Any unverified case yields no repository, which every caller reports as `cannot-verify`.

## Alternatives considered

**Accept any host.** Makes the alias case work and turns every non-GitHub remote into a lookup of whatever same-named repository github.com has. A false `met` on `release.github` is worse than a `cannot-verify`. Rejected.

**Trust `gh repo view` alone.** `gh` resolves aliases itself, but its answer follows `gh repo set-default`, which is stored in the repository's own `.git/config` and is writable by the agent the checker is meant to hold to account. Kept only as a cross-check that can veto, never as the source. Rejected as the primary source.

**Ask the user to configure the repository once.** Reliable, but it adds a setup step to every repository and does nothing for a run that has already started. The run record already freezes the approved repository; the resolver only fills the gap before a record exists. Rejected.

**Accept both `github.com` and `GH_HOST`.** This was the first implementation. The final-phase adversarial review showed that with `GH_HOST` set, a github.com remote would have been checked against a same-named repository on the enterprise host. Replaced by the single host `gh` queries.

## Consequences

This repository's full runs can reach `PLAN COMPLETE`. A user whose SSH config routes GitHub through a proxy, or who sets `GH_HOST` while pushing to github.com, gets `cannot-verify` rather than a result about a different server. Git transport overrides (`core.sshCommand`, `GIT_SSH_COMMAND`, `http.curloptResolve`, proxies) and a push remote other than origin are not yet inspected; they are recorded as v4.13.5 WN-2 and WN-3 and owned by v4.13.6.
