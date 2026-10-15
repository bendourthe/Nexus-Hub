---
name: microservices-patterns
description: Microservices architecture patterns including service decomposition, inter-service communication, data management, and resilience. Use when designing distributed systems, migrating monoliths, or implementing service mesh.
summary_l0: "Architect microservices with decomposition, resilience, and distributed data patterns"
overview_l1: "This skill provides comprehensive guidance for designing, building, and operating microservices architectures. Use it when decomposing a monolith into microservices, choosing communication patterns (sync REST/gRPC, async messaging, event-driven), implementing distributed data patterns (database per service, saga, CQRS, event sourcing), adding resilience patterns (circuit breaker, bulkhead, retry, timeout), designing API gateway routing, setting up service discovery and load balancing, implementing distributed tracing, or planning strangler fig migrations. Key capabilities include decomposition strategies by business capability and subdomain, inter-service communication pattern selection, saga orchestration and choreography, circuit breaker implementation, API gateway configuration, service mesh setup (Istio, Linkerd), and observability instrumentation. The expected output is architecture documentation, service boundary definitions, communication contracts, and infrastructure configuration. Trigger phrases: microservices, service decomposition, circuit breaker, saga pattern, CQRS, event sourcing, API gateway, service mesh, distributed system, strangler fig, bulkhead, service discovery."
---

# Microservices Patterns

Comprehensive guidance for designing, building, and operating microservices architectures, covering service decomposition strategies, inter-service communication, distributed data management, resilience patterns, and infrastructure concerns like API gateways, service discovery, and observability.

## When to Use This Skill

Use this skill for:

- Decomposing a monolith into microservices
- Choosing communication patterns (sync REST/gRPC, async messaging, event-driven)
- Implementing distributed data patterns (database per service, saga, CQRS, event sourcing)
- Adding resilience patterns (circuit breaker, bulkhead, retry, timeout)
- Designing API gateway routing and aggregation
- Setting up service discovery and load balancing
- Implementing distributed tracing and observability
- Planning a strangler fig migration from monolith to microservices
- Configuring service mesh (Istio, Linkerd) for traffic management

**Trigger phrases**: "microservices", "service decomposition", "circuit breaker", "saga pattern", "CQRS", "event sourcing", "API gateway", "service mesh", "distributed system", "strangler fig", "bulkhead", "service discovery"

## What This Skill Does

Provides distributed system patterns including:

- **Decomposition**: By business capability, by subdomain, strangler fig migration
- **Communication**: Synchronous (REST, gRPC), asynchronous (message queues, event bus)
- **Data Management**: Database per service, saga orchestration/choreography, CQRS, event sourcing
- **Resilience**: Circuit breaker, bulkhead, retry with backoff, timeout, fallback
- **Infrastructure**: API gateway, service discovery, service mesh, sidecar pattern
- **Observability**: Distributed tracing, structured logging, metrics, health checks
- **Deployment**: Independent deployability, container orchestration, blue-green, canary

## Instructions

### Step 1: Decide Whether Microservices Are Appropriate

Microservices add operational complexity. Use them only when the benefits outweigh the costs.

**When Microservices Make Sense**:

```
- Multiple autonomous teams need independent deployment cycles
- Different parts of the system have vastly different scaling needs
- Different parts need different technology stacks
- The monolith has become too large for a single team to reason about
- Deployment of one feature blocks deployment of unrelated features
```

**When a Monolith Is Better**:

```
- Small team (fewer than 8 engineers)
- Early-stage product with unclear domain boundaries
- Low traffic with uniform scaling needs
- Simple CRUD application without complex business rules
- Team lacks operational maturity (no CI/CD, no monitoring)
```

### Step 2: Decompose by Business Capability or Subdomain

**Decomposition by Business Capability**:

```
E-Commerce Platform
│
├── Product Catalog Service    (manages product information)
├── Inventory Service          (tracks stock levels)
├── Order Service              (handles order lifecycle)
├── Payment Service            (processes payments)
├── Shipping Service           (manages delivery logistics)
├── Customer Service           (customer profiles, preferences)
├── Notification Service       (email, SMS, push notifications)
└── Analytics Service          (reporting, dashboards)
```

**Decomposition by DDD Subdomain**:

