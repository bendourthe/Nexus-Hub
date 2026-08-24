### Step 5: Implement Event Sourcing

**Event Store Schema (PostgreSQL)**:

```sql
-- Event store table
CREATE TABLE event_store (
    id              BIGSERIAL PRIMARY KEY,
    aggregate_type  TEXT NOT NULL,
    aggregate_id    UUID NOT NULL,
    event_type      TEXT NOT NULL,
    event_version   INTEGER NOT NULL,
    data            JSONB NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Optimistic concurrency: no two events for the same aggregate
    -- can have the same version
    UNIQUE (aggregate_id, event_version)
);

CREATE INDEX idx_event_store_aggregate
    ON event_store (aggregate_type, aggregate_id, event_version);

CREATE INDEX idx_event_store_type
    ON event_store (event_type, created_at);

-- Processed events table (for idempotent consumers)
CREATE TABLE processed_events (
    event_id        TEXT PRIMARY KEY,
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Snapshots table (for performance optimization)
CREATE TABLE snapshots (
    aggregate_type  TEXT NOT NULL,
    aggregate_id    UUID NOT NULL,
    version         INTEGER NOT NULL,
    state           JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (aggregate_type, aggregate_id)
);
```

**Event Store Implementation (Python)**:

```python
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import list, Optional

@dataclass
class DomainEvent:
    event_type: str
    aggregate_id: str
    data: dict
    version: int = 0
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

class EventStore:
    def __init__(self, db):
        self.db = db

    async def append(
        self,
        aggregate_type: str,
        aggregate_id: str,
        events: list[DomainEvent],
        expected_version: int,
    ):
        """Append events with optimistic concurrency control."""
        async with self.db.transaction():
            # Check current version
            row = await self.db.fetchone(
                "SELECT COALESCE(MAX(event_version), 0) AS version "
                "FROM event_store WHERE aggregate_id = :id",
                {"id": aggregate_id},
            )
            current_version = row["version"]

            if current_version != expected_version:
                raise ConcurrencyError(
                    f"Expected version {expected_version}, "
                    f"but current version is {current_version}"
                )

            for i, event in enumerate(events):
                version = expected_version + i + 1
                await self.db.execute(
                    """INSERT INTO event_store
                       (aggregate_type, aggregate_id, event_type,
                        event_version, data, metadata)
                       VALUES (:agg_type, :agg_id, :evt_type,
                               :version, :data, :metadata)""",
                    {
                        "agg_type": aggregate_type,
                        "agg_id": aggregate_id,
                        "evt_type": event.event_type,
                        "version": version,
                        "data": json.dumps(event.data),
                        "metadata": json.dumps(event.metadata),
                    },
                )

    async def load(
        self,
        aggregate_id: str,
        after_version: int = 0,
    ) -> list[DomainEvent]:
        """Load events for an aggregate, optionally after a snapshot version."""
        rows = await self.db.fetchall(
            """SELECT event_type, aggregate_id, event_version, data, metadata, created_at
               FROM event_store
               WHERE aggregate_id = :id AND event_version > :after
               ORDER BY event_version""",
            {"id": aggregate_id, "after": after_version},
        )
        return [
            DomainEvent(
                event_type=r["event_type"],
                aggregate_id=r["aggregate_id"],
                data=json.loads(r["data"]),
                version=r["event_version"],
                timestamp=r["created_at"],
                metadata=json.loads(r["metadata"]),
            )
            for r in rows
        ]

class ConcurrencyError(Exception):
    pass
```

**Aggregate Reconstruction**:

```python
class OrderAggregate:
    """Reconstruct order state by replaying events."""

    def __init__(self):
        self.id: Optional[str] = None
        self.status: str = "unknown"
        self.items: list = []
        self.total: float = 0.0
        self.version: int = 0

    def apply(self, event: DomainEvent):
        handler = getattr(self, f"_on_{event.event_type}", None)
        if handler:
            handler(event.data)
        self.version = event.version

    def _on_order_created(self, data):
        self.id = data["orderId"]
        self.status = "pending"
        self.items = data["items"]
        self.total = data["total"]

    def _on_order_confirmed(self, data):
        self.status = "confirmed"

    def _on_order_cancelled(self, data):
        self.status = "cancelled"

    @classmethod
    async def load(cls, event_store: EventStore, aggregate_id: str) -> "OrderAggregate":
        order = cls()
        events = await event_store.load(aggregate_id)
        for event in events:
            order.apply(event)
        return order
```
