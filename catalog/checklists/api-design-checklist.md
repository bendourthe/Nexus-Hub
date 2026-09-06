# API Design Checklist Reference

Quick-reference checklist for REST, GraphQL, and gRPC API design. Use when designing new endpoints, reviewing API changes, or evaluating whether an API is ready for external consumers.

---

## REST API Design Checklist

### Resource Naming

- [ ] Resources are nouns, not verbs: `/orders` not `/getOrders`
- [ ] Collection resources are plural: `/users`, `/products`
- [ ] Nested resources reflect ownership: `/users/{id}/orders` not `/user-orders?userId={id}`
- [ ] IDs are opaque (UUIDs preferred over sequential integers for external APIs)
- [ ] No implementation details in paths: no `/v1/db/user_table`

### HTTP Methods and Status Codes

- [ ] `GET` is idempotent and has no side effects
- [ ] `POST` creates or triggers actions; returns `201 Created` with `Location` header
- [ ] `PUT` replaces the full resource; `PATCH` modifies partially
- [ ] `DELETE` returns `204 No Content` on success (not `200` with a body)
- [ ] `400 Bad Request` for client errors (validation failures); `422` for semantic failures
- [ ] `401 Unauthorized` means not authenticated; `403 Forbidden` means not authorized
- [ ] `404 Not Found` does not reveal whether the resource exists but is forbidden
- [ ] `409 Conflict` for state conflicts (duplicate creation, optimistic lock failure)
- [ ] `429 Too Many Requests` with `Retry-After` header for rate limiting

### Request/Response Shape

- [ ] Consistent envelope: all responses use the same top-level structure (`data`, `error`, `meta`)
- [ ] Error responses include: `code` (machine-readable), `message` (human-readable), optional `details`
- [ ] Never expose stack traces, file paths, or database error messages in responses
- [ ] Dates in ISO 8601 format (`2026-04-06T21:46:31Z`), not Unix timestamps or locale-specific strings
- [ ] Booleans as `true`/`false`, not `1`/`0` or `"yes"`/`"no"`
- [ ] Empty collections return `[]`, not `null`

### Pagination

- [ ] Cursor-based pagination for large, frequently-updated collections
- [ ] Offset/page pagination only for small, stable collections
- [ ] Pagination metadata in response: `total`, `page`, `per_page`, `next_cursor` / `next_url`
- [ ] Maximum page size enforced (default: 20, max: 100)
- [ ] Consistent sort order guaranteed (stable sort key, usually `created_at DESC, id DESC`)

### Versioning

- [ ] Version in URL path (`/v1/`) for REST (not in headers -- harder to test/share)
- [ ] Breaking changes require a new version; additive changes are backwards-compatible
- [ ] Old versions have a documented sunset date with at least 6 months notice
- [ ] `Deprecation: true` response header on deprecated endpoints

---

## GraphQL API Checklist

- [ ] Queries follow the principle of least data -- clients request only what they need
- [ ] N+1 resolved with DataLoader for any field that fetches related entities
- [ ] Input validation on mutations: explicit error type for each invalid field
- [ ] Subscriptions scoped to authenticated user's data -- no cross-user event leakage
- [ ] Schema documentation: every field has a description; required fields are non-null
- [ ] Query depth and complexity limits enforced to prevent DoS
- [ ] Persisted queries used in production to prevent schema enumeration

---

## API Security Checklist

- [ ] Authentication required before any data is returned (fail closed, not open)
- [ ] Rate limiting per user/IP -- not just per endpoint
- [ ] Input size limits on all request bodies (prevent payload-based DoS)
- [ ] CORS restricted to known origins -- `*` is never acceptable for authenticated APIs
- [ ] Sensitive fields (passwords, tokens) never returned in responses
- [ ] Audit log for all mutating operations (who, what, when)

---

## API Documentation Checklist

- [ ] OpenAPI / Swagger spec is complete and up-to-date with implementation
- [ ] Every endpoint has: description, all parameters, all response codes, example request, example response
- [ ] Authentication documented: how to obtain tokens, how to include them
- [ ] Error codes listed with meaning and resolution guidance
- [ ] Changelog section for breaking changes
- [ ] Interactive documentation available (Swagger UI, Redoc, or equivalent)

---

## API Readiness for External Consumers

Before exposing an API externally:

- [ ] Backwards-compatibility policy communicated
- [ ] Rate limits published and enforced
- [ ] SDK or client library provided (or third-party clients verified to work)
- [ ] Status page / uptime commitment defined
- [ ] Support channel identified (email, Slack, GitHub issues)

---

## Common API Anti-Patterns

| Anti-Pattern | Example | Fix |
|---|---|---|
| Verb in URL | `POST /createUser` | `POST /users` |
| God endpoint | `POST /action?type=create\|update\|delete` | Separate endpoints per action |
| Inconsistent casing | `userId` in one field, `user_id` in another | Pick one (camelCase for JSON APIs) |
| Returning 200 for errors | `{"success": false, "message": "not found"}` | Return `404` with proper error body |
| Leaking internals | Stack trace in `error.detail` | Log server-side, return generic message |
| Unbounded response | `GET /events` returns all 10M rows | Require pagination parameters |

---

Related skills: `api-design`, `graphql-development`, `api-documentation`, `security-review`, `performance-review`
