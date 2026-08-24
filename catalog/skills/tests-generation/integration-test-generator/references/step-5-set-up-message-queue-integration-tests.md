### Step 5: Set Up Message Queue Integration Tests

**Python (Kafka with testcontainers):**
```python
import pytest
import json
from testcontainers.kafka import KafkaContainer
from kafka import KafkaProducer, KafkaConsumer


@pytest.fixture(scope="module")
def kafka():
    with KafkaContainer("confluentinc/cp-kafka:7.5.0") as kc:
        yield kc


class TestOrderEventMessaging:
    """Integration tests for Kafka message production and consumption."""

    def test_order_created_event_published(self, kafka):
        producer = KafkaProducer(
            bootstrap_servers=kafka.get_bootstrap_server(),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        consumer = KafkaConsumer(
            "order-events",
            bootstrap_servers=kafka.get_bootstrap_server(),
            auto_offset_reset="earliest",
            consumer_timeout_ms=10000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

        event = {
            "type": "order.created",
            "order_id": "ord_123",
            "customer_email": "alice@example.com",
            "total": 99.99,
        }
        producer.send("order-events", event)
        producer.flush()

        messages = list(consumer)
        assert len(messages) >= 1
        assert messages[0].value["type"] == "order.created"
        assert messages[0].value["order_id"] == "ord_123"

        producer.close()
        consumer.close()
```
