---
name: event-driven-architecture
description: Event-driven architecture patterns including event sourcing, CQRS, message brokers, and event schema design. Use when designing asynchronous systems, implementing event stores, or choosing messaging infrastructure.
summary_l0: "Build event-driven systems with event sourcing, CQRS, and message broker patterns"
overview_l1: "This skill provides comprehensive guidance on building event-driven systems, covering event sourcing, CQRS, message broker selection, event schema design, saga patterns, idempotency, and event versioning. Use it when designing publish/subscribe or event streaming systems, implementing event sourcing with an event store, applying CQRS to separate read and write models, choosing between Kafka, RabbitMQ, AWS SNS/SQS, and NATS, implementing saga patterns (orchestration or choreography), designing event schemas with CloudEvents, Avro, or Protobuf, handling idempotency and exactly-once semantics, managing dead letter queues and event replay, or versioning events without breaking consumers. Key capabilities include core event patterns, broker comparison matrices, schema design with the CloudEvents standard, saga coordination, idempotency key strategies, dead letter queue management, and event evolution techniques. The expected output is event schemas, broker configuration, saga implementations, and event store setup."
---

# Event-Driven Architecture

Comprehensive guidance on building event-driven systems, covering event sourcing, CQRS, message broker selection (Kafka, RabbitMQ, NATS), event schema design with CloudEvents, saga patterns, idempotency, and strategies for event versioning and evolution.

## When to Use This Skill

Use this skill for:

- Designing publish/subscribe or event streaming systems
- Implementing event sourcing with an event store
- Applying CQRS to separate read and write models
- Choosing between Kafka, RabbitMQ, AWS SNS/SQS, and NATS
- Implementing the saga pattern (orchestration or choreography)
- Designing event schemas with CloudEvents, Avro, or Protobuf
- Handling idempotency and exactly-once semantics
- Managing dead letter queues and event replay
- Versioning events without breaking consumers

**Trigger phrases**: "event-driven", "event sourcing", "CQRS", "message broker", "Kafka", "RabbitMQ", "pub/sub", "saga pattern", "event store", "dead letter queue", "event schema", "CloudEvents", "eventual consistency"

## What This Skill Does

Provides production-ready event-driven patterns including:

- **Core Patterns**: Pub/sub, event streaming, event sourcing, CQRS
- **Broker Selection**: Feature comparison and trade-offs for Kafka, RabbitMQ, NATS, SNS/SQS
- **Schema Design**: CloudEvents format, Avro schemas, schema registry, event versioning
- **Reliability**: Idempotency, outbox pattern, dead letter queues, exactly-once semantics
- **Orchestration**: Saga pattern (orchestrator-based and choreography-based)
- **Operations**: Consumer groups, partitioning, replay, monitoring

## Instructions

### Step 1: Understand Event-Driven Patterns

Full walkthrough: [step-1-understand-event-driven-patterns.md](references/step-1-understand-event-driven-patterns.md) (load this step when you reach it).

### Step 2: Choose a Message Broker

Full walkthrough: [step-2-choose-a-message-broker.md](references/step-2-choose-a-message-broker.md) (load this step when you reach it).

### Step 3: Design Event Schemas

Full walkthrough: [step-3-design-event-schemas.md](references/step-3-design-event-schemas.md) (load this step when you reach it).

### Step 4: Implement Kafka Producer and Consumer

Full walkthrough: [step-4-implement-kafka-producer-and-consumer.md](references/step-4-implement-kafka-producer-and-consumer.md) (load this step when you reach it).

### Step 5: Implement Event Sourcing

Full walkthrough: [step-5-implement-event-sourcing.md](references/step-5-implement-event-sourcing.md) (load this step when you reach it).

### Step 6: Implement the Saga Pattern

Full walkthrough: [step-6-implement-the-saga-pattern.md](references/step-6-implement-the-saga-pattern.md) (load this step when you reach it).

### Step 7: Handle Event Versioning and Evolution

Full walkthrough: [step-7-handle-event-versioning-and-evolution.md](references/step-7-handle-event-versioning-and-evolution.md) (load this step when you reach it).

### Step 8: Implement the Outbox Pattern

Full walkthrough: [step-8-implement-the-outbox-pattern.md](references/step-8-implement-the-outbox-pattern.md) (load this step when you reach it).

## Best Practices

- **Use the outbox pattern** to guarantee atomicity between state changes and event publication
- **Design events as facts** (past tense, immutable); never update a published event
- **Include enough context** in events so consumers do not need to call back to the producer
- **Implement idempotent consumers** using a processed-events table or deduplication key
- **Use a schema registry** (Confluent, Apicurio) to enforce schema compatibility
- **Version events from day one**; include a schema_version field in metadata
- **Set up dead letter queues** for every consumer to capture unprocessable messages
- **Partition by aggregate ID** so all events for one entity go to the same partition (ordering)
- **Monitor consumer lag** as a key health metric; alert when lag exceeds a threshold
- **Prefer choreography for simple flows** (2-3 services); use orchestration for complex sagas (4+)
- **Replay events to rebuild read models** rather than writing complex migration scripts

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll write to the database and publish the event in the same method, that's atomic enough" | A crash between the commit and the publish leaves the data changed but no event emitted, silently desynchronizing every downstream consumer; the transactional outbox pattern exists because dual writes are not atomic. |
| "At-least-once delivery is fine, duplicates are rare" | Brokers redeliver on consumer restart and rebalance, so duplicates are routine, not rare; a non-idempotent consumer that charges a card on each delivery double-bills the customer the first time a pod restarts mid-batch. |
| "We can add a field to the event and consumers will just ignore it" | Adding a required field or renaming one breaks every consumer deserializing the old schema; without a registry enforcing backward compatibility and an upcasting strategy, a producer deploy takes down the consumers. |
| "Choreography is simpler than orchestration, just let services react to events" | Pure choreography across many services produces an emergent workflow nobody can see or debug, and compensating a half-completed saga becomes guesswork; complex multi-step transactions need an explicit orchestrator with defined compensations. |

## Verification

- [ ] Events use past tense and follow a consistent naming convention
- [ ] Event schemas include specversion, id, source, type, and timestamp (CloudEvents)
- [ ] Outbox pattern ensures atomicity between data writes and event publication
- [ ] Consumers are idempotent (duplicate event processing is safe)
- [ ] Dead letter queues configured for every consumer
- [ ] Schema versioning strategy documented (upcasting or dual-publish)
- [ ] Consumer group lag is monitored and alerted
- [ ] Partitioning strategy ensures ordering where needed
- [ ] Saga compensations handle failure of compensating actions
- [ ] Event retention and compaction policies defined
- [ ] Read model rebuild procedure documented and tested
- [ ] Schema registry enforces backward compatibility

## Related Skills

- [[async-patterns]] -- concurrency patterns for event processing
- [[observability-setup]] -- monitoring event-driven systems and consumer lag
- [[graphql-development]] -- GraphQL subscriptions as an event delivery mechanism
- [[cloud-architect]] -- managed messaging services (SNS/SQS, EventBridge, Pub/Sub)
- [[microservices-patterns]] -- the service topology this event infrastructure connects
- [[ddd-strategic-design]] -- domain events and bounded contexts that define the event catalog

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
