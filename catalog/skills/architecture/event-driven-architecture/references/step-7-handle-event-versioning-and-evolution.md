### Step 7: Handle Event Versioning and Evolution

**Versioning Strategies**:

```python
# Strategy 1: Upcasting (transform old events to new format on read)
class EventUpcaster:
    """Transform events from older versions to the current schema."""

    upcasters = {}

    @classmethod
    def register(cls, event_type: str, from_version: int, to_version: int):
        def decorator(fn):
            cls.upcasters[(event_type, from_version, to_version)] = fn
            return fn
        return decorator

    @classmethod
    def upcast(cls, event: DomainEvent) -> DomainEvent:
        key = (event.event_type, event.metadata.get("schema_version", 1), 2)
        upcaster = cls.upcasters.get(key)
        if upcaster:
            return upcaster(event)
        return event

@EventUpcaster.register("order_created", from_version=1, to_version=2)
def upcast_order_created_v1_to_v2(event: DomainEvent) -> DomainEvent:
    """V1 had 'amount'; V2 renamed to 'total' and added 'currency'."""
    data = dict(event.data)
    data["total"] = data.pop("amount", 0)
    data.setdefault("currency", "USD")
    event.data = data
    event.metadata["schema_version"] = 2
    return event
```

**Backward-Compatible Evolution Rules**:

```
SAFE changes (backward compatible):
  - Add a new optional field with a default value
  - Add a new event type
  - Add a new optional header

UNSAFE changes (breaking):
  - Remove or rename a field
  - Change a field's type
  - Change the meaning of a field
  - Remove an event type

MIGRATION strategy for breaking changes:
  1. Publish both old and new event versions simultaneously
  2. Migrate all consumers to read the new version
  3. Stop publishing the old version
  4. (Optional) Upcast old events on read
```
