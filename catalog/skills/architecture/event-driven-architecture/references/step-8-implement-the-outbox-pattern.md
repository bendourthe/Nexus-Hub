### Step 8: Implement the Outbox Pattern

```python
# The outbox pattern ensures atomicity between database writes and event publishing.
# Events are written to an outbox table in the same transaction as the business data.
# A separate process reads the outbox and publishes to the message broker.

async def create_order_with_outbox(db, order_data: dict):
    """Atomically persist order and queue event for publishing."""
    async with db.transaction():
        # 1. Write business data
        order = await db.execute(
            "INSERT INTO orders (customer_id, total, status) "
            "VALUES (:cid, :total, 'pending') RETURNING *",
            {"cid": order_data["customer_id"], "total": order_data["total"]},
        )

        # 2. Write event to outbox (same transaction)
        await db.execute(
            """INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
               VALUES ('order', :id, 'order.created', :payload)""",
            {
                "id": order["id"],
                "payload": json.dumps({
                    "orderId": order["id"],
                    "customerId": order["customer_id"],
                    "total": order["total"],
                }),
            },
        )

    return order

# Outbox publisher (runs as a background process)
async def outbox_publisher(db, producer, poll_interval: float = 1.0):
    """Poll outbox table and publish to Kafka."""
    while True:
        rows = await db.fetchall(
            "SELECT * FROM outbox WHERE published_at IS NULL "
            "ORDER BY created_at LIMIT 100",
        )
        for row in rows:
            producer.produce(
                topic=row["aggregate_type"] + "s",
                key=row["aggregate_id"].encode(),
                value=row["payload"].encode(),
            )
            await db.execute(
                "UPDATE outbox SET published_at = NOW() WHERE id = :id",
                {"id": row["id"]},
            )
        producer.flush()
        await asyncio.sleep(poll_interval)
```

**RabbitMQ Setup (Docker Compose + Python)**:

```yaml
# docker-compose.yaml
services:
  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    ports:
      - "5672:5672"     # AMQP
      - "15672:15672"   # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: secret
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  rabbitmq-data:
```

```python
# RabbitMQ publisher with exchange and routing
import pika
import json

def setup_rabbitmq(host: str = "localhost"):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, credentials=pika.PlainCredentials("admin", "secret"))
    )
    channel = connection.channel()

    # Topic exchange for flexible routing
    channel.exchange_declare(exchange="events", exchange_type="topic", durable=True)

    # Dead letter exchange
    channel.exchange_declare(exchange="events.dlx", exchange_type="topic", durable=True)

    # Queues with dead letter routing
    channel.queue_declare(
        queue="order-processing",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "events.dlx",
            "x-dead-letter-routing-key": "order.failed",
            "x-message-ttl": 300000,  # 5 min TTL
        },
    )
    channel.queue_bind(queue="order-processing", exchange="events", routing_key="order.*")

    # Dead letter queue
    channel.queue_declare(queue="order-failed-dlq", durable=True)
    channel.queue_bind(queue="order-failed-dlq", exchange="events.dlx", routing_key="order.failed")

    return connection, channel

def publish_event(channel, routing_key: str, event: dict):
    channel.basic_publish(
        exchange="events",
        routing_key=routing_key,
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode=2,         # Persistent
            content_type="application/json",
            message_id=event.get("id", ""),
        ),
    )
```
