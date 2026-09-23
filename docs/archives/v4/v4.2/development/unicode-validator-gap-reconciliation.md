# v4.2 Unicode Validator Gap Reconciliation

This record covers the post-release repair of v4.2.2 DF-1 and v4.2.3 DF-1. It is release-bound evidence, not a change to the original phase records.

## Implemented

- `scripts/validate_unicode_safety.py` includes active `.html` files in its text scan while retaining the existing `archive` and `archives` exclusions.
- English `.md` and `.html` documents report non-Latin alphabetic code points as hard errors. The validator does not guess replacements for those letters.
- HTML character references that decode to a hidden unsafe character or non-Latin letter are reported at their source position. The `--fix` mode leaves these references unchanged for human review.
- The lone Greek-letter unit label in the active performance-review template was changed to ASCII `us` so the active scan is clean. The common micro sign used as a unit symbol remains allowed.

## Verification on 2026-09-22

- `python -m pytest tests/validators/test_validate_unicode_safety.py -q`: 45 passed, 1 skipped. Cases include raw HTML, archive exemption, wrong-script Markdown and HTML, HTML character references, and the non-guessing `--fix` behavior.
- `python scripts/validate_unicode_safety.py --strict --verbose`: 2,842 active text files scanned, 0 warnings, 0 errors.
- `python scripts/ci/run.py --profile full --only docs --quiet`: 8 passed.
- `python scripts/ci/run.py --profile fast --quiet`: 17 passed.
- `python -m ruff check scripts/validate_unicode_safety.py tests/validators/test_validate_unicode_safety.py`: two pre-existing findings on unchanged lines (`SIM103` in the validator and `I001` in the test imports); no new lint finding was introduced.

Publication and hosted CI remain separate gates. The five-person workshop recorded as v4.2.2 and v4.2.3 DF-2 is not covered by this repair.
