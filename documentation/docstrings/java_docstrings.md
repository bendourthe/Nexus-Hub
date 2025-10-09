# Java Documentation Generation (JavaDoc)

## Objective
Generate comprehensive, standards-compliant JavaDoc documentation for all public interfaces (packages, classes, methods) that clearly document purpose, parameters, return values, exceptions, and provide usage examples with proper type information.

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

### Package-Level Documentation
- [ ] Package purpose and scope clearly explained
- [ ] Key classes and interfaces listed
- [ ] Dependencies and requirements noted
- [ ] Usage examples provided for package imports
- [ ] Author information included

### Class/Interface Documentation
- [ ] Class purpose and responsibility documented
- [ ] All public fields described with types
- [ ] Constructor parameters documented
- [ ] Class-level examples provided
- [ ] Inheritance relationships explained
- [ ] Interface contracts documented

### Method Documentation
- [ ] Method purpose clearly stated
- [ ] All parameters documented with types and descriptions
- [ ] Return values documented with types
- [ ] Exceptions documented with @throws
- [ ] Thread safety documented
- [ ] Usage examples for complex methods

### Type Integration
- [ ] JavaDoc complements type signatures
- [ ] Generic type usage clarified
- [ ] Type constraints documented
- [ ] Null handling documented

### Documentation Style
- [ ] Consistent JavaDoc style throughout codebase
- [ ] Formatting conventions followed
- [ ] Code examples properly formatted
- [ ] Cross-references to related classes/methods

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Documentation Generation Request

Please generate comprehensive JavaDoc documentation for this Java project following this protocol:

## Phase 1: Analysis & Style Selection

1. **Analyze Existing Code**
   - Inventory all packages, classes, and public methods
   - Identify existing JavaDoc patterns
   - Note special documentation requirements
   - Review inheritance hierarchies

2. **Determine Documentation Style**
   Use **JavaDoc standard** with proper HTML formatting.

3. **Review Type Definitions**
   - Check generic type usage
   - Ensure JavaDoc complements type signatures
   - Document complex type relationships

## Phase 2: Package-Level Documentation

For each package, create comprehensive documentation:

### Package Documentation Template (package-info.java)
```java
/**
 * [One-line summary of package purpose]
 *
 * <p>[Detailed description of package functionality, scope, and use cases.
 * Include key concepts, main responsibilities, and intended usage.]</p>
 *
 * <h2>Key Classes</h2>
 * <ul>
 *   <li>{@link ClassName1} - Brief description</li>
 *   <li>{@link ClassName2} - Brief description</li>
 * </ul>
 *
 * <h2>Usage Example</h2>
 * <pre>{@code
 * import com.example.package.*;
 *
 * MainClass instance = new MainClass(param1, param2);
 * Result result = instance.process();
 * }</pre>
 *
 * <h2>Dependencies</h2>
 * <ul>
 *   <li>org.apache.commons:commons-lang3:3.12.0 - String utilities</li>
 *   <li>com.google.guava:guava:32.0.0 - Collections utilities</li>
 * </ul>
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @version 1.0.0
 * @since 1.0.0
 */
package com.example.package;
```

## Phase 3: Class/Interface Documentation

For each class and interface, document:

### Class Documentation Template
```java
/**
 * [One-line summary of class purpose]
 *
 * <p>[Detailed description of class responsibility, behavior, and usage.
 * Explain what problems this class solves and how it fits into the
 * overall architecture.]</p>
 *
 * <p>This class is thread-safe / not thread-safe. [Explain thread safety]</p>
 *
 * <h2>Example Usage</h2>
 * <pre>{@code
 * // Basic usage example
 * ExampleClass obj = new ExampleClass("value");
 * Result result = obj.process();
 * System.out.println(result.getValue()); // prints: processed_value
 * }</pre>
 *
 * <pre>{@code
 * // Advanced usage with builder pattern
 * ExampleClass obj = new ExampleClass.Builder()
 *     .setValue("value")
 *     .setVerbose(true)
 *     .setMaxRetries(3)
 *     .build();
 * Result result = obj.processAsync().get();
 * }</pre>
 *
 * @param <T> the type of elements processed by this class
 * @see RelatedClass
 * @see <a href="https://docs.example.com/classes">Documentation</a>
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @version 1.0.0
 * @since 1.0.0
 */
public class ExampleClass<T> {
    // Implementation
}
```

