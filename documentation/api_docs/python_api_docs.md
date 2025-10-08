# API & Reference Documentation

Build comprehensive API reference documentation for all public interfaces.

---

## Overview

This review focuses on creating complete API reference documentation that developers can use to understand and integrate with your codebase. This includes detailed specifications for all public classes, methods, functions, and their parameters.

---

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown

Please help me create comprehensive API reference documentation for my Python project.
**Project Context:**
- Project name: [YOUR_PROJECT_NAME]
- Package name: [package_name]
- API type: [Library / REST API / CLI / Mixed]
- Public modules: [List main public modules]
---
## API Reference Structure
### 1. API Overview (docs/api/README.md)
Create main API documentation index:
# API Reference

Complete reference documentation for [Project Name] APIs.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Modules](#core-modules)
3. [Data Models](#data-models)
4. [Exceptions](#exceptions)
5. [Utilities](#utilities)
6. [Examples](#examples)

## Quick Start

### Installation
pip install [package-name]

### Basic Usage
```python
from [package] import [MainClass]

# Initialize
instance = [MainClass](config)

# Use
result = instance.method(parameters)
```

## Core Modules

### [package].core
Core functionality and main processing classes.

**Classes**:
- [`MainProcessor`](core.md#mainprocessor) - Primary processing class
- [`DataValidator`](core.md#datavalidator) - Data validation
- [`Transformer`](core.md#transformer) - Data transformation

**Functions**:
- [`process_batch()`](core.md#process_batch) - Batch processing utility

### [package].models
Data models and schemas.

**Classes**:
- [`InputModel`](models.md#inputmodel) - Input data model
- [`OutputModel`](models.md#outputmodel) - Output data model
- [`ConfigModel`](models.md#configmodel) - Configuration model

### [package].utils
Utility functions and helpers.

**Functions**:
- [`format_timestamp()`](utils.md#format_timestamp) - Timestamp formatting
- [`validate_email()`](utils.md#validate_email) - Email validation
- [`parse_config()`](utils.md#parse_config) - Configuration parsing

## Installation Options

### From PyPI
```bash
pip install [package-name]
```

### From Source
```bash
git clone [repo-url]
cd [project]
pip install -e .
```

### With Optional Dependencies
```bash
# Full installation
pip install [package-name][all]

# Specific extras
pip install [package-name][dev]     # Development tools
pip install [package-name][docs]    # Documentation tools
pip install [package-name][api]     # API server dependencies
```

## Version Information

**Current Version**: [X.Y.Z]
**Requires**: Python 3.9+
**License**: [License Type]

## Support

- **Documentation**: [https://docs.example.com](https://docs.example.com)
- **Issues**: [https://github.com/user/project/issues](https://github.com/user/project/issues)
- **Discussions**: [https://github.com/user/project/discussions](https://github.com/user/project/discussions)
~~~

---

### 2. Core Module Reference (docs/api/core.md)

Document core module with complete API specifications:

```markdown
# Core Module API Reference

`[package].core` - Core functionality and main processing classes.

---

## Classes

### MainProcessor

Primary data processing class that orchestrates validation, transformation, and output generation.

#### Constructor

```python
MainProcessor(
    config: Optional[Dict[str, Any]] = None,
    validator: Optional[ValidatorBase] = None,
    transformer: Optional[TransformerBase] = None
)
```

**Parameters**:
- `config` (dict, optional): Configuration dictionary with processing options
  - `batch_size` (int): Number of items per batch (default: 100)
  - `timeout` (int): Processing timeout in seconds (default: 30)
  - `strict_mode` (bool): Enable strict validation (default: True)
- `validator` (ValidatorBase, optional): Custom validator instance (default: DefaultValidator)
- `transformer` (TransformerBase, optional): Custom transformer instance (default: DefaultTransformer)

**Raises**:
- `ValueError`: If config contains invalid values
- `TypeError`: If validator/transformer don't implement required interface

**Example**:
```python
from mypackage.core import MainProcessor

# Basic initialization
processor = MainProcessor()

# With custom configuration
processor = MainProcessor(config={
    'batch_size': 50,
    'timeout': 60,
    'strict_mode': False
})

# With custom validator
from mypackage.validators import CustomValidator
processor = MainProcessor(validator=CustomValidator())
```

---

#### Methods

##### process()

Process input data through validation, transformation, and business logic pipeline.

```python
process(
    data: Union[List[Dict], pd.DataFrame],
    callback: Optional[Callable[[float], None]] = None
) -> ProcessingResult
```

**Parameters**:
- `data` (List[Dict] or DataFrame): Input data to process
  - If list: Each dict must contain required fields
  - If DataFrame: Must have required columns
- `callback` (callable, optional): Progress callback function
  - Receives float (0.0 to 1.0) indicating progress
  - Called periodically during processing

**Returns**:
- `ProcessingResult`: Object containing:
  - `results` (List[Dict]): Processed data records
  - `success_count` (int): Number of successfully processed items
  - `failure_count` (int): Number of failed items
  - `errors` (List[str]): Error messages for failed items
  - `duration` (float): Processing duration in seconds

**Raises**:
- `ValidationError`: If input data fails validation
- `ProcessingError`: If processing logic fails
- `TimeoutError`: If processing exceeds configured timeout

**Example**:
```python
# Basic usage
result = processor.process(input_data)
print(f"Processed: {result.success_count} items")

# With progress callback
def progress_callback(progress):
    print(f"Progress: {progress * 100:.1f}%")

result = processor.process(input_data, callback=progress_callback)

# Error handling
try:
    result = processor.process(input_data)
except ValidationError as e:
    print(f"Validation failed: {e}")
except ProcessingError as e:
    print(f"Processing failed: {e}")
```

**Performance Notes**:
- Processing is done in batches for efficiency
- Memory usage is O(batch_size), not O(n)
- Typical throughput: ~1000 items/second

**Thread Safety**: This method is thread-safe when using different processor instances

---

##### validate()

Validate input data without processing.

```python
validate(data: Union[List[Dict], pd.DataFrame]) -> ValidationResult
```

**Parameters**:
- `data`: Data to validate (same format as `process()`)

**Returns**:
- `ValidationResult`: Object containing:
  - `is_valid` (bool): Overall validation status
  - `errors` (List[str]): Validation error messages
  - `warnings` (List[str]): Non-critical warnings

**Example**:
```python
validation = processor.validate(input_data)
if validation.is_valid:
    result = processor.process(input_data)
else:
    print(f"Validation failed: {validation.errors}")
```

---

##### transform()

Transform data without full processing pipeline.

```python
transform(
    data: Union[List[Dict], pd.DataFrame],
    transformations: Optional[List[str]] = None
) -> TransformResult
```

**Parameters**:
- `data`: Data to transform
- `transformations`: List of transformation names to apply (default: all)

**Returns**:
- `TransformResult`: Transformed data

**Example**:
```python
# Apply all transformations
transformed = processor.transform(input_data)

# Apply specific transformations
transformed = processor.transform(
    input_data,
    transformations=['normalize', 'enrich']
)
```

---

#### Properties

##### config

Current processor configuration.

```python
@property
def config(self) -> Dict[str, Any]
```

**Returns**: Dictionary with current configuration

**Example**:
```python
current_config = processor.config
print(f"Batch size: {current_config['batch_size']}")
```

---

##### is_ready

Check if processor is ready for processing.

```python
@property
def is_ready(self) -> bool
```

**Returns**: True if processor is configured and ready

---

#### Context Manager Support

MainProcessor can be used as a context manager for automatic resource cleanup:

```python
with MainProcessor(config) as processor:
    result = processor.process(data)
# Resources automatically cleaned up
```

---

### DataValidator

Data validation class for schema and business rule validation.

#### Constructor

```python
DataValidator(
    schema: Optional[Dict[str, Any]] = None,
    strict: bool = True
)
```

**Parameters**:
- `schema`: JSON schema or Pydantic model for validation
- `strict`: Enable strict validation mode

**Example**:
```python
from mypackage.core import DataValidator

# With JSON schema
schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "value": {"type": "number", "minimum": 0}
    },
    "required": ["id", "value"]
}
validator = DataValidator(schema=schema)

# With Pydantic model
from pydantic import BaseModel

class MyModel(BaseModel):
    id: str
    value: float

validator = DataValidator(schema=MyModel)
```

---

#### Methods

##### validate()

Validate data against schema and business rules.

```python
validate(data: Any) -> ValidationResult
```

**Parameters**:
- `data`: Data to validate

**Returns**:
- `ValidationResult`: Validation results

**Raises**:
- `SchemaValidationError`: If schema validation fails in strict mode

**Example**:
```python
result = validator.validate(input_data)
if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")
```

---

## Functions

### process_batch()

Utility function for batch processing without creating processor instance.

```python
process_batch(
    data: List[Dict],
    batch_size: int = 100,
    config: Optional[Dict] = None
) -> ProcessingResult
```

**Parameters**:
- `data`: List of data dictionaries to process
- `batch_size`: Items per batch (default: 100)
- `config`: Processing configuration (optional)

**Returns**:
- `ProcessingResult`: Processing results

**Example**:
```python
from mypackage.core import process_batch

result = process_batch(
    data=input_data,
    batch_size=50,
    config={'strict_mode': False}
)
```

---

### create_processor()

Factory function for creating configured processor instances.

```python
create_processor(
    preset: str = "default",
    **kwargs
) -> MainProcessor
```

**Parameters**:
- `preset`: Configuration preset name
  - `"default"`: Standard processing
  - `"fast"`: Optimized for speed
  - `"strict"`: Maximum validation
- `**kwargs`: Additional configuration overrides

**Returns**:
- `MainProcessor`: Configured processor instance

**Example**:
```python
from mypackage.core import create_processor

# Use preset
processor = create_processor(preset="fast")

# Preset with overrides
processor = create_processor(
    preset="strict",
    batch_size=200
)
```

---

## Exceptions

### ProcessingError

Base exception for processing errors.

```python
class ProcessingError(Exception):
    """Base exception for processing errors."""
```

**Attributes**:
- `message` (str): Error message
- `details` (Dict): Additional error details

**Example**:
```python
try:
    result = processor.process(data)
except ProcessingError as e:
    print(f"Error: {e.message}")
    print(f"Details: {e.details}")
```

### ValidationError

Exception raised when validation fails.

```python
class ValidationError(ProcessingError):
    """Validation failure exception."""
```

**Attributes**:
- `errors` (List[str]): List of validation errors
- `field` (str, optional): Field that failed validation

---

## Type Definitions

### ProcessingResult

```python
from typing import TypedDict, List

class ProcessingResult(TypedDict):
    results: List[Dict]
    success_count: int
    failure_count: int
    errors: List[str]
    duration: float
```

### ValidationResult

```python
class ValidationResult(TypedDict):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
```

---

## Usage Examples

### Example 1: Basic Processing

```python
from mypackage.core import MainProcessor

# Create processor
processor = MainProcessor(config={
    'batch_size': 100,
    'timeout': 30
})

# Process data
data = [
    {'id': '1', 'value': 100.0},
    {'id': '2', 'value': 200.0}
]

result = processor.process(data)

# Handle results
print(f"Success: {result.success_count}")
print(f"Failed: {result.failure_count}")
print(f"Duration: {result.duration:.2f}s")
```

### Example 2: Validation Before Processing

```python
# Validate first
validation = processor.validate(data)

if validation.is_valid:
    result = processor.process(data)
else:
    print("Validation errors:")
    for error in validation.errors:
        print(f"  - {error}")
```

### Example 3: Custom Validator

```python
from mypackage.core import MainProcessor, ValidatorBase

class CustomValidator(ValidatorBase):
    def validate(self, data):
        # Custom validation logic
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        )

processor = MainProcessor(validator=CustomValidator())
result = processor.process(data)
```

### Example 4: Progress Tracking

```python
import time

def progress_handler(progress):
    # Update progress bar or logging
    bar_length = 50
    filled = int(bar_length * progress)
    bar = '=' * filled + '-' * (bar_length - filled)
    print(f'\r[{bar}] {progress*100:.1f}%', end='', flush=True)

result = processor.process(large_dataset, callback=progress_handler)
print()  # New line after progress
```

### Example 5: Error Handling

```python
from mypackage.core import MainProcessor, ValidationError, ProcessingError

processor = MainProcessor()

try:
    result = processor.process(data)
    print(f"Processed {result.success_count} items")
    
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    for error in e.errors:
        print(f"  - {error}")
        
except ProcessingError as e:
    print(f"Processing failed: {e.message}")
    print(f"Details: {e.details}")
    
except TimeoutError:
    print("Processing timeout exceeded")
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Performance Guidelines

### Optimization Tips

1. **Batch Size**: Adjust based on data size
   - Small data (<1000): batch_size=100
   - Medium data (1000-100k): batch_size=1000
   - Large data (>100k): batch_size=10000

2. **Memory**: Monitor memory with large datasets
   - Use streaming for very large files
   - Process in chunks if memory limited

3. **Parallelization**: For CPU-bound operations
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   with ThreadPoolExecutor(max_workers=4) as executor:
       futures = [executor.submit(processor.process, chunk) 
                  for chunk in chunks]
   ```

### Benchmarks

Typical performance on modern hardware (4-core CPU, 16GB RAM):

| Operation | Items | Time | Throughput |
|-----------|-------|------|------------|
| Validation | 10,000 | ~0.5s | 20,000/s |
| Processing | 10,000 | ~10s | 1,000/s |
| Transform | 10,000 | ~5s | 2,000/s |

---

*API Reference Version: [X.Y.Z]*
*Last Updated: [Date]*
```

---

### 3. Models Reference (docs/api/models.md)

Document all data models:

```markdown
# Models API Reference

`[package].models` - Data models and schemas.

---

## Data Models

### InputModel

Input data model for processing requests.

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class InputModel(BaseModel):
    """
    Input data record model.
    
    Represents a single data record for processing.
    """
    
    id: str = Field(..., description="Unique record identifier")
    value: float = Field(..., gt=0, description="Positive numeric value")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "rec_123",
                "value": 100.50,
                "timestamp": "2024-10-06T10:00:00Z",
                "metadata": {"source": "api"}
            }
        }
```

**Fields**:
- `id`: Unique identifier for record
- `value`: Numeric value (must be positive)
- `timestamp`: When record was created
- `metadata`: Additional key-value data

**Validation Rules**:
- `id` must be non-empty string
- `value` must be > 0
- `timestamp` must be valid datetime
- `metadata` must be dictionary if provided

**Example Usage**:
```python
from mypackage.models import InputModel

# Create instance
record = InputModel(
    id="rec_001",
    value=150.75,
    metadata={"category": "A"}
)

# From dictionary
data = {"id": "rec_002", "value": 200.0}
record = InputModel(**data)

# Validation
try:
    record = InputModel(id="test", value=-10)  # Fails: negative value
except ValidationError as e:
    print(e)
```

---

### OutputModel

Output data model for processing results.

```python
class OutputModel(BaseModel):
    """Processed data output model."""
    
    input_id: str
    result: float
    status: str = Field(..., pattern="^(success|error|partial)$")
    processed_at: datetime
    errors: Optional[List[str]] = None
```

**Example**:
```python
output = OutputModel(
    input_id="rec_001",
    result=150.75,
    status="success",
    processed_at=datetime.utcnow()
)
```

---

## Enumerations

### ProcessingStatus

```python
from enum import Enum

class ProcessingStatus(str, Enum):
    """Processing status values."""
    
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    PENDING = "pending"
```

**Usage**:
```python
from mypackage.models import ProcessingStatus

status = ProcessingStatus.SUCCESS
if status == ProcessingStatus.SUCCESS:
    print("Processing completed")
```

---

*For complete model reference, see source code documentation.*
```

---

## Deliverables

Please create:

1. **docs/api/README.md** - API overview and index
2. **docs/api/core.md** - Core module complete reference
3. **docs/api/models.md** - Data models reference
4. **docs/api/utils.md** - Utilities reference
5. **docs/api/exceptions.md** - Exceptions reference

**For Each Public Class:**
- Complete constructor documentation
- All public methods documented
- Parameters fully specified with types
- Return values described
- Exceptions listed
- Usage examples provided
- Performance notes where relevant

**For Each Public Function:**
- Purpose and behavior explained
- All parameters documented
- Return value specified
- Exceptions listed
- Code examples provided

**Quality Checks:**
- [ ] All public APIs documented
- [ ] Parameters have types and descriptions
- [ ] Return values explained
- [ ] Examples provided and tested
- [ ] Exceptions documented
- [ ] Performance notes included where relevant
- [ ] Cross-references working

Complete and confirm API documentation is comprehensive and accurate.

---

## Success Criteria

- ✅ All public classes documented
- ✅ All public methods documented
- ✅ All public functions documented
- ✅ Parameters fully specified
- ✅ Return values described
- ✅ Exceptions listed
- ✅ Usage examples provided
- ✅ Type annotations documented
- ✅ Performance notes included

---

## Tools for API Documentation

### Sphinx
```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Generate documentation
sphinx-apidoc -o docs/api src/
sphinx-build -b html docs/ docs/_build
```

### pdoc
```bash
# Install pdoc
pip install pdoc3

# Generate documentation
pdoc --html --output-dir docs/ src/
```

### MkDocs
```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Serve documentation
mkdocs serve
```

---

## Next Steps

After completing Phase 5:
- Review all documentation for accuracy
- Test all code examples
- Publish documentation to hosting platform
- Set up documentation versioning
- Establish documentation maintenance process
