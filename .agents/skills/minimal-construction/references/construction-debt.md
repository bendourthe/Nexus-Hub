# Construction-debt markers

Use a generic in-code marker when a deliberate corner cuts a real ceiling. This is not a second known-gaps ledger and not a SQALE score. `known-gaps-tracker` still owns version deferrals. `technical-debt-analyzer` still owns interest quantification.

## Marker convention

Language-appropriate comment prefix, then:

`construction-debt: <ceiling>, <upgrade trigger>`

Examples:

```python
# construction-debt: in-memory dict cache, add Redis when a second process shares this map
```

```ts
// construction-debt: native date input only, add a calendar widget when the locale picker ships
```

```go
// construction-debt: linear scan, add an index when n exceeds 10k rows in production
```

Rules:

- Name the ceiling that was cut (what a fuller solution would add).
- Name an observable upgrade trigger (when to revisit). If the trigger is missing, harvest tags the hit `no-trigger`.
- Never use an external product name as the marker.
- Do not treat End-of-Task Summary, a user-requested explanation, a proving command, or a trust-boundary check as a ceiling to cut.

## Harvest (read-only)

Default is report-only. Do not edit files during harvest.

Skip `node_modules`, `.git`, and build output (`dist`, `build`, `coverage`, `__pycache__`, `.venv`).

POSIX:

```bash
rg -n --hidden -g '!node_modules' -g '!.git' -g '!dist' -g '!build' -g '!coverage' -g '!__pycache__' -g '!.venv' "construction-debt:"
```

PowerShell:

```powershell
rg -n --hidden -g '!node_modules' -g '!.git' -g '!dist' -g '!build' -g '!coverage' -g '!__pycache__' -g '!.venv' "construction-debt:"
```

If `rg` is absent, a slower fallback is acceptable:

```powershell
Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\\(node_modules|\.git|dist|build|coverage|__pycache__|\.venv)\\' } | Select-String -Pattern 'construction-debt:'
```

## Report shape

One row per hit:

| File | Line | Ceiling | Trigger | Tag |
|---|---|---|---|---|
| path | N | parsed ceiling | parsed trigger or empty | `no-trigger` when the upgrade path is missing |

End with counts: total hits, hits with a trigger, `no-trigger` hits.

Do not write those rows into `known-gaps.md`. If a hit should become a version-level deferral, hand it to `known-gaps-tracker` as a separate decision.

No top-level `scripts/*.py` is required for this harvest. Recursive skill copy distributes this reference with no installer edit.
