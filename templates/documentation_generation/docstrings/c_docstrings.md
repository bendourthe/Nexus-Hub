---
template_id: c_docstrings
template_name: Docstrings - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: documentation
phase: docstrings
difficulty: beginner
estimated_time_hours: 2-3
prerequisites: []
tools:
  - unity
  - cmocka
  - check
tags:
  - documentation
  - documentation
  - c
---
# C Documentation Comments (Doxygen)

## Objective
Generate comprehensive, standards-compliant Doxygen documentation comments for all public interfaces (files, structs, functions) that clearly document purpose, parameters, return values, and provide usage examples following Doxygen conventions for C code.

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

### File Documentation

- [ ] File purpose and scope clearly explained

- [ ] Key structures and functions listed

- [ ] Dependencies and requirements noted

- [ ] Usage examples provided

- [ ] Author and version information included

### Structure/Union Documentation

- [ ] Structure purpose and usage documented

- [ ] All fields described with types

- [ ] Memory layout considerations noted

- [ ] Structure-level examples provided

- [ ] Alignment and padding documented

### Function Documentation

- [ ] Function purpose clearly stated

- [ ] All parameters documented with @param

- [ ] Return values documented with @return

- [ ] Side effects documented

- [ ] Thread safety noted

- [ ] Memory ownership explained

### Macro Documentation

- [ ] Macro purpose documented

- [ ] Parameter expansion explained

- [ ] Side effects and preconditions noted

- [ ] Type safety considerations documented

### Documentation Style

- [ ] Consistent Doxygen style throughout codebase

- [ ] Proper use of Doxygen commands (@param, @return, @brief, etc.)

- [ ] Code examples formatted correctly

- [ ] Cross-references properly linked

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C Doxygen Documentation Generation Request

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

Please generate comprehensive Doxygen documentation for this C project following this protocol:

## Phase 1: Analysis & Doxygen Configuration

1. **Analyze Existing Code**
   - Inventory all files, structures, and public functions
   - Identify existing documentation patterns
   - Note any special documentation requirements
   - Check for existing Doxyfile configuration

2. **Review Doxygen Standards**
   - Follow Doxygen documentation conventions
   - Use JavaDoc style (/** ... */) or Qt style (/*! ... */)
   - Implement standard commands (@param, @return, @brief, etc.)
   - Include code examples where beneficial

3. **Check Project Structure**
   - Verify header file organization
   - Identify public API vs internal implementation
   - Note memory management patterns
   - Document compilation requirements

## Phase 2: File Documentation

For each header and source file:

### File Documentation Template
```c
/**
 * @file processor.h
 * @brief Data processing and transformation functions.
 *
 * This file provides a comprehensive interface for processing data from
 * various sources. It defines structures and functions for coordinating
 * processing operations with configurable error handling and resource management.
 *
 * The API is designed to be:
 * - Thread-safe for concurrent use
 * - Memory-efficient with minimal allocations
 * - Error-resistant with comprehensive checking
 *
 * @section usage Usage Example
 * @code
 * #include "processor.h"
 *
 * // Initialize processor
 * processor_t *proc = processor_create(PROCESSOR_MODE_STRICT, 10);
 * if (!proc) {
 *     fprintf(stderr, "Failed to create processor\n");
 *     return -1;
 * }
 *
 * // Process data
 * result_t result;
 * int status = processor_process(proc, data, data_len, &result);
 * if (status != 0) {
 *     fprintf(stderr, "Processing failed: %d\n", status);
 * }
 *
 * // Cleanup
 * processor_destroy(proc);
 * @endcode
 *
 * @section threading Thread Safety
 * All functions are thread-safe unless explicitly documented otherwise.
 * Multiple threads can safely call processor_process() on the same
 * processor instance concurrently.
 *
 * @section memory Memory Management
 * - Caller is responsible for freeing resources allocated by *_create()
 *   functions using corresponding *_destroy() functions.
 * - Functions that return allocated memory are clearly documented.
 * - All functions validate pointer arguments and return appropriate errors
 *   for NULL pointers.
 *
 * @section errors Error Handling
 * Functions return 0 on success and negative error codes on failure:
 * - -1: Invalid arguments
 * - -2: Memory allocation failure
 * - -3: Processing error
 * - -4: Timeout
 *
 * @author John Doe <john.doe@example.com>
 * @version 1.0.0
 * @date 2024-01-15
 * @copyright MIT License
 *
 * @see processor.c
 * @see processor_types.h
 */

#ifndef PROCESSOR_H
#define PROCESSOR_H
```

