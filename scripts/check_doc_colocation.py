#!/usr/bin/env python3
"""Enforce the comparison / adoption-plan co-location invariant.

A `/compare` report and the `/plan from-comparison` plan it seeds must live in
the SAME version directory (`docs/v<MAJOR>/v<MAJOR>.<MINOR>/`). This was an
inline bash block in `.github/workflows/doc-colocation.yml` until v3.17.7; it
moved here because three fail-open defects needed fixing at once and an inline
`run:` block cannot be unit-tested.

The three defects, all of which reported a clean gate while checking nothing:

1. **Only the highest major was scanned.** `CURRENT_MAJOR` was computed with
   `sort -n | tail -1`, so the moment a `docs/v4/` tree appeared, every plan
   under `docs/v3/` stopped being checked. The reorganization that retargeted
   four plans to v4.0.0/v4.1.0 would have created exactly that tree. Every
   major is now scanned.

2. **A dangling `Seeded from` passed.** The old check extracted a version
   directory from the path *string* and compared it, never opening the file. A
   plan could cite a comparison that did not exist and still pass. Two did:
   `v3.18.0-comparison-jcodemunch.md` and `v3.18.1-comparison-optmem.md`, both
   naming pre-rename slugs. A dangling seed is now a MISMATCH.

3. **Relative `Seeded from` paths were skipped entirely.** The extraction regex
   matched only `docs/v...`, so a `../comparisons/x.md` reference yielded an
   empty match and the plan was silently skipped. That is how the two dangling
   references above survived. Relative paths are now resolved against the
   plan's own directory and checked like any other.

4. **The scan root was the pre-refactor layout.** `majors()` looked for
   `docs/v<N>/` directly under `docs/`, but the docs layout refactor moved the
   active tree to `docs/releases/v<N>/`. From that commit until v4.8.0 this
   gate printed "No docs/v<N> tree found; nothing to check." and exited 0 on
   every run - the fourth fail-open defect of the same character as the three
   above, and found while repairing the identical bug in
   `check_docs_retention.py`. Both the canonical `docs/releases/v<N>/` and the
   legacy `docs/v<N>/` layout are now scanned, and an empty scan is reported as
   a WARNING rather than as a clean gate.

Grandfathering that is deliberately KEPT: `docs/archives/**` and the legacy
singular `docs/archive/**` are out of scope (neither is under a version root a
`majors()` scan reaches), a plan with no `Seeded from` field is not a
from-comparison plan and is skipped, and a comparison with no `Adoption target`
field is a legacy report reported as a non-fatal note.

Repo-internal guard: no installer copy step and no `.ps1` sibling, same as
`check_version_sync.py` and `check_required_check_coverage.py`. Listed in
`DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py`.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# `docs/releases/v3/v3.17/plans/x.md` -> `docs/releases/v3/v3.17`, and the
# legacy `docs/v3/v3.17/plans/x.md` -> `docs/v3/v3.17`. The `releases/` segment
# is optional so both layouts resolve; see defect 4 in the module docstring.
VERSION_DIR_RE = re.compile(r"^(docs/(?:releases/)?v\d+/v\d+\.\d+)/")
# A `**Seeded from**:` line's path token, relative or repo-rooted, optionally
# wrapped in a Markdown link or backticks.
SEEDED_LINE_RE = re.compile(r"^\s*\*\*Seeded from\*\*:")
SEEDED_PATH_RE = re.compile(r"((?:\.\./)*[A-Za-z0-9_./-]*comparisons/[^`()\[\]\s]+\.md)")
ADOPTION_TARGET_RE = re.compile(r"Adoption target", re.IGNORECASE)
SEMVER_RE = re.compile(r"v(\d+)\.(\d+)\.(\d+)")


class Mismatch(str):
    """A single co-location violation, rendered as its own message."""


def version_dir(rel_path: str) -> str | None:
    """Return the `docs/v<M>/v<M>.<N>` prefix of a repo-relative path."""
    m = VERSION_DIR_RE.match(rel_path.replace("\\", "/"))
    return m.group(1) if m else None


def resolve_seed(plan_rel: str, token: str) -> str:
    """Resolve a `Seeded from` token to a repo-relative POSIX path.

    A repo-rooted token (`docs/...`) is returned as-is. Anything else is
    resolved against the plan's own directory, which is what makes a
    `../comparisons/x.md` reference checkable at all (defect 3).
    """
    token = token.replace("\\", "/")
    if token.startswith("docs/"):
        return token
    parent = Path(plan_rel).parent
    # PurePosixPath has no normalization, so walk the parts manually rather
    # than touching the filesystem (keeps this pure and testable).
    parts: list[str] = [p for p in parent.as_posix().split("/") if p not in ("", ".")]
    for part in token.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


# Version-tree containers, canonical first. `docs/releases/` is the layout the
# docs refactor established; bare `docs/` is the pre-refactor layout, still
# honored in place exactly as `docs-layout-refactor` specifies. Scanning both
# means this gate survives the next rename instead of going quiet (defect 4).
TREE_PREFIXES = ("docs/releases", "docs")


def version_roots(root: Path) -> list[tuple[str, str]]:
    """Every version tree as (prefix, major), ascending, canonical layout first.

    Returns e.g. `[("docs/releases", "3"), ("docs/releases", "4")]`. All majors
    are scanned, not just the highest (defect 1), and both layouts are reached
    (defect 4). A prefix contributing no major is simply absent from the result,
    which is what lets `main` distinguish "scanned nothing" from "found nothing
    wrong".
    """
    out: list[tuple[str, str]] = []
    for prefix in TREE_PREFIXES:
        base = root / prefix
        if not base.is_dir():
            continue
        found: set[int] = set()
        for child in base.iterdir():
            m = re.fullmatch(r"v(\d+)", child.name)
            if m and child.is_dir():
                found.add(int(m.group(1)))
        out.extend((prefix, str(n)) for n in sorted(found))
    return out


def check_plans(root: Path, prefix: str, major: str) -> tuple[list[Mismatch], list[str]]:
    """Direction 1: a plan must be co-located with the comparison it cites."""
    problems: list[Mismatch] = []
    notes: list[str] = []
    for plan in sorted((root / prefix / f"v{major}").rglob("*.md")):
        rel = plan.relative_to(root).as_posix()
        if "/plans/" not in rel:
            continue
        text = plan.read_text(encoding="utf-8", errors="replace")
        line = next(
            (ln for ln in text.splitlines() if SEEDED_LINE_RE.search(ln)), None
        )
        if line is None:
            continue  # not a from-comparison plan
        token = SEEDED_PATH_RE.search(line)
        if token is None:
            # A plan may legitimately be seeded from something that is not a
            # /compare report: a research document, a maintainer bug report, or
            # a release session. Those have no co-location duty. Only a cited
            # COMPARISON is checked, which is what the invariant is about.
            notes.append(f"NOTE: seed is not a comparison, skipping: {rel}")
            continue
        seed = resolve_seed(rel, token.group(1))
        if not (root / seed).is_file():
            problems.append(
                Mismatch(
                    f"MISMATCH (dangling seed): {rel} is seeded from {seed}, "
                    f"which does not exist"
                )
            )
            continue
        pdir, cdir = version_dir(rel), version_dir(seed)
        if pdir is None or cdir is None:
            notes.append(f"NOTE: skipping non-versioned path pair: {rel} -> {seed}")
            continue
        if pdir != cdir:
            problems.append(
                Mismatch(
                    f"MISMATCH (plan/comparison): {rel} (in {pdir}) is seeded "
                    f"from {seed} (in {cdir}); expected the comparison under "
                    f"{pdir}/comparisons/"
                )
            )
    return problems, notes


def check_comparisons(
    root: Path, prefix: str, major: str
) -> tuple[list[Mismatch], list[str]]:
    """Direction 2: a comparison must sit in its declared target's directory."""
    problems: list[Mismatch] = []
    notes: list[str] = []
    for cmp_path in sorted((root / prefix / f"v{major}").rglob("*.md")):
        rel = cmp_path.relative_to(root).as_posix()
        if "/comparisons/" not in rel:
            continue
        text = cmp_path.read_text(encoding="utf-8", errors="replace")
        line = next(
            (ln for ln in text.splitlines() if ADOPTION_TARGET_RE.search(ln)), None
        )
        if line is None:
            notes.append(f"NOTE: legacy comparison with no Adoption target: {rel}")
            continue
        sem = SEMVER_RE.search(line)
        if sem is None:
            notes.append(f"NOTE: Adoption target present but unparseable: {rel}")
            continue
        expected = f"{prefix}/v{sem.group(1)}/v{sem.group(1)}.{sem.group(2)}"
        cdir = version_dir(rel)
        if cdir != expected:
            problems.append(
                Mismatch(
                    f"MISMATCH (comparison placement): {rel} (in {cdir}) declares "
                    f"Adoption target v{sem.group(1)}.{sem.group(2)}.{sem.group(3)}; "
                    f"expected under {expected}/comparisons/"
                )
            )
    return problems, notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--root",
        default=".",
        help="Repository root to scan (default: current directory)",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Also print non-fatal notes (legacy reports, skipped paths)",
    )
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    found = version_roots(root)
    if not found:
        # A WARNING, not a clean gate. Printing a reassuring line here while
        # checking nothing is defect 4, and it hid this gate for a whole major
        # version. Still exit 0: a project with no version tree is a legitimate
        # state, but it must never read as "checked and clean".
        print(
            "WARNING: no version tree found under any of "
            f"{', '.join(p + '/v<N>' for p in TREE_PREFIXES)}; "
            "co-location gate checked NOTHING. If the docs layout moved, add the "
            "new container to TREE_PREFIXES in scripts/check_doc_colocation.py."
        )
        return 0

    trees = ", ".join(f"{prefix}/v{m}" for prefix, m in found)
    print(
        f"Enforcing co-location under every major: {trees} "
        "(docs/archives/** and docs/archive/** grandfathered)"
    )

    problems: list[Mismatch] = []
    notes: list[str] = []
    for prefix, major in found:
        p1, n1 = check_plans(root, prefix, major)
        p2, n2 = check_comparisons(root, prefix, major)
        problems += p1 + p2
        notes += n1 + n2

    if args.verbose:
        for note in notes:
            print(note)

    for problem in problems:
        print(problem)

    if problems:
        print(
            f"FAIL: {len(problems)} comparison / adoption-plan co-location "
            "mismatch(es) found - reconcile via docs-layout-refactor"
        )
        return 1

    print(f"OK: no comparison / adoption-plan co-location mismatches under {trees}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
