"""Unit tests for tool_engine: http_request, schema_parser, and registry."""
from __future__ import annotations

import socket
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.engines.tool_engine.builtin.http_request import (
    INPUT_SCHEMA,
    _execute,
    http_request_tool,
)
from app.engines.tool_engine.registry import ToolDef, ToolRegistry


# ---------------------------------------------------------------------------
# ToolDef and ToolRegistry
# ---------------------------------------------------------------------------


class TestToolDef:
    def test_tool_def_creation(self):
        handler = AsyncMock()
        tool = ToolDef(
            name="test_tool",
            description="A test tool",
            tool_type="builtin",
            input_schema={"type": "object", "properties": {}},
            handler=handler,
        )
        assert tool.name == "test_tool"
        assert tool.tool_type == "builtin"
        assert tool.permissions == []

    def test_to_openai_function(self):
        tool = ToolDef(
            name="my_tool",
            description="Does things",
            tool_type="custom",
            input_schema={"type": "object", "properties": {"x": {"type": "string"}}},
            handler=AsyncMock(),
        )
        result = tool.to_openai_function()
        assert result["type"] == "function"
        assert result["function"]["name"] == "my_tool"
        assert result["function"]["parameters"]["properties"]["x"]["type"] == "string"

    def test_to_dict(self):
        tool = ToolDef(
            name="my_tool",
            description="Desc",
            tool_type="builtin",
            input_schema={"type": "object"},
            handler=AsyncMock(),
            permissions=["tool:test"],
        )
        d = tool.to_dict()
        assert d["name"] == "my_tool"
        assert d["permissions"] == ["tool:test"]


class TestToolRegistry:
    def setup_method(self):
        # Reset singleton for test isolation
        ToolRegistry._instance = None

    def test_register_and_get(self):
        reg = ToolRegistry()
        tool = ToolDef(
            name="t1", description="d", tool_type="builtin",
            input_schema={}, handler=AsyncMock(),
        )
        reg.register(tool)
        assert reg.get("t1") is tool
        assert reg.get("nonexistent") is None

    def test_unregister(self):
        reg = ToolRegistry()
        tool = ToolDef(
            name="t1", description="d", tool_type="builtin",
            input_schema={}, handler=AsyncMock(),
        )
        reg.register(tool)
        assert reg.unregister("t1") is True
        assert reg.get("t1") is None
        assert reg.unregister("t1") is False

    def test_list_tools_filtered(self):
        reg = ToolRegistry()
        reg.register(ToolDef(
            name="a", description="", tool_type="builtin",
            input_schema={}, handler=AsyncMock(),
        ))
        reg.register(ToolDef(
            name="b", description="", tool_type="custom",
            input_schema={}, handler=AsyncMock(), permissions=["tool:x"],
        ))
        assert len(reg.list_tools(tool_type="builtin")) == 1
        assert len(reg.list_tools(permission="tool:x")) == 1
        assert len(reg.list_tools()) == 2


# ---------------------------------------------------------------------------
# http_request builtin tool
# ---------------------------------------------------------------------------


