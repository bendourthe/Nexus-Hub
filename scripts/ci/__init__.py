"""Nexus-Hub's repository-native CI engine (v4.0.0).

Definitive validation logic lives here, in the repository, callable with no CI
provider present. `.github/workflows/` is a trigger and reporting layer that
calls into these profiles; it does not re-declare what they run.

The defect this exists to prevent is drift between two lists. Before v4.0.0 the
`validate` job in `ci.yml` re-declared the Makefile's validator sequence as 31
separate steps, and the two had already diverged in production: a duplicate YAML
key silently dropped `validate_no_personal_paths.py` from CI for a period while
the local list still ran it. One list, called from both places.

Modules:

- `profiles`  -- what each profile runs, as data.
- `change_scope` -- classify a diff into the groups a profile can skip.
- `reporting` -- turn a run into `reports/` artifacts.
- `run`       -- the CLI.

Repo-internal by design: nothing here is installer-copied. An end-user
`~/.nexus-hub/scripts/` has no catalog source, no test tree, and no workflows to
validate, so a copy would be inert.
"""

from __future__ import annotations

__all__ = ["PROFILE_NAMES"]

#: The canonical profile roster. Defined in
#: `docs/releases/v4/v4.0/development/ci-cd-lifecycle-contract.md` section 3 and owned by
#: the `cicd-architect` skill. Do not rename; do not add a sixth without
#: recording the decision.
PROFILE_NAMES = ("fast", "full", "platform", "report", "release")
