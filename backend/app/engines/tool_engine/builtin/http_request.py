"""Built-in tool: SSRF-safe HTTP requests."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.ssrf import safe_request
from app.engines.tool_engine.registry import ToolDef

logger = logging.getLogger(__name__)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {"type": "string", "description": "URL to request"},
        "method": {
            "type": "string",
            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "default": "GET",
        },
        "headers": {"type": "object", "description": "HTTP headers", "default": {}},
        "body": {"type": "object", "description": "Request body (JSON)"},
        "timeout": {"type": "integer", "default": 30, "description": "Timeout in seconds"},
    },
    "required": ["url"],
}


async def _execute(params: dict[str, Any]) -> dict[str, Any]:
    """Execute an HTTP request with SSRF protection."""
    url = params["url"]
    method = params.get("method", "GET").upper()
    headers = params.get("headers", {})
    body = params.get("body")
    timeout = params.get("timeout", 30)

    try:
        kwargs: dict[str, Any] = {}
        if body and method in ("POST", "PUT", "PATCH"):
            kwargs["json"] = body

        resp = await safe_request(
            method, url,
            timeout=timeout,
            follow_redirects=False,
            headers=headers,
            **kwargs,
        )
        content = resp.text[:50000]

        return {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": content,
        }
    except ValueError as e:
        return {"error": str(e)}
    except httpx.TimeoutException:
        return {"error": f"Request timed out after {timeout}s"}
    except Exception as e:
        return {"error": f"Request failed: {e}"}


http_request_tool = ToolDef(
    name="http_request",
    description="Make HTTP requests with SSRF protection.",
    tool_type="builtin",
    input_schema=INPUT_SCHEMA,
    handler=_execute,
    permissions=["tool:http_request"],
)