### Simple File Documentation
```c
/**
 * @file utils.h
 * @brief Utility functions and helper macros.
 * @author Jane Smith
 * @date 2024-01-15
 */
```

## Phase 3: Structure and Type Documentation

For each structure, union, and typedef:

### Structure Documentation Template
```c
/**
 * @struct processor_t
 * @brief Represents a data processor instance.
 *
 * The processor_t structure maintains state for data processing operations.
 * It manages worker threads, resource allocation, and processing configuration.
 *
 * This structure is opaque to API users. All access must be through the
 * provided API functions. Direct field access is not supported and may
 * break in future versions.
 *
 * @note This structure should only be created via processor_create() and
 *       destroyed via processor_destroy(). Never allocate this structure
 *       directly on the stack or with malloc().
 *
 * @warning Do not access structure fields directly. Use accessor functions.
 *
 * @see processor_create()
 * @see processor_destroy()
 * @see processor_process()
 */
typedef struct processor_t processor_t;

/**
 * @struct processor_options
 * @brief Configuration options for processor creation.
 *
 * This structure defines the configuration parameters for creating a
 * processor instance. All fields must be initialized before passing to
 * processor_create().
 *
 * @note Default values are available via processor_default_options().
 *
 * @code
 * processor_options opts = processor_default_options();
 * opts.mode = PROCESSOR_MODE_LENIENT;
 * opts.max_workers = 20;
 * processor_t *proc = processor_create(&opts);
 * @endcode
 */
struct processor_options {
    /** @brief Processing mode (STRICT, LENIENT, or FAILSAFE). */
    processor_mode_t mode;

    /**
     * @brief Maximum number of worker threads.
     *
     * Must be greater than 0. Recommended value is number of CPU cores.
     * Higher values may increase memory usage without improving performance.
     */
    int max_workers;

    /**
     * @brief Timeout in milliseconds for processing operations.
     *
     * Set to 0 for no timeout. Positive values specify the maximum time
     * allowed for a single item processing operation.
     */
    int timeout_ms;

    /**
     * @brief Number of retry attempts for failed operations.
     *
     * Must be non-negative. 0 means no retries. Each retry may delay
     * overall processing time.
     */
    int retry_attempts;

    /**
     * @brief User data pointer passed to callbacks.
     *
     * This pointer is passed unchanged to all callback functions.
     * The processor does not access or free this memory.
     *
     * @note Caller is responsible for managing lifetime of user_data.
     */
    void *user_data;
};
```

### Union Documentation
```c
/**
 * @union data_value
 * @brief Holds a value of various possible types.
 *
 * This union allows a single variable to store values of different types.
 * The actual type must be tracked separately (typically with a type field
 * in the containing structure).
 *
 * @warning Only one member should be accessed at a time. The active member
 *          must match the type indicator in the containing structure.
 *
 * @see data_item
 */
union data_value {
    /** @brief Integer value (type = DATA_TYPE_INT). */
    int64_t int_val;

    /** @brief Floating-point value (type = DATA_TYPE_FLOAT). */
    double float_val;

    /** @brief String value (type = DATA_TYPE_STRING).
     *  @note Caller owns this pointer and must free it. */
    char *string_val;

    /** @brief Binary data value (type = DATA_TYPE_BINARY).
     *  @note Caller owns this pointer and must free it. */
    void *binary_val;
};
```

