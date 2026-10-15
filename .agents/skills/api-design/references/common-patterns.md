## Common Patterns

### Pattern 1: Idempotency Key for POST

Prevent duplicate resource creation due to retries:

```
POST /v1/orders HTTP/1.1
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{"customerId": "abc", "lines": [...]}
```

```python
# Server-side idempotency check
async def create_order(request):
    key = request.headers.get("Idempotency-Key")
    if key:
        cached = await redis.get(f"idempotency:{key}")
        if cached:
            return json.loads(cached)  # Return same response

    order = await order_service.create(request.json)
    response = serialize(order)

    if key:
        await redis.set(f"idempotency:{key}", json.dumps(response),
                        ex=86400)  # 24-hour TTL
    return response, 201
```

### Pattern 2: HATEOAS Links for Discoverability

```json
{
  "id": "order-123",
  "status": "placed",
  "total": {"amount": 4999, "currency": "USD"},
  "_links": {
    "self": {"href": "/v1/orders/order-123"},
    "cancel": {"href": "/v1/orders/order-123/cancel", "method": "POST"},
    "customer": {"href": "/v1/customers/cust-456"},
    "lines": {"href": "/v1/orders/order-123/lines"}
  }
}
```

### Pattern 3: Bulk Operations

```
POST /v1/orders/bulk HTTP/1.1
Content-Type: application/json

{
  "operations": [
    {"method": "POST", "body": {"customerId": "a", "lines": [...]}},
    {"method": "POST", "body": {"customerId": "b", "lines": [...]}}
  ]
}

HTTP/1.1 207 Multi-Status
{
  "results": [
    {"status": 201, "body": {"id": "order-1", ...}},
    {"status": 422, "body": {"type": "/errors/validation-error", ...}}
  ]
}
```
