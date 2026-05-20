"""FastMCP server exposing the fetch_url tool."""
from __future__ import annotations

import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from nexus_web_fetch.fetcher import FetchError, fetch_url
from nexus_web_fetch.ssrf_guard import GuardConfig, SSRFError

logger = logging.getLogger("nexus-web-fetch")


async def run_server() -> None:
    server = Server("nexus-web-fetch")
    config = GuardConfig.load()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="fetch_url",
                description=(
                    "Fetch a URL over HTTPS and extract readable content. Data destination "
                    "is the URL itself; no third-party intermediary. SSRF-guarded "
                    "(RFC 1918, loopback, link-local blocked by default). "
                    "extract_mode: 'readability' (default, main article), 'text' "
                    "(full plain text), 'raw' (raw HTML). render_js=True is reserved "
                    "for v1.1.0 and raises NotImplementedError in v1.0.0."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Target URL (http or https)"},
                        "render_js": {
                            "type": "boolean",
                            "default": False,
                            "description": "Reserved for v1.1.0. Must be false in v1.0.0.",
                        },
                        "extract_mode": {
                            "type": "string",
                            "enum": ["readability", "text", "raw"],
                            "default": "readability",
                        },
                    },
                    "required": ["url"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name != "fetch_url":
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
        try:
            result = await fetch_url(
                url=arguments["url"],
                render_js=bool(arguments.get("render_js", False)),
                extract_mode=arguments.get("extract_mode", "readability"),
                config=config,
            )
            return [TextContent(type="text", text=json.dumps(result.to_dict()))]
        except SSRFError as exc:
            return [TextContent(type="text", text=json.dumps({"error": f"ssrf_blocked: {exc}"}))]
        except NotImplementedError as exc:
            return [TextContent(type="text", text=json.dumps({"error": f"not_implemented: {exc}"}))]
        except (FetchError, ValueError) as exc:
            return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]
        except Exception as exc:  # noqa: BLE001
            logger.exception("fetch_url failed unexpectedly")
            return [TextContent(type="text", text=json.dumps({"error": f"unexpected: {exc}"}))]

    logger.info("Starting nexus-web-fetch (stdio transport)")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
