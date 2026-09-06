---
name: integration-test-generator
description: Generate integration tests that verify component interactions across API boundaries, databases, message queues, and external services. Use when testing service-to-service communication, database operations, contract testing, REST/GraphQL endpoints, or using testcontainers for realistic environments.
summary_l0: "Generate integration tests for APIs, databases, message queues, and service interactions"
overview_l1: "This skill generates integration tests that verify component interactions across API boundaries, databases, message queues, and external services. Use it when testing service-to-service communication, database operations, contract testing, REST/GraphQL endpoints, or setting up testcontainers for realistic environments. Key capabilities include API boundary test generation, database integration testing with migration verification, message queue consumer/producer testing, external service integration with contract validation, testcontainers setup for realistic database and service environments, REST and GraphQL endpoint testing, and test data seeding strategies. The expected output is integration test suites with realistic environment setup, proper isolation, and cross-component verification. Trigger phrases: integration tests, API testing, database testing, testcontainers, service testing, contract testing, message queue testing, REST testing, GraphQL testing."
---

# Integration Test Generator

Generate integration tests that verify the correct interaction between multiple components, services, and infrastructure dependencies. Unlike unit tests that isolate a single function, integration tests exercise the boundaries where components connect: HTTP APIs, database queries, message queues, file systems, and third-party services.

## When to Use This Skill

Use this skill when you need to:

- Test REST or GraphQL API endpoints end-to-end (request through response)
- Verify database operations (queries, transactions, migrations) against a real or containerized database
- Test service-to-service communication patterns (synchronous calls, async messaging)
- Validate message queue producers and consumers (Kafka, RabbitMQ, SQS)
- Implement contract tests between API providers and consumers
- Set up testcontainers for reproducible integration test environments
- Verify authentication and authorization flows across service boundaries
- Test file upload/download and storage integration
- Validate caching behaviour with real cache stores (Redis, Memcached)

**Trigger phrases**: "integration test", "API test", "database test", "service test", "contract test", "testcontainers", "end-to-end API", "test the endpoint", "test database queries", "message queue test", "REST test", "GraphQL test"

## What This Skill Does

### Integration Testing Layers

Integration tests operate at several layers, each with different scope and infrastructure requirements:

| Layer | What It Tests | Infrastructure Needed |
|---|---|---|
| API Integration | HTTP request/response cycle | Running application server |
| Database Integration | SQL/NoSQL operations, migrations, transactions | Database instance (container or in-memory) |
| Service-to-Service | Inter-service HTTP/gRPC calls | Multiple running services or mocks |
| Message Queue | Producer/consumer message flow | Message broker (container or embedded) |
| Contract Testing | API schema compatibility between provider and consumer | Contract broker (e.g., Pact) |
| External Service | Third-party API integration | Mocks, stubs, or sandbox environments |

### Test Architecture Principles

1. **Use real infrastructure when feasible**: Prefer containerized databases and brokers over in-memory fakes to catch real-world issues (SQL dialect differences, connection pooling, transaction isolation)
2. **Isolate test data**: Each test should create its own data and clean up afterward; never depend on pre-existing database rows
3. **Control external boundaries**: Mock or stub external services you do not own; use contract tests to verify compatibility
4. **Keep tests fast**: Integration tests are slower than unit tests but should still complete in seconds, not minutes; use connection pooling, parallel containers, and test data factories
5. **Test failure modes**: Integration tests should cover not just happy paths but also network errors, timeouts, invalid responses, and partial failures

## Instructions

### Step 1: Set Up API Integration Tests

Full walkthrough: [step-1-set-up-api-integration-tests.md](references/step-1-set-up-api-integration-tests.md) (load this step when you reach it).

### Step 2: Set Up Database Integration Tests with Testcontainers

Full walkthrough: [step-2-set-up-database-integration-tests-with-testcontainers.md](references/step-2-set-up-database-integration-tests-with-testcontainers.md) (load this step when you reach it).

### Step 3: Set Up Service-to-Service Integration Tests

Full walkthrough: [step-3-set-up-service-to-service-integration-tests.md](references/step-3-set-up-service-to-service-integration-tests.md) (load this step when you reach it).

### Step 4: Set Up Contract Tests

Full walkthrough: [step-4-set-up-contract-tests.md](references/step-4-set-up-contract-tests.md) (load this step when you reach it).

### Step 5: Set Up Message Queue Integration Tests

