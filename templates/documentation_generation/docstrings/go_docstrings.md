---
template_id: go_docstrings
template_name: Docstrings - Go
version: 1.0.0
last_updated: 2025-12-03
language: Go
category: documentation
phase: docstrings
difficulty: beginner
estimated_time_hours: 2-3
prerequisites: []
tools:

  - go test (1.23+)
  - testify
tags:

  - documentation
  - documentation
  - go
---
# Go Documentation Generation (godoc)

## Objective
Generate comprehensive, idiomatic Go documentation comments that integrate with godoc and pkg.go.dev, clearly documenting purpose, parameters, return values, and providing usage examples following Go conventions.

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

### Package-Level Documentation

- [ ] Package purpose clearly explained

- [ ] Key types and functions listed

- [ ] Usage examples provided

- [ ] Package-level doc.go file created if needed

### Type Documentation

- [ ] Type purpose and usage documented

- [ ] Struct fields documented when non-obvious

- [ ] Interface contracts explained

- [ ] Type-level examples provided

### Function Documentation

- [ ] Function purpose clearly stated

- [ ] Parameters and returns implicitly documented

- [ ] Error return values explained

- [ ] Usage examples for complex functions

- [ ] Goroutine safety documented

### Go Conventions

- [ ] First sentence is complete and starts with name

- [ ] Documentation immediately precedes declaration

- [ ] Examples follow naming convention (Example_functionName)

- [ ] Code examples are testable

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Documentation Generation Request

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

Please generate comprehensive godoc-compatible documentation for this Go project following this protocol:

## Phase 1: Analysis & Go Conventions

1. **Analyze Existing Code**
   - Inventory all packages, types, and exported functions
   - Identify existing documentation patterns
   - Note special documentation requirements
   - Review interface definitions

2. **Go Documentation Style**
   Use **godoc conventions**: documentation comments immediately precede declarations,
   start with the name being documented, and form complete sentences.

## Phase 2: Package-Level Documentation

### Package Documentation (in any .go file or doc.go)
```go
// Package example provides utilities for processing data streams.
//
// This package implements a high-performance data processing pipeline
// with support for filtering, transformation, and aggregation operations.
//
// Basic Usage:
//
//	processor := example.NewProcessor(options)
//	result, err := processor.Process(data)
//	if err != nil {
//		log.Fatal(err)
//	}
//
// The package supports concurrent processing with goroutine-safe operations.
// See the Processor type for detailed usage examples.
//
// For more information, visit: https://pkg.go.dev/example.com/module/example
package example
```

### Dedicated doc.go File (for longer package documentation)
```go
// Package processing provides a comprehensive framework for data processing.
//
// # Overview
//
// This package offers a flexible and extensible system for processing
// various types of data with built-in support for:
//   - Filtering and validation
//   - Transformation and mapping
//   - Aggregation and reduction
//   - Concurrent processing
//
// # Architecture
//
// The package is organized into several key components:
//
//	┌─────────────┐
//	│  Processor  │
//	├─────────────┤
//	│   Filter    │
//	│ Transformer │
//	│ Aggregator  │
//	└─────────────┘
//
// # Quick Start
//
//	proc := processing.NewProcessor(processing.Options{
//		Workers: 4,
//		BufferSize: 1000,
//	})
//	defer proc.Close()
//
//	results := make(chan Result)
//	go proc.Process(data, results)
//
//	for result := range results {
//		// Handle result
//	}
//
// # Thread Safety
//
// All exported types in this package are safe for concurrent use
// unless explicitly documented otherwise.
//
// # Error Handling
//
// Functions return errors following Go conventions. Wrap errors with
// context using fmt.Errorf with %w verb for error unwrapping support.
package processing
```

## Phase 3: Type Documentation

