## JavaScript Conventions

**Tooling**:
- **Package Manager**: `npm` or `yarn`
- **Linting**: ESLint with standard or Airbnb config
- **Formatting**: Prettier

**Naming**: `camelCase` for variables/functions, `PascalCase` for classes/components, `UPPER_CASE` for constants

**Code Patterns**:
- ES6+ features (arrow functions, destructuring, spread, template literals)
- `const` over `let`, never `var`
- `async/await` over `.then()` chains
- ES Modules (`import`/`export`) over CommonJS (`require`) unless legacy Node.js
- Strict equality `===` always
- `try-finally` for resource cleanup

**Testing**: Jest or Vitest with `describe`/`it` blocks.

```javascript
describe('MathUtils', () => {
  it('should add two numbers correctly', () => {
    expect(add(2, 3)).toBe(5);
  });
});
```
