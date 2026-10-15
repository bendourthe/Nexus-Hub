### Step 2: Build the Configuration Parser

**Multi-Format Configuration Loader** (`scripts/config_loader.py`):

```python
"""Load configuration from multiple formats into a normalized structure."""
import json
import os
import re
from pathlib import Path
from typing import Any


def load_yaml(path: str) -> dict[str, Any]:
    """Load a YAML configuration file."""
    import yaml
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_json(path: str) -> dict[str, Any]:
    """Load a JSON configuration file."""
    with open(path) as f:
        return json.load(f)


def load_toml(path: str) -> dict[str, Any]:
    """Load a TOML configuration file."""
    import tomllib
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_dotenv(path: str) -> dict[str, str]:
    """Load a .env file into a flat dictionary."""
    result = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Remove surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key] = value
    return result


LOADERS = {
    "yaml": load_yaml,
    "yml": load_yaml,
    "json": load_json,
    "toml": load_toml,
    "dotenv": load_dotenv,
    "env": load_dotenv,
}


def flatten_dict(d: dict, prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dictionary into dot-separated keys.

    Example: {"database": {"host": "localhost"}} -> {"database.host": "localhost"}
    """
    items = {}
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, full_key))
        else:
            items[full_key] = value
    return items


def detect_type(value: Any) -> str:
    """Detect the semantic type of a configuration value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, str):
        # Detect common patterns
        if re.match(r"^https?://", value):
            return "url"
        if re.match(r"^\d+$", value):
            return "integer_string"
        if re.match(r"^(true|false)$", value, re.IGNORECASE):
            return "boolean_string"
        if re.match(r"^(arn:|vault:|ssm:)", value):
            return "secret_reference"
        return "string"
    return "unknown"


def load_config(path: str, format: str) -> dict[str, Any]:
    """Load a configuration file and return flattened key-value pairs with metadata."""
    loader = LOADERS.get(format)
    if loader is None:
        raise ValueError(f"Unsupported format: {format}")

    raw = loader(path)
    flat = flatten_dict(raw)

    # Annotate each value with type metadata
    annotated = {}
    for key, value in flat.items():
        annotated[key] = {
            "value": value,
            "type": detect_type(value),
            "source": path,
        }

    return annotated
```
