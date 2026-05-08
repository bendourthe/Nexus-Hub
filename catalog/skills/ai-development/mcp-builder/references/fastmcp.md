# FastMCP Reference

Deeper API surface for FastMCP, the Python SDK for the Model Context Protocol. Loaded on demand by `mcp-builder/SKILL.md`.

## Install

```bash
pip install "mcp[cli]"
```

The `[cli]` extra installs the `mcp` command-line tool, which provides the `mcp dev <module>` inspector. Without it, you get the SDK only.

Minimum runtime: Python 3.10+. Type annotations are mandatory throughout (FastMCP uses them to derive tool schemas).

## Minimal server

```python
# server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers and return the sum."""
    return a + b

if __name__ == "__main__":
    mcp.run()  # stdio transport by default
```

Run: `python server.py` (silent stdio loop). Inspect: `mcp dev server.py` (opens the inspector at http://localhost:5173).

## Tool definitions

The `@mcp.tool()` decorator turns a Python function into an MCP tool. The function signature drives the input schema; the return type drives the output schema.

```python
from pydantic import BaseModel, Field

class QueryResult(BaseModel):
    rows: list[dict]
    row_count: int = Field(description="Number of rows returned")

@mcp.tool()
def query_postgres(sql: str, max_rows: int = 100) -> QueryResult:
    """Run a read-only SQL query against the configured Postgres database.

    Use this whenever the user wants to inspect their database, run reports, or
    verify data shape. SKIP: any query that mutates state (INSERT / UPDATE / DELETE
    / DDL) - this tool is read-only.
    """
    # ... implementation
    return QueryResult(rows=[...], row_count=len(...))
```

Key points:

1. **Type annotations are required**. Untyped parameters fail at decoration time.
2. **Return Pydantic models for structured output**. `dict` works but loses field-level descriptions.
3. **Docstrings become the tool's description**. Apply the pushy-description rule: list trigger phrases, list `SKIP:` clauses, give an example.
4. **Default values become optional parameters**. The agent infers required vs optional from whether a default exists.
5. **Use `Field(description=...)` for parameter-level docs**. Surfaces in the inspector and in the agent's tool catalog.

## Transports

| Transport | When to use | Configuration |
|---|---|---|
| stdio | Default. Local server invoked by an MCP client (the AI CLI). | `mcp.run()` (no args). |
| HTTP | Remote server, multiple clients, debugging via curl. | `mcp.run(transport="http", host="0.0.0.0", port=8000)`. |
| SSE | Streaming responses to a remote browser-based client. | `mcp.run(transport="sse", host="0.0.0.0", port=8000)`. |

Stdio is correct 90% of the time. Promote to HTTP only when the server runs on a different host from the agent or when the same server needs to serve multiple clients simultaneously.

## Auth (HTTP / SSE only)

Stdio transport runs as the user's process; auth is implicit. HTTP / SSE transports need explicit auth.

```python
from fastapi import HTTPException, Header
from typing import Annotated
import os

EXPECTED_TOKEN = os.environ.get("MCP_AUTH_TOKEN")

@mcp.tool()
def query_postgres(
    sql: str,
    authorization: Annotated[str, Header()] = "",
) -> QueryResult:
    """..."""
    if authorization != f"Bearer {EXPECTED_TOKEN}":
        raise HTTPException(status_code=401, detail="invalid token")
    # ... implementation
```

For OAuth or more complex flows, mount FastAPI middleware on the FastMCP app via `mcp.app.add_middleware(...)`. The FastMCP app is a standard FastAPI app under the hood.

## Resources and prompts

Beyond tools, MCP supports resources (read-only data the agent can fetch) and prompts (parameterized prompt templates).

```python
@mcp.resource("schema://postgres/{table}")
def get_schema(table: str) -> str:
    """Return the column schema for a table."""
    return f"... DDL for {table} ..."

@mcp.prompt()
def review_query(sql: str) -> str:
    """Prompt the agent to review a SQL query for correctness."""
    return f"Review this SQL for safety and performance:\n\n{sql}"
```

Resources and prompts are optional. Most MCPs ship tools only.

## Testing patterns

| Pattern | When | How |
|---|---|---|
| Inspector smoke test | Every commit | `mcp dev server.py`; click each tool, paste sample input, verify output shape. |
| Unit tests for tool functions | Tools with non-trivial logic | Call the function directly with `pytest`; the decorator preserves the underlying function. |
| Schema regression tests | Before publishing | `mcp.list_tools()` returns the registered schemas; assert against a fixture JSON. |
| Integration tests over stdio | Pre-release | Use `mcp.client.stdio.stdio_client` from the SDK to spawn the server and call tools. |

Avoid mocking the MCP transport in tool tests - test the function logic directly. Reserve transport tests for the integration tier.

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Tool returns `Exception` raised in handler crashes the transport | Return a structured error: `return {"error": "...", "code": "..."}`; or use Pydantic `Result[T, ErrorModel]` shape. |
| Tool description is one sentence; agent under-calls | Apply the pushy-description rule: trigger phrases, `SKIP:` clause, sample invocation. |
| Tool input schema accepts `Any` / `dict` | Type the input precisely. `Any` defeats schema generation; the agent gets no input hints. |
| Stdio server hangs on stderr | FastMCP captures stderr by default; if your code uses `print()`, route to a logger that writes to a file, NOT stderr. |
| `mcp dev` inspector won't open | Confirm the `[cli]` extra is installed: `pip show mcp` should list `cli` in extras. |
| Server registered in settings.json but tools don't appear | Path must be absolute, not `~/...`. Verify with `python /abs/path/server.py` directly first. |

## Going beyond the scaffold

The `init-mcp-fastmcp.{sh,ps1}` script ships a one-tool hello-world. Extending past that:

1. **Multiple tools**: add additional `@mcp.tool()` decorated functions. Group by domain (e.g., `query_*`, `mutate_*`, `health_*`).
2. **Configuration**: load secrets and config from environment variables at startup; never hardcode.
3. **Logging**: use Python's `logging` module to write to a file under `~/.devai-hub/logs/<server-name>/`. NOT stderr (stdio transport conflict).
4. **Lifespan hooks**: use FastMCP's lifespan context for setup / teardown (DB connections, etc.).
5. **Distribution**: package the server as a console script in `pyproject.toml` so users can `pipx install` it.
