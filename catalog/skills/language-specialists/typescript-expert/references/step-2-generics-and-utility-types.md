### Step 2: Generics and Utility Types

**Generic Constraints**:

Generics allow you to write functions and types that work with any type while preserving type information. Constraints (the `extends` keyword) restrict what types a generic parameter can accept.

```typescript
// Basic generic function
function identity<T>(value: T): T {
  return value;
}

const num = identity(42);       // inferred as number
const str = identity("hello");  // inferred as string

// Constrained generic - T must have a length property
function getLength<T extends { length: number }>(item: T): number {
  return item.length;
}

getLength("hello");    // OK - string has length
getLength([1, 2, 3]);  // OK - array has length
// getLength(42);       // Error: number doesn't have length

// Generic with keyof constraint
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: "Alice", age: 30, active: true };
const name = getProperty(user, "name");    // type: string
const age = getProperty(user, "age");      // type: number
// getProperty(user, "email");              // Error: "email" not in keyof typeof user

// Multiple generic parameters with relationships
function merge<T extends object, U extends object>(a: T, b: U): T & U {
  return { ...a, ...b };
}

const merged = merge({ name: "Alice" }, { age: 30 });
// type: { name: string } & { age: number }
```

**Conditional Types**:

Conditional types select one of two types based on a condition, using the syntax `T extends U ? X : Y`. They are especially powerful when combined with `infer` to extract types from complex structures.

```typescript
// Basic conditional type
type IsString<T> = T extends string ? true : false;

type A = IsString<"hello">; // true
type B = IsString<42>;      // false

// Distributive conditional types (distributes over unions)
type ToArray<T> = T extends unknown ? T[] : never;
type Result = ToArray<string | number>; // string[] | number[]

// Non-distributive (wrap in tuple to prevent distribution)
type ToArrayNonDist<T> = [T] extends [unknown] ? T[] : never;
type Result2 = ToArrayNonDist<string | number>; // (string | number)[]

// The infer keyword - extract types from structures
type ReturnTypeOf<T> = T extends (...args: unknown[]) => infer R ? R : never;
type FnReturn = ReturnTypeOf<(x: number) => string>; // string

type ElementType<T> = T extends (infer E)[] ? E : T;
type El = ElementType<string[]>;  // string
type El2 = ElementType<number>;   // number (fallback)

// Extract promise value type
type Awaited<T> = T extends Promise<infer U> ? Awaited<U> : T;
type Resolved = Awaited<Promise<Promise<string>>>; // string

// Infer from function parameters
type FirstParam<T> = T extends (first: infer P, ...rest: unknown[]) => unknown ? P : never;
type Param = FirstParam<(x: number, y: string) => void>; // number
```

**Mapped Types**:

Mapped types transform every property of an existing type by iterating over its keys. They are the foundation of many built-in utility types.

```typescript
// Basic mapped type
type Readonly<T> = {
  readonly [K in keyof T]: T[K];
};

type Optional<T> = {
  [K in keyof T]?: T[K];
};

// Mapped type with key remapping (TypeScript 4.1+)
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface Person {
  name: string;
  age: number;
}

type PersonGetters = Getters<Person>;
// { getName: () => string; getAge: () => number }

// Filtering keys with mapped types
type FilterByType<T, ValueType> = {
  [K in keyof T as T[K] extends ValueType ? K : never]: T[K];
};

interface Mixed {
  name: string;
  age: number;
  active: boolean;
  email: string;
}

type StringProps = FilterByType<Mixed, string>;
// { name: string; email: string }
```

**Built-in Utility Types**:

TypeScript provides a comprehensive set of utility types that cover the most common type transformations. Knowing these prevents you from reinventing them.

```typescript
// Record - construct an object type with specific keys and value types
type PageInfo = Record<"home" | "about" | "contact", { title: string; url: string }>;

// Pick and Omit - select or remove properties
type UserSummary = Pick<User, "id" | "name">;
type UserWithoutPassword = Omit<User, "password">;

// Extract and Exclude - filter union members
type NumOrStr = Extract<string | number | boolean, string | number>; // string | number
type OnlyBool = Exclude<string | number | boolean, string | number>; // boolean

// Parameters and ReturnType - extract function type info
type Params = Parameters<typeof fetch>; // [input: RequestInfo | URL, init?: RequestInit]
type Return = ReturnType<typeof fetch>;  // Promise<Response>

// NonNullable - remove null and undefined
type MaybeString = string | null | undefined;
type DefiniteString = NonNullable<MaybeString>; // string

// Partial and Required - toggle optionality
interface Config {
  host: string;
  port: number;
  debug?: boolean;
}

type PartialConfig = Partial<Config>;   // all optional
type FullConfig = Required<Config>;     // all required (debug becomes required)

// Readonly at the utility level
type FrozenConfig = Readonly<Config>;
// { readonly host: string; readonly port: number; readonly debug?: boolean }
```
