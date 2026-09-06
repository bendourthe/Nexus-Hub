### Step 4: Implement Kafka Producer and Consumer

**Python Producer (confluent-kafka)**:

```python
import json
import uuid
from datetime import datetime, timezone
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

def create_producer(bootstrap_servers: str) -> Producer:
    config = {
        "bootstrap.servers": bootstrap_servers,
        "acks": "all",                    # Wait for all replicas
        "enable.idempotence": True,       # Exactly-once producer semantics
        "max.in.flight.requests.per.connection": 5,
        "retries": 2147483647,            # Infinite retries with idempotence
        "linger.ms": 5,                   # Batch for 5ms for throughput
        "compression.type": "lz4",        # Compress batches
    }
    return Producer(config)

def publish_order_created(producer: Producer, order: dict):
    """Publish an OrderCreated event with CloudEvents envelope."""
    event = {
        "specversion": "1.0",
        "id": str(uuid.uuid4()),
        "source": "urn:example:order-service",
        "type": "com.example.order.created",
        "datacontenttype": "application/json",
        "time": datetime.now(timezone.utc).isoformat(),
        "subject": order["id"],
        "data": order,
    }

    producer.produce(
        topic="orders",
        key=order["id"].encode("utf-8"),    # Partition by order ID
        value=json.dumps(event).encode("utf-8"),
        headers={
            "ce-type": "com.example.order.created",
            "ce-source": "urn:example:order-service",
        },
        callback=delivery_callback,
    )
    producer.flush()

def delivery_callback(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")
```

**Python Consumer with Idempotency**:

```python
import json
from confluent_kafka import Consumer, KafkaError
from typing import Callable

def create_consumer(
    bootstrap_servers: str,
    group_id: str,
    topics: list[str],
) -> Consumer:
    config = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,       # Manual commit for reliability
        "max.poll.interval.ms": 300000,    # 5 min processing budget
        "session.timeout.ms": 45000,
    }
    consumer = Consumer(config)
    consumer.subscribe(topics)
    return consumer

class IdempotentConsumer:
    """Consumer that tracks processed event IDs to ensure exactly-once handling."""

    def __init__(self, consumer: Consumer, db, handler: Callable):
        self.consumer = consumer
        self.db = db
        self.handler = handler

    async def run(self):
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise Exception(f"Consumer error: {msg.error()}")

                event = json.loads(msg.value().decode("utf-8"))
                event_id = event["id"]

                # Idempotency check: skip if already processed
                if await self.db.execute(
                    "SELECT 1 FROM processed_events WHERE event_id = :id",
                    {"id": event_id},
                ):
                    self.consumer.commit(msg)
                    continue

                # Process event within a transaction
                async with self.db.transaction():
                    await self.handler(event)
                    await self.db.execute(
                        "INSERT INTO processed_events (event_id, processed_at) "
                        "VALUES (:id, NOW())",
                        {"id": event_id},
                    )

                self.consumer.commit(msg)

        finally:
            self.consumer.close()
```
