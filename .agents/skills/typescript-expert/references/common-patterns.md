## Common Patterns

### Pattern 1: Type-Safe Event Emitter

```typescript
type EventMap = {
  userCreated: { userId: string; email: string };
  orderPlaced: { orderId: string; total: number };
  error: { message: string; code: number };
};

type EventHandlers<Events> = {
  [K in keyof Events]?: Set<(data: Events[K]) => void>;
};

class TypedEmitter<Events> {
  private handlers: EventHandlers<Events> = {};

  on<K extends keyof Events>(event: K, handler: (data: Events[K]) => void): void {
    const handlers = this.handlers[event] ?? new Set<(data: Events[K]) => void>();
    handlers.add(handler);
    this.handlers[event] = handlers;
  }

  emit<K extends keyof Events>(event: K, data: Events[K]): void {
    this.handlers[event]?.forEach((handler) => handler(data));
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
