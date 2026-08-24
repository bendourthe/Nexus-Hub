### Step 2: Choose a Message Broker

**Broker Comparison**:

```
┌──────────────┬────────────────┬─────────────────┬───────────────┬──────────────┐
│ Feature      │ Apache Kafka   │ RabbitMQ        │ AWS SNS/SQS   │ NATS         │
├──────────────┼────────────────┼─────────────────┼───────────────┼──────────────┤
│ Model        │ Log-based      │ Queue/exchange  │ Queue + topic │ Pub/sub +    │
│              │ streaming      │ broker          │ cloud managed │ JetStream    │
├──────────────┼────────────────┼─────────────────┼───────────────┼──────────────┤
│ Ordering     │ Per-partition  │ Per-queue       │ FIFO optional │ Per-subject  │
│              │ guaranteed     │ guaranteed      │ (SQS FIFO)    │ (JetStream)  │
├──────────────┼────────────────┼─────────────────┼───────────────┼──────────────┤
│ Retention    │ Configurable   │ Until consumed  │ Up to 14 days │ Configurable │
│              │ (days/size)    │                 │ (SQS)         │ (JetStream)  │
├──────────────┼────────────────┼─────────────────┼───────────────┼──────────────┤
│ Replay       │ Yes (offset)   │ No (dead letter │ No (DLQ only) │ Yes          │
│              │                │ only)           │               │ (JetStream)  │
├──────────────┼────────────────┼─────────────────┼───────────────┼──────────────┤
│ Throughput   │ Very high      │ Moderate        │ High          │ Very high    │
│              │ (millions/sec) │ (tens of k/sec) │ (managed)     │ (millions/s) │
├──────────────┼────────────────┼─────────────────┼───────────────┼──────────────┤
│ Complexity   │ High           │ Moderate        │ Low           │ Low-Moderate │
├──────────────┼────────────────┼─────────────────┼───────────────┼──────────────┤
│ Best For     │ Event streams, │ Task queues,    │ Serverless,   │ Microservice │
│              │ CDC, analytics │ RPC, routing    │ AWS-native    │ messaging    │
└──────────────┴────────────────┴─────────────────┴───────────────┴──────────────┘
```
