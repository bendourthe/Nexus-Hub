# Compression accuracy-regression report

- CCR round-trip fidelity: **100.0%**
- Signature preservation: **100.0%**
- Mean character reduction: **45.8%** (gated effectiveness metric, tokenizer-independent)
- Mean token ratio: **58.1%** retained (informational)

## Per-fixture

| Fixture | Kind | Units (before -> after) | Char reduction | CCR round-trip | Signatures |
|---------|------|-------------------------|----------------|----------------|------------|
| json_logs | json_array | 30 -> 5 | 74.4% | 5/5 | n/a |
| search_hits | json_array | 20 -> 11 | 40.8% | 2/2 | n/a |
| python_module | code | 64 -> 42 | 42.1% | 4/4 | 11/11 |
| typescript_module | code | 39 -> 31 | 25.8% | 2/2 | 6/6 |

## Detail

### json_logs

- 30 records -> 5 kept + 4 CCR marker(s)

### search_hits

- 20 records -> 11 kept + 1 CCR marker(s)

### python_module

- strategy=ast, 64 -> 42 lines, 4 CCR-elided bod(y/ies)

### typescript_module

- strategy=ast, 39 -> 31 lines, 2 CCR-elided bod(y/ies)

## Gate

PASS -- no fidelity or effectiveness regression against the baseline.
