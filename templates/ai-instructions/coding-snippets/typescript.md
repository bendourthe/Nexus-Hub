## TypeScript Conventions

**Tooling**:
- **Execution**: `ts-node` for dev, `tsc` for build
- **Linting**: ESLint with TypeScript integration
- **Formatting**: Prettier
- **Config**: `strict: true` in `tsconfig.json`

**Naming**: `camelCase` for variables/functions, `PascalCase` for classes/interfaces/types, `UPPER_CASE` for constants

**Code Patterns**:
- `interface` for object shapes/classes, `type` for unions/intersections/aliases
- Avoid `any`; use `unknown` for unsafe inputs
- Optional chaining `?.` and nullish coalescing `??`
- Explicit imports with absolute paths (if configured in `tsconfig.json`)
- Avoid unsafe type assertions (`as ...`)

**Testing**: Jest or Vitest (with `ts-jest` or native support).

```typescript
import { add } from './math';

describe('MathUtils', () => {
  it('should add two numbers correctly', () => {
    const result: number = add(2, 3);
    expect(result).toBe(5);
  });
});
```
