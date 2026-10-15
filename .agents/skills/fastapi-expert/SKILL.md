---
name: fastapi-expert
description: Deep FastAPI expertise for async API development, dependency injection, Pydantic models, middleware, and testing. Use when building Python APIs with FastAPI, designing API schemas, or implementing authentication.
summary_l0: "Build FastAPI applications with async patterns, Pydantic models, and dependency injection"
overview_l1: "This skill provides specialized FastAPI expertise covering async API design, Pydantic v2 model patterns, dependency injection, middleware, background tasks, WebSocket support, async database integration, testing, OpenAPI customization, and production deployment. Use it when designing RESTful APIs, building Pydantic v2 models with validators, implementing dependency injection hierarchies, writing middleware for CORS, auth, and rate limiting, running background tasks and WebSocket connections, integrating async databases (SQLAlchemy async, Tortoise ORM), testing with TestClient and dependency overrides, or deploying with uvicorn and Docker. Key capabilities include async endpoint design, Pydantic v2 model architecture, DI hierarchy design, middleware chain implementation, WebSocket handler creation, and comprehensive testing patterns. The expected output is a production-ready FastAPI application with proper async patterns, validation, dependency injection, and deployment configuration. Trigger phrases: fastapi, fast api, pydantic, python api, async api, uvicorn, python rest api, fastapi dependency injection, fastapi middleware, fastapi testing."
---

# FastAPI Expert

Specialized expertise in FastAPI development, providing deep guidance on async API design, Pydantic v2 model patterns, dependency injection, middleware, background tasks, WebSocket support, async database integration, testing strategies, OpenAPI customization, and production deployment.

## When to Use This Skill

Use this skill for:

- Designing RESTful APIs with path, query, and body parameters
- Building Pydantic v2 models with validators, computed fields, and serialization
- Implementing dependency injection hierarchies and scoped dependencies
- Writing middleware for CORS, authentication, rate limiting, and logging
- Running background tasks and WebSocket connections
- Integrating async databases (SQLAlchemy async, Tortoise ORM)
- Testing with TestClient, async fixtures, and dependency overrides
- Customizing OpenAPI schema and documentation
- Deploying with uvicorn, gunicorn, and Docker

**Trigger phrases**: "fastapi", "fast api", "pydantic", "python api", "async api", "uvicorn", "python rest api", "fastapi dependency injection", "fastapi middleware", "fastapi testing"

## What This Skill Does

Provides FastAPI expertise including:

- **Route Design**: Path parameters, query parameters, request body, response models
- **Pydantic v2**: Model validators, computed fields, serialization aliases, discriminated unions
- **Dependency Injection**: Sub-dependencies, yield dependencies, scoped lifetimes
- **Middleware**: CORS, authentication, rate limiting, request timing
- **Background Tasks**: Async background work, task queues
- **WebSockets**: Real-time connections with connection management
- **Database**: SQLAlchemy async sessions, repository pattern, migrations
- **Testing**: TestClient, httpx async client, dependency overrides, factory fixtures
- **Deployment**: uvicorn, gunicorn workers, Docker, health checks

## Instructions

### Step 1: Structure a FastAPI Project

Full walkthrough: [step-1-structure-a-fastapi-project.md](references/step-1-structure-a-fastapi-project.md) (load this step when you reach it).

### Step 2: Design Pydantic v2 Schemas

Full walkthrough: [step-2-design-pydantic-v2-schemas.md](references/step-2-design-pydantic-v2-schemas.md) (load this step when you reach it).

### Step 3: Implement Dependency Injection

Full walkthrough: [step-3-implement-dependency-injection.md](references/step-3-implement-dependency-injection.md) (load this step when you reach it).

### Step 4: Build Route Handlers

Full walkthrough: [step-4-build-route-handlers.md](references/step-4-build-route-handlers.md) (load this step when you reach it).

### Step 5: Middleware Patterns

Full walkthrough: [step-5-middleware-patterns.md](references/step-5-middleware-patterns.md) (load this step when you reach it).

### Step 6: Database Integration (SQLAlchemy Async)

Full walkthrough: [step-6-database-integration-sqlalchemy-async.md](references/step-6-database-integration-sqlalchemy-async.md) (load this step when you reach it).

### Step 7: Background Tasks and WebSockets

Full walkthrough: [step-7-background-tasks-and-websockets.md](references/step-7-background-tasks-and-websockets.md) (load this step when you reach it).

### Step 8: Testing

Full walkthrough: [step-8-testing.md](references/step-8-testing.md) (load this step when you reach it).

### Step 9: Deployment

Full walkthrough: [step-9-deployment.md](references/step-9-deployment.md) (load this step when you reach it).

## Best Practices

- **Use async endpoints for I/O-bound operations**: database queries, HTTP calls, file I/O
- **Define response models explicitly**: prevents leaking internal fields (e.g., hashed_password)
- **Use Annotated type aliases for dependencies**: `DbSession`, `CurrentUser` keep signatures clean
- **Validate all input with Pydantic schemas**: never trust raw request data
- **Use dependency injection, not global state**: makes testing trivial with overrides
- **Commit in the dependency, not the route**: the `get_db` dependency should commit on success and rollback on error
- **Keep routes thin**: delegate business logic to service classes
- **Use structured logging**: include request ID, user ID, and duration in log entries
- **Pin dependency versions**: use `uv.lock` or `pip-compile` for reproducible builds

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will define the endpoint with a plain dict instead of a `response_model`; it is faster." | Without `response_model`, internal fields (password hashes, internal IDs) leak into the JSON response, and the OpenAPI schema no longer matches reality. The explicit model is what enforces the API contract and filters the output. |
| "It is just one synchronous DB call inside an async endpoint; it will not matter." | A blocking call inside an `async def` handler stalls the entire event loop, so one slow query freezes every concurrent request, not just its own. Use an async driver or offload to a thread pool. |
| "I will validate the request body with a few `if` checks instead of a Pydantic model." | Manual checks miss type coercion and edge cases Pydantic handles for free, and they do not appear in the generated docs. A malformed payload then reaches your business logic instead of being rejected at the boundary with a 422. |

## Verification

- [ ] All endpoints have explicit `response_model` definitions
- [ ] Input validation uses Pydantic schemas (not manual checks)
- [ ] Passwords are hashed (bcrypt/argon2), never stored in plain text
- [ ] JWT tokens have expiration times and are validated on every request
- [ ] Database sessions are managed via dependency injection with proper cleanup
- [ ] Background tasks do not block the event loop (use async or thread pool)
- [ ] CORS is configured with specific origins (not wildcard in production)
- [ ] Tests use dependency overrides for database isolation
- [ ] Health check endpoint verifies database connectivity
- [ ] Dockerfile uses non-root user and multi-stage build
- [ ] OpenAPI schema is reviewed and reflects actual API contract
- [ ] Rate limiting is applied to authentication endpoints

## References

- `references/dependency-injection-patterns.md` - quick-lookup guide for FastAPI dependency injection patterns covering database sessions, authentication, pagination, and testing.

## Related Skills

- [[python-cleanup]] - Python code quality and cleanup patterns
- [[unit-tests]] - General unit testing strategies
- [[api-documentation]] - API documentation standards
- [[kubernetes-expert]] - Container orchestration for API deployment
- [[security-review]] - Security review for API endpoints

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