class TestHttpRequestTool:
    def test_tool_definition(self):
        assert http_request_tool.name == "http_request"
        assert http_request_tool.tool_type == "builtin"
        assert "url" in INPUT_SCHEMA["required"]

    @pytest.mark.asyncio
    async def test_successful_get(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "text/plain"}
        mock_resp.text = "OK"

        with patch(
            "app.engines.tool_engine.builtin.http_request.safe_request",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ) as mock_req:
            result = await _execute({"url": "https://example.com/api"})

        assert result["status_code"] == 200
        assert result["body"] == "OK"
        mock_req.assert_called_once()
        call_args = mock_req.call_args
        assert call_args[0] == ("GET", "https://example.com/api")

    @pytest.mark.asyncio
    async def test_successful_post_with_body(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.headers = {}
        mock_resp.text = '{"id": 1}'

        with patch(
            "app.engines.tool_engine.builtin.http_request.safe_request",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ) as mock_req:
            result = await _execute({
                "url": "https://example.com/api",
                "method": "POST",
                "body": {"name": "test"},
            })

        assert result["status_code"] == 201
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["json"] == {"name": "test"}

    @pytest.mark.asyncio
    async def test_get_request_no_body(self):
        """GET requests should not pass json body even if provided."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.text = ""

        with patch(
            "app.engines.tool_engine.builtin.http_request.safe_request",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ) as mock_req:
            await _execute({"url": "https://example.com", "method": "GET", "body": {"x": 1}})

        call_kwargs = mock_req.call_args[1]
        assert "json" not in call_kwargs

    @pytest.mark.asyncio
    async def test_ssrf_blocked(self):
        with patch(
            "app.engines.tool_engine.builtin.http_request.safe_request",
            new_callable=AsyncMock,
            side_effect=ValueError("URL blocked: Blocked IP: 127.0.0.1"),
        ):
            result = await _execute({"url": "http://127.0.0.1/admin"})

        assert "error" in result
        assert "URL blocked" in result["error"]

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        with patch(
            "app.engines.tool_engine.builtin.http_request.safe_request",
            new_callable=AsyncMock,
            side_effect=httpx.TimeoutException("timeout"),
        ):
            result = await _execute({"url": "https://example.com", "timeout": 5})

        assert "error" in result
        assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_general_error(self):
        with patch(
            "app.engines.tool_engine.builtin.http_request.safe_request",
            new_callable=AsyncMock,
            side_effect=ConnectionError("refused"),
        ):
            result = await _execute({"url": "https://example.com"})

        assert "error" in result
        assert "Request failed" in result["error"]

    @pytest.mark.asyncio
    async def test_body_truncated(self):
        """Response body should be truncated to 50000 chars."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.text = "x" * 60000

        with patch(
            "app.engines.tool_engine.builtin.http_request.safe_request",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            result = await _execute({"url": "https://example.com"})

        assert len(result["body"]) == 50000


# ---------------------------------------------------------------------------
# schema_parser
# ---------------------------------------------------------------------------


class TestSchemaParser:
    def _import(self):
        from app.engines.tool_engine.schema_parser import (
            _build_input_schema,
            _extract_base_url,
            _create_api_handler,
            parse_openapi_to_tools,
        )
        return _extract_base_url, _build_input_schema, _create_api_handler, parse_openapi_to_tools

    def test_extract_base_url_from_servers(self):
        _extract_base_url, _, _, _ = self._import()
        spec = {"servers": [{"url": "https://api.example.com/v1"}]}
        assert _extract_base_url(spec) == "https://api.example.com/v1"

    def test_extract_base_url_from_host_basepath(self):
        _extract_base_url, _, _, _ = self._import()
        spec = {"host": "api.example.com", "basePath": "/v2", "schemes": ["https"]}
        assert _extract_base_url(spec) == "https://api.example.com/v2"

    def test_extract_base_url_empty(self):
        _extract_base_url, _, _, _ = self._import()
        assert _extract_base_url({}) == ""

    def test_build_input_schema_with_params(self):
        _, _build_input_schema, _, _ = self._import()
        operation = {
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}},
                {"name": "filter", "in": "query", "schema": {"type": "string"}},
            ]
        }
        schema = _build_input_schema(operation)
        assert "id" in schema["properties"]
        assert "id" in schema["required"]
        assert "filter" in schema["properties"]
        assert "filter" not in schema["required"]

    def test_build_input_schema_with_request_body(self):
        _, _build_input_schema, _, _ = self._import()
        operation = {
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Name"},
                            },
                            "required": ["name"],
                        }
                    }
                }
            }
        }
        schema = _build_input_schema(operation)
        assert "name" in schema["properties"]
        assert "name" in schema["required"]

    @pytest.mark.asyncio
    async def test_handler_path_param_substitution(self):
        _, _, _create_api_handler, _ = self._import()
        operation = {"parameters": []}
        handler = _create_api_handler("https://api.example.com", "/users/{id}", "get", operation)

        with patch(
            "app.engines.tool_engine.schema_parser.safe_request",
            new_callable=AsyncMock,
        ) as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = '{"user": 1}'
            mock_req.return_value = mock_resp

            await handler({"id": 42})

        call_url = mock_req.call_args[0][1]
        assert "/users/42" in call_url

    @pytest.mark.asyncio
    async def test_handler_query_vs_body_separation(self):
        _, _, _create_api_handler, _ = self._import()
        operation = {
            "parameters": [
                {"name": "page", "in": "query", "schema": {"type": "integer"}},
            ]
        }
        handler = _create_api_handler("https://api.example.com", "/items", "post", operation)

        with patch(
            "app.engines.tool_engine.schema_parser.safe_request",
            new_callable=AsyncMock,
        ) as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "ok"
            mock_req.return_value = mock_resp

            await handler({"page": 2, "name": "test"})

        call_kwargs = mock_req.call_args[1]
        assert call_kwargs.get("params") == {"page": 2}
        assert call_kwargs.get("json") == {"name": "test"}

    @pytest.mark.asyncio
    async def test_handler_ssrf_blocked(self):
        _, _, _create_api_handler, _ = self._import()
        operation = {"parameters": []}
        handler = _create_api_handler("http://127.0.0.1", "/admin", "get", operation)

        with patch(
            "app.engines.tool_engine.schema_parser.safe_request",
            new_callable=AsyncMock,
            side_effect=ValueError("URL blocked: Blocked IP: 127.0.0.1"),
        ):
            result = await handler({})

        assert "error" in result
        assert "SSRF protection" in result["error"]

    @pytest.mark.asyncio
    async def test_handler_general_error(self):
        _, _, _create_api_handler, _ = self._import()
        operation = {"parameters": []}
        handler = _create_api_handler("https://api.example.com", "/fail", "get", operation)

        with patch(
            "app.engines.tool_engine.schema_parser.safe_request",
            new_callable=AsyncMock,
            side_effect=ConnectionError("refused"),
        ):
            result = await handler({})

        assert "error" in result

    def test_parse_openapi_to_tools(self):
        _, _, _, _parse_openapi_to_tools = self._import()
        spec = {
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "listUsers",
                        "summary": "List all users",
                        "parameters": [
                            {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                        ],
                    },
                    "post": {
                        "operationId": "createUser",
                        "summary": "Create a user",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"name": {"type": "string"}},
                                        "required": ["name"],
                                    }
                                }
                            }
                        },
                    },
                },
            },
        }
        tools = _parse_openapi_to_tools(spec)
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert "listUsers" in names
        assert "createUser" in names
        for t in tools:
            assert callable(t.handler)
            assert t.tool_type == "custom"

    def test_parse_openapi_generates_name_from_path(self):
        """operationId fallback should use method + path."""
        _, _, _, _parse_openapi_to_tools = self._import()
        spec = {
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/items/{id}": {
                    "get": {"summary": "Get item"},
                },
            },
        }
        tools = _parse_openapi_to_tools(spec)
        assert len(tools) == 1
        assert "get" in tools[0].name
