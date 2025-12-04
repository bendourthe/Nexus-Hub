---
template_id: csharp_docstrings
template_name: Docstrings - C#
version: 1.0.0
last_updated: 2025-12-03
language: C#
category: documentation
phase: docstrings
difficulty: beginner
estimated_time_hours: 2-3
prerequisites: []
tools:
  - NUnit (4.2.2)
  - xUnit
  - MSTest
tags:
  - documentation
  - documentation
  - c#
---
# C# Documentation Generation (XML Documentation Comments)

## Objective
Generate comprehensive, standards-compliant XML documentation comments for all public interfaces (namespaces, classes, methods) that clearly document purpose, parameters, return values, exceptions, and provide usage examples with proper type information compatible with IntelliSense and DocFX.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/docstrings/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/docstrings/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Namespace-Level Documentation

- [ ] Namespace purpose and scope clearly explained

- [ ] Key classes and interfaces listed

- [ ] Dependencies and requirements noted

- [ ] Usage examples provided

- [ ] Author information included

### Class/Interface Documentation

- [ ] Class purpose and responsibility documented

- [ ] All public properties described with types

- [ ] Constructor parameters documented

- [ ] Class-level examples provided

- [ ] Inheritance relationships explained

- [ ] Generic type parameters documented

### Method Documentation

- [ ] Method purpose clearly stated

- [ ] All parameters documented with types and descriptions

- [ ] Return values documented with types

- [ ] Exceptions documented with `<exception>`

- [ ] Thread safety documented

- [ ] Usage examples for complex methods

### XML Documentation Integration

- [ ] XML comments complement type signatures

- [ ] Generic type usage clarified with `<typeparam>`

- [ ] Null handling documented with nullable reference types

- [ ] CREF links to related types

### Documentation Style

- [ ] Consistent XML comment style throughout codebase

- [ ] Formatting conventions followed

- [ ] Code examples properly formatted

- [ ] Cross-references using `<see cref=""/>` tags

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# XML Documentation Generation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/docstrings"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please generate comprehensive XML documentation comments for this C# project following this protocol:

## Phase 1: Analysis & Style Selection

1. **Analyze Existing Code**
   - Inventory all namespaces, classes, and public methods
   - Identify existing XML documentation patterns
   - Note special documentation requirements (nullable reference types, etc.)
   - Review inheritance hierarchies and interfaces

2. **Determine Documentation Style**
   Use **C# XML Documentation Comments** standard compatible with IntelliSense and DocFX.

3. **Review Type Definitions**
   - Check generic type usage
   - Ensure XML comments complement type signatures
   - Document nullable reference types

## Phase 2: Namespace-Level Documentation

### Namespace Documentation Template
```csharp
/// <summary>
/// [One-line summary of namespace purpose]
/// </summary>
/// <remarks>
/// <para>
/// Detailed description of namespace functionality, scope, and use cases.
/// Include key concepts, main responsibilities, and intended usage.
/// </para>
/// <para><strong>Key Classes:</strong></para>
/// <list type="bullet">
/// <item><description><see cref="ClassName1"/> - Brief description</description></item>
/// <item><description><see cref="ClassName2"/> - Brief description</description></item>
/// </list>
/// <example>
/// <code>
/// using Example.Namespace;
///
/// var instance = new MainClass(param1, param2);
/// var result = instance.Process();
/// </code>
/// </example>
/// </remarks>
namespace Example.Namespace
{
    // Classes and interfaces
}
```

## Phase 3: Class/Interface Documentation

### Class Documentation Template
```csharp
/// <summary>
/// [One-line summary of class purpose]
/// </summary>
/// <remarks>
/// <para>
/// Detailed description of class responsibility, behavior, and usage.
/// Explain what problems this class solves and how it fits into the
/// overall architecture.
/// </para>
/// <para>
/// This class is thread-safe / not thread-safe. [Explain thread safety]
/// </para>
/// </remarks>
/// <typeparam name="T">The type of elements processed by this class</typeparam>
/// <example>
/// <para><strong>Basic usage example:</strong></para>
/// <code>
/// var obj = new ExampleClass&lt;string&gt;("value");
/// var result = obj.Process();
/// Console.WriteLine(result.Value); // prints: processed_value
/// </code>
/// <para><strong>Advanced usage with configuration:</strong></para>
/// <code>
/// var obj = new ExampleClass&lt;string&gt;("value", new Options
/// {
///     Verbose = true,
///     MaxRetries = 3
/// });
/// var result = await obj.ProcessAsync();
/// </code>
/// </example>
/// <seealso cref="RelatedClass"/>
/// <seealso href="https://docs.example.com/classes">Documentation</seealso>
public class ExampleClass<T>
{
    // Implementation
}
```