```
Core Subdomains (competitive advantage, build in-house):
  - Order Management
  - Pricing Engine
  - Recommendation Engine

Supporting Subdomains (necessary but not differentiating):
  - Inventory Management
  - Customer Management
  - Notification Delivery

Generic Subdomains (commodity, buy or use open source):
  - Authentication (Auth0, Keycloak)
  - Payment Processing (Stripe, Adyen)
  - Email Delivery (SendGrid, SES)
```

**Strangler Fig Migration Plan**:

```
Phase 1: Add Facade (API Gateway)
  ┌──────────────┐
  │  API Gateway  │
  │  (new facade) │
  └──────┬───────┘
         │ Routes 100% to monolith
         ▼
  ┌──────────────┐
  │   Monolith   │
  └──────────────┘

Phase 2: Extract First Service
  ┌──────────────┐
  │  API Gateway  │
  └──┬────────┬──┘
     │        │
     ▼        ▼
  ┌──────┐ ┌──────────┐
  │ New  │ │ Monolith │
  │ Svc  │ │ (minus   │
  │  A   │ │  Svc A)  │
  └──────┘ └──────────┘

Phase 3: Extract More Services
  ┌──────────────┐
  │  API Gateway  │
  └─┬───┬───┬──┬─┘
    │   │   │  │
    ▼   ▼   ▼  ▼
  ┌───┐┌───┐┌───┐┌──────────┐
  │ A ││ B ││ C ││ Monolith │
  └───┘└───┘└───┘│ (shrinking)│
                  └──────────┘

Phase N: Decommission Monolith
  All traffic routed to new services.
```

### Step 3: Choose Communication Patterns

**Synchronous Communication (REST/gRPC)**:

```
Use when:
  - Request needs an immediate response
  - Simple request-reply semantics
  - Low latency required between two specific services

Risks:
  - Temporal coupling (caller blocks until response)
  - Cascading failures (downstream outage blocks upstream)
  - Must implement circuit breakers and timeouts
```

**Asynchronous Communication (Message Queue / Event Bus)**:

```
Use when:
  - Caller does not need an immediate response
  - Fan-out to multiple consumers
  - Load leveling (absorb traffic spikes)
  - Cross-context integration via domain events

Benefits:
  - Temporal decoupling (producer and consumer run independently)
  - Natural resilience (messages are buffered during outages)
  - Scalable consumers (add more workers as load increases)
```

**Event-Driven Architecture**:

```python
# Order Service publishes event after placing order
# infrastructure/message_publisher.py
import json
from datetime import datetime

class OrderEventPublisher:
    def __init__(self, broker_client):
        self._broker = broker_client

    async def publish_order_placed(self, order) -> None:
        event = {
            "eventType": "order.placed",
            "eventId": str(uuid4()),
            "occurredAt": datetime.utcnow().isoformat(),
            "data": {
                "orderId": str(order.id),
                "customerId": str(order.customer_id),
                "totalCents": order.total.amount,
                "currency": order.total.currency,
                "lineItems": [
                    {
                        "productId": str(line.product_id),
                        "quantity": line.quantity.value,
                    }
                    for line in order.lines
                ],
            },
        }
        await self._broker.publish(
            topic="orders.events",
            key=str(order.id),
            value=json.dumps(event).encode(),
        )
```

```python
# Inventory Service consumes order.placed events
# infrastructure/order_event_consumer.py
class InventoryEventHandler:
    def __init__(self, inventory_repo):
        self._repo = inventory_repo

    async def handle_order_placed(self, event: dict) -> None:
        for item in event["data"]["lineItems"]:
            await self._repo.reserve_stock(
                product_id=item["productId"],
                quantity=item["quantity"],
                order_id=event["data"]["orderId"],
            )
```

### Step 4: Implement Distributed Data Patterns

**Database per Service**:

```
Each service owns its data exclusively.
No direct database access across service boundaries.
Data is shared only through APIs or events.

┌────────────┐  ┌────────────┐  ┌────────────┐
│  Order Svc │  │ Catalog Svc│  │ Customer   │
│            │  │            │  │ Svc        │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      │               │               │
┌─────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
│ Orders DB  │  │ Catalog DB │  │ Customers  │
│ (Postgres) │  │ (MongoDB)  │  │ DB (PG)    │
└────────────┘  └────────────┘  └────────────┘
```

**Saga Pattern: Orchestration vs. Choreography**:

Orchestration (central coordinator):

