# Architecture Checklist Reference

Quick-reference checklist for architecture design and review decisions. Use when designing new systems, evaluating architectural changes, or reviewing PRs that touch system boundaries.

---

## Design Principles Check

- [ ] **Single Responsibility**: each module/service has one reason to change
- [ ] **Open/Closed**: extend by adding, not by modifying existing code
- [ ] **Liskov Substitution**: subtypes are substitutable without breaking callers
- [ ] **Interface Segregation**: clients depend only on the methods they use
- [ ] **Dependency Inversion**: high-level modules depend on abstractions, not concretions
- [ ] **Separation of Concerns**: business logic, I/O, and presentation are isolated layers
- [ ] **Don't Repeat Yourself**: shared logic exists in one place, with one owner

---

## System Boundary Checklist

Before finalizing a service/module boundary:

- [ ] The boundary is drawn at a seam that will not change often (domain boundary, not technical layer)
- [ ] Communication across the boundary is explicit (API contract, event schema, shared interface)
- [ ] Data ownership is clear -- each entity has one authoritative owner
- [ ] Failure modes across the boundary are defined: what happens if the other side is down?
- [ ] The boundary could be replaced independently without affecting callers

---

## Scalability Checklist

- [ ] Stateless services: session state stored in Redis/DB, not in-process
- [ ] Horizontal scaling tested: multiple instances do not conflict (file locks, in-memory caches)
- [ ] Async for I/O: database calls, HTTP calls, file operations use async/non-blocking patterns
- [ ] Long-running tasks offloaded to queues (not blocking the request thread)
- [ ] Rate limiting and backpressure at system entry points
- [ ] Caching strategy defined: what is cached, TTL, invalidation trigger

---

## Data Architecture Checklist

- [ ] Schema changes are backwards-compatible (additive, not breaking) or gated behind a migration strategy
- [ ] Indexes exist for all columns used in `WHERE`, `JOIN`, `ORDER BY` clauses at expected data volume
- [ ] N+1 query problems identified and resolved with eager loading or DataLoader
- [ ] Sensitive data (PII, payment) identified and marked for encryption-at-rest
- [ ] Soft delete vs. hard delete decision documented -- hard delete by default; soft delete only when audit trail is required
- [ ] Data retention policy defined for all tables/collections

---

## Resilience Checklist

- [ ] Timeouts set on all external calls (HTTP, DB, queue)
- [ ] Circuit breaker pattern for services with high failure probability
- [ ] Retry with exponential backoff and jitter -- not naive retry loops
- [ ] Graceful degradation: what does the system do when a non-critical dependency fails?
- [ ] Health check endpoints return meaningful status (not just 200 OK)
- [ ] Runbook exists for the top 3 most likely failure scenarios

---

## Observability Checklist

- [ ] Structured logging: JSON format, consistent field names (`service`, `trace_id`, `level`, `message`)
- [ ] Distributed tracing: trace IDs propagated across service boundaries
- [ ] Key metrics instrumented: request rate, error rate, latency (p50/p95/p99)
- [ ] Alerts defined for SLO breach (not just "CPU > 80%")
- [ ] Dashboards exist for oncall -- they can diagnose an incident without reading code

---

## ADR (Architecture Decision Record) Checklist

Every significant architectural decision should have an ADR:

- [ ] **Status**: Proposed / Accepted / Deprecated / Superseded
- [ ] **Context**: What is the problem? What constraints exist?
- [ ] **Decision**: What was decided?
- [ ] **Consequences**: What are the positive and negative trade-offs?
- [ ] **Alternatives considered**: What was rejected and why?

Minimum bar: if a developer joining in 6 months would ask "why did you do it this way?", write an ADR.

---

## Common Architecture Anti-Patterns

| Anti-Pattern | Symptom | Fix |
|---|---|---|
| Distributed Monolith | Services that must deploy together | Define proper domain boundaries |
| Shared Database | Two services read/write the same table | Each service owns its data; use events to sync |
| Chatty Services | 10+ API calls to render one page | Coarser APIs or BFF (Backend for Frontend) |
| Anemic Domain Model | Business logic in controllers/services, not entities | Move logic into domain objects |
| God Object | One class/module does everything | Decompose by Single Responsibility |
| Magic Configuration | Behavior controlled by undocumented env flags | Document all config options; use typed config schemas |

---

Related skills: `architecture-design`, `api-design`, `component-boundary-identifier`, `ddd-strategic-design`, `event-driven-architecture`, `microservices-patterns`, `observability-setup`
