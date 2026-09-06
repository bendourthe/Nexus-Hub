### Step 4: Advanced Type Patterns

**Recursive Types**:

TypeScript supports recursive type aliases, which reference themselves in their definition. These are essential for modelling tree structures, JSON values, and deeply nested data.

```typescript
// JSON type - a classic recursive type
type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

// Deeply nested readonly
type DeepReadonly<T> = T extends object
  ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
  : T;

interface NestedConfig {
  db: { host: string; credentials: { user: string; pass: string } };
  features: string[];
}

type FrozenConfig = DeepReadonly<NestedConfig>;
// All properties at every depth are readonly

// Deep partial
type DeepPartial<T> = T extends object
  ? { [K in keyof T]?: DeepPartial<T[K]> }
  : T;

// Recursive path type - generates dot-notation paths for an object
type Path<T, Prefix extends string = ""> = T extends object
  ? {
      [K in keyof T & string]: K | `${K}.${Path<T[K], "">}`;
    }[keyof T & string]
  : never;

interface Form {
  user: { name: string; address: { city: string; zip: string } };
  tags: string[];
}

type FormPath = Path<Form>;
// "user" | "user.name" | "user.address" | "user.address.city" | "user.address.zip" | "tags"
```

**Variadic Tuple Types**:

Variadic tuple types (TypeScript 4.0+) allow generic spreading of tuple types, enabling type-safe operations on function arguments and tuple manipulation.

```typescript
// Spread in tuple types
type Concat<A extends unknown[], B extends unknown[]> = [...A, ...B];
type Result = Concat<[1, 2], [3, 4]>; // [1, 2, 3, 4]

// Prepend an element to a tuple
type Prepend<T, Arr extends unknown[]> = [T, ...Arr];
type WithId = Prepend<number, [string, boolean]>; // [number, string, boolean]

// Typed zip function
function zip<A extends unknown[], B extends unknown[]>(
  a: [...A],
  b: [...B],
): { [K in keyof A]: [A[K], K extends keyof B ? B[K] : undefined] } {
  // SAFETY: map preserves the length and numeric index order of tuple `a`; absent indices in `b` produce undefined.
  return a.map((val, i) => [val, b[i]]) as never;
}

const zipped = zip([1, "a"] as const, [true, 42] as const);
// type: [[1, true], ["a", 42]]

// Type-safe pipe function using variadic tuples
type Last<T extends unknown[]> = T extends [...unknown[], infer L] ? L : never;

function pipe<T, Fns extends ((arg: never) => unknown)[]>(
  initial: T,
  ...fns: Fns
): ReturnType<Last<Fns> extends (...args: never[]) => infer R ? () => R : never> {
  // SAFETY: callers provide an ordered function tuple whose adjacent input and output types compose.
  return fns.reduce((acc, fn) => fn(acc), initial) as never;
}
```

**Declaration Merging and Module Augmentation**:

TypeScript merges declarations with the same name in the same scope. Interfaces merge automatically, and module augmentation lets you extend third-party types without modifying their source.

```typescript
// Interface merging - declarations combine
interface Box {
  width: number;
  height: number;
}

interface Box {
  color: string;
}

// Box now has width, height, and color
const box: Box = { width: 10, height: 20, color: "red" };

// Module augmentation - extend third-party types
// Extend Express Request with custom properties
declare module "express" {
  interface Request {
    userId?: string;
    correlationId: string;
  }
}

// Now TypeScript knows about req.userId and req.correlationId
// in all Express route handlers

// Augmenting a global type
declare global {
  interface Window {
    __APP_CONFIG__: {
      apiUrl: string;
      version: string;
    };
  }
}

// Now window.__APP_CONFIG__ is typed everywhere

// Namespace merging with enums
enum Color {
  Red = "RED",
  Blue = "BLUE",
}

namespace Color {
  export function parse(str: string): Color | undefined {
    const values = [Color.Red, Color.Blue] as const;
    return values.find((color) => color === str);
  }
}

Color.parse("RED"); // Color.Red
```

**Type-Level Programming**:

TypeScript's type system is Turing-complete, allowing you to encode logic (string parsing, arithmetic, validation) entirely at the type level. Use this sparingly for library APIs where compile-time safety justifies the complexity.

```typescript
// Type-level string parsing
type Split<S extends string, D extends string> = S extends `${infer Head}${D}${infer Tail}`
  ? [Head, ...Split<Tail, D>]
  : [S];

type Parts = Split<"a.b.c", ".">; // ["a", "b", "c"]

// Type-level builder pattern
interface QueryBuilder<Selected extends string = never> {
  select<Col extends string>(
    column: Col,
  ): QueryBuilder<Selected | Col>;
  where(column: Selected, value: unknown): QueryBuilder<Selected>;
  execute(): Promise<Record<Selected, unknown>[]>;
}

// Usage ensures you can only filter on selected columns
declare const qb: QueryBuilder;
const query = qb
  .select("name")
  .select("age")
  .where("name", "Alice") // OK - "name" is selected
  // .where("email", "x")  // Error - "email" is not in Selected

// Compile-time route parameter extraction
type ExtractParams<T extends string> = T extends `${string}:${infer Param}/${infer Rest}`
  ? Param | ExtractParams<Rest>
  : T extends `${string}:${infer Param}`
    ? Param
    : never;

type RouteParams = ExtractParams<"/users/:userId/posts/:postId">;
// "userId" | "postId"

type ParamMap<T extends string> = Record<ExtractParams<T>, string>;
// For the route above: { userId: string; postId: string }
```
