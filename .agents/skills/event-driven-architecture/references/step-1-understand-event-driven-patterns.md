### Step 1: Understand Event-Driven Patterns

```
┌────────────────────────────────────────────────────────────────────┐
│                    EVENT-DRIVEN PATTERNS                          │
├──────────────────┬──────────────────┬──────────────────────────────┤
│    PUB/SUB       │ EVENT STREAMING  │    EVENT SOURCING            │
│                  │                  │                              │
│  Fire-and-forget │  Ordered log of  │  Persist all state changes   │
│  message         │  events with     │  as events; derive current   │
│  broadcasting    │  consumer replay │  state by replaying          │
│                  │                  │                              │
│  Use: notifs,    │  Use: data       │  Use: audit, undo, temporal  │
│  webhooks,       │  pipelines,      │  queries, complex domains    │
│  decoupling      │  CDC, analytics  │                              │
│                  │                  │                              │
│  Tools:          │  Tools:          │  Tools:                      │
│  RabbitMQ, SNS,  │  Kafka, Pulsar,  │  EventStoreDB, Kafka +      │
│  Redis Pub/Sub   │  Kinesis, NATS   │  custom store, Axon          │
│                  │  JetStream       │                              │
└──────────────────┴──────────────────┴──────────────────────────────┘
```

**Pattern Selection Guide**:

```
Q: Do I need to replay past events?
├── No  -> Simple pub/sub (RabbitMQ, SNS/SQS)
└── Yes
    Q: Do I need to reconstruct state from events?
    ├── No  -> Event streaming (Kafka, NATS JetStream)
    └── Yes -> Event sourcing (EventStoreDB, custom event store)

Q: Are reads and writes significantly different in shape or scale?
├── No  -> Single model is fine
└── Yes -> CQRS (separate read/write models, eventually consistent)
```
