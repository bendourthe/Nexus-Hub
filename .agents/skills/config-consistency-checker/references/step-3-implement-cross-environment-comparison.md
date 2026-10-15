### Step 3: Implement Cross-Environment Comparison

**Configuration Comparator** (`scripts/config_compare.py`):

```python
"""Compare configuration across environments and detect inconsistencies."""
import json
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class FindingType(str, Enum):
    MISSING_KEY = "missing_key"
    TYPE_MISMATCH = "type_mismatch"
    VALUE_DRIFT = "value_drift"
    EXTRA_KEY = "extra_key"
    SECRET_REFERENCE_MISSING = "secret_reference_missing"
    SCHEMA_VIOLATION = "schema_violation"


@dataclass
class Finding:
    finding_type: FindingType
    severity: Severity
    key: str
    message: str
    environments: dict = field(default_factory=dict)
    remediation: str = ""


def compare_environments(
    configs: dict[str, dict[str, Any]],
    reference_env: str = "production",
    ignore_keys: Optional[list[str]] = None,
) -> list[Finding]:
    """Compare all environments against a reference environment.

    Args:
        configs: Mapping of environment name to flattened config dict.
        reference_env: The environment to treat as the source of truth.
        ignore_keys: Keys to skip during comparison (environment-specific by design).

    Returns:
        List of findings sorted by severity.
    """
    findings = []
    ignore = set(ignore_keys or [])

    if reference_env not in configs:
        raise ValueError(f"Reference environment '{reference_env}' not found")

    ref_config = configs[reference_env]
    all_keys = set()
    for env_config in configs.values():
        all_keys.update(env_config.keys())

    for key in sorted(all_keys):
        if key in ignore:
            continue

        in_ref = key in ref_config
        env_presence = {env: key in cfg for env, cfg in configs.items()}
        present_envs = [env for env, present in env_presence.items() if present]
        missing_envs = [env for env, present in env_presence.items() if not present]

        # Check for missing keys
        if in_ref and missing_envs:
            findings.append(Finding(
                finding_type=FindingType.MISSING_KEY,
                severity=Severity.CRITICAL,
                key=key,
                message=f"Key exists in {reference_env} but is missing from: {', '.join(missing_envs)}",
                environments={
                    env: ref_config[key]["value"] if env == reference_env else "MISSING"
                    for env in configs
                },
                remediation=f"Add '{key}' to the configuration for: {', '.join(missing_envs)}",
            ))

        # Check for extra keys (in non-reference environments only)
        if not in_ref and present_envs:
            non_ref_present = [e for e in present_envs if e != reference_env]
            if non_ref_present:
                findings.append(Finding(
                    finding_type=FindingType.EXTRA_KEY,
                    severity=Severity.INFO,
                    key=key,
                    message=f"Key exists in {', '.join(non_ref_present)} but not in {reference_env}",
                    environments={
                        env: configs[env][key]["value"] if key in configs[env] else "MISSING"
                        for env in configs
                    },
                    remediation=f"Either add '{key}' to {reference_env} or remove it from {', '.join(non_ref_present)}",
                ))

        # Check for type mismatches across environments that have the key
        if len(present_envs) > 1:
            types = {
                env: configs[env][key]["type"]
                for env in present_envs
            }
            unique_types = set(types.values())
            if len(unique_types) > 1:
                findings.append(Finding(
                    finding_type=FindingType.TYPE_MISMATCH,
                    severity=Severity.WARNING,
                    key=key,
                    message=f"Type varies across environments: {types}",
                    environments={
                        env: f"{configs[env][key]['value']} ({configs[env][key]['type']})"
                        for env in present_envs
                    },
                    remediation=f"Ensure '{key}' has the same type in all environments. Expected type based on {reference_env}: {types.get(reference_env, 'unknown')}",
                ))

        # Check for secret references that might be missing
        for env in present_envs:
            entry = configs[env][key]
            if entry["type"] == "secret_reference":
                findings.append(Finding(
                    finding_type=FindingType.SECRET_REFERENCE_MISSING,
                    severity=Severity.WARNING,
                    key=key,
                    message=f"Secret reference in {env}: {entry['value']}. Verify this secret exists in the target store.",
                    environments={env: entry["value"]},
                    remediation=f"Verify that the secret '{entry['value']}' exists and is accessible from the {env} environment",
                ))

    # Sort by severity (critical first)
    severity_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
    findings.sort(key=lambda f: severity_order[f.severity])

    return findings


def load_and_compare(inventory_path: str) -> list[Finding]:
    """Load configuration inventory and run comparison."""
    import yaml
    from config_loader import load_config

    with open(inventory_path) as f:
        inventory = yaml.safe_load(f)

    configs = {}
    for env_name, env_def in inventory["environments"].items():
        env_config = {}
        for file_def in env_def.get("config_files", []):
            file_config = load_config(file_def["path"], file_def["format"])
            env_config.update(file_config)
        configs[env_name] = env_config

    ignore_keys = inventory.get("ignore_keys", [])

    return compare_environments(
        configs,
        reference_env="production",
        ignore_keys=ignore_keys,
    )


if __name__ == "__main__":
    inventory = sys.argv[1] if len(sys.argv) > 1 else "config-inventory.yaml"
    output = sys.argv[2] if len(sys.argv) > 2 else "config_findings.json"

    findings = load_and_compare(inventory)

    with open(output, "w") as f:
        json.dump([asdict(f) for f in findings], f, indent=2, default=str)

    critical = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    warnings = sum(1 for f in findings if f.severity == Severity.WARNING)
    info = sum(1 for f in findings if f.severity == Severity.INFO)

    print(f"Findings: {len(findings)} total ({critical} critical, {warnings} warning, {info} info)")

    if critical > 0:
        print("CRITICAL findings detected. Review config_findings.json for details.")
        sys.exit(1)
```
