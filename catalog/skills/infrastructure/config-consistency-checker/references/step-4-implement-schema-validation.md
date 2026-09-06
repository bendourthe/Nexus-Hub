### Step 4: Implement Schema Validation

Define a JSON Schema that describes the expected configuration structure and validate each environment against it.

**Configuration Schema** (`config/schema.json`):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Application Configuration",
  "type": "object",
  "required": [
    "database.host",
    "database.port",
    "database.name",
    "server.port",
    "server.host",
    "auth.jwt_secret",
    "auth.token_expiry_seconds",
    "logging.level",
    "logging.format"
  ],
  "properties": {
    "database.host": {
      "type": "string",
      "minLength": 1,
      "description": "Database hostname or IP address"
    },
    "database.port": {
      "type": "integer",
      "minimum": 1,
      "maximum": 65535,
      "description": "Database port number"
    },
    "database.name": {
      "type": "string",
      "pattern": "^[a-zA-Z][a-zA-Z0-9_]*$",
      "description": "Database name (alphanumeric and underscores)"
    },
    "database.max_connections": {
      "type": "integer",
      "minimum": 1,
      "maximum": 1000,
      "default": 20,
      "description": "Maximum number of database connections in the pool"
    },
    "server.port": {
      "type": "integer",
      "minimum": 1,
      "maximum": 65535
    },
    "server.host": {
      "type": "string",
      "format": "hostname"
    },
    "auth.jwt_secret": {
      "type": "string",
      "minLength": 32,
      "description": "JWT signing secret (minimum 32 characters)"
    },
    "auth.token_expiry_seconds": {
      "type": "integer",
      "minimum": 60,
      "maximum": 604800,
      "description": "Token expiry in seconds (1 minute to 7 days)"
    },
    "logging.level": {
      "type": "string",
      "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    },
    "logging.format": {
      "type": "string",
      "enum": ["json", "text"]
    },
    "cache.ttl_seconds": {
      "type": "integer",
      "minimum": 0,
      "description": "Cache time-to-live in seconds (0 to disable)"
    },
    "cache.max_size_mb": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10240
    },
    "feature_flags.enable_new_search": {
      "type": "boolean"
    },
    "feature_flags.enable_export_v2": {
      "type": "boolean"
    }
  },
  "additionalProperties": true
}
```

**Schema Validator** (`scripts/config_validate_schema.py`):

```python
"""Validate configuration against a JSON Schema."""
import json
import sys
from dataclasses import dataclass
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator


@dataclass
class SchemaViolation:
    key: str
    message: str
    schema_path: str
    environment: str
    value: Any
    severity: str = "critical"


def validate_config(
    config: dict[str, Any],
    schema: dict,
    environment: str,
) -> list[SchemaViolation]:
    """Validate a flattened config dict against a JSON Schema.

    The config dict uses dot-separated keys. The schema must also use
    dot-separated keys in its properties (not nested objects).
    """
    violations = []

    # Extract just the values from annotated config
    values = {}
    for key, entry in config.items():
        if isinstance(entry, dict) and "value" in entry:
            values[key] = entry["value"]
        else:
            values[key] = entry

    # Coerce string values to their schema-expected types for validation
    properties = schema.get("properties", {})
    coerced = {}
    for key, value in values.items():
        if key in properties:
            expected_type = properties[key].get("type")
            if expected_type == "integer" and isinstance(value, str):
                try:
                    coerced[key] = int(value)
                except ValueError:
                    coerced[key] = value
            elif expected_type == "boolean" and isinstance(value, str):
                coerced[key] = value.lower() in ("true", "1", "yes")
            elif expected_type == "number" and isinstance(value, str):
                try:
                    coerced[key] = float(value)
                except ValueError:
                    coerced[key] = value
            else:
                coerced[key] = value
        else:
            coerced[key] = value

    # Validate
    validator = Draft202012Validator(schema)
    for error in validator.iter_errors(coerced):
        # Determine the key from the error path
        if error.path:
            key = ".".join(str(p) for p in error.path)
        elif error.validator == "required":
            key = error.message.split("'")[1] if "'" in error.message else "unknown"
        else:
            key = "root"

        violations.append(SchemaViolation(
            key=key,
            message=error.message,
            schema_path=".".join(str(p) for p in error.absolute_schema_path),
            environment=environment,
            value=coerced.get(key),
        ))

    return violations


def validate_all_environments(
    configs: dict[str, dict[str, Any]],
    schema_path: str,
) -> dict[str, list[SchemaViolation]]:
    """Validate all environments against the schema."""
    with open(schema_path) as f:
        schema = json.load(f)

    results = {}
    for env_name, config in configs.items():
        violations = validate_config(config, schema, env_name)
        results[env_name] = violations

    return results


if __name__ == "__main__":
    import yaml
    from config_loader import load_config

    inventory_path = sys.argv[1] if len(sys.argv) > 1 else "config-inventory.yaml"

    with open(inventory_path) as f:
        inventory = yaml.safe_load(f)

    schema_path = inventory["schema"]["path"]

    all_violations = {}
    for env_name, env_def in inventory["environments"].items():
        env_config = {}
        for file_def in env_def.get("config_files", []):
            file_config = load_config(file_def["path"], file_def["format"])
            env_config.update(file_config)

        with open(schema_path) as f:
            schema = json.load(f)
        violations = validate_config(env_config, schema, env_name)
        all_violations[env_name] = violations

        if violations:
            print(f"\n{env_name}: {len(violations)} schema violations")
            for v in violations:
                print(f"  [{v.severity}] {v.key}: {v.message}")
        else:
            print(f"\n{env_name}: schema valid")

    total = sum(len(v) for v in all_violations.values())
    if total > 0:
        print(f"\nTotal schema violations: {total}")
        sys.exit(1)
    else:
        print("\nAll environments pass schema validation")
```
