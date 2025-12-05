---
template_id: SKILL
template_name: Extract-Microservice - Generic
version: 1.0.0
last_updated: 2025-12-03
language: Generic
category: skills
phase: extract-microservice
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tags:

  - skills
  - generic
---
# extract-microservice

---
category: migration-refactoring
priority: MEDIUM
languages: [python, javascript, typescript, java, csharp, go]
requires_user_input: true
estimated_duration: 4-16 hours
---

## Overview

Extract functionality from a monolithic application into an independent microservice, handling API boundaries, data migration, and deployment strategies.

## When to Use This Skill

- Monolithic application growing too large
- Team scaling requires independent deployments
- Different scaling requirements for different features
- Technology stack needs to vary by component
- Organizational boundaries align with service boundaries
- Performance isolation needed for specific features

## Prerequisites

- Understanding of domain-driven design
- Knowledge of API design (REST/GraphQL/gRPC)
- Database migration experience
- Container/orchestration platform access
- Monitoring and logging infrastructure
- Service mesh or API gateway (recommended)

## Step-by-Step Instructions

### Phase 1: Domain Analysis

#### Step 1: Identify Service Boundaries

**Domain-driven design analysis:**

```markdown
## Domain Analysis for [Feature] Microservice

### Current Monolith Structure
```
monolith/
├── users/          # User management
├── orders/         # Order processing
├── inventory/      # Stock management
├── payments/       # Payment processing
├── notifications/  # Email/SMS notifications
└── shared/         # Shared utilities
```

### Proposed Extraction: Order Service

**Bounded Context:**
- Order creation and management
- Order status tracking
- Order history
- Order validation

**Dependencies:**
- Users service (authentication)
- Inventory service (stock checking)
- Payments service (payment processing)
- Notifications service (order updates)

**Data Ownership:**
- Orders table (primary)
- Order items table
- Order status history
- Order metadata

### Decision Criteria

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Business capability alignment | 5 | Clear business domain |
| Team autonomy | 4 | Dedicated team possible |
| Data separation | 3 | Some shared data concerns |
| Technology fit | 4 | Could benefit from different stack |
| Scalability needs | 5 | High load, needs independent scaling |
| Deployment independence | 4 | Frequent updates needed |

**Recommendation**: Proceed with extraction
```

#### Step 2: Map Dependencies

```python
# Create dependency graph
"""
Current Dependencies Analysis

OrderService currently depends on:

Direct Dependencies:
1. UserService.get_user(user_id) → Authentication
2. UserService.get_shipping_address(user_id) → Address info
3. InventoryService.check_stock(product_id) → Availability
4. InventoryService.reserve_items(items) → Stock reservation
5. PaymentService.charge(payment_info) → Payment processing
6. NotificationService.send_email(template, data) → Customer notifications

Database Dependencies:
- users table → customer information
- products table → product details
- inventory table → stock levels
- payments table → payment records

Shared Libraries:
- validation_utils → Input validation
- logging_utils → Centralized logging
- auth_middleware → JWT validation

Reverse Dependencies (who calls OrderService):
- ShippingService.create_shipment(order_id)
- AnalyticsService.track_order(order_data)
- AdminDashboard.get_order_details(order_id)
"""

# Document API contracts needed
class ServiceContracts:
    """
    API contracts for microservice boundaries.
    """

    # What Order Service needs from other services
    DEPENDENCIES = {
        'user_service': {
            'get_user': {
                'input': {'user_id': 'int'},
                'output': {'id': 'int', 'email': 'str', 'name': 'str'},
                'fallback': 'Return cached data or fail gracefully'
            },
            'get_address': {
                'input': {'user_id': 'int', 'address_id': 'int'},
                'output': {'street': 'str', 'city': 'str', 'zip': 'str'},
                'fallback': 'Return default or require re-entry'
            }
        },
        'inventory_service': {
            'check_availability': {
                'input': {'product_id': 'int', 'quantity': 'int'},
                'output': {'available': 'bool', 'stock_level': 'int'},
                'fallback': 'Assume unavailable, fail order'
            },
            'reserve_items': {
                'input': {'items': 'list[{product_id, quantity}]'},
                'output': {'reservation_id': 'str', 'expires_at': 'datetime'},
                'fallback': 'Retry with exponential backoff'
            }
        }
    }

    # What Order Service exposes to other services
    PROVIDES = {
        'create_order': {
            'input': {'user_id': 'int', 'items': 'list', 'payment_method': 'str'},
            'output': {'order_id': 'int', 'status': 'str', 'total': 'float'},
            'sla': '500ms p99'
        },
        'get_order': {
            'input': {'order_id': 'int'},
            'output': {'order': 'OrderDTO'},
            'sla': '100ms p99'
        },
        'update_order_status': {
            'input': {'order_id': 'int', 'status': 'str'},
            'output': {'success': 'bool'},
            'sla': '200ms p99'
        }
    }
```

