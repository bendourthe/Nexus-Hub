### Step 2: Implement Tool Integration

Tools are the agent's interface to the external world. Design them for LLM consumption (see the `tool-design` skill for detailed guidance).

**Function Calling Schema Best Practices**:

```python
# Good: Specific, documented, constrained
file_edit_tool = {
    "name": "edit_file",
    "description": (
        "Replace a specific string in a file with new content. "
        "The old_string must appear exactly once in the file. "
        "Use when you need to modify existing code. "
        "Do NOT use for creating new files (use write_file instead)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to edit."
            },
            "old_string": {
                "type": "string",
                "description": "The exact text to find and replace. Must be unique in the file."
            },
            "new_string": {
                "type": "string",
                "description": "The replacement text. Must differ from old_string."
            }
        },
        "required": ["file_path", "old_string", "new_string"]
    }
}
```

**MCP Server Integration**:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def connect_mcp_server(command: str, args: list[str]) -> ClientSession:
    """Connect to an MCP server and return a session."""
    server_params = StdioServerParameters(command=command, args=args)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                print(f"  {tool.name}: {tool.description}")

            return session


async def call_mcp_tool(session: ClientSession, name: str, arguments: dict):
    """Call a tool on the MCP server and return the result."""
    result = await session.call_tool(name, arguments=arguments)
    return result.content
```

**Tool Execution with Error Handling**:

```python
import json
import traceback


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool call with structured error handling."""
    try:
        if name == "search_codebase":
            return search_codebase(**arguments)
        elif name == "read_file":
            return read_file(**arguments)
        elif name == "edit_file":
            return edit_file(**arguments)
        else:
            return json.dumps({
                "error": f"Unknown tool: {name}",
                "available_tools": ["search_codebase", "read_file", "edit_file"],
                "suggestion": "Check the tool name and try again."
            })
    except FileNotFoundError as e:
        return json.dumps({
            "error": f"File not found: {e}",
            "suggestion": "Use search_codebase to find the correct file path."
        })
    except PermissionError as e:
        return json.dumps({
            "error": f"Permission denied: {e}",
            "recoverable": False,
            "suggestion": "This file cannot be modified. Ask the user for guidance."
        })
    except Exception as e:
        return json.dumps({
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
            "suggestion": "An unexpected error occurred. Try a different approach."
        })
```
