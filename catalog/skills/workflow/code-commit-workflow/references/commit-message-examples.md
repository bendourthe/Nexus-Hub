# Commit Message Examples

Worked good and bad commit messages for every commit type. Kept out of the skill body because examples are looked up when writing a specific message, not needed on every trigger; the RULES they illustrate live in `SKILL.md`.

### Good Examples

```
feat(user): add profile photo upload

Allow users to upload profile photos. Supports JPEG, PNG, and GIF formats up to 5MB. Photos are automatically resized to 200x200px.

Implements user story US-789
```

```
fix(cart): prevent duplicate items when adding quickly

Race condition caused duplicate items when users clicked "Add to Cart" rapidly. Added debounce and server-side idempotency check.

Fixes #234
```

```
refactor(payment): extract card validation to separate module

Move credit card validation logic from PaymentService to CardValidator class. This improves testability and allows reuse in other contexts.

No functional changes.
```

```
test(auth): add integration tests for OAuth flow

Add comprehensive tests covering:
- Successful OAuth login
- Token refresh
- Permission denied scenarios
- Rate limiting behavior

Coverage increased from 72% to 89%
```

For multi-component commits, use the sectioned-bullet structure (labeled headers, contiguous bullets, no flowing-paragraph body):

```
feat(v0.3.0): phase 6 docxtpl report engine and Analyze page

Lands the Phase 6 deliverables: a docxtpl-driven report engine, a desktop Analyze page that picks ingest runs and generates Supira-branded docx files, and a Settings tab for swapping in a custom template.

Reporting package (`src/reporting/`):
- `snapshot.py`: immutable Pydantic snapshot of confirmed extractions, plus a `build_snapshot` walker over `ingest_runs` / `source_artifacts` / `ingest_units` / `extractions`.
- `renderer.py`: `ReportRenderer.render(snapshot, template_path)` runs `docxtpl.DocxTemplate.render` against a full context dict, then appends deterministic per-run / per-artifact / per-unit sections via python-docx so reports stay populated even when the template carries no Jinja placeholders.

Packaging and paths:
- Bundles `assets/report_template_default.docx` (verbatim copy of the branding template).
- Adds `default_report_template_path` / `user_report_template_path` / `report_template_path` / `reports_dir` / `run_report_dir` helpers in `installer/gui/utils/paths.py`.
- PyInstaller spec collects `docxtpl` and `docx` and ships the bundled template under `<bundle>/assets/`.

Desktop UI:
- Replaces the `AnalyzePage` stub with the run-picker plus Generate report flow.
- Adds `ReportTab` in `installer/gui/settings_qt.py` that browses for a `.docx`, copies it on Save, and offers Reset to bundled default.

Tests:
- 51 new tests across `tests/reporting/` and `tests/installer/`.
- Total suite: 495 passed, 4 skipped, coverage 86.99%.

Known gaps (tracked as DF in `docs/v0.3.0/known-gaps.md`):
- Bundled template ships without `{{ jinja }}` placeholders; renderer falls back to python-docx append pass.
- `AnalyzePage` not yet wired into `MainWindow`'s engine and run providers (deferred to Phase 8).
```

### Bad Examples

```
# Too vague
fix bug

# Not imperative
fixed the login issue

# Too long subject
add new feature to allow users to upload their profile photos in multiple formats

# Missing type
update user model

# Doesn't explain why
refactor code

# Hard-wrapped paragraph (every body paragraph and bullet must be a single source line)
feat(api): add rate limiting middleware

Introduce a token-bucket rate limiter that runs ahead of the auth
middleware so unauthenticated traffic is throttled before any
database lookup. Defaults are 60 req/min per IP and 600 req/min per
authenticated user.

- Added the rate-limit middleware and registered it before the auth
  middleware so anonymous traffic is throttled cheaply.
- Exposed `X-RateLimit-Remaining` and `Retry-After` headers on every
  response so clients can self-throttle.

# Multi-paragraph flowing-prose body for a multi-component commit (use sectioned bullets instead)
feat(v0.3.0): phase 6 docxtpl report engine and analyze page

Lands the Phase 6 deliverables: a docxtpl-driven report engine, a desktop Analyze page that picks ingest runs and generates Supira-branded docx files, and a Settings tab for swapping in a custom template.

Adds the `src/reporting/` package with `snapshot.py` and `renderer.py`. Output paths follow `%LOCALAPPDATA%\...\reports\<report_id>\YYYYMMDD-HHMMSS.docx`.

Bundles `assets/report_template_default.docx` and adds path helpers in `installer/gui/utils/paths.py`. The PyInstaller spec collects `docxtpl` + `docx`.

Replaces the `AnalyzePage` stub with the run-picker plus Generate report flow and the new `ReportTab` in `installer/gui/settings_qt.py`.

Test suite expansion: 51 new tests across `tests/reporting/` and `tests/installer/`. Total suite: 495 passed, 4 skipped, coverage 86.99%.

Three deviations tracked as DF in `docs/v0.3.0/known-gaps.md`.
```
