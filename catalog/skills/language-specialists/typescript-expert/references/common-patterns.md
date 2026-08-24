## Common Patterns

### Pattern 1: Type-Safe Event Emitter

```typescript
type EventMap = {
  userCreated: { userId: string; email: string };
  orderPlaced: { orderId: string; total: number };
  error: { message: string; code: number };
};

class TypedEmitter<Events extends Record<string, unknown>> {
  private handlers = new Map<keyof Events, Set<(data: never) => void>>();

  on<K extends keyof Events>(event: K, handler: (data: Events[K]) => void): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler as (data: never) => void);
  }

  emit<K extends keyof Events>(event: K, data: Events[K]): void {
    this.handlers.get(event)?.forEach((handler) => handler(data as never));
  }
}

const emitter = new TypedEmitter<EventMap>();
emitter.on("userCreated", (data) => {
  // data is { userId: string; email: string }
  console.log(data.userId);
});
// emitter.emit("userCreated", { orderId: "123" }); // Error: missing userId
```

### Pattern 2: Type-Safe API Client

```typescript
// Define route map as a type
interface ApiRoutes {
  "GET /users": { response: User[]; query: { page?: number } };
  "GET /users/:id": { response: User; params: { id: string } };
  "POST /users": { response: User; body: CreateUserDto };
  "PUT /users/:id": { response: User; params: { id: string }; body: UpdateUserDto };
  "DELETE /users/:id": { response: void; params: { id: string } };
}

type Method = "GET" | "POST" | "PUT" | "DELETE";

type RoutesForMethod<M extends Method> = {
  [K in keyof ApiRoutes]: K extends `${M} ${string}` ? K : never;
}[keyof ApiRoutes];

// The client enforces correct params, body, and query for each route
async function apiClient<K extends keyof ApiRoutes>(
  route: K,
  options: Omit<ApiRoutes[K], "response">,
): Promise<ApiRoutes[K]["response"]> {
  // Implementation: parse method and path from route key, substitute params, fetch...
  throw new Error("Not implemented");
}

// Usage - fully type-checked
const users = await apiClient("GET /users", { query: { page: 1 } });
const user = await apiClient("POST /users", { body: { name: "Alice", email: "a@b.com" } });
```