Full walkthrough: [step-5-set-up-message-queue-integration-tests.md](references/step-5-set-up-message-queue-integration-tests.md) (load this step when you reach it).

## Best Practices

- **Use testcontainers over mocks for databases**: In-memory databases (H2, SQLite) have different SQL dialects and behaviour; testcontainers provide the real engine with minimal overhead
- **Isolate test data with transactions**: Wrap each test in a transaction and roll back after; this is faster than truncating tables
- **Test both success and failure paths**: An integration test that only covers the happy path provides false confidence; test timeouts, 4xx/5xx responses, and malformed data
- **Use contract tests between teams**: When two teams own different services, contract tests prevent breaking changes without requiring both services to be running simultaneously
- **Keep integration tests in a separate directory**: Integration tests have different infrastructure requirements and run slower; separate them from unit tests so developers can run unit tests quickly
- **Tag tests by infrastructure dependency**: Use markers/tags (e.g., `@Tag("database")`, `@pytest.mark.database`) so you can run subsets locally
- **Use factory functions for test data**: Create helper functions that generate valid test entities with sensible defaults; this reduces boilerplate and makes tests more readable
- **Set explicit timeouts on all network calls**: An integration test that hangs for 30 seconds waiting for a response wastes CI time; set timeouts and assert on timeout behaviour

## Common Pitfalls

- **Testing implementation details instead of contracts**: Integration tests should verify external behaviour (HTTP status codes, response bodies, database state), not internal method calls
- **Sharing test data across tests**: Tests that depend on data created by other tests are order-dependent and fragile; each test must create its own data
- **Not cleaning up resources**: Containers, connections, and file handles that are not closed leak resources and cause subsequent tests to fail
- **Using production credentials in tests**: Integration tests should never connect to production databases or APIs; use containers, mocks, or sandbox environments
- **Making tests too broad**: An integration test that exercises the entire request lifecycle through five services is an end-to-end test, not an integration test; keep the scope to 2-3 components
- **Ignoring test container startup time**: Container startup adds seconds to the test suite; use module-scoped containers that are shared across tests within the same module
- **Hardcoding URLs and ports**: Tests that bind to `localhost:5432` fail when that port is in use; use dynamic port allocation from testcontainers
- **Not testing idempotency**: Integration tests should verify that retrying an operation (e.g., creating the same order twice) produces the correct result, not a duplicate
- **Skipping error response body assertions**: Verifying that an API returns 400 is not enough; assert that the error response body contains a meaningful error code and message

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Unit tests are enough -- integration tests duplicate coverage" | Unit tests verify individual functions with mocked dependencies; integration tests verify that the wiring between those functions works correctly; the Therac-25 radiation overdose incidents involved components that each worked correctly in isolation but failed catastrophically when integrated. |
| "Integration tests are too slow to run in CI" | Testcontainers starts a real database in 2-5 seconds and tears it down after the suite; the total overhead for a 50-test integration suite using containers is typically under 60 seconds, well within CI time budgets. |
| "We'll catch integration issues in the staging environment" | Staging environments are shared, have stale data, and are expensive to reproduce deterministically; an integration test suite that runs on every PR catches integration regressions at the point of introduction, not after merge. |
| "Sharing a database across integration tests is fine if tests are careful" | Test isolation via shared state fails when tests run in parallel or when a failing test leaves the database in an unexpected state; each test must own its data setup and teardown to be deterministic. |
| "Integration tests should cover the full end-to-end flow" | Tests that span the entire system are end-to-end tests, not integration tests; keeping integration tests scoped to 2-3 components produces tests that are fast, reliable, and unambiguous when they fail. |

## Verification

- [ ] Each integration test creates its own test data and does not depend on data from another test (verified by running tests in random order)
- [ ] All database and service containers are started and torn down per test module (not shared across the entire suite)
- [ ] Integration tests cover both success and error paths for each tested boundary
- [ ] Test suite completes in under 120 seconds on a standard CI runner
- [ ] All tests pass deterministically on three consecutive runs: `pytest tests/integration -q` exits with code 0 each time

## Related Skills

- [[unit-tests]] -- isolates single functions with mocks beneath the integration layer these tests exercise
- [[e2e-testing-automation]] -- drives full end-to-end flows where this skill stops at 2-3 components
- [[mocks-fixtures]] -- supplies the stubs and data factories used to control external boundaries here
- [[domain-contract-validator]] -- enforces the provider/consumer contracts these integration tests validate
- [[test-structure]] -- sets up the separate integration test directory and infrastructure config
