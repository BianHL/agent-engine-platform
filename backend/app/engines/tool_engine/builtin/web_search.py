"""Built-in tool: web search via DuckDuckGo."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.engines.tool_engine.registry import ToolDef

logger = logging.getLogger(__name__)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search query"},
        "max_results": {
            "type": "integer",
            "description": "Maximum results to return",
            "default": 5,
        },
    },
    "required": ["query"],
}


async def _execute(params: dict[str, Any]) -> dict[str, Any]:
    """Execute web search using DuckDuckGo."""
    query = params["query"]
    max_results = params.get("max_results", 5)

    try:
        from duckduckgo_search import DDGS

        def _search():
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return results

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, _search)
        return {
            "results": [
                {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
                for r in results
            ]
        }
    except ImportError:
        logger.warning("duckduckgo_search not installed, using fallback")
        return {"results": [], "error": "duckduckgo_search package not installed"}
    except Exception as e:
        logger.error("Web search failed: %s", e)
        return {"results": [], "error": str(e)}


web_search_tool = ToolDef(
    name="web_search",
    description="Search the web using DuckDuckGo. Returns titles, URLs, and snippets.",
    tool_type="builtin",
    input_schema=INPUT_SCHEMA,
    handler=_execute,
    permissions=["tool:web_search"],
)