### Enum Documentation
```c
/**
 * @enum processor_mode_t
 * @brief Processing mode enumeration.
 *
 * Defines how the processor handles errors during processing operations.
 * The mode affects both behavior and performance characteristics.
 */
typedef enum {
    /**
     * @brief Strict mode - fail immediately on any error.
     *
     * In strict mode, the first processing error causes the entire
     * operation to abort immediately. No partial results are returned.
     *
     * Use this mode when data integrity is critical and partial results
     * are unacceptable.
     */
    PROCESSOR_MODE_STRICT = 0,

    /**
     * @brief Lenient mode - continue processing despite errors.
     *
     * In lenient mode, processing continues even when individual items
     * fail. Errors are accumulated and reported at the end.
     *
     * Use this mode when best-effort processing is acceptable and some
     * data is better than none.
     */
    PROCESSOR_MODE_LENIENT = 1,

    /**
     * @brief Fail-safe mode - substitute defaults on error.
     *
     * In fail-safe mode, errors are handled silently with default values
     * substituted. No errors are returned to the caller.
     *
     * Use this mode when reliability is more important than accuracy.
     */
    PROCESSOR_MODE_FAILSAFE = 2
} processor_mode_t;
```

## Phase 4: Function Documentation

For each function:

### Function Documentation Template
```c
/**
 * @brief Processes a collection of data items.
 *
 * This function processes all items in the provided array using the configured
 * processing strategy. Processing may occur in parallel using multiple worker
 * threads.
 *
 * The function blocks until all items are processed or an unrecoverable error
 * occurs. In strict mode, processing stops at the first error. In lenient mode,
 * processing continues and errors are accumulated.
 *
 * @param[in] proc Pointer to initialized processor instance. Must not be NULL.
 * @param[in] items Array of items to process. Must not be NULL.
 * @param[in] count Number of items in array. Must be greater than 0.
 * @param[out] result Pointer to result structure. Must not be NULL.
 *                    Filled with processing results on success.
 *
 * @return 0 on success, negative error code on failure:
 *         - -1: Invalid arguments (NULL pointers or count <= 0)
 *         - -2: Memory allocation failure
 *         - -3: Processing error (in strict mode only)
 *         - -4: Timeout (if configured)
 *
 * @note The result structure is always filled, even on error, allowing
 *       inspection of partial progress in lenient mode.
 *
 * @warning This function may modify the items array if configured for
 *          in-place processing. Pass PROCESSOR_FLAG_COPY to process copies.
 *
 * @par Thread Safety
 * This function is thread-safe. Multiple threads can call processor_process()
 * concurrently on the same processor instance.
 *
 * @par Memory Management
 * The caller retains ownership of all pointers. This function does not free
 * items or result memory. The result structure may contain pointers to
 * allocated memory that must be freed with processor_free_result().
 *
 * @par Example
 * @code
 * processor_t *proc = processor_create(&opts);
 * data_item_t items[100];
 * // ... initialize items ...
 *
 * result_t result;
 * int status = processor_process(proc, items, 100, &result);
 * if (status == 0) {
 *     printf("Processed %zu items successfully\n", result.succeeded);
 * } else {
 *     fprintf(stderr, "Processing failed with code %d\n", status);
 * }
 *
 * processor_free_result(&result);
 * processor_destroy(proc);
 * @endcode
 *
 * @par Performance
 * Time complexity: O(n) where n is the number of items.
 * Space complexity: O(n) for result storage.
 * May spawn up to max_workers threads for parallel processing.
 *
 * @see processor_create()
 * @see processor_destroy()
 * @see processor_free_result()
 * @see processor_validate_item()
 *
 * @since 1.0.0
 */
int processor_process(processor_t *proc,
                     data_item_t *items,
                     size_t count,
                     result_t *result);
```