### Phase 2: API Design

#### Step 3: Design Service API

**REST API example:**

```python
# order_service/api/v1/endpoints.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Order Service", version="1.0.0")

# Data models
class OrderItem(BaseModel):
    product_id: int
    quantity: int
    price: float

class CreateOrderRequest(BaseModel):
    user_id: int
    items: List[OrderItem]
    shipping_address_id: int
    payment_method_id: int
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    order_id: int
    user_id: int
    status: str
    total: float
    created_at: datetime
    items: List[OrderItem]

class OrderStatus(BaseModel):
    order_id: int
    status: str
    updated_at: datetime

# Endpoints
@app.post("/api/v1/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    request: CreateOrderRequest,
    order_service: OrderService = Depends(get_order_service)
):
    """
    Create a new order.

    Workflow:
    1. Validate user and address
    2. Check inventory availability
    3. Create order record
    4. Reserve inventory
    5. Process payment
    6. Send confirmation
    """
    try:
        order = await order_service.create_order(request)
        return order
    except InventoryUnavailableError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PaymentFailedError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service)
):
    """Get order details by ID."""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/v1/orders", response_model=List[OrderResponse])
async def list_orders(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    order_service: OrderService = Depends(get_order_service)
):
    """List orders with optional filtering."""
    orders = await order_service.list_orders(
        user_id=user_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return orders

@app.patch("/api/v1/orders/{order_id}/status", response_model=OrderStatus)
async def update_order_status(
    order_id: int,
    status: str,
    order_service: OrderService = Depends(get_order_service)
):
    """Update order status."""
    try:
        updated = await order_service.update_status(order_id, status)
        return updated
    except InvalidStatusTransition as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/v1/orders/{order_id}", status_code=204)
async def cancel_order(
    order_id: int,
    reason: str,
    order_service: OrderService = Depends(get_order_service)
):
    """Cancel an order."""
    await order_service.cancel_order(order_id, reason)
```

**gRPC API example:**

```protobuf
// order_service.proto
syntax = "proto3";

package order.v1;

service OrderService {
  rpc CreateOrder(CreateOrderRequest) returns (OrderResponse);
  rpc GetOrder(GetOrderRequest) returns (OrderResponse);
  rpc ListOrders(ListOrdersRequest) returns (ListOrdersResponse);
  rpc UpdateOrderStatus(UpdateOrderStatusRequest) returns (OrderResponse);
  rpc CancelOrder(CancelOrderRequest) returns (CancelOrderResponse);
}

message OrderItem {
  int32 product_id = 1;
  int32 quantity = 2;
  double price = 3;
}

message CreateOrderRequest {
  int32 user_id = 1;
  repeated OrderItem items = 2;
  int32 shipping_address_id = 3;
  int32 payment_method_id = 4;
  string notes = 5;
}

message OrderResponse {
  int32 order_id = 1;
  int32 user_id = 2;
  string status = 3;
  double total = 4;
  int64 created_at = 5;
  repeated OrderItem items = 6;
}

message GetOrderRequest {
  int32 order_id = 1;
}

message ListOrdersRequest {
  optional int32 user_id = 1;
  optional string status = 2;
  int32 skip = 3;
  int32 limit = 4;
}

message ListOrdersResponse {
  repeated OrderResponse orders = 1;
  int32 total_count = 2;
}

message UpdateOrderStatusRequest {
  int32 order_id = 1;
  string status = 2;
}

message CancelOrderRequest {
  int32 order_id = 1;
  string reason = 2;
}

message CancelOrderResponse {
  bool success = 1;
}
```

#### Step 4: Design Service Communication