```python
# application/sagas/create_order_saga.py
class CreateOrderSaga:
    """Orchestrator that coordinates the order creation workflow."""

    STEPS = [
        ("inventory", "reserve"),
        ("payment", "authorize"),
        ("order", "confirm"),
    ]
    COMPENSATIONS = {
        "payment.authorize": ("payment", "void"),
        "inventory.reserve": ("inventory", "release"),
    }

    def __init__(self, inventory_client, payment_client, order_repo):
        self._inventory = inventory_client
        self._payment = payment_client
        self._orders = order_repo

    async def execute(self, order_id: str) -> str:
        completed_steps = []

        try:
            # Step 1: Reserve inventory
            await self._inventory.reserve(order_id)
            completed_steps.append("inventory.reserve")

            # Step 2: Authorize payment
            await self._payment.authorize(order_id)
            completed_steps.append("payment.authorize")

            # Step 3: Confirm order
            await self._orders.confirm(order_id)
            completed_steps.append("order.confirm")

            return "completed"

        except Exception as e:
            # Compensate in reverse order
            for step in reversed(completed_steps):
                if step in self.COMPENSATIONS:
                    svc, method = self.COMPENSATIONS[step]
                    client = getattr(self, f"_{svc}")
                    await getattr(client, method)(order_id)

            await self._orders.reject(order_id, reason=str(e))
            return "failed"
```

Choreography (event-driven, no central coordinator):

```
Order Service                    Inventory Service
     │                                │
     │── OrderPlaced ────────────────>│
     │                                │── InventoryReserved ──>
     │                                │
     │                          Payment Service
     │                                │
     │                                │── PaymentAuthorized ──>
     │                                │
     │<── PaymentAuthorized ──────────│
     │                                │
     │── OrderConfirmed ─────────────>│ (notification, etc.)

# Compensation flow (if payment fails):
Payment Service
     │
     │── PaymentDeclined ────────────> Inventory Service
     │                                      │
     │                                      │── InventoryReleased
     │
     │── PaymentDeclined ────────────> Order Service
                                            │
                                            │── OrderRejected
```

**CQRS (Command Query Responsibility Segregation)**:

```python
# Write side: rich domain model
class OrderCommandHandler:
    def __init__(self, repo: OrderRepository, events: EventPublisher):
        self._repo = repo
        self._events = events

    async def handle_place_order(self, cmd: PlaceOrderCommand) -> str:
        order = await self._repo.find_by_id(cmd.order_id)
        order.place()  # Domain logic, invariant checks
        await self._repo.save(order)
        for event in order.collect_events():
            await self._events.publish(event)
        return str(order.id)

# Read side: optimized projections
class OrderReadModel:
    """Denormalized read model, updated by consuming domain events."""

    def __init__(self, read_db):
        self._db = read_db

    async def handle_order_placed(self, event: dict) -> None:
        await self._db.execute("""
            INSERT INTO order_summaries
                (id, customer_id, status, total, item_count, placed_at)
            VALUES (%s, %s, 'placed', %s, %s, %s)
        """, (
            event["orderId"],
            event["customerId"],
            event["total"],
            event["itemCount"],
            event["placedAt"],
        ))

    async def search_orders(
        self, customer_id: str, status: str | None = None
    ) -> list[dict]:
        query = "SELECT * FROM order_summaries WHERE customer_id = %s"
        params = [customer_id]
        if status:
            query += " AND status = %s"
            params.append(status)
        return await self._db.fetch(query, params)
```

### Step 5: Implement Resilience Patterns

**Circuit Breaker (Python)**:

```python
# infrastructure/circuit_breaker.py
import time
from enum import Enum
from threading import Lock

class CircuitState(Enum):
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, reject fast
    HALF_OPEN = "half_open"    # Testing recovery

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 3,
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._success_threshold = success_threshold
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and time.time() - self._last_failure_time
                    > self._recovery_timeout
            ):
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            return self._state

    def call(self, func, *args, **kwargs):
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitOpenError(
                "Circuit is open. Call rejected to protect downstream."
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            else:
                self._failure_count = 0

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._failure_count >= self._failure_threshold:
                self._state = CircuitState.OPEN

class CircuitOpenError(Exception):
    pass
```

**Retry with Exponential Backoff**:

```python
# infrastructure/retry.py
import asyncio
import random
from functools import wraps

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (IOError, TimeoutError),
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    if attempt == max_retries:
                        raise
                    delay = min(
                        base_delay * (2 ** attempt)
                        + random.uniform(0, 1),  # Jitter
                        max_delay,
                    )
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_retries=3, retryable_exceptions=(IOError,))
async def call_payment_service(order_id: str, amount: int):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            "http://payment-service/authorize",
            json={"orderId": order_id, "amount": amount},
        )
        resp.raise_for_status()
        return resp.json()
```

**Bulkhead Pattern (Thread Pool Isolation)**:

```python
# infrastructure/bulkhead.py
import asyncio
from contextlib import asynccontextmanager

class Bulkhead:
    """Limits concurrent calls to a resource to prevent cascade failures."""

    def __init__(self, name: str, max_concurrent: int = 10):
        self.name = name
        self._semaphore = asyncio.Semaphore(max_concurrent)

    @asynccontextmanager
    async def acquire(self):
        acquired = self._semaphore._value > 0
        if not acquired:
            raise BulkheadFullError(
                f"Bulkhead '{self.name}' is full. "
                f"Max concurrent: {self._semaphore._value}"
            )
        async with self._semaphore:
            yield

class BulkheadFullError(Exception):
    pass

# Usage
payment_bulkhead = Bulkhead("payment-service", max_concurrent=20)
inventory_bulkhead = Bulkhead("inventory-service", max_concurrent=50)

async def process_order(order_id: str):
    async with payment_bulkhead.acquire():
        payment = await call_payment_service(order_id)
    async with inventory_bulkhead.acquire():
        reservation = await call_inventory_service(order_id)
```

### Step 6: Configure API Gateway

**API Gateway Responsibilities**:

```
- Request routing to backend services
- Authentication and authorization (JWT validation)
- Rate limiting and throttling
- Request/response transformation
- SSL termination
- Load balancing
- Circuit breaking for downstream services
- Request logging and distributed tracing header injection
```

**Kong Gateway Configuration Example**:

```yaml
# kong.yml (declarative configuration)
_format_version: "3.0"

services:
  - name: order-service
    url: http://order-service:8080
    routes:
      - name: orders-route
        paths:
          - /v1/orders
        strip_path: false
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          policy: redis
          redis_host: redis
      - name: jwt
        config:
          claims_to_verify:
            - exp
      - name: correlation-id
        config:
          header_name: X-Correlation-ID
          generator: uuid

  - name: catalog-service
    url: http://catalog-service:8080
    routes:
      - name: products-route
        paths:
          - /v1/products
        strip_path: false
    plugins:
      - name: rate-limiting
        config:
          minute: 500
          policy: redis
          redis_host: redis
      - name: proxy-cache
        config:
          response_code:
            - 200
          request_method:
            - GET
          content_type:
            - application/json
          cache_ttl: 60
```

### Step 7: Multi-Service Docker Compose (Development)

```yaml
# docker-compose.yml
version: "3.9"

services:
  # --- API Gateway ---
  gateway:
    image: kong:3.6
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /etc/kong/kong.yml
    volumes:
      - ./gateway/kong.yml:/etc/kong/kong.yml:ro
    depends_on:
      - order-service
      - catalog-service
      - customer-service

  # --- Order Service ---
  order-service:
    build: ./services/order
    ports:
      - "8081:8080"
    environment:
      DATABASE_URL: postgres://orders:secret@order-db:5432/orders
      KAFKA_BROKERS: kafka:9092
    depends_on:
      order-db:
        condition: service_healthy
      kafka:
        condition: service_healthy

  order-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: orders
      POSTGRES_USER: orders
      POSTGRES_PASSWORD: secret
    volumes:
      - order-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orders"]
      interval: 5s
      timeout: 5s
      retries: 5

  # --- Catalog Service ---
  catalog-service:
    build: ./services/catalog
    ports:
      - "8082:8080"
    environment:
      MONGO_URI: mongodb://catalog-db:27017/catalog
    depends_on:
      catalog-db:
        condition: service_healthy

  catalog-db:
    image: mongo:7
    volumes:
      - catalog-data:/data/db
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh --quiet
      interval: 5s
      timeout: 5s
      retries: 5

  # --- Customer Service ---
  customer-service:
    build: ./services/customer
    ports:
      - "8083:8080"
    environment:
      DATABASE_URL: postgres://customers:secret@customer-db:5432/customers
    depends_on:
      customer-db:
        condition: service_healthy

  customer-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: customers
      POSTGRES_USER: customers
      POSTGRES_PASSWORD: secret
    volumes:
      - customer-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U customers"]
      interval: 5s
      timeout: 5s
      retries: 5

  # --- Messaging ---
  kafka:
    image: bitnami/kafka:3.7
    ports:
      - "9092:9092"
    environment:
      KAFKA_CFG_NODE_ID: 0
      KAFKA_CFG_PROCESS_ROLES: controller,broker
      KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: 0@kafka:9093
      KAFKA_CFG_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_CFG_CONTROLLER_LISTENER_NAMES: CONTROLLER
    healthcheck:
      test: kafka-topics.sh --bootstrap-server localhost:9092 --list
      interval: 10s
      timeout: 10s
      retries: 5

  # --- Observability ---
  jaeger:
    image: jaegertracing/all-in-one:1.55
    ports:
      - "16686:16686"   # UI
      - "4317:4317"     # OTLP gRPC
      - "4318:4318"     # OTLP HTTP

volumes:
  order-data:
  catalog-data:
  customer-data:
```