### Struct Documentation
```go
// Processor handles data processing operations with configurable behavior.
//
// A Processor manages a pool of workers that process data concurrently.
// It is safe for concurrent use by multiple goroutines.
//
// Fields are exported to allow JSON marshaling. Modify fields only
// before calling Start. After Start, fields should be treated as read-only.
type Processor struct {
	// MaxWorkers is the maximum number of concurrent workers.
	// Must be > 0. Default is runtime.NumCPU().
	MaxWorkers int

	// BufferSize determines the channel buffer size.
	// Larger values reduce blocking but use more memory.
	BufferSize int

	// Timeout specifies the maximum duration for processing.
	// Zero means no timeout.
	Timeout time.Duration

	// unexported fields below
	workers []*worker
	done    chan struct{}
}

// NewProcessor creates a new Processor with the given options.
//
// It initializes internal state and prepares the processor for use.
// The returned processor is not started; call Start to begin processing.
//
// Example:
//
//	proc := NewProcessor(Options{
//		MaxWorkers: 4,
//		BufferSize: 100,
//		Timeout:    5 * time.Second,
//	})
//	defer proc.Close()
func NewProcessor(opts Options) *Processor {
	// Implementation
}

// Process processes the input data and sends results to the output channel.
//
// It spawns worker goroutines according to MaxWorkers and distributes
// work across them. Results are sent to out as they become available.
// The out channel is closed when all processing is complete.
//
// Process blocks until all data is processed or ctx is canceled.
// If ctx is canceled, Process returns immediately and outstanding work
// is abandoned.
//
// Example:
//
//	ctx := context.Background()
//	results := make(chan Result, 10)
//	err := proc.Process(ctx, data, results)
//	if err != nil {
//		log.Fatal(err)
//	}
//	for result := range results {
//		fmt.Println(result)
//	}
func (p *Processor) Process(ctx context.Context, data []Data, out chan<- Result) error {
	// Implementation
}
```

### Interface Documentation
```go
// Filter represents a data filtering strategy.
//
// Implementations must be safe for concurrent use by multiple goroutines.
// The Accept method is called for each data item to determine if it
// should be included in the output.
//
// Example implementation:
//
//	type sizeFilter struct{ maxSize int }
//
//	func (f *sizeFilter) Accept(data Data) bool {
//		return len(data.Content) <= f.maxSize
//	}
type Filter interface {
	// Accept returns true if the data item should be included.
	//
	// Implementations should be fast and avoid blocking operations.
	// If Accept panics, the behavior is undefined.
	Accept(data Data) bool
}

// Transformer converts data from one form to another.
//
// Implementations must be safe for concurrent use by multiple goroutines.
// Transform should return an error for data that cannot be transformed.
type Transformer interface {
	// Transform converts the input data to output data.
	//
	// It returns an error if the transformation fails. The returned
	// error should be actionable and include context about the failure.
	Transform(ctx context.Context, input Data) (Data, error)
}
```

## Phase 4: Function Documentation

### Function Documentation Template
```go
// ProcessData processes a slice of data items using the specified options.
//
// It applies filtering, transformation, and aggregation in sequence.
// Processing happens concurrently using up to opts.MaxWorkers goroutines.
//
// The function blocks until all processing completes or ctx is canceled.
// If ctx is canceled, ProcessData returns immediately with a context error.
//
// Parameters:
//   - ctx: Context for cancellation and deadlines
//   - data: Slice of data items to process
//   - opts: Processing options (see Options type)
//
// Returns the processed results and any error encountered.
// If multiple errors occur, only the first is returned.
//
// Example:
//
//	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
//	defer cancel()
//
//	results, err := ProcessData(ctx, data, Options{MaxWorkers: 4})
//	if err != nil {
//		log.Fatal(err)
//	}
func ProcessData(ctx context.Context, data []Data, opts Options) ([]Result, error) {
	// Implementation
}
```

### Method Documentation
```go
// Start begins processing with the configured workers.
//
// It must be called before Process. Calling Start multiple times
// or calling Start after Close results in undefined behavior.
//
// Start is not safe for concurrent use with other methods.
func (p *Processor) Start() error {
	// Implementation
}

// Close shuts down the processor and releases resources.
//
// It waits for all active workers to complete their current tasks.
// After Close returns, the processor cannot be reused.
//
// Close is idempotent; multiple calls are safe.
// Close blocks until shutdown completes or ctx is canceled.
func (p *Processor) Close() error {
	// Implementation
}
```

## Phase 5: Special Cases

### Error Variables and Types
```go
// ErrInvalidData indicates that input data failed validation.
//
// This error is returned when data does not meet expected format
// or constraints. It can be checked using errors.Is.
var ErrInvalidData = errors.New("invalid data format")

// ErrTimeout indicates that an operation exceeded its time limit.
//
// This error wraps the original context error and can be unwrapped
// with errors.Unwrap.
var ErrTimeout = errors.New("operation timeout")

// ProcessingError represents an error that occurred during processing.
//
// It includes details about the failure and can be unwrapped to
// access the underlying cause.
type ProcessingError struct {
	// Op is the operation that failed.
	Op string
	// Data is the data item that caused the error.
	Data Data
	// Err is the underlying error.
	Err error
}

// Error returns a string representation of the error.
//
// It includes the operation name and underlying error message.
func (e *ProcessingError) Error() string {
	return fmt.Sprintf("%s: %v", e.Op, e.Err)
}

// Unwrap returns the underlying error for use with errors.Is and errors.As.
func (e *ProcessingError) Unwrap() error {
	return e.Err
}
```

