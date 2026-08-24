### Step 3: Design Event Schemas

**CloudEvents Format (JSON)**:

```json
{
  "specversion": "1.0",
  "id": "evt-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "source": "urn:example:order-service",
  "type": "com.example.order.created",
  "datacontenttype": "application/json",
  "time": "2026-03-03T10:30:00Z",
  "subject": "order-12345",
  "data": {
    "orderId": "order-12345",
    "customerId": "cust-67890",
    "items": [
      {
        "productId": "prod-111",
        "quantity": 2,
        "unitPrice": 29.99
      }
    ],
    "total": 59.98,
    "currency": "USD"
  }
}
```

**Event Naming Convention**:

```
Format:  <domain>.<aggregate>.<past-tense-verb>
Examples:
  com.example.order.created
  com.example.order.cancelled
  com.example.payment.processed
  com.example.inventory.reserved
  com.example.shipment.dispatched
  com.example.user.email_verified

Rules:
  1. Always past tense (something that HAS happened)
  2. Domain-qualified to avoid collisions
  3. Specific enough to convey meaning without reading the payload
```

**Avro Schema (for schema registry)**:

```json
{
  "type": "record",
  "name": "OrderCreated",
  "namespace": "com.example.order.events",
  "fields": [
    {"name": "orderId", "type": "string"},
    {"name": "customerId", "type": "string"},
    {"name": "items", "type": {
      "type": "array",
      "items": {
        "type": "record",
        "name": "OrderItem",
        "fields": [
          {"name": "productId", "type": "string"},
          {"name": "quantity", "type": "int"},
          {"name": "unitPrice", "type": {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}}
        ]
      }
    }},
    {"name": "total", "type": {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}},
    {"name": "currency", "type": "string", "default": "USD"},
    {"name": "occurredAt", "type": {"type": "long", "logicalType": "timestamp-millis"}}
  ]
}
```