### Interface Documentation Template
```java
/**
 * [One-line summary of interface contract]
 *
 * <p>[Detailed description of what implementations must provide.
 * Explain the contract, invariants, and expected behavior.]</p>
 *
 * <p><strong>Implementation Requirements:</strong></p>
 * <ul>
 *   <li>Implementations must be thread-safe</li>
 *   <li>Methods must not return null unless documented</li>
 *   <li>Exceptions must be properly documented</li>
 * </ul>
 *
 * <h2>Example Implementation</h2>
 * <pre>{@code
 * public class MyProcessor implements Processor<String> {
 *     @Override
 *     public String process(String input) {
 *         return input.toUpperCase();
 *     }
 * }
 * }</pre>
 *
 * @param <T> the type of elements to process
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @since 1.0.0
 */
public interface Processor<T> {
    /**
     * Process the given input element.
     *
     * @param input the element to process, must not be null
     * @return the processed element, never null
     * @throws ProcessingException if processing fails
     */
    T process(T input) throws ProcessingException;
}
```

## Phase 4: Method Documentation

For each method, document:

### Method Documentation Template
```java
/**
 * [One-line summary of what method does]
 *
 * <p>[Detailed description of method behavior, algorithm, and usage.
 * Explain the problem it solves and any important implementation details.]</p>
 *
 * <p>This method is thread-safe and can be called concurrently.</p>
 *
 * @param param1 Description of param1. Include constraints, expected
 *               format, or valid values. Can span multiple lines.
 * @param param2 Description of param2. Explain what the parameter
 *               controls or represents.
 * @param param3 Description of optional param. Explain behavior when
 *               null vs when provided. Defaults to empty list if null.
 *
 * @return Description of return value structure. For complex returns,
 *         document the object properties and their meanings.
 *         Returns a Result object containing:
 *         <ul>
 *           <li>status - Success/failure status</li>
 *           <li>data - The processed result</li>
 *           <li>metadata - Additional information</li>
 *         </ul>
 *
 * @throws IllegalArgumentException if param1 is null or empty
 * @throws IllegalStateException if object is not initialized
 * @throws ProcessingException if processing fails
 *
 * @see #relatedMethod(String)
 * @see OtherClass#method(String, int)
 *
 * @since 1.0.0
 * @deprecated Use {@link #newMethod(String, int, List)} instead.
 *             This method will be removed in version 2.0.
 */
public Result complexMethod(String param1, int param2, List<String> param3)
        throws ProcessingException {
    // Implementation
}
```

### Constructor Documentation
```java
/**
 * Constructs a new ExampleClass with the specified parameters.
 *
 * <p>Creates and initializes all internal data structures. This constructor
 * performs validation and will throw if parameters are invalid.</p>
 *
 * @param value the initial value, must not be null or empty
 * @param options configuration options for this instance. If null,
 *                default options will be used.
 *
 * @throws IllegalArgumentException if value is null or empty
 * @throws NullPointerException if value is null
 *
 * @see Builder
 */
public ExampleClass(String value, Options options) {
    // Implementation
}
```

## Phase 5: Special Cases

### Generic Methods
```java
/**
 * Process a collection of items using the provided transformer.
 *
 * <p>This method applies the transformer to each element in the input
 * collection and returns a new collection with the results. The original
 * collection is not modified.</p>
 *
 * @param <I> the type of input elements
 * @param <O> the type of output elements
 * @param items the collection to process, must not be null
 * @param transformer the transformation function, must not be null
 * @return a new collection containing transformed elements, never null
 * @throws NullPointerException if items or transformer is null
 * @throws ProcessingException if transformation fails
 *
 * @see Transformer
 */
public <I, O> List<O> transform(Collection<I> items,
                                 Transformer<I, O> transformer)
        throws ProcessingException {
    // Implementation
}
```