### Interface Documentation Template
```csharp
/// <summary>
/// [One-line summary of interface contract]
/// </summary>
/// <remarks>
/// <para>
/// Detailed description of what implementations must provide.
/// Explain the contract, invariants, and expected behavior.
/// </para>
/// <para><strong>Implementation Requirements:</strong></para>
/// <list type="bullet">
/// <item><description>Implementations must be thread-safe</description></item>
/// <item><description>Methods must not return null unless documented</description></item>
/// <item><description>Exceptions must be properly documented</description></item>
/// </list>
/// </remarks>
/// <typeparam name="T">The type of elements to process</typeparam>
/// <example>
/// <code>
/// public class MyProcessor : IProcessor&lt;string&gt;
/// {
///     public string Process(string input)
///     {
///         return input.ToUpper();
///     }
/// }
/// </code>
/// </example>
public interface IProcessor<T>
{
    /// <summary>
    /// Process the given input element.
    /// </summary>
    /// <param name="input">The element to process, must not be null</param>
    /// <returns>The processed element, never null</returns>
    /// <exception cref="ArgumentNullException">Thrown when input is null</exception>
    /// <exception cref="ProcessingException">Thrown when processing fails</exception>
    T Process(T input);
}
```

## Phase 4: Method Documentation

### Method Documentation Template
```csharp
/// <summary>
/// [One-line summary of what method does]
/// </summary>
/// <remarks>
/// <para>
/// Detailed description of method behavior, algorithm, and usage.
/// Explain the problem it solves and any important implementation details.
/// </para>
/// <para>
/// This method is thread-safe and can be called concurrently.
/// </para>
/// </remarks>
/// <param name="param1">
/// Description of param1. Include constraints, expected format, or valid values.
/// Can span multiple lines.
/// </param>
/// <param name="param2">
/// Description of param2. Explain what the parameter controls or represents.
/// </param>
/// <param name="param3">
/// Description of optional param. Explain behavior when null vs when provided.
/// Defaults to empty list if null.
/// </param>
/// <returns>
/// Description of return value structure. For complex returns, document the
/// object properties:
/// <list type="bullet">
/// <item><description>Status - Success/failure status</description></item>
/// <item><description>Data - The processed result</description></item>
/// <item><description>Metadata - Additional information</description></item>
/// </list>
/// </returns>
/// <exception cref="ArgumentNullException">
/// Thrown when <paramref name="param1"/> is null or empty
/// </exception>
/// <exception cref="InvalidOperationException">
/// Thrown when object is not initialized
/// </exception>
/// <exception cref="ProcessingException">
/// Thrown when processing fails
/// </exception>
/// <example>
/// <code>
/// var result = await ComplexMethod("input", 42, new List&lt;string&gt;());
/// Console.WriteLine(result.Status);
/// </code>
/// </example>
/// <seealso cref="RelatedMethod(string)"/>
/// <seealso cref="OtherClass.Method(string, int)"/>
public async Task<Result> ComplexMethod(
    string param1,
    int param2,
    List<string>? param3 = null)
{
    // Implementation
}
```

### Constructor Documentation
```csharp
/// <summary>
/// Initializes a new instance of the <see cref="ExampleClass"/> class
/// with the specified parameters.
/// </summary>
/// <remarks>
/// Creates and initializes all internal data structures. This constructor
/// performs validation and will throw if parameters are invalid.
/// </remarks>
/// <param name="value">The initial value, must not be null or empty</param>
/// <param name="options">
/// Configuration options for this instance. If null, default options will be used.
/// </param>
/// <exception cref="ArgumentNullException">
/// Thrown when <paramref name="value"/> is null
/// </exception>
/// <exception cref="ArgumentException">
/// Thrown when <paramref name="value"/> is empty
/// </exception>
/// <example>
/// <code>
/// var obj = new ExampleClass("test", new Options { Verbose = true });
/// </code>
/// </example>
public ExampleClass(string value, Options? options = null)
{
    // Implementation
}
```

## Phase 5: Special Cases

### Generic Methods
```csharp
/// <summary>
/// Process a collection of items using the provided transformer function.
/// </summary>
/// <remarks>
/// <para>
/// This method applies the transformer to each element in the input
/// collection and returns a new collection with the results. The original
/// collection is not modified.
/// </para>
/// </remarks>
/// <typeparam name="TInput">The type of input elements</typeparam>
/// <typeparam name="TOutput">The type of output elements</typeparam>
/// <param name="items">The collection to process, must not be null</param>
/// <param name="transformer">The transformation function, must not be null</param>
/// <returns>A new collection containing transformed elements, never null</returns>
/// <exception cref="ArgumentNullException">
/// Thrown when <paramref name="items"/> or <paramref name="transformer"/> is null
/// </exception>
/// <exception cref="ProcessingException">
/// Thrown when transformation fails
/// </exception>
/// <example>
/// <code>
/// var numbers = new List&lt;int&gt; { 1, 2, 3 };
/// var strings = Transform(numbers, x => x.ToString());
/// </code>
/// </example>
public List<TOutput> Transform<TInput, TOutput>(
    IEnumerable<TInput> items,
    Func<TInput, TOutput> transformer)
{
    // Implementation
}
```

