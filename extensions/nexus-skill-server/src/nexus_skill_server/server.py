from __future__ import annotations

import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from nexus_skill_server.catalog import SkillCatalog
from nexus_skill_server.config import resolve_config
from nexus_skill_server.search import SearchEngine
from nexus_skill_server.types import DetailLevel

logger = logging.getLogger("nexus-skill-server")

NOT_LOADED_MSG = (
    "Nexus-Hub skill catalog not found. "
    "Set the NEXUS_HUB_ROOT environment variable to your Nexus-Hub repository root, "
    "or run the Nexus-Hub installer (install.sh / install.bat)."
)

SERVER_INSTRUCTIONS = """\
nexus-skill-server: Nexus-Hub skill catalog over MCP.

Tools (what / when):
  search_skills      Keyword + natural-language search across the Nexus-Hub
                     skill index. Use when you need to find skills that match
                     a task ("how do I write integration tests?", "FastAPI
                     async patterns"). Level: l0 / l1 / l2 progressive disclosure.
  get_skill          Fetch a specific skill by exact kebab-case name. Use when
                     you already know the skill name and need its full body
                     (level=l2).
  list_categories    Enumerate the 22 skill categories with counts.
  list_bundles       Enumerate the role-based skill bundles.
  get_bundle         Inspect one bundle by id; returns the contained skill list.

MCP Registry Policy:
  This server is `already-local` per the MCP Registry Policy
  (catalog/mcp-configs/mcp-servers.json). Zero outbound calls; zero
  credentials; the skill catalog is read directly off disk from the
  repository root pointed to by NEXUS_HUB_ROOT.

Related skill:
  The `using-nexus-hub` skill (workflow category) orients you to the
  catalog structure, common discovery patterns, and the L0 -> L2 loading
  model. Load it via search_skills(query="using-nexus-hub", level="l1").
"""


def _level_from_str(s: str) -> DetailLevel:
    try:
        return DetailLevel(s.lower())
    except ValueError:
        return DetailLevel.L0


async def run_server() -> None:
    config = resolve_config()
    catalog = SkillCatalog(config)
    catalog.load()

    search_engine = SearchEngine(config)
    if catalog.is_loaded:
        search_engine.build_index(catalog.get_all_skills_metadata(), catalog.version)

    server = Server("nexus-skill-server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="search_skills",
                description=(
                    "Search Nexus-Hub skills by keyword or natural language query. "
                    "Returns matching skills ranked by relevance. "
                    "Use level=l0 for one-line summaries, l1 for paragraph overviews, l2 for full content."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (keywords, skill name, category, or natural language description of what you need)",
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                            "description": "Maximum number of results to return",
                        },
                        "level": {
                            "type": "string",
                            "enum": ["l0", "l1", "l2"],
                            "default": "l0",
                            "description": "Detail level: l0=one-line summary, l1=paragraph overview, l2=full SKILL.md content",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_skill",
                description=(
                    "Retrieve a specific Nexus-Hub skill by exact name (kebab-case). "
                    "Use level=l0 for summary, l1 for overview, l2 for full SKILL.md content."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Skill name in kebab-case (e.g., 'code-review-security', 'ai-agent-development')",
                        },
                        "level": {
                            "type": "string",
                            "enum": ["l0", "l1", "l2"],
                            "default": "l2",
                            "description": "Detail level: l0=summary, l1=overview, l2=full content",
                        },
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="list_categories",
                description="List all Nexus-Hub skill categories with skill counts and names.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="list_bundles",
                description="List all role-based skill bundles (e.g., core-developer, ai-engineer, security-specialist).",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_bundle",
                description="Get details of a specific role-based bundle including all contained skill names.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "bundle_id": {
                            "type": "string",
                            "description": "Bundle ID in kebab-case (e.g., 'core-developer', 'ai-engineer')",
                        },
                    },
                    "required": ["bundle_id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if not catalog.is_loaded:
            return [TextContent(type="text", text=json.dumps({"error": NOT_LOADED_MSG}))]

        if name == "search_skills":
            return _handle_search(arguments, catalog, search_engine)
        if name == "get_skill":
            return _handle_get_skill(arguments, catalog)
        if name == "list_categories":
            return _handle_list_categories(catalog)
        if name == "list_bundles":
            return _handle_list_bundles(catalog)
        if name == "get_bundle":
            return _handle_get_bundle(arguments, catalog)

        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    logger.info("Starting nexus-skill-server (stdio transport)")
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options().model_copy(
            update={"instructions": SERVER_INSTRUCTIONS}
        )
        await server.run(read_stream, write_stream, init_options)


def _handle_search(args: dict, catalog: SkillCatalog, engine: SearchEngine) -> list[TextContent]:
    query = args.get("query", "")
    max_results = min(args.get("max_results", 5), 20)
    level = _level_from_str(args.get("level", "l0"))

    matches = engine.search(query, max_results)

    results = []
    for skill_name, score in matches:
        skill = catalog.get_skill(skill_name, level)
        if skill:
            result = skill.model_dump()
            result["_score"] = round(score, 4)
            results.append(result)

    response = {
        "query": query,
        "total_matches": len(results),
        "level": level.value,
        "results": results,
    }
    return [TextContent(type="text", text=json.dumps(response, indent=2))]


def _handle_get_skill(args: dict, catalog: SkillCatalog) -> list[TextContent]:
    name = args.get("name", "")
    level = _level_from_str(args.get("level", "l2"))

    skill = catalog.get_skill(name, level)
    if skill:
        return [TextContent(type="text", text=json.dumps(skill.model_dump(), indent=2))]

    suggestion = catalog.find_closest_match(name)
    error = {"error": f"Skill '{name}' not found."}
    if suggestion:
        error["suggestion"] = f"Did you mean '{suggestion}'?"
    error["available_count"] = len(catalog.get_all_skill_names())
    return [TextContent(type="text", text=json.dumps(error, indent=2))]


def _handle_list_categories(catalog: SkillCatalog) -> list[TextContent]:
    categories = catalog.list_categories()
    data = [c.model_dump() for c in categories]
    return [TextContent(type="text", text=json.dumps(data, indent=2))]


def _handle_list_bundles(catalog: SkillCatalog) -> list[TextContent]:
    bundles = catalog.list_bundles()
    data = [b.model_dump() for b in bundles]
    return [TextContent(type="text", text=json.dumps(data, indent=2))]


def _handle_get_bundle(args: dict, catalog: SkillCatalog) -> list[TextContent]:
    bundle_id = args.get("bundle_id", "")
    bundle = catalog.get_bundle(bundle_id)
    if bundle:
        return [TextContent(type="text", text=json.dumps(bundle.model_dump(), indent=2))]

    available = [b.id for b in catalog.list_bundles()]
    return [TextContent(type="text", text=json.dumps({
        "error": f"Bundle '{bundle_id}' not found.",
        "available_bundles": available,
    }, indent=2))]
