### Step 6: Handle Audience-Specific Formatting

Different audiences need different levels of detail:

**User-Facing Release Notes** (for product announcements, in-app changelogs):

```markdown
# What's New in v2.5.0

## New Features

- **Dashboard**: Added a real-time activity feed showing team member actions as they happen
- **Export**: PDF export now supports custom page layouts and company branding
- **Search**: Full-text search across all project documents with highlighted results

## Improvements

- File upload speed improved by 40% for documents over 10 MB
- Mobile navigation now remembers your last visited section
- Reduced initial page load time by 200ms through optimized asset loading

## Bug Fixes

- Fixed an issue where notifications were not delivered for shared documents
- Corrected timezone display for users in UTC-negative regions
- Resolved a crash that occurred when uploading files with special characters in the filename

## Important Notes

This release requires all users to re-authenticate once after upgrading.
The legacy CSV import format is deprecated and will be removed in v3.0.
```

**Developer Release Notes** (for API consumers, library users):

```markdown
# v2.5.0

## Breaking Changes

- `GET /api/v1/users` now returns paginated results by default (limit: 50). Pass `?limit=0` to retrieve all results. ([#342](https://github.com/org/app/pull/342))
- The `UserPreferences` type now uses `Record<string, unknown>` instead of `any` for the `settings` field. ([#358](https://github.com/org/app/pull/358))

## Features

- **api**: Added `POST /api/v1/documents/search` endpoint with full-text search support ([#345](https://github.com/org/app/pull/345))
- **sdk**: New `DocumentClient.search()` method wrapping the search endpoint ([#347](https://github.com/org/app/pull/347))
- **webhooks**: Added `document.searched` event type ([#350](https://github.com/org/app/pull/350))

## Bug Fixes

- **api**: Fixed race condition in concurrent document updates ([#355](https://github.com/org/app/pull/355))
- **sdk**: Corrected retry logic for 429 responses to respect `Retry-After` header ([#360](https://github.com/org/app/pull/360))

## Migration Guide

### Pagination Change

If your integration fetches all users in a single request, update your code:

Before:
    response = client.get("/api/v1/users")
    all_users = response.json()

After:
    all_users = []
    page = 1
    while True:
        response = client.get(f"/api/v1/users?page={page}&limit=100")
        data = response.json()
        all_users.extend(data["items"])
        if not data["has_next"]:
            break
        page += 1
```