### Constructor/Destructor Documentation
```c
/**
 * @brief Creates a new processor instance.
 *
 * Allocates and initializes a new processor with the specified options.
 * The returned processor must be destroyed with processor_destroy() when
 * no longer needed.
 *
 * This function allocates memory and spawns worker threads. If any
 * initialization step fails, all resources are cleaned up and NULL is
 * returned.
 *
 * @param[in] opts Pointer to options structure. Must not be NULL.
 *                 The structure is copied; caller retains ownership.
 *
 * @return Pointer to new processor on success, NULL on failure.
 *         On failure, errno is set to indicate the error:
 *         - EINVAL: Invalid options (NULL pointer or invalid values)
 *         - ENOMEM: Memory allocation failure
 *         - EAGAIN: Thread creation failure
 *
 * @note Always check the return value before use. A NULL return indicates
 *       failure and errno will be set appropriately.
 *
 * @warning The returned processor must be freed with processor_destroy().
 *          Failure to do so will leak memory and system resources.
 *
 * @par Example
 * @code
 * processor_options opts = processor_default_options();
 * opts.max_workers = 8;
 *
 * processor_t *proc = processor_create(&opts);
 * if (!proc) {
 *     perror("processor_create");
 *     return EXIT_FAILURE;
 * }
 *
 * // Use processor...
 *
 * processor_destroy(proc);
 * @endcode
 *
 * @see processor_destroy()
 * @see processor_default_options()
 *
 * @since 1.0.0
 */
processor_t *processor_create(const processor_options *opts);

/**
 * @brief Destroys a processor and releases all resources.
 *
 * Stops all worker threads, frees allocated memory, and invalidates the
 * processor pointer. After this call, the processor must not be used.
 *
 * This function blocks until all worker threads have terminated and all
 * resources are cleaned up. It is safe to call even if processing operations
 * are in progress; they will be canceled and cleaned up.
 *
 * @param[in] proc Pointer to processor to destroy. May be NULL (no-op).
 *
 * @note Passing NULL is safe and does nothing (no-op).
 * @note This function never fails. All cleanup is performed even if
 *       errors occur internally.
 *
 * @warning After this call, the proc pointer is invalid and must not be used.
 * @warning Do not call this function while other threads are using the
 *          processor unless you coordinate shutdown explicitly.
 *
 * @see processor_create()
 *
 * @since 1.0.0
 */
void processor_destroy(processor_t *proc);
```

### Simple Function Documentation
```c
/**
 * @brief Validates a data item.
 *
 * Checks if an item meets all validation requirements for processing.
 *
 * @param[in] item Pointer to item to validate. Must not be NULL.
 * @return 1 if valid, 0 if invalid or NULL.
 */
int processor_validate_item(const data_item_t *item);
```

## Phase 5: Macro Documentation

### Macro Documentation Template
```c
/**
 * @def PROCESSOR_MAX_WORKERS
 * @brief Maximum number of worker threads allowed.
 *
 * This constant defines the upper limit for max_workers in processor_options.
 * Attempting to create a processor with more workers will be clamped to this
 * value.
 *
 * The default value of 64 balances parallelism with resource usage. Higher
 * values may not improve performance and will increase memory overhead.
 */
#define PROCESSOR_MAX_WORKERS 64

/**
 * @def MIN(a, b)
 * @brief Returns the minimum of two values.
 *
 * Evaluates to the smaller of two values. Both arguments are evaluated twice,
 * so do not use expressions with side effects.
 *
 * @param a First value to compare.
 * @param b Second value to compare.
 * @return The smaller value.
 *
 * @warning Arguments are evaluated twice. Do not use with expressions that
 *          have side effects (e.g., MIN(x++, y++) is undefined behavior).
 *
 * @warning No type checking. Ensure both arguments have compatible types.
 *
 * @code
 * int x = MIN(10, 20);  // x = 10
 * int y = MIN(-5, 0);   // y = -5
 *
 * // WRONG: Side effects
 * int bad = MIN(x++, y++);  // Undefined behavior!
 * @endcode
 */
#define MIN(a, b) ((a) < (b) ? (a) : (b))

/**
 * @def PROCESSOR_FOREACH_ITEM(proc, item)
 * @brief Iterates over all items in a processor.
 *
 * This macro provides a convenient way to iterate over all items managed
 * by a processor. It expands to a for loop that assigns each item to the
 * specified variable.
 *
 * @param proc Processor instance to iterate.
 * @param item Variable name for current item (declared in macro).
 *
 * @note The item variable is declared by the macro and is only valid within
 *       the loop body.
 *
 * @warning Do not modify the processor while iterating. Do not call
 *          processor_destroy() within the loop.
 *
 * @code
 * PROCESSOR_FOREACH_ITEM(proc, item) {
 *     printf("Item ID: %s\n", item->id);
 *     process_item(item);
 * }
 * @endcode
 */
#define PROCESSOR_FOREACH_ITEM(proc, item) \
    for (data_item_t *item = processor_first_item(proc); \
         item != NULL; \
         item = processor_next_item(proc))
```

