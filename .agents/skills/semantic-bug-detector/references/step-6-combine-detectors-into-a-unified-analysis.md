### Step 6: Combine Detectors into a Unified Analysis

Run all detectors together and produce a prioritized report.

**Python: Unified semantic analysis**

```python
def run_full_semantic_analysis(source_code: str, filename: str) -> dict:
    """Run all semantic bug detectors and return a unified report."""
    results = {
        "filename": filename,
        "logic_flow": analyze_logic_flow(source_code, filename),
        "off_by_one": detect_off_by_one(source_code, filename),
        "null_safety": analyze_null_safety(source_code, filename),
        "total_issues": 0,
        "critical_count": 0,
        "high_count": 0,
    }

    all_issues = (
        results["logic_flow"]
        + results["off_by_one"]
        + results["null_safety"]
    )

    results["total_issues"] = len(all_issues)
    results["critical_count"] = sum(
        1 for i in all_issues
        if (i.severity if hasattr(i, "severity") else i.get("severity")) == "critical"
    )
    results["high_count"] = sum(
        1 for i in all_issues
        if (i.severity if hasattr(i, "severity") else i.get("severity")) == "high"
    )

    return results
```