## Best Practices

- **Start with a modular monolith** - Extract services only when you have proven bounded context boundaries
- **One database per service** - Shared databases create hidden coupling that defeats the purpose of microservices
- **Use asynchronous communication by default** - Synchronous calls between services create temporal coupling
- **Implement circuit breakers on all outbound calls** - One slow dependency should not bring down your entire system
- **Design for independent deployability** - Each service must be deployable without coordinating with other teams
- **Automate everything** - CI/CD per service, infrastructure as code, automated testing
- **Implement distributed tracing from day one** - Debugging distributed systems without tracing is nearly impossible
- **Use correlation IDs across all services** - Propagate a single request ID through every log and span
- **Prefer choreography over orchestration** - Choreography is more resilient and loosely coupled
- **Define clear API contracts** - Use schema registries or contract testing (Pact) to prevent breaking changes

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Sharing one database between two services is fine, it's simpler" | A shared database couples the two services at the schema level, so neither can change a table without coordinating a release, which defeats the independent-deployability that justified splitting them; database-per-service is the boundary that makes services autonomous. |
| "We don't need circuit breakers, our services are reliable" | A single slow downstream dependency without a circuit breaker exhausts the caller's thread pool, and the failure cascades upstream until the whole system is down; the breaker exists to fail fast and contain the blast radius. |
| "Synchronous calls are easier than async messaging, just chain the services" | A request that synchronously fans out across five services multiplies latency and fails if any one is down; for workflows that can tolerate eventual consistency, async messaging removes the temporal coupling that makes the chain fragile. |
| "We'll add distributed tracing later when we have time" | Without correlation IDs and tracing from day one, the first cross-service production incident is undiagnosable -- you cannot follow one request across service logs; retrofitting tracing during an outage is far costlier than wiring it in upfront. |

## Verification

- [ ] Each service has a single, well-defined business responsibility
- [ ] Each service owns its data (no shared databases)
- [ ] Inter-service communication uses defined contracts (OpenAPI, proto, AsyncAPI)
- [ ] Circuit breakers configured on all outbound synchronous calls
- [ ] Retry with exponential backoff and jitter for transient failures
- [ ] Timeouts set on every network call (no unbounded waits)
- [ ] Distributed tracing enabled across all services (OpenTelemetry)
- [ ] Correlation ID propagated through all requests and logs
- [ ] Health check endpoints expose dependency status
- [ ] Transactional outbox or CDC used for reliable event publishing
- [ ] API gateway handles cross-cutting concerns (auth, rate limiting, routing)
- [ ] Each service independently deployable (no coordinated releases)
- [ ] Contract tests (Pact or similar) verify API compatibility
- [ ] Runbooks documented for common operational scenarios

## Related Skills

- [[architecture-design]] -- system-level architecture and trade-off analysis
- [[ddd-strategic-design]] -- bounded contexts that become service boundaries
- [[api-design]] -- designing inter-service API contracts
- [[kubernetes-expert]] -- container orchestration for microservices deployment
- [[cicd-architect]] -- independent deployment pipelines per service
- [[event-driven-architecture]] -- async messaging and event infrastructure
- [[component-boundary-identifier]] -- finding the extraction seams before splitting a monolith

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