### Builder Pattern
```java
/**
 * Builder for creating {@link ExampleClass} instances.
 *
 * <p>This builder provides a fluent API for constructing ExampleClass
 * objects with optional parameters. All builder methods return {@code this}
 * to enable method chaining.</p>
 *
 * <h2>Example Usage</h2>
 * <pre>{@code
 * ExampleClass obj = new ExampleClass.Builder()
 *     .setValue("test")
 *     .setVerbose(true)
 *     .setMaxRetries(5)
 *     .build();
 * }</pre>
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @since 1.0.0
 */
public static class Builder {
    /**
     * Sets the value for this builder.
     *
     * @param value the value to set, must not be null
     * @return this builder instance for method chaining
     * @throws IllegalArgumentException if value is null or empty
     */
    public Builder setValue(String value) {
        // Implementation
        return this;
    }

    /**
     * Builds and returns a new ExampleClass instance.
     *
     * <p>All required parameters must be set before calling this method.</p>
     *
     * @return a new ExampleClass configured with this builder's parameters
     * @throws IllegalStateException if required parameters are not set
     */
    public ExampleClass build() {
        // Implementation
    }
}
```

### Enum Documentation
```java
/**
 * Defines the status of a processing operation.
 *
 * <p>Each status represents a distinct state in the processing lifecycle.
 * Status transitions follow a specific order: PENDING -> PROCESSING ->
 * (SUCCESS | FAILURE).</p>
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @since 1.0.0
 */
public enum ProcessingStatus {
    /**
     * Operation is pending and has not started yet.
     */
    PENDING,

    /**
     * Operation is currently being processed.
     */
    PROCESSING,

    /**
     * Operation completed successfully.
     */
    SUCCESS,

    /**
     * Operation failed with an error.
     */
    FAILURE;

    /**
     * Checks if this status represents a terminal state.
     *
     * @return true if status is SUCCESS or FAILURE, false otherwise
     */
    public boolean isTerminal() {
        return this == SUCCESS || this == FAILURE;
    }
}
```

### Exception Documentation
```java
/**
 * Exception thrown when data processing fails.
 *
 * <p>This exception indicates a recoverable processing error. Clients
 * may retry the operation or handle the error gracefully. The exception
 * message provides details about the failure.</p>
 *
 * <h2>Common Causes</h2>
 * <ul>
 *   <li>Invalid input format</li>
 *   <li>Resource temporarily unavailable</li>
 *   <li>Processing timeout</li>
 * </ul>
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @see Processor
 * @since 1.0.0
 */
public class ProcessingException extends Exception {
    /**
     * Constructs a new processing exception with the specified detail message.
     *
     * @param message the detail message explaining the error
     */
    public ProcessingException(String message) {
        super(message);
    }

    /**
     * Constructs a new processing exception with message and cause.
     *
     * @param message the detail message
     * @param cause the underlying cause of this exception
     */
    public ProcessingException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

### Field Documentation
```java
/**
 * The maximum number of retry attempts for failed operations.
 *
 * <p>This value is used by {@link #retryOperation(Operation)} to determine
 * how many times to retry before giving up. The default value is 3.</p>
 *
 * @see #retryOperation(Operation)
 */
private static final int MAX_RETRIES = 3;

/**
 * Current processing status.
 *
 * <p>This field is volatile to ensure visibility across threads.
 * Access should be synchronized when both reading and writing.</p>
 */
private volatile ProcessingStatus status;
```

## Phase 6: Documentation Quality Checks

Verify each JavaDoc comment meets these criteria:

### Completeness
- [ ] Purpose clearly stated
- [ ] All parameters documented
- [ ] Return value documented
- [ ] Exceptions documented with @throws
- [ ] Examples provided for non-trivial methods

### Clarity
- [ ] Uses clear, concise language
- [ ] Avoids jargon or explains technical terms
- [ ] Follows consistent tense (present tense for descriptions)
- [ ] HTML formatting used appropriately

### Examples
- [ ] Examples are compilable and runnable
- [ ] Examples cover common use cases
- [ ] Complex methods have multiple examples
- [ ] Examples demonstrate best practices

### Formatting
- [ ] Consistent style throughout codebase
- [ ] Proper HTML tags for formatting
- [ ] Code blocks use {@code} or <pre>{@code}</pre>
- [ ] Cross-references use {@link} syntax

## Phase 7: Documentation Generation

After JavaDoc comments are complete:

1. **Generate API Documentation**
   ```bash
   # Using javadoc command
   javadoc -d docs/api \
           -sourcepath src/main/java \
           -subpackages com.example \
           -author -version \
           -private

   # Using Maven
   mvn javadoc:javadoc

   # Using Gradle
   gradle javadoc
   ```

2. **Verify Documentation Coverage**
   ```bash
   # Using Maven CheckStyle plugin
   mvn checkstyle:check

   # Using SpotBugs
   mvn spotbugs:check
   ```

3. **Validate JavaDoc**
   ```bash
   # Validate with doclint (Java 8+)
   javadoc -Xdoclint:all -d /tmp/javadoc src/main/java/**/*.java
   ```

## Output Format

Please provide JavaDoc documentation in this format:

### File-by-File Report
```markdown
## Package: com.example.package

