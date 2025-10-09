# JavaScript Documentation Generation (JSDoc)

## Objective
Generate comprehensive, standards-compliant JSDoc documentation for all public interfaces (modules, classes, functions) that clearly document purpose, parameters, return values, exceptions, and provide usage examples with TypeScript type support.

## Output Directory Structure

All documentation outputs should be saved in organized directories:

```
documentation/
└── docstrings/
    ├── generated_docs/
    ├── templates/
    ├── assets/
    └── exports/
```

**Directory Setup**:
- Create `documentation/` directory in repository root if it doesn't exist
- Create `documentation/docstrings/` subdirectory for this documentation phase
- All documentation files, templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:
- `generated_docs/` - Generated documentation files (HTML, MD, PDF)
- `templates/` - Documentation templates and examples
- `assets/` - Images, diagrams, supplementary files
- `exports/` - Published documentation, release artifacts

## Implementation Checklist

### Module-Level Documentation
- [ ] Module purpose and scope clearly explained
- [ ] Key classes and functions listed
- [ ] Dependencies and requirements noted
- [ ] Usage examples provided for module imports
- [ ] Author information included

### Class Documentation
- [ ] Class purpose and responsibility documented
- [ ] All public properties described with types
- [ ] Constructor parameters documented
- [ ] Class-level examples provided
- [ ] Inheritance relationships explained

### Function/Method Documentation
- [ ] Function purpose clearly stated
- [ ] All parameters documented with types and descriptions
- [ ] Return values documented with types
- [ ] Exceptions/errors documented
- [ ] Async/Promise behavior noted
- [ ] Usage examples for complex functions

### TypeScript Integration
- [ ] JSDoc complements TypeScript definitions
- [ ] Complex types explained in documentation
- [ ] Generic type usage clarified
- [ ] Type constraints documented

### Documentation Style
- [ ] Consistent JSDoc style throughout codebase
- [ ] Formatting conventions followed
- [ ] Code examples properly formatted
- [ ] Cross-references to related functions/classes

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript/TypeScript Documentation Generation Request

Please generate comprehensive JSDoc documentation for this JavaScript/TypeScript project following this protocol:

## Phase 1: Analysis & Style Selection

1. **Analyze Existing Code**
   - Inventory all modules, classes, and public functions
   - Identify existing documentation patterns
   - Note TypeScript usage and type definitions
   - Check for special documentation requirements

2. **Determine Documentation Style**
   Use **JSDoc 3** standard with TypeScript support.

3. **Review Type Definitions**
   - Check existing TypeScript types or Flow annotations
   - Ensure JSDoc complements (not duplicates) type definitions
   - Document complex types requiring additional explanation

## Phase 2: Module-Level Documentation

For each module, create comprehensive documentation:

### Module Documentation Template
```javascript
/**
 * @fileoverview [One-line summary of module purpose]
 *
 * [Detailed description of module functionality, scope, and use cases.
 * Include key concepts, main responsibilities, and intended usage.]
 *
 * @module moduleName
 * @requires dependency1
 * @requires dependency2
 *
 * @example
 * // Typical usage example
 * import { MainClass } from './module-name';
 *
 * const instance = new MainClass(param1, param2);
 * const result = instance.process();
 *
 * @example
 * // CommonJS require
 * const { MainClass } = require('./module-name');
 *
 * @author Benjamin Dourthe <benjamin@adonamed.com>
 * @version 1.0.0
 * @since 1.0.0
 * @license MIT
 */
```

## Phase 3: Class Documentation

For each class, document:

### Class Documentation Template
```javascript
/**
 * [One-line summary of class purpose]
 *
 * [Detailed description of class responsibility, behavior, and usage.
 * Explain what problems this class solves and how it fits into the
 * overall architecture.]
 *
 * @class
 * @classdesc [Additional detailed description if needed]
 *
 * @property {string} propertyName - Description of what this property represents
 *     and how it's used. Can span multiple lines if needed.
 * @property {number|null} anotherProp - Description including null behavior.
 *
 * @example
 * // Basic usage example showing common patterns
 * const obj = new ExampleClass('value');
 * const result = obj.process();
 * console.log(result); // 'processed_value'
 *
 * @example
 * // Advanced usage with options
 * const obj = new ExampleClass('value', {
 *   verbose: true,
 *   maxRetries: 3
 * });
 * const result = await obj.processAsync();
 *
 * @throws {TypeError} When constructor receives invalid parameters
 * @throws {ValidationError} When validation fails
 *
 * @see RelatedClass
 * @see {@link https://docs.example.com/classes Documentation}
 *
 * @since 1.0.0
 */
class ExampleClass {
  /**
   * Creates an instance of ExampleClass.
   *
   * @constructor
   * @param {string} value - The initial value to process
   * @param {Object} [options={}] - Configuration options
   * @param {boolean} [options.verbose=false] - Enable verbose output
   * @param {number} [options.maxRetries=3] - Maximum retry attempts
   * @throws {TypeError} If value is not a string
   */
  constructor(value, options = {}) {
    // Implementation
  }
}
```

### TypeScript Class with JSDoc
```typescript
/**
 * Type-safe example class with JSDoc documentation.
 *
 * @template T - The type of items this class processes
 * @implements {Processor<T>}
 */
class GenericProcessor<T> implements Processor<T> {
  /**
   * Process items of type T.
   *
   * @param {T[]} items - Array of items to process
   * @returns {Promise<T[]>} Processed items
   * @throws {ProcessingError} If processing fails
   *
   * @example
   * const processor = new GenericProcessor<string>();
   * const result = await processor.process(['a', 'b', 'c']);
   */
  async process(items: T[]): Promise<T[]> {
    // Implementation
  }
}
```

## Phase 4: Function/Method Documentation

For each function and method, document:

### Function Documentation Template
```javascript
/**
 * [One-line summary of what function does]
 *
 * [Detailed description of function behavior, algorithm, and usage.
 * Explain the problem it solves and any important implementation details.]
 *
 * @function
 * @async
 * @param {string} param1 - Description of param1. Include constraints,
 *     expected format, or valid values. Can span multiple lines.
 * @param {number} param2 - Description of param2. Explain what the
 *     parameter controls or represents.
 * @param {string[]} [param3=[]] - Description of optional param.
 *     Explain behavior when empty vs when provided.
 *
 * @returns {Promise<Object>} Description of return value structure.
 *     For complex returns, document the object shape:
 *     - status {string} - Success/failure status
 *     - data {*} - The processed result
 *     - metadata {Object} - Additional information
 *
 * @throws {ValueError} When param1 is empty or invalid format
 * @throws {TypeError} When param2 is not a number
 * @throws {CustomError} When specific condition occurs
 *
 * @example
 * // Basic usage
 * const result = await complexFunction('input', 42);
 * console.log(result.status); // 'success'
 *
 * @example
 * // Advanced usage with optional parameter
 * const items = ['a', 'b', 'c'];
 * const result = await complexFunction('input', 42, items);
 * console.log(result.data); // ['processed_a', 'processed_b', 'processed_c']
 *
 * @see {@link relatedFunction} Similar functionality
 * @see {@link AnotherClass#method} Used internally by this function
 *
 * @since 1.0.0
 * @deprecated Use newFunction instead
 */
async function complexFunction(param1, param2, param3 = []) {
  // Implementation
}
```

### Arrow Function Documentation
```javascript
/**
 * Process array items using a callback function.
 *
 * @type {Function}
 * @param {Array<*>} items - Items to process
 * @param {Function} callback - Processing callback
 * @param {*} callback.item - Current item
 * @param {number} callback.index - Current index
 * @returns {Array<*>} Processed items
 *
 * @example
 * const result = processItems([1, 2, 3], (item, index) => item * 2);
 * // Returns: [2, 4, 6]
 */
const processItems = (items, callback) => {
  return items.map(callback);
};
```

## Phase 5: Special Cases