```python
# service_clients/user_service_client.py
import httpx
from typing import Optional
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential

class UserServiceClient:
    """Client for User Service API with resilience patterns."""

    def __init__(self, base_url: str, timeout: int = 5):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)
        self.cache = {}

    @circuit(failure_threshold=5, recovery_timeout=60)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def get_user(self, user_id: int) -> Optional[dict]:
        """
        Get user details with circuit breaker and retry logic.

        Falls back to cache if service is unavailable.
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/users/{user_id}"
            )
            response.raise_for_status()
            user_data = response.json()

            # Update cache
            self.cache[user_id] = user_data
            return user_data

        except Exception as e:
            # Fallback to cache
            if user_id in self.cache:
                return self.cache[user_id]
            raise

    async def get_shipping_address(
        self,
        user_id: int,
        address_id: int
    ) -> Optional[dict]:
        """Get shipping address for user."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/users/{user_id}/addresses/{address_id}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

# service_clients/inventory_service_client.py
class InventoryServiceClient:
    """Client for Inventory Service with saga pattern support."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def check_availability(
        self,
        product_id: int,
        quantity: int
    ) -> dict:
        """Check if product is available in requested quantity."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/inventory/check",
            json={'product_id': product_id, 'quantity': quantity}
        )
        response.raise_for_status()
        return response.json()

    async def reserve_items(self, items: list) -> dict:
        """
        Reserve items for order (saga transaction).

        Returns reservation ID that can be committed or rolled back.
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/inventory/reserve",
            json={'items': items}
        )
        response.raise_for_status()
        return response.json()

    async def commit_reservation(self, reservation_id: str) -> None:
        """Commit inventory reservation (complete saga)."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/inventory/reservations/{reservation_id}/commit"
        )
        response.raise_for_status()

    async def rollback_reservation(self, reservation_id: str) -> None:
        """Rollback inventory reservation (compensating transaction)."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/inventory/reservations/{reservation_id}/rollback"
        )
        response.raise_for_status()

# Event-driven communication
# order_service/events/publisher.py
import json
from typing import Dict, Any
import aio_pika

class EventPublisher:
    """Publish domain events to message queue."""

    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self.connection = None
        self.channel = None

    async def connect(self):
        """Establish connection to message broker."""
        self.connection = await aio_pika.connect_robust(self.amqp_url)
        self.channel = await self.connection.channel()

    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Publish domain event."""
        event = {
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }

        exchange = await self.channel.declare_exchange(
            'order_events',
            aio_pika.ExchangeType.TOPIC
        )

        message = aio_pika.Message(
            body=json.dumps(event).encode(),
            content_type='application/json'
        )

        await exchange.publish(
            message,
            routing_key=f"order.{event_type}"
        )

# Usage in service
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        event_publisher: EventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher

    async def create_order(self, request: CreateOrderRequest) -> OrderResponse:
        """Create order and publish event."""
        order = await self.repository.create(request)

        # Publish domain event
        await self.event_publisher.publish_event(
            'order.created',
            {
                'order_id': order.id,
                'user_id': order.user_id,
                'total': order.total,
                'items': [item.to_dict() for item in order.items]
            }
        )

        return order
```

### Phase 3: Data Migration

#### Step 5: Plan Data Migration Strategy

```sql
-- Current monolith database
-- users, products, orders, order_items, inventory, payments all in one DB

-- Migration Strategy: Strangler Fig Pattern

-- Phase 1: Dual-write (monolith and microservice)
-- - Monolith writes to both databases
-- - Microservice reads from its own database
-- - Monolith remains source of truth

-- Phase 2: Data sync and verification
-- - Background job syncs historical data
-- - Compare data consistency
-- - Fix discrepancies

-- Phase 3: Cut over
-- - Microservice becomes source of truth
-- - Monolith reads from microservice API
-- - Stop dual-writes

-- New microservice database schema
CREATE DATABASE order_service;

USE order_service;

-- Orders table (owned by order service)
CREATE TABLE orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    shipping_address_id BIGINT,
    payment_method_id BIGINT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Order items (owned by order service)
CREATE TABLE order_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    product_name VARCHAR(255) NOT NULL,  -- Denormalized for performance
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,

    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
);

-- Order status history (for audit trail)
CREATE TABLE order_status_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    reason TEXT,
    changed_by BIGINT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id)
);

-- Cached user data (eventual consistency)
CREATE TABLE user_cache (
    user_id BIGINT PRIMARY KEY,
    email VARCHAR(255),
    name VARCHAR(255),
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_cached_at (cached_at)
);
```

**Data migration script:**

