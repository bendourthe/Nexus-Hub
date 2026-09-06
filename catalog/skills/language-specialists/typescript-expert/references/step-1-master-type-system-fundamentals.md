### Step 1: Master Type System Fundamentals

**Strict Mode and Compiler Flags**:

TypeScript's `strict` flag is an umbrella that enables a family of stricter checks. Always enable it in production projects. The individual flags it activates include `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitAny`, `noImplicitThis`, `useUnknownInCatchVariables`, and `alwaysStrict`.

```typescript
// tsconfig.json (strict mode enabled)
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

**Literal Types and Const Assertions**:

Literal types narrow a value to an exact string, number, or boolean rather than the wider primitive type. Use `as const` to tell the compiler to infer the narrowest possible type for an expression.

```typescript
// Literal types
type Direction = "north" | "south" | "east" | "west";
type HttpStatus = 200 | 301 | 404 | 500;
type Toggle = true | false;

function move(direction: Direction): void {
  console.log(`Moving ${direction}`);
}

move("north"); // OK
// move("up"); // Error: Argument of type '"up"' is not assignable

// const assertion - infers the narrowest type
const config = {
  endpoint: "https://api.example.com",
  retries: 3,
  methods: ["GET", "POST"],
} as const;
// Type: { readonly endpoint: "https://api.example.com"; readonly retries: 3; readonly methods: readonly ["GET", "POST"] }

// Without `as const`, methods would be string[] and retries would be number
const looseConfig = {
  endpoint: "https://api.example.com",
  retries: 3,
  methods: ["GET", "POST"],
};
// Type: { endpoint: string; retries: number; methods: string[] }

// Extracting literal union from const array
const ROLES = ["admin", "editor", "viewer"] as const;
type Role = (typeof ROLES)[number]; // "admin" | "editor" | "viewer"
```

**Template Literal Types**:

Template literal types build string types by interpolating other types into template literal positions. They are useful for creating constrained string patterns at the type level.

```typescript
// Basic template literal type
type EventName = `on${string}`;
type ValidEvent = EventName; // any string starting with "on"

// Combining unions in template literals
type Color = "red" | "blue" | "green";
type Shade = "light" | "dark";
type ColorVariant = `${Shade}-${Color}`;
// "light-red" | "light-blue" | "light-green" | "dark-red" | "dark-blue" | "dark-green"

// CSS unit type
type CSSUnit = "px" | "em" | "rem" | "%";
type CSSValue = `${number}${CSSUnit}`;

function setWidth(value: CSSValue): void {
  // ...
}

setWidth("100px");  // OK
setWidth("1.5rem"); // OK
// setWidth("100");  // Error: not assignable to CSSValue

// Intrinsic string manipulation types
type Uppercased = Uppercase<"hello">; // "HELLO"
type Lowercased = Lowercase<"HELLO">; // "hello"
type Capitalized = Capitalize<"hello">; // "Hello"
type Uncapitalized = Uncapitalize<"Hello">; // "hello"
```

**Branded Types**:

Branded types (also called nominal types or opaque types) use an intersection with a unique symbol to prevent accidental mixing of structurally identical types. This is a powerful pattern for domain modelling.

```typescript
// Branded type pattern
type Brand<T, B extends string> = T & { readonly __brand: B };

type USD = Brand<number, "USD">;
type EUR = Brand<number, "EUR">;
type UserId = Brand<string, "UserId">;
type OrderId = Brand<string, "OrderId">;

// Constructor functions that brand raw values
function usd(amount: number): USD {
  if (!Number.isFinite(amount) || amount < 0) throw new RangeError("USD amount must be finite and non-negative");
  // SAFETY: the constructor checked the currency domain invariant before applying the USD brand.
  return amount as USD;
}

function eur(amount: number): EUR {
  if (!Number.isFinite(amount) || amount < 0) throw new RangeError("EUR amount must be finite and non-negative");
  // SAFETY: the constructor checked the currency domain invariant before applying the EUR brand.
  return amount as EUR;
}

function userId(id: string): UserId {
  if (id.trim() === "") throw new TypeError("UserId must not be empty");
  // SAFETY: the constructor checked the non-empty identifier invariant before applying the UserId brand.
  return id as UserId;
}

// Type safety prevents mixing currencies or IDs
function chargeUSD(amount: USD): void {
  console.log(`Charging $${amount}`);
}

chargeUSD(usd(19.99));   // OK
// chargeUSD(eur(19.99)); // Error: EUR is not assignable to USD
// chargeUSD(19.99);      // Error: number is not assignable to USD

function getUser(id: UserId): void { /* ... */ }
// getUser("abc");         // Error: string is not assignable to UserId
// getUser(orderId("abc")); // Error: OrderId is not assignable to UserId
```
