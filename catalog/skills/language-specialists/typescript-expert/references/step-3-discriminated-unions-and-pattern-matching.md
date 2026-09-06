### Step 3: Discriminated Unions and Pattern Matching

**Tagged Unions**:

Discriminated unions (also called tagged unions) use a common literal property (the discriminant) to distinguish between variants. TypeScript narrows the type automatically inside switch or if blocks that check the discriminant.

```typescript
// Define a discriminated union for API responses
type ApiResponse<T> =
  | { status: "success"; data: T; timestamp: number }
  | { status: "error"; error: string; code: number }
  | { status: "loading" };

function handleResponse(response: ApiResponse<User>): void {
  switch (response.status) {
    case "success":
      // TypeScript knows: response.data is User, response.timestamp is number
      console.log(`User: ${response.data.name}`);
      break;
    case "error":
      // TypeScript knows: response.error is string, response.code is number
      console.error(`Error ${response.code}: ${response.error}`);
      break;
    case "loading":
      // TypeScript knows: no other properties
      console.log("Loading...");
      break;
  }
}

// Shape example - classic discriminated union
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rectangle"; width: number; height: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "rectangle":
      return shape.width * shape.height;
    case "triangle":
      return 0.5 * shape.base * shape.height;
  }
}
```

**Exhaustive Checks**:

The `never` type is TypeScript's bottom type (no value is assignable to it). Use it in the default branch of a switch statement to ensure all union variants are handled. If a new variant is added to the union, the code will fail to compile until you handle it.

```typescript
// Exhaustiveness check with never
function assertNever(value: never): never {
  throw new Error(`Unexpected value: ${JSON.stringify(value)}`);
}

function getShapeColor(shape: Shape): string {
  switch (shape.kind) {
    case "circle":
      return "red";
    case "rectangle":
      return "blue";
    case "triangle":
      return "green";
    default:
      return assertNever(shape); // Compile error if a variant is missing
  }
}

// Alternative: satisfies-based exhaustive check
type Action =
  | { type: "INCREMENT"; amount: number }
  | { type: "DECREMENT"; amount: number }
  | { type: "RESET" };

function reducer(state: number, action: Action): number {
  switch (action.type) {
    case "INCREMENT":
      return state + action.amount;
    case "DECREMENT":
      return state - action.amount;
    case "RESET":
      return 0;
    default: {
      const _exhaustive: never = action;
      return state;
    }
  }
}
```

**Type Guards and Assertion Functions**:

Type guards are functions that return a type predicate (`param is Type`), allowing TypeScript to narrow the type in the calling scope. Assertion functions (`asserts param is Type`) narrow by throwing on failure rather than returning a boolean.

```typescript
// User-defined type guard
function isString(value: unknown): value is string {
  return typeof value === "string";
}

function processValue(value: unknown): void {
  if (isString(value)) {
    // value is narrowed to string
    console.log(value.toUpperCase());
  }
}

// Type guard for discriminated union members
interface Dog { kind: "dog"; bark(): void }
interface Cat { kind: "cat"; meow(): void }
type Animal = Dog | Cat;

function isDog(animal: Animal): animal is Dog {
  return animal.kind === "dog";
}

// Type guard with in operator
function hasName(obj: unknown): obj is { name: string } {
  return typeof obj === "object" && obj !== null && "name" in obj;
}

// Assertion function - narrows by throwing
function assertDefined<T>(value: T | null | undefined, message?: string): asserts value is T {
  if (value === null || value === undefined) {
    throw new Error(message ?? "Value is null or undefined");
  }
}

function processUser(user: User | null): void {
  assertDefined(user, "User must exist");
  // user is narrowed to User (not null)
  console.log(user.name);
}

// Assertion function for custom conditions
function assertIsAdmin(user: User): asserts user is User & { role: "admin" } {
  if (user.role !== "admin") {
    throw new Error("User is not an admin");
  }
}
```