```python
# migrations/migrate_orders.py
import asyncio
import asyncpg
from datetime import datetime

class OrderDataMigration:
    """Migrate order data from monolith to microservice."""

    def __init__(self, source_dsn: str, target_dsn: str):
        self.source_dsn = source_dsn
        self.target_dsn = target_dsn

    async def run_migration(self, batch_size: int = 1000):
        """
        Run migration in batches.

        Strategy:
        1. Migrate historical data first
        2. Enable dual-write
        3. Sync remaining data
        4. Verify consistency
        """
        source_conn = await asyncpg.connect(self.source_dsn)
        target_conn = await asyncpg.connect(self.target_dsn)

        try:
            # Get total count
            total = await source_conn.fetchval(
                "SELECT COUNT(*) FROM orders"
            )
            print(f"Migrating {total} orders...")

            # Migrate in batches
            offset = 0
            migrated = 0

            while offset < total:
                # Fetch batch from source
                orders = await source_conn.fetch(
                    """
                    SELECT id, user_id, status, total_amount,
                           shipping_address_id, payment_method_id,
                           notes, created_at, updated_at
                    FROM orders
                    ORDER BY id
                    LIMIT $1 OFFSET $2
                    """,
                    batch_size,
                    offset
                )

                # Insert into target
                for order in orders:
                    await self._migrate_order(source_conn, target_conn, order)
                    migrated += 1

                print(f"Migrated {migrated}/{total} orders...")
                offset += batch_size

            print("Migration complete!")

        finally:
            await source_conn.close()
            await target_conn.close()

    async def _migrate_order(
        self,
        source_conn,
        target_conn,
        order
    ):
        """Migrate single order with items."""
        # Insert order
        await target_conn.execute(
            """
            INSERT INTO orders (
                id, user_id, status, total_amount,
                shipping_address_id, payment_method_id,
                notes, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (id) DO NOTHING
            """,
            order['id'],
            order['user_id'],
            order['status'],
            order['total_amount'],
            order['shipping_address_id'],
            order['payment_method_id'],
            order['notes'],
            order['created_at'],
            order['updated_at']
        )

        # Fetch and migrate order items
        items = await source_conn.fetch(
            """
            SELECT oi.id, oi.order_id, oi.product_id,
                   p.name as product_name, oi.quantity,
                   oi.unit_price, oi.total_price
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = $1
            """,
            order['id']
        )

        for item in items:
            await target_conn.execute(
                """
                INSERT INTO order_items (
                    id, order_id, product_id, product_name,
                    quantity, unit_price, total_price
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO NOTHING
                """,
                item['id'],
                item['order_id'],
                item['product_id'],
                item['product_name'],
                item['quantity'],
                item['unit_price'],
                item['total_price']
            )

    async def verify_migration(self):
        """Verify data consistency between source and target."""
        source_conn = await asyncpg.connect(self.source_dsn)
        target_conn = await asyncpg.connect(self.target_dsn)

        try:
            # Compare order counts
            source_count = await source_conn.fetchval(
                "SELECT COUNT(*) FROM orders"
            )
            target_count = await target_conn.fetchval(
                "SELECT COUNT(*) FROM orders"
            )

            print(f"Source orders: {source_count}")
            print(f"Target orders: {target_count}")

            if source_count != target_count:
                print("WARNING: Order counts don't match!")
                return False

            # Sample verification
            sample_ids = await source_conn.fetch(
                "SELECT id FROM orders ORDER BY RAND() LIMIT 100"
            )

            mismatches = 0
            for row in sample_ids:
                order_id = row['id']

                source_order = await source_conn.fetchrow(
                    "SELECT * FROM orders WHERE id = $1", order_id
                )
                target_order = await target_conn.fetchrow(
                    "SELECT * FROM orders WHERE id = $1", order_id
                )

                if not self._orders_match(source_order, target_order):
                    print(f"Mismatch for order {order_id}")
                    mismatches += 1

            if mismatches == 0:
                print("✓ Sample verification passed!")
                return True
            else:
                print(f"✗ Found {mismatches} mismatches in sample")
                return False

        finally:
            await source_conn.close()
            await target_conn.close()

    def _orders_match(self, source, target) -> bool:
        """Compare two order records."""
        return (
            source['user_id'] == target['user_id'] and
            source['status'] == target['status'] and
            abs(source['total_amount'] - target['total_amount']) < 0.01
        )

# Run migration
if __name__ == '__main__':
    migration = OrderDataMigration(
        source_dsn="postgresql://monolith_db",
        target_dsn="postgresql://order_service_db"
    )

    asyncio.run(migration.run_migration())
    asyncio.run(migration.verify_migration())
```

### Phase 4: Deployment

#### Step 6: Containerize Microservice

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY order_service/ ./order_service/

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "order_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  order-service:
    build: .
    ports:

      - "8000:8000"
    environment:

      - DATABASE_URL=postgresql://order_db:5432/orders
      - USER_SERVICE_URL=http://user-service:8001
      - INVENTORY_SERVICE_URL=http://inventory-service:8002
      - PAYMENT_SERVICE_URL=http://payment-service:8003
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://rabbitmq:5672
    depends_on:

      - order-db
      - redis
      - rabbitmq
    restart: unless-stopped

  order-db:
    image: postgres:15
    environment:

      - POSTGRES_DB=orders
      - POSTGRES_USER=order_user
      - POSTGRES_PASSWORD=order_pass
    volumes:

      - order-data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:

      - "15672:15672"
    restart: unless-stopped