### Property Documentation
```csharp
/// <summary>
/// Gets or sets the maximum number of retry attempts for failed operations.
/// </summary>
/// <value>
/// An integer representing the maximum retry count. Must be between 0 and 10.
/// Default value is 3.
/// </value>
/// <exception cref="ArgumentOutOfRangeException">
/// Thrown when value is less than 0 or greater than 10
/// </exception>
/// <example>
/// <code>
/// var processor = new Processor();
/// processor.MaxRetries = 5;
/// </code>
/// </example>
public int MaxRetries { get; set; } = 3;

/// <summary>
/// Gets the current processing status.
/// </summary>
/// <value>
/// A <see cref="ProcessingStatus"/> indicating the current state.
/// This property is thread-safe.
/// </value>
/// <seealso cref="ProcessingStatus"/>
public ProcessingStatus Status { get; private set; }
```

### Enum Documentation
```csharp
/// <summary>
/// Defines the status of a processing operation.
/// </summary>
/// <remarks>
/// <para>
/// Each status represents a distinct state in the processing lifecycle.
/// Status transitions follow a specific order: Pending → Processing → (Success | Failure).
/// </para>
/// </remarks>
[Flags]
public enum ProcessingStatus
{
    /// <summary>
    /// Operation is pending and has not started yet.
    /// </summary>
    Pending = 0,

    /// <summary>
    /// Operation is currently being processed.
    /// </summary>
    Processing = 1,

    /// <summary>
    /// Operation completed successfully.
    /// </summary>
    Success = 2,

    /// <summary>
    /// Operation failed with an error.
    /// </summary>
    Failure = 4
}
```

### Exception Documentation
```csharp
/// <summary>
/// Exception thrown when data processing fails.
/// </summary>
/// <remarks>
/// <para>
/// This exception indicates a recoverable processing error. Clients may retry
/// the operation or handle the error gracefully. The exception message provides
/// details about the failure.
/// </para>
/// <para><strong>Common Causes:</strong></para>
/// <list type="bullet">
/// <item><description>Invalid input format</description></item>
/// <item><description>Resource temporarily unavailable</description></item>
/// <item><description>Processing timeout</description></item>
/// </list>
/// </remarks>
/// <seealso cref="IProcessor{T}"/>
[Serializable]
public class ProcessingException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessingException"/> class.
    /// </summary>
    public ProcessingException() : base() { }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessingException"/> class
    /// with a specified error message.
    /// </summary>
    /// <param name="message">The message that describes the error</param>
    public ProcessingException(string message) : base(message) { }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessingException"/> class
    /// with a specified error message and a reference to the inner exception.
    /// </summary>
    /// <param name="message">The error message</param>
    /// <param name="innerException">The exception that caused this exception</param>
    public ProcessingException(string message, Exception innerException)
        : base(message, innerException) { }
}
```

### Event Documentation
```csharp
/// <summary>
/// Occurs when the processing operation completes.
/// </summary>
/// <remarks>
/// <para>
/// This event is raised after processing completes, regardless of success or failure.
/// Subscribers should check the <see cref="ProcessingEventArgs.Status"/> property
/// to determine the outcome.
/// </para>
/// </remarks>
/// <example>
/// <code>
/// processor.ProcessingCompleted += (sender, args) =>
/// {
///     Console.WriteLine($"Processing {args.Status}");
/// };
/// </code>
/// </example>
public event EventHandler<ProcessingEventArgs>? ProcessingCompleted;
```

## Phase 6: Documentation Quality Checks

Verify each XML comment meets these criteria:

### Completeness

- [ ] Purpose clearly stated in `<summary>`

- [ ] All parameters documented with `<param>`

- [ ] Return value documented with `<returns>`

- [ ] Exceptions documented with `<exception>`

- [ ] Examples provided in `<example>` for non-trivial methods

### Clarity

- [ ] Uses clear, concise language

- [ ] Avoids jargon or explains technical terms

- [ ] Follows consistent tense

- [ ] XML tags properly formatted

### Examples

- [ ] Examples are compilable

- [ ] Examples cover common use cases

- [ ] Complex methods have multiple examples

- [ ] Examples demonstrate best practices

### Formatting

- [ ] Consistent style throughout codebase

- [ ] Proper XML structure with paired tags