### Async Functions
```javascript
/**
 * Asynchronously fetch and process data from URL.
 *
 * @async
 * @function
 * @param {string} url - The endpoint URL to fetch from
 * @param {Object} [options] - Fetch options
 * @returns {Promise<Object>} The processed response data
 * @rejects {FetchError} If network request fails
 * @rejects {TimeoutError} If operation exceeds timeout
 *
 * @example
 * try {
 *   const result = await asyncOperation('https://api.example.com/data');
 *   console.log(result.status);
 * } catch (error) {
 *   console.error('Failed:', error);
 * }
 */
async function asyncOperation(url, options = {}) {
  // Implementation
}
```

### Generator Functions
```javascript
/**
 * Generate sequence of numbers from start to end.
 *
 * @generator
 * @function
 * @param {number} start - First number in sequence
 * @param {number} end - Last number in sequence (inclusive)
 * @yields {number} Next number in the sequence
 *
 * @example
 * for (const num of numberGenerator(1, 5)) {
 *   console.log(num); // 1, 2, 3, 4, 5
 * }
 */
function* numberGenerator(start, end) {
  for (let i = start; i <= end; i++) {
    yield i;
  }
}
```

### Higher-Order Functions
```javascript
/**
 * Creates a function that retries on failure.
 *
 * @function
 * @param {number} [maxAttempts=3] - Maximum number of retry attempts
 * @returns {Function} Decorated function with retry logic
 *     @param {Function} fn - Function to wrap
 *     @returns {Function} Wrapped function
 *
 * @example
 * const retryable = withRetry(5);
 * const stableFunction = retryable(unstableFunction);
 * await stableFunction();
 */
function withRetry(maxAttempts = 3) {
  return function(fn) {
    return async function(...args) {
      // Implementation
    };
  };
}
```

### TypeScript Type Definitions
```typescript
/**
 * Configuration options for the application.
 *
 * @typedef {Object} AppConfig
 * @property {string} apiKey - API authentication key
 * @property {string} [baseUrl='https://api.example.com'] - Base API URL
 * @property {number} [timeout=5000] - Request timeout in milliseconds
 * @property {RetryOptions} [retry] - Retry configuration
 */

/**
 * Retry configuration options.
 *
 * @typedef {Object} RetryOptions
 * @property {number} maxAttempts - Maximum retry attempts
 * @property {number} backoff - Backoff multiplier
 * @property {number[]} retryStatusCodes - HTTP status codes to retry
 */

/**
 * Initialize application with configuration.
 *
 * @param {AppConfig} config - Application configuration
 * @returns {Promise<Application>} Initialized application instance
 */
async function initApp(config) {
  // Implementation
}
```

### React Components (JSX)
```javascript
/**
 * User profile display component.
 *
 * @component
 * @param {Object} props - Component props
 * @param {User} props.user - User object to display
 * @param {Function} props.onEdit - Callback when edit button clicked
 * @param {boolean} [props.showAvatar=true] - Whether to show user avatar
 *
 * @returns {React.Element} Rendered component
 *
 * @example
 * <UserProfile
 *   user={currentUser}
 *   onEdit={(user) => handleEdit(user)}
 *   showAvatar={true}
 * />
 */
function UserProfile({ user, onEdit, showAvatar = true }) {
  return (
    // JSX implementation
  );
}
```

## Phase 6: Documentation Quality Checks

Verify each JSDoc comment meets these criteria:

### Completeness
- [ ] Purpose clearly stated
- [ ] All parameters documented
- [ ] Return value documented
- [ ] Exceptions/errors documented
- [ ] Examples provided for non-trivial functions

### Clarity
- [ ] Uses clear, concise language
- [ ] Avoids jargon or explains technical terms
- [ ] Follows consistent tense
- [ ] No redundant information with TypeScript types

### Examples
- [ ] Examples are runnable
- [ ] Examples cover common use cases
- [ ] Complex functions have multiple examples
- [ ] Examples demonstrate edge cases or important patterns

### Formatting
- [ ] Consistent style throughout codebase
- [ ] Proper indentation and line breaks
- [ ] Code blocks properly formatted
- [ ] Cross-references use proper syntax

## Phase 7: Documentation Generation

After JSDoc comments are complete:

1. **Generate API Documentation**
   ```bash
   # Using JSDoc
   npm install -g jsdoc
   jsdoc src/ -d docs/api -r

   # Using documentation.js
   npm install -g documentation
   documentation build src/** -f html -o docs

   # Using TypeDoc (for TypeScript)
   npm install -g typedoc
   typedoc --out docs src/
   ```

2. **Verify Documentation Coverage**
   ```bash
   # Check documentation coverage
   npm install -g documentation
   documentation lint src/**/*.js
   ```

3. **Validate JSDoc**
   ```bash
   # Validate JSDoc syntax
   npm install -g eslint eslint-plugin-jsdoc
   eslint src/ --ext .js
   ```

## Output Format

Please provide JSDoc documentation in this format:

### File-by-File Report
```markdown
## Module: src/module-name.js

### Module Documentation
[Generated module JSDoc]

### Class: ClassName
[Generated class JSDoc]

### Function: functionName
[Generated function JSDoc]

---
```

### Summary Report
```markdown
## JSDoc Generation Summary

**Files Processed**: [count]
**Modules Documented**: [count]
**Classes Documented**: [count]
**Functions Documented**: [count]
**Properties Documented**: [count]

**Documentation Style**: JSDoc 3
**TypeScript Integration**: [Complete/Partial/None]
**Examples Added**: [count]

**Coverage Metrics**:
- Module coverage: [X%]
- Class coverage: [X%]
- Function coverage: [X%]
- Overall coverage: [X%]

**Quality Checks**:
- [ ] All public interfaces documented
- [ ] Consistent style throughout
- [ ] Examples provided where appropriate
- [ ] TypeScript types complemented (not duplicated)
- [ ] Documentation builds successfully
```

## JSDoc Style Guide Reference

### Best Practices

1. **Write for Humans First**
   - JSDoc is primarily for developers
   - Use clear, natural language
   - Explain concepts, not just syntax

2. **Complement TypeScript**
   - Don't repeat type information from TypeScript
   - Explain constraints, validation, or complex type usage
   - Document expected formats or patterns

3. **Provide Context**
   - Explain why, not just what
   - Link to related functions/classes
   - Note performance considerations or side effects

4. **Keep Examples Simple**
   - Start with basic usage
   - Add complex examples only if needed
   - Make examples copy-paste runnable

5. **Maintain Consistency**
   - Use same style throughout project
   - Follow team conventions
   - Update JSDoc when code changes

## Tools & Validation

```json
{
  "devDependencies": {
    "jsdoc": "^4.0.0",
    "documentation": "^14.0.0",
    "typedoc": "^0.25.0",
    "eslint": "^8.0.0",
    "eslint-plugin-jsdoc": "^46.0.0"
  }
}
```

### ESLint Configuration
```javascript
// .eslintrc.js
module.exports = {
  plugins: ['jsdoc'],
  extends: ['plugin:jsdoc/recommended'],
  rules: {
    'jsdoc/require-description': 'warn',
    'jsdoc/require-example': 'off',
    'jsdoc/require-param-description': 'warn',
    'jsdoc/require-returns-description': 'warn'
  }
};
```

## Common Mistakes to Avoid

1. **Don't duplicate TypeScript types in prose**
   - Bad: `@param {string} param1 - param1 is a string that...`
   - Good: `@param {string} param1 - The identifier used to...`

2. **Don't use imperative mood**
   - Bad: `Calculate the sum...`
   - Good: `Calculates the sum...` or `The sum of...`

3. **Don't omit important details**
   - Document side effects
   - Explain non-obvious behavior
   - Note performance implications

4. **Don't write overly verbose documentation**
   - Be concise but complete
   - Avoid redundant phrases
   - Get to the point quickly

5. **Don't forget to update JSDoc**
   - Keep in sync with code changes
   - Update examples when behavior changes
   - Remove obsolete information
~~~

## Output Format Specifications

The generated JSDoc should:
- Follow JSDoc 3 standard consistently
- Include all required tags based on code element type
- Provide runnable examples where appropriate
- Complement TypeScript definitions without redundancy
- Use clear, concise language
- Include proper cross-references to related functionality
- Pass linters (ESLint with jsdoc plugin)
- Generate properly formatted API documentation