### Package Documentation (package-info.java)
[Generated package JavaDoc]

### Class: ClassName
[Generated class JavaDoc]

### Method: methodName
[Generated method JavaDoc]

---
```

### Summary Report
```markdown
## JavaDoc Generation Summary

**Packages Processed**: [count]
**Classes Documented**: [count]
**Interfaces Documented**: [count]
**Methods Documented**: [count]
**Fields Documented**: [count]

**Documentation Style**: JavaDoc Standard
**HTML Version**: HTML5
**Examples Added**: [count]

**Coverage Metrics**:
- Package coverage: [X%]
- Class coverage: [X%]
- Method coverage: [X%]
- Overall coverage: [X%]

**Quality Checks**:
- [ ] All public interfaces documented
- [ ] Consistent style throughout
- [ ] Examples provided where appropriate
- [ ] Cross-references valid
- [ ] HTML formatting correct
- [ ] Documentation builds without warnings
```

## JavaDoc Style Guide Reference

### Best Practices

1. **First Sentence is Summary**
   - First sentence should be a concise summary
   - Ends at first period followed by space or end of paragraph
   - Shows in method summaries and package lists

2. **Use HTML Formatting**
   - `<p>` for paragraphs
   - `<pre>{@code}</pre>` for code blocks
   - `<ul>/<ol>` for lists
   - `<strong>/<em>` for emphasis

3. **Provide Context**
   - Explain why, not just what
   - Link to related methods/classes with {@link}
   - Note thread safety considerations
   - Document null handling

4. **Document Contracts**
   - Pre-conditions and post-conditions
   - Side effects
   - Thread safety guarantees
   - Immutability

5. **Maintain Consistency**
   - Use same style throughout project
   - Follow Sun/Oracle conventions
   - Update JavaDoc when code changes

## Tools & Validation

```xml
<!-- Maven POM configuration -->
<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-javadoc-plugin</artifactId>
            <version>3.6.0</version>
            <configuration>
                <author>true</author>
                <version>true</version>
                <show>private</show>
                <doclint>all</doclint>
            </configuration>
        </plugin>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-checkstyle-plugin</artifactId>
            <version>3.3.0</version>
            <configuration>
                <configLocation>checkstyle.xml</configLocation>
            </configuration>
        </plugin>
    </plugins>
</build>
```

## Common Mistakes to Avoid

1. **Don't duplicate method signature in prose**
   - Bad: `This method takes a String param1 and int param2 and returns Result`
   - Good: `Processes the input using the specified configuration`

2. **Don't use imperative mood for methods**
   - Bad: `Process the data...`
   - Good: `Processes the data...`

3. **Don't omit important details**
   - Document null handling explicitly
   - Explain thread safety
   - Note performance implications
   - Document side effects

4. **Don't forget HTML escaping**
   - Use `{@code}` for code snippets
   - Escape HTML characters in descriptions
   - Use `{@literal}` for literal text with special chars

5. **Don't forget to update JavaDoc**
   - Keep in sync with code changes
   - Update examples when behavior changes
   - Remove obsolete @deprecated tags
   - Update @since versions appropriately
~~~

## Output Format Specifications

The generated JavaDoc should:
- Follow JavaDoc standard conventions
- Include all required tags based on element type
- Provide compilable examples where appropriate
- Use proper HTML formatting
- Include cross-references using {@link}
- Document thread safety and null handling
- Pass javadoc tool without warnings
- Generate properly formatted HTML documentation