### Constants
```go
// Default configuration values for processors.
const (
	// DefaultMaxWorkers is the default number of concurrent workers.
	DefaultMaxWorkers = 4

	// DefaultBufferSize is the default channel buffer size.
	DefaultBufferSize = 100

	// MaxBufferSize is the maximum allowed buffer size.
	// Values above this will be clamped.
	MaxBufferSize = 10000
)
```

### Example Functions (Testable Examples)
```go
// Example demonstrates basic usage of the Processor.
func Example() {
	proc := NewProcessor(Options{MaxWorkers: 2})
	defer proc.Close()

	data := []Data{{Content: "test"}}
	results := make(chan Result, 1)

	go proc.Process(context.Background(), data, results)

	for result := range results {
		fmt.Println(result.Value)
	}
	// Output: test
}

// Example_concurrent demonstrates concurrent processing.
func Example_concurrent() {
	proc := NewProcessor(Options{
		MaxWorkers: 4,
		BufferSize: 10,
	})
	defer proc.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	data := generateTestData(100)
	results := make(chan Result, 10)

	go proc.Process(ctx, data, results)

	count := 0
	for range results {
		count++
	}
	fmt.Printf("Processed %d items\n", count)
	// Output: Processed 100 items
}

// Example_error demonstrates error handling.
func Example_error() {
	proc := NewProcessor(Options{MaxWorkers: 1})
	defer proc.Close()

	data := []Data{{Content: ""}} // Invalid data
	results := make(chan Result, 1)

	err := proc.Process(context.Background(), data, results)
	if errors.Is(err, ErrInvalidData) {
		fmt.Println("Caught invalid data error")
	}
	// Output: Caught invalid data error
}
```

## Phase 6: Documentation Best Practices

### Godoc Conventions
1. **Start with the name being documented**
   ```go
   // Good: Processor handles data processing operations.
   // Bad: This type handles data processing operations.
   ```

2. **Form complete sentences**
   ```go
   // Good: MaxWorkers is the maximum number of concurrent workers.
   // Bad: Max number of workers
   ```

3. **Document concurrency behavior**
   ```go
   // Process is safe for concurrent use by multiple goroutines.
   // Process is NOT safe for concurrent use.
   ```

4. **Document what, not how (usually)**
   ```go
   // Good: Sum returns the sum of all elements.
   // Bad: Sum loops through elements and adds them.
   ```

5. **Use sections for long package docs**
   ```go
   // # Section Title
   //
   // Section content...
   ```

## Phase 7: Documentation Generation

```bash
# Generate and serve documentation locally
go doc -all                          # Show all package docs
go doc package.Type                  # Show specific type docs
go doc package.Type.Method           # Show specific method docs

# View in browser
godoc -http=:6060                    # Local godoc server

# Generate static HTML
godoc -html package > ${OUTPUT_DIR}/exports/package.html

# View on pkg.go.dev (for public modules)
# https://pkg.go.dev/module@version/package
```

## Output Format

```markdown
## Documentation Generation Summary

**Packages Documented**: [count]
**Types Documented**: [count]
**Functions Documented**: [count]
**Examples Added**: [count]

**Go Conventions**:

- [ ] Comments start with name being documented

- [ ] Complete sentences used throughout

- [ ] Concurrency behavior documented

- [ ] Examples are testable

- [ ] Package docs include usage examples

**Quality Checks**:

- [ ] All exported identifiers documented

- [ ] Examples compile and pass

- [ ] godoc formatting correct

- [ ] Cross-references work

- [ ] pkg.go.dev rendering verified
```

## Common Mistakes to Avoid

1. **Don't start comments with "This"**
   ```go
   // Bad: This function processes data
   // Good: ProcessData processes the input data
   ```

2. **Don't omit the name**
   ```go
   // Bad: Returns the size in bytes
   // Good: Size returns the size in bytes
   ```

3. **Don't forget concurrency documentation**
   ```go
   // Must document if type is goroutine-safe
   // Type is safe for concurrent use by multiple goroutines.
   ```

4. **Don't use prose-style parameter documentation**
   ```go
   // Bad: The ctx parameter is the context
   // Good: ctx controls cancellation and timeouts
   ```

5. **Don't create untestable examples**
   ```go
   // Examples must be functions named Example_* or Example
   // They must have predictable output for testing
   ```

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
