"""Unit tests for MCP Server."""
import json
import os
import pytest
from unittest.mock import patch

from app.mcp.server import (
    MCPServer,
    TOOL_DEFINITIONS,
    RESOURCE_TEMPLATES,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_api_key():
    """Set a test API key for MCP authentication."""
    with patch.dict(os.environ, {"MCP_API_KEY": "test-key-123"}):
        with patch("app.config.settings.MCP_API_KEY", "test-key-123"):
            yield "test-key-123"


@pytest.fixture
def authenticated_server(mock_api_key):
    """Return a pre-authenticated MCPServer."""
    server = MCPServer()
    server._authenticated = True
    return server


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

def test_tool_definitions_exist():
    """All expected tools are defined."""
    tool_names = {t["name"] for t in TOOL_DEFINITIONS}
    expected = {
        "create_agent", "update_agent", "delete_agent", "list_agents",
        "send_message", "search_knowledge", "list_knowledge_bases",
        "evaluate_rag", "run_workflow", "list_workflows",
        "get_audit_logs", "check_safety", "manage_memory",
        "list_models", "manage_multi_agent", "get_platform_stats",
    }
    assert tool_names == expected


def test_tool_definitions_have_schema():
    """Every tool has name, description, and inputSchema."""
    for tool in TOOL_DEFINITIONS:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"


def test_create_agent_tool_schema():
    tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "create_agent")
    props = tool["inputSchema"]["properties"]
    assert "name" in props
    assert "description" in props
    assert "name" in tool["inputSchema"]["required"]


def test_search_knowledge_tool_schema():
    tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "search_knowledge")
    assert "query" in tool["inputSchema"]["required"]
    assert "kb_id" in tool["inputSchema"]["required"]


def test_run_workflow_tool_schema():
    tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "run_workflow")
    assert "workflow_id" in tool["inputSchema"]["required"]


def test_send_message_tool_schema():
    tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "send_message")
    assert "agent_id" in tool["inputSchema"]["required"]
    assert "message" in tool["inputSchema"]["required"]


# ---------------------------------------------------------------------------
# Resource templates
# ---------------------------------------------------------------------------

def test_resource_templates_exist():
    """All resource templates are defined."""
    uri_templates = {r["uriTemplate"] for r in RESOURCE_TEMPLATES}
    expected = {
        "agent://{agent_id}", "kb://{kb_id}", "workflow://{workflow_id}",
        "audit://{limit}", "memory://{agent_id}", "stats://{metric_type}",
        "models://{provider_type}", "crew://{crew_id}",
    }
    assert uri_templates == expected


def test_resource_templates_have_mime_type():
    for tmpl in RESOURCE_TEMPLATES:
        assert "mimeType" in tmpl
        assert tmpl["mimeType"] == "application/json"


# ---------------------------------------------------------------------------
# MCP Server dispatch
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_server_initialize():
    server = MCPServer()
    result = await server._dispatch({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {},
    })
    assert result is not None
    assert result["id"] == 1
    assert "result" in result
    assert result["result"]["protocolVersion"] == "2024-11-05"
    assert "capabilities" in result["result"]


@pytest.mark.asyncio
async def test_server_initialize_with_api_key(mock_api_key):
    """Initialize with valid API key should authenticate the server."""
    server = MCPServer()
    result = await server._dispatch({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"apiKey": "test-key-123"},
    })
    assert result is not None
    assert "result" in result
    assert server._authenticated is True


@pytest.mark.asyncio
async def test_server_tools_list(authenticated_server):
    result = await authenticated_server._dispatch({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    })
    assert result is not None
    tools = result["result"]["tools"]
    assert len(tools) == 16


@pytest.mark.asyncio
async def test_server_ping(authenticated_server):
    result = await authenticated_server._dispatch({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "ping",
        "params": {},
    })
    assert result is not None
    assert "result" in result
    assert result["result"]["server"] == "agent-engine-platform"


@pytest.mark.asyncio
async def test_server_unknown_method(authenticated_server):
    result = await authenticated_server._dispatch({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "unknown/method",
        "params": {},
    })
    assert result is not None
    assert "error" in result
    assert result["error"]["code"] == -32601


@pytest.mark.asyncio
async def test_server_notification_no_response():
    """Notifications (no id) should not produce a response."""
    server = MCPServer()
    result = await server._dispatch({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    })
    assert result is None


@pytest.mark.asyncio
async def test_server_resource_templates(authenticated_server):
    result = await authenticated_server._dispatch({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "resources/templates/list",
        "params": {},
    })
    assert result is not None
    templates = result["result"]["resourceTemplates"]
    assert len(templates) == 8


@pytest.mark.asyncio
async def test_server_resources_list(authenticated_server):
    result = await authenticated_server._dispatch({
        "jsonrpc": "2.0",
        "id": 6,
        "method": "resources/list",
        "params": {},
    })
    assert result is not None
    assert "resources" in result["result"]


@pytest.mark.asyncio
async def test_server_requires_auth():
    """Methods other than initialize should require authentication."""
    server = MCPServer()
    result = await server._dispatch({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    })
    assert result is not None
    assert "error" in result
    assert result["error"]["code"] == -32001
