## Common Patterns

### Pattern 1: CQRS with Separate Read Model

```python
# Write side: event-sourced aggregate
async def place_order(command, event_store):
    order = await OrderAggregate.load(event_store, command.order_id)
    events = order.place(command)
    await event_store.append("order", command.order_id, events, order.version)

# Read side: projector updates a denormalized read model
async def on_order_created(event, read_db):
    await read_db.execute(
        """INSERT INTO order_view
           (id, customer_name, total, status, item_count, created_at)
           VALUES (:id, :name, :total, 'pending', :count, :ts)""",
        {
            "id": event.data["orderId"],
            "name": event.data["customerName"],
            "total": event.data["total"],
            "count": len(event.data["items"]),
            "ts": event.timestamp,
        },
    )
```

### Pattern 2: Dead Letter Queue Handler

```python
async def process_dlq(consumer, alert_service):
    """Process dead letter queue: log, alert, and store for manual review."""
    for message in consumer:
        await alert_service.notify(
            channel="ops",
            message=f"DLQ message: {message.topic} | "
                    f"Key: {message.key} | "
                    f"Error: {message.headers.get('x-error')}",
        )
        await store_for_review(message)
        consumer.commit(message)
```

### Pattern 3: Event Replay for Read Model Rebuild

```python
async def rebuild_read_model(event_store, projector, aggregate_type: str):
    """Replay all events to rebuild a read model from scratch."""
    await projector.truncate()  # Clear the read model

    offset = 0
    batch_size = 1000
    while True:
        events = await event_store.load_all(
            aggregate_type=aggregate_type,
            after_id=offset,
            limit=batch_size,
        )
        if not events:
            break
        for event in events:
            await projector.project(event)
            offset = event.id
    print(f"Rebuilt read model from {offset} events")
```
