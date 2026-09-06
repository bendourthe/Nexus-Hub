---
name: api-design
description: API design principles for REST, GraphQL, and gRPC including versioning, pagination, error handling, and documentation. Use when designing new APIs, reviewing API contracts, or migrating between API styles.
summary_l0: "Design REST, GraphQL, and gRPC APIs with versioning, pagination, and error handling"
overview_l1: "This skill provides comprehensive guidance for designing, documenting, and evolving APIs across REST, GraphQL, and gRPC paradigms. Use it when designing a new API from scratch, reviewing an existing API contract, choosing between REST, GraphQL, and gRPC, implementing pagination, filtering, and sorting, designing error response formats (RFC 7807 Problem Details), planning API versioning and evolution, setting up rate limiting and authentication, writing OpenAPI, GraphQL schema, or protobuf definitions, or migrating between API styles. Key capabilities include resource naming and HTTP method mapping, GraphQL schema and resolver design, gRPC service and protobuf definition, pagination patterns (cursor, offset, keyset), error handling standards, versioning strategies (URL, header, content type), and contract-first development workflows. The expected output is API specifications (OpenAPI, GraphQL SDL, or proto files), implementation code, and documentation. Trigger phrases: API design, REST API, GraphQL schema, gRPC proto, API versioning, pagination, error handling, OpenAPI, API contract, rate limiting, HATEOAS."
---

# API Design

Comprehensive guidance for designing, documenting, and evolving APIs across REST, GraphQL, and gRPC paradigms, covering resource modeling, versioning strategies, error handling standards, pagination, rate limiting, and contract-first development.

## When to Use This Skill

Use this skill for:

- Designing a new REST, GraphQL, or gRPC API from scratch
- Reviewing an existing API contract for consistency and best practices
- Choosing between REST, GraphQL, and gRPC for a given use case
- Implementing pagination, filtering, and sorting patterns
- Designing error response formats (RFC 7807 Problem Details)
- Planning API versioning and evolution strategies
- Setting up rate limiting and authentication headers
- Writing OpenAPI, GraphQL schema, or protobuf definitions
- Migrating between API styles (REST to GraphQL, REST to gRPC)

**Trigger phrases**: "API design", "REST API", "GraphQL schema", "gRPC proto", "API versioning", "pagination", "error handling", "OpenAPI", "API contract", "rate limiting", "HATEOAS"

## What This Skill Does

Provides API design patterns including:

- **REST Design**: Resource naming, HTTP methods, status codes, HATEOAS links
- **GraphQL Design**: Schema definition, query/mutation patterns, N+1 prevention
- **gRPC Design**: Service definitions, protobuf best practices, streaming patterns
- **Versioning**: URL path, header, content negotiation strategies with trade-offs
- **Pagination**: Cursor-based, offset-based, keyset patterns with examples
- **Error Handling**: RFC 7807 Problem Details, GraphQL error extensions, gRPC status codes
- **Rate Limiting**: Token bucket, sliding window, response headers
- **Authentication**: API key, OAuth 2.0, JWT bearer token header conventions
- **Documentation**: OpenAPI 3.1, GraphQL introspection, gRPC reflection

## Instructions

### Step 1: Choose the Right API Style

Full walkthrough: [step-1-choose-the-right-api-style.md](references/step-1-choose-the-right-api-style.md) (load this step when you reach it).

### Step 2: Design REST APIs

Full walkthrough: [step-2-design-rest-apis.md](references/step-2-design-rest-apis.md) (load this step when you reach it).

### Step 3: Design GraphQL APIs

Full walkthrough: [step-3-design-graphql-apis.md](references/step-3-design-graphql-apis.md) (load this step when you reach it).

### Step 4: Design gRPC APIs

Full walkthrough: [step-4-design-grpc-apis.md](references/step-4-design-grpc-apis.md) (load this step when you reach it).

### Step 5: Implement Error Handling

Full walkthrough: [step-5-implement-error-handling.md](references/step-5-implement-error-handling.md) (load this step when you reach it).

### Step 6: Implement Pagination

Full walkthrough: [step-6-implement-pagination.md](references/step-6-implement-pagination.md) (load this step when you reach it).

### Step 7: API Versioning Strategy

Full walkthrough: [step-7-api-versioning-strategy.md](references/step-7-api-versioning-strategy.md) (load this step when you reach it).

## Best Practices

- **Design the API before writing code** - Contract-first development prevents drift
- **Use consistent naming** - Pick camelCase or snake_case and stick with it project-wide
- **Return appropriate status codes** - 201 for creation, 204 for deletion, 422 for validation
- **Always paginate list endpoints** - Even if you think the list will be small
- **Version from day one** - Adding versioning later is painful
- **Use RFC 7807 for errors** - Structured errors are machine-parseable and debuggable
- **Include rate limit headers** - Clients need to know their quota without guessing
- **Make APIs idempotent** - Use idempotency keys for POST operations
- **Document every endpoint** - Undocumented APIs are unusable APIs
- **Validate inputs strictly, accept outputs liberally** - Postel's law applies to APIs

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll version the API when we need to break it" | Adding versioning to an unversioned API requires coordinating all consumers simultaneously; the Stripe API has never forced a breaking change on consumers precisely because versioning was built in from day one. |
| "Error codes don't matter, clients just check HTTP status" | Undifferentiated 400 responses with no error code force clients to parse free-text error messages to distinguish "invalid email format" from "email already exists", creating brittle integrations that break when wording changes. |
| "Cursor-based pagination is too complex; offset is fine" | Offset pagination silently skips or duplicates records when items are inserted or deleted between pages; this causes data loss in exports and duplicate processing in event consumers at any non-trivial insert rate. |
| "The OpenAPI spec is documentation, not the source of truth" | When code and spec diverge, the spec becomes actively harmful -- clients build to the spec and encounter runtime errors; contract-first development enforces equivalence at every build. |
| "We'll add rate limiting after launch if it becomes a problem" | Unrated endpoints have been used in credential-stuffing attacks that generated millions of login attempts within minutes of launch; retroactively adding rate limiting to a live API requires coordinating with all existing integrations. |
| "GraphQL means we don't need to worry about over-fetching" | GraphQL eliminates over-fetching at the field level but introduces N+1 query problems at the resolver level; without DataLoader or query depth limits, a single client request can trigger thousands of database queries. |

## Verification

- [ ] API versioning strategy is implemented (URL path, header, or content-type negotiation) and documented
- [ ] All error responses conform to RFC 7807 Problem Details with a machine-readable `type` and `code` field
- [ ] Pagination is implemented with cursor-based or keyset approach for all list endpoints (no raw offset on mutable collections)
- [ ] OpenAPI, GraphQL SDL, or proto file is checked into source control and matches the deployed API behavior
- [ ] Rate limiting headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`) are returned on throttled responses
- [ ] All state-changing POST endpoints that may be retried support idempotency keys

## Related Skills

- [[architecture-design]] -- system-level architecture that APIs expose
- [[ddd-strategic-design]] -- published language and open host service patterns
- [[api-documentation]] -- generating and maintaining API reference docs
- [[security-review]] -- authentication, authorization, and API security audit
- [[performance-review]] -- API latency optimization and caching strategies

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
