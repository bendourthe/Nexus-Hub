# Maintainer Git hooks

Repository-local attribution prevention for Nexus-Hub maintainers. These hooks are outside `catalog/hooks/` and are never copied by the installers. They check metadata, not authenticated authorship.

## Enable locally

Run from the repository root after reviewing the hook:

```bash
git config user.name "Ben Dourthe"
git config user.email "50595044+bendourthe@users.noreply.github.com"
git config core.hooksPath .githooks
```

These are repository-local settings. Enabling `core.hooksPath` replaces any previously configured hook directory; inspect `git config --get core.hooksPath` first and retain that value if restoring another hook setup may be necessary. Installation of this repository does not activate the hook automatically.

## Behavior

`commit-msg` invokes `scripts/check_commit_attribution.py --pending-commit --message-file` through Python. It rejects forbidden author and committer identities, including identities inherited by an amend, and forbidden or malformed `Co-authored-by` / `Made-with` fields. Git's canonical maintainer identity and GitHub's own committer are allowed by the checker policy. Missing Git or Python and incomplete scans fail the commit rather than silently allowing it.

Requires Git, Bash and Python 3.10 or newer on PATH. Git for Windows supplies Bash. A clean message alone does not prove a clean pending author; the hook deliberately runs both modes. A user can bypass local hooks, so the existing CI validate job independently scans all reachable history with a full checkout.

## Verify and restore

Run `python scripts/check_commit_attribution.py --all-refs --root .` in a full-history clone; expected exit is 0 with zero findings. A shallow clone returns exit 2 and must fetch complete history first. The attribution fixture suite creates isolated repositories and exercises real Git commits without installing hooks globally.

To stop using this hook, restore the previously recorded local `core.hooksPath` value, or run `git config --local --unset core.hooksPath` if no local value existed. This does not disable CI enforcement or change a global setting.
