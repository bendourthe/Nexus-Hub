### Step 5: Runtime Validation with Zod

**Schema Definition**:

TypeScript types are erased at compile time and provide no runtime safety. Zod bridges this gap by defining schemas that validate data at runtime and infer static types from the same source of truth.

```typescript
import { z } from "zod";

// Primitive schemas
const nameSchema = z.string().min(1).max(100);
const ageSchema = z.number().int().positive().max(150);
const emailSchema = z.string().email();

// Named metadata schema: the accepted keys and value types are explicit.
const UserMetadataSchema = z.object({
  source: z.enum(["signup", "import", "admin"]),
  marketingOptIn: z.boolean().optional(),
}).strict();

// Object schema
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  email: z.string().email(),
  age: z.number().int().min(0).max(150),
  role: z.enum(["admin", "editor", "viewer"]),
  metadata: UserMetadataSchema.optional(),
});

// Infer the TypeScript type from the schema
type User = z.infer<typeof UserSchema>;
// metadata?: { source: "signup" | "import" | "admin"; marketingOptIn?: boolean }

// Nested and composed schemas
const AddressSchema = z.object({
  street: z.string(),
  city: z.string(),
  country: z.string().length(2), // ISO country code
  zip: z.string().regex(/^\d{5}(-\d{4})?$/),
});

const UserWithAddressSchema = UserSchema.extend({
  address: AddressSchema,
  tags: z.array(z.string()).default([]),
});
```

**safeParse and Error Handling**:

Always prefer `safeParse` over `parse` in application code. While `parse` throws on invalid input, `safeParse` returns a discriminated union that forces you to handle both success and failure paths explicitly.

```typescript
// safeParse returns a discriminated union
const result = UserSchema.safeParse(unknownData);

if (result.success) {
  // result.data is fully typed as User
  console.log(result.data.name);
} else {
  // result.error contains detailed validation errors
  const formatted = result.error.format();
  console.error(formatted);

  // Iterate individual issues
  for (const issue of result.error.issues) {
    console.error(`${issue.path.join(".")}: ${issue.message}`);
  }
}

// In an Express route handler
app.post("/users", (req, res) => {
  const parsed = UserSchema.safeParse(req.body);

  if (!parsed.success) {
    return res.status(400).json({
      errors: parsed.error.issues.map((i) => ({
        field: i.path.join("."),
        message: i.message,
      })),
    });
  }

  // parsed.data is User - fully validated and typed
  createUser(parsed.data);
  return res.status(201).json(parsed.data);
});
```

**Transforms and Refinements**:

Transforms change the output type of a schema (for example, coercing a date string into a `Date` object). Refinements add custom validation logic without changing the type.

```typescript
// Transform: change the output type
const DateStringSchema = z
  .string()
  .datetime()
  .transform((str) => new Date(str));

type DateOutput = z.infer<typeof DateStringSchema>; // Date (not string)

// Coercion helpers
const CoercedNumber = z.coerce.number(); // "42" -> 42
const CoercedBoolean = z.coerce.boolean(); // "true" -> true

// Refinement: custom validation without changing the type
const PasswordSchema = z
  .string()
  .min(8)
  .refine((pw) => /[A-Z]/.test(pw), "Must contain an uppercase letter")
  .refine((pw) => /[0-9]/.test(pw), "Must contain a digit")
  .refine((pw) => /[^A-Za-z0-9]/.test(pw), "Must contain a special character");

// Superrefine for cross-field validation
const SignupSchema = z
  .object({
    password: z.string().min(8),
    confirmPassword: z.string(),
  })
  .superRefine((data, ctx) => {
    if (data.password !== data.confirmPassword) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Passwords do not match",
        path: ["confirmPassword"],
      });
    }
  });

// Discriminated union schema
const EventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("click"), x: z.number(), y: z.number() }),
  z.object({ type: z.literal("keypress"), key: z.string() }),
  z.object({ type: z.literal("scroll"), delta: z.number() }),
]);

type AppEvent = z.infer<typeof EventSchema>;
```