- [ ] Code blocks use `<code>` tags

- [ ] Cross-references use `<see cref=""/>` or `<seealso cref=""/>`

## Phase 7: Documentation Generation

After XML comments are complete:

1. **Generate API Documentation**
   ```bash
   # Using DocFX
   docfx init
   docfx build docfx.json
   docfx serve _site

   # Using Sandcastle Help File Builder (SHFB)
   # Use Visual Studio or MSBuild with SHFB project

   # Build XML documentation file
   dotnet build /p:GenerateDocumentationFile=true
   ```

2. **Project Configuration**
   ```xml
   <!-- In .csproj file -->
   <PropertyGroup>
     <GenerateDocumentationFile>true</GenerateDocumentationFile>
     <DocumentationFile>bin\$(Configuration)\$(TargetFramework)\$(AssemblyName).xml</DocumentationFile>
     <NoWarn>$(NoWarn);1591</NoWarn> <!-- Suppress missing XML comment warnings -->
   </PropertyGroup>
   ```

3. **Verify Documentation**
   ```bash
   # Check for missing documentation
   dotnet build /p:TreatWarningsAsErrors=true /p:WarningsAsErrors=CS1591
   ```

## Output Format

### Summary Report
```markdown
## XML Documentation Generation Summary

**Namespaces Processed**: [count]
**Classes Documented**: [count]
**Interfaces Documented**: [count]
**Methods Documented**: [count]
**Properties Documented**: [count]
**Events Documented**: [count]

**Documentation Style**: C# XML Comments
**IntelliSense Compatible**: Yes
**DocFX Compatible**: Yes
**Examples Added**: [count]

**Coverage Metrics**:

- Namespace coverage: [X%]

- Class coverage: [X%]

- Method coverage: [X%]

- Overall coverage: [X%]

**Quality Checks**:

- [ ] All public members documented

- [ ] Consistent style throughout

- [ ] Examples provided where appropriate

- [ ] CREF links valid

- [ ] XML structure valid

- [ ] Documentation builds without errors
```

## Best Practices

1. **First Sentence is Summary**
   - Keep `<summary>` concise (one or two sentences)
   - Use `<remarks>` for detailed explanations
   - Summary shows in IntelliSense popup

2. **Use Proper XML Tags**
   - `<para>` for paragraphs
   - `<code>` for code snippets
   - `<list type="bullet|number|table">` for lists
   - `<c>` for inline code references

3. **Cross-Reference with CREF**
   - Use `<see cref=""/>` for inline references
   - Use `<seealso cref=""/>` for related items
   - Use `<paramref name=""/>` to reference parameters

4. **Document Null Handling**
   - Explicitly document nullable parameters and returns
   - Use nullable reference types (`T?`)
   - Document null behavior in `<param>` and `<returns>`

5. **Maintain Consistency**
   - Use same style throughout project
   - Follow Microsoft documentation conventions
   - Update XML comments when code changes

## Common Mistakes to Avoid

1. **Don't duplicate method signature**
   - Bad: `This method takes string param1 and returns Result`
   - Good: `Processes the input using the specified configuration`

2. **Don't forget to document exceptions**
   - Always use `<exception cref="ExceptionType">`
   - Explain when and why the exception is thrown
   - Reference parameters using `<paramref>`

3. **Don't use invalid XML**
   - Always close tags properly
   - Escape XML characters: `&lt;`, `&gt;`, `&amp;`
   - Use `<![CDATA[...]]>` for complex code examples

4. **Don't forget IntelliSense compatibility**
   - Keep `<summary>` concise for tooltip display
   - Put detailed info in `<remarks>`
   - Test IntelliSense display in Visual Studio

5. **Don't forget to enable XML documentation**
   - Set `GenerateDocumentationFile` to true in .csproj
   - Configure warnings appropriately
   - Include XML files in NuGet packages

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/docstrings/generated_docs
mkdir -p ${OUTPUT_DIR}/docstrings/templates
mkdir -p ${OUTPUT_DIR}/docstrings/assets
mkdir -p ${OUTPUT_DIR}/docstrings/exports
```

**Save files as follows**:


- Templates → `documentation/docstrings/templates/`

- Assets → `documentation/docstrings/assets/`

- Exports → `documentation/docstrings/exports/`

Replace `{phase_name}` with the specific phase (docstrings, comments, user_docs, technical_docs, api_docs, or sbom).

---

## Output Format Specifications

The generated XML documentation should:

- Follow C# XML documentation comments standard

- Be compatible with IntelliSense

- Generate valid documentation with DocFX/Sandcastle

- Include proper XML structure with paired tags

- Use CREF for cross-references

- Document nullable reference types

- Pass build without XML documentation warnings

- Generate comprehensive API documentation

~~~
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
