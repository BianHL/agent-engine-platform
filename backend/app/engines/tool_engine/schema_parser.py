"""Parse OpenAPI 3.0 schemas into tool definitions for custom API tools."""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.core.ssrf import safe_request
from app.engines.tool_engine.registry import ToolDef

logger = logging.getLogger(__name__)


def parse_openapi_to_tools(spec: dict[str, Any]) -> list[ToolDef]:
    """Parse an OpenAPI 3.0 spec into a list of ToolDef objects.

    Each operation (GET/POST/PUT/DELETE) on each path becomes a separate tool.
    """
    tools: list[ToolDef] = []
    base_url = _extract_base_url(spec)
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        for method in ("get", "post", "put", "delete", "patch"):
            operation = path_item.get(method)
            if not operation:
                continue

            tool_name = operation.get("operationId", f"{method}_{path.replace('/', '_')}").replace(" ", "_")
            description = operation.get("summary", "") or operation.get("description", "")

            # Build input schema from parameters and request body
            input_schema = _build_input_schema(operation)

            tool = ToolDef(
                name=tool_name,
                description=description,
                tool_type="custom",
                input_schema=input_schema,
                handler=_create_api_handler(base_url, path, method, operation),
                config={
                    "base_url": base_url,
                    "path": path,
                    "method": method,
                    "headers": spec.get("components", {}).get("securitySchemes", {}),
                },
            )
            tools.append(tool)

    return tools


def _extract_base_url(spec: dict[str, Any]) -> str:
    """Extract base URL from OpenAPI spec."""
    if "servers" in spec and spec["servers"]:
        return spec["servers"][0].get("url", "")
    host = spec.get("host", "")
    basePath = spec.get("basePath", "")
    schemes = spec.get("schemes", ["https"])
    if host:
        return f"{schemes[0]}://{host}{basePath}"
    return ""


def _build_input_schema(operation: dict[str, Any]) -> dict[str, Any]:
    """Build JSON Schema from OpenAPI operation parameters + request body."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    # Path and query parameters
    for param in operation.get("parameters", []):
        name = param.get("name", "")
        schema = param.get("schema", {"type": "string"})
        properties[name] = {
            "type": schema.get("type", "string"),
            "description": param.get("description", ""),
        }
        if param.get("required"):
            required.append(name)

    # Request body
    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {})
    if "application/json" in content:
        body_schema = content["application/json"].get("schema", {})
        if body_schema.get("type") == "object":
            for prop_name, prop_schema in body_schema.get("properties", {}).items():
                properties[prop_name] = {
                    "type": prop_schema.get("type", "string"),
                    "description": prop_schema.get("description", ""),
                }
            required.extend(body_schema.get("required", []))
        elif body_schema:
            properties["body"] = body_schema

    return {
        "type": "object",
        "properties": properties,
        "required": list(set(required)),
    }


def _create_api_handler(
    base_url: str, path: str, method: str, operation: dict[str, Any]
):
    """Create an async handler function for an API endpoint."""

    async def handler(params: dict[str, Any]) -> dict[str, Any]:
        # Build URL with path parameters
        url = base_url.rstrip("/") + path
        for name, value in params.items():
            url = url.replace(f"{{{name}}}", str(value))

        # Separate query params and body
        query_params = {}
        body = {}
        defined_params = {p["name"] for p in operation.get("parameters", [])}

        for name, value in params.items():
            if name in defined_params:
                query_params[name] = value
            else:
                body[name] = value

        try:
            kwargs: dict[str, Any] = {"params": query_params}
            if body and method in ("post", "put", "patch"):
                kwargs["json"] = body

            resp = await safe_request(method, url, timeout=30, **kwargs)
            return {
                "status_code": resp.status_code,
                "body": resp.text[:50000],
            }
        except ValueError as e:
            return {"error": f"SSRF protection: {e}"}
        except Exception as e:
            return {"error": str(e)}

    return handler
