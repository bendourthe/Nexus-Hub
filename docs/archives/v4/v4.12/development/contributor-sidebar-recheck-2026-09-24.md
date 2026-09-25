# Contributor sidebar recheck - 2026-09-24

This record rechecks v4.12 QG-2 for the repository owner before a GitHub Support handoff. It compares the public Code-page rendering with GitHub's contributor APIs after the approved attribution rewrite; it does not change history or claim that a GitHub display cache has been corrected.

## Current observation

At 2026-09-24 19:55 PDT, unauthenticated Playwright Chromium 151.0.7922.34 loaded the public [Nexus-Hub Code page](https://github.com/bendourthe/Nexus-Hub). The rendered Contributors heading still showed `5`. Its five image alt labels were `@bendourthe`, `@cursoragent`, `@benjamin-dourthe`, `@claude`, and `@dependabot[bot]`. This is the displayed result, not an inference from raw HTML: the initial response contains a loading skeleton in that region.

The same-session read-only GitHub API calls disagreed with the sidebar:

| Surface | Observed result |
|---|---|
| `GET /repos/bendourthe/Nexus-Hub/contributors` | `bendourthe`: 1,753 contributions; no other returned account |
| `GET /repos/bendourthe/Nexus-Hub/stats/contributors` | `bendourthe`: 1,394 non-merge commits; no other returned account |
| Default-branch metadata | `main` at `224cfb5ff4bee7ce17813f2c93514cff2d30da00`, committed 2026-09-21 16:05:51 UTC |

The Code-page one-contributor acceptance criterion is still **not met**. The API results neither overwrite nor explain the rendered result. No further history rewrite is supported by this evidence. The September 22 observation in [known gaps](../../../../releases/v4/v4.12/known-gaps.md) remains the prior checkpoint; this record is a fresh, separately dated recheck.

## Reproduction

Run `gh api repos/bendourthe/Nexus-Hub/contributors --jq '[.[] | {login, contributions}]'` and `gh api repos/bendourthe/Nexus-Hub/stats/contributors --jq '[.[] | {login: .author.login, total}]'`. Then load `https://github.com/bendourthe/Nexus-Hub` without signing in, wait for the Contributors heading to finish loading, and read the displayed count and avatar alt labels. Raw HTML alone does not prove the rendered count because GitHub initially serves a skeleton there.

## Support handoff draft

Subject: Nexus-Hub public Code sidebar retains five contributors after attribution rewrite

The public Code page for `bendourthe/Nexus-Hub` still renders `Contributors 5` and lists `bendourthe`, `cursoragent`, `benjamin-dourthe`, `claude`, and `dependabot[bot]`. The repository contributors API returns only `bendourthe` with 1,753 contributions, and the statistics API returns only `bendourthe` with 1,394 non-merge commits. The default branch is `main` at `224cfb5ff4bee7ce17813f2c93514cff2d30da00`. The attribution rewrite was published on 2026-09-14, so the discrepancy persists well beyond the documented refresh window. Please explain which GitHub-held data feeds the Code sidebar and provide a supported cache refresh or correction if it is stale. We do not want to rewrite history again or remove pull-request refs without GitHub guidance.

No Support case was submitted by this record. QG-2 closes only after a fresh public render shows the intended result, or GitHub gives an explicit supported disposition that the owner accepts.
