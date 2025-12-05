---
name: generate-docstrings
description: Generate comprehensive docstrings and inline documentation for all functions, classes, and modules with type hints and usage examples
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language (Python, JavaScript, Java, C#, Go, C, C++)
category: Documentation
priority: MEDIUM
tags: [documentation, docstrings, jsdoc, javadoc, xml-docs, godoc, doxygen, comments, type-hints]
template_sources:

  - documentation/docstrings/python_docstrings.md
  - documentation/docstrings/javascript_docstrings.md
  - documentation/docstrings/java_docstrings.md
  - documentation/docstrings/csharp_docstrings.md
  - documentation/docstrings/go_docstrings.md
  - documentation/docstrings/c_docstrings.md
  - documentation/docstrings/cpp_docstrings.md
---

# Generate Docstrings

Create comprehensive, standards-compliant docstrings and inline documentation for all public and private interfaces including functions, methods, classes, and modules with complete parameter descriptions, return values, exceptions, and usage examples.

## When to Use This Skill

Use this skill when you need to:
- Document all public APIs with comprehensive docstrings
- Add parameter descriptions and type information to functions
- Document class attributes and methods
- Create module-level documentation
- Add usage examples to complex functions
- Generate documentation for existing undocumented code
- Ensure consistency across documentation style
- Prepare code for documentation tools (Sphinx, JSDoc, JavaDoc, etc.)
- Meet documentation standards for code review or publication

## What This Skill Does

This skill generates language-appropriate docstrings and documentation:

### For All Languages
1. **Function/Method Documentation**
   - Purpose and behavior description
   - Parameter names, types, and descriptions
   - Return value types and descriptions
   - Exceptions/errors that can be raised
   - Usage examples for complex functions

2. **Class Documentation**
   - Class purpose and responsibility
   - Attribute descriptions with types
   - Constructor parameters
   - Method summaries
   - Usage patterns and examples

3. **Module Documentation**
   - Module purpose and contents
   - Public interface overview
   - Dependencies and requirements
   - Usage examples
   - Author and version information

4. **Type Information**
   - Type hints integration (Python, TypeScript)
   - Type annotations (Java, C#)
   - Parameter type documentation
   - Generic type parameters
   - Nullable/optional indicators

### Language-Specific Features

#### Python
- **Styles**: Google, NumPy, reStructuredText (Sphinx)
- **Type Hints**: PEP 484 type annotations
- **Tools**: Sphinx, pdoc, MkDocs
- **Examples**:
  ```python
  def process_data(items: List[Dict[str, Any]], threshold: float = 0.5) -> List[Dict[str, Any]]:
      """
      Process and filter data items based on threshold.

      Filters input items by comparing their score against the threshold value,
      returning only items that meet or exceed the threshold.

      Args:
          items: List of dictionaries containing data with 'score' key
          threshold: Minimum score value for inclusion (default: 0.5)

      Returns:
          List of filtered dictionaries meeting threshold criteria

      Raises:
          ValueError: If items list is empty or threshold is negative
          KeyError: If any item lacks 'score' key

      Example:
          >>> data = [{'id': 1, 'score': 0.8}, {'id': 2, 'score': 0.3}]
          >>> result = process_data(data, threshold=0.5)
          >>> len(result)
          1

      Authors:
          - Benjamin Dourthe (benjamin@adonamed.com)
      """
  ```

#### JavaScript/TypeScript
- **Format**: JSDoc, TSDoc
- **Type System**: TypeScript definitions
- **Tools**: JSDoc, TypeDoc, ESDoc
- **Examples**:
  ```javascript
  /**

   * Process and filter data items based on threshold.
   *

   * Filters input items by comparing their score against the threshold value,
   * returning only items that meet or exceed the threshold.
   *

   * @param {Array<Object>} items - List of objects containing data with 'score' property
   * @param {number} [threshold=0.5] - Minimum score value for inclusion
   * @returns {Array<Object>} Filtered array of objects meeting threshold criteria
   * @throws {Error} If items array is empty or threshold is negative
   *

   * @example
   * const data = [{id: 1, score: 0.8}, {id: 2, score: 0.3}];
   * const result = processData(data, 0.5);
   * console.log(result.length); // 1
   *

   * @author Benjamin Dourthe <benjamin@adonamed.com>
   * @version 1.0.0
   */
  function processData(items, threshold = 0.5) {
      // Implementation
  }
  ```

  ```typescript
  /**

   * Process and filter data items based on threshold.
   *

   * @template T - Type of data items
   * @param items - List of typed objects with score property
   * @param threshold - Minimum score value for inclusion
   * @returns Filtered array meeting threshold criteria
   */
  function processData<T extends { score: number }>(
      items: T[],
      threshold: number = 0.5
  ): T[] {
      // Implementation
  }
  ```

#### Java
- **Format**: JavaDoc
- **Annotations**: @param, @return, @throws, @see
- **Tools**: JavaDoc, Asciidoctor
- **Examples**:
  ```java
  /**

   * Process and filter data items based on threshold.
   *

   * <p>Filters input items by comparing their score against the threshold value,
   * returning only items that meet or exceed the threshold.</p>
   *

   * @param items List of data items with score property
   * @param threshold Minimum score value for inclusion (must be non-negative)
   * @return List of filtered items meeting threshold criteria
   * @throws IllegalArgumentException if items is null or empty, or threshold is negative
   * @throws NullPointerException if any item in list is null
   *

   * @example
   * <pre>{@code
   * List<DataItem> data = Arrays.asList(
   *     new DataItem(1, 0.8),
   *     new DataItem(2, 0.3)
   * );
   * List<DataItem> result = processData(data, 0.5);
   * assert result.size() == 1;
   * }</pre>
   *

   * @author Benjamin Dourthe
   * @version 1.0.0
   * @since 1.0
   * @see DataItem
   */
  public List<DataItem> processData(List<DataItem> items, double threshold) {
      // Implementation
  }
  ```

#### C#
- **Format**: XML Documentation Comments
- **Tags**: `<summary>`, `<param>`, `<returns>`, `<exception>`
- **Tools**: DocFX, Sandcastle, Visual Studio IntelliSense
- **Examples**:
  ```csharp
  /// <summary>
  /// Process and filter data items based on threshold.
  /// </summary>
  /// <remarks>
  /// Filters input items by comparing their score against the threshold value,
  /// returning only items that meet or exceed the threshold.
  /// </remarks>
  /// <param name="items">List of data items with Score property</param>
  /// <param name="threshold">Minimum score value for inclusion (default: 0.5)</param>
  /// <returns>IEnumerable of filtered items meeting threshold criteria</returns>
  /// <exception cref="ArgumentNullException">Thrown when items is null</exception>
  /// <exception cref="ArgumentException">Thrown when items is empty or threshold is negative</exception>
  /// <example>
  /// <code>
  /// var data = new List&lt;DataItem&gt; {
  ///     new DataItem { Id = 1, Score = 0.8 },
  ///     new DataItem { Id = 2, Score = 0.3 }
  /// };
  /// var result = ProcessData(data, 0.5);
  /// Console.WriteLine(result.Count()); // Output: 1
  /// </code>
  /// </example>
  /// <author>Benjamin Dourthe</author>
  /// <version>1.0.0</version>
  public IEnumerable<DataItem> ProcessData(List<DataItem> items, double threshold = 0.5)
  {
      // Implementation
  }
  ```

#### Go
- **Format**: Godoc
- **Conventions**: Comment directly before declaration
- **Tools**: godoc, pkgsite
- **Examples**:
  ```go
  // ProcessData filters data items based on threshold.
  //
  // Filters input items by comparing their score against the threshold value,
  // returning only items that meet or exceed the threshold.
  //
  // Parameters:
  //   - items: Slice of DataItem structs with Score field
  //   - threshold: Minimum score value for inclusion
  //
  // Returns:
  //   - Filtered slice of DataItem meeting threshold criteria
  //   - Error if items is empty or threshold is negative
  //
  // Example:
  //   data := []DataItem{
  //       {ID: 1, Score: 0.8},
  //       {ID: 2, Score: 0.3},
  //   }
  //   result, err := ProcessData(data, 0.5)
  //   if err != nil {
  //       log.Fatal(err)
  //   }
  //   fmt.Println(len(result)) // Output: 1
  //
  // Author: Benjamin Dourthe <benjamin@adonamed.com>
  func ProcessData(items []DataItem, threshold float64) ([]DataItem, error) {
      // Implementation
  }
  ```

#### C
- **Format**: Doxygen
- **Style**: JavaDoc-style or Qt-style
- **Tools**: Doxygen, GTK-Doc
- **Examples**:
  ```c
  /**

   * @brief Process and filter data items based on threshold.
   *

   * Filters input items by comparing their score against the threshold value,
   * returning only items that meet or exceed the threshold.
   *

   * @param items Array of data_item_t structures with score field
   * @param item_count Number of items in the array
   * @param threshold Minimum score value for inclusion
   * @param result_count Pointer to store count of filtered items
   * @return Pointer to newly allocated array of filtered items, or NULL on error
   *

   * @note Caller is responsible for freeing returned array with free()
   * @warning Returns NULL if items is NULL, item_count is 0, or threshold is negative
   *

   * @code
   * data_item_t data[] = {{1, 0.8}, {2, 0.3}};
   * size_t result_count;
   * data_item_t* result = process_data(data, 2, 0.5, &result_count);
   * if (result) {
   *     printf("Filtered count: %zu\n", result_count); // Output: 1
   *     free(result);
   * }
   * @endcode
   *

   * @author Benjamin Dourthe <benjamin@adonamed.com>
   * @version 1.0.0
   * @since 1.0
   */
  data_item_t* process_data(const data_item_t* items, size_t item_count,
                            double threshold, size_t* result_count);
  ```

#### C++
- **Format**: Doxygen with C++ extensions
- **Features**: Template documentation, concept documentation
- **Tools**: Doxygen, Breathe, Sphinx
- **Examples**:
  ```cpp
  /**

   * @brief Process and filter data items based on threshold.
   *

   * @tparam T Type of data items (must have score member)
   * @tparam Compare Comparison function type
   *

   * Filters input items by comparing their score against the threshold value,
   * returning only items that meet or exceed the threshold.
   *

   * @param items Vector of data items with score member
   * @param threshold Minimum score value for inclusion
   * @return std::vector<T> Filtered vector meeting threshold criteria
   *

   * @throws std::invalid_argument if items is empty or threshold is negative
   * @throws std::runtime_error if comparison operation fails
   *

   * @code{.cpp}
   * std::vector<DataItem> data = {{1, 0.8}, {2, 0.3}};
   * auto result = processData(data, 0.5);
   * std::cout << result.size() << std::endl; // Output: 1
   * @endcode
   *

   * @note This function uses move semantics for efficiency
   * @see DataItem
   * @author Benjamin Dourthe <benjamin@adonamed.com>
   * @version 1.0.0
   */
  template<typename T>
  requires HasScore<T>
  std::vector<T> processData(const std::vector<T>& items, double threshold) {
      // Implementation
  }
  ```

## Prerequisites

- Codebase with functions, classes, or modules requiring documentation
- Understanding of your code's purpose and behavior
- Knowledge of language-specific documentation standards
- Access to type information (if applicable)
- Documentation generation tool (optional: Sphinx, JSDoc, Doxygen, etc.)

## Instructions

### Step 1: Analyze Your Codebase

1. **Identify Undocumented Code**:
   ```bash
   # Python - find functions without docstrings
   grep -r "def " --include="*.py" | grep -v '"""'

   # JavaScript - find functions without JSDoc
   grep -r "function " --include="*.js" | grep -B1 -v "/\*\*"

   # Java - find methods without JavaDoc
   grep -r "public.*(" --include="*.java" | grep -B1 -v "/\*\*"
   ```

2. **Prioritize Documentation**:
   - Public APIs first
   - Complex functions second
   - Internal utilities third
   - Simple getters/setters last

3. **Determine Documentation Style**:
   - Python: Google style (recommended), NumPy, or Sphinx
   - JavaScript: JSDoc 3
   - TypeScript: TSDoc
   - Java: JavaDoc
   - C#: XML Documentation Comments
   - Go: Godoc conventions
   - C/C++: Doxygen

### Step 2: Invoke the Generate Docstrings Skill

For **Python** code:
```
"Use the generate-docstrings skill to create comprehensive docstrings for Python code.

Language: Python
Style: Google / NumPy / Sphinx
Scope: Module 'data_processor.py' / Entire 'src/' directory
Include: Type hints, parameter descriptions, return values, exceptions, examples
Type Hint Integration: Yes
Generate: Module docstrings, class docstrings, function docstrings"
```

For **JavaScript/TypeScript** code:
```
"Use the generate-docstrings skill for JavaScript/TypeScript documentation.

Language: JavaScript / TypeScript
Style: JSDoc / TSDoc
Scope: Module 'utils.js' / Directory 'src/services/'
Include: Parameter types, return types, examples, @throws tags
TypeScript: Full type definitions with generics
Generate: Function JSDoc, class JSDoc, module documentation"
```

For **Java** code:
```
"Use the generate-docstrings skill for Java class documentation.

Language: Java
Style: JavaDoc
Scope: Class 'DataProcessor.java' / Package 'com.example.services'
Include: Method documentation, parameter descriptions, @throws, @see tags, examples
Generate: Class JavaDoc, method JavaDoc, constructor documentation"
```

For **C#** code:
```
"Use the generate-docstrings skill for C# XML documentation.

Language: C#
Style: XML Documentation Comments
Scope: Class 'DataProcessor.cs' / Namespace 'MyApp.Services'
Include: Summary, remarks, param, returns, exception, example tags
IntelliSense: Yes (for IDE integration)
Generate: Class documentation, method documentation, property documentation"
```

For **Go** code:
```
"Use the generate-docstrings skill for Go package documentation.

Language: Go
Style: Godoc
Scope: Package 'processor' / File 'utils.go'
Include: Function comments, struct comments, package overview, examples
Generate: Package documentation, function comments, type comments"
```

For **C/C++** code:
```
"Use the generate-docstrings skill for C/C++ Doxygen documentation.

Language: C / C++
Style: Doxygen (JavaDoc-style)
Scope: Header file 'processor.h' / Directory 'include/'
Include: Function briefs, parameters, return values, code examples, warnings
Generate: Function documentation, struct documentation, macro documentation"
```

### Step 3: Review Generated Documentation Structure

The skill generates organized documentation:

```
For Python (Sphinx):
src/
├── module.py
│   └── """Module docstring"""
├── classes.py
│   ├── """Module docstring"""
│   └── class MyClass:
│       └── """Class docstring"""
└── functions.py
    ├── """Module docstring"""
    └── def my_function():
        └── """Function docstring"""

For JavaScript (JSDoc):
src/
├── module.js
│   └── /** @module MyModule */
├── classes.js
│   └── /** @class MyClass */
└── functions.js
    └── /** @function myFunction */

For Java (JavaDoc):
src/com/example/
├── package-info.java
│   └── /** Package documentation */
└── MyClass.java
    ├── /** Class documentation */
    └── /** Method documentation */
```

### Step 4: Customize Documentation

1. **Add Domain-Specific Details**:
   - Business logic explanations
   - Algorithm references
   - Performance characteristics
   - Thread safety information

2. **Enhance Examples**:
   - Real-world use cases
   - Edge case handling
   - Error scenarios
   - Integration patterns

3. **Add Cross-References**:
   - Related functions/classes
   - See-also links
   - External documentation
   - API references

4. **Include Metadata**:
   - Author information
   - Version numbers
   - Since/deprecation info
   - License information

### Step 5: Generate Documentation Output

#### For Python (Sphinx):

**Setup Sphinx**:
```bash
pip install sphinx sphinx-rtd-theme
sphinx-quickstart docs
```

**Configure `docs/conf.py`**:
```python
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # For Google/NumPy style
    'sphinx.ext.viewcode',
]

napoleon_google_docstring = True
napoleon_numpy_docstring = True
```

**Generate Documentation**:
```bash
cd docs
sphinx-apidoc -o source ../src
make html
```

#### For JavaScript (JSDoc):

**Install JSDoc**:
```bash
npm install --save-dev jsdoc
```

**Configure `jsdoc.json`**:
```json
{
  "source": {
    "include": ["src"],
    "includePattern": ".js$"
  },
  "opts": {
    "destination": "./docs",
    "recurse": true
  }
}
```

**Generate Documentation**:
```bash
npx jsdoc -c jsdoc.json
```

#### For Java (JavaDoc):

**Generate with Maven**:
```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-javadoc-plugin</artifactId>
  <version>3.5.0</version>
</plugin>
```

```bash
mvn javadoc:javadoc
```

**Generate with Gradle**:
```gradle
javadoc {
    source = sourceSets.main.allJava
    classpath = configurations.compileClasspath
}
```

```bash
gradle javadoc
```

#### For C# (DocFX):

**Install DocFX**:
```bash
dotnet tool install -g docfx
```

**Generate Documentation**:
```bash
docfx init
docfx build
docfx serve
```

#### For Go (Godoc):

**View Documentation**:
```bash
# Local package documentation
godoc -http=:6060
# Open browser to http://localhost:6060/pkg/yourpackage

# Or use pkgsite
go install golang.org/x/pkgsite/cmd/pkgsite@latest
pkgsite -http=:8080
```

#### For C/C++ (Doxygen):

**Install Doxygen**:
```bash
# Ubuntu/Debian
sudo apt-get install doxygen graphviz

# macOS
brew install doxygen graphviz
```

**Generate Config**:
```bash
doxygen -g Doxyfile
```

**Configure `Doxyfile`**:
```
PROJECT_NAME = "My Project"
INPUT = src include
RECURSIVE = YES
GENERATE_HTML = YES
```

**Generate Documentation**:
```bash
doxygen Doxyfile
```

### Step 6: Validate and Test

1. **Check Completeness**:
   ```bash
   # Python - check for missing docstrings
   pydocstyle src/

   # Or use pylint
   pylint --disable=all --enable=missing-docstring src/
   ```

2. **Validate Syntax**:
   - Ensure documentation tools parse without errors
   - Check for broken links or references
   - Validate code examples

3. **Test Examples**:
   ```python
   # Python - doctest
   python -m doctest -v module.py
   ```

4. **Review Generated Output**:
   - Open HTML documentation
   - Navigate through sections
   - Test search functionality
   - Check code syntax highlighting

## Quality Checklist

Before finalizing docstring generation, verify:

- [ ] All public functions/methods have docstrings
- [ ] All parameters are documented with types
- [ ] Return values are clearly described
- [ ] Exceptions/errors are documented
- [ ] Complex functions include usage examples
- [ ] Class attributes are documented
- [ ] Module-level documentation exists
- [ ] Type hints integrated (Python, TypeScript)
- [ ] Documentation style is consistent
- [ ] Cross-references are correct
- [ ] Code examples are valid and tested
- [ ] Documentation builds without errors
- [ ] Output is accessible and navigable
- [ ] Search functionality works (if applicable)
- [ ] All TODO/FIXME items addressed

## Common Issues and Solutions

### Issue: Docstrings Too Verbose
**Solution**:

- Keep descriptions concise but complete
- Use examples for complex cases
- Avoid repeating obvious type information
- Focus on behavior, not implementation

### Issue: Inconsistent Style
**Solution**:

- Choose one style guide and stick to it
- Use linters (pydocstyle, ESLint with JSDoc plugin)
- Create style guide document for team
- Automate style checking in CI/CD

### Issue: Outdated Documentation
**Solution**:

- Update docstrings when modifying code
- Use doctest to keep examples current
- Automate documentation generation in CI/CD
- Review documentation during code reviews

### Issue: Missing Type Information
**Solution**:

- Add type hints (Python) or type annotations
- Use TypeScript instead of JavaScript
- Enable strict type checking
- Document types in docstrings if hints unavailable

## Success Criteria

After using this skill, you should have:

- [ ] Complete docstrings for all public APIs
- [ ] Parameter and return type documentation
- [ ] Exception/error documentation
- [ ] Usage examples for complex functions
- [ ] Class and module documentation
- [ ] Consistent documentation style
- [ ] Valid, tested code examples
- [ ] Generated documentation output (HTML/PDF)
- [ ] Integrated with documentation tools
- [ ] Documentation accessible to team/users

## Related Skills

- `generate-api-docs`: Build comprehensive API reference documentation
- `add-strategic-comments`: Add explanatory comments to complex logic
- `create-user-documentation`: Create user-facing documentation
- `create-technical-docs`: Document architecture and design
- `code-review-quality`: Review code quality including documentation

## Tools by Language

### Python
- **pydocstyle**: Docstring style checker
- **Sphinx**: Documentation generator
- **pdoc**: Simple auto-documentation
- **napoleon**: Google/NumPy style support for Sphinx
- **doctest**: Test code examples in docstrings

### JavaScript/TypeScript
- **JSDoc**: JavaScript documentation generator
- **TypeDoc**: TypeScript documentation
- **ESLint**: JSDoc validation
- **documentation.js**: Modern documentation
- **API Extractor**: API documentation for TypeScript

### Java
- **JavaDoc**: Standard Java documentation
- **Maven JavaDoc Plugin**: Maven integration
- **Gradle JavaDoc**: Gradle integration
- **QDox**: JavaDoc parser
- **Checkstyle**: JavaDoc validation

### C#
- **DocFX**: Static site generator for .NET
- **Sandcastle**: Documentation compiler
- **GhostDoc**: Documentation generation tool
- **StyleCop**: XML documentation validation
- **NSwag**: API documentation generator

### Go
- **godoc**: Official Go documentation tool
- **pkgsite**: Go package documentation server
- **golint**: Checks for missing comments
- **staticcheck**: Code analysis including documentation

### C/C++
- **Doxygen**: Multi-language documentation generator
- **Breathe**: Sphinx/Doxygen bridge
- **Natural Docs**: Multi-language documentation
- **GTK-Doc**: GNOME documentation system
- **Sphinx**: With C/C++ domain support

## Additional Resources

- [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Google Python Style Guide - Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [JSDoc Official Documentation](https://jsdoc.app/)
- [Oracle JavaDoc Guide](https://www.oracle.com/technical-resources/articles/java/javadoc-tool.html)
- [Microsoft XML Documentation Comments](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/)
- [Effective Go - Commentary](https://golang.org/doc/effective_go#commentary)
- [Doxygen Manual](https://www.doxygen.nl/manual/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - documentation/docstrings/
