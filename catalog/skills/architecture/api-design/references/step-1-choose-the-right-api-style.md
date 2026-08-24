### Step 1: Choose the Right API Style

**Decision Matrix**:

| Factor | REST | GraphQL | gRPC |
|--------|------|---------|------|
| Client diversity | Many unknown clients | Multiple frontends (web, mobile) | Internal service-to-service |
| Data shape | Fixed, resource-oriented | Flexible, client-driven | Fixed, contract-driven |
| Performance | Good (HTTP caching) | Variable (no HTTP caching) | Excellent (binary, HTTP/2) |
| Real-time | Webhooks, SSE | Subscriptions | Bidirectional streaming |
| Discoverability | OpenAPI, HATEOAS | Introspection | Reflection, proto files |
| Learning curve | Low | Medium | Medium-High |
| Browser support | Native | Native (via HTTP) | Requires grpc-web proxy |
| File uploads | Native multipart | Awkward (base64 or multipart) | Streaming chunks |

**When to Choose Each**:

```
REST:    Public APIs, third-party integrations, CRUD-heavy services,
         when HTTP caching matters, when you need broad tooling support.

GraphQL: Multiple client types with different data needs (mobile wants
         less data than web), rapid frontend iteration, aggregating
         data from multiple backend services into a single query.

gRPC:    Internal microservice communication, low-latency requirements,
         polyglot environments (code generation from proto files),
         bidirectional streaming (chat, live data feeds).
```