## Phase 6: Callback and Function Pointer Documentation

### Callback Documentation Template
```c
/**
 * @typedef processor_callback_t
 * @brief Callback function for processing individual items.
 *
 * This callback is invoked for each item during processing. The callback
 * should process the item and return a status code indicating success or
 * failure.
 *
 * @param[in] item Pointer to item to process. Never NULL.
 * @param[in] user_data User data pointer from processor_options.
 * @param[out] result Pointer to store processing result. May be NULL if
 *                    caller doesn't need detailed results.
 *
 * @return 0 on success, negative value on error. Error codes are
 *         application-defined.
 *
 * @note Callbacks must be thread-safe if max_workers > 1. Multiple worker
 *       threads may call the callback concurrently.
 *
 * @note The callback should not block for extended periods. Long-running
 *       callbacks will reduce overall throughput.
 *
 * @warning Do not call processor functions from within the callback as this
 *          may cause deadlock.
 *
 * @par Example
 * @code
 * int my_callback(data_item_t *item, void *user_data, item_result_t *result) {
 *     // Process item
 *     if (!validate_item(item)) {
 *         return -1;  // Validation failed
 *     }
 *
 *     // Perform processing
 *     int status = process_item_data(item);
 *
 *     // Fill result if provided
 *     if (result) {
 *         result->processed_count = 1;
 *         result->bytes_processed = item->size;
 *     }
 *
 *     return status;
 * }
 * @endcode
 *
 * @see processor_set_callback()
 */
typedef int (*processor_callback_t)(data_item_t *item,
                                   void *user_data,
                                   item_result_t *result);
```

## Phase 7: Doxygen Quality Checks

Verify each Doxygen comment meets these criteria:

### Completeness

- [ ] All public APIs documented

- [ ] All @param tags present and documented

- [ ] @return documented for non-void functions

- [ ] Memory ownership clearly documented

- [ ] Thread safety explicitly stated

- [ ] Examples for non-trivial functions

### Doxygen Commands

- [ ] @brief for summaries

- [ ] @param[in/out/in,out] for parameters

- [ ] @return for return values

- [ ] @note for important information

- [ ] @warning for critical warnings

- [ ] @see for cross-references

- [ ] @code/@endcode for examples

### C-Specific Documentation

- [ ] Memory ownership documented

- [ ] Pointer validity requirements stated

- [ ] NULL handling explicitly documented

- [ ] Side effects clearly noted

- [ ] errno usage documented

### Clarity

- [ ] Clear, professional language

- [ ] Technical terms explained

- [ ] No redundant information

- [ ] Proper grammar and spelling

## Phase 8: Documentation Generation

After Doxygen comments are complete:

1. **Create Doxyfile**
   ```bash
   # Generate default configuration
   doxygen -g Doxyfile

   # Edit key settings
   # PROJECT_NAME = "My Project"
   # INPUT = src/ include/
   # RECURSIVE = YES
   # EXTRACT_ALL = YES
   # GENERATE_HTML = YES
   # GENERATE_LATEX = NO
   ```

2. **Generate Documentation**
   ```bash
   # Generate HTML documentation
   doxygen Doxyfile

   # View generated docs
   open html/index.html  # macOS
   xdg-open html/index.html  # Linux
   start html/index.html  # Windows
   ```

3. **Validate Documentation**
   ```bash
   # Check for warnings
   doxygen Doxyfile 2>&1 | grep -i warning

   # Check coverage
   doxygen -d Doxyfile | grep "Preprocessing"
   ```

## Output Format

Please provide Doxygen comments in this format:

### File-by-File Report
```markdown
## File: src/processor.c

### Function: processor_create
[Generated Doxygen comment]

### Function: processor_destroy
[Generated Doxygen comment]

### Function: processor_process
[Generated Doxygen comment]

---
```

### Summary Report
```markdown
## Doxygen Documentation Generation Summary

**Files Processed**: [count]
**Structures Documented**: [count]
**Functions Documented**: [count]
**Macros Documented**: [count]
**Typedefs Documented**: [count]

**Doxygen Standards Compliance**:

- [ ] All public APIs documented

- [ ] All @param tags present

- [ ] All @return tags present

- [ ] Memory ownership documented

- [ ] Thread safety documented

**C-Specific Documentation**:

- [ ] NULL handling documented

- [ ] errno usage documented

- [ ] Side effects noted

- [ ] Pointer ownership clear

**Coverage Metrics**:

- File coverage: [X%]

- Function coverage: [X%]

- Structure coverage: [X%]

- Overall coverage: [X%]
```

## C/Doxygen Best Practices

1. **Document Memory Ownership**
   - Who allocates memory?
   - Who is responsible for freeing?
   - When should memory be freed?

2. **Document Thread Safety**
   - Is function thread-safe?
   - What synchronization is needed?
   - Any race conditions?

3. **Document NULL Handling**
   - Can parameters be NULL?
   - Can return value be NULL?
   - What happens with NULL?

4. **Document Side Effects**
   - Does function modify globals?
   - Does it modify arguments?
   - Does it set errno?

5. **Use Consistent Style**
   - JavaDoc (/** */) or Qt (/*! */)
   - Consistent @param directions
   - Standard error code documentation

## Common Doxygen Mistakes

1. **Forgetting parameter directions**
   - Use @param[in], @param[out], @param[in,out]

2. **Not documenting memory ownership**
   - Always state who owns returned pointers
   - Document when to free memory

3. **Ignoring thread safety**
   - Always document thread safety
   - Note any synchronization requirements

4. **Missing NULL documentation**
   - Document NULL parameter behavior
   - Document NULL return conditions

5. **Incomplete error documentation**
   - Document all return codes
   - Document errno usage
   - Explain error conditions

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
~~~

## Validation Configuration

```doxyfile
# Doxyfile configuration for validation

# Enable all warnings
WARN_IF_UNDOCUMENTED = YES
WARN_IF_DOC_ERROR = YES
WARN_NO_PARAMDOC = YES
WARN_AS_ERROR = NO

# Extract all entities
EXTRACT_ALL = NO
EXTRACT_PRIVATE = NO
EXTRACT_STATIC = NO

# Documentation requirements
JAVADOC_AUTOBRIEF = YES
QT_AUTOBRIEF = YES
```

## Output Format Specifications

The generated Doxygen comments should:

- Follow Doxygen conventions and C documentation best practices

- Include all standard commands (@param, @return, @brief, etc.)

- Document memory ownership and management explicitly

- State thread safety guarantees clearly

- Include runnable code examples in @code blocks

- Cross-reference related functions with @see

- Generate well-formatted HTML and LaTeX documentation

- Pass Doxygen validation without warnings

- Document all error conditions and errno usage
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