volumes:
  order-data:
```

#### Step 7: Deploy to Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  labels:
    app: order-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      containers:

      - name: order-service
        image: myregistry/order-service:1.0.0
        ports:

        - containerPort: 8000
        env:

        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: order-service-secrets
              key: database-url

        - name: USER_SERVICE_URL
          value: "http://user-service:8001"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  selector:
    app: order-service
  ports:

  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: order-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service
  minReplicas: 3
  maxReplicas: 10
  metrics:

  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Phase 5: Monitoring and Observability

#### Step 8: Add Observability

```python
# order_service/observability.py
from prometheus_client import Counter, Histogram, Gauge
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
import logging

# Prometheus metrics
order_created_counter = Counter(
    'order_created_total',
    'Total number of orders created'
)

order_creation_duration = Histogram(
    'order_creation_duration_seconds',
    'Time spent creating orders'
)

active_orders_gauge = Gauge(
    'active_orders',
    'Number of currently active orders'
)

service_dependency_latency = Histogram(
    'service_dependency_latency_seconds',
    'Latency of service dependencies',
    ['service_name', 'endpoint']
)

# Distributed tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Structured logging
import structlog

logger = structlog.get_logger()

# Instrument FastAPI app
def setup_observability(app):
    """Setup observability for FastAPI app."""
    FastAPIInstrumentor.instrument_app(app)

    @app.middleware("http")
    async def log_requests(request, call_next):
        """Log all requests with structured logging."""
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client=request.client.host
        )

        response = await call_next(request)

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code
        )

        return response

# Usage in service
class OrderService:
    async def create_order(self, request: CreateOrderRequest):
        """Create order with observability."""
        with tracer.start_as_current_span("create_order") as span:
            span.set_attribute("user_id", request.user_id)
            span.set_attribute("item_count", len(request.items))

            with order_creation_duration.time():
                try:
                    # Create order
                    order = await self._create_order_record(request)

                    # Update metrics
                    order_created_counter.inc()
                    active_orders_gauge.inc()

                    logger.info(
                        "order_created",
                        order_id=order.id,
                        user_id=request.user_id,
                        total=order.total
                    )

                    span.set_attribute("order_id", order.id)
                    return order

                except Exception as e:
                    logger.error(
                        "order_creation_failed",
                        error=str(e),
                        user_id=request.user_id
                    )
                    span.record_exception(e)
                    raise
```

## Expected Outcomes

After completing this extraction:

1. **Independent microservice**
   - Runs separately from monolith
   - Own database and data ownership
   - Independent deployment and scaling

2. **Clean API boundaries**
   - Well-defined REST/gRPC APIs
   - Event-driven communication
   - Resilience patterns implemented

3. **Data consistency**
   - Data migration completed
   - Eventual consistency handled
   - No data loss

4. **Operational readiness**
   - Monitoring and logging
   - Health checks and metrics
   - Deployment automation

## Success Criteria

- [ ] Service boundaries clearly defined
- [ ] API contracts documented
- [ ] Data migration completed successfully
- [ ] Service deployed and running
- [ ] Inter-service communication working
- [ ] Monitoring and alerting configured
- [ ] Load testing completed
- [ ] Rollback plan documented
- [ ] Zero data loss during migration
- [ ] Performance SLAs met
- [ ] Team trained on new service

## Common Pitfalls

1. **Data consistency issues**
   - Plan for eventual consistency
   - Implement saga patterns for transactions

2. **Tight coupling**
   - Avoid shared databases
   - Use events instead of direct calls

3. **Network failures**
   - Implement retries and circuit breakers
   - Design for failure

4. **Incomplete extraction**
   - Ensure all dependencies identified
   - Don't leave shared code

## Related Skills

- **refactor-for-testability**: Improve code testability
- **dependency-upgrade**: Upgrade dependencies
- **setup-python-project**: Initialize new projects
- **add-api-endpoint**: Add new endpoints
- **database-migration**: Migrate databases

## Additional Resources

### Books
- "Building Microservices" by Sam Newman
- "Microservices Patterns" by Chris Richardson
- "Domain-Driven Design" by Eric Evans

### Patterns
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)

### Tools
- Docker/Kubernetes for containerization
- Istio/Linkerd for service mesh
- Prometheus/Grafana for monitoring
- Jaeger/Zipkin for tracing

---

**Note**: Microservice extraction is a complex process. Start small, validate frequently, and be prepared to iterate.
